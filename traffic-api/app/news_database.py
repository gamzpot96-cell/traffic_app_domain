
from datetime import datetime
from decimal import Decimal

from dotenv import load_dotenv

from app.database import get_database_connection


# .env에 저장된 데이터베이스 연결 설정 읽기
load_dotenv()


# 뉴스 기사와 경로 정보를 하나의 작업으로 저장
def save_news_article(news_data, generation_id=None):

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
