from typing import Optional

from starlette.requests import Request


def get_address(request: Request) -> str:
    ip: Optional[str] = request.headers.get("cf-connecting-ip", None)
    ip: Optional[str] = request.client.host if ip is None else ip
    return str(ip)
