import time

from app.middleware.rate_limit import InMemoryRateLimiter


def test_allows_up_to_the_limit():
    limiter = InMemoryRateLimiter(max_requests=3, window_seconds=60)
    assert limiter.allow("client-a")
    assert limiter.allow("client-a")
    assert limiter.allow("client-a")


def test_blocks_beyond_the_limit():
    limiter = InMemoryRateLimiter(max_requests=2, window_seconds=60)
    assert limiter.allow("client-b")
    assert limiter.allow("client-b")
    assert not limiter.allow("client-b")


def test_different_keys_are_independent():
    limiter = InMemoryRateLimiter(max_requests=1, window_seconds=60)
    assert limiter.allow("client-c")
    assert limiter.allow("client-d")  # different key, own budget


def test_window_expiry_allows_requests_again():
    limiter = InMemoryRateLimiter(max_requests=1, window_seconds=1)
    assert limiter.allow("client-e")
    assert not limiter.allow("client-e")
    time.sleep(1.1)
    assert limiter.allow("client-e")
