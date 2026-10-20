"""F17 stored snapshot time-series API and browser markup checks."""
import unittest
from datetime import datetime
from decimal import Decimal
from unittest.mock import patch
from fastapi.testclient import TestClient

from app.main import app
from app.traffic_export import get_route_history


class TrafficHistoryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    @classmethod
    def tearDownClass(cls):
        cls.client.close()

    def test_history_route_and_kst_date_filters(self):
        fake_records = [
            {
                "article_id": 8,
                "retrieved_at": "2026-10-19T11:08:04+09:00",
                "duration_seconds": 2424,
                "congestion_ratio": 10.16
            }
        ]
        with patch("app.main.get_route_history", return_value=fake_records) as query:
            response = self.client.get("/api/traffic/history", params={
                "origin": "서울역", "destination": "잠실역 2호선",
                "start_date": "2026-10-19", "end_date": "2026-10-19", "limit": 100
            })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["count"], 1)
        args = query.call_args.args
        self.assertEqual(args[0:2], ("서울역", "잠실역 2호선"))
        self.assertEqual(args[2].isoformat(), "2026-10-19T00:00:00+09:00")
        self.assertEqual(args[3].isoformat(), "2026-10-20T00:00:00+09:00")
        self.assertEqual(args[4], 100)

    def test_history_input_validation(self):
        bad_inputs = [
            {},
            {"origin": "서울역"},
            {"origin": "a", "destination": "잠실역"},
            {"origin": "서울역", "destination": "잠실역", "limit": 501},
            {"origin": "서울역", "destination": "잠실역", "start_date": "2026-10-20", "end_date": "2026-10-19"},
            {"origin": "서울역", "destination": "잠실역", "end_date": "9999-12-31"}
        ]
        with patch("app.main.get_route_history") as query:
            for params in bad_inputs:
                with self.subTest(params=params):
                    self.assertEqual(
                        self.client.get("/api/traffic/history", params=params).status_code, 422
                    )
            query.assert_not_called()

    def test_empty_records(self):
        with patch("app.main.get_route_history", return_value=[]):
            response = self.client.get(
                "/api/traffic/history?origin=서울역&destination=잠실역"
            )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["count"], 0)
        self.assertEqual(response.json()["records"], [])

    def test_excess_records_and_system_errors(self):
        with patch("app.main.get_route_history", side_effect=ValueError("조회 결과 초과")):
            self.assertEqual(self.client.get(
                "/api/traffic/history?origin=서울역&destination=잠실역"
            ).status_code, 422)
        with patch("app.main.get_route_history", side_effect=RuntimeError("secret DB")):
            response = self.client.get(
                "/api/traffic/history?origin=서울역&destination=잠실역"
            )
        self.assertEqual(response.status_code, 503)
        self.assertNotIn("secret DB", response.text)

    def test_query_read_only_and_order(self):
        fake_data = [
            (8, datetime.fromisoformat("2026-10-19T11:08:04+09:00"), 17210, 2421, 1749, Decimal("10.16")),
            (6, datetime.fromisoformat("2026-10-19T10:55:47+09:00"), 17210, 2514, 1749, Decimal("10.16"))
        ]
        class Cursor:
            def execute(self, sql, params):
                self.sql, self.params = sql, params
                self_outer.executed_sql = sql
                self_outer.bound_params = params
            def fetchall(self):
                return fake_data
            def __enter__(self): return self
            def __exit__(self, *args): pass
        class Connection:
            def cursor(self): return Cursor()
            def __enter__(self): return self
            def __exit__(self, *args): pass
        self_outer = self
        with patch("app.traffic_export.get_database_connection", return_value=Connection()):
            result = get_route_history("서울역", "잠실역", limit=100)
        self.assertEqual([item["article_id"] for item in result], [6, 8])
        self.assertEqual(result[0]["congestion_ratio"], 10.16)
        self.assertIn("SELECT", self.executed_sql)
        self.assertNotIn("INSERT", self.executed_sql)
        self.assertNotIn("DELETE", self.executed_sql)
        self.assertIn("LIMIT %s", self.executed_sql)
        self.assertEqual(self.bound_params[-1], 101)

    def test_limit_exceed_raises(self):
        class Cursor:
            def execute(self, *args): pass
            def fetchall(self):
                return [(1, datetime.now().astimezone(), 100, 100, 10, 10)] * 3
            def __enter__(self): return self
            def __exit__(self, *args): pass
        class Connection:
            def cursor(self): return Cursor()
            def __enter__(self): return self
            def __exit__(self, *args): pass
        with patch("app.traffic_export.get_database_connection", return_value=Connection()):
            with self.assertRaisesRegex(ValueError, "제한"):
                get_route_history("서울역", "잠실역", limit=2)

    def test_frontend_chart_and_table_present(self):
        response = self.client.get("/news")
        self.assertEqual(response.status_code, 200)
        for fragment in [
            'id="trafficTrends"', 'id="trendRoute"', 'id="trendMetric"',
            'id="trafficTrendChart"', 'id="trafficTrendTable"',
            '/api/traffic/history?', 'trendRecords', 'createElementNS'
        ]:
            self.assertIn(fragment, response.text)


if __name__ == "__main__":
    unittest.main()
