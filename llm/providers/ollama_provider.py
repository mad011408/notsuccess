"""
NEXUS AI Agent - Ollama Provider (Local Models)
"""

import os
from typing import Optional, List, Dict, Any, AsyncGenerator
from datetime import datetime
import aiohttp

from .base_provider import BaseLLMProvider, LLMResponse, GenerationConfig

from config.logging_config import get_logger


logger = get_logger(__name__)


class OllamaProvider(BaseLLMProvider):
    """Ollama provider for local model inference"""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = "http://localhost:11434",
        **kwargs
    ):
        super().__init__(api_key, **kwargs)
        self._base_url = base_url
        self._session: Optional[aiohttp.ClientSession] = None

    @property
    def provider_name(self) -> str:
        return "ollama"

    @property
    def supported_models(self) -> List[str]:
        # Common Ollama models
        return [
            "llama3.1",
            "llama3.1:70b",
            "llama3.1:405b",
            "llama3",
            "llama3:70b",
            "codellama",
            "codellama:34b",
            "mistral",
            "mixtral",
            "mixtral:8x22b",
            "phi3",
            "phi3:medium",
            "gemma2",
            "gemma2:27b",
            "qwen2",
            "qwen2:72b",
            "deepseek-coder-v2",
        ]

    async def initialize(self) -> None:
        """Initialize Ollama client"""
        if self._initialized:
            return

        self._session = aiohttp.ClientSession()
        self._initialized = True
        logger.info(f"Ollama provider initialized at {self._base_url}")

    async def generate(
        self,
        messages: List[Dict[str, str]],
        model: str,
        config: Optional[GenerationConfig] = None,
        **kwargs
    ) -> LLMResponse:
        """Generate response from Ollama"""
        if not self._initialized:
            await self.initialize()

        config = config or GenerationConfig()
        start_time = datetime.utcnow()

        try:
            payload = {
                "model": model,
                "messages": messages,
                "stream": False,
                "options": {
                    "temperature": config.temperature,
                    "num_predict": config.max_tokens,
                    "top_p": config.top_p,
                }
            }

            if config.stop_sequences:
                payload["options"]["stop"] = config.stop_sequences

            async with self._session.post(
                f"{self._base_url}/api/chat",
                json=payload
            ) as response:
                response.raise_for_status()
                data = await response.json()

            end_time = datetime.utcnow()
            latency = (end_time - start_time).total_seconds() * 1000

            content = data.get("message", {}).get("content", "")

            # Ollama provides eval counts
            eval_count = data.get("eval_count", 0)
            prompt_eval_count = data.get("prompt_eval_count", 0)

            return LLMResponse(
                content=content,
                model=model,
                provider=self.provider_name,
                input_tokens=prompt_eval_count,
                output_tokens=eval_count,
                total_tokens=prompt_eval_count + eval_count,
                finish_reason=data.get("done_reason", "stop"),
                latency_ms=latency,
                cost=0.0,  # Local models are free
                raw_response=data,
            )

        except Exception as e:
            logger.error(f"Ollama generation error: {e}")
            raise

    async def generate_stream(
        self,
        messages: List[Dict[str, str]],
        model: str,
        config: Optional[GenerationConfig] = None,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """Generate streaming response"""
        if not self._initialized:
            await self.initialize()

        config = config or GenerationConfig()

        try:
            payload = {
                "model": model,
                "messages": messages,
                "stream": True,
                "options": {
                    "temperature": config.temperature,
                    "num_predict": config.max_tokens,
                    "top_p": config.top_p,
                }
            }

            async with self._session.post(
                f"{self._base_url}/api/chat",
                json=payload
            ) as response:
                response.raise_for_status()

                async for line in response.content:
                    if line:
                        import json
                        try:
                            data = json.loads(line.decode())
                            if "message" in data and "content" in data["message"]:
                                yield data["message"]["content"]
                        except json.JSONDecodeError:
                            continue

        except Exception as e:
            logger.error(f"Ollama streaming error: {e}")
            raise

    async def embed(
        self,
        text: str,
        model: Optional[str] = None
    ) -> List[float]:
        """Generate embeddings"""
        if not self._initialized:
            await self.initialize()

        model = model or "nomic-embed-text"

        try:
            payload = {
                "model": model,
                "prompt": text
            }

            async with self._session.post(
                f"{self._base_url}/api/embeddings",
                json=payload
            ) as response:
                response.raise_for_status()
                data = await response.json()

            return data.get("embedding", [])

        except Exception as e:
            logger.error(f"Ollama embedding error: {e}")
            raise

    async def list_local_models(self) -> List[Dict[str, Any]]:
        """List locally available models"""
        if not self._initialized:
            await self.initialize()

        try:
            async with self._session.get(f"{self._base_url}/api/tags") as response:
                response.raise_for_status()
                data = await response.json()

            return data.get("models", [])

        except Exception as e:
            logger.error(f"Ollama list models error: {e}")
            return []

    async def pull_model(self, model: str) -> bool:
        """Pull a model from Ollama library"""
        if not self._initialized:
            await self.initialize()

        try:
            payload = {"name": model}

            async with self._session.post(
                f"{self._base_url}/api/pull",
                json=payload
            ) as response:
                response.raise_for_status()

                async for line in response.content:
                    if line:
                        import json
                        try:
                            data = json.loads(line.decode())
                            status = data.get("status", "")
                            logger.info(f"Pull {model}: {status}")
                        except:
                            pass

            return True

        except Exception as e:
            logger.error(f"Ollama pull model error: {e}")
            return False

    async def health_check(self) -> bool:
        """Check if Ollama is running"""
        try:
            if not self._session:
                await self.initialize()

            async with self._session.get(f"{self._base_url}/api/tags") as response:
                return response.status == 200

        except Exception:
            return False

    def _calculate_cost(
        self,
        input_tokens: int,
        output_tokens: int,
        model: str
    ) -> float:
        """Local models are free"""
        return 0.0

    async def close(self) -> None:
        """Cleanup"""
        if self._session:
            await self._session.close()
        self._session = None
        self._initialized = False
