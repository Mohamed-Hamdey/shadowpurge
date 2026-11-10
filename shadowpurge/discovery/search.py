"""Search engine integration for large-scale digital footprint discovery."""

import asyncio
import httpx
import json
import re
import urllib.parse
from typing import List, Dict, Any, Optional, AsyncIterator
from dataclasses import dataclass, field

from shadowpurge.core.exceptions import DiscoveryError, NetworkError, RateLimitError
from shadowpurge.core.retry import retry
from shadowpurge.core.ratelimit import RateLimiter
from shadowpurge.core.config import get_settings
from shadowpurge.discovery.url_extractor import URLExtractor, ExtractedURL
from shadowpurge.discovery.platform_detector import PlatformDetector, PlatformInfo


@dataclass
class SearchResult:
    """A single search result with platform information."""
    url: ExtractedURL
    platform: Optional[PlatformInfo]
    title: str = ""
    snippet: str = ""
    source_engine: str = ""

    @property
    def is_known_platform(self) -> bool:
        return self.platform is not None

    @property
    def platform_name(self) -> Optional[str]:
        return self.platform.name if self.platform else None


@dataclass
class SearchConfig:
    """Configuration for a search engine."""
    name: str
    base_url: str
    query_param: str = "q"
    page_param: str = "p"
    user_agent: str = "ShadowPurge-Digital-Footprint-Scanner/1.0"
    rate_limit_rpm: int = 10
    max_pages: int = 3
    result_selector: str = ""  # CSS selector for results (for HTML parsing)
    title_selector: str = ""   # CSS selector for title
    snippet_selector: str = "" # CSS selector for snippet


# Predefined search engine configurations
SEARCH_ENGINES = {
    "duckduckgo": SearchConfig(
        name="DuckDuckGo",
        base_url="https://duckduckgo.com/html/",
        query_param="q",
        page_param="p",
        rate_limit_rpm=5,
        max_pages=3,
        result_selector=".result",
        title_selector=".result__title",
        snippet_selector=".result__snippet",
    ),
    "google": SearchConfig(
        name="Google",
        base_url="https://www.google.com/search",
        query_param="q",
        page_param="start",
        rate_limit_rpm=5,
        max_pages=3,
    ),
    "bing": SearchConfig(
        name="Bing",
        base_url="https://www.bing.com/search",
        query_param="q",
        page_param="first",
        rate_limit_rpm=10,
        max_pages=3,
    ),
    "serpapi": SearchConfig(
        name="SerpAPI",
        base_url="https://serpapi.com/search.json",
        query_param="q",
        page_param="start",
        rate_limit_rpm=100,
        max_pages=10,
    ),
    "google_cse": SearchConfig(
        name="Google CSE",
        base_url="https://www.googleapis.com/customsearch/v1",
        query_param="q",
        page_param="start",
        rate_limit_rpm=100,
        max_pages=10,
    ),
    "bing_api": SearchConfig(
        name="Bing API",
        base_url="https://api.bing.microsoft.com/v7.0/search",
        query_param="q",
        page_param="offset",
        rate_limit_rpm=100,
        max_pages=10,
    ),
}


class SearchEngine:
    """Base search engine class with rate limiting and retry logic."""

    def __init__(self, config: SearchConfig, api_key: Optional[str] = None):
        self.config = config
        self.api_key = api_key
        self.rate_limiter = RateLimiter(requests_per_minute=config.rate_limit_rpm)
        self.url_extractor = URLExtractor()
        self.platform_detector = PlatformDetector()

    @retry(max_retries=3, delay=1.0, backoff=2.0)
    async def _fetch_page(self, client: httpx.AsyncClient, url: str) -> str:
        """Fetch a search results page with rate limiting and retries."""
        await self.rate_limiter.acquire(self.config.name)

        headers = {"User-Agent": self.config.user_agent}
        response = await client.get(url, headers=headers, timeout=30.0, follow_redirects=True)

        if response.status_code == 429:
            raise RateLimitError(f"Rate limited by {self.config.name}")
        elif response.status_code == 202:
            # 202 "Accepted" - often indicates a CAPTCHA challenge page
            # Check if it's a challenge page by looking for CAPTCHA indicators
            content = response.text
            if "captcha" in content.lower() or "challenge" in content.lower() or "anomaly" in content.lower():
                # Return empty content instead of raising error - let parser handle empty results
                return ""
            return response.text
        elif response.status_code != 200:
            raise NetworkError(f"{self.config.name} returned {response.status_code}")

        return response.text

    def _build_search_url(self, query: str, page: int = 1) -> str:
        """Build the search URL for a query and page."""
        params = {self.config.query_param: query}
        if page > 1:
            params[self.config.page_param] = str((page - 1) * 10)
        return f"{self.config.base_url}?{urllib.parse.urlencode(params)}"

    def _parse_results(self, html: str, query: str) -> List[SearchResult]:
        """Parse search results from HTML. Override in subclasses."""
        return []

    async def search(self, query: str, max_pages: Optional[int] = None) -> AsyncIterator[SearchResult]:
        """Search for a query and yield results."""
        max_pages = max_pages or self.config.max_pages

        async with httpx.AsyncClient() as client:
            for page in range(1, max_pages + 1):
                url = self._build_search_url(query, page)
                try:
                    html = await self._fetch_page(client, url)
                    results = self._parse_results(html, query)

                    for result in results:
                        yield result

                    # Stop if we got fewer than 10 results (likely last page)
                    if len(results) < 10:
                        break

                except (RateLimitError, NetworkError) as e:
                    raise DiscoveryError(f"Search failed: {e}")


class DuckDuckGoEngine(SearchEngine):
    """DuckDuckGo search engine (HTML-based, no API key needed)."""

    def __init__(self, api_key: Optional[str] = None):
        config = SEARCH_ENGINES["duckduckgo"]
        super().__init__(config, api_key)
        # Use a more realistic browser user agent
        self.config.user_agent = (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )


class SerpAPIEngine(SearchEngine):
    """SerpAPI search engine (JSON API, requires API key)."""

    def __init__(self, api_key: Optional[str] = None):
        config = SEARCH_ENGINES["serpapi"]
        # Get API key from settings if not provided
        settings = get_settings()
        api_key = api_key or settings.search.serpapi.api_key
        super().__init__(config, api_key)

    def _build_search_url(self, query: str, page: int = 1) -> str:
        """Build the SerpAPI search URL."""
        params = {
            "q": query,
            "api_key": self.api_key,
            "engine": "google",
        }
        if page > 1:
            params["start"] = str((page - 1) * 10)
        return f"{self.config.base_url}?{urllib.parse.urlencode(params)}"

    def _parse_results(self, html: str, query: str) -> List[SearchResult]:
        """Parse SerpAPI JSON results."""
        import json
        from bs4 import BeautifulSoup

        try:
            data = json.loads(html)
        except json.JSONDecodeError:
            return []

        results = []
        organic_results = data.get("organic_results", [])

        for result_data in organic_results:
            try:
                url_str = result_data.get("link", "")
                if not url_str or not url_str.startswith("http"):
                    continue

                title = result_data.get("title", "")
                snippet = result_data.get("snippet", "")

                extracted = ExtractedURL(url=url_str)
                platform = self.platform_detector.detect(extracted)

                if platform:
                    results.append(SearchResult(
                        url=extracted,
                        platform=platform,
                        title=result_data.get("title", ""),
                        snippet=result_data.get("snippet", ""),
                        source_engine="SerpAPI"
                    ))
            except Exception:
                continue

        return results


class GoogleCSEEngine(SearchEngine):
    """Google Custom Search Engine (JSON API, requires API key + CX)."""

    def __init__(self, api_key: Optional[str] = None):
        config = SEARCH_ENGINES["google_cse"]
        settings = get_settings()
        api_key = api_key or settings.search.google_cse.api_key
        super().__init__(config, api_key)
        self.cx = settings.search.google_cse.cx

    def _build_search_url(self, query: str, page: int = 1) -> str:
        """Build the Google CSE search URL."""
        params = {
            "q": query,
            "key": self.api_key,
            "cx": self.cx,
        }
        if page > 1:
            params["start"] = str((page - 1) * 10 + 1)
        return f"{self.config.base_url}?{urllib.parse.urlencode(params)}"

    def _parse_results(self, html: str, query: str) -> List[SearchResult]:
        """Parse Google CSE JSON results."""
        import json

        try:
            data = json.loads(html)
        except json.JSONDecodeError:
            return []

        results = []
        items = data.get("items", [])

        for item in items:
            try:
                url_str = item.get("link", "")
                if not url_str or not url_str.startswith("http"):
                    continue

                extracted = ExtractedURL(url=url_str)
                platform = self.platform_detector.detect(extracted)

                if platform:
                    results.append(SearchResult(
                        url=extracted,
                        platform=platform,
                        title=item.get("title", ""),
                        snippet=item.get("snippet", ""),
                        source_engine="Google CSE"
                    ))
            except Exception:
                continue

        return results


class BingAPIEngine(SearchEngine):
    """Bing Web Search API (JSON API, requires API key)."""

    def __init__(self, api_key: Optional[str] = None):
        config = SEARCH_ENGINES["bing_api"]
        settings = get_settings()
        api_key = api_key or settings.search.bing.api_key
        super().__init__(config, api_key)

    def _build_search_url(self, query: str, page: int = 1) -> str:
        """Build the Bing API search URL."""
        params = {
            "q": query,
            "count": 10,
        }
        if page > 1:
            params["offset"] = str((page - 1) * 10)
        return f"{self.config.base_url}?{urllib.parse.urlencode(params)}"

    async def _fetch_page(self, client: httpx.AsyncClient, url: str) -> str:
        """Fetch a search results page with API key authentication."""
        await self.rate_limiter.acquire(self.config.name)

        headers = {
            "User-Agent": self.config.user_agent,
            "Ocp-Apim-Subscription-Key": self.api_key,
        }
        response = await client.get(url, headers=headers, timeout=30.0, follow_redirects=True)

        if response.status_code == 429:
            raise RateLimitError(f"Rate limited by {self.config.name}")
        elif response.status_code == 202:
            content = response.text
            if "captcha" in content.lower() or "challenge" in content.lower():
                return ""
            return response.text
        elif response.status_code != 200:
            raise NetworkError(f"{self.config.name} returned {response.status_code}")

        return response.text

    def _parse_results(self, html: str, query: str) -> List[SearchResult]:
        """Parse Bing API JSON results."""
        import json

        try:
            data = json.loads(html)
        except json.JSONDecodeError:
            return []

        results = []
        web_pages = data.get("webPages", {})
        items = web_pages.get("value", [])

        for item in items:
            try:
                url_str = item.get("url", "")
                if not url_str or not url_str.startswith("http"):
                    continue

                extracted = ExtractedURL(url=url_str)
                platform = self.platform_detector.detect(extracted)

                if platform:
                    results.append(SearchResult(
                        url=extracted,
                        platform=platform,
                        title=item.get("name", ""),
                        snippet=item.get("snippet", ""),
                        source_engine="Bing API"
                    ))
            except Exception:
                continue

        return results

    def _parse_results(self, html: str, query: str) -> List[SearchResult]:
        """Parse DuckDuckGo HTML results."""
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, "html.parser")
        results = []

        # Try primary selector
        for result_elem in soup.select(self.config.result_selector):
            try:
                # Extract link
                link_elem = result_elem.select_one("a.result__snippet, a.result__url, a")
                if not link_elem or not link_elem.get("href"):
                    continue

                url_str = link_elem["href"]
                # Clean DuckDuckGo redirect URLs
                if url_str.startswith("//duckduckgo.com/l/?"):
                    # Extract actual URL from redirect
                    parsed = urllib.parse.urlparse("https:" + url_str)
                    params = urllib.parse.parse_qs(parsed.query)
                    if "uddg" in params:
                        url_str = params["uddg"][0]

                # Extract title
                title_elem = result_elem.select_one(self.config.title_selector)
                title = title_elem.get_text(strip=True) if title_elem else ""

                # Extract snippet
                snippet_elem = result_elem.select_one(self.config.snippet_selector)
                snippet = snippet_elem.get_text(strip=True) if snippet_elem else ""

                # Extract and normalize URL
                extracted = ExtractedURL(url=url_str)
                platform = self.platform_detector.detect(extracted)

                results.append(SearchResult(
                    url=extracted,
                    platform=platform,
                    title=title,
                    snippet=snippet,
                    source_engine="DuckDuckGo"
                ))

            except Exception:
                continue

        # Fallback: if no results found with primary selector, try extracting all links
        if not results:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html, "html.parser")
            for link in soup.find_all("a", href=True):
                url_str = link.get("href")
                if not url_str or not url_str.startswith("http"):
                    continue

                # Skip DuckDuckGo internal links
                if "duckduckgo.com" in url_str:
                    continue

                title = link.get_text(strip=True)
                snippet = ""

                extracted = ExtractedURL(url=url_str)
                platform = self.platform_detector.detect(extracted)

                if platform:
                    results.append(SearchResult(
                        url=extracted,
                        platform=platform,
                        title=title,
                        snippet=snippet,
                        source_engine="DuckDuckGo"
                    ))

        return results


class SearchEngineManager:
    """Manages multiple search engines for comprehensive discovery."""

    def __init__(self, engines: Optional[Dict[str, SearchEngine]] = None):
        self.engines = engines or {}
        self.url_extractor = URLExtractor()
        self.platform_detector = PlatformDetector()

    def add_engine(self, name: str, engine: SearchEngine):
        """Add a search engine."""
        self.engines[name] = engine

    def remove_engine(self, name: str):
        """Remove a search engine."""
        self.engines.pop(name, None)

    def get_engine(self, name: str) -> Optional[SearchEngine]:
        """Get a search engine by name."""
        return self.engines.get(name)

    def list_engines(self) -> List[str]:
        """List available search engines."""
        return list(self.engines.keys())

    async def search_all(
        self,
        query: str,
        engines: Optional[List[str]] = None,
        max_pages_per_engine: int = 3,
        max_results: int = 100
    ) -> List[SearchResult]:
        """Search across multiple engines and aggregate results."""
        engines_to_use = engines or list(self.engines.keys())
        all_results: List[SearchResult] = []

        for engine_name in engines_to_use:
            engine = self.engines.get(engine_name)
            if not engine:
                continue

            try:
                page_count = 0
                async for result in engine.search(query, max_pages=max_pages_per_engine):
                    all_results.append(result)
                    if len(all_results) >= max_results:
                        break
                    page_count += 1
            except DiscoveryError:
                # Log and continue with other engines
                continue

        # Deduplicate by URL
        seen_urls = set()
        unique_results = []
        for result in all_results:
            if result.url.url not in seen_urls:
                seen_urls.add(result.url.url)
                unique_results.append(result)

        return unique_results[:max_results]

    async def discover_profiles(
        self,
        target: str,
        target_type: str = "username",
        engines: Optional[List[str]] = None,
        max_pages_per_engine: int = 3,
        max_results: int = 100
    ) -> Dict[str, Any]:
        """
        Discover profiles for a target across search engines.

        Args:
            target: Username, email, or phone to search for
            target_type: Type of target ("username", "email", "phone")
            engines: List of engine names to use (default: all)
            max_pages_per_engine: Max pages per search engine
            max_results: Max total results

        Returns:
            Dictionary with discovered platforms and search results
        """
        # Build search queries based on target type
        queries = self._build_queries(target, target_type)

        all_results = []
        for query in queries:
            results = await self.search_all(
                query,
                engines=engines,
                max_pages_per_engine=max_pages_per_engine,
                max_results=max_results // len(queries) if queries else max_results
            )
            all_results.extend(results)

        # Deduplicate and aggregate by platform
        platform_results: Dict[str, List[SearchResult]] = {}
        for result in all_results:
            if result.platform:
                key = result.platform.domain
                if key not in platform_results:
                    platform_results[key] = []
                platform_results[key].append(result)

        # Build summary
        discovered_platforms = []
        for domain, results in platform_results.items():
            platform_info = results[0].platform
            urls = [r.url.url for r in results]
            discovered_platforms.append({
                "platform": platform_info.name if platform_info else "Unknown",
                "domain": domain,
                "category": platform_info.category if platform_info else "Unknown",
                "confidence": platform_info.confidence if platform_info else 0.5,
                "profile_urls": urls,
                "deletion_url": platform_info.deletion_url if platform_info else None,
                "removal_instructions": platform_info.removal_instructions if platform_info else None,
                "automation_supported": platform_info.automation_supported if platform_info else False,
                "search_snippets": [r.snippet for r in results[:3]],
            })

        return {
            "target": target,
            "target_type": target_type,
            "queries_used": queries,
            "engines_used": engines or list(self.engines.keys()),
            "total_results": len(all_results),
            "discovered_platforms": discovered_platforms,
        }

    def _build_queries(self, target: str, target_type: str) -> List[str]:
        """Build search queries for a target."""
        queries = []

        if target_type == "username":
            # Exact username search
            queries.append(f'"{target}"')
            # Site-specific searches
            queries.append(f'{target} site:github.com OR site:twitter.com OR site:linkedin.com OR site:reddit.com')
            queries.append(f'{target} profile OR account OR bio')
        elif target_type == "email":
            # Email search
            queries.append(f'"{target}"')
            queries.append(f'{target} site:github.com OR site:linkedin.com OR site:twitter.com')
            queries.append(f'{target} contact OR profile')
        elif target_type == "phone":
            # Phone search (various formats)
            queries.append(f'"{target}"')
            cleaned = re.sub(r'[\s\-\(\)\+]', '', target)
            queries.append(f'"{cleaned}"')
            queries.append(f'{target} site:facebook.com OR site:linkedin.com OR site:twitter.com')
        else:
            queries.append(f'"{target}"')

        return queries


# Default engine manager with DuckDuckGo
def create_default_search_manager() -> SearchEngineManager:
    """Create a search engine manager with all available engines based on config."""
    from shadowpurge.core.config import get_settings
    settings = get_settings()

    manager = SearchEngineManager()

    # Always add DuckDuckGo (no API key required)
    manager.add_engine("duckduckgo", DuckDuckGoEngine())

    # Add SerpAPI if API key is configured
    if settings.search.serpapi.api_key:
        manager.add_engine("serpapi", SerpAPIEngine())

    # Add Google CSE if API key and CX are configured
    if settings.search.google_cse.api_key and settings.search.google_cse.cx:
        manager.add_engine("google_cse", GoogleCSEEngine())

    # Add Bing API if API key is configured
    if settings.search.bing.api_key:
        manager.add_engine("bing_api", BingAPIEngine())

    return manager