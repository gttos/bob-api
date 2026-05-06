import time
from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import redis.asyncio as redis

from app.config.settings import settings

class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self._redis = None

    def _get_redis(self):
        if self._redis is None and settings.RATE_LIMIT_ENABLED:
             self._redis = redis.from_url(settings.REDIS_URL, decode_responses=True)
        return self._redis

    def _get_rate_limit_key(self, request: Request) -> str:
        # Simplistic key formatting for MVP, combining client IP and date
        client_ip = request.client.host if request.client else "unknown"
        date_str = time.strftime("%Y-%m-%d")
        return f"rate_limit:{client_ip}:{date_str}"

    async def dispatch(self, request: Request, call_next):
        if not settings.RATE_LIMIT_ENABLED:
            return await call_next(request)

        # Only applies to POST requests to endpoints containing "/generations"
        if request.method != "POST" or "/generations" not in request.url.path:
            return await call_next(request)

        redis_client = self._get_redis()
        if not redis_client:
            return await call_next(request)

        key = self._get_rate_limit_key(request)
        count = await redis_client.incr(key)

        if count == 1:
            await redis_client.expire(key, 86400)

        if count > settings.RATE_LIMIT_GENERATIONS_PER_DAY:
            ttl = await redis_client.ttl(key)
            return JSONResponse(
                status_code=429,
                content={
                    "error": "rate_limit_exceeded",
                    "limit": settings.RATE_LIMIT_GENERATIONS_PER_DAY,
                    "reset_in_seconds": ttl
                }
            )

        return await call_next(request)
