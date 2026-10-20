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
        self.assertIn(":where(input, textarea, select):focus {\n    outline: none;\n}", css)
        self.assertNotIn(":where(button, input, select, textarea, a):focus-visible", css)
        navigation_css = self.client.get("/static/navigation.css").text
        self.assertNotIn(".site-nav-item a:focus-visible", navigation_css)

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
        # 사용자 정책: 메뉴에 포커스 외곽선을 추가하지 않습니다.
        self.assertNotIn(".site-nav-item a:focus-visible", css)

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

    def test_d02_shared_styles_and_legacy_function_ids(self):
        css = self.client.get("/static/d02-journalism.css")
        self.assertEqual(css.status_code, 200)
        self.assertIn("text/css", css.headers.get("content-type", ""))
        self.assertIn("@media(max-width:600px)", css.text)
        for path, required in {
            "/": ("routeForm", "overviewButton", "briefingContent", "historySection"),
            "/map": ("mapRouteForm", "map", "savedArticlePanel"),
            "/news": ("newsSearchForm", "newsTitle", "savedArticleRouteList", "trafficExportForm"),
            "/admin": ("loginForm", "adminPanel", "generateDraftButton", "saveDraftButton"),
        }.items():
            with self.subTest(path=path):
                response = self.client.get(path)
                self.assertEqual(response.status_code, 200)
                self.assertIn('/static/d02-journalism.css', response.text)
                for name in required:
                    if path == "/" and name == "historySection":
                        self.assertIn('/news#historySection', response.text)
                    else:
                        self.assertIn('id="' + name + '"', response.text)
        self.assertIn("교통 데이터를 읽는 뉴스룸", self.client.get("/news").text)
        admin_html = self.client.get("/admin").text
        self.assertIn('adminPanel.style.removeProperty("display");', admin_html)
        self.assertNotIn('adminPanel.style.display = "block";', admin_html)

    def test_d02_map_news_admin_layout_refinement(self):
        css_response = self.client.get("/static/d02-journalism.css")
        self.assertEqual(css_response.status_code, 200)
        css = css_response.text
        for rule in (
            ".map-content .map-controls #mapRouteForm{display:grid;",
            ".news-layout>#historySection{order:1;}",
            ".news-layout>#trafficDashboard{order:2;}",
            ".news-layout>article{order:4;}",
            "body.admin-active .admin-panel{display:block;}",
            "body.admin-active .admin-panel{display:grid;",
            ".admin-panel > .workspace-section + .workspace-section{margin-top:24px;}",
            ".admin-panel #draftPreview[hidden]{display:none!important;}",
            ".admin-panel #draftPreview[hidden]{display:none!important;}",
            "@media(max-width:600px)",
        ):
            with self.subTest(rule=rule):
                self.assertIn(rule, css)
        required = {
            "/map": ('id="mapRouteForm"', 'id="map"', 'id="savedArticlePanel"'),
            "/news": ('id="historySection"', 'id="trafficDashboard"', 'id="trafficTrends"', 'id="newsTitle"'),
            "/admin": ('id="adminPanel"', 'id="generateDraftButton"', 'id="draftPreview"', 'id="saveDraftButton"'),
        }
        for route, markers in required.items():
            page = self.client.get(route)
            self.assertEqual(page.status_code, 200)
            for marker in markers:
                with self.subTest(route=route, marker=marker):
                    self.assertIn(marker, page.text)

    def test_all_shared_styles_have_no_focus_outline_rules(self):
        for filename in (
            "design-system.css", "navigation.css",
            "d02-journalism.css", "favorites.css",
        ):
            with self.subTest(filename=filename):
                css = self.client.get("/static/" + filename).text
                self.assertEqual(self.client.get("/static/" + filename).status_code, 200)
                self.assertNotRegex(css, r"(?i):focus(?:-visible)?[^{}]*\{[^{}]*(?:outline\s*:\s*(?!none\b)|box-shadow\s*:)")
                self.assertNotRegex(css, r"(?i)outline\s*:\s*(?!none\b)[^;{}]+;")

    def test_d02_no_yellow_focus_outlines(self):
        styles = (
            "/static/design-system.css",
            "/static/navigation.css",
            "/static/d02-journalism.css",
        )
        for path in styles:
            with self.subTest(path=path):
                css = self.client.get(path).text.lower()
                for forbidden in ("#f59e0b", "#facc15", "#f3b749", "#e2ab3c"):
                    self.assertNotIn(forbidden, css)
        self.assertIn("outline:none;", self.client.get("/static/d02-journalism.css").text)

    def test_d02_news_hero_actions_share_a_row(self):
        from html.parser import HTMLParser

        class HeroActionsParser(HTMLParser):
            def __init__(self):
                super().__init__()
                self.in_actions = 0
                self.tags = []

            def handle_starttag(self, tag, attrs):
                attrs = dict(attrs)
                if tag == "div" and "d02-news-actions" in attrs.get("class", "").split():
                    self.in_actions = 1
                elif self.in_actions and tag == "div":
                    self.in_actions += 1
                elif self.in_actions and tag in ("a", "button"):
                    self.tags.append((tag, attrs.get("id", ""), attrs.get("href", "")))

            def handle_endtag(self, tag):
                if tag == "div" and self.in_actions:
                    self.in_actions -= 1

        response = self.client.get("/news")
        self.assertEqual(response.status_code, 200)
        parser = HeroActionsParser()
        parser.feed(response.text)
        self.assertEqual(parser.tags, [
            ("a", "", "#historySection"),
            ("a", "", "#trafficDashboard"),
            ("button", "loadNewsButton", ""),
        ])
        css = self.client.get("/static/d02-journalism.css").text
        self.assertIn(".news-intro .d02-news-actions{display:flex;", css)
        self.assertIn(".news-intro .d02-news-actions #loadNewsButton{display:inline-flex;", css)
        self.assertIn(".news-intro .d02-news-actions{flex-direction:column;}", css)

    def test_existing_admin_guard(self):
        for route in ("/api/admin/me", "/api/admin/news/generate"):
            with self.subTest(route=route):
                response = self.client.get(route) if route.endswith("/me") else self.client.post(route)
                self.assertEqual(response.status_code, 401)


if __name__ == "__main__":
    unittest.main()
