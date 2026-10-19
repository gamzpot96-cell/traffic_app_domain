
"""카카오 기반 서울 교통 경로 조회 서비스."""
import os
import httpx

from pydantic import BaseModel
from dotenv import load_dotenv
import logging
from app.news_database import (
    get_saved_news_articles,
    get_saved_news_article
)
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
from fastapi import FastAPI, HTTPException, Query, Depends
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from starlette.concurrency import run_in_threadpool

from app.kakao_api import (
    KakaoApiError,
    find_place,
    get_car_route,
    summarize_route
)

from app.briefing import create_traffic_briefing
from app.traffic_analysis import analyze_seoul_routes
from app.overview_briefing import (
    create_overview_briefing,
    create_news_briefing
)
from app.admin_auth import require_admin
from app.news_database import save_news_article
from app.news_drafts import (
    create_draft_token,
    verify_draft_token,
    DRAFT_TTL_SECONDS
)

# 로그 설정
logger = logging.getLogger(__name__)

# 프로젝트 폴더 경로
ROOT = Path(__file__).resolve().parent.parent
load_dotenv()

# FastAPI 애플리케이션 생성
app = FastAPI(
    title="서울 도로교통 브리핑 - Kakao",
    description="카카오 자동차 경로 교통정보 및 자동 브리핑 서비스",
    version="0.3.0"
)

# 공통 메뉴 CSS/JavaScript 등 정적 자산을 로컬에서도 제공합니다.
# 기존 페이지와 /api 경로는 변경하지 않습니다.
app.mount("/static", StaticFiles(directory=ROOT / "static"), name="static")


# 메인 페이지
@app.get("/")
async def home():
    return FileResponse(ROOT / "static" / "index.html")


# 지도 페이지
@app.get("/map")
async def map_page():
    return FileResponse(ROOT / "static" / "map.html")


# 자동차 경로 및 교통 브리핑 조회
@app.get("/api/route")
async def route_search(
    origin: str = Query(
        ...,
        min_length=2,
        max_length=100,
        description="출발지 장소명"
    ),
    destination: str = Query(
        ...,
        min_length=2,
        max_length=100,
        description="목적지 장소명"
    )
):

    try:
        # 1. 출발지 검색
        start_place = await find_place(origin)

        # 2. 목적지 검색
        end_place = await find_place(destination)

        # 3. 카카오 자동차 경로 조회
        route = await get_car_route(
            start_place,
            end_place
        )

        # 4. 교통정보 정리
        route_information = {
            "origin": start_place,
            "destination": end_place,
            **summarize_route(route)
        }

        # 5. 교통 브리핑 생성
        traffic_briefing = create_traffic_briefing(
            route_information
        )

        # 6. 교통정보와 브리핑 반환
        return {
            **route_information,
            "briefing": traffic_briefing
        }

    except KakaoApiError as error:

        logger.warning(
            "카카오 경로 조회 실패 (%s): %s",
            error.status_code,
            error.message
        )

        raise HTTPException(
            status_code=error.status_code,
            detail=error.message
        ) from error

# 서울 주요 경로 종합 교통 브리핑 API
@app.get("/api/briefing/overview")
async def get_overview_briefing():

    # 1. 서울 주요 경로 3곳 조회
    analysis_results = await analyze_seoul_routes()

    # 2. 성공적으로 조회한 경로가 있는지 확인
    if not analysis_results:
        raise HTTPException(
            status_code=503,
            detail="교통정보를 가져오지 못했습니다."
        )

    # 3. 종합 교통 브리핑 생성
    briefing_text = create_overview_briefing(
        analysis_results
    )

    # 4. JSON 형식으로 반환
    return {
        "title": "서울 주요 경로 종합 교통 브리핑",
        "analyzed_route_count": len(analysis_results),
        "routes": analysis_results,
        "briefing": briefing_text,
        "scope_notice": (
            "선택한 자동차 경로의 교통정보이며 "
            "서울 전체 도로의 상황을 대표하지 않습니다."
        )
    }


# 서울 주요 경로 뉴스형 교통 브리핑 API
@app.get("/api/briefing/news")
async def get_news_briefing():

    # 1. 서울 주요 이동 경로 조회
    analysis_results = await analyze_seoul_routes()

    # 2. 조회가 완료된 시각 기록 (한국 시간)
    retrieved_at = datetime.now(
        ZoneInfo("Asia/Seoul")
    )

    # 3. 조회 결과 확인
    if not analysis_results:
        raise HTTPException(
            status_code=503,
            detail="뉴스 브리핑을 생성할 교통정보가 없습니다."
        )

    # 4. 뉴스 제목, 리드, 본문 생성
    news = create_news_briefing(analysis_results)

    # 5. JSON 응답 반환
    return {
        "title": news["title"],
        "lead": news["lead"],
        "body": news["body"],
        "scope_notice": news["scope_notice"],
        "analyzed_route_count": len(analysis_results),
        "routes": analysis_results,
        "retrieved_at": retrieved_at.isoformat()
    }


# 뉴스형 교통 브리핑 웹페이지
@app.get("/news")
async def news_page():

    return FileResponse(
        ROOT / "static" / "news.html"
    )

# Supabase에 저장된 뉴스 목록 조회 API
@app.get("/api/news/history")
def get_news_history():

    try:
        articles = get_saved_news_articles(limit=10)

        return {
            "count": len(articles),
            "articles": articles
        }

    except Exception:
        logger.exception("저장된 뉴스 목록 조회 실패")

        raise HTTPException(
            status_code=503,
            detail="저장된 뉴스 목록을 가져오지 못했습니다."
        )

# 저장된 뉴스 상세 조회 API
@app.get("/api/news/history/{article_id}")
def get_news_history_detail(article_id: int):

    if article_id < 1:
        raise HTTPException(
            status_code=400,
            detail="기사 ID는 1 이상의 정수여야 합니다."
        )

    try:
        article = get_saved_news_article(article_id)

    except Exception as error:
        logger.exception("뉴스 상세 조회 실패")

        raise HTTPException(
            status_code=503,
            detail="저장된 뉴스를 불러오지 못했습니다."
        ) from error

    if article is None:
        raise HTTPException(
            status_code=404,
            detail="해당 기사를 찾을 수 없습니다."
        )

    return article

# 관리자 로그인 상태 확인 API
@app.get("/api/admin/me")
async def get_admin_profile(
    admin_user=Depends(require_admin)
):

    return {
        "authenticated": True,
        "is_admin": True,
        "user_id": admin_user["id"]
    }

# 관리자 로그인 요청 데이터
class AdminLoginRequest(BaseModel):
    email: str
    password: str


# Supabase Auth를 통한 로그인
@app.post("/api/admin/login")
async def admin_login(login_data: AdminLoginRequest):

    supabase_url = os.getenv("SUPABASE_URL", "").rstrip("/")
    supabase_key = os.getenv("SUPABASE_ANON_KEY", "")

    if not supabase_url or not supabase_key:
        raise HTTPException(
            status_code=503,
            detail="Supabase 인증 설정이 없습니다."
        )

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:

            response = await client.post(
                supabase_url + "/auth/v1/token",
                params={"grant_type": "password"},
                headers={
                    "apikey": supabase_key,
                    "Content-Type": "application/json"
                },
                json={
                    "email": login_data.email,
                    "password": login_data.password
                }
            )

    except httpx.RequestError:
        raise HTTPException(
            status_code=503,
            detail="인증 서버에 연결할 수 없습니다."
        )

    if response.status_code != 200:
        raise HTTPException(
            status_code=401,
            detail="이메일 또는 비밀번호를 확인하세요."
        )

    login_result = response.json()

    # 로그인 성공 후 실제 관리자 UID 확인
    admin_user_id = os.getenv("ADMIN_USER_ID", "")
    logged_in_user = login_result.get("user", {})
    logged_in_user_id = logged_in_user.get("id", "")

    import secrets

    if (
        not admin_user_id
        or not isinstance(logged_in_user_id, str)
        or not secrets.compare_digest(
            logged_in_user_id,
            admin_user_id
        )
    ):
        raise HTTPException(
            status_code=403,
            detail="관리자 권한이 없습니다."
        )

    return {
        "message": "관리자 로그인 성공",
        "access_token": login_result["access_token"],
        "token_type": "bearer",
        "expires_in": login_result.get("expires_in")
    }

# 관리자 로그인 웹페이지
@app.get("/admin")
async def admin_page():

    return FileResponse(
        ROOT / "static" / "admin.html"
    )



# 관리자가 저장할 뉴스를 생성하고, 저장용 서명 증표를 발급
@app.post("/api/admin/news/generate")
async def generate_admin_news(admin_user=Depends(require_admin)):
    analysis_results = await analyze_seoul_routes()

    # 데이터가 일부만 수집되면 세 경로 뉴스로 저장하지 않습니다.
    if len(analysis_results) != 3:
        raise HTTPException(
            status_code=503,
            detail="세 경로가 모두 조회되지 않아 기사 생성을 중단했습니다."
        )

    retrieved_at = datetime.now(ZoneInfo("Asia/Seoul")).isoformat()
    article = create_news_briefing(analysis_results)

    news_data = {
        "title": article["title"],
        "lead": article["lead"],
        "body": article["body"],
        "scope_notice": article["scope_notice"],
        "analyzed_route_count": len(analysis_results),
        "retrieved_at": retrieved_at,
        "routes": analysis_results
    }

    try:
        draft_token, generation_id = create_draft_token(
            news_data, admin_user["id"]
        )
    except (RuntimeError, ValueError):
        logger.exception("기사 저장용 서명 증표 생성 실패")
        raise HTTPException(
            status_code=503,
            detail="기사 서명 설정을 확인할 수 없습니다."
        )

    return {
        "news": news_data,
        "draft_token": draft_token,
        "generation_id": generation_id,
        "expires_in": DRAFT_TTL_SECONDS
    }


class AdminNewsSaveRequest(BaseModel):
    draft_token: str


# 관리자가 확인한 동일한 기사 초안만 서버에서 검증하고 저장
@app.post("/api/admin/news/save")
async def save_admin_news(
    save_request: AdminNewsSaveRequest,
    admin_user=Depends(require_admin)
):
    try:
        generation_id, news_data = verify_draft_token(
            save_request.draft_token, admin_user["id"]
        )
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="기사 저장 증표가 만료됐거나 올바르지 않습니다. 새로 생성하세요."
        )
    except RuntimeError:
        raise HTTPException(
            status_code=503,
            detail="기사 서명 설정을 확인할 수 없습니다."
        )

    try:
        # psycopg 동기 호출은 요청 이벤트 루프 밖에서 수행
        return await run_in_threadpool(
            save_news_article, news_data, generation_id
        )
    except (ValueError, KeyError, TypeError):
        logger.exception("저장 데이터 유효성 검사 실패")
        raise HTTPException(
            status_code=400,
            detail="기사 데이터가 올바르지 않습니다."
        )
    except Exception:
        logger.exception("관리자 뉴스 DB 저장 실패")
        raise HTTPException(
            status_code=503,
            detail="기사 저장 중 데이터베이스 오류가 발생했습니다."
        )
