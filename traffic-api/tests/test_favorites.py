"""F18 관심 경로 UI 및 저장 규칙의 정적 회귀 테스트."""
import re
import unittest
from pathlib import Path

STATIC = Path(__file__).resolve().parents[1] / "static"


class RouteFavoritesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.js = (STATIC / "favorites.js").read_text(encoding="utf-8")
        cls.css = (STATIC / "favorites.css").read_text(encoding="utf-8")

    def test_both_pages_load_same_favorite_module(self):
        for page in ("index.html", "map.html"):
            with self.subTest(page=page):
                html = (STATIC / page).read_text(encoding="utf-8")
                self.assertIn('src="/static/favorites.js" defer', html)
                self.assertIn('href="/static/favorites.css"', html)
                for item in ("favoriteRoutes", "favoriteRouteList", "favoriteRouteStatus", "saveFavoriteRoute"):
                    self.assertEqual(len(re.findall('id="' + item + '"', html)), 1)

    def test_storage_key_limit_and_validation(self):
        for fragment in (
            '"seoul-traffic-favorites-v1"', "const LIMIT = 10;",
            "origin.length >= 2", "destination.length >= 2",
            "origin.length <= 100", "destination.length <= 100",
            "keyFor(item) === keyFor(pair)", "favorites.length >= LIMIT",
        ):
            with self.subTest(fragment=fragment):
                self.assertIn(fragment, self.js)

    def test_only_values_saved_and_text_content_rendered(self):
        self.assertIn("JSON.stringify(next)", self.js)
        self.assertIn("pair = { origin: normalize(originInput.value), destination: normalize(destinationInput.value) }", self.js)
        self.assertIn("label.textContent =", self.js)
        self.assertIn("list.replaceChildren()", self.js)
        self.assertNotIn("innerHTML", self.js)

    def test_load_is_manual_and_delete_is_single_entry(self):
        self.assertIn('button.dataset.action === "load"', self.js)
        self.assertIn("originInput.value = item.origin", self.js)
        self.assertIn("destinationInput.value = item.destination", self.js)
        self.assertIn('button.dataset.action === "delete"', self.js)
        self.assertIn("favorites.filter(function (_, i) { return i !== index; })", self.js)
        self.assertNotIn("fetch(", self.js)
        self.assertNotIn(".submit(", self.js)
        self.assertNotIn("requestSubmit(", self.js)

    def test_manual_route_guidance_after_load(self):
        navigation = (STATIC / "navigation.js").read_text(encoding="utf-8")
        map_html = (STATIC / "map.html").read_text(encoding="utf-8")
        self.assertIn('{name: "관심 경로", href: "/map#favoriteRoutes"}', navigation)
        self.assertNotIn('{name: "관심 경로", planned: true}', navigation)
        self.assertIn('id="favoriteRoutes"', map_html)
        self.assertIn(
            '<p id="result" role="status">경로 표시 버튼을 눌러 현재 교통정보를 조회하세요.</p>',
            map_html,
        )
        self.assertIn('if (form.id === "mapRouteForm")', self.js)
        self.assertIn('document.getElementById("result").textContent =', self.js)
        self.assertIn('경로를 불러왔습니다. 경로 표시 버튼을 눌러 현재 교통정보를 조회하세요.', self.js)
        self.assertNotIn("requestSubmit(", self.js)
        self.assertNotIn("fetch(", self.js)

    def test_browser_storage_failure_is_handled(self):
        self.assertIn("try {", self.js)
        self.assertIn("catch (error)", self.js)
        self.assertIn("storageAvailable = false;", self.js)

    def test_mobile_layout_and_no_yellow_focus(self):
        self.assertIn("@media(max-width:600px)", self.css)
        self.assertNotIn(":focus-visible", self.css)
        self.assertNotIn("outline:", self.css)
        for color in ("#f59e0b", "#facc15", "#f3b749", "#e2ab3c"):
            self.assertNotIn(color, self.css.lower())


if __name__ == "__main__":
    unittest.main()
