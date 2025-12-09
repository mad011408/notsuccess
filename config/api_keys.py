"""
NEXUS AI Agent - API Keys Configuration
TryBons AI Configuration
"""

from typing import Optional, Dict, Any
from dataclasses import dataclass
from config.logging_config import get_logger


logger = get_logger(__name__)


# =============================================================================
# TryBons AI API Configuration
# =============================================================================

@dataclass
class APIConfig:
    """API Configuration for TryBons AI"""
    api_key: str = "sk_cr_CLACzLNP4e7FGgNFLZ3NuaT25vaJQj3hMPufwsYZG4oG"
    base_url: str = "https://go.trybons.ai"
    provider: str = "anthropic"

    def get_headers(self) -> Dict[str, str]:
        """Get headers for API requests"""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "anthropic-version": "2023-06-01",
            "x-api-key": self.api_key
        }


class APIKeyManager:
    """
    Manages API keys and configurations for TryBons AI
    """

    # Default Configuration
    DEFAULT_API_KEY = "sk_cr_CLACzLNP4e7FGgNFLZ3NuaT25vaJQj3hMPufwsYZG4oG"
    DEFAULT_BASE_URL = "https://go.trybons.ai"

    AVAILABLE_MODELS = [
        "claude-opus-4-1-20250805",
        "claude-opus-4-5",
        "claude-opus-4-5-20251101"
    ]

    def __init__(self):
        self._config = APIConfig()
        self._initialized = False

    @property
    def api_key(self) -> str:
        """Get the API key"""
        return self._config.api_key

    @property
    def base_url(self) -> str:
        """Get the base URL"""
        return self._config.base_url

    @property
    def provider(self) -> str:
        """Get the provider name"""
        return self._config.provider

    def set_api_key(self, api_key: str) -> None:
        """Set a custom API key"""
        self._config.api_key = api_key
        logger.info("API key updated")

    def set_base_url(self, base_url: str) -> None:
        """Set a custom base URL"""
        self._config.base_url = base_url
        logger.info(f"Base URL updated to: {base_url}")

    def get_headers(self) -> Dict[str, str]:
        """Get headers for API requests"""
        return self._config.get_headers()

    def get_config(self) -> Dict[str, Any]:
        """Get full configuration"""
        return {
            "api_key": self._mask_key(self._config.api_key),
            "base_url": self._config.base_url,
            "provider": self._config.provider,
            "available_models": self.AVAILABLE_MODELS
        }

    def validate(self) -> bool:
        """Validate API configuration"""
        if not self._config.api_key:
            logger.error("API key is not set")
            return False

        if not self._config.base_url:
            logger.error("Base URL is not set")
            return False

        if not self._config.api_key.startswith("sk_"):
            logger.warning("API key format may be invalid")

        return True

    def get_endpoint(self, path: str) -> str:
        """Get full endpoint URL"""
        base = self._config.base_url.rstrip("/")
        path = path.lstrip("/")
        return f"{base}/{path}"

    def get_chat_endpoint(self) -> str:
        """Get chat completions endpoint"""
        return self.get_endpoint("/v1/messages")

    def get_completions_endpoint(self) -> str:
        """Get completions endpoint"""
        return self.get_endpoint("/v1/complete")

    def get_key(self, provider: str = "anthropic") -> Optional[str]:
        """Get API key for provider (for compatibility)"""
        if provider == "anthropic":
            return self._config.api_key
        return None

    def has_key(self, provider: str = "anthropic") -> bool:
        """Check if provider has key configured"""
        return provider == "anthropic" and bool(self._config.api_key)

    def list_providers(self) -> list:
        """List available providers"""
        return ["anthropic"]

    @staticmethod
    def _mask_key(key: str) -> str:
        """Mask API key for display"""
        if len(key) <= 8:
            return "*" * len(key)
        return key[:8] + "*" * (len(key) - 12) + key[-4:]


# Global API manager instance
api_key_manager = APIKeyManager()


def get_api_key() -> str:
    """Get the API key"""
    return api_key_manager.api_key


def get_base_url() -> str:
    """Get the base URL"""
    return api_key_manager.base_url


def get_api_headers() -> Dict[str, str]:
    """Get API headers"""
    return api_key_manager.get_headers()
