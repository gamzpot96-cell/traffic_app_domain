"""F22 저장된 경로 분석 CSV 내보내기. 읽기 전용 데이터 접근."""
import csv
import io
import math
import re
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from zoneinfo import ZoneInfo

from app.database import get_database_connection


MAX_EXPORT_ROWS = 5000
KST = ZoneInfo("Asia/Seoul")
CSV_HEADERS = (
    "기사 ID", "조회 완료 시각(KST)", "출발지", "목적지",
    "거리(km)", "예상 소요시간(분)", "정체·지체 거리(km)", "정체·지체 거리 비율(%)"
)


def get_export_route_options():
    """스냅샷에 실제 저장된 경로 쌍만 반환합니다."""
    with get_database_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT DISTINCT start_place, end_place
                FROM public.traffic_route_snapshots
                WHERE NOT EXISTS (
    SELECT 1 FROM public.traffic_article_publication pub
    WHERE pub.article_id = traffic_route_snapshots.article_id
      AND pub.status <> 'published'
)
                ORDER BY start_place, end_place
                """
            )
            rows = cursor.fetchall()
    return [{"origin": start, "destination": end} for start, end in rows]


def get_export_rows(origin=None, destination=None, start_time=None, end_time=None):
    """5001행째가 있으면 오류를 내고 절대로 일부 결과를 조용히 자르지 않습니다."""
    filters = ["""NOT EXISTS (
    SELECT 1 FROM public.traffic_article_publication pub
    WHERE pub.article_id = traffic_route_snapshots.article_id
      AND pub.status <> 'published'
)"""]
    params = []
    if origin is not None:
        filters.append("start_place = %s AND end_place = %s")
        params.extend((origin, destination))
    if start_time is not None:
        filters.append("retrieved_at >= %s")
        params.append(start_time)
    if end_time is not None:
        filters.append("retrieved_at < %s")
        params.append(end_time)
    where_clause = " WHERE " + " AND ".join(filters) if filters else ""

    with get_database_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT article_id, retrieved_at, start_place, end_place,
                       distance_m, duration_seconds, congested_distance_m,
                       congestion_ratio
                FROM public.traffic_route_snapshots
                """ + where_clause + """
                ORDER BY retrieved_at DESC, article_id DESC, id DESC
                LIMIT %s
                """,
                tuple(params) + (MAX_EXPORT_ROWS + 1,)
            )
            rows = cursor.fetchall()
    if len(rows) > MAX_EXPORT_ROWS:
        raise ValueError("다운로드 결과가 5,000행을 초과합니다. 기간이나 경로를 좁혀주세요.")
    return rows


def safe_csv_text(value):
    """Excel/스프레드시트에서 문자열을 수식으로 실행하지 않게 합니다."""
    if value is None:
        return ""
    text = str(value)
    # 제어문자와 앞 공백으로 수식 시작 기호를 숨기는 것도 차단합니다.
    if re.match(r"^[\s\x00-\x1f\x7f]*[=+\-@]", text):
        return "'" + text
    return text


def as_unit(value, denominator):
    if value is None:
        return ""
    result = (Decimal(str(value)) / Decimal(denominator)).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP
    )
    return str(result)


def encode_csv(rows):
    """UTF-8 BOM CSV 바이트. 반환된 행은 수정하지 않습니다."""
    output = io.StringIO(newline="")
    writer = csv.writer(output)
    writer.writerow(CSV_HEADERS)
    for record in rows:
        article_id, retrieved_at, start, end, distance, duration, congested, ratio = record
        local_time = retrieved_at.astimezone(KST).strftime("%Y-%m-%d %H:%M:%S") if retrieved_at else ""
        writer.writerow((
            article_id, local_time,
            safe_csv_text(start), safe_csv_text(end),
            as_unit(distance, 1000), as_unit(duration, 60),
            as_unit(congested, 1000),
            as_unit(ratio, 1)
        ))
    return ("\ufeff" + output.getvalue()).encode("utf-8")


def get_route_history(origin, destination, start_time=None, end_time=None, limit=100):
    """F17: 실제 저장된 단일 경로 시점만 조회합니다. 집계/보간 없음."""
    filters = ["""NOT EXISTS (
    SELECT 1 FROM public.traffic_article_publication pub
    WHERE pub.article_id = traffic_route_snapshots.article_id
      AND pub.status <> 'published'
)""", "start_place = %s", "end_place = %s"]
    params = [origin, destination]
    if start_time is not None:
        filters.append("retrieved_at >= %s")
        params.append(start_time)
    if end_time is not None:
        filters.append("retrieved_at < %s")
        params.append(end_time)
    sql = """
        SELECT article_id, retrieved_at, distance_m, duration_seconds,
               congested_distance_m, congestion_ratio
        FROM public.traffic_route_snapshots
        WHERE """ + " AND ".join(filters) + """
        ORDER BY retrieved_at DESC, id DESC
        LIMIT %s
    """
    params.append(limit + 1)
    with get_database_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(sql, tuple(params))
            rows = cursor.fetchall()
    if len(rows) > limit:
        raise ValueError("조회 결과가 제한을 초과합니다. 조회 기간을 좁혀주세요.")
    # 시간 흐름대로, 동일 시점에서는 기존 조회 정렬을 유지합니다.
    rows.reverse()
    return [
        {
            "article_id": row[0],
            "retrieved_at": row[1].isoformat(),
            "distance_m": row[2],
            "duration_seconds": row[3],
            "congested_distance_m": row[4],
            "congestion_ratio": float(row[5]) if row[5] is not None else None
        }
        for row in rows
    ]
