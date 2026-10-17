
import asyncio
from datetime import datetime
from zoneinfo import ZoneInfo

from app.traffic_analysis import analyze_seoul_routes
from app.overview_briefing import create_news_briefing
from app.news_database import save_news_article


async def main():

    print("===== 교통 뉴스 Supabase 저장 테스트 =====")

    # 1. 카카오 API로 서울 주요 경로 조회
    analysis_results = await analyze_seoul_routes()

    # 2. 세 경로를 모두 조회했는지 확인
    if len(analysis_results) != 3:
        print("조회한 경로가 3개가 아니므로 저장을 중단합니다.")
        return

    # 3. 뉴스 기사 생성
    news = create_news_briefing(analysis_results)

    # 4. 조회 완료 시각 기록
    retrieved_at = datetime.now(
        ZoneInfo("Asia/Seoul")
    ).isoformat()

    # 5. 데이터베이스에 저장할 데이터 구성
    news_data = {
        "title": news["title"],
        "lead": news["lead"],
        "body": news["body"],
        "scope_notice": news["scope_notice"],
        "analyzed_route_count": len(analysis_results),
        "routes": analysis_results,
        "retrieved_at": retrieved_at
    }

    print()
    print("생성된 뉴스 제목:")
    print(news_data["title"])

    print()
    print("분석한 경로 수:", len(analysis_results))

    # 6. Supabase에 저장
    try:
        save_result = save_news_article(news_data)

        print()
        print("===== 저장 성공 =====")
        print("뉴스 기사 ID:", save_result["article_id"])
        print("저장된 경로 수:", save_result["saved_route_count"])
        print("저장 결과:", save_result["message"])

    except Exception as error:

        print()
        print("===== 저장 실패 =====")
        print("오류 유형:", type(error).__name__)
        print("오류 내용:", error)


if __name__ == "__main__":
    asyncio.run(main())
