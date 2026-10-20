"""ITS 독립 기능의 경로 연결 및 카카오 홈 보존 확인."""
import unittest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from app.main import app

class ItsPageTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_its_page_available(self):
        response = self.client.get("/its")
        self.assertEqual(response.status_code, 200)
        self.assertIn("ITS", response.text)

    def test_kakao_home_unchanged(self):
        self.assertEqual(self.client.get("/").status_code, 200)

    def test_its_bbox_endpoint_is_connected(self):
        payload = {"header": {"resultCode": "00"}, "body": {"items": []}}
        with patch("app.its_routes.get_traffic_information", new_callable=AsyncMock, return_value=payload):
            response = self.client.get("/traffic", params={
                "min_x": 126.9, "max_x": 127.0, "min_y": 37.4, "max_y": 37.6
            })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), payload)

if __name__ == "__main__":
    unittest.main()
