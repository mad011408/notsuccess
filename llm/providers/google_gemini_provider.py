"""
NEXUS AI Agent - Google Gemini Provider
"""

import os
from typing import Optional, List, Dict, Any, AsyncGenerator
from datetime import datetime

from .base_provider import BaseLLMProvider, LLMResponse, GenerationConfig

from config.logging_config import get_logger


logger = get_logger(__name__)


class GoogleGeminiProvider(BaseLLMProvider):
    """Google Gemini API provider"""

    PRICING = {
        "gemini-pro": {"input": 0.00025, "output": 0.0005},
        "gemini-pro-vision": {"input": 0.00025, "output": 0.0005},
        "gemini-1.5-pro": {"input": 0.00125, "output": 0.005},
        "gemini-1.5-flash": {"input": 0.000075, "output": 0.0003},
        "gemini-ultra": {"input": 0.0025, "output": 0.0075},
    }

    def __init__(self, api_key: Optional[str] = None, **kwargs):
        super().__init__(api_key or os.getenv("GOOGLE_API_KEY"), **kwargs)
        self._model_cache = {}

    @property
    def provider_name(self) -> str:
        return "google"

    @property
    def supported_models(self) -> List[str]:
        return [
            "gemini-pro",
            "gemini-pro-vision",
            "gemini-1.5-pro",
            "gemini-1.5-flash",
            "gemini-ultra",
        ]

    async def initialize(self) -> None:
        """Initialize Google Gemini client"""
        if self._initialized:
            return

        try:
            import google.generativeai as genai

            genai.configure(api_key=self.api_key)
            self._genai = genai
            self._initialized = True
            logger.info("Google Gemini provider initialized")

        except ImportError:
            raise ImportError("google-generativeai package required: pip install google-generativeai")

    def _get_model(self, model: str):
        """Get or create model instance"""
        if model not in self._model_cache:
            self._model_cache[model] = self._genai.GenerativeModel(model)
        return self._model_cache[model]

    async def generate(
        self,
        messages: List[Dict[str, str]],
        model: str,
        config: Optional[GenerationConfig] = None,
        **kwargs
    ) -> LLMResponse:
        """Generate response from Gemini"""
        if not self._initialized:
            await self.initialize()

        config = config or GenerationConfig()
        start_time = datetime.utcnow()

        # Convert messages to Gemini format
        gemini_messages = self._convert_messages(messages)
        gemini_model = self._get_model(model)

        try:
            generation_config = self._genai.types.GenerationConfig(
                temperature=config.temperature,
                max_output_tokens=config.max_tokens,
                top_p=config.top_p,
                stop_sequences=config.stop_sequences or [],
            )

            response = await gemini_model.generate_content_async(
                gemini_messages,
                generation_config=generation_config,
            )

            end_time = datetime.utcnow()
            latency = (end_time - start_time).total_seconds() * 1000

            content = response.text if response.text else ""

            # Estimate tokens (Gemini doesn't always return usage)
            input_tokens = sum(len(m.get("content", "")) for m in messages) // 4
            output_tokens = len(content) // 4

            return LLMResponse(
                content=content,
                model=model,
                provider=self.provider_name,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                total_tokens=input_tokens + output_tokens,
                finish_reason=response.candidates[0].finish_reason.name if response.candidates else "",
                latency_ms=latency,
                cost=self._calculate_cost(input_tokens, output_tokens, model),
                raw_response={"text": content},
            )

        except Exception as e:
            logger.error(f"Gemini generation error: {e}")
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

        # Convert messages to Gemini format
        gemini_messages = self._convert_messages(messages)
        gemini_model = self._get_model(model)

        try:
            generation_config = self._genai.types.GenerationConfig(
                temperature=config.temperature,
                max_output_tokens=config.max_tokens,
                top_p=config.top_p,
            )

            response = await gemini_model.generate_content_async(
                gemini_messages,
                generation_config=generation_config,
                stream=True,
            )

            async for chunk in response:
                if chunk.text:
                    yield chunk.text

        except Exception as e:
            logger.error(f"Gemini streaming error: {e}")
            raise

    async def generate_with_tools(
        self,
        messages: List[Dict[str, str]],
        model: str,
        tools: List[Dict[str, Any]],
        config: Optional[GenerationConfig] = None,
        **kwargs
    ) -> LLMResponse:
        """Generate with function calling"""
        if not self._initialized:
            await self.initialize()

        config = config or GenerationConfig()
        start_time = datetime.utcnow()

        # Convert messages
        gemini_messages = self._convert_messages(messages)

        # Convert tools to Gemini function declarations
        function_declarations = []
        for tool in tools:
            func = tool.get("function", tool)
            function_declarations.append({
                "name": func.get("name"),
                "description": func.get("description"),
                "parameters": func.get("parameters", {})
            })

        gemini_model = self._genai.GenerativeModel(
            model,
            tools=[{"function_declarations": function_declarations}]
        )

        try:
            generation_config = self._genai.types.GenerationConfig(
                temperature=config.temperature,
                max_output_tokens=config.max_tokens,
            )

            response = await gemini_model.generate_content_async(
                gemini_messages,
                generation_config=generation_config,
            )

            end_time = datetime.utcnow()
            latency = (end_time - start_time).total_seconds() * 1000

            content = ""
            tool_calls = []

            for candidate in response.candidates:
                for part in candidate.content.parts:
                    if hasattr(part, "text") and part.text:
                        content += part.text
                    elif hasattr(part, "function_call"):
                        tool_calls.append({
                            "id": f"call_{len(tool_calls)}",
                            "type": "function",
                            "function": {
                                "name": part.function_call.name,
                                "arguments": dict(part.function_call.args)
                            }
                        })

            input_tokens = sum(len(m.get("content", "")) for m in messages) // 4
            output_tokens = len(content) // 4

            return LLMResponse(
                content=content,
                model=model,
                provider=self.provider_name,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                total_tokens=input_tokens + output_tokens,
                finish_reason="",
                latency_ms=latency,
                cost=self._calculate_cost(input_tokens, output_tokens, model),
                tool_calls=tool_calls if tool_calls else None,
            )

        except Exception as e:
            logger.error(f"Gemini tool use error: {e}")
            raise

    async def embed(
        self,
        text: str,
        model: Optional[str] = None
    ) -> List[float]:
        """Generate embeddings"""
        if not self._initialized:
            await self.initialize()

        model = model or "embedding-001"

        try:
            result = self._genai.embed_content(
                model=f"models/{model}",
                content=text,
                task_type="retrieval_document"
            )
            return result["embedding"]

        except Exception as e:
            logger.error(f"Gemini embedding error: {e}")
            raise

    def _convert_messages(self, messages: List[Dict[str, str]], response_number: int = 1) -> List[Dict[str, Any]]:
        """Convert messages to Gemini format with enforcement"""
        gemini_messages = []
        system_prompt = ""

        for msg in messages:
            role = msg["role"]
            content = msg["content"]

            if role == "system":
                system_prompt = content
            elif role == "user":
                gemini_messages.append({
                    "role": "user",
                    "parts": [content]
                })
            elif role == "assistant":
                gemini_messages.append({
                    "role": "model",
                    "parts": [content]
                })

        # DIRECT pass - system prompt goes straight to model
        if system_prompt and gemini_messages:
            first_msg = gemini_messages[0]
            if first_msg["role"] == "user":
                first_msg["parts"][0] = f"{system_prompt}\n\n{first_msg['parts'][0]}"

        return gemini_messages

    def _calculate_cost(
        self,
        input_tokens: int,
        output_tokens: int,
        model: str
    ) -> float:
        """Calculate cost for API call"""
        pricing = self.PRICING.get(model, {"input": 0.0, "output": 0.0})
        input_cost = (input_tokens / 1000) * pricing["input"]
        output_cost = (output_tokens / 1000) * pricing["output"]
        return input_cost + output_cost

    async def close(self) -> None:
        """Cleanup"""
        self._model_cache.clear()
        self._initialized = False
