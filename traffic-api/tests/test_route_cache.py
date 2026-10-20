"""F19-A 공개 경로 캐시 회귀 테스트. 실제 Kakao API/DB를 호출하지 않습니다."""
import asyncio
import unittest
from unittest.mock import AsyncMock, patch

import httpx
from app import main


class RouteCacheTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        main.route_cache.clear()
        self.client = httpx.AsyncClient(
            transport=httpx.ASGITransport(app=main.app),
            base_url="http://testserver",
        )
        self.place = {"name": "장소", "longitude": 127.0, "latitude": 37.5}
        self.route = {"summary": {"distance": 1000, "duration": 120}, "sections": []}

    async def asyncTearDown(self):
        await self.client.aclose()
        main.route_cache.clear()

    async def test_repeat_and_normalized_key(self):
        with patch.object(main, "find_place", new_callable=AsyncMock, return_value=self.place) as find, \
             patch.object(main, "get_car_route", new_callable=AsyncMock, return_value=self.route) as directions:
            first = await self.client.get("/api/route", params={"origin": "서울역", "destination": "잠실역"})
            second = await self.client.get("/api/route", params={"origin": " 서울역 ", "destination": "잠실역"})
        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 200)
        self.assertEqual(first.json(), second.json())
        self.assertEqual(first.headers["x-route-cache"], "MISS")
        self.assertEqual(second.headers["x-route-cache"], "HIT")
        self.assertEqual(find.await_count, 2)
        self.assertEqual(directions.await_count, 1)

    async def test_direction_and_different_route_are_separate(self):
        with patch.object(main, "find_place", new_callable=AsyncMock, return_value=self.place), \
             patch.object(main, "get_car_route", new_callable=AsyncMock, return_value=self.route) as directions:
            for start, end in [("서울역", "잠실역"), ("잠실역", "서울역"), ("서울역", "강남역")]:
                result = await self.client.get("/api/route", params={"origin": start, "destination": end})
                self.assertEqual(result.headers["x-route-cache"], "MISS")
        self.assertEqual(directions.await_count, 3)

    async def test_expiry_causes_fresh_call(self):
        with patch.object(main, "find_place", new_callable=AsyncMock, return_value=self.place), \
             patch.object(main, "get_car_route", new_callable=AsyncMock, return_value=self.route) as directions:
            await self.client.get("/api/route", params={"origin": "서울역", "destination": "잠실역"})
            key = main.route_cache_key("서울역", "잠실역")
            timestamp, result = main.route_cache[key]
            main.route_cache[key] = (timestamp - main.ROUTE_CACHE_TTL_SECONDS - 1, result)
            refreshed = await self.client.get("/api/route", params={"origin": "서울역", "destination": "잠실역"})
        self.assertEqual(refreshed.headers["x-route-cache"], "MISS")
        self.assertEqual(directions.await_count, 2)

    async def test_failure_does_not_cache(self):
        from app.kakao_api import KakaoApiError
        with patch.object(main, "find_place", new_callable=AsyncMock, side_effect=KakaoApiError("조회 실패", 502)):
            for _ in range(2):
                result = await self.client.get("/api/route", params={"origin": "서울역", "destination": "잠실역"})
                self.assertEqual(result.status_code, 502)
        self.assertEqual(len(main.route_cache), 0)

    async def test_concurrent_same_route_calls_once(self):
        with patch.object(main, "find_place", new_callable=AsyncMock, return_value=self.place), \
             patch.object(main, "get_car_route", new_callable=AsyncMock, return_value=self.route) as directions:
            async def request():
                return await self.client.get("/api/route", params={"origin": "서울역", "destination": "잠실역"})
            one, two = await asyncio.gather(request(), request())
        self.assertEqual({one.headers["x-route-cache"], two.headers["x-route-cache"]}, {"MISS", "HIT"})
        self.assertEqual(directions.await_count, 1)

    async def test_bounded_cache(self):
        with patch.object(main, "find_place", new_callable=AsyncMock, return_value=self.place), \
             patch.object(main, "get_car_route", new_callable=AsyncMock, return_value=self.route):
            for i in range(main.ROUTE_CACHE_MAX_ENTRIES + 2):
                result = await self.client.get("/api/route", params={"origin": "서울역", "destination": f"장소{i}"})
                self.assertEqual(result.status_code, 200)
        self.assertEqual(len(main.route_cache), main.ROUTE_CACHE_MAX_ENTRIES)


if __name__ == "__main__":
    unittest.main()
