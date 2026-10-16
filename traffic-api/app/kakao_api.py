"""Kakao Local API + Kakao Mobility 자동차 길찾기 API 연동."""

import os

import httpx
from dotenv import load_dotenv

load_dotenv()

LOCAL_SEARCH_URL = "https://dapi.kakao.com/v2/local/search/keyword.json"
DIRECTIONS_URL = "https://apis-navi.kakaomobility.com/v1/directions"


class KakaoApiError(Exception):
    def __init__(self, message: str, status_code: int = 502):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


def get_kakao_headers():
    api_key = os.getenv("KAKAO_REST_API_KEY", "").strip()
    if not api_key:
        raise KakaoApiError("KAKAO_REST_API_KEY 환경변수가 설정되지 않았습니다.", 500)
    return {"Authorization": f"KakaoAK {api_key}"}


async def request_kakao_json(url: str, parameters: dict) -> dict:
    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.get(
                url, params=parameters, headers=get_kakao_headers()
            )
            response.raise_for_status()
            data = response.json()
    except httpx.TimeoutException as error:
        raise KakaoApiError("카카오 API 요청 시간이 초과되었습니다.", 504) from error
    except httpx.HTTPStatusError as error:
        status_code = error.response.status_code
        if status_code in (401, 403):
            raise KakaoApiError(
                "카카오 API 인증키 또는 자동차 길찾기 이용 권한을 확인하세요.", 502
            ) from error
        raise KakaoApiError(f"카카오 API HTTP 오류: {status_code}") from error
    except (httpx.RequestError, ValueError) as error:
        raise KakaoApiError("카카오 API 응답을 처리할 수 없습니다.") from error

    if not isinstance(data, dict):
        raise KakaoApiError("카카오 API 응답 형식이 올바르지 않습니다.")
    return data


async def find_place(place_name: str) -> dict:
    data = await request_kakao_json(
        LOCAL_SEARCH_URL, {"query": place_name}
    )
    documents = data.get("documents")
    if not isinstance(documents, list):
        raise KakaoApiError("장소 검색 응답 형식이 올바르지 않습니다.")
    if not documents:
        raise KakaoApiError(f"'{place_name}'에 해당하는 장소가 없습니다.", 404)

    place = documents[0]
    try:
        return {
            "name": place.get("place_name") or place_name,
            "longitude": float(place["x"]),
            "latitude": float(place["y"]),
        }
    except (KeyError, TypeError, ValueError) as error:
        raise KakaoApiError("검색된 장소의 좌표가 올바르지 않습니다.") from error


async def get_car_route(start_place: dict, end_place: dict) -> dict:
    parameters = {
        "origin": f"{start_place['longitude']},{start_place['latitude']}",
        "destination": f"{end_place['longitude']},{end_place['latitude']}",
        "priority": "RECOMMEND",
        "summary": "false",
    }
    data = await request_kakao_json(DIRECTIONS_URL, parameters)
    routes = data.get("routes")
    if not isinstance(routes, list) or not routes:
        raise KakaoApiError("검색된 자동차 경로가 없습니다.", 404)

    route = routes[0]
    if route.get("result_code") != 0:
        raise KakaoApiError(
            route.get("result_msg") or "자동차 경로 검색에 실패했습니다.", 404
        )
    return route


def summarize_route(route: dict) -> dict:
    """응답의 도로 구간 정보를 웹 화면에 필요한 값으로 정리합니다."""
    summary = route.get("summary") or {}
    roads = []
    for section in route.get("sections") or []:
        for road in section.get("roads") or []:
            roads.append({
                "name": road.get("name") or "이름 없는 도로",
                "distance_m": road.get("distance"),
                "traffic_speed_kmh": road.get("traffic_speed"),
                "traffic_state": road.get("traffic_state"),
                "vertexes": road.get("vertexes") or [],
            })
    return {
        "total_distance_m": summary.get("distance"),
        "total_duration_seconds": summary.get("duration"),
        "roads": roads,
        "scope_notice": "카카오 자동차 길찾기 경로의 교통정보이며, 서울 전체 도로의 현황을 뜻하지 않습니다.",
    }
