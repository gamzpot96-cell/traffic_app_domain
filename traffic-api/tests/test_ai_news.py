"""관리자 전용 OpenAI 기사 생성 계약 테스트. 실제 외부 API / DB 호출 없음."""
import os
import unittest
from unittest.mock import AsyncMock, Mock, patch

from fastapi.testclient import TestClient

from app import main
from app.admin_auth import require_admin
from app.ai_news import create_ai_news_briefing, NewsGenerationError


ROUTES = [
    {"start": "서울역", "end": "잠실역", "distance_m": 16000,
     "duration_seconds": 3000, "total_road_count": 12,
     "congested_count": 2, "congested_distance_m": 2000},
    {"start": "광화문", "end": "강남역", "distance_m": 11000,
     "duration_seconds": 1800, "total_road_count": 8,
     "congested_count": 1, "congested_distance_m": 1000},
    {"start": "여의도역", "end": "잠실역", "distance_m": 15000,
     "duration_seconds": 2100, "total_road_count": 10,
     "congested_count": 0, "congested_distance_m": 0},
]


class AiNewsTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(main.app)

    def tearDown(self):
        main.app.dependency_overrides.pop(require_admin, None)
        self.client.close()

    def test_public_generation_is_forbidden_without_collecting_data(self):
        with patch("app.main.analyze_seoul_routes", new_callable=AsyncMock) as collect:
            response = self.client.get("/api/briefing/news")
        self.assertEqual(response.status_code, 403)
        collect.assert_not_called()
        public_page = self.client.get("/news").text
        self.assertNotIn('id="loadNewsButton"', public_page)
        self.assertIn('id="historySection"', public_page)

    def test_admin_generation_requires_login(self):
        with patch("app.main.analyze_seoul_routes", new_callable=AsyncMock) as collect:
            response = self.client.post("/api/admin/news/generate")
        self.assertEqual(response.status_code, 401)
        collect.assert_not_called()

    def test_openai_uses_fact_sheet_and_returns_article(self):
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "choices": [{"message": {"content":
                '{"title":"세 경로 교통 분석","lead":"카카오 경로 비교",'
                '"body":"서울역에서 잠실역까지 예상 소요시간을 비교했습니다."}'}}]
        }
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-only", "OPENAI_MODEL": "gpt-4.1-mini"}), \\
             patch("app.ai_news.httpx.AsyncClient") as client_class:
            client_class.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )
            import asyncio
            article = asyncio.run(create_ai_news_briefing(ROUTES))
            arguments = client_class.return_value.__aenter__.return_value.post.call_args
        self.assertEqual(article["title"], "세 경로 교통 분석")
        self.assertIn("3개 자동차 경로", article["scope_notice"])
        self.assertEqual(arguments.args[0], "https://api.openai.com/v1/chat/completions")
        import json
        prompt = arguments.kwargs["json"]["messages"][1]["content"]
        self.assertIn('"distance_m": 16000', prompt)
        self.assertIn('"congestion_ratio_percent": 12.5', prompt)
        self.assertNotIn("test-only", prompt)

    def test_missing_key_blocks_generation(self):
        with patch.dict(os.environ, {"OPENAI_API_KEY": ""}):
            import asyncio
            with self.assertRaises(NewsGenerationError):
                asyncio.run(create_ai_news_briefing(ROUTES))

    def test_admin_success_uses_ai_and_signed_draft(self):
        main.app.dependency_overrides[require_admin] = lambda: {"id": "test-admin"}
        with patch("app.main.analyze_seoul_routes", new_callable=AsyncMock, return_value=ROUTES), \\
             patch("app.main.create_ai_news_briefing", new_callable=AsyncMock,
                   return_value={"title": "AI 제목", "lead": "AI 리드",
                                 "body": "AI 본문", "scope_notice": "선택 경로 한정"}) as generate, \\
             patch("app.main.create_draft_token", return_value=("signed-token", "generation-id")):
            response = self.client.post("/api/admin/news/generate")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["news"]["title"], "AI 제목")
        self.assertEqual(response.json()["draft_token"], "signed-token")
        generate.assert_awaited_once_with(ROUTES)

    def test_admin_openai_failure_is_not_replaced_with_template(self):
        main.app.dependency_overrides[require_admin] = lambda: {"id": "test-admin"}
        with patch("app.main.analyze_seoul_routes", new_callable=AsyncMock, return_value=ROUTES), \\
             patch("app.main.create_ai_news_briefing", new_callable=AsyncMock,
                   side_effect=NewsGenerationError("test only")):
            response = self.client.post("/api/admin/news/generate")
        self.assertEqual(response.status_code, 503)
        self.assertNotIn("test only", response.text)


if __name__ == "__main__":
    unittest.main()
