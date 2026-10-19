"""F22 CSV export: API contracts, Korean Excel CSV, injection and DB boundaries."""
import csv
import io
import unittest
from datetime import datetime
from decimal import Decimal
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app
from app.traffic_export import (
    CSV_HEADERS, MAX_EXPORT_ROWS, encode_csv, get_export_rows, safe_csv_text
)


def example_row(start="서울역", end="잠실역 2호선"):
    return (
        8, datetime.fromisoformat("2026-10-19T11:08:04+09:00"),
        start, end, 17200, 2424, 1754, Decimal("10.2")
    )


class TrafficExportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    @classmethod
    def tearDownClass(cls):
        cls.client.close()

    def test_csv_bom_korean_columns_and_units(self):
        content = encode_csv([example_row()])
        self.assertTrue(content.startswith(b"\xef\xbb\xbf"))
        parsed = list(csv.reader(io.StringIO(content.decode("utf-8-sig"))))
        self.assertEqual(tuple(parsed[0]), CSV_HEADERS)
        self.assertEqual(parsed[1][0], "8")
        self.assertEqual(parsed[1][1], "2026-10-19 11:08:04")
        self.assertEqual(parsed[1][2], "서울역")
        self.assertEqual(parsed[1][4], "17.20")
        self.assertEqual(parsed[1][5], "40.40")
        self.assertEqual(parsed[1][6], "1.75")
        self.assertEqual(parsed[1][7], "10.20")

    def test_csv_formula_text_sanitization(self):
        for text in ("=2+3", "+SUM(A1)", "-10+20", "@value", "   =1+1", "\t@SUM(A1)"):
            with self.subTest(value=text):
                self.assertTrue(safe_csv_text(text).startswith("'"))
        parsed = list(csv.reader(io.StringIO(
            encode_csv([example_row(start="=HYPERLINK(\"url\")")]).decode("utf-8-sig")
        )))
        self.assertEqual(parsed[1][2][0], "'")

    def test_empty_download_contains_only_header(self):
        with patch("app.main.get_export_rows", return_value=[]) as query:
            response = self.client.get("/api/traffic/export.csv")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["X-Export-Row-Count"], "0")
        self.assertEqual(len(list(csv.reader(io.StringIO(response.content.decode("utf-8-sig"))))), 1)
        query.assert_called_once_with(
            origin=None, destination=None, start_time=None, end_time=None
        )

    def test_filter_parameters_are_kst_and_bound(self):
        with patch("app.main.get_export_rows", return_value=[example_row()]) as query:
            response = self.client.get("/api/traffic/export.csv", params={
                "origin": "서울역", "destination": "잠실역 2호선",
                "start_date": "2026-10-18", "end_date": "2026-10-19"
            })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["X-Export-Row-Count"], "1")
        kwargs = query.call_args.kwargs
        self.assertEqual(kwargs["origin"], "서울역")
        self.assertEqual(kwargs["destination"], "잠실역 2호선")
        self.assertEqual(kwargs["start_time"].isoformat(), "2026-10-18T00:00:00+09:00")
        self.assertEqual(kwargs["end_time"].isoformat(), "2026-10-20T00:00:00+09:00")
        self.assertIn("attachment;", response.headers["content-disposition"])

    def test_invalid_filters_rejected_without_query(self):
        cases = [
            {"origin": "서울역"},
            {"destination": "잠실역"},
            {"origin": "a", "destination": "bb"},
            {"start_date": "2026-10-20", "end_date": "2026-10-19"},
            {"end_date": "9999-12-31"}
        ]
        with patch("app.main.get_export_rows") as query:
            for params in cases:
                with self.subTest(params=params):
                    self.assertEqual(
                        self.client.get("/api/traffic/export.csv", params=params).status_code, 422
                    )
            query.assert_not_called()

    def test_oversized_export_is_rejected(self):
        fake_rows = [example_row()] * (MAX_EXPORT_ROWS + 1)
        class FakeCursor:
            def execute(self, sql, params):
                self.sql = sql
                self.params = params
            def fetchall(self):
                return fake_rows
            def __enter__(self):
                return self
            def __exit__(self, *args):
                pass
        class FakeConnection:
            def cursor(self):
                return FakeCursor()
            def __enter__(self):
                return self
            def __exit__(self, *args):
                pass
        with patch("app.traffic_export.get_database_connection", return_value=FakeConnection()):
            with self.assertRaisesRegex(ValueError, "5,000행"):
                get_export_rows()
        with patch("app.main.get_export_rows", side_effect=ValueError("5,000행 초과")):
            self.assertEqual(self.client.get("/api/traffic/export.csv").status_code, 422)

    def test_database_error_is_generic(self):
        with patch("app.main.get_export_rows", side_effect=RuntimeError("private DB detail")):
            response = self.client.get("/api/traffic/export.csv")
        self.assertEqual(response.status_code, 503)
        self.assertNotIn("private DB detail", response.text)

    def test_route_options_and_frontend_controls(self):
        with patch("app.main.get_export_route_options", return_value=[
            {"origin": "서울역", "destination": "잠실역 2호선"}
        ]):
            options = self.client.get("/api/traffic/routes")
        self.assertEqual(options.status_code, 200)
        self.assertEqual(len(options.json()["routes"]), 1)
        page = self.client.get("/news")
        self.assertEqual(page.status_code, 200)
        self.assertIn('id="trafficExportForm"', page.text)
        self.assertIn('id="exportRoute"', page.text)
        self.assertIn('"/api/traffic/export.csv?"', page.text)


if __name__ == "__main__":
    unittest.main()
