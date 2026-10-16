"""카카오 기반 서울 교통 경로 조회 서비스."""

import logging
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse

from app.kakao_api import KakaoApiError, find_place, get_car_route, summarize_route

logger = logging.getLogger(__name__)
ROOT = Path(__file__).resolve().parent.parent

app = FastAPI(
    title="서울 도로교통 브리핑 - Kakao",
    description="카카오 장소 검색과 자동차 길찾기 결과를 기반으로 경로 교통정보를 제공합니다.",
    version="0.2.0",
)


@app.get("/")
async def home():
    return FileResponse(ROOT / "static" / "index.html")


@app.get("/map")
async def map_page():
    return FileResponse(ROOT / "static" / "map.html")


@app.get("/api/route")
async def route_search(
    origin: str = Query(..., min_length=2, max_length=100, description="출발지 장소명"),
    destination: str = Query(..., min_length=2, max_length=100, description="목적지 장소명"),
):
    """장소명을 좌표로 바꾼 뒤 자동차 경로의 교통정보를 조회합니다."""
    try:
        start_place = await find_place(origin)
        end_place = await find_place(destination)
        route = await get_car_route(start_place, end_place)
        return {
            "origin": start_place,
            "destination": end_place,
            **summarize_route(route),
        }
    except KakaoApiError as error:
        logger.warning("카카오 경로 조회 실패 (%s): %s", error.status_code, error.message)
        raise HTTPException(status_code=error.status_code, detail=error.message) from error
