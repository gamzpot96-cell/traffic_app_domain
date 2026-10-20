"""F21 durable, privacy-safe operational error records.

Only allow-listed error categories and HTTP statuses are persisted.
No request URL, body, API key, user input or raw exception is stored.
"""
import logging

from app.database import get_database_connection
from app.operation_policies import safe_error_code

logger = logging.getLogger(__name__)


def record_operational_failure(source: str, event_type: str, code: str,
                               http_status: int | None = None) -> bool:
    if source not in {"kakao", "collector", "database"}:
        return False
    if event_type not in {"local_request", "directions_request",
                          "collection_run", "database_operation"}:
        return False
    status = http_status if isinstance(http_status, int) and 100 <= http_status <= 599 else None
    safe_code = safe_error_code(code)
    try:
        with get_database_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO public.traffic_operational_events
                        (source, event_type, outcome, safe_error_code, http_status)
                    VALUES (%s, %s, 'failure', %s, %s)
                    """,
                    (source, event_type, safe_code, status)
                )
        return True
    except Exception:
        # This monitoring path must not mask the original route request error.
        logger.warning("운영 오류 기록 저장 실패 (상세 정보 생략)")
        return False


def get_recent_operational_events(limit: int = 30) -> dict:
    if not 1 <= limit <= 100:
        raise ValueError("조회 건수가 올바르지 않습니다.")
    with get_database_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT event_time, source, event_type, outcome,
                       safe_error_code, http_status, occurrence_count
                FROM public.traffic_operational_events
                ORDER BY event_time DESC, id DESC
                LIMIT %s
                """,
                (limit,)
            )
            rows = cursor.fetchall()
    items = [
        {
            "event_time": row[0].isoformat(),
            "source": row[1],
            "event_type": row[2],
            "outcome": row[3],
            "error_code": row[4],
            "http_status": row[5],
            "occurrence_count": row[6]
        }
        for row in rows
    ]
    return {
        "events": items,
        "count": len(items),
        "scope_notice": "허용된 장애 코드만 보관한 최근 기록입니다. 자동 수집 이력·공식 카카오 사용량을 뜻하지 않습니다."
    }
