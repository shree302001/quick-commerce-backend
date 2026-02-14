import logging
import sys
import json
import time
from typing import Any
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware


class StructuredLogger:
    def __init__(self, name: str = "app"):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)

        # Avoid duplicate handlers
        if not self.logger.handlers:
            handler = logging.StreamHandler(sys.stdout)
            # Simple JSON formatter
            handler.setFormatter(logging.Formatter("%(message)s"))
            self.logger.addHandler(handler)

    def _log(self, level: str, event: str, **kwargs: Any):
        log_entry = {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "level": level,
            "event": event,
            **kwargs,
        }
        self.logger.log(getattr(logging, level), json.dumps(log_entry))

    def info(self, event: str, **kwargs: Any):
        self._log("INFO", event, **kwargs)

    def error(self, event: str, **kwargs: Any):
        self._log("ERROR", event, **kwargs)

    def warning(self, event: str, **kwargs: Any):
        self._log("WARNING", event, **kwargs)


logger = StructuredLogger()


from app.core.db_events import get_query_count, reset_query_count, QUERY_COUNT_THRESHOLD


class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Any) -> Response:
        start_time = time.time()
        reset_query_count()  # Reset for this request context

        # Request context
        request_id = request.headers.get("X-Request-ID", "unknown")

        try:
            response = await call_next(request)
            process_time = (time.time() - start_time) * 1000  # ms
            q_count = get_query_count()

            log_data = {
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "process_time_ms": round(process_time, 2),
                "query_count": q_count,
                "request_id": request_id,
            }

            if q_count > QUERY_COUNT_THRESHOLD:
                logger.warning("high_query_count_detected", **log_data)
            else:
                logger.info("request_completed", **log_data)

            return response
        except Exception as e:
            process_time = (time.time() - start_time) * 1000
            logger.error(
                "request_failed",
                method=request.method,
                path=request.url.path,
                error=str(e),
                query_count=get_query_count(),
                process_time_ms=round(process_time, 2),
                request_id=request_id,
            )
            raise e


def add_cache_headers(response: Response, max_age: int = 60):
    """
    Helper to add Cache-Control headers to a response.
    """
    response.headers["Cache-Control"] = f"public, max-age={max_age}"
    return response
