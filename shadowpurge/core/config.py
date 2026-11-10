"""Configuration management for ShadowPurge."""

import os
from pathlib import Path
from typing import Optional, List
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class SearchEngineConfig(BaseSettings):
    """Configuration for a search engine."""

    enabled: bool = True
    api_key: Optional[str] = None
    rate_limit_rpm: int = 10
    max_pages: int = 3


class SerpAPIConfig(SearchEngineConfig):
    """SerpAPI configuration."""

    api_key: Optional[str] = Field(default=None, validation_alias="SERPAPI_KEY")


class GoogleCSEConfig(SearchEngineConfig):
    """Google Custom Search Engine configuration."""

    api_key: Optional[str] = Field(default=None, validation_alias="GOOGLE_CSE_KEY")
    cx: Optional[str] = Field(default=None, validation_alias="GOOGLE_CSE_CX")


class BingConfig(SearchEngineConfig):
    """Bing Web Search API configuration."""

    api_key: Optional[str] = Field(default=None, validation_alias="BING_API_KEY")


class BraveConfig(SearchEngineConfig):
    """Brave Search API configuration."""

    api_key: Optional[str] = Field(default=None, validation_alias="BRAVE_API_KEY")


class MojeekConfig(SearchEngineConfig):
    """Mojeek Search API configuration."""

    api_key: Optional[str] = Field(default=None, validation_alias="MOJEEK_API_KEY")


class SearchConfig(BaseSettings):
    """Search configuration."""

    model_config = SettingsConfigDict(env_prefix="SHADOWPURGE_SEARCH_")

    engines: List[str] = Field(
        default=["duckduckgo"], description="Enabled search engines"
    )
    max_pages: int = Field(default=3, ge=1, le=10)
    max_results: int = Field(default=100, ge=1, le=1000)
    timeout: int = Field(default=30, ge=5, le=300)

    # Engine-specific configs
    serpapi: SerpAPIConfig = SerpAPIConfig()
    google_cse: GoogleCSEConfig = GoogleCSEConfig()
    bing: BingConfig = BingConfig()
    brave: BraveConfig = BraveConfig()
    mojeek: MojeekConfig = MojeekConfig()


class DeletionConfig(BaseSettings):
    """Deletion automation configuration."""

    model_config = SettingsConfigDict(env_prefix="SHADOWPURGE_DELETION_")

    browser: str = Field(
        default="chromium", description="Browser to use (chromium, firefox, webkit)"
    )
    headless: bool = Field(default=False, description="Run browser in headless mode")
    timeout: int = Field(
        default=60000, ge=5000, le=300000, description="Timeout in milliseconds"
    )
    slow_mo: int = Field(
        default=0, ge=0, le=1000, description="Slow down operations by ms"
    )
    user_data_dir: Optional[str] = Field(
        default=None, description="Browser user data directory for session persistence"
    )
    viewport_width: int = Field(default=1280, ge=800, le=3840)
    viewport_height: int = Field(default=720, ge=600, le=2160)


class OutputConfig(BaseSettings):
    """Output and export configuration."""

    model_config = SettingsConfigDict(env_prefix="SHADOWPURGE_OUTPUT_")

    format: str = Field(
        default="json", description="Default export format (json, csv, html, markdown)"
    )
    export_dir: str = Field(
        default="./exports", description="Directory for exported reports"
    )
    include_timestamps: bool = Field(
        default=True, description="Include timestamps in exports"
    )
    include_snippets: bool = Field(
        default=True, description="Include search snippets in exports"
    )


class ScanConfig(BaseSettings):
    """Scanning configuration."""

    model_config = SettingsConfigDict(env_prefix="SHADOWPURGE_SCAN_")

    max_concurrent: int = Field(
        default=10, ge=1, le=50, description="Max concurrent requests"
    )
    timeout: int = Field(
        default=30, ge=5, le=300, description="Request timeout in seconds"
    )
    user_agent: str = Field(
        default="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        description="Default user agent",
    )
    follow_redirects: bool = Field(default=True, description="Follow HTTP redirects")
    verify_ssl: bool = Field(default=True, description="Verify SSL certificates")


class LoggingConfig(BaseSettings):
    """Logging configuration."""

    model_config = SettingsConfigDict(env_prefix="SHADOWPURGE_LOG_")

    level: str = Field(
        default="INFO", description="Log level (DEBUG, INFO, WARNING, ERROR)"
    )
    format: str = Field(default="json", description="Log format (json, text)")
    file: Optional[str] = Field(default=None, description="Log file path (optional)")
    console: bool = Field(default=True, description="Log to console")


class Settings(BaseSettings):
    """Main settings class combining all configurations."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        extra="ignore",
    )

    # Application info
    app_name: str = "ShadowPurge"
    version: str = "0.1.0"
    debug: bool = Field(default=False, validation_alias="SHADOWPURGE_DEBUG")

    # Sub-configurations
    search: SearchConfig = SearchConfig()
    deletion: DeletionConfig = DeletionConfig()
    output: OutputConfig = OutputConfig()
    scan: ScanConfig = ScanConfig()
    logging: LoggingConfig = LoggingConfig()

    # Paths
    data_dir: str = Field(default="./data", description="Data directory")
    export_dir: str = Field(default="./exports", description="Export directory")
    cache_dir: str = Field(default="./cache", description="Cache directory")

    def get_platforms_file(self) -> str:
        """Get path to platforms.json."""
        return os.path.join(self.data_dir, "platforms.json")

    def get_cache_dir(self) -> Path:
        """Get cache directory as Path."""
        path = Path(self.cache_dir)
        path.mkdir(parents=True, exist_ok=True)
        return path

    def get_export_dir(self) -> Path:
        """Get export directory as Path."""
        path = Path(self.export_dir)
        path.mkdir(parents=True, exist_ok=True)
        return path


# Global settings instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get global settings instance (singleton)."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


def reload_settings() -> Settings:
    """Reload settings from environment/config."""
    global _settings
    _settings = Settings()
    return _settings
