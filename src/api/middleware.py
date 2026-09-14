import time
from collections import deque
from typing import Deque, Dict

from fastapi import Request, Response, status
from starlette.middleware.base import BaseHTTPMiddleware

from src.core.metrics import metrics_collector


class SlidingWindowRateLimiter(BaseHTTPMiddleware):
    """In-memory sliding window rate limiter."""

    def __init__(self, app, max_requests_per_minute: int = 200):
        super().__init__(app)
        self.max_requests = max_requests_per_minute
        self.window_seconds = 60.0
        self.clients: Dict[str, Deque[float]] = {}

    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host if request.client else "unknown"
        now = time.time()

        if client_ip not in self.clients:
            self.clients[client_ip] = deque()

        queue = self.clients[client_ip]
        while queue and queue[0] <= now - self.window_seconds:
            queue.popleft()

        if len(queue) >= self.max_requests:
            return Response(
                content='{"detail": "Too many requests. Rate limit exceeded."}',
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                media_type="application/json"
            )

        queue.append(now)
        return await call_next(request)


class TelemetryMiddleware(BaseHTTPMiddleware):
    """Tracks HTTP request counts and latency metrics."""

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        metrics_collector.record_request(request.method, request.url.path, response.status_code)
        return response
