from __future__ import annotations

import base64
import json
from typing import Optional, Dict

import aiohttp
import aioredis

from models.response import AsyncResponse


class GeolocateResponse(AsyncResponse):
    """
    Using the https://geojs.io Open-Source IP Geolocation API

    """

    def __init__(self, ip: str, redis: aioredis.Redis):
        super().__init__()
        self.ip: str = ip
        self.redis: aioredis.Redis = redis

    @classmethod
    async def request_ip(cls, ip: str):

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"https://get.geojs.io/v1/ip/geo/{ip}.json") as request:
                    return await request.json()
        except:
            return None

    async def retrieve_cached(self, ip: str) -> Optional[Dict]:
        result = await self.redis.get(f"chromegle:geolocate:{ip}")

        # Not found
        if result is None:
            return None

        try:
            return json.loads(result.decode('utf-8'))
        except:
            return None


    async def update_cached(self, ip: str, data: dict) -> None:

        # Update cached data
        if ip is not None and len(ip) > 0:
            await self.redis.set(f"chromegle:geolocate:{ip}", json.dumps(data), ex=7200)


    async def complete(self) -> GeolocateResponse:

        # Retrieve from cache
        response: Optional[Dict] = await self.retrieve_cached(self.ip)

        # If not found in cache, get
        if response is None:
            response: Optional[Dict] = await self.request_ip(self.ip)

        # If not found
        if not response or type(response) != dict:
            self._payload, self._status, self._message = self._payload, 500, f"Failed to grab geolocation data for {self.ip}"
            return self

        await self.update_cached(self.ip, response)
        self._payload, self._status, self._message = response, 200, f"Successfully retrieved geolocation data for {self.ip}"

        return self
