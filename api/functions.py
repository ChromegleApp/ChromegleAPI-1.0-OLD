import base64

from config import MAX_IMAGE_SIZE
from random import randint
import aiohttp
import aiofiles

MAX_IMAGE_SIZE = MAX_IMAGE_SIZE * 1000000


async def download_image(image_data):
    file_name = f"{randint(6969, 6999)}.jpg"

    try:
        f = await aiofiles.open(file_name, mode='wb')
        await f.write(base64.decodebytes(image_data))
        await f.close()
    except:
        return None

    return file_name
