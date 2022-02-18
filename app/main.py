import asyncio
import hashlib
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

import config
from api.geolocate import GeolocateResponse
from api.omeglestats import StatResponse
from models.mysql import create_template
from models.response import FilledResponse, StatsPayload
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


@app.post("/chromegle/stats", tags=['Chromegle'], dependencies=[Depends(RateLimiter(times=3, seconds=2))])
async def post_chromegle_stats(payload: StatsPayload, request: Request):
    """

    NGINX REQUIREMENTS

    REQUIRES --proxy-headers flag
    proxy_set_header   X-Real-IP        $remote_addr;
    proxy_set_header   X-Forwarded-For  $proxy_add_x_forwarded_for;

    """

    if not payload.action or not payload.signature or (hashlib.sha1(str(request.client.host).encode("utf-8")).hexdigest() != payload.signature):
        return FilledResponse(status=400, message="Unauthorized Request").serialize()

    await log_statistics(signature=payload.signature, action=payload.action, sql_pool=app.sql_pool)
    return FilledResponse(status=200, message="Received Statistics").serialize()


@app.get("/chromegle/stats", tags=['Chromegle'], dependencies=[Depends(RateLimiter(times=5, seconds=1))])
async def get_chromegle_stats(request: Request):
    stats: dict = await get_statistics(sql_pool=app.sql_pool, redis=app.redis)

    return FilledResponse(
        status=200,
        message="Successfully retrieved statistics",
        payload=stats
    ).serialize()


"""
@app.post("/omegle/classify_image", tags=['Omegle'], dependencies=[Depends(RateLimiter(times=3, seconds=2))])
async def detect_nsfw(payload: NSFWPayload):
    return (await NSFWResponse(payload).complete()).serialize()
"""


@app.get("/omegle/geolocate/{address}", tags=['Omegle'], dependencies=[Depends(RateLimiter(times=1, seconds=1))])
async def geolocate_ip(address: str):
    return (await GeolocateResponse(address, app.redis).complete()).serialize()


@app.get("/omegle/stats", tags=['Omegle'], dependencies=[Depends(RateLimiter(times=3, seconds=2))])
async def retrieve_omegle_stats():
    return (await StatResponse().complete()).serialize()


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=config.PORT, log_level="info")
