import os
from typing import Mapping, List

import uvicorn
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

import config

os.environ["CUDA_VISIBLE_DEVICES"] = "-1"
from api.classify_image import NSFWPayload, NSFWResponse


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

    def __init__(self, **extra: dict):
        super().__init__(**self.__set_identity(**extra))

        self.origins: List[str] = ["*"]
        self.add_middleware(
            CORSMiddleware,
            allow_origins=self.origins,
            allow_methods=self.origins,
            allow_headers=self.origins,
            allow_credentials=True
        )


app = ChromegleAPI()


@app.post("/nsfw")
async def detect_nsfw_legacy(payload: NSFWPayload):
    response: NSFWResponse = await NSFWResponse(payload).complete()
    json_response: dict = {"status": 0 if response.status != 200 else 1}
    json_response.update(response.payload if type(response.payload) == dict else {})
    return json_response


@app.post("/classify_image")
async def detect_nsfw(payload: NSFWPayload):
    return (await NSFWResponse(payload).complete()).serialize()


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=config.PORT, log_level="info")
