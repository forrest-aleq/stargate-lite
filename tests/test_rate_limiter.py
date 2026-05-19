"""Rate limiter regression tests for Stargate execute traffic."""

from __future__ import annotations

from typing import Any

from app.rate_limiter import RateLimiter


class FakeRedis:
    """Minimal sorted-set Redis stub for rate limiter tests."""

    def __init__(self) -> None:
        self._sets: dict[str, dict[str, float]] = {}

    def zremrangebyscore(self, key: str, min_score: float, max_score: float) -> int:
        bucket = self._sets.setdefault(key, {})
        to_remove = [
            member
            for member, score in bucket.items()
            if float(min_score) <= score <= float(max_score)
        ]
        for member in to_remove:
            bucket.pop(member, None)
        return len(to_remove)

    def zcard(self, key: str) -> int:
        return len(self._sets.get(key, {}))

    def zadd(self, key: str, mapping: dict[str, float]) -> int:
        bucket = self._sets.setdefault(key, {})
        bucket.update(mapping)
        return len(mapping)

    def expire(self, key: str, ttl: int) -> bool:
        return True

    def zrange(self, key: str, start: int, stop: int, withscores: bool = False) -> list[Any]:
        bucket = self._sets.get(key, {})
        items = sorted(bucket.items(), key=lambda item: item[1])
        if stop == -1:
            selected = items[start:]
        else:
            selected = items[start : stop + 1]
        if withscores:
            return selected
        return [member for member, _ in selected]


def _build_limiter(fake_redis: FakeRedis) -> RateLimiter:
    limiter = RateLimiter()
    limiter._redis = fake_redis
    limiter._initialized = True
    return limiter


def test_denied_requests_do_not_extend_window(monkeypatch) -> None:
    fake_redis = FakeRedis()
    limiter = _build_limiter(fake_redis)

    monkeypatch.setattr("app.rate_limiter.RATE_LIMIT_REQUESTS", 1)
    monkeypatch.setattr("app.rate_limiter.RATE_LIMIT_WINDOW_SECONDS", 60)
    monkeypatch.setattr("app.rate_limiter.RATE_LIMIT_READ_REQUESTS", 1)
    monkeypatch.setattr("app.rate_limiter.RATE_LIMIT_READ_WINDOW_SECONDS", 60)
    monkeypatch.setattr("app.rate_limiter.time.time", lambda: 1000.0)

    allowed, info = limiter.check_rate_limit("org-test", "vendor.list", {"verb_tier": 0})
    assert allowed is True
    assert info["bucket"] == "read"

    key = "stargate:ratelimit:org-test:read"
    assert fake_redis.zcard(key) == 1

    allowed, info = limiter.check_rate_limit("org-test", "vendor.list", {"verb_tier": 0})
    assert allowed is False
    assert info["remaining"] == 0
    assert fake_redis.zcard(key) == 1

    allowed, _ = limiter.check_rate_limit("org-test", "vendor.list", {"verb_tier": 0})
    assert allowed is False
    assert fake_redis.zcard(key) == 1


def test_read_only_capabilities_use_read_bucket(monkeypatch) -> None:
    fake_redis = FakeRedis()
    limiter = _build_limiter(fake_redis)

    monkeypatch.setattr("app.rate_limiter.RATE_LIMIT_REQUESTS", 1)
    monkeypatch.setattr("app.rate_limiter.RATE_LIMIT_WINDOW_SECONDS", 60)
    monkeypatch.setattr("app.rate_limiter.RATE_LIMIT_READ_REQUESTS", 3)
    monkeypatch.setattr("app.rate_limiter.RATE_LIMIT_READ_WINDOW_SECONDS", 60)
    monkeypatch.setattr("app.rate_limiter.time.time", lambda: 2000.0)

    for _ in range(3):
        allowed, info = limiter.check_rate_limit("org-read", "vendor.list", {"verb_tier": 0})
        assert allowed is True
        assert info["bucket"] == "read"
        assert info["limit"] == 3

    allowed, info = limiter.check_rate_limit("org-read", "vendor.list", {"verb_tier": 0})
    assert allowed is False
    assert info["bucket"] == "read"
    assert info["limit"] == 3


def test_write_capabilities_stay_on_default_bucket(monkeypatch) -> None:
    fake_redis = FakeRedis()
    limiter = _build_limiter(fake_redis)

    monkeypatch.setattr("app.rate_limiter.RATE_LIMIT_REQUESTS", 1)
    monkeypatch.setattr("app.rate_limiter.RATE_LIMIT_WINDOW_SECONDS", 60)
    monkeypatch.setattr("app.rate_limiter.RATE_LIMIT_READ_REQUESTS", 3)
    monkeypatch.setattr("app.rate_limiter.RATE_LIMIT_READ_WINDOW_SECONDS", 60)
    monkeypatch.setattr("app.rate_limiter.time.time", lambda: 3000.0)

    allowed, info = limiter.check_rate_limit("org-write", "vendor.create", {"verb_tier": 2})
    assert allowed is True
    assert info["bucket"] == "default"
    assert info["limit"] == 1

    allowed, info = limiter.check_rate_limit("org-write", "vendor.create", {"verb_tier": 2})
    assert allowed is False
    assert info["bucket"] == "default"
    assert info["limit"] == 1
