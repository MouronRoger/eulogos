"""Performance monitoring middleware.

This middleware tracks request execution time and logs performance metrics.
"""

import time
from typing import Callable

from fastapi import Request, Response
from loguru import logger
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp


class PerformanceMiddleware(BaseHTTPMiddleware):
    """Middleware for monitoring request performance."""

    def __init__(self, app: ASGIApp, log_threshold_ms: int = 100):
        """Initialize the middleware.

        Args:
            app: The ASGI application
            log_threshold_ms: Threshold in milliseconds to log slow requests
        """
        super().__init__(app)
        self.log_threshold_ms = log_threshold_ms

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process the request and track execution time.

        Args:
            request: The incoming request
            call_next: The next middleware/route handler

        Returns:
            The response from the route handler
        """
        start_time = time.time()

        # Process the request
        response = await call_next(request)

        # Calculate execution time
        process_time = (time.time() - start_time) * 1000

        # Add processing time header
        response.headers["X-Process-Time"] = f"{process_time:.2f}ms"

        # Log slow requests
        if process_time > self.log_threshold_ms:
            logger.warning(
                f"SLOW REQUEST: {request.method} {request.url.path} - {process_time:.2f}ms",
                extra={
                    "method": request.method,
                    "path": request.url.path,
                    "query_params": str(request.query_params),
                    "process_time": process_time,
                    "status_code": response.status_code,
                },
            )
        else:
            logger.debug(
                f"REQUEST: {request.method} {request.url.path} - {process_time:.2f}ms",
                extra={
                    "method": request.method,
                    "path": request.url.path,
                    "process_time": process_time,
                    "status_code": response.status_code,
                },
            )

        return response
