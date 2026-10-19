"""카카오맵 SDK 전환: 키 설정·기존 경로/기사 기능 회귀. 실키/DB 필요 없음."""
import os
import unittest
from unittest.mock import patch
from fastapi.testclient import TestClient
from app.main import app


class KakaoMapTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    @classmethod
    def tearDownClass(cls):
        cls.client.close()

    def test_missing_javascript_key(self):
        with patch.dict(os.environ, {"KAKAO_MAP_JS_KEY": ""}):
            response = self.client.get("/api/map/sdk-config")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"provider": "unconfigured"})
        self.assertEqual(response.headers["cache-control"], "no-store")

    def test_valid_javascript_key_only(self):
        with patch.dict(os.environ, {"KAKAO_MAP_JS_KEY": "test-js-key"}):
            response = self.client.get("/api/map/sdk-config")
        self.assertEqual(response.json(), {"provider": "kakao", "javascript_key": "test-js-key"})
        self.assertNotIn("SUPABASE", response.text)
        self.assertNotIn("REST", response.text)

    def test_bad_javascript_key_falls_back(self):
        with patch.dict(os.environ, {"KAKAO_MAP_JS_KEY": "bad\nkey"}):
            response = self.client.get("/api/map/sdk-config")
        self.assertEqual(response.json(), {"provider": "unconfigured"})
        self.assertNotIn("bad", response.text)

    def test_kakao_sdk_and_legacy_recovery(self):
        response = self.client.get("/map")
        self.assertEqual(response.status_code, 200)
        source = response.text
        for piece in (
            "initializeKakaoMap();", 'fetch("/api/map/sdk-config"',
            "dapi.kakao.com/v2/maps/sdk.js?autoload=false&appkey=",
            "new kakao.maps.Map(", "new kakao.maps.ZoomControl()",
            "new kakao.maps.Polyline(", "new kakao.maps.Marker(",
            "new kakao.maps.LatLngBounds()", "kakaoMap.setBounds(bounds)",
            "strokeColor: roadColors[road.traffic_state] || \"#64748b\"",
            "new kakao.maps.LatLng(latitude, longitude)",
            "displayedPolylines.forEach(", "displayedMarkers.forEach(",
            'id="mapRecovery"', "/static/legacy-map.html",
            "window.location.search", "showMapError(",
        ):
            with self.subTest(piece=piece):
                self.assertIn(piece, source)

    def test_saved_article_and_manual_route_are_retained(self):
        source = self.client.get("/map").text
        for piece in (
            'query.get("article_id")', 'query.get("route_index")',
            'fetch("/api/news/history/"',
            'id="savedArticlePanel"',
            'id="savedArticleMetrics"',
            "loadSavedArticleRouteFromUrl();",
            'document.getElementById("mapRouteForm").addEventListener("submit"',
            'fetch("/api/route?" + params.toString())',
            "drawCurrentRoute(data);", "data.roads.forEach(",
            "selectedRoute.duration_seconds / 60",
            "현재 경로 새로 조회",
        ):
            with self.subTest(piece=piece):
                self.assertIn(piece, source)
        self.assertNotIn("routeSource.clear()", source)

    def test_legacy_map_still_accessible(self):
        response = self.client.get("/static/legacy-map.html?article_id=8&route_index=0")
        self.assertEqual(response.status_code, 200)
        self.assertIn("new ol.Map(", response.text)
        self.assertIn("loadSavedArticleRouteFromUrl();", response.text)


if __name__ == "__main__":
    unittest.main()
