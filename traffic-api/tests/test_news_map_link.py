"""F23 뉴스-지도 연동 1단계: 링크 생성 구조 검증 (외부 API/DB 사용 없음)."""
import unittest

from fastapi.testclient import TestClient

from app.main import app


class NewsMapLinkTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    @classmethod
    def tearDownClass(cls):
        cls.client.close()

    def test_saved_article_route_container_present(self):
        response = self.client.get("/news")
        self.assertEqual(response.status_code, 200)
        self.assertIn('id="savedArticleRoutes"', response.text)
        self.assertIn('id="savedArticleRouteList"', response.text)
        self.assertIn("displaySavedArticleRouteLinks(article);", response.text)

    def test_route_index_and_article_id_link_contract(self):
        response = self.client.get("/news")
        self.assertIn('"/map?article_id="', response.text)
        self.assertIn('"&route_index="', response.text)
        self.assertIn("encodeURIComponent(String(article.id))", response.text)
        self.assertIn("encodeURIComponent(String(index))", response.text)

    def test_missing_article_routes_do_not_leave_stale_links(self):
        response = self.client.get("/news")
        self.assertIn("displaySavedArticleRouteLinks(null);", response.text)
        self.assertIn("section.hidden = true;", response.text)
        self.assertIn("list.replaceChildren();", response.text)


if __name__ == "__main__":
    unittest.main()
