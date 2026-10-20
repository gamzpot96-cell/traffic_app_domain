"""D01 지도 배경: 키 유무에 따른 고해상도 타일 선택과 기존 기능 보존."""
import os
import unittest
from unittest.mock import patch
from fastapi.testclient import TestClient

from app.main import app


class BasemapConfigTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    @classmethod
    def tearDownClass(cls):
        cls.client.close()

    def test_missing_key_uses_existing_osm(self):
        with patch.dict(os.environ, {"CARTO_BASEMAP_KEY": ""}):
            response = self.client.get("/api/map/basemap-config")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"provider": "osm"})

    def test_valid_public_browser_key_uses_real_2x_tiles(self):
        with patch.dict(os.environ, {"CARTO_BASEMAP_KEY": "local-test-public-key"}):
            response = self.client.get("/api/map/basemap-config")
        self.assertEqual(response.status_code, 200)
        result = response.json()
        self.assertEqual(result["provider"], "carto")
        self.assertIn("/rastertiles/voyager/{z}/{x}/{y}@2x.png?key=", result["tile_url"])
        self.assertTrue(result["tile_url"].endswith("local-test-public-key"))
        self.assertNotIn("KAKAO", response.text)
        self.assertNotIn("SUPABASE", response.text)

    def test_invalid_key_falls_back_without_leaking(self):
        with patch.dict(os.environ, {"CARTO_BASEMAP_KEY": "bad\nkey"}):
            response = self.client.get("/api/map/basemap-config")
        self.assertEqual(response.json(), {"provider": "osm"})
        self.assertNotIn("bad", response.text)

    def test_legacy_page_preserves_retina_tiles_and_osm_fallback(self):
        response = self.client.get("/static/legacy-map.html")
        self.assertEqual(response.status_code, 200)
        page = response.text
        for expected in (
            'id="mapBasemapStatus"', "configureRetinaBasemap();",
            'fetch("/api/map/basemap-config")',
            "tilePixelRatio: 2", 'new ol.source.XYZ({',
            "backgroundLayer.setSource(retinaSource)",
            "backgroundLayer.setSource(standardOsmSource)",
            "new ol.source.OSM()", 'carto.com/attribution/',
            'openstreetmap.org/copyright',
            'id="savedArticlePanel"', 'id="mapRouteForm"',
            'id="map"', 'routeSource.clear()', 'data.roads.forEach(drawRoad)',
        ):
            with self.subTest(expected=expected):
                self.assertIn(expected, page)


if __name__ == "__main__":
    unittest.main()
