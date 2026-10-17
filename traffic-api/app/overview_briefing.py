
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
