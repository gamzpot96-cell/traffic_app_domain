"""F16 뉴스 검색 API 계약 및 입력값 테스트 (DB 연결 없이 수행)."""
import unittest
from datetime import datetime
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app


class NewsSearchApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    @classmethod
    def tearDownClass(cls):
        cls.client.close()

    def test_search_default_params(self):
        payload = {"total": 0, "page": 1, "page_size": 10, "total_pages": 0, "articles": []}
        with patch("app.main.search_saved_news_articles", return_value=payload) as search:
            result = self.client.get("/api/news/search")
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.json(), payload)
        search.assert_called_once_with(
            keyword="", start_time=None, end_time=None, page=1, page_size=10
        )

    def test_kst_dates_inclusive_end_and_keyword(self):
        with patch("app.main.search_saved_news_articles", return_value={
            "total": 1, "page": 2, "page_size": 20, "total_pages": 1, "articles": []
        }) as search:
            response = self.client.get(
                "/api/news/search",
                params={
                    "q": "  서울%_역  ", "start_date": "2026-10-18",
                    "end_date": "2026-10-19", "page": 2, "page_size": 20
                }
            )
        self.assertEqual(response.status_code, 200)
        args = search.call_args.kwargs
        self.assertEqual(args["keyword"], "서울%_역")
        self.assertEqual(args["page"], 2)
        self.assertEqual(args["page_size"], 20)
        self.assertEqual(args["start_time"].isoformat(), "2026-10-18T00:00:00+09:00")
        self.assertEqual(args["end_time"].isoformat(), "2026-10-20T00:00:00+09:00")

    def test_rejects_invalid_filters(self):
        bad_cases = [
            {"page": 0},
            {"page_size": 15},
            {"start_date": "2026-10-20", "end_date": "2026-10-19"},
            {"start_date": "not-a-date"},
            {"q": "x" * 101},
            {"end_date": "9999-12-31"}
        ]
        with patch("app.main.search_saved_news_articles") as search:
            for params in bad_cases:
                with self.subTest(params=params):
                    response = self.client.get("/api/news/search", params=params)
                    self.assertEqual(response.status_code, 422)
            search.assert_not_called()

    def test_database_failure_returns_503(self):
        with patch("app.main.search_saved_news_articles", side_effect=RuntimeError("test DB error")):
            response = self.client.get("/api/news/search")
        self.assertEqual(response.status_code, 503)
        self.assertNotIn("test DB error", response.text)

    def test_old_history_api_still_exists(self):
        with patch("app.main.get_saved_news_articles", return_value=[]):
            response = self.client.get("/api/news/history")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"count": 0, "articles": []})


if __name__ == "__main__":
    unittest.main()
