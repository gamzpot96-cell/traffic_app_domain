"""서명된 관리자 뉴스 초안 검증 테스트 (외부 API 및 DB 연결 없음)."""
import os
import unittest
from unittest.mock import patch

from app.news_drafts import create_draft_token, verify_draft_token


class NewsDraftSignatureTests(unittest.TestCase):
    def setUp(self):
        self.settings = patch.dict(
            os.environ, {"NEWS_DRAFT_SIGNING_KEY": "test-only-signing-key-" + "x" * 40}
        )
        self.settings.start()
        self.addCleanup(self.settings.stop)
        self.news = {
            "title": "테스트 뉴스", "lead": "테스트 리드",
            "body": "테스트 본문", "scope_notice": "경로 한정",
            "retrieved_at": "2026-10-19T10:00:00+09:00",
            "routes": [{}, {}, {}]
        }

    def test_valid_token(self):
        token, generation_id = create_draft_token(self.news, "admin-id")
        parsed_id, parsed_news = verify_draft_token(token, "admin-id")
        self.assertEqual(parsed_id, generation_id)
        self.assertEqual(parsed_news, self.news)

    def test_wrong_admin(self):
        token, _ = create_draft_token(self.news, "admin-id")
        with self.assertRaises(ValueError):
            verify_draft_token(token, "another-admin")

    def test_tampered_token(self):
        token, _ = create_draft_token(self.news, "admin-id")
        first, signature = token.split(".")
        replacement = ("A" if first[0] != "A" else "B") + first[1:]
        with self.assertRaises(ValueError):
            verify_draft_token(replacement + "." + signature, "admin-id")

    def test_expired_token(self):
        with patch("app.news_drafts.time.time", return_value=1000):
            token, _ = create_draft_token(self.news, "admin-id")
        with patch("app.news_drafts.time.time", return_value=1000 + 1201):
            with self.assertRaises(ValueError):
                verify_draft_token(token, "admin-id")


if __name__ == "__main__":
    unittest.main()
