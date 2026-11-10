import asyncio
import time
from collections import defaultdict
from typing import Dict, List


class RateLimiter:
    """Token bucket rate limiter for platform requests."""

    def __init__(self, requests_per_minute: int = 30):
        self.requests_per_minute = requests_per_minute
        self.tokens: Dict[str, List[float]] = defaultdict(list)
        self._lock = asyncio.Lock()

    async def acquire(self, platform: str) -> float:
        """Acquire a token for the given platform. Returns wait time in seconds."""
        async with self._lock:
            now = time.time()
            window_start = now - 60.0

            # Remove tokens outside the window
            self.tokens[platform] = [
                t for t in self.tokens[platform] if t > window_start
            ]

            if len(self.tokens[platform]) >= self.requests_per_minute:
                # Calculate wait time until oldest token expires
                oldest = min(self.tokens[platform])
                wait_time = oldest + 60.0 - now
                return max(wait_time, 0.1)

            self.tokens[platform].append(now)
            return 0.0

    async def wait_and_acquire(self, platform: str):
        """Wait if necessary, then acquire a token."""
        wait_time = await self.acquire(platform)
        if wait_time > 0:
            await asyncio.sleep(wait_time)
            await self.acquire(platform)

    def reset(self, platform: str = None):
        """Reset rate limit counters."""
        if platform:
            self.tokens.pop(platform, None)
        else:
            self.tokens.clear()


class AdaptiveRateLimiter:
    """Rate limiter that adapts based on platform responses."""

    def __init__(self, initial_rpm: int = 30):
        self.limiters: Dict[str, RateLimiter] = {}
        self.initial_rpm = initial_rpm
        self.backoff_multiplier: Dict[str, float] = defaultdict(lambda: 1.0)

    def get_limiter(self, platform: str) -> RateLimiter:
        if platform not in self.limiters:
            rpm = int(self.initial_rpm * self.backoff_multiplier[platform])
            self.limiters[platform] = RateLimiter(requests_per_minute=max(rpm, 1))
        return self.limiters[platform]

    async def wait_and_acquire(self, platform: str):
        """Wait if necessary, then acquire a token from the platform's limiter."""
        limiter = self.get_limiter(platform)
        await limiter.wait_and_acquire(platform)

    def report_rate_limit(self, platform: str):
        """Reduce rate limit when platform reports rate limiting."""
        self.backoff_multiplier[platform] *= 2.0
        # Recreate limiter with new rate
        old_limiter = self.limiters.pop(platform, None)
        if old_limiter:
            rpm = int(self.initial_rpm * self.backoff_multiplier[platform])
            self.limiters[platform] = RateLimiter(requests_per_minute=max(rpm, 1))

    def report_success(self, platform: str):
        """Gradually restore rate limit on successful requests."""
        if self.backoff_multiplier[platform] > 1.0:
            self.backoff_multiplier[platform] = max(
                1.0,
                self.backoff_multiplier[platform] * 0.9
            )