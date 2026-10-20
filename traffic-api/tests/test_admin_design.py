"""D01 관리자 UI 구조 회귀검사: 네트워크 호출·DB 저장 없이 정적 파일만 검증."""
import re
import unittest
from pathlib import Path

ADMIN_HTML = Path(__file__).resolve().parents[1] / "static" / "admin.html"


class AdminDesignTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html = ADMIN_HTML.read_text(encoding="utf-8").replace("\r\n", "\n")
        cls.script = re.search(r"<script>([\s\S]*?)</script>", cls.html)
        assert cls.script is not None, "관리자 인라인 JavaScript 누락"

    def test_required_ids_are_unique(self):
        ids = (
            "sharedNavigation", "loginForm", "adminEmail", "adminPassword",
            "loginButton", "loginMessage", "adminPanel", "logoutButton",
            "generateDraftButton", "saveDraftButton", "draftStatus",
            "draftPreview", "draftTitle", "draftRetrievedAt", "draftLead",
            "draftBody", "draftNotice", "draftRoutes", "savedArticleLink",
        )
        for identifier in ids:
            with self.subTest(identifier=identifier):
                self.assertEqual(
                    len(re.findall(r'\bid="' + identifier + r'"', self.html)), 1
                )

    def test_login_and_workshop_layout(self):
        for token in (
            'class="admin-login-layout"', 'class="admin-hero"',
            'class="login-card"', 'class="workspace-header"',
            'class="steps"', 'class="workspace-section"',
            'body.admin-active .admin-login-layout { display: none; }',
            '.admin-panel { display: none; }',
            '@media (max-width: 850px)', '@media (max-width: 600px)',
            '/static/design-system.css', '/static/navigation.css',
        ):
            with self.subTest(token=token):
                self.assertIn(token, self.html)

    def test_password_and_saved_article_protections(self):
        self.assertIn('type="password" id="adminPassword"', self.html)
        self.assertIn('id="saveDraftButton" disabled', self.html)
        self.assertIn('id="draftPreview" class="draft-preview" hidden', self.html)
        self.assertIn('id="loginMessage" class="message" role="status"', self.html)
        for fragment in (
            'fetch("/api/admin/login"', 'fetch("/api/admin/me"',
            'fetch("/api/admin/news/generate"', 'fetch("/api/admin/news/save"',
            'if (!verifyData.authenticated || !verifyData.is_admin)',
            'adminPanel.style.removeProperty("display")',
            'adminPanel.style.display = "none"',
            'pendingDraftToken = null;',
            'saveButton.disabled = true;',
        ):
            with self.subTest(fragment=fragment):
                self.assertIn(fragment, self.script.group(1))
        self.assertEqual(self.script.group(1).count('fetch("/api/admin/news/save"'), 1)

    def test_complete_html_and_script(self):
        self.assertEqual(len(re.findall(r"<script(?:\s|>)", self.html)), self.html.count("</script>"))
        self.assertTrue(self.html.rstrip().endswith("</html>"))
        self.assertIn("</body>", self.html)
        self.assertIn('function showDraft(news)', self.script.group(1))
        self.assertEqual(self.script.group(1).count('loginForm.addEventListener("submit"'), 1)


if __name__ == "__main__":
    unittest.main()
