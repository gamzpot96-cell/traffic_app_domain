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

    def test_d01_design_css_and_four_pages(self):
        asset = self.client.get("/static/design-system.css")
        self.assertEqual(asset.status_code, 200)
        for token in ("--d01-navy", "--d01-blue", "--d01-border"):
            self.assertIn(token, asset.text)
        for route in ("/", "/news", "/map", "/admin"):
            with self.subTest(route=route):
                response = self.client.get(route)
                self.assertEqual(response.status_code, 200)
                self.assertIn('/static/design-system.css', response.text)

    def test_d01_form_fields_do_not_receive_orange_outline(self):
        css = self.client.get("/static/design-system.css").text.replace("\r\n", "\n")
        self.assertIn(":where(button, a):focus-visible {", css)
        self.assertIn(":where(input, textarea, select):focus {\n    outline: none;\n}", css)
        self.assertNotIn(":where(button, a):focus {\n    outline: none;\n}", css)
        self.assertNotIn(":where(button, input, select, textarea, a):focus-visible", css)
        self.assertIn("outline: 3px solid #f59e0b;", css)
        navigation_css = self.client.get("/static/navigation.css").text
        self.assertIn(".site-nav-item a:focus-visible", navigation_css)

    def test_d01_menu_links_refer_to_implemented_features(self):
        navigation = self.client.get("/static/navigation.js")
        self.assertEqual(navigation.status_code, 200)
        for fragment in (
            '/news#trafficTrends', '/news#trafficExport',
            '/news#historySection'
        ):
            self.assertIn(fragment, navigation.text)
        news = self.client.get("/news")
        for target in ('id="trafficTrends"', 'id="trafficExport"', 'id="historySection"'):
            self.assertIn(target, news.text)

    def test_d01_menu_uses_hover_only_for_background_highlighting(self):
        # 현재 URL이나 열린 메뉴 여부가 배경색을 고정하지 않아야 합니다.
        css = self.client.get("/static/navigation.css").text
        javascript = self.client.get("/static/navigation.js").text
        self.assertIn(".site-nav-trigger:hover{background:", css)
        self.assertIn(".site-nav-item a:hover{background:", css)
        self.assertNotIn(".site-nav-trigger.site-nav-current{background:", css)
        self.assertNotIn('.site-nav-trigger[aria-expanded="true"]', css)
        self.assertNotIn('.site-nav-item a[aria-current="page"]', css)
        self.assertNotIn('trigger.classList.add("site-nav-current")', javascript)
        self.assertIn("linkUrl.hash === currentHash", javascript)
        self.assertIn('link.setAttribute("aria-current", "page")', javascript)
        # 키보드 포커스 강조를 지우지 않아야 합니다.
        self.assertIn(".site-nav-item a:focus-visible", css)

    def test_d01_home_layout_keeps_existing_query_and_briefing(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        for required in (
            'class="home-hero"', 'class="home-main"', 'class="home-search"',
            'grid-template-columns: minmax(0,1fr) minmax(0,1fr)',
            '@media (max-width: 850px)', '@media (max-width: 600px)',
            'id="routeForm"', 'id="origin"', 'id="destination"',
            'id="summary"', 'id="roadRows"', 'id="overviewButton"',
            'id="overviewTableBody"', 'id="briefingContent"',
            'id="overviewBriefingText"', 'function loadOverviewBriefing()'
        ):
            with self.subTest(required=required):
                self.assertIn(required, response.text)

    def test_d01_news_layout_preserves_existing_features(self):
        response = self.client.get("/news")
        self.assertEqual(response.status_code, 200)
        for text in (
            'class="container news-layout"', 'class="news-intro"',
            'id="loadNewsButton"', 'id="newsStatus"',
            'id="trafficTrends"', 'id="historySection"',
            'id="trafficExport"', 'id="trafficDashboard"',
            'id="savedArticleRoutes"', 'id="newsTitle"',
            'id="newsBody"', 'id="trafficTrendChart"',
            'id="trafficTrendTable"', 'id="newsSearchForm"',
            'id="trafficExportForm"', '@media (max-width: 850px)',
            '@media (max-width: 600px)'
        ):
            with self.subTest(text=text):
                self.assertIn(text, response.text)

    def test_d01_map_layout_keeps_map_and_saved_article_route(self):
        response = self.client.get("/map")
        self.assertEqual(response.status_code, 200)
        for required in (
            'class="map-hero"', 'class="map-hero-inner"',
            'class="map-content"', 'class="map-controls"',
            'class="map-canvas-frame"', 'id="map"',
            'id="savedArticlePanel"', 'id="savedArticleTitle"',
            'id="mapArticleStatus"', 'id="mapRouteForm"',
            'id="origin"', 'id="destination"', 'id="mapRouteSubmit"',
            'id="result"', 'drawCurrentRoute(data)', 'loadSavedArticleRouteFromUrl()',
            '@media (max-width: 850px)', '@media (max-width: 600px)'
        ):
            with self.subTest(required=required):
                self.assertIn(required, response.text)

    def test_existing_admin_guard(self):
        for route in ("/api/admin/me", "/api/admin/news/generate"):
            with self.subTest(route=route):
                response = self.client.get(route) if route.endswith("/me") else self.client.post(route)
                self.assertEqual(response.status_code, 401)


if __name__ == "__main__":
    unittest.main()
