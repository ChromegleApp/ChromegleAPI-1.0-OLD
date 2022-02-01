import os
from typing import Mapping, List, Optional

import aioredis
import uvicorn
from fastapi import FastAPI, Depends
from fastapi_limiter import FastAPILimiter
from fastapi_limiter.depends import RateLimiter
from starlette.middleware.cors import CORSMiddleware

import config
from api.geolocate import GeolocateResponse
from api.site_stats import StatResponse

os.environ["CUDA_VISIBLE_DEVICES"] = "-1"
from api.classify_image import NSFWPayload, NSFWResponse


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


app = ChromegleAPI(
    config.REDIS_HOST,
    config.REDIS_PORT,
    config.REDIS_PASSWORD
)



@app.on_event("startup")
async def startup():
    app.redis = aioredis.Redis(host=app.redis_host, port=app.redis_port, password=app.redis_password)
    await FastAPILimiter.init(app.redis)


@app.post("/nsfw", tags=['Chromegle'], dependencies=[Depends(RateLimiter(times=3, seconds=10))])
async def detect_nsfw_legacy(payload: NSFWPayload):
    response: NSFWResponse = await NSFWResponse(payload).complete()
    json_response: dict = {"status": 0 if response.status != 200 else 1}
    json_response.update(response.payload if type(response.payload) == dict else {})
    return json_response


@app.post("/omegle/classify_image", tags=['Chromegle'], dependencies=[Depends(RateLimiter(times=3, seconds=10))])
async def detect_nsfw(payload: NSFWPayload):
    return (await NSFWResponse(payload).complete()).serialize()


@app.get("/omegle/geolocate", tags=['Chromegle'], dependencies=[Depends(RateLimiter(times=1, seconds=1))])
async def geolocate_ip(address: str):
    return (await GeolocateResponse(address, app.redis).complete()).serialize()


# TODO remember to return rate limit when done
@app.get("/omegle/stats", tags=['Omegle'], dependencies=[Depends(RateLimiter(times=3, seconds=2))])
async def retrieve_omegle_stats():
    return (await StatResponse().complete()).serialize()


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=config.PORT, log_level="info")
