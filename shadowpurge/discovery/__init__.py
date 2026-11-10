"""ShadowPurge Discovery Module

This module provides functionality for discovering digital footprints
across the internet using search engines and OSINT APIs.
"""

from .engine import DiscoveryEngine, PlatformRegistry
from .osint import OSINTScanner
from .search import (
    SearchEngine,
    DuckDuckGoEngine,
    SearchEngineManager,
    SearchConfig,
    SearchResult,
    create_default_search_manager,
)
from .url_extractor import URLExtractor, ExtractedURL
from .platform_detector import PlatformDetector, PlatformInfo

__all__ = [
    "DiscoveryEngine",
    "PlatformRegistry",
    "OSINTScanner",
    "SearchEngine",
    "DuckDuckGoEngine",
    "SearchEngineManager",
    "SearchConfig",
    "SearchResult",
    "create_default_search_manager",
    "URLExtractor",
    "ExtractedURL",
    "PlatformDetector",
    "PlatformInfo",
]
