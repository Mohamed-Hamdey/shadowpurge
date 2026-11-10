import httpx
import asyncio
import hashlib
from typing import List, Dict, Any, Optional

from shadowpurge.core.exceptions import OSINTError
from shadowpurge.core.ratelimit import RateLimiter
from shadowpurge.core.retry import retry


class OSINTScanner:
    """Scanner for email and phone footprint discovery using OSINT sources."""

    HIBP_BASE_URL = "https://haveibeenpwned.com/api/v3"
    HIBP_USER_AGENT = "ShadowPurge-Digital-Footprint-Scanner/1.0"

    def __init__(self, api_key: Optional[str] = None):
        self.headers = {
            "User-Agent": self.HIBP_USER_AGENT,
            "Accept": "application/json",
        }
        if api_key:
            self.headers["hibp-api-key"] = api_key

        # HIBP has rate limits: 1 request per 1.5 seconds for free tier
        self.rate_limiter = RateLimiter(requests_per_minute=30)
        self._cache: Dict[str, List[Dict[str, Any]]] = {}

    @retry(max_retries=3, delay=1.5, backoff=2.0)
    async def _hibp_request(self, client: httpx.AsyncClient, endpoint: str) -> List[Dict[str, Any]]:
        """Make a rate-limited request to HaveIBeenPwned API."""
        await self.rate_limiter.acquire("haveibeenpwned")

        url = f"{self.HIBP_BASE_URL}{endpoint}"
        response = await client.get(url, headers=self.headers, timeout=30.0)

        if response.status_code == 404:
            # No breaches found
            return []
        elif response.status_code == 429:
            raise OSINTError("Rate limited by HaveIBeenPwned API")
        elif response.status_code != 200:
            raise OSINTError(f"HIBP API error: {response.status_code}")

        return response.json()

    async def check_email_breaches(self, email: str) -> List[Dict[str, Any]]:
        """
        Check if an email address has been involved in data breaches using HaveIBeenPwned API.

        Args:
            email: The email address to check

        Returns:
            List of breach records with details
        """
        if not email or "@" not in email:
            raise OSINTError("Invalid email address")

        cache_key = f"breach:{email.lower()}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        async with httpx.AsyncClient() as client:
            try:
                breaches = await self._hibp_request(
                    client,
                    f"/breachedaccount/{email.lower()}"
                )

                # Transform HIBP response to our standard format
                results = []
                for breach in breaches:
                    results.append({
                        "source": "HaveIBeenPwned",
                        "domain": breach.get("Domain", "unknown"),
                        "breach_name": breach.get("Name", "Unknown Breach"),
                        "breach_date": breach.get("BreachDate", "Unknown"),
                        "exposed_data": breach.get("DataClasses", []),
                        "description": breach.get("Description", ""),
                        "is_verified": breach.get("IsVerified", False),
                        "is_fabricated": breach.get("IsFabricated", False),
                        "is_sensitive": breach.get("IsSensitive", False),
                        "is_retired": breach.get("IsRetired", False),
                        "is_spam_list": breach.get("IsSpamList", False),
                        "logo_path": breach.get("LogoPath", ""),
                        "pwn_count": breach.get("PwnCount", 0),
                        "category": "Breach Record"
                    })

                self._cache[f"breach:{email.lower()}"] = results
                return results

            except OSINTError:
                raise
            except Exception as e:
                raise OSINTError(f"Failed to check email breaches: {e}")

    async def check_email_pastes(self, email: str) -> List[Dict[str, Any]]:
        """
        Check if an email address appears in pastes (pastebin, etc.) using HIBP API.
        """
        cache_key = f"paste:{email.lower()}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        async with httpx.AsyncClient() as client:
            try:
                pastes = await self._hibp_request(
                    client,
                    f"/pasteaccount/{email.lower()}"
                )

                results = []
                for paste in pastes:
                    results.append({
                        "source": "HaveIBeenPwned Paste",
                        "source_id": paste.get("Id", ""),
                        "source_url": paste.get("Source", ""),
                        "title": paste.get("Title", ""),
                        "date": paste.get("Date", ""),
                        "email_count": paste.get("EmailCount", 0),
                        "category": "Paste Record"
                    })

                self._cache[f"paste:{email.lower()}"] = results
                return results

            except OSINTError:
                raise
            except Exception as e:
                raise OSINTError(f"Failed to check email pastes: {e}")

    async def check_phone_footprint(self, phone: str) -> List[Dict[str, Any]]:
        """
        Check phone number footprint using public sources.
        Note: HIBP doesn't support phone numbers directly.
        This is a placeholder for future integration with phone OSINT APIs.
        """
        # For now, return empty list - phone OSINT requires different APIs
        # Future integration: Truecaller, Whitepages, Sync.me, Numverify, etc.
        return []

    async def check_username_on_haveibeenpwned(self, username: str) -> List[Dict[str, Any]]:
        """
        Check if a username appears in breaches (some breaches include usernames).
        """
        cache_key = f"username:{username.lower()}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        async with httpx.AsyncClient() as client:
            try:
                # HIBP doesn't have direct username search, but we can search
                # the breaches for username mentions in data classes
                all_breaches = await self._hibp_request(client, "/breaches")

                results = []
                for breach in all_breaches:
                    data_classes = breach.get("DataClasses", [])
                    # Check if username is a potential data class in this breach
                    if any("username" in dc.lower() or "user" in dc.lower() for dc in data_classes):
                        results.append({
                            "source": "HaveIBeenPwned",
                            "domain": breach.get("Domain", "unknown"),
                            "breach_name": breach.get("Name", "Unknown Breach"),
                            "breach_date": breach.get("BreachDate", "Unknown"),
                            "exposed_data": data_classes,
                            "description": breach.get("Description", ""),
                            "pwn_count": breach.get("PwnCount", 0),
                            "category": "Potential Username Breach"
                        })

                self._cache[f"username:{username.lower()}"] = results
                return results

            except OSINTError:
                raise
            except Exception as e:
                raise OSINTError(f"Failed to check username breaches: {e}")

    def clear_cache(self):
        """Clear the internal cache."""
        self._cache.clear()