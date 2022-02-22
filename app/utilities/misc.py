import hashlib
from typing import Optional

from starlette.requests import Request


def get_address(request: Request, hashed: bool = True) -> str:
    ip: Optional[str] = request.headers.get("cf-connecting-ip", None)
    ip: Optional[str] = request.client.host if ip is None else ip
    return hashlib.sha1(str(ip).encode("utf-8")).hexdigest() if hashed else str(ip)
