import asyncio
import os
from asyncio import AbstractEventLoop
from typing import Mapping, List, Optional

import aiomysql
import aioredis
import uvicorn
from fastapi import FastAPI, Depends
from fastapi_limiter import FastAPILimiter
from fastapi_limiter.depends import RateLimiter
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import Response

import config
from api.classify_image import NSFWResponse, NSFWPayload
from api.geolocate import GeolocateResponse
from api.omeglestats import StatResponse
from api.statsimage import StatsImageResponse
from models.mysql import create_template
from models.response import FilledResponse
from utilities.misc import get_address
from utilities.statistics.geo_auth import authorized
from utilities.statistics.statistics import log_statistics, get_statistics

os.environ["CUDA_VISIBLE_DEVICES"] = "-1"


# from api.classify_image import NSFWPayload, NSFWResponse


# TODO rate limiting

class ChromegleAPI(FastAPI):

    @classmethod
    def __set_identity(cls, **extra: Mapping):
        new: Mapping = {
            "docs_url": '/',
            "redoc_url": "/docs",
            "title": "Chromegle Internal API",
            "version": "1.0.0",
            "openapi_url": "/api-docs",
            "description": "Internal API for the Chromegle Chrome Extension",
        }
        extra.update(new)
        return extra

    def __init__(self, redis_host: str, redis_port: int, redis_password: str, **extra: dict):
        super().__init__(**self.__set_identity(**extra))

        self.redis: Optional[aioredis.Redis] = None
        self.redis_host: str = redis_host
        self.redis_port: int = redis_port
        self.redis_password: str = redis_password

        self.origins: List[str] = ["*"]

        self.add_middleware(
            CORSMiddleware,
            allow_origins=self.origins,
            allow_methods=self.origins,
            allow_headers=self.origins,
            allow_credentials=True
        )

        try:
            self.loop: AbstractEventLoop = asyncio.get_running_loop()
        except RuntimeError:
            self.loop: AbstractEventLoop = asyncio.get_event_loop()

        self.sql_pool: Optional[aiomysql.Pool] = None


app: ChromegleAPI = ChromegleAPI(
    config.Redis.HOST,
    config.Redis.PORT,
    config.Redis.PASSWORD
)


@app.on_event("startup")
async def startup():
    print("Go for launch!")

    # Create SQL Pool
    app.sql_pool = await aiomysql.create_pool(
        host=config.MariaDB.HOST, port=config.MariaDB.PORT,
        user=config.MariaDB.USERNAME, password=config.MariaDB.PASSWORD,
        db=config.MariaDB.DATABASE, loop=app.loop
    )

    # Create Template
    await create_template(app.sql_pool, file_path=config.MariaDB.SQL_TEMPLATE_PATH)

    # Create Redis
    app.redis = aioredis.Redis(host=app.redis_host, port=app.redis_port, password=app.redis_password)
    await FastAPILimiter.init(app.redis)


@app.post("/chromegle/stats", tags=['Chromegle'], dependencies=[Depends(RateLimiter(times=50, seconds=10))])
async def post_chromegle_stats(action: str, request: Request):
    await log_statistics(signature=get_address(request), action=action, sql_pool=app.sql_pool)
    return FilledResponse(status=200, message="Received Statistics").serialize()


@app.get("/chromegle/stats", tags=['Chromegle'])
async def get_chromegle_stats(request: Request):
    stats: dict = await get_statistics(sql_pool=app.sql_pool, redis=app.redis)
    image: str = str((await StatsImageResponse(stats, app.redis).complete()).payload)
    stats["image"] = image
    stats["address"] = get_address(request, hashed=False)

    return FilledResponse(
        status=200,
        message="Successfully retrieved statistics",
        payload=stats
    ).serialize()


@app.post("/omegle/classify_image", tags=['Omegle'], dependencies=[Depends(RateLimiter(times=3, seconds=2))])
async def detect_nsfw(payload: NSFWPayload):
    return (await NSFWResponse(payload).complete()).serialize()


@app.get("/omegle/geolocate/{address}", tags=['Omegle'], dependencies=[Depends(RateLimiter(times=1, seconds=1))], include_in_schema=False)
async def geolocate_ip(address: str, request: Request):
    if not await authorized(request, app.sql_pool):
        return Response(status_code=403)

    return (await GeolocateResponse(address, app.redis).complete()).serialize()


@app.get("/omegle/stats", tags=['Omegle'], dependencies=[Depends(RateLimiter(times=3, seconds=2))])
async def retrieve_omegle_stats():
    return (await StatResponse().complete()).serialize()


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=config.PORT, log_level="info", proxy_headers=True)
