"""
Rate limiting foundation.

MVP implementation: a simple in-memory fixed-window counter per client IP.
This is intentionally basic — good enough for a single-process local/pilot
deployment, and explicitly NOT sufficient once the API runs as more than one
process/instance (an in-memory counter isn't shared across processes).

Upgrade path when that matters: back this same interface with Redis
(already on the free-tools roadmap) — call sites don't change.

Not yet wired into every route; per Step 10, this phase establishes the
*design and interface* required for OTP-request and image-upload endpoints
to use once those business modules exist, plus a self-test to prove the
counter logic itself is correct.
"""
import time
from collections import defaultdict


class InMemoryRateLimiter:
    def __init__(self, max_requests: int, window_seconds: int = 60):
        self._max_requests = max_requests
        self._window_seconds = window_seconds
        self._hits: dict[str, list[float]] = defaultdict(list)

    def allow(self, key: str) -> bool:
        now = time.monotonic()
        window_start = now - self._window_seconds
        hits = [t for t in self._hits[key] if t > window_start]
        hits.append(now)
        self._hits[key] = hits
        return len(hits) <= self._max_requests
