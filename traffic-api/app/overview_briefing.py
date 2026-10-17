
import asyncio

from datetime import datetime
from zoneinfo import ZoneInfo

from app.traffic_analysis import analyze_seoul_routes


# 여러 경로의 교통정보를 브리핑으로 변환
def create_overview_briefing(analysis_results):

    if not analysis_results:
        return "조회된 교통정보가 없습니다."

    briefing_sentences = []

    briefing_sentences.append(
        f"서울 주요 이동 경로 {len(analysis_results)}곳의 "
        "교통 상황을 살펴보겠습니다."
    )

    for result in analysis_results:

        start_name = result["start"]
        end_name = result["end"]

        distance_m = result["distance_m"]
        duration_seconds = result["duration_seconds"]

        congested_count = result["congested_count"]
        congested_distance = result["congested_distance_m"]

        # 전체 거리와 예상 시간
        if distance_m is None or duration_seconds is None:
            briefing_sentences.append(
                f"{start_name}에서 {end_name}까지의 "
                "이동 거리 또는 예상 시간 정보가 없습니다."
            )
            continue

        distance_km = distance_m / 1000
        duration_minutes = duration_seconds / 60

        # 정체·지체 구간 거리 비율
        if distance_m > 0:
            congestion_ratio = (
                congested_distance / distance_m * 100
            )
        else:
            congestion_ratio = 0

        sentence = (
            f"{start_name}에서 {end_name}까지의 "
            f"이동 거리는 약 {distance_km:.1f}km이며, "
            f"예상 소요 시간은 약 {duration_minutes:.1f}분입니다. "
            f"정체 또는 지체 상태인 도로 구간은 "
            f"{congested_count}개이며, "
            f"해당 구간의 거리 합계는 약 "
            f"{congested_distance / 1000:.1f}km입니다. "
            f"이는 전체 이동 거리의 약 "
            f"{congestion_ratio:.1f}%에 해당합니다."
        )

        briefing_sentences.append(sentence)

    briefing_sentences.append(
        "이번 분석은 카카오 자동차 길찾기로 조회한 "
        "세 경로에 한정됩니다. "
        "서울 전체 도로의 교통 상황을 "
        "대표하는 결과는 아닙니다."
    )

    return "\n\n".join(briefing_sentences)


# 프로그램 실행
async def main():

    print("서울 주요 경로 교통정보를 조회합니다.")

    # 기존 traffic_analysis.py의 함수 재사용
    analysis_results = await analyze_seoul_routes()

    # 종합 브리핑 생성
    briefing_text = create_overview_briefing(
        analysis_results
    )

    # 브리핑 생성 시각
    current_time = datetime.now(
        ZoneInfo("Asia/Seoul")
    )

    print("\n===== 서울 주요 경로 종합 브리핑 =====")
    print(
        "생성 시각:",
        current_time.strftime("%Y-%m-%d %H:%M:%S")
    )

    print()
    print(briefing_text)


if __name__ == "__main__":
    asyncio.run(main())

# 6. 경로별 정체·지체 거리 비율 계산
def calculate_congestion_ratio(route_data):

    total_distance = route_data.get("distance_m")
    congested_distance = route_data.get("congested_distance_m")

    if total_distance is None or total_distance <= 0:
        return None

    if congested_distance is None or congested_distance < 0:
        return None

    if congested_distance > total_distance:
        return None

    return congested_distance / total_distance * 100


# 7. 경로별 뉴스 브리핑 생성
def create_news_briefing(analysis_results):

    if not analysis_results:
        return {
            "title": "교통정보를 조회하지 못했습니다.",
            "lead": "분석 가능한 자동차 경로가 없습니다.",
            "body": "",
            "scope_notice": "조회 결과가 없어 비교할 수 없습니다."
        }

    # 비교할 수 있는 경로만 정리
    valid_routes = []

    for route_data in analysis_results:

        congestion_ratio = calculate_congestion_ratio(
            route_data
        )

        if congestion_ratio is None:
            continue

        valid_routes.append({
            "start": route_data["start"],
            "end": route_data["end"],
            "distance_m": route_data["distance_m"],
            "duration_seconds": route_data.get("duration_seconds"),
            "congested_count": route_data["congested_count"],
            "congested_distance_m": route_data["congested_distance_m"],
            "congestion_ratio": congestion_ratio
        })

    if not valid_routes:
        return {
            "title": "교통정보 비교 자료가 부족합니다.",
            "lead": "정체·지체 거리 비율을 계산할 수 없습니다.",
            "body": "",
            "scope_notice": "유효한 경로 거리 정보가 필요합니다."
        }

    # 정체·지체 거리 비율이 높은 순서로 정렬
    valid_routes.sort(
        key=lambda route: route["congestion_ratio"],
        reverse=True
    )

    highest_route = valid_routes[0]

    # 동률 가능성을 고려하여 표시
    highest_ratio = highest_route["congestion_ratio"]

    highest_routes = [
        route for route in valid_routes
        if abs(route["congestion_ratio"] - highest_ratio) < 0.05
    ]

    # 뉴스 제목 생성
    if len(highest_routes) > 1:
        title = (
            f"서울 주요 {len(valid_routes)}개 경로 중 "
            "정체·지체 거리 비율 공동 최고 구간 확인"
        )
    else:
        title = (
            f"서울 주요 {len(valid_routes)}개 경로 중 "
            f"{highest_route['start']}~{highest_route['end']}, "
            "정체·지체 거리 비율 가장 높아"
        )

    # 뉴스 리드 생성
    if len(valid_routes) == 1:
        lead = (
            "조회한 자동차 이동 경로 1곳에서 "
            f"정체·지체 거리 비율이 "
            f"{highest_ratio:.1f}%로 나타났습니다."
        )
    elif len(highest_routes) > 1:
        lead = (
            f"서울 주요 자동차 이동 경로 {len(valid_routes)}곳을 "
            "분석한 결과, 복수의 경로에서 "
            f"정체·지체 거리 비율이 약 {highest_ratio:.1f}%로 "
            "비슷하게 나타났습니다."
        )
    else:
        lead = (
            f"서울 주요 자동차 이동 경로 {len(valid_routes)}곳을 "
            "분석한 결과, "
            f"{highest_route['start']}에서 "
            f"{highest_route['end']}까지의 경로에서 "
            f"정체·지체 거리 비율이 {highest_ratio:.1f}%로 "
            "가장 높게 나타났습니다."
        )

    # 경로별 뉴스 본문 생성
    body_sentences = []

    for route in valid_routes:

        distance_km = route["distance_m"] / 1000

        duration_seconds = route["duration_seconds"]

        if duration_seconds is None:
            duration_text = "예상 소요 시간은 확인되지 않았습니다."
        else:
            duration_minutes = duration_seconds / 60
            duration_text = (
                f"예상 소요 시간은 약 {duration_minutes:.1f}분입니다."
            )

        sentence = (
            f"{route['start']}에서 {route['end']}까지의 "
            f"이동 거리는 약 {distance_km:.1f}km이며, "
            f"{duration_text} "
            f"정체·지체 구간은 {route['congested_count']}개, "
            f"해당 구간의 거리 합계는 "
            f"약 {route['congested_distance_m'] / 1000:.1f}km입니다. "
            f"이는 전체 경로 거리의 "
            f"{route['congestion_ratio']:.1f}%에 해당합니다."
        )

        body_sentences.append(sentence)

    body = "\n\n".join(body_sentences)

    scope_notice = (
        "이번 분석은 카카오 자동차 길찾기로 조회한 "
        f"{len(valid_routes)}개 경로에 한정됩니다. "
        "서울 전체 도로의 교통 상황을 대표하지 않으며, "
        "정체·지체 거리 비율만으로 전체 교통 혼잡도를 "
        "판단할 수는 없습니다."
    )

    return {
        "title": title,
        "lead": lead,
        "body": body,
        "scope_notice": scope_notice
    }
