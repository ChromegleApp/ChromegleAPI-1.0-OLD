from __future__ import annotations

import base64
import io

import aioredis
from PIL import Image, ImageDraw, ImageFont

import config
from models.response import AsyncResponse


class DynamicStatsImage:
    MARGIN, SPACE_BETWEEN = 0, 0

    LARGE_FONT = ImageFont.truetype(config.Statistics.STATS_IMAGE_FONT_PATH, 30)
    SMALL_FONT = ImageFont.truetype(config.Statistics.STATS_IMAGE_FONT_PATH, 10)

    LARGE_LABEL_COLOUR: hex = "white"
    SMALL_LABEL_COLOUR: hex = "white"

    ONLINE_COUNT_LABEL = "Online Chromeglers"
    ONLINE_COUNT_SMALL_LABEL_LENGTH = SMALL_FONT.getsize(ONLINE_COUNT_LABEL)[0]

    LARGE_FONT_HEIGHT = LARGE_FONT.size

    def __init__(self, online_count: str):
        self.online_count: str = online_count

    def generate(self) -> Image:
        IMAGE_WIDTH, IMAGE_HEIGHT = 150, 57
        image: Image = Image.new("RGBA", (IMAGE_WIDTH, IMAGE_HEIGHT))
        draw: ImageDraw = ImageDraw.Draw(image)

        draw.text(
            ((IMAGE_WIDTH / 2 - self.LARGE_FONT.getsize(self.online_count)[0] / 2), self.MARGIN / 2 + 4),
            self.online_count, font=self.LARGE_FONT, fill=self.LARGE_LABEL_COLOUR)

        draw.text(
            ((IMAGE_WIDTH / 2 - self.ONLINE_COUNT_SMALL_LABEL_LENGTH / 2), self.MARGIN / 2 + self.LARGE_FONT_HEIGHT + 7),
            self.ONLINE_COUNT_LABEL, font=self.SMALL_FONT, fill=self.SMALL_LABEL_COLOUR
        )

        return image


class StatsImageResponse(AsyncResponse):

    def __init__(self, stats_data: dict, redis: aioredis.Redis):
        super().__init__()
        self.stats_data: dict = stats_data
        self.redis: aioredis.Redis = redis

    async def __generate_image(self) -> bytes:
        image: Image = DynamicStatsImage(f"{self.stats_data['online_users']:,}+").generate()

        buffered = io.BytesIO()
        image.save(buffered, format="PNG")
        return base64.b64encode(buffered.getvalue())

    async def get_image(self) -> str:
        # Get from Redis Cache if available
        image = await self.redis.get("chromegle:stats:statistics-image")
        if image is not None:
            return image.decode("utf-8")

        # Get and enter into Redis Cache
        image = await self.__generate_image()
        await self.redis.set("chromegle:stats:statistics-image", image, ex=config.Statistics.STATS_IMAGE_EXPIREY)

    async def complete(self) -> StatsImageResponse:
        self._payload, self._status, self._message = await self.get_image(), 200, "Successfully retrieved Omegle's website stats as an image"
        return self
