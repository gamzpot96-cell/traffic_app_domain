
"""카카오 기반 서울 교통 경로 조회 서비스."""

import logging
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse

from app.kakao_api import (
    KakaoApiError,
    find_place,
    get_car_route,
    summarize_route
)

from app.briefing import create_traffic_briefing


# 로그 설정
logger = logging.getLogger(__name__)

# 프로젝트 폴더 경로
ROOT = Path(__file__).resolve().parent.parent


# FastAPI 애플리케이션 생성
app = FastAPI(
    title="서울 도로교통 브리핑 - Kakao",
    description="카카오 자동차 경로 교통정보 및 자동 브리핑 서비스",
    version="0.3.0"
)


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
