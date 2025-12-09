"""
NEXUS AI Agent - Model Configuration
TryBons AI - Claude Models Only
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum

from .constants import (
    LLMProvider,
    ClaudeModels,
    TOKEN_LIMITS,
    MODEL_PRICING,
    API_KEY,
    API_BASE_URL,
    AVAILABLE_MODELS,
    DEFAULT_MODEL
)


@dataclass
class ModelCapabilities:
    """Model capabilities configuration"""
    supports_functions: bool = True
    supports_vision: bool = True
    supports_streaming: bool = True
    supports_json_mode: bool = False
    supports_system_message: bool = True
    max_images: int = 20
    supports_tools: bool = True


@dataclass
class ModelParameters:
    """Model parameters configuration"""
    temperature: float = 0.7
    max_tokens: int = 49000
    top_p: float = 1.0
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0
    stop_sequences: List[str] = field(default_factory=list)
    timeout: int = 1600


@dataclass
class ModelInfo:
    """Complete model information"""
    model_id: str
    provider: LLMProvider
    display_name: str
    context_window: int
    input_price_per_1k: float
    output_price_per_1k: float
    capabilities: ModelCapabilities = field(default_factory=ModelCapabilities)
    default_parameters: ModelParameters = field(default_factory=ModelParameters)
    description: str = ""
    deprecated: bool = False


class ModelConfig:
    """
    Model configuration manager for TryBons AI
    Supports only Claude models via custom API endpoint
    """

    # API Configuration
    API_KEY = API_KEY
    API_BASE_URL = API_BASE_URL

    def __init__(self):
        self._models: Dict[str, ModelInfo] = {}
        self._load_claude_models()

    def _load_claude_models(self) -> None:
        """Load Claude model configurations for TryBons AI"""

        # Claude Opus 4.1
        self._models["claude-opus-4-1-20250805"] = ModelInfo(
            model_id="claude-opus-4-1-20250805",
            provider=LLMProvider.ANTHROPIC,
            display_name="Claude Opus 4.1",
            context_window=200000,
            input_price_per_1k=0.015,
            output_price_per_1k=0.075,
            capabilities=ModelCapabilities(
                supports_functions=True,
                supports_vision=True,
                supports_streaming=True,
                supports_tools=True,
                max_images=20
            ),
            description="Claude Opus 4.1 - Advanced reasoning model"
        )

        # Claude Opus 4.5
        self._models["claude-opus-4-5"] = ModelInfo(
            model_id="claude-opus-4-5",
            provider=LLMProvider.ANTHROPIC,
            display_name="Claude Opus 4.5",
            context_window=200000,
            input_price_per_1k=0.015,
            output_price_per_1k=0.075,
            capabilities=ModelCapabilities(
                supports_functions=True,
                supports_vision=True,
                supports_streaming=True,
                supports_tools=True,
                max_images=20
            ),
            description="Claude Opus 4.5 - Latest and most capable model"
        )

        # Claude Opus 4.5 Dated
        self._models["claude-opus-4-5-20251101"] = ModelInfo(
            model_id="claude-opus-4-5-20251101",
            provider=LLMProvider.ANTHROPIC,
            display_name="Claude Opus 4.5 (Nov 2025)",
            context_window=200000,
            input_price_per_1k=0.015,
            output_price_per_1k=0.075,
            capabilities=ModelCapabilities(
                supports_functions=True,
                supports_vision=True,
                supports_streaming=True,
                supports_tools=True,
                max_images=20
            ),
            description="Claude Opus 4.5 - November 2025 snapshot"
        )

    def get_model(self, model_id: str) -> Optional[ModelInfo]:
        """Get model information by ID"""
        return self._models.get(model_id)

    def get_default_model(self) -> str:
        """Get the default model ID"""
        return DEFAULT_MODEL

    def list_models(self, provider: Optional[LLMProvider] = None) -> List[ModelInfo]:
        """List all available models"""
        models = list(self._models.values())
        if provider:
            models = [m for m in models if m.provider == provider]
        return models

    def list_model_ids(self) -> List[str]:
        """List all available model IDs"""
        return AVAILABLE_MODELS.copy()

    def get_models_by_capability(self, capability: str) -> List[ModelInfo]:
        """Get models that support a specific capability"""
        return [
            m for m in self._models.values()
            if getattr(m.capabilities, capability, False)
        ]

    def register_model(self, model_info: ModelInfo) -> None:
        """Register a new model"""
        self._models[model_info.model_id] = model_info

    def get_token_limit(self, model_id: str) -> int:
        """Get token limit for a model"""
        model = self._models.get(model_id)
        if model:
            return model.context_window
        return TOKEN_LIMITS.get(model_id, 200000)

    def get_pricing(self, model_id: str) -> Dict[str, float]:
        """Get pricing for a model"""
        model = self._models.get(model_id)
        if model:
            return {
                "input": model.input_price_per_1k,
                "output": model.output_price_per_1k
            }
        return MODEL_PRICING.get(model_id, {"input": 0.015, "output": 0.075})

    def calculate_cost(
        self,
        model_id: str,
        input_tokens: int,
        output_tokens: int
    ) -> float:
        """Calculate cost for token usage"""
        pricing = self.get_pricing(model_id)
        input_cost = (input_tokens / 1000) * pricing["input"]
        output_cost = (output_tokens / 1000) * pricing["output"]
        return input_cost + output_cost

    def is_valid_model(self, model_id: str) -> bool:
        """Check if model ID is valid"""
        return model_id in self._models

    def get_api_config(self) -> Dict[str, Any]:
        """Get API configuration"""
        return {
            "api_key": self.API_KEY,
            "base_url": self.API_BASE_URL,
            "provider": "anthropic",
            "available_models": AVAILABLE_MODELS,
            "default_model": DEFAULT_MODEL
        }


# Global model config instance
model_config = ModelConfig()


def get_model_info(model_id: str) -> Optional[ModelInfo]:
    """Get model information"""
    return model_config.get_model(model_id)


def get_available_models() -> List[str]:
    """Get list of available models"""
    return model_config.list_model_ids()


def get_default_model() -> str:
    """Get default model"""
    return model_config.get_default_model()
