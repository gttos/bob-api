import time
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
import structlog

logger = structlog.get_logger("request_logger")

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.perf_counter()

        try:
            response = await call_next(request)
            duration_ms = (time.perf_counter() - start_time) * 1000

            # Structlog context vars already bound by CorrelationIDMiddleware

            log_data = {
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_ms": duration_ms
            }

            if response.status_code >= 500:
                logger.error("Request failed", **log_data)
            elif response.status_code >= 400:
                logger.warning("Request failed with client error", **log_data)
            else:
                logger.info("Request successful", **log_data)

            return response

        except Exception as e:
            duration_ms = (time.perf_counter() - start_time) * 1000
            logger.error(
                "Unhandled exception processing request",
                method=request.method,
                path=request.url.path,
                status_code=500,
                duration_ms=duration_ms,
                error=str(e),
                exc_info=True
            )
            raise
