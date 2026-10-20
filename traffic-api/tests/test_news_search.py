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

    def test_paginated_search_passthrough(self):
        # DB를 실제로 변경하지 않고 2페이지 결과 전달을 검사합니다.
        fake_result = {
            "total": 23,
            "page": 2,
            "page_size": 10,
            "total_pages": 3,
            "articles": [{"id": 6, "title": "테스트 기사"}]
        }
        with patch("app.main.search_saved_news_articles", return_value=fake_result) as search:
            response = self.client.get("/api/news/search", params={"page": 2})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["page"], 2)
        self.assertEqual(response.json()["total_pages"], 3)
        self.assertEqual(response.json()["articles"][0]["id"], 6)
        self.assertEqual(search.call_args.kwargs["page"], 2)

    def test_page_state_reset_code_present(self):
        # DOM 조작 자체는 실제 브라우저에서 별도 확인합니다.
        response = self.client.get("/news")
        self.assertEqual(response.status_code, 200)
        self.assertIn('currentNewsPage = data.total_pages === 0 ? 0 : data.page;', response.text)
        # Windows CRLF / Unix LF 및 들여쓰기 차이에 무관하게 코드 순서를 검사합니다.
        self.assertRegex(
            response.text,
            r'historyList\.replaceChildren\(\);\s*currentNewsPage\s*=\s*0;'
        )

    def test_old_history_api_still_exists(self):
        with patch("app.main.get_saved_news_articles", return_value=[]):
            response = self.client.get("/api/news/history")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"count": 0, "articles": []})


if __name__ == "__main__":
    unittest.main()
