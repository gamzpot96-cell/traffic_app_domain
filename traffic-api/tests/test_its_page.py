"""사용 종료된 ITS 기능이 노출되지 않는지 확인합니다."""
import unittest
from fastapi.testclient import TestClient
from app.main import app


class RetiredItsTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_its_page_is_not_served(self):
        self.assertEqual(self.client.get("/its").status_code, 404)

    def test_its_traffic_endpoint_is_not_served(self):
        self.assertEqual(self.client.get("/traffic", params={
            "min_x": 126.9, "max_x": 127.0,
            "min_y": 37.4, "max_y": 37.6,
        }).status_code, 404)

    def test_kakao_pages_are_preserved(self):
        for path in ("/", "/map", "/news", "/admin"):
            self.assertEqual(self.client.get(path).status_code, 200)

    def test_navigation_has_no_its_link(self):
        from pathlib import Path
        navigation = (Path(__file__).resolve().parent.parent / "static" / "navigation.js").read_text(encoding="utf-8")
        self.assertNotIn('href: "/its"', navigation)
