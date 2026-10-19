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

    def test_map_supports_saved_article_query_parameters(self):
        response = self.client.get("/map")
        self.assertEqual(response.status_code, 200)
        self.assertIn('query.get("article_id")', response.text)
        self.assertIn('query.get("route_index")', response.text)
        self.assertIn('fetch("/api/news/history/"', response.text)
        self.assertIn('id="savedArticlePanel"', response.text)

    def test_map_does_not_auto_submit_route(self):
        response = self.client.get("/map")
        self.assertIn('if (articleIdText === null && routeIndexText === null) return;', response.text)
        self.assertIn('loadSavedArticleRouteFromUrl();', response.text)
        self.assertIn('document.getElementById("mapRouteForm").addEventListener("submit"', response.text)
        # 현재 경로 조회는 사용자의 폼 제출에만 연결됩니다.
        self.assertNotIn('document.getElementById("mapRouteForm").requestSubmit()', response.text)

    def test_map_retains_manual_search_and_failure_notice(self):
        response = self.client.get("/map")
        self.assertIn('id="origin"', response.text)
        self.assertIn('id="destination"', response.text)
        self.assertIn("해당 기사를 찾을 수 없습니다.", response.text)
        self.assertIn("아래에서 직접 경로를 검색할 수 있습니다.", response.text)
        self.assertIn('"/api/route?"', response.text)

    def test_missing_article_routes_do_not_leave_stale_links(self):
        response = self.client.get("/news")
        self.assertIn("displaySavedArticleRouteLinks(null);", response.text)
        self.assertIn("section.hidden = true;", response.text)
        self.assertIn("list.replaceChildren();", response.text)


if __name__ == "__main__":
    unittest.main()
