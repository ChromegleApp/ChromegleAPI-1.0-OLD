from api import predict, app
from api.functions import download_image
from config import PORT
import os
import uvicorn
from pydantic import BaseModel
model = predict.load_model('nsfw_detector/nsfw_model.h5')


class Model(BaseModel):
    base64: bytes

@app.post("/nsfw")
async def detect_nsfw(payload: Model):

    if not payload.base64:
        return {"ERROR": "base64 PARAMETER EMPTY", "status": 0}

    image = await download_image(payload.base64)
    if not image:
        return {"ERROR": "Image supplied was invalid", "status": 0}

    try:
        results = predict.classify(model, image)
    except:
        return {"ERROR": "Failed to classify image", "status": 0}

    os.remove(image)
    results['status'] = 1
    hentai = results['data']['hentai']
    sexy = results['data']['sexy']
    porn = results['data']['porn']
    drawings = results['data']['drawings']
    neutral = results['data']['neutral']
    if neutral >= 25:
        results['data']['is_nsfw'] = False
        return results
    elif (sexy + porn + hentai) >= 70:
        results['data']['is_nsfw'] = True
        return results
    elif drawings >= 40:
        results['data']['is_nsfw'] = False
        return results
    else:
        results['data']['is_nsfw'] = False
        return results

if __name__ == "__main__":
    uvicorn.run("api:app", host="0.0.0.0", port=PORT, log_level="info")
