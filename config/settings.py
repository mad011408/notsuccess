"""
NEXUS AI Agent - Main Settings Configuration
"""

from typing import Optional, List, Dict, Any
from pydantic_settings import BaseSettings
from pydantic import Field
from functools import lru_cache
from enum import Enum


class Environment(str, Enum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class LogLevel(str, Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class Settings(BaseSettings):
    """Main application settings"""

    # Application Settings
    app_name: str = Field(default="NEXUS AI Agent", description="Application name")
    app_version: str = Field(default="1.0.0", description="Application version")
    environment: Environment = Field(default=Environment.DEVELOPMENT, description="Environment")
    debug: bool = Field(default=False, description="Debug mode")

    # Server Settings
    host: str = Field(default="0.0.0.0", description="Server host")
    port: int = Field(default=8000, description="Server port")
    workers: int = Field(default=4, description="Number of workers")

    # LLM Settings - TryBons AI Configuration
    default_llm_provider: str = Field(default="anthropic", description="Default LLM provider")
    default_model: str = Field(default="claude-opus-4-5", description="Default model")
    max_tokens: int = Field(default=49000, description="Max tokens per request")
    default_temperature: float = Field(default=0.7, description="Default temperature")
    streaming_enabled: bool = Field(default=True, description="Enable streaming")
    default_timeout: int = Field(default=1600, description="Default timeout in seconds")

    # TryBons AI API Configuration
    api_key: str = Field(
        default="sk_cr_CLACzLNP4e7FGgNFLZ3NuaT25vaJQj3hMPufwsYZG4oG",
        description="TryBons AI API Key"
    )
    api_base_url: str = Field(
        default="https://go.trybons.ai",
        description="TryBons AI Base URL"
    )

    # Available Models
    available_models: List[str] = Field(
        default=[
            "claude-opus-4-1-20250805",
            "claude-opus-4-5",
            "claude-opus-4-5-20251101"
        ],
        description="Available Claude models"
    )

    # Memory Settings
    memory_type: str = Field(default="conversation_buffer", description="Memory type")
    max_memory_tokens: int = Field(default=8000, description="Max memory tokens")
    vector_store_type: str = Field(default="chromadb", description="Vector store type")
    embedding_model: str = Field(default="text-embedding-3-small", description="Embedding model")

    # Database Settings
    database_url: str = Field(
        default="sqlite:///./nexus.db",
        env="DATABASE_URL",
        description="Database URL"
    )
    redis_url: Optional[str] = Field(default=None, env="REDIS_URL")

    # Security Settings
    secret_key: str = Field(default="your-secret-key-change-in-production", env="SECRET_KEY")
    jwt_algorithm: str = Field(default="HS256", description="JWT algorithm")
    access_token_expire_minutes: int = Field(default=30, description="Token expiry")
    rate_limit_requests: int = Field(default=100, description="Rate limit requests")
    rate_limit_period: int = Field(default=60, description="Rate limit period (seconds)")

    # Logging Settings
    log_level: LogLevel = Field(default=LogLevel.INFO, description="Log level")
    log_format: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        description="Log format"
    )
    log_file: Optional[str] = Field(default="logs/nexus.log", description="Log file path")

    # Tool Settings
    enable_web_search: bool = Field(default=True, description="Enable web search")
    enable_code_execution: bool = Field(default=True, description="Enable code execution")
    sandbox_enabled: bool = Field(default=True, description="Enable sandbox for code")
    max_execution_time: int = Field(default=30, description="Max code execution time (s)")

    # Agent Settings
    max_iterations: int = Field(default=10, description="Max agent iterations")
    max_retries: int = Field(default=3, description="Max retries on failure")
    agent_timeout: int = Field(default=1600, description="Agent timeout (seconds)")

    # RAG Settings
    chunk_size: int = Field(default=1000, description="Document chunk size")
    chunk_overlap: int = Field(default=200, description="Chunk overlap")
    top_k_retrieval: int = Field(default=5, description="Top K retrieval results")

    # Cost Tracking
    track_costs: bool = Field(default=True, description="Track API costs")
    cost_alert_threshold: float = Field(default=10.0, description="Cost alert threshold ($)")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()


# Global settings instance
settings = get_settings()
