
from datetime import datetime
from decimal import Decimal

from dotenv import load_dotenv

from app.database import get_database_connection


# .env에 저장된 데이터베이스 연결 설정 읽기
load_dotenv()


# 뉴스 기사와 경로 정보를 하나의 작업으로 저장
def save_news_article(news_data):

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
            cursor.execute(
                """
                INSERT INTO public.traffic_news_articles (
                    title,
                    lead,
                    body,
                    scope_notice,
                    analyzed_route_count,
                    retrieved_at
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
        "message": "뉴스 기사와 경로 정보 저장 완료"
    }
