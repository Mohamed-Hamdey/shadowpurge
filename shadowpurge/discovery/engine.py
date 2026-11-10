import asyncio
import json
import os
from typing import List, Dict, Any
import httpx

from shadowpurge.core.exceptions import (
    DiscoveryError,
    NetworkError,
    TimeoutError,
    RateLimitError,
    RegistryError,
)
from shadowpurge.core.retry import retry
from shadowpurge.core.ratelimit import AdaptiveRateLimiter


class DiscoveryEngine:
    def __init__(
        self,
        platforms_file: str = "data/platforms.json",
        max_concurrent: int = 10,
        timeout: float = 10.0,
    ):
        self.platforms_file = platforms_file
        self.max_concurrent = max_concurrent
        self.timeout = timeout
        self.platforms = self._load_platforms()
        self.rate_limiter = AdaptiveRateLimiter(initial_rpm=30)
        self._semaphore = asyncio.Semaphore(max_concurrent)

    def _load_platforms(self) -> List[Dict[str, Any]]:
        if not os.path.exists(self.platforms_file):
            raise RegistryError(
                f"Platform registry file not found: {self.platforms_file}",
                error_code="REGISTRY_FILE_MISSING",
            )
        try:
            with open(self.platforms_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("platforms", [])
        except json.JSONDecodeError as e:
            raise RegistryError(
                f"Invalid JSON in platform registry: {e}",
                error_code="REGISTRY_INVALID_JSON",
            )

    @retry(max_retries=3, delay=1.0, backoff=2.0)
    async def _check_profile(
        self, client: httpx.AsyncClient, platform: Dict[str, Any], target: str
    ) -> Dict[str, Any]:
        """Check for a specific target (username, email, or phone) on a platform."""
        url = platform["url_template"].format(target)
        result = {
            "name": platform["name"],
            "category": platform["category"],
            "url": url,
            "deletion_url": platform["deletion_url"],
            "removal_instructions": platform["removal_instructions"],
            "automation_supported": platform.get("automation_supported", False),
            "found": False,
            "status_code": None,
        }

        platform_name = platform["name"]

        async with self._semaphore:
            # Apply adaptive rate limiting
            await self.rate_limiter.wait_and_acquire(platform_name)

            try:
                # Base headers
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
                    "Accept-Language": "en-US,en;q=0.9",
                    "Accept-Encoding": "gzip, deflate, br",
                    "Connection": "keep-alive",
                    "Upgrade-Insecure-Requests": "1",
                    "Sec-Fetch-Dest": "document",
                    "Sec-Fetch-Mode": "navigate",
                    "Sec-Fetch-Site": "none",
                    "Sec-Fetch-User": "?1",
                    "Cache-Control": "max-age=0",
                }

                # Merge platform-specific headers if provided
                if "headers" in platform:
                    headers.update(platform["headers"])

                response = await client.get(
                    url, headers=headers, follow_redirects=True, timeout=self.timeout
                )
                result["status_code"] = response.status_code

                if response.status_code == 200:
                    content = response.text.lower()
                    if (
                        "not found" in content
                        or "user not found" in content
                        or "no longer exists" in content
                    ):
                        result["found"] = False
                    else:
                        result["found"] = True
                        self.rate_limiter.report_success(platform_name)
                elif response.status_code == 429:
                    self.rate_limiter.report_rate_limit(platform_name)
                    result["error"] = "Rate limited by platform"
                elif response.status_code in (403, 503, 999):
                    # 999 is LinkedIn's custom rate limit/blocking code
                    self.rate_limiter.report_rate_limit(platform_name)
                    result["error"] = "Platform blocked automated access (rate limited)"
                elif response.status_code >= 500:
                    raise NetworkError(
                        f"Server error from {platform_name}: HTTP {response.status_code}",
                        retryable=True,
                    )

            except httpx.TimeoutException as e:
                result["error"] = "Request timed out"
                raise TimeoutError(
                    f"Timeout scanning {platform_name}", original_exception=e
                )
            except httpx.ConnectError as e:
                result["error"] = f"Connection failed: {e}"
                raise NetworkError(
                    f"Connection failed for {platform_name}", original_exception=e
                )
            except httpx.HTTPError as e:
                result["error"] = f"HTTP error: {e}"
                raise NetworkError(
                    f"HTTP error scanning {platform_name}", original_exception=e
                )
            except (NetworkError, TimeoutError):
                raise
            except Exception as e:
                result["error"] = f"Unexpected error: {e}"

        return result

    async def scan(self, username: str) -> List[Dict[str, Any]]:
        async with httpx.AsyncClient() as client:
            tasks = [self._check_profile(client, p, username) for p in self.platforms]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Convert any unhandled exceptions to error results
            processed_results = []
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    platform = self.platforms[i]
                    processed_results.append(
                        {
                            "name": platform["name"],
                            "category": platform["category"],
                            "url": platform["url_template"].format(username),
                            "deletion_url": platform["deletion_url"],
                            "removal_instructions": platform["removal_instructions"],
                            "automation_supported": platform.get(
                                "automation_supported", False
                            ),
                            "found": False,
                            "status_code": None,
                            "error": f"Scan failed: {result}",
                        }
                    )
                else:
                    processed_results.append(result)

            return processed_results


class PlatformRegistry:
    def __init__(self, platforms_file: str = "data/platforms.json"):
        self.platforms_file = platforms_file
        self.platforms = self._load_platforms()

    def _load_platforms(self) -> List[Dict[str, Any]]:
        if not os.path.exists(self.platforms_file):
            raise RegistryError(
                f"Platform registry file not found: {self.platforms_file}",
                error_code="REGISTRY_FILE_MISSING",
            )
        try:
            with open(self.platforms_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("platforms", [])
        except json.JSONDecodeError as e:
            raise RegistryError(
                f"Invalid JSON in platform registry: {e}",
                error_code="REGISTRY_INVALID_JSON",
            )

    def add_platform(self, platform: Dict[str, Any]) -> None:
        required_fields = {
            "name",
            "url_template",
            "category",
            "deletion_url",
            "removal_instructions",
        }
        if not required_fields.issubset(platform.keys()):
            raise RegistryError(
                f"Platform must contain all required fields: {required_fields}",
                error_code="REGISTRY_MISSING_FIELDS",
            )
        self.platforms.append(platform)
        self._save_platforms()

    def _save_platforms(self) -> None:
        try:
            with open(self.platforms_file, "w", encoding="utf-8") as f:
                json.dump(
                    {"platforms": self.platforms}, f, indent=2, ensure_ascii=False
                )
        except IOError as e:
            raise RegistryError(
                f"Failed to save platform registry: {e}",
                error_code="REGISTRY_SAVE_FAILED",
            )

    def get_platforms(self) -> List[Dict[str, Any]]:
        return self.platforms

    def get_platform_by_name(self, name: str) -> Dict[str, Any]:
        for platform in self.platforms:
            if platform["name"].lower() == name.lower():
                return platform
        raise RegistryError(
            f"Platform '{name}' not found", error_code="PLATFORM_NOT_FOUND"
        )

    def remove_platform(self, name: str) -> None:
        platform = self.get_platform_by_name(name)
        self.platforms.remove(platform)
        self._save_platforms()

    def get_categories(self) -> List[str]:
        categories = [platform["category"] for platform in self.platforms]
        return list(set(categories))
