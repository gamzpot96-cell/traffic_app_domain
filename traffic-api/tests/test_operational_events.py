"""F21 safe operational diagnostics contracts; never uses live Supabase."""
import unittest
from unittest.mock import patch
from fastapi.testclient import TestClient

from app.main import app
from app.admin_auth import require_admin
from app import operational_events


class OperationalEventsTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def tearDown(self):
        app.dependency_overrides.pop(require_admin, None)
        self.client.close()

    def test_protected_operations_endpoint(self):
        self.assertIn(self.client.get("/api/admin/operations").status_code, (401, 403))
        app.dependency_overrides[require_admin] = lambda: {"id": "admin-test"}
        with patch("app.operational_events.get_recent_operational_events",
                   return_value={"events": [], "count": 0, "scope_notice": "test"}):
            response = self.client.get("/api/admin/operations")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["count"], 0)

    def test_unknown_failure_codes_normalized_and_secrets_not_saved(self):
        calls = []

        class Cursor:
            def execute(self, query, params):
                calls.append((query, params))
            def __enter__(self):
                return self
            def __exit__(self, *args):
                pass

        class Connection:
            def cursor(self):
                return Cursor()
            def __enter__(self):
                return self
            def __exit__(self, *args):
                pass

        with patch("app.operational_events.get_database_connection",
                   return_value=Connection()):
            result = operational_events.record_operational_failure(
                "kakao", "directions_request", "secret token value", 502
            )
        self.assertTrue(result)
        self.assertEqual(calls[0][1], ("kakao", "directions_request", "unexpected_error", 502))
        self.assertNotIn("secret", str(calls[0]))

    def test_failure_to_record_does_not_mask_original_error(self):
        with patch("app.operational_events.get_database_connection",
                   side_effect=RuntimeError("db offline")):
            self.assertFalse(operational_events.record_operational_failure(
                "kakao", "local_request", "timeout"
            ))

    def test_invalid_sources_and_types_not_written(self):
        with patch("app.operational_events.get_database_connection") as db:
            self.assertFalse(operational_events.record_operational_failure(
                "user value", "local_request", "timeout"
            ))
            self.assertFalse(operational_events.record_operational_failure(
                "kakao", "unsafe arbitrary event", "timeout"
            ))
            db.assert_not_called()

    def test_admin_page_has_manual_diagnostics(self):
        page = self.client.get("/admin").text
        for marker in (
            'id="operationsSection"',
            'id="refreshOperationsButton"',
            'id="operationsList"',
            'id="operationsStatus"',
            "/api/admin/operations"
        ):
            self.assertIn(marker, page)
