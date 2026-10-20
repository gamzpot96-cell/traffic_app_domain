"""F19-B usage counters and admin endpoint tests; no live Kakao or Supabase."""
import unittest
from collections import Counter
from unittest.mock import AsyncMock, patch

import httpx
from fastapi.testclient import TestClient

from app import main, kakao_api, api_usage
from app.admin_auth import require_admin


class ApiUsageTests(unittest.TestCase):
    def setUp(self):
        self.original_types = api_usage._api_counts
        self.original_cache = api_usage._cache_counts
        self.original_failure = api_usage._last_failure_at
        api_usage._api_counts = {"local": Counter(), "directions": Counter()}
        api_usage._cache_counts = Counter()
        api_usage._last_failure_at = None

    def tearDown(self):
        api_usage._api_counts = self.original_types
        api_usage._cache_counts = self.original_cache
        api_usage._last_failure_at = self.original_failure
        main.app.dependency_overrides.pop(require_admin, None)

    def test_anonymous_counts_and_cache_hit_rate(self):
        api_usage.record_api_result("local", "success")
        api_usage.record_api_result("directions", "timeout")
        api_usage.record_api_result("unknown", "success")
        for result in ("miss", "hit", "hit", "failure"):
            api_usage.record_cache_result(result)
        snapshot = api_usage.usage_snapshot()
        self.assertEqual(snapshot["external_requests"]["total"], 2)
        self.assertEqual(snapshot["external_requests"]["success"], 1)
        self.assertEqual(snapshot["external_requests"]["failure"], 1)
        self.assertEqual(snapshot["route_cache"]["hit_rate_percent"], 66.7)
        self.assertEqual(snapshot["route_cache"]["failure"], 1)
        self.assertIsNotNone(snapshot["last_api_failure_at"])
        self.assertNotIn("서울역", str(snapshot))
        self.assertNotIn("api_key", str(snapshot).lower())

    def test_missing_credentials_never_counts_external_request(self):
        with patch.object(kakao_api, "get_kakao_headers", side_effect=kakao_api.KakaoApiError("missing", 500)):
            with self.assertRaises(kakao_api.KakaoApiError):
                import asyncio
                asyncio.run(kakao_api.request_kakao_json(kakao_api.LOCAL_SEARCH_URL, {"query": "서울역"}))
        self.assertEqual(api_usage.usage_snapshot()["external_requests"]["total"], 0)

    def test_external_success_and_http_errors(self):
        import asyncio

        async def fake_get(url, **kwargs):
            if "directions" in url:
                return httpx.Response(429, request=httpx.Request("GET", url))
            return httpx.Response(200, json={"documents": []}, request=httpx.Request("GET", url))

        class FakeClient:
            async def __aenter__(self):
                return self
            async def __aexit__(self, *args):
                return False
            async def get(self, url, **kwargs):
                return await fake_get(url, **kwargs)

        with patch.object(kakao_api, "get_kakao_headers", return_value={"Authorization": "test"}), \
             patch.object(kakao_api.httpx, "AsyncClient", return_value=FakeClient()):
            self.assertEqual(asyncio.run(kakao_api.request_kakao_json(kakao_api.LOCAL_SEARCH_URL, {})), {"documents": []})
            with self.assertRaises(kakao_api.KakaoApiError):
                asyncio.run(kakao_api.request_kakao_json(kakao_api.DIRECTIONS_URL, {}))
        values = api_usage.usage_snapshot()["external_requests"]
        self.assertEqual((values["total"], values["success"], values["failure"]), (2, 1, 1))
        self.assertEqual(values["by_type"]["directions"]["http_error"], 1)

    def test_admin_endpoint_denies_anonymous_and_allows_admin(self):
        with TestClient(main.app) as client:
            response = client.get("/api/admin/api-usage")
            self.assertEqual(response.status_code, 401)
            main.app.dependency_overrides[require_admin] = lambda: {"id": "admin"}
            accepted = client.get("/api/admin/api-usage")
            self.assertEqual(accepted.status_code, 200)
            self.assertEqual(accepted.json()["external_requests"]["total"], 0)
            self.assertNotIn("access_token", str(accepted.json()))

    def test_admin_page_is_on_demand_and_has_no_focus_outline(self):
        with TestClient(main.app) as client:
            page = client.get("/admin")
        self.assertEqual(page.status_code, 200)
        self.assertIn('id="refreshApiUsageButton"', page.text)
        self.assertIn('id="apiUsageDetails" hidden', page.text)
        self.assertIn('fetch("/api/admin/api-usage"', page.text)
        self.assertIn('adminAccessToken', page.text)
        self.assertIn('document.getElementById("apiUsageDetails").hidden = true', page.text)
        self.assertNotIn(":focus-visible", page.text)


if __name__ == "__main__":
    unittest.main()
