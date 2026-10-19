"""외부 API 요청 없이 카카오 경로 엔드포인트를 확인합니다."""

from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient

from app.main import app
from app.kakao_api import KakaoApiError, summarize_route

client = TestClient(app)
START = {"name": "서울역", "longitude": 126.97, "latitude": 37.55}
END = {"name": "잠실역", "longitude": 127.10, "latitude": 37.51}
ROUTE = {
    "summary": {"distance": 15000, "duration": 1800},
    "sections": [{"roads": [{
        "name": "테스트 도로", "distance": 1000,
        "traffic_speed": 22, "traffic_state": 2,
        "vertexes": [126.97, 37.55, 126.98, 37.56],
    }]}],
}


def test_home_and_map():
    assert client.get("/").status_code == 200
    assert client.get("/map").status_code == 200


def test_valid_route():
    with patch("app.main.find_place", new_callable=AsyncMock) as find, \
         patch("app.main.get_car_route", new_callable=AsyncMock) as directions:
        find.side_effect = [START, END]
        directions.return_value = ROUTE
        response = client.get("/api/route", params={
            "origin": "서울역", "destination": "잠실역"
        })
    assert response.status_code == 200
    result = response.json()
    assert result["total_duration_seconds"] == 1800
    assert result["roads"][0]["traffic_speed_kmh"] == 22
    assert result["origin"]["name"] == "서울역"


def test_missing_destination():
    assert client.get("/api/route", params={"origin": "서울역"}).status_code == 422


def test_kakao_error():
    with patch("app.main.find_place", new_callable=AsyncMock) as find:
        find.side_effect = KakaoApiError("장소 없음", 404)
        response = client.get("/api/route", params={
            "origin": "서울역", "destination": "잠실역"
        })
    assert response.status_code == 404


def test_summary_without_sections():
    assert summarize_route({"summary": {"distance": 100, "duration": 20}})["roads"] == []
