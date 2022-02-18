from __future__ import annotations

import random
import string
from typing import Union

import aiohttp

from models.response import AsyncResponse


class StatResponse(AsyncResponse):

    def __init__(self):
        super().__init__()

    @classmethod
    def __generate_request_url(cls):
        no_cache = random.randint(1000000000000000, 9999999999999999)
        rand_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=7))
        return f"https://front38.omegle.com/status?nocache=0.{no_cache}&randid={rand_id}"

    @classmethod
    async def request_data(cls) -> Union[str, dict]:
        async with aiohttp.ClientSession() as session:
            async with session.get(cls.__generate_request_url()) as request:
                try:
                    return await request.json()
                except:
                    return await request.text()

    async def complete(self) -> StatResponse:
        response: dict = await self.request_data()

        if not response or type(response) != dict:
            self._payload, self._status, self._message = self._payload, 500, "Failed to grab stats from Omegle's website"
            return self

        # Remove Extra Data
        response.pop("rtmfp", None)
        response.pop("antinudepercent", None)
        response.pop("force_unmon", None)
        response.pop("timestamp", None)

        # Add New Data
        response["servercount"] = len(response.get("online_count", []))
        response["antinudeservercount"] = len(response.get("antinudeservers", []))

        self._payload, self._status, self._message = response, 200, "Successfully retrieved Omegle's website stats"
        return self
