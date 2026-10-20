
from datetime import datetime
from decimal import Decimal

from dotenv import load_dotenv

from app.database import get_database_connection


# .env에 저장된 데이터베이스 연결 설정 읽기
load_dotenv()


# 뉴스 기사와 경로 정보를 하나의 작업으로 저장
def save_news_article(news_data, generation_id=None, changed_by="system"):

    routes = news_data.get("routes", [])

    if not routes:
        raise ValueError("저장할 경로 정보가 없습니다.")

    retrieved_at = datetime.fromisoformat(
        news_data["retrieved_at"]
    )

    if retrieved_at.tzinfo is None:
        raise ValueError("조회 시각에 시간대 정보가 없습니다.")

    # 1. 저장할 경로 데이터 먼저 검사
    route_values = []

    for route in routes:

        distance = route["distance_m"]
        congested_distance = route["congested_distance_m"]
        total_road_count = route["total_road_count"]
        congested_count = route["congested_count"]
        duration = route.get("duration_seconds")

        if distance is None or distance <= 0:
            raise ValueError("경로 거리가 올바르지 않습니다.")

        if (
            congested_distance is None
            or congested_distance < 0
            or congested_distance > distance
        ):
            raise ValueError("정체·지체 거리가 올바르지 않습니다.")

        if (
            total_road_count < 0
            or congested_count < 0
            or congested_count > total_road_count
        ):
            raise ValueError("도로 구간 수가 올바르지 않습니다.")

        if duration is not None and duration < 0:
            raise ValueError("예상 소요 시간이 올바르지 않습니다.")

        congestion_ratio = (
            Decimal(congested_distance)
            / Decimal(distance)
            * Decimal(100)
        )

        route_values.append({
            "start": route["start"],
            "end": route["end"],
            "distance": distance,
            "duration": duration,
            "total_road_count": total_road_count,
            "congested_count": congested_count,
            "congested_distance": congested_distance,
            "congestion_ratio": congestion_ratio
        })

    # 2. Supabase PostgreSQL 연결
    # 정상 종료 시 자동 COMMIT, 오류 발생 시 자동 ROLLBACK
    with get_database_connection() as connection:

        with connection.cursor() as cursor:

            # 3. 뉴스 기사 저장
            # 관리자 웹 저장은 generation_id를 UNIQUE로 관리
            # 기존 CLI 호출(None)은 이전 방식과 호환
            if generation_id is not None:
                cursor.execute(
                    """
                    INSERT INTO public.traffic_news_articles (
                        title, lead, body, scope_notice,
                        analyzed_route_count, retrieved_at, generation_id
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (generation_id) DO NOTHING
                    RETURNING id
                    """,
                    (
                        news_data["title"],
                        news_data["lead"],
                        news_data["body"],
                        news_data["scope_notice"],
                        len(route_values),
                        retrieved_at,
                        generation_id
                    )
                )
                inserted = cursor.fetchone()

                if inserted is None:
                    # 동일 ID가 이미 저장되어 있으면 경로 재삽입 없이 반환
                    cursor.execute(
                        """
                        SELECT id FROM public.traffic_news_articles
                        WHERE generation_id = %s
                        """,
                        (generation_id,)
                    )
                    old_article = cursor.fetchone()
                    if old_article is None:
                        raise RuntimeError("중복 기사 ID를 확인할 수 없습니다.")
                    return {
                        "article_id": old_article[0],
                        "saved_route_count": 0,
                        "already_saved": True,
                        "message": "이미 저장된 뉴스입니다."
                    }

                article_id = inserted[0]

            else:
                # 기존 CLI 저장 테스트용 경로
                cursor.execute(
                    """
                    INSERT INTO public.traffic_news_articles (
                        title, lead, body, scope_notice,
                        analyzed_route_count, retrieved_at
                    )
                    VALUES (%s, %s, %s, %s, %s, %s)
                    RETURNING id
                    """,
                    (
                        news_data["title"],
                        news_data["lead"],
                        news_data["body"],
                        news_data["scope_notice"],
                        len(route_values),
                        retrieved_at
                    )
                )
                article_id = cursor.fetchone()[0]

            # 4. 경로별 교통정보 저장
            for route in route_values:

                cursor.execute(
                    """
                    INSERT INTO public.traffic_route_snapshots (
                        article_id,
                        start_place,
                        end_place,
                        distance_m,
                        duration_seconds,
                        total_road_count,
                        congested_count,
                        congested_distance_m,
                        congestion_ratio,
                        retrieved_at
                    )
                    VALUES (
                        %s, %s, %s, %s, %s,
                        %s, %s, %s, %s, %s
                    )
                    """,
                    (
                        article_id,
                        route["start"],
                        route["end"],
                        route["distance"],
                        route["duration"],
                        route["total_road_count"],
                        route["congested_count"],
                        route["congested_distance"],
                        route["congestion_ratio"],
                        retrieved_at
                    )
                )

            # F20: 기사·경로·공개 상태·감사 기록을 동일 트랜잭션으로 저장합니다.
            # 상태 삽입에 실패하면 기사와 스냅샷 저장도 함께 롤백됩니다.
            cursor.execute(
                """
                INSERT INTO public.traffic_article_publication
                    (article_id, status, changed_by)
                VALUES (%s, 'review', %s)
                """,
                (article_id, str(changed_by))
            )
            cursor.execute(
                """
                INSERT INTO public.traffic_article_publication_events
                    (article_id, old_status, new_status, changed_by, note)
                VALUES (%s, NULL, 'review', %s, 'article_created')
                """,
                (article_id, str(changed_by))
            )

    # 여기까지 오류 없이 실행되면 저장 완료
    return {
        "article_id": article_id,
        "saved_route_count": len(route_values),
        "already_saved": False,
        "message": "뉴스 기사와 경로 정보 저장 완료"
    }

# Supabase에 저장된 최신 뉴스 목록 조회
def get_saved_news_articles(limit=10):

    # 한 번에 조회할 기사 수 제한
    if not 1 <= limit <= 50:
        raise ValueError("조회할 기사 수는 1~50 사이여야 합니다.")

    with get_database_connection() as connection:

        with connection.cursor() as cursor:

            cursor.execute(
                """
                SELECT
                    id,
                    title,
                    lead,
                    analyzed_route_count,
                    retrieved_at,
                    created_at
                FROM public.traffic_news_articles
                WHERE NOT EXISTS (
                    SELECT 1 FROM public.traffic_article_publication pub
                    WHERE pub.article_id = traffic_news_articles.id
                      AND pub.status <> 'published'
                )
                ORDER BY created_at DESC, id DESC
                LIMIT %s
                """,
                (limit,)
            )

            rows = cursor.fetchall()

    articles = []

    for row in rows:

        articles.append({
            "id": row[0],
            "title": row[1],
            "lead": row[2],
            "analyzed_route_count": row[3],
            "retrieved_at": row[4].isoformat(),
            "created_at": row[5].isoformat()
        })

    return articles


# F16: 저장된 기사만 읽는 키워드/조회 시각/페이지 검색
def search_saved_news_articles(
    keyword="", start_time=None, end_time=None, page=1, page_size=10
):
    if page < 1 or page_size not in (10, 20, 50):
        raise ValueError("페이지 또는 페이지 크기가 올바르지 않습니다.")

    # 키워드를 SQL 패턴이 아닌 일반 문자열로 검색합니다.
    # 기존 기사(공개 상태 기록 없음)는 계속 공개합니다.
    # 새 검토/보류 기사는 공개 검색 결과와 개수에서 모두 제외합니다.
    conditions = ["""
        NOT EXISTS (
            SELECT 1 FROM public.traffic_article_publication pub
            WHERE pub.article_id = traffic_news_articles.id
              AND pub.status <> 'published'
        )
    """]
    parameters = []
    if keyword:
        conditions.append(
            "(POSITION(LOWER(%s) IN LOWER(title)) > 0 "
            "OR POSITION(LOWER(%s) IN LOWER(lead)) > 0)"
        )
        parameters.extend([keyword, keyword])
    if start_time is not None:
        conditions.append("retrieved_at >= %s")
        parameters.append(start_time)
    if end_time is not None:
        conditions.append("retrieved_at < %s")
        parameters.append(end_time)

    where_clause = " WHERE " + " AND ".join(conditions) if conditions else ""
    offset = (page - 1) * page_size

    with get_database_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT COUNT(*) FROM public.traffic_news_articles" + where_clause,
                tuple(parameters)
            )
            total = cursor.fetchone()[0]

            cursor.execute(
                """
                SELECT id, title, lead, analyzed_route_count,
                       retrieved_at, created_at
                FROM public.traffic_news_articles
                """ + where_clause + """
                ORDER BY retrieved_at DESC, id DESC
                LIMIT %s OFFSET %s
                """,
                tuple(parameters) + (page_size, offset)
            )
            rows = cursor.fetchall()

    articles = []
    for row in rows:
        articles.append({
            "id": row[0],
            "title": row[1],
            "lead": row[2],
            "analyzed_route_count": row[3],
            "retrieved_at": row[4].isoformat(),
            "created_at": row[5].isoformat()
        })

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size,
        "articles": articles
    }


# 저장된 뉴스 기사 1건과 연결된 경로 조회
def get_saved_news_article(article_id):

    with get_database_connection() as connection:

        with connection.cursor() as cursor:

            # 1. 뉴스 기사 조회
            cursor.execute(
                """
                SELECT
                    id,
                    title,
                    lead,
                    body,
                    scope_notice,
                    analyzed_route_count,
                    retrieved_at,
                    created_at
                FROM public.traffic_news_articles
                WHERE id = %s
                  AND NOT EXISTS (
                    SELECT 1 FROM public.traffic_article_publication pub
                    WHERE pub.article_id = traffic_news_articles.id
                      AND pub.status <> 'published'
                  )
                """,
                (article_id,)
            )

            article_row = cursor.fetchone()

            # 해당 ID의 기사가 없는 경우
            if article_row is None:
                return None

            # 2. 기사에 연결된 경로 분석 결과 조회
            cursor.execute(
                """
                SELECT
                    start_place,
                    end_place,
                    distance_m,
                    duration_seconds,
                    total_road_count,
                    congested_count,
                    congested_distance_m,
                    congestion_ratio
                FROM public.traffic_route_snapshots
                WHERE article_id = %s
                ORDER BY id
                """,
                (article_id,)
            )

            route_rows = cursor.fetchall()

    # 3. 경로 데이터를 JSON으로 변환할 수 있게 정리
    routes = []

    for route in route_rows:
        routes.append({
            "start": route[0],
            "end": route[1],
            "distance_m": route[2],
            "duration_seconds": route[3],
            "total_road_count": route[4],
            "congested_count": route[5],
            "congested_distance_m": route[6],
            "congestion_ratio": float(route[7])
        })

    # 4. 뉴스 기사와 경로 데이터 반환
    return {
        "id": article_row[0],
        "title": article_row[1],
        "lead": article_row[2],
        "body": article_row[3],
        "scope_notice": article_row[4],
        "analyzed_route_count": article_row[5],
        "retrieved_at": article_row[6].isoformat(),
        "created_at": article_row[7].isoformat(),
        "routes": routes
    }


# F20: 관리자 전용 전체 기사 및 공개 상태 목록
def get_admin_publication_articles(limit=50):
    if not 1 <= limit <= 100:
        raise ValueError("조회 개수가 올바르지 않습니다.")

    with get_database_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT news.id, news.title, news.retrieved_at,
                       publication.status, news.created_at
                FROM public.traffic_news_articles news
                LEFT JOIN public.traffic_article_publication publication
                    ON publication.article_id = news.id
                ORDER BY news.created_at DESC, news.id DESC
                LIMIT %s
                """,
                (limit,)
            )
            rows = cursor.fetchall()

    return [
        {
            "id": row[0],
            "title": row[1],
            "retrieved_at": row[2].isoformat(),
            "status": row[3] if row[3] is not None else "published",
            "legacy": row[3] is None,
            "created_at": row[4].isoformat()
        }
        for row in rows
    ]


# F20: 같은 트랜잭션에서 상태 변경과 변경 이력을 기록합니다.
def change_article_publication_status(article_id, target_status, changed_by):
    from app.operation_policies import publication_transition_allowed

    with get_database_connection() as connection:
        with connection.cursor() as cursor:
            # 기존 공개 기사는 상태 기록이 없을 수 있습니다.
            cursor.execute(
                """
                SELECT id FROM public.traffic_news_articles
                WHERE id = %s FOR UPDATE
                """,
                (article_id,)
            )
            if cursor.fetchone() is None:
                return None

            cursor.execute(
                """
                SELECT status FROM public.traffic_article_publication
                WHERE article_id = %s FOR UPDATE
                """,
                (article_id,)
            )
            current_row = cursor.fetchone()
            previous = current_row[0] if current_row else "published"

            if not publication_transition_allowed(previous, target_status):
                raise ValueError("허용되지 않는 기사 상태 변경입니다.")

            if current_row:
                cursor.execute(
                    """
                    UPDATE public.traffic_article_publication
                    SET status = %s, changed_by = %s, changed_at = now()
                    WHERE article_id = %s
                    """,
                    (target_status, str(changed_by), article_id)
                )
            else:
                cursor.execute(
                    """
                    INSERT INTO public.traffic_article_publication
                        (article_id, status, changed_by)
                    VALUES (%s, %s, %s)
                    """,
                    (article_id, target_status, str(changed_by))
                )

            cursor.execute(
                """
                INSERT INTO public.traffic_article_publication_events
                    (article_id, old_status, new_status, changed_by, note)
                VALUES (%s, %s, %s, %s, 'admin_transition')
                """,
                (article_id, previous, target_status, str(changed_by))
            )

    return {
        "article_id": article_id,
        "old_status": previous,
        "status": target_status
    }
