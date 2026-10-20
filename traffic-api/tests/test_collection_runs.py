"""F19 offline daily collector contracts; no live Kakao/DB calls."""
import asyncio
import unittest
from datetime import date, datetime, timezone
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app
from app.admin_auth import require_admin
from app import collection_runs


class CollectionRunsTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def tearDown(self):
        app.dependency_overrides.pop(require_admin, None)
        self.client.close()

    def test_admin_history_access_does_not_run_collector(self):
        self.assertIn(self.client.get("/api/admin/collection-runs").status_code, (401, 403))
        app.dependency_overrides[require_admin] = lambda: {"id": "admin-test"}
        with patch("app.collection_runs.get_collection_run_history", return_value=[]) as read, \
             patch("app.collection_runs.collect_daily_routes") as collector:
            response = self.client.get("/api/admin/collection-runs")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["scheduler_enabled"], False)
        self.assertEqual(response.json()["count"], 0)
        read.assert_called_once()
        collector.assert_not_called()

    def test_duplicate_slot_skips_external_api(self):
        with patch("app.collection_runs.reserve_collection_day", return_value=None), \
             patch("app.collection_runs.analyze_one_route") as analysis:
            result = asyncio.run(collection_runs.collect_daily_routes(date(2026, 10, 20)))
        self.assertEqual(result["status"], "duplicate")
        analysis.assert_not_called()

    def test_first_daily_slot_at_0900_korea(self):
        scheduled = collection_runs.scheduled_slot_utc(date(2026, 10, 20))
        self.assertEqual(scheduled.isoformat(), "2026-10-20T00:00:00+00:00")

    def test_admin_history_ui_explains_scheduler_off(self):
        page = self.client.get("/admin").text
        for marker in (
            'id="collectionRunsSection"',
            'id="refreshCollectionRunsButton"',
            'id="collectionRunsList"',
            "/api/admin/collection-runs",
            "자동 실행은 비활성"
        ):
            self.assertIn(marker, page)
