
import asyncio

from app.kakao_api import (
    KakaoApiError,
    find_place,
    get_car_route,
    summarize_route
)


# 1. 분석할 서울 주요 이동 경로
SEOUL_ROUTES = [
    ("서울역", "잠실역"),
    ("광화문", "강남역"),
    ("여의도역", "잠실역")
]


# 2. 하나의 경로에 대한 교통정보 분석
async def analyze_one_route(start_name, end_name):

    # 카카오 API로 출발지와 목적지 검색
    start_place = await find_place(start_name)
    end_place = await find_place(end_name)

    # 자동차 경로 조회
    route = await get_car_route(
        start_place,
        end_place
    )

    # 교통정보 정리
    route_data = summarize_route(route)

    roads = route_data["roads"]

    # 정체 또는 지체 상태인 구간 추출
    congested_roads = []

    for road in roads:
        traffic_state = road.get("traffic_state")

        if traffic_state in [1, 2]:
            congested_roads.append(road)

    # 정체·지체 구간의 거리 합계
    congested_distance = 0

    for road in congested_roads:
        road_distance = road.get("distance_m")

        if road_distance is not None:
            congested_distance += road_distance

    # 결과를 딕셔너리로 반환
    return {
        "start": start_place["name"],
        "end": end_place["name"],
        "distance_m": route_data["total_distance_m"],
        "duration_seconds": route_data["total_duration_seconds"],
        "total_road_count": len(roads),
        "congested_count": len(congested_roads),
        "congested_distance_m": congested_distance
    }


# 3. 서울 주요 경로 전체 분석
async def analyze_seoul_routes():

    analysis_results = []

    for start_name, end_name in SEOUL_ROUTES:

        print()
        print(f"조회 중: {start_name} → {end_name}")

        try:
            result = await analyze_one_route(
                start_name,
                end_name
            )

            analysis_results.append(result)

            print("조회 성공")

        except KakaoApiError as error:
            print("조회 실패:", error.message)

    return analysis_results


# 4. 분석 결과 출력
def display_results(analysis_results):

    print()
    print("===== 서울 주요 경로 교통정보 =====")

    for result in analysis_results:

        print()
        print("------------------------------")

        print(
            "경로:",
            result["start"],
            "→",
            result["end"]
        )

        distance = result["distance_m"]
        duration = result["duration_seconds"]

        if distance is not None:
            print(
                "이동 거리:",
                round(distance / 1000, 2),
                "km"
            )

        if duration is not None:
            print(
                "예상 시간:",
                round(duration / 60, 1),
                "분"
            )

        print(
            "전체 도로 구간:",
            result["total_road_count"],
            "개"
        )

        print(
            "정체·지체 구간:",
            result["congested_count"],
            "개"
        )

        print(
            "정체·지체 구간 거리 합계:",
            result["congested_distance_m"],
            "m"
        )


# 5. 프로그램 실행
async def main():

    results = await analyze_seoul_routes()

    display_results(results)


if __name__ == "__main__":
    asyncio.run(main())
