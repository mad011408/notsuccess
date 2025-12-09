"""
NEXUS AI Agent - Model Registry
"""

from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime

from config.logging_config import get_logger
from config.model_config import ModelInfo, ModelCapabilities


logger = get_logger(__name__)


@dataclass
class RegisteredModel:
    """Registered model information"""
    model_id: str
    provider: str
    display_name: str
    context_window: int
    input_price_per_1k: float
    output_price_per_1k: float
    capabilities: Dict[str, Any] = field(default_factory=dict)
    aliases: List[str] = field(default_factory=list)
    is_available: bool = True
    last_checked: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class ModelRegistry:
    """
    Central registry for all available models

    Manages:
    - Model registration
    - Model lookup
    - Model aliases
    - Availability tracking
    """

    def __init__(self):
        self._models: Dict[str, RegisteredModel] = {}
        self._aliases: Dict[str, str] = {}
        self._load_default_models()

    def _load_default_models(self) -> None:
        """Load default model configurations"""
        default_models = [
            # OpenAI
            RegisteredModel(
                model_id="gpt-4o",
                provider="openai",
                display_name="GPT-4o",
                context_window=128000,
                input_price_per_1k=0.005,
                output_price_per_1k=0.015,
                capabilities={"vision": True, "functions": True, "streaming": True},
                aliases=["gpt4o", "gpt-4-omni"]
            ),
            RegisteredModel(
                model_id="gpt-4o-mini",
                provider="openai",
                display_name="GPT-4o Mini",
                context_window=128000,
                input_price_per_1k=0.00015,
                output_price_per_1k=0.0006,
                capabilities={"vision": True, "functions": True, "streaming": True},
                aliases=["gpt4o-mini", "mini"]
            ),
            RegisteredModel(
                model_id="gpt-4-turbo",
                provider="openai",
                display_name="GPT-4 Turbo",
                context_window=128000,
                input_price_per_1k=0.01,
                output_price_per_1k=0.03,
                capabilities={"vision": True, "functions": True, "streaming": True},
                aliases=["gpt4-turbo"]
            ),
            RegisteredModel(
                model_id="o1",
                provider="openai",
                display_name="O1",
                context_window=128000,
                input_price_per_1k=0.015,
                output_price_per_1k=0.06,
                capabilities={"vision": True, "functions": False, "streaming": False},
                aliases=["o1-full"]
            ),

            # Anthropic
            RegisteredModel(
                model_id="claude-3-5-sonnet-20241022",
                provider="anthropic",
                display_name="Claude 3.5 Sonnet",
                context_window=200000,
                input_price_per_1k=0.003,
                output_price_per_1k=0.015,
                capabilities={"vision": True, "functions": True, "streaming": True},
                aliases=["claude-3.5-sonnet", "claude-sonnet", "sonnet"]
            ),
            RegisteredModel(
                model_id="claude-3-opus-20240229",
                provider="anthropic",
                display_name="Claude 3 Opus",
                context_window=200000,
                input_price_per_1k=0.015,
                output_price_per_1k=0.075,
                capabilities={"vision": True, "functions": True, "streaming": True},
                aliases=["claude-opus", "opus"]
            ),
            RegisteredModel(
                model_id="claude-3-haiku-20240307",
                provider="anthropic",
                display_name="Claude 3 Haiku",
                context_window=200000,
                input_price_per_1k=0.00025,
                output_price_per_1k=0.00125,
                capabilities={"vision": True, "functions": True, "streaming": True},
                aliases=["claude-haiku", "haiku"]
            ),

            # Google
            RegisteredModel(
                model_id="gemini-1.5-pro",
                provider="google",
                display_name="Gemini 1.5 Pro",
                context_window=1000000,
                input_price_per_1k=0.00125,
                output_price_per_1k=0.005,
                capabilities={"vision": True, "functions": True, "streaming": True},
                aliases=["gemini-pro", "gemini"]
            ),
            RegisteredModel(
                model_id="gemini-1.5-flash",
                provider="google",
                display_name="Gemini 1.5 Flash",
                context_window=1000000,
                input_price_per_1k=0.000075,
                output_price_per_1k=0.0003,
                capabilities={"vision": True, "functions": True, "streaming": True},
                aliases=["gemini-flash", "flash"]
            ),

            # Groq (Free)
            RegisteredModel(
                model_id="llama-3.1-70b-versatile",
                provider="groq",
                display_name="Llama 3.1 70B",
                context_window=131072,
                input_price_per_1k=0.0,
                output_price_per_1k=0.0,
                capabilities={"vision": False, "functions": True, "streaming": True},
                aliases=["llama-70b", "llama3-70b"]
            ),
            RegisteredModel(
                model_id="llama-3.1-8b-instant",
                provider="groq",
                display_name="Llama 3.1 8B",
                context_window=131072,
                input_price_per_1k=0.0,
                output_price_per_1k=0.0,
                capabilities={"vision": False, "functions": True, "streaming": True},
                aliases=["llama-8b", "llama3-8b"]
            ),

            # Mistral
            RegisteredModel(
                model_id="mistral-large-latest",
                provider="mistral",
                display_name="Mistral Large",
                context_window=32000,
                input_price_per_1k=0.004,
                output_price_per_1k=0.012,
                capabilities={"vision": False, "functions": True, "streaming": True},
                aliases=["mistral-large", "mistral"]
            ),

            # DeepSeek
            RegisteredModel(
                model_id="deepseek-chat",
                provider="deepseek",
                display_name="DeepSeek Chat",
                context_window=64000,
                input_price_per_1k=0.00014,
                output_price_per_1k=0.00028,
                capabilities={"vision": False, "functions": True, "streaming": True},
                aliases=["deepseek"]
            ),
        ]

        for model in default_models:
            self.register(model)

    def register(self, model: RegisteredModel) -> None:
        """Register a model"""
        self._models[model.model_id] = model

        # Register aliases
        for alias in model.aliases:
            self._aliases[alias.lower()] = model.model_id

        logger.debug(f"Model registered: {model.model_id}")

    def get(self, model_id: str) -> Optional[RegisteredModel]:
        """Get model by ID or alias"""
        # Check direct ID
        if model_id in self._models:
            return self._models[model_id]

        # Check aliases
        resolved_id = self._aliases.get(model_id.lower())
        if resolved_id:
            return self._models.get(resolved_id)

        return None

    def resolve_alias(self, alias: str) -> Optional[str]:
        """Resolve alias to model ID"""
        if alias in self._models:
            return alias
        return self._aliases.get(alias.lower())

    def list_models(
        self,
        provider: Optional[str] = None,
        capability: Optional[str] = None,
        available_only: bool = True
    ) -> List[RegisteredModel]:
        """
        List models with optional filtering

        Args:
            provider: Filter by provider
            capability: Filter by capability
            available_only: Only show available models

        Returns:
            List of matching models
        """
        models = list(self._models.values())

        if provider:
            models = [m for m in models if m.provider == provider]

        if capability:
            models = [m for m in models if m.capabilities.get(capability)]

        if available_only:
            models = [m for m in models if m.is_available]

        return models

    def list_by_provider(self, provider: str) -> List[RegisteredModel]:
        """List all models for a provider"""
        return [m for m in self._models.values() if m.provider == provider]

    def list_providers(self) -> List[str]:
        """List all available providers"""
        return list(set(m.provider for m in self._models.values()))

    def get_cheapest(
        self,
        min_context: int = 0,
        capability: Optional[str] = None
    ) -> Optional[RegisteredModel]:
        """Get cheapest model meeting requirements"""
        models = self.list_models(capability=capability)
        models = [m for m in models if m.context_window >= min_context]

        if not models:
            return None

        return min(models, key=lambda m: m.input_price_per_1k + m.output_price_per_1k)

    def get_best_quality(
        self,
        provider: Optional[str] = None
    ) -> Optional[RegisteredModel]:
        """Get highest quality model"""
        models = self.list_models(provider=provider)

        if not models:
            return None

        # Quality heuristic: higher price usually means higher quality
        return max(models, key=lambda m: m.input_price_per_1k + m.output_price_per_1k)

    def calculate_cost(
        self,
        model_id: str,
        input_tokens: int,
        output_tokens: int
    ) -> float:
        """Calculate cost for token usage"""
        model = self.get(model_id)
        if not model:
            return 0.0

        input_cost = (input_tokens / 1000) * model.input_price_per_1k
        output_cost = (output_tokens / 1000) * model.output_price_per_1k
        return input_cost + output_cost

    def set_availability(self, model_id: str, available: bool) -> None:
        """Set model availability"""
        model = self.get(model_id)
        if model:
            model.is_available = available
            model.last_checked = datetime.utcnow()

    def add_alias(self, model_id: str, alias: str) -> bool:
        """Add alias for a model"""
        if model_id in self._models:
            self._aliases[alias.lower()] = model_id
            self._models[model_id].aliases.append(alias)
            return True
        return False

    def search(self, query: str) -> List[RegisteredModel]:
        """Search models by name or alias"""
        query = query.lower()
        results = []

        for model in self._models.values():
            if query in model.model_id.lower() or query in model.display_name.lower():
                results.append(model)
                continue

            for alias in model.aliases:
                if query in alias.lower():
                    results.append(model)
                    break

        return results


# Global registry instance
model_registry = ModelRegistry()
