"""M01/M02 공통 메뉴: 서버 정적 파일·페이지 연결 회귀 테스트."""
import unittest

from fastapi.testclient import TestClient
from app.main import app


class SharedNavigationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    @classmethod
    def tearDownClass(cls):
        cls.client.close()

    def test_navigation_assets(self):
        for asset, media_type in [
            ("/static/navigation.css", "text/css"),
            ("/static/navigation.js", "javascript"),
        ]:
            with self.subTest(asset=asset):
                response = self.client.get(asset)
                self.assertEqual(response.status_code, 200)
                self.assertIn(media_type, response.headers.get("content-type", ""))

    def test_all_pages_have_shared_navigation(self):
        for path in ("/", "/map", "/news", "/admin"):
            with self.subTest(path=path):
                response = self.client.get(path)
                self.assertEqual(response.status_code, 200)
                self.assertIn('id="sharedNavigation"', response.text)
                self.assertIn('/static/navigation.css', response.text)
                self.assertIn('/static/navigation.js', response.text)

    def test_news_history_anchor(self):
        response = self.client.get("/news")
        self.assertEqual(response.status_code, 200)
        self.assertIn('id="historySection"', response.text)
        self.assertIn('id="trafficDashboard"', response.text)

    def test_existing_admin_guard(self):
        for route in ("/api/admin/me", "/api/admin/news/generate"):
            with self.subTest(route=route):
                response = self.client.get(route) if route.endswith("/me") else self.client.post(route)
                self.assertEqual(response.status_code, 401)


if __name__ == "__main__":
    unittest.main()
