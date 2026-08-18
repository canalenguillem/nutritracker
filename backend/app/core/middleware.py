import logging
from time import perf_counter
from uuid import UUID, uuid4

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from app.core.logging import bind_request_id, reset_request_id

logger = logging.getLogger(__name__)


class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        request_id = self._request_id(request.headers.get("X-Request-ID"))
        request.state.request_id = request_id
        token = bind_request_id(request_id)
        started_at = perf_counter()
        status_code = 500

        try:
            response = await call_next(request)
            status_code = response.status_code
            response.headers["X-Request-ID"] = request_id
            return response
        finally:
            latency_ms = round((perf_counter() - started_at) * 1000, 2)
            logger.info(
                "http_request_completed",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": status_code,
                    "latency_ms": latency_ms,
                },
            )
            reset_request_id(token)

    @staticmethod
    def _request_id(value: str | None) -> str:
        if value is not None:
            try:
                return str(UUID(value))
            except ValueError:
                pass
        return str(uuid4())
