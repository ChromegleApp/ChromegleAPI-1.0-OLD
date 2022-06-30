import hashlib
from typing import Optional

from starlette.requests import Request


def hash_address(ip: str) -> str:
    return hashlib.sha1(ip.encode("utf-8")).hexdigest()


def get_address(request: Request, hashed: bool = True) -> str:
    ip: Optional[str] = request.headers.get("cf-connecting-ip", None)
    ip: Optional[str] = str(request.client.host if ip is None else ip)
    return hash_address(ip) if hashed else ip
