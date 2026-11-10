"""URL extraction and normalization utilities for search results."""

import re
import urllib.parse
from typing import List, Optional
from dataclasses import dataclass


@dataclass
class ExtractedURL:
    """A normalized URL extracted from search results."""

    url: str
    domain: str = ""
    path: str = ""
    platform_hint: Optional[str] = None

    def __post_init__(self):
        # First, parse the original URL to get domain and path
        parsed = urllib.parse.urlparse(self.url)
        # Remove www. from domain
        netloc = parsed.netloc.lower()
        if netloc.startswith("www."):
            netloc = netloc[4:]
        self.domain = netloc
        self.path = parsed.path.rstrip("/")

        # Then normalize the URL for display
        self.url = self._normalize(self.url)

    @staticmethod
    def _normalize(url: str) -> str:
        """Normalize a URL: remove protocol, lowercase domain, strip tracking params."""
        url = url.strip()

        # Parse the URL first to extract components
        parsed = urllib.parse.urlparse(url)
        netloc = parsed.netloc.lower()
        path = parsed.path.rstrip("/")
        query_params = urllib.parse.parse_qs(parsed.query)

        # Remove www.
        if netloc.startswith("www."):
            netloc = netloc[4:]

        # Keep only non-tracking params
        tracking_params = {
            "utm_source",
            "utm_medium",
            "utm_campaign",
            "utm_term",
            "utm_content",
            "fbclid",
            "gclid",
            "msclkid",
            "mc_cid",
            "mc_eid",
            "ref",
            "source",
            "src",
            "cmpid",
            "cmp",
            "igshid",
            "spm",
            "vnv",
            "v=1",
            "ved",
            "ei",
            "client",
            "oeis",
        }
        filtered_params = {
            k: v for k, v in query_params.items() if k.lower() not in tracking_params
        }

        new_query = urllib.parse.urlencode(filtered_params, doseq=True)
        clean_url = path
        if new_query:
            clean_url += "?" + new_query

        return (netloc + clean_url).lower()

    @property
    def root_domain(self) -> str:
        """Get the root domain (e.g., 'github.com' from 'www.github.com')."""
        parts = self.domain.split(".")
        if len(parts) >= 2:
            return ".".join(parts[-2:])
        return self.domain


class URLExtractor:
    """Extracts and normalizes URLs from HTML search results."""

    # Common URL patterns in search results
    URL_PATTERNS = [
        # Standard URLs
        r'https?://[^\s<>"\']+',
        # URLs in href attributes
        r'href=["\']([^"\']+)["\']',
        # URLs in text content
        r'(?:^|\s)(https?://[^\s<>"\']+)',
    ]

    # Known platform domains for hinting
    PLATFORM_HINTS = {
        "github.com": "GitHub",
        "twitter.com": "Twitter/X",
        "x.com": "Twitter/X",
        "reddit.com": "Reddit",
        "instagram.com": "Instagram",
        "linkedin.com": "LinkedIn",
        "facebook.com": "Facebook",
        "twitch.tv": "Twitch",
        "spotify.com": "Spotify",
        "steamcommunity.com": "Steam",
        "pinterest.com": "Pinterest",
        "tiktok.com": "TikTok",
        "discord.com": "Discord",
        "youtube.com": "YouTube",
        "vimeo.com": "Vimeo",
        "medium.com": "Medium",
        "substack.com": "Substack",
        "dev.to": "Dev.to",
        "gitlab.com": "GitLab",
        "bitbucket.org": "Bitbucket",
        "npmjs.com": "npm",
        "pypi.org": "PyPI",
        "dribbble.com": "Dribbble",
        "behance.net": "Behance",
        "flickr.com": "Flickr",
        "tumblr.com": "Tumblr",
        "snapchat.com": "Snapchat",
        "telegram.org": "Telegram",
        "whatsapp.com": "WhatsApp",
        "quora.com": "Quora",
        "dailymotion.com": "DailyMotion",
        "soundcloud.com": "SoundCloud",
        "bandcamp.com": "BandCamp",
        "patreon.com": "Patreon",
        "kofi.com": "Ko-fi",
        "linktr.ee": "Linktree",
        "onlyfans.com": "OnlyFans",
        "about.me": "About.me",
        "gravatar.com": "Gravatar",
        "wordpress.com": "WordPress",
        "blogspot.com": "Blogger",
        "wix.com": "Wix",
        "squarespace.com": "Squarespace",
        " Carrd.co": "Carrd",
    }

    def __init__(self):
        self._seen_urls = set()

    def extract(self, html_content: str, max_urls: int = 50) -> List[ExtractedURL]:
        """Extract and normalize URLs from HTML content."""
        urls = []

        # Extract URLs using regex
        for pattern in self.URL_PATTERNS:
            matches = re.findall(pattern, html_content, re.IGNORECASE)
            for match in matches:
                # Handle tuple matches (from capture groups)
                if isinstance(match, tuple):
                    match = match[0] if match else ""
                if match and match.startswith("http"):
                    urls.append(match)

        # Deduplicate and normalize
        normalized = []
        for url in urls:
            try:
                extracted = ExtractedURL(url=url)
                if extracted.url not in self._seen_urls:
                    self._seen_urls.add(extracted.url)
                    # Add platform hint
                    extracted.platform_hint = self.PLATFORM_HINTS.get(
                        extracted.root_domain
                    )
                    normalized.append(extracted)
            except Exception:
                continue

            if len(normalized) >= max_urls:
                break

        return normalized

    def extract_from_text(self, text: str, max_urls: int = 50) -> List[ExtractedURL]:
        """Extract URLs from plain text (e.g., JSON API responses)."""
        return self.extract(text, max_urls=max_urls)

    def reset(self):
        """Reset the deduplication cache."""
        self._seen_urls.clear()

    def is_social_platform(self, url: ExtractedURL) -> bool:
        """Check if a URL belongs to a known social/platform domain."""
        return url.platform_hint is not None

    def get_platform_name(self, url: ExtractedURL) -> Optional[str]:
        """Get the platform name from a URL, if known."""
        return url.platform_hint or self.PLATFORM_HINTS.get(url.root_domain)
