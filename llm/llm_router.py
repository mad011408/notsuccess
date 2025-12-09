"""
NEXUS AI Agent - Intelligent LLM Router
"""

from typing import Optional, List, Dict, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
import asyncio

from .llm_client import LLMClient, PROVIDER_REGISTRY
from .providers.base_provider import LLMResponse, GenerationConfig

from config.logging_config import get_logger


logger = get_logger(__name__)


class RoutingStrategy(str, Enum):
    """Routing strategies"""
    COST_OPTIMIZED = "cost_optimized"
    QUALITY_OPTIMIZED = "quality_optimized"
    SPEED_OPTIMIZED = "speed_optimized"
    BALANCED = "balanced"
    FALLBACK = "fallback"
    ROUND_ROBIN = "round_robin"


@dataclass
class ModelCapability:
    """Model capability scores"""
    quality: float = 0.8
    speed: float = 0.5
    cost_efficiency: float = 0.5
    context_length: int = 8000
    supports_functions: bool = True
    supports_vision: bool = False


@dataclass
class RouteConfig:
    """Configuration for a route"""
    provider: str
    model: str
    priority: int = 0
    weight: float = 1.0
    max_tokens: int = 4096
    capability: ModelCapability = field(default_factory=ModelCapability)


class LLMRouter:
    """
    Intelligent LLM Router

    Routes requests to optimal models based on:
    - Task requirements
    - Cost optimization
    - Quality needs
    - Speed requirements
    - Fallback handling
    """

    def __init__(self, strategy: RoutingStrategy = RoutingStrategy.BALANCED):
        self._strategy = strategy
        self._routes: List[RouteConfig] = []
        self._clients: Dict[str, LLMClient] = {}
        self._round_robin_index = 0
        self._route_stats: Dict[str, Dict[str, Any]] = {}

    def add_route(
        self,
        provider: str,
        model: str,
        priority: int = 0,
        weight: float = 1.0,
        capability: Optional[ModelCapability] = None,
        **kwargs
    ) -> None:
        """
        Add a routing option

        Args:
            provider: Provider name
            model: Model name
            priority: Priority (higher = preferred)
            weight: Weight for load balancing
            capability: Model capability scores
            **kwargs: Additional config
        """
        route = RouteConfig(
            provider=provider,
            model=model,
            priority=priority,
            weight=weight,
            max_tokens=kwargs.get("max_tokens", 4096),
            capability=capability or ModelCapability()
        )
        self._routes.append(route)
        self._routes.sort(key=lambda x: x.priority, reverse=True)

        # Initialize client if needed
        if provider not in self._clients:
            self._clients[provider] = LLMClient(provider=provider, model=model)

        logger.info(f"Route added: {provider}/{model} (priority: {priority})")

    def remove_route(self, provider: str, model: str) -> bool:
        """Remove a route"""
        original_len = len(self._routes)
        self._routes = [
            r for r in self._routes
            if not (r.provider == provider and r.model == model)
        ]
        return len(self._routes) < original_len

    def set_strategy(self, strategy: RoutingStrategy) -> None:
        """Set routing strategy"""
        self._strategy = strategy
        logger.info(f"Routing strategy set to: {strategy.value}")

    async def route(
        self,
        messages: List[Dict[str, str]],
        requirements: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> LLMResponse:
        """
        Route request to optimal model

        Args:
            messages: Chat messages
            requirements: Task requirements
            **kwargs: Generation options

        Returns:
            LLMResponse from selected model
        """
        requirements = requirements or {}

        # Select best route
        route = self._select_route(requirements)

        if not route:
            raise ValueError("No available routes")

        # Get or create client
        client = self._clients.get(route.provider)
        if not client:
            client = LLMClient(provider=route.provider, model=route.model)
            self._clients[route.provider] = client

        try:
            # Make request
            response = await self._make_request(client, route, messages, **kwargs)

            # Update stats
            self._update_stats(route, success=True, response=response)

            return response

        except Exception as e:
            logger.error(f"Route {route.provider}/{route.model} failed: {e}")
            self._update_stats(route, success=False, error=str(e))

            # Try fallback if available
            if self._strategy == RoutingStrategy.FALLBACK:
                return await self._fallback(messages, route, **kwargs)

            raise

    async def route_stream(
        self,
        messages: List[Dict[str, str]],
        requirements: Optional[Dict[str, Any]] = None,
        **kwargs
    ):
        """Route streaming request"""
        requirements = requirements or {}
        route = self._select_route(requirements)

        if not route:
            raise ValueError("No available routes")

        client = self._clients.get(route.provider)
        if not client:
            client = LLMClient(provider=route.provider, model=route.model)
            self._clients[route.provider] = client

        async for chunk in client.generate_stream(
            messages,
            model=route.model,
            **kwargs
        ):
            yield chunk

    def _select_route(self, requirements: Dict[str, Any]) -> Optional[RouteConfig]:
        """Select optimal route based on strategy and requirements"""
        if not self._routes:
            return None

        available_routes = [r for r in self._routes]

        # Filter by requirements
        if requirements.get("min_context"):
            available_routes = [
                r for r in available_routes
                if r.capability.context_length >= requirements["min_context"]
            ]

        if requirements.get("needs_functions"):
            available_routes = [
                r for r in available_routes
                if r.capability.supports_functions
            ]

        if requirements.get("needs_vision"):
            available_routes = [
                r for r in available_routes
                if r.capability.supports_vision
            ]

        if not available_routes:
            return self._routes[0]  # Fallback to first route

        # Select based on strategy
        if self._strategy == RoutingStrategy.COST_OPTIMIZED:
            return self._select_cost_optimized(available_routes)
        elif self._strategy == RoutingStrategy.QUALITY_OPTIMIZED:
            return self._select_quality_optimized(available_routes)
        elif self._strategy == RoutingStrategy.SPEED_OPTIMIZED:
            return self._select_speed_optimized(available_routes)
        elif self._strategy == RoutingStrategy.ROUND_ROBIN:
            return self._select_round_robin(available_routes)
        else:  # BALANCED or FALLBACK
            return self._select_balanced(available_routes)

    def _select_cost_optimized(self, routes: List[RouteConfig]) -> RouteConfig:
        """Select most cost-efficient route"""
        return max(routes, key=lambda r: r.capability.cost_efficiency)

    def _select_quality_optimized(self, routes: List[RouteConfig]) -> RouteConfig:
        """Select highest quality route"""
        return max(routes, key=lambda r: r.capability.quality)

    def _select_speed_optimized(self, routes: List[RouteConfig]) -> RouteConfig:
        """Select fastest route"""
        return max(routes, key=lambda r: r.capability.speed)

    def _select_round_robin(self, routes: List[RouteConfig]) -> RouteConfig:
        """Select routes in round-robin fashion"""
        route = routes[self._round_robin_index % len(routes)]
        self._round_robin_index += 1
        return route

    def _select_balanced(self, routes: List[RouteConfig]) -> RouteConfig:
        """Select based on balanced scoring"""
        def score(route: RouteConfig) -> float:
            cap = route.capability
            return (cap.quality * 0.4 + cap.speed * 0.3 + cap.cost_efficiency * 0.3) * route.weight

        return max(routes, key=score)

    async def _make_request(
        self,
        client: LLMClient,
        route: RouteConfig,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> LLMResponse:
        """Make request to specific route"""
        await client.initialize()

        config = GenerationConfig(
            temperature=kwargs.get("temperature", 0.7),
            max_tokens=min(kwargs.get("max_tokens", 4096), route.max_tokens),
            top_p=kwargs.get("top_p", 1.0),
        )

        return await client._provider.generate(messages, route.model, config)

    async def _fallback(
        self,
        messages: List[Dict[str, str]],
        failed_route: RouteConfig,
        **kwargs
    ) -> LLMResponse:
        """Try fallback routes"""
        for route in self._routes:
            if route.provider == failed_route.provider and route.model == failed_route.model:
                continue

            try:
                client = self._clients.get(route.provider)
                if not client:
                    client = LLMClient(provider=route.provider, model=route.model)
                    self._clients[route.provider] = client

                response = await self._make_request(client, route, messages, **kwargs)
                logger.info(f"Fallback to {route.provider}/{route.model} succeeded")
                return response

            except Exception as e:
                logger.warning(f"Fallback {route.provider}/{route.model} failed: {e}")
                continue

        raise RuntimeError("All routes failed")

    def _update_stats(
        self,
        route: RouteConfig,
        success: bool,
        response: Optional[LLMResponse] = None,
        error: Optional[str] = None
    ) -> None:
        """Update routing statistics"""
        key = f"{route.provider}/{route.model}"

        if key not in self._route_stats:
            self._route_stats[key] = {
                "requests": 0,
                "successes": 0,
                "failures": 0,
                "total_tokens": 0,
                "total_latency_ms": 0,
            }

        stats = self._route_stats[key]
        stats["requests"] += 1

        if success:
            stats["successes"] += 1
            if response:
                stats["total_tokens"] += response.total_tokens
                stats["total_latency_ms"] += response.latency_ms
        else:
            stats["failures"] += 1

    def get_stats(self) -> Dict[str, Any]:
        """Get routing statistics"""
        return self._route_stats.copy()

    def get_routes(self) -> List[Dict[str, Any]]:
        """Get all configured routes"""
        return [
            {
                "provider": r.provider,
                "model": r.model,
                "priority": r.priority,
                "weight": r.weight,
                "capability": {
                    "quality": r.capability.quality,
                    "speed": r.capability.speed,
                    "cost_efficiency": r.capability.cost_efficiency,
                }
            }
            for r in self._routes
        ]

    async def close(self) -> None:
        """Cleanup all clients"""
        for client in self._clients.values():
            await client.close()
        self._clients.clear()


def create_router(strategy: str = "balanced") -> LLMRouter:
    """Create router with common configurations"""
    router = LLMRouter(strategy=RoutingStrategy(strategy))

    # Add common routes
    router.add_route(
        "openai", "gpt-4o",
        priority=10,
        capability=ModelCapability(quality=0.95, speed=0.7, cost_efficiency=0.6)
    )
    router.add_route(
        "openai", "gpt-4o-mini",
        priority=8,
        capability=ModelCapability(quality=0.85, speed=0.9, cost_efficiency=0.95)
    )
    router.add_route(
        "anthropic", "claude-3-5-sonnet-20241022",
        priority=9,
        capability=ModelCapability(quality=0.95, speed=0.75, cost_efficiency=0.7)
    )
    router.add_route(
        "groq", "llama-3.1-70b-versatile",
        priority=7,
        capability=ModelCapability(quality=0.85, speed=0.95, cost_efficiency=1.0)
    )

    return router
