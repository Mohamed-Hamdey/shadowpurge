"""Platform detection from URLs for dynamic platform discovery."""

import re
from typing import Optional, Dict, List
from dataclasses import dataclass, field
from .url_extractor import ExtractedURL


@dataclass
class PlatformInfo:
    """Information about a detected platform."""

    name: str
    domain: str
    category: str
    url_pattern: str  # Regex pattern to match profile URLs
    deletion_url: Optional[str] = None
    removal_instructions: Optional[str] = None
    automation_supported: bool = False
    confidence: float = 0.0  # 0.0 to 1.0
    examples: List[str] = field(default_factory=list)


class PlatformDetector:
    """Detects platforms from extracted URLs using pattern matching."""

    # Known platform configurations
    KNOWN_PLATFORMS = {
        "github.com": PlatformInfo(
            name="GitHub",
            domain="github.com",
            category="Developer",
            url_pattern=r"github\.com/([a-zA-Z0-9_-]+)/?$",
            deletion_url="https://github.com/settings/admin",
            removal_instructions="Go to Settings > Account > Delete Account",
            automation_supported=True,
            confidence=0.95,
            examples=["github.com/username", "github.com/user-name"],
        ),
        "twitter.com": PlatformInfo(
            name="Twitter/X",
            domain="twitter.com",
            category="Social",
            url_pattern=r"(?:twitter|x)\.com/([a-zA-Z0-9_]+)/?$",
            deletion_url="https://twitter.com/settings/deactivate",
            removal_instructions="Go to Settings > Your account > Deactivate your account",
            automation_supported=True,
            confidence=0.95,
            examples=["twitter.com/username", "x.com/username"],
        ),
        "x.com": PlatformInfo(
            name="Twitter/X",
            domain="x.com",
            category="Social",
            url_pattern=r"x\.com/([a-zA-Z0-9_]+)/?$",
            deletion_url="https://twitter.com/settings/deactivate",
            removal_instructions="Go to Settings > Your account > Deactivate your account",
            automation_supported=True,
            confidence=0.95,
            examples=["x.com/username"],
        ),
        "reddit.com": PlatformInfo(
            name="Reddit",
            domain="reddit.com",
            category="Social",
            url_pattern=r"reddit\.com/(?:user|u)/([a-zA-Z0-9_-]+)/?$",
            deletion_url="https://www.reddit.com/settings/account",
            removal_instructions="Go to User Settings > Account > Deactivate Account",
            automation_supported=True,
            confidence=0.95,
            examples=["reddit.com/user/username", "reddit.com/u/username"],
        ),
        "instagram.com": PlatformInfo(
            name="Instagram",
            domain="instagram.com",
            category="Social",
            url_pattern=r"instagram\.com/([a-zA-Z0-9_.]+)/?$",
            deletion_url="https://www.instagram.com/accounts/remove/request/permanent/",
            removal_instructions="Log in and follow the permanent deletion request form",
            automation_supported=True,
            confidence=0.9,
            examples=["instagram.com/username"],
        ),
        "linkedin.com": PlatformInfo(
            name="LinkedIn",
            domain="linkedin.com",
            category="Social",
            url_pattern=r"linkedin\.com/in/([a-zA-Z0-9_-]+)/?$",
            deletion_url="https://www.linkedin.com/psettings/member-delete-profile",
            removal_instructions="Go to Privacy settings > Delete your LinkedIn account",
            automation_supported=False,
            confidence=0.95,
            examples=["linkedin.com/in/username"],
        ),
        "facebook.com": PlatformInfo(
            name="Facebook",
            domain="facebook.com",
            category="Social",
            url_pattern=r"facebook\.com/([a-zA-Z0-9_.]+)/?$",
            deletion_url="https://www.facebook.com/settings",
            removal_instructions="Go to Settings > Account Settings > Deactivate/Close your account",
            automation_supported=False,
            confidence=0.9,
            examples=["facebook.com/username"],
        ),
        "twitch.tv": PlatformInfo(
            name="Twitch",
            domain="twitch.tv",
            category="Social",
            url_pattern=r"twitch\.tv/([a-zA-Z0-9_]+)/?$",
            deletion_url="https://www.twitch.tv/settings/delete",
            removal_instructions="Go to Settings > Advanced > Delete Account",
            automation_supported=True,
            confidence=0.95,
            examples=["twitch.tv/username"],
        ),
        "spotify.com": PlatformInfo(
            name="Spotify",
            domain="spotify.com",
            category="Entertainment",
            url_pattern=r"(?:open\.)?spotify\.com/user/([a-zA-Z0-9_]+)/?$",
            deletion_url="https://www.spotify.com/account/settings",
            removal_instructions="Go to Account Settings > Delete Account",
            automation_supported=True,
            confidence=0.9,
            examples=["open.spotify.com/user/username", "spotify.com/user/username"],
        ),
        "steamcommunity.com": PlatformInfo(
            name="Steam",
            domain="steamcommunity.com",
            category="Gaming",
            url_pattern=r"steamcommunity\.com/(?:id|profiles)/([a-zA-Z0-9_-]+)/?$",
            deletion_url="https://steamcommunity.com/profile/delete",
            removal_instructions="Go to Profile settings > Delete Account",
            automation_supported=False,
            confidence=0.95,
            examples=[
                "steamcommunity.com/id/username",
                "steamcommunity.com/profiles/123456789",
            ],
        ),
        "pinterest.com": PlatformInfo(
            name="Pinterest",
            domain="pinterest.com",
            category="Social",
            url_pattern=r"pinterest\.com/([a-zA-Z0-9_]+)/?$",
            deletion_url="https://www.pinterest.com/settings/",
            removal_instructions="Go to Settings > Account Basics > Close Account",
            automation_supported=False,
            confidence=0.9,
            examples=["pinterest.com/username"],
        ),
        "tiktok.com": PlatformInfo(
            name="TikTok",
            domain="tiktok.com",
            category="Social",
            url_pattern=r"tiktok\.com/@([a-zA-Z0-9_.]+)/?$",
            deletion_url="https://www.tiktok.com/settings/account",
            removal_instructions="Go to Settings > Manage Account > Delete Account",
            automation_supported=False,
            confidence=0.9,
            examples=["tiktok.com/@username"],
        ),
        "discord.com": PlatformInfo(
            name="Discord",
            domain="discord.com",
            category="Social",
            url_pattern=r"discord\.com/users/(\d+)/?$",
            deletion_url="https://discord.com/settings",
            removal_instructions="Go to User Settings > My Account > Delete Account",
            automation_supported=False,
            confidence=0.85,
            examples=["discord.com/users/123456789"],
        ),
        "youtube.com": PlatformInfo(
            name="YouTube",
            domain="youtube.com",
            category="Entertainment",
            url_pattern=r"youtube\.com/(?:@|channel/|user/|c/)([a-zA-Z0-9_-]+)/?$",
            deletion_url="https://myaccount.google.com/delete_services",
            removal_instructions="Go to Google Account > Data & Privacy > Delete a Google Service",
            automation_supported=False,
            confidence=0.9,
            examples=[
                "youtube.com/@username",
                "youtube.com/channel/UC...",
                "youtube.com/user/username",
            ],
        ),
        "medium.com": PlatformInfo(
            name="Medium",
            domain="medium.com",
            category="Social",
            url_pattern=r"medium\.com/@([a-zA-Z0-9_-]+)/?$",
            deletion_url="https://medium.com/me/settings",
            removal_instructions="Go to Settings > Account > Delete Account",
            automation_supported=False,
            confidence=0.9,
            examples=["medium.com/@username"],
        ),
        "gitlab.com": PlatformInfo(
            name="GitLab",
            domain="gitlab.com",
            category="Developer",
            url_pattern=r"gitlab\.com/([a-zA-Z0-9_-]+)/?$",
            deletion_url="https://gitlab.com/profile",
            removal_instructions="Go to Profile > Account > Delete Account",
            automation_supported=True,
            confidence=0.95,
            examples=["gitlab.com/username"],
        ),
        "bitbucket.org": PlatformInfo(
            name="Bitbucket",
            domain="bitbucket.org",
            category="Developer",
            url_pattern=r"bitbucket\.org/([a-zA-Z0-9_-]+)/?$",
            deletion_url="https://bitbucket.org/account/settings/",
            removal_instructions="Go to Settings > Delete Account",
            automation_supported=False,
            confidence=0.9,
            examples=["bitbucket.org/username"],
        ),
        "pypi.org": PlatformInfo(
            name="PyPI",
            domain="pypi.org",
            category="Developer",
            url_pattern=r"pypi\.org/user/([a-zA-Z0-9_-]+)/?$",
            deletion_url="https://pypi.org/manage/account/",
            removal_instructions="Go to Account Settings > Delete Account",
            automation_supported=False,
            confidence=0.9,
            examples=["pypi.org/user/username"],
        ),
        "npmjs.com": PlatformInfo(
            name="npm",
            domain="npmjs.com",
            category="Developer",
            url_pattern=r"npmjs\.com/~([a-zA-Z0-9_-]+)/?$",
            deletion_url="https://www.npmjs.com/settings/profile",
            removal_instructions="Go to Profile Settings > Delete Account",
            automation_supported=False,
            confidence=0.9,
            examples=["npmjs.com/~username"],
        ),
        "dev.to": PlatformInfo(
            name="Dev.to",
            domain="dev.to",
            category="Developer",
            url_pattern=r"dev\.to/([a-zA-Z0-9_-]+)/?$",
            deletion_url="https://dev.to/settings/account",
            removal_instructions="Go to Settings > Account > Delete Account",
            automation_supported=False,
            confidence=0.9,
            examples=["dev.to/username"],
        ),
        "dribbble.com": PlatformInfo(
            name="Dribbble",
            domain="dribbble.com",
            category="Social",
            url_pattern=r"dribbble\.com/([a-zA-Z0-9_-]+)/?$",
            deletion_url="https://dribbble.com/settings/account",
            removal_instructions="Go to Settings > Account > Delete Account",
            automation_supported=False,
            confidence=0.9,
            examples=["dribbble.com/username"],
        ),
        "behance.net": PlatformInfo(
            name="Behance",
            domain="behance.net",
            category="Social",
            url_pattern=r"behance\.net/([a-zA-Z0-9_-]+)/?$",
            deletion_url="https://www.behance.net/settings/account",
            removal_instructions="Go to Settings > Account > Delete Account",
            automation_supported=False,
            confidence=0.9,
            examples=["behance.net/username"],
        ),
        "flickr.com": PlatformInfo(
            name="Flickr",
            domain="flickr.com",
            category="Entertainment",
            url_pattern=r"flickr\.com/people/([a-zA-Z0-9_@]+)/?$",
            deletion_url="https://www.flickr.com/account/delete",
            removal_instructions="Go to Account Settings > Delete Your Account",
            automation_supported=False,
            confidence=0.9,
            examples=["flickr.com/people/username"],
        ),
        "tumblr.com": PlatformInfo(
            name="Tumblr",
            domain="tumblr.com",
            category="Social",
            url_pattern=r"([a-zA-Z0-9_-]+)\.tumblr\.com/?$",
            deletion_url="https://www.tumblr.com/settings/account",
            removal_instructions="Go to Settings > Account > Delete Account",
            automation_supported=False,
            confidence=0.9,
            examples=["username.tumblr.com"],
        ),
        "vimeo.com": PlatformInfo(
            name="Vimeo",
            domain="vimeo.com",
            category="Entertainment",
            url_pattern=r"vimeo\.com/([a-zA-Z0-9_-]+)/?$",
            deletion_url="https://vimeo.com/settings/account",
            removal_instructions="Go to Settings > Account > Delete Account",
            automation_supported=False,
            confidence=0.9,
            examples=["vimeo.com/username"],
        ),
        "soundcloud.com": PlatformInfo(
            name="SoundCloud",
            domain="soundcloud.com",
            category="Entertainment",
            url_pattern=r"soundcloud\.com/([a-zA-Z0-9_-]+)/?$",
            deletion_url="https://soundcloud.com/settings/account",
            removal_instructions="Go to Settings > Account > Delete Account",
            automation_supported=False,
            confidence=0.9,
            examples=["soundcloud.com/username"],
        ),
        "bandcamp.com": PlatformInfo(
            name="BandCamp",
            domain="bandcamp.com",
            category="Entertainment",
            url_pattern=r"([a-zA-Z0-9_-]+)\.bandcamp\.com/?$",
            deletion_url="https://bandcamp.com/settings",
            removal_instructions="Go to Settings > Account > Delete Account",
            automation_supported=False,
            confidence=0.9,
            examples=["username.bandcamp.com"],
        ),
        "patreon.com": PlatformInfo(
            name="Patreon",
            domain="patreon.com",
            category="Social",
            url_pattern=r"patreon\.com/([a-zA-Z0-9_-]+)/?$",
            deletion_url="https://www.patreon.com/settings/account",
            removal_instructions="Go to Settings > Account > Delete Account",
            automation_supported=False,
            confidence=0.9,
            examples=["patreon.com/username"],
        ),
        "kofi.com": PlatformInfo(
            name="Ko-fi",
            domain="kofi.com",
            category="Social",
            url_pattern=r"ko-fi\.com/([a-zA-Z0-9_-]+)/?$",
            deletion_url="https://ko-fi.com/settings",
            removal_instructions="Go to Settings > Delete Account",
            automation_supported=False,
            confidence=0.9,
            examples=["kofi.com/username"],
        ),
        "onlyfans.com": PlatformInfo(
            name="OnlyFans",
            domain="onlyfans.com",
            category="Social",
            url_pattern=r"onlyfans\.com/([a-zA-Z0-9_-]+)/?$",
            deletion_url="https://onlyfans.com/settings",
            removal_instructions="Go to Settings > Delete Account",
            automation_supported=False,
            confidence=0.9,
            examples=["onlyfans.com/username"],
        ),
        "about.me": PlatformInfo(
            name="About.me",
            domain="about.me",
            category="Social",
            url_pattern=r"about\.me/([a-zA-Z0-9_-]+)/?$",
            deletion_url="https://about.me/settings",
            removal_instructions="Go to Settings > Delete Account",
            automation_supported=False,
            confidence=0.9,
            examples=["about.me/username"],
        ),
        "gravatar.com": PlatformInfo(
            name="Gravatar",
            domain="gravatar.com",
            category="Social",
            url_pattern=r"gravatar\.com/([a-zA-Z0-9_-]+)/?$",
            deletion_url="https://en.gravatar.com/settings",
            removal_instructions="Go to Settings > Delete Account",
            automation_supported=False,
            confidence=0.85,
            examples=["gravatar.com/username"],
        ),
        "wordpress.com": PlatformInfo(
            name="WordPress",
            domain="wordpress.com",
            category="Social",
            url_pattern=r"wordpress\.com/([a-zA-Z0-9_-]+)/?$",
            deletion_url="https://wordpress.com/me/settings",
            removal_instructions="Go to Settings > Delete Account",
            automation_supported=False,
            confidence=0.9,
            examples=["wordpress.com/username"],
        ),
        "substack.com": PlatformInfo(
            name="Substack",
            domain="substack.com",
            category="Social",
            url_pattern=r"([a-zA-Z0-9_-]+)\.substack\.com/?$",
            deletion_url="https://substack.com/settings",
            removal_instructions="Go to Settings > Delete Account",
            automation_supported=False,
            confidence=0.9,
            examples=["username.substack.com"],
        ),
    }

    def __init__(self):
        self._compiled_patterns: Dict[str, re.Pattern] = {}
        self._compile_patterns()

    def _compile_patterns(self):
        """Pre-compile regex patterns for all known platforms."""
        for domain, info in self.KNOWN_PLATFORMS.items():
            try:
                self._compiled_patterns[domain] = re.compile(
                    info.url_pattern, re.IGNORECASE
                )
            except re.error:
                # Skip invalid patterns
                pass

    def detect(self, extracted_url: "ExtractedURL") -> Optional[PlatformInfo]:
        """Detect platform from an extracted URL."""
        domain = extracted_url.root_domain

        # Direct match from known platforms
        if domain in self.KNOWN_PLATFORMS:
            return self.KNOWN_PLATFORMS[domain]

        # Try subdomain matches (e.g., username.tumblr.com)
        for domain_key, info in self.KNOWN_PLATFORMS.items():
            if domain.endswith("." + domain_key) or domain == domain_key:
                # Update confidence based on match type
                info_copy = PlatformInfo(
                    name=info.name,
                    domain=info.domain,
                    category=info.category,
                    url_pattern=info.url_pattern,
                    deletion_url=info.deletion_url,
                    removal_instructions=info.removal_instructions,
                    automation_supported=info.automation_supported,
                    confidence=info.confidence * 0.9,  # Slightly lower for subdomain
                    examples=info.examples,
                )
                return info_copy

        return None

    def detect_from_url(self, url: str) -> Optional[PlatformInfo]:
        """Detect platform directly from a URL string."""
        from .url_extractor import ExtractedURL

        extracted = ExtractedURL(url=url)
        return self.detect(extracted)

    def detect_from_urls(self, urls: List["ExtractedURL"]) -> Dict[str, PlatformInfo]:
        """Detect platforms from a list of URLs, returning unique platforms."""
        detected = {}
        for url in urls:
            platform = self.detect(url)
            if platform:
                # Use domain as key, keep highest confidence
                key = platform.domain
                if (
                    key not in detected
                    or platform.confidence > detected[key].confidence
                ):
                    detected[key] = platform
        return detected

    def get_all_known_platforms(self) -> List[PlatformInfo]:
        """Get list of all known platforms."""
        return list(self.KNOWN_PLATFORMS.values())

    def add_platform(self, platform: PlatformInfo):
        """Add a new platform to the detector."""
        self.KNOWN_PLATFORMS[platform.domain] = platform
        try:
            self._compiled_patterns[platform.domain] = re.compile(
                platform.url_pattern, re.IGNORECASE
            )
        except re.error:
            pass

    def remove_platform(self, domain: str):
        """Remove a platform from the detector."""
        self.KNOWN_PLATFORMS.pop(domain, None)
        self._compiled_patterns.pop(domain, None)

    def update_confidence(self, domain: str, confidence: float):
        """Update confidence score for a platform."""
        if domain in self.KNOWN_PLATFORMS:
            self.KNOWN_PLATFORMS[domain].confidence = max(0.0, min(1.0, confidence))
