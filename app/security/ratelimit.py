"""Shared rate limiter used to throttle abuse-prone endpoints (e.g. /auth).

Keying is by client IP. Behind Railway's edge proxy the real client address
arrives in ``X-Forwarded-For``; we honour the first hop there and fall back to
the socket peer for direct/local connections.
"""
from slowapi import Limiter
from slowapi.util import get_remote_address
from starlette.requests import Request

from app.config import RATE_LIMIT_ENABLED


def client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        # Left-most entry is the original client.
        return forwarded.split(",")[0].strip()
    return get_remote_address(request)


limiter = Limiter(key_func=client_ip, enabled=RATE_LIMIT_ENABLED)
