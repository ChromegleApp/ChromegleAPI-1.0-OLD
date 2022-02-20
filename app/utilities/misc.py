from starlette.requests import Request


def get_address(request: Request) -> str:
    ip: str = str(request.headers.get("cf-connecting-ip"))
    return str(request.client.host) if "None" else ip
