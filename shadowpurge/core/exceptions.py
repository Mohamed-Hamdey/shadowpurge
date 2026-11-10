from typing import Optional


class ShadowPurgeError(Exception):
    """Base exception for all ShadowPurge errors."""

    def __init__(self, message: str, error_code: Optional[str] = None,
                 retryable: bool = False, original_exception: Optional[Exception] = None):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.retryable = retryable
        self.original_exception = original_exception

    def __str__(self) -> str:
        base_msg = super().__str__()
        if self.error_code:
            return f"[{self.error_code}] {base_msg}"
        return base_msg


class DiscoveryError(ShadowPurgeError):
    """Raised when platform discovery fails."""
    pass


class PlatformNotFoundError(DiscoveryError):
    """Raised when a platform cannot be found in the registry."""
    def __init__(self, platform_name: str):
        super().__init__(
            f"Platform '{platform_name}' not found in registry",
            error_code="PLATFORM_NOT_FOUND",
            retryable=False
        )


class NetworkError(ShadowPurgeError):
    """Raised when network requests fail."""
    def __init__(self, message: str, retryable: bool = True,
                 original_exception: Optional[Exception] = None):
        super().__init__(
            message,
            error_code="NETWORK_ERROR",
            retryable=retryable,
            original_exception=original_exception
        )


class TimeoutError(ShadowPurgeError):
    """Raised when a request times out."""
    def __init__(self, message: str = "Request timed out",
                 original_exception: Optional[Exception] = None):
        super().__init__(
            message,
            error_code="TIMEOUT",
            retryable=True,
            original_exception=original_exception
        )


class RateLimitError(ShadowPurgeError):
    """Raised when rate limited by a platform."""
    def __init__(self, message: str = "Rate limit exceeded",
                 retry_after: Optional[int] = None):
        super().__init__(
            message,
            error_code="RATE_LIMIT",
            retryable=True
        )
        self.retry_after = retry_after


class OSINTError(ShadowPurgeError):
    """Raised when OSINT scanning fails."""
    pass


class DeletionError(ShadowPurgeError):
    """Raised when account deletion fails."""
    def __init__(self, message: str, platform: Optional[str] = None,
                 retryable: bool = False):
        super().__init__(
            message,
            error_code="DELETION_ERROR",
            retryable=retryable
        )
        self.platform = platform


class VerificationError(ShadowPurgeError):
    """Raised when identity verification fails."""
    def __init__(self, message: str = "Identity verification failed"):
        super().__init__(
            message,
            error_code="VERIFICATION_FAILED",
            retryable=False
        )


class RegistryError(ShadowPurgeError):
    """Raised when platform registry operations fail."""
    pass


class ConfigurationError(ShadowPurgeError):
    """Raised when configuration is invalid."""
    def __init__(self, message: str):
        super().__init__(
            message,
            error_code="CONFIG_ERROR",
            retryable=False
        )