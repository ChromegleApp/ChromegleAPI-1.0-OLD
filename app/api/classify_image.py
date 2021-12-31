from __future__ import annotations

import base64
import os
import uuid
from typing import Optional

import aiofiles
from pydantic import BaseModel

from models.response import AsyncResponse
from utilities import nsfw_predict


class NSFWPayload(BaseModel):
    base64: bytes


class NSFWResponse(AsyncResponse):
    MODEL = nsfw_predict.load_model('resources/nsfw_model.h5')

    def __init__(self, nsfw_payload: NSFWPayload):
        super().__init__()
        self.nsfw_payload: NSFWPayload = nsfw_payload

    @classmethod
    async def save_image(cls, payload: bytes, file_name: str = f"./resources/nsfw_images/{uuid.uuid4()}.jpg") -> Optional[str]:

        try:

            async with aiofiles.open(file_name, mode="wb") as file:
                await file.write(base64.decodebytes(payload))
                await file.close()

        except:

            return None

        return file_name

    @classmethod
    def classify_model(cls, model, image_path):

        results: Optional[dict] = None

        try:

            results = nsfw_predict.classify(model, image_path)

        except:

            pass

        return results

    @classmethod
    def remove_image(cls, image_path):

        try:

            os.remove(image_path)

        except:

            pass

    @classmethod
    def is_nsfw(cls, results: dict):
        data = results['data']

        if data['neutral'] >= 45:
            nsfw = False

        elif (data['sexy'] + data['porn'] + data['hentai']) >= 70:
            nsfw = True

        else:
            nsfw = False

        results['data']['is_nsfw'] = nsfw
        return results

    async def complete(self) -> NSFWResponse:

        file_name: str = await self.save_image(self.nsfw_payload.base64)

        # Failed to do it
        if not file_name:
            self._status, self._message = 400, "The photo you submitted was unable to be read by the system (did you supply an image?)"
            return self

        results: Optional[dict] = self.classify_model(self.MODEL, file_name)

        if not results:
            self._status, self._message = 500, "Failed to classify the requested image due to an error (perhaps an invalid image?)"
            return self

        self._payload, self._status, self._message = self.is_nsfw(results), 200, "Successfully classified the requested image"
        return self
