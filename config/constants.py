"""
NEXUS AI Agent - Constants
"""

from enum import Enum
from typing import Dict, List

# =============================================================================
# LLM Provider Constants - TryBons AI Only
# =============================================================================

class LLMProvider(str, Enum):
    ANTHROPIC = "anthropic"
    NVIDIA = "nvidia"
    BYTEZ = "bytez"
    OPENROUTER = "openrouter"


class ClaudeModels(str, Enum):
    """Available Claude models via TryBons AI"""
    CLAUDE_OPUS_4_1 = "claude-opus-4-1-20250805"
    CLAUDE_OPUS_4_5 = "claude-opus-4-5"
    CLAUDE_OPUS_4_5_DATED = "claude-opus-4-5-20251101"


class NvidiaModels(str, Enum):
    """Available models via NVIDIA API"""
    MINIMAX_M2 = "minimaxai/minimax-m2"
    KIMI_K2 = "moonshotai/kimi-k2-instruct-0905"
    MISTRAL_LARGE = "mistralai/mistral-large-3-675b-instruct-2512"
    DEEPSEEK_V3 = "deepseek-ai/deepseek-v3.1-terminus"


class BytezModels(str, Enum):
    """Available models via Bytez API"""
    GPT_4_1 = "openai/gpt-4.1"
    GPT_4O = "openai/gpt-4o"
    GPT_5_1 = "openai/gpt-5.1"
    GPT_5 = "openai/gpt-5"


class OpenRouterModels(str, Enum):
    """Available models via OpenRouter API"""
    DEEPSEEK_V3_SPECIALE = "deepseek/deepseek-v3.2-speciale"
    KIMI_K2_FREE = "moonshotai/kimi-k2:free"


# =============================================================================
# API Configuration - TryBons AI (Anthropic/Claude)
# =============================================================================

API_KEY = "sk_cr_CLACzLNP4e7FGgNFLZ3NuaT25vaJQj3hMPufwsYZG4oG"
API_BASE_URL = "https://go.trybons.ai"

# =============================================================================
# API Configuration - NVIDIA
# =============================================================================

NVIDIA_API_KEY = "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"
NVIDIA_API_BASE_URL = "https://integrate.api.nvidia.com/v1"
NVIDIA_API_PATH = "/chat/completions"

# =============================================================================
# API Configuration - Bytez
# =============================================================================

BYTEZ_API_KEY = "2bf563bc9321a38a5add2a0d816a5662"
BYTEZ_API_BASE_URL = "https://api.bytez.com/models/v2/openai/v1"
BYTEZ_API_PATH = "/chat/completions"

# =============================================================================
# API Configuration - OpenRouter
# =============================================================================

OPENROUTER_API_KEY = "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"
OPENROUTER_API_BASE_URL = "https://openrouter.ai/api/v1"
OPENROUTER_API_PATH = "/chat/completions"

# =============================================================================
# Available Models - All Providers
# =============================================================================

AVAILABLE_MODELS: List[str] = [
    # TryBons AI / Claude
    "claude-opus-4-1-20250805",
    "claude-opus-4-5",
    "claude-opus-4-5-20251101",
    # NVIDIA
    "minimaxai/minimax-m2",
    "moonshotai/kimi-k2-instruct-0905",
    "mistralai/mistral-large-3-675b-instruct-2512",
    "deepseek-ai/deepseek-v3.1-terminus",
    # Bytez
    "openai/gpt-4.1",
    "openai/gpt-4o",
    "openai/gpt-5.1",
    "openai/gpt-5",
    # OpenRouter
    "deepseek/deepseek-v3.2-speciale",
    "moonshotai/kimi-k2:free",
]

NVIDIA_MODELS: List[str] = [
    "minimaxai/minimax-m2",
    "moonshotai/kimi-k2-instruct-0905",
    "mistralai/mistral-large-3-675b-instruct-2512",
    "deepseek-ai/deepseek-v3.1-terminus",
]

BYTEZ_MODELS: List[str] = [
    "openai/gpt-4.1",
    "openai/gpt-4o",
    "openai/gpt-5.1",
    "openai/gpt-5",
]

OPENROUTER_MODELS: List[str] = [
    "deepseek/deepseek-v3.2-speciale",
    "moonshotai/kimi-k2:free",
]

CLAUDE_MODELS: List[str] = [
    "claude-opus-4-1-20250805",
    "claude-opus-4-5",
    "claude-opus-4-5-20251101",
]

DEFAULT_MODEL = "claude-opus-4-5"


# =============================================================================
# Message Role Constants
# =============================================================================

class MessageRole(str, Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    FUNCTION = "function"
    TOOL = "tool"


# =============================================================================
# Agent Types
# =============================================================================

class AgentType(str, Enum):
    RESEARCHER = "researcher"
    CODER = "coder"
    WRITER = "writer"
    ANALYST = "analyst"
    PLANNER = "planner"
    CRITIC = "critic"
    GENERAL = "general"


# =============================================================================
# Reasoning Strategies
# =============================================================================

class ReasoningStrategy(str, Enum):
    CHAIN_OF_THOUGHT = "chain_of_thought"
    TREE_OF_THOUGHT = "tree_of_thought"
    REACT = "react"
    REFLEXION = "reflexion"
    SELF_CONSISTENCY = "self_consistency"


# =============================================================================
# Memory Types
# =============================================================================

class MemoryType(str, Enum):
    CONVERSATION_BUFFER = "conversation_buffer"
    SLIDING_WINDOW = "sliding_window"
    SUMMARY_BUFFER = "summary_buffer"
    EPISODIC = "episodic"
    SEMANTIC = "semantic"


# =============================================================================
# Vector Store Types
# =============================================================================

class VectorStoreType(str, Enum):
    CHROMADB = "chromadb"
    PINECONE = "pinecone"
    QDRANT = "qdrant"
    PGVECTOR = "pgvector"


# =============================================================================
# Tool Categories
# =============================================================================

class ToolCategory(str, Enum):
    WEB = "web"
    CODE = "code"
    FILE_SYSTEM = "file_system"
    DOCUMENTS = "documents"
    DATABASE = "database"
    API = "api"
    DATA_ANALYSIS = "data_analysis"
    NLP = "nlp"
    UTILITIES = "utilities"


# =============================================================================
# Task Status
# =============================================================================

class TaskStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


# =============================================================================
# Token Limits - All Providers
# =============================================================================

TOKEN_LIMITS: Dict[str, int] = {
    # Claude
    "claude-opus-4-1-20250805": 200000,
    "claude-opus-4-5": 200000,
    "claude-opus-4-5-20251101": 200000,
    # NVIDIA
    "minimaxai/minimax-m2": 128000,
    "moonshotai/kimi-k2-instruct-0905": 128000,
    "mistralai/mistral-large-3-675b-instruct-2512": 128000,
    "deepseek-ai/deepseek-v3.1-terminus": 128000,
    # Bytez
    "openai/gpt-4.1": 128000,
    "openai/gpt-4o": 128000,
    "openai/gpt-5.1": 128000,
    "openai/gpt-5": 128000,
    # OpenRouter
    "deepseek/deepseek-v3.2-speciale": 128000,
    "moonshotai/kimi-k2:free": 128000,
}

# =============================================================================
# Pricing (per 1K tokens in USD) - All Models
# =============================================================================

MODEL_PRICING: Dict[str, Dict[str, float]] = {
    # Claude
    "claude-opus-4-1-20250805": {"input": 0.015, "output": 0.075},
    "claude-opus-4-5": {"input": 0.015, "output": 0.075},
    "claude-opus-4-5-20251101": {"input": 0.015, "output": 0.075},
    # NVIDIA
    "minimaxai/minimax-m2": {"input": 0.001, "output": 0.002},
    "moonshotai/kimi-k2-instruct-0905": {"input": 0.001, "output": 0.002},
    "mistralai/mistral-large-3-675b-instruct-2512": {"input": 0.002, "output": 0.006},
    "deepseek-ai/deepseek-v3.1-terminus": {"input": 0.001, "output": 0.002},
    # Bytez
    "openai/gpt-4.1": {"input": 0.01, "output": 0.03},
    "openai/gpt-4o": {"input": 0.005, "output": 0.015},
    "openai/gpt-5.1": {"input": 0.02, "output": 0.06},
    "openai/gpt-5": {"input": 0.02, "output": 0.06},
    # OpenRouter
    "deepseek/deepseek-v3.2-speciale": {"input": 0.001, "output": 0.002},
    "moonshotai/kimi-k2:free": {"input": 0.0, "output": 0.0},
}

# =============================================================================
# Default Values
# =============================================================================

DEFAULT_TEMPERATURE = 0.7
DEFAULT_MAX_TOKENS = 49000
DEFAULT_TOP_P = 1.0
DEFAULT_FREQUENCY_PENALTY = 0.0
DEFAULT_PRESENCE_PENALTY = 0.0
DEFAULT_TIMEOUT = 1600

# =============================================================================
# System Messages
# =============================================================================

DEFAULT_SYSTEM_MESSAGE = """You are NEXUS, an advanced AI assistant powered by Claude.
You are helpful, harmless, and honest. You assist users with various tasks including:
- Answering questions and providing information
- Writing and editing content
- Code development and debugging
- Data analysis and research
- Problem-solving and planning

Always be clear, concise, and accurate in your responses."""

# =============================================================================
# File Extensions
# =============================================================================

SUPPORTED_CODE_EXTENSIONS: List[str] = [
    ".py", ".js", ".ts", ".jsx", ".tsx", ".java", ".cpp", ".c", ".h",
    ".cs", ".go", ".rs", ".rb", ".php", ".swift", ".kt", ".scala",
    ".html", ".css", ".scss", ".sql", ".sh", ".bash", ".ps1", ".yaml", ".yml"
]

SUPPORTED_DOCUMENT_EXTENSIONS: List[str] = [
    ".pdf", ".docx", ".doc", ".txt", ".md", ".csv", ".xlsx", ".xls",
    ".json", ".xml", ".rtf", ".odt"
]

SUPPORTED_IMAGE_EXTENSIONS: List[str] = [
    ".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp", ".svg"
]
