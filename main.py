#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║    ███╗   ██╗███████╗██╗  ██╗██╗   ██╗███████╗     █████╗ ██╗               ║
║    ████╗  ██║██╔════╝╚██╗██╔╝██║   ██║██╔════╝    ██╔══██╗██║               ║
║    ██╔██╗ ██║█████╗   ╚███╔╝ ██║   ██║███████╗    ███████║██║               ║
║    ██║╚██╗██║██╔══╝   ██╔██╗ ██║   ██║╚════██║    ██╔══██║██║               ║
║    ██║ ╚████║███████╗██╔╝ ╚██╗╚██████╔╝███████║    ██║  ██║██║               ║
║    ╚═╝  ╚═══╝╚══════╝╚═╝   ╚═╝ ╚═════╝ ╚══════╝    ╚═╝  ╚═╝╚═╝               ║
║                                                                              ║
║    NEXUS AI AGENT v2.0.0 - Professional Edition                              ║
║    Powered by TryBons AI (Claude Models)                                     ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import asyncio
import argparse
import sys
import os
import json
import shutil
from typing import Optional, Dict, Any, List
from datetime import datetime
from dataclasses import dataclass
import uuid

# Windows color support
if sys.platform == "win32":
    os.system("")
    try:
        import ctypes
        kernel32 = ctypes.windll.kernel32
        kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
    except:
        pass

# =============================================================================
# ALL MODULE IMPORTS - A2Z Integration
# =============================================================================

# Configuration
from config.settings import get_settings, Settings
from config.logging_config import setup_logging, get_logger
from config.constants import (
    # Models & Providers
    DEFAULT_MODEL, AVAILABLE_MODELS, API_BASE_URL, API_KEY,
    NVIDIA_API_KEY, NVIDIA_API_BASE_URL, NVIDIA_MODELS,
    BYTEZ_API_KEY, BYTEZ_API_BASE_URL, BYTEZ_MODELS,
    CLAUDE_MODELS, LLMProvider, NvidiaModels, BytezModels, ClaudeModels,
    # Agent & Task
    AgentType, ReasoningStrategy, TaskStatus, ToolCategory,
    MemoryType as ConstMemoryType, MessageRole, TOKEN_LIMITS,
    MODEL_PRICING, DEFAULT_TEMPERATURE, DEFAULT_MAX_TOKENS,
    DEFAULT_SYSTEM_MESSAGE, DEFAULT_TIMEOUT
)
from config.api_keys import APIKeyManager, api_key_manager
from config.model_config import ModelConfig, model_config

# LLM - All Providers
from llm import LLMClient, create_llm_client
from llm.providers import (
    AnthropicProvider,
    NvidiaProvider,
    BytezProvider,
    BaseLLMProvider,
    LLMResponse,
    GenerationConfig
)

# Core
from core.nexus_agent import NexusAgent, AgentConfig, AgentState, create_agent
from core.brain_engine import BrainEngine, BrainContext, ThoughtProcess
from core.context_engine import ContextEngine
from core.session_handler import SessionHandler
from core.execution_engine import ExecutionEngine
from core.response_generator import ResponseGenerator
from core.stream_processor import StreamProcessor
from core.callback_manager import CallbackManager

# Memory
from memory.memory_manager import MemoryManager, Memory, MemoryType
from memory.conversation_buffer import ConversationBuffer
from memory.sliding_window import SlidingWindowMemory
from memory.summary_buffer import SummaryBuffer

# Tools
from tools.tool_registry import ToolRegistry, tool_registry, tool, ToolDefinition
from tools.tool_executor import ToolExecutor
from tools.tool_selector import ToolSelector

# Reasoning
from reasoning.reasoning_orchestrator import ReasoningOrchestrator, ReasoningType, reasoning_orchestrator
from reasoning.chain_of_thought import ChainOfThought
from reasoning.tree_of_thought import TreeOfThought
from reasoning.react_strategy import ReActStrategy
from reasoning.reflexion_strategy import ReflexionStrategy

# Agents
from agents.base_agent import BaseAgent, SimpleAgent, AgentCapability, AgentOutput, AgentContext
from agents.agent_factory import AgentFactory

# Planning
from planning.task_planner import TaskPlanner
from planning.task_decomposer import TaskDecomposer
from planning.plan_executor import PlanExecutor

# Core - Additional
from core.reasoning_core import ReasoningCore
from core.decision_engine import DecisionEngine
from core.task_orchestrator import TaskOrchestrator

# Reasoning - Additional
from reasoning.self_consistency import SelfConsistency
from reasoning.thought_processor import ThoughtProcessor
from reasoning.fact_checker import FactChecker

# Planning - Additional
from planning.dependency_resolver import DependencyResolver
from planning.plan_validator import PlanValidator

# Memory - Additional
from memory.episodic_store import EpisodicStore
from memory.semantic_store import SemanticStore
from memory.memory_retriever import MemoryRetriever
from memory.memory_compressor import MemoryCompressor

# Memory - Vector Stores
from memory.vector_stores.base_vector_store import BaseVectorStore
from memory.vector_stores.chromadb_store import ChromaDBStore
from memory.vector_stores.pinecone_store import PineconeStore
from memory.vector_stores.qdrant_store import QdrantStore
from memory.vector_stores.pgvector_store import PGVectorStore

# Memory - Embeddings
from memory.embeddings.base_embedder import BaseEmbedder
from memory.embeddings.openai_embedder import OpenAIEmbedder
from memory.embeddings.cohere_embedder import CohereEmbedder
from memory.embeddings.local_embedder import LocalEmbedder

# Agents - Additional
from agents.multi_agent import MultiAgentSystem
from agents.specialized.researcher_agent import ResearcherAgent
from agents.specialized.coder_agent import CoderAgent
from agents.specialized.writer_agent import WriterAgent
from agents.specialized.analyst_agent import AnalystAgent

# Tools - Web
from tools.web.web_search import WebSearch as WebSearchTool
from tools.web.web_scraper import WebScraper as WebScraperTool
from tools.web.url_fetcher import URLFetcher as URLFetcherTool
from tools.web.google_search import GoogleSearch as GoogleSearchTool
from tools.web.tavily_search import TavilySearch as TavilySearchTool
from tools.web.content_extractor import ContentExtractor
from tools.web.browser_tool import BrowserTool

# Tools - Code
from tools.code.code_executor import CodeExecutor as CodeExecutorTool
from tools.code.code_analyzer import CodeAnalyzer as CodeAnalyzerTool
from tools.code.python_repl import PythonREPL as PythonREPLTool
from tools.code.code_formatter import CodeFormatter as CodeFormatterTool
from tools.code.git_tool import GitTool

# Tools - File System
from tools.file_system.file_reader import FileReader as FileReaderTool
from tools.file_system.file_writer import FileWriter as FileWriterTool
from tools.file_system.directory_tool import DirectoryTool
from tools.file_system.file_search import FileSearch as FileSearchTool

# Tools - Documents
from tools.documents.pdf_reader import PDFReader as PDFReaderTool
from tools.documents.csv_tool import CSVTool
from tools.documents.docx_reader import DocxReader as DocxReaderTool
from tools.documents.excel_tool import ExcelTool
from tools.documents.markdown_tool import MarkdownTool

# Tools - Database
from tools.database.sql_executor import SQLExecutor as SQLExecutorTool
from tools.database.database_connector import DatabaseConnector
from tools.database.query_builder import QueryBuilder

# Tools - API
from tools.api_clients.rest_client import RESTClient
from tools.api_clients.graphql_client import GraphQLClient
from tools.api_clients.websocket_client import WebSocketClient

# Tools - Data Analysis
from tools.data_analysis.data_analyzer import DataAnalyzer
from tools.data_analysis.statistics_tool import StatisticsTool
from tools.data_analysis.visualization_tool import VisualizationTool

# Tools - NLP
from tools.nlp.text_processor import TextProcessor
from tools.nlp.summarizer import Summarizer
from tools.nlp.sentiment_analyzer import SentimentAnalyzer
from tools.nlp.entity_extractor import EntityExtractor

# Tools - Utilities
from tools.utilities.calculator import Calculator as CalculatorTool
from tools.utilities.datetime_tool import DateTimeTool
from tools.utilities.json_tool import JSONTool
from tools.utilities.converter import Converter as ConverterTool
from tools.utilities.regex_tool import RegexTool

# Tools - Additional
from tools.custom_tool_builder import CustomToolBuilder

# Prompts
from prompts.prompt_manager import PromptManager
from prompts.prompt_builder import PromptBuilder
from prompts.prompt_template import PromptTemplate
from prompts.few_shot_selector import FewShotSelector
from prompts.dynamic_prompt import DynamicPrompt

# Prompts - System Prompts (all from __init__.py)
from prompts.system_prompts import (
    DEFAULT_SYSTEM_PROMPT,
    CODER_SYSTEM_PROMPT,
    RESEARCHER_SYSTEM_PROMPT,
    ANALYST_SYSTEM_PROMPT,
    ASSISTANT_SYSTEM_PROMPT,
    PYTHON_CODER, JAVASCRIPT_CODER, FULLSTACK_CODER,
    ACADEMIC_RESEARCHER, MARKET_RESEARCHER, TECHNICAL_RESEARCHER,
    DATA_ANALYST, BUSINESS_ANALYST, FINANCIAL_ANALYST,
    GENERAL_ASSISTANT, WRITING_ASSISTANT, PLANNING_ASSISTANT,
    get_system_prompt, get_combined_prompt
)
# Direct system prompt pass-through (no wrappers)
# System prompt from base_system_prompts.py goes directly to model

# RAG
from rag.rag_pipeline import RAGPipeline
from rag.document_loader import DocumentLoader
from rag.text_splitter import TextSplitter
from rag.retriever import Retriever

# Pipelines
from pipelines.base_pipeline import BasePipeline
from pipelines.data_pipeline import DataPipeline
from pipelines.agent_pipeline import AgentPipeline

# Exceptions
from exceptions.base_exceptions import NexusException
from exceptions.agent_exceptions import AgentException
from exceptions.llm_exceptions import LLMException

# Types
from nexus_types.common_types import Message, ToolCall, ToolResult, FunctionSchema, GenerationConfig as GenConfig
from nexus_types.agent_types import TaskStatus as NexusTaskStatus, AgentStatus, AgentState as NexusAgentState, ExecutionResult

# Utils
from utils.helpers import generate_id, truncate_text, retry_async, deep_merge
from utils.validators import validate_url, validate_json, validate_api_key

# Logger
logger = get_logger(__name__)


# =============================================================================
# PROFESSIONAL THEME - Claude CLI Style
# =============================================================================

class S:
    """Professional CLI Styling - Claude CLI Inspired"""

    # Reset
    RESET = "\033[0m"

    # Text Styles
    BOLD = "\033[1m"
    DIM = "\033[2m"
    ITALIC = "\033[3m"
    UNDERLINE = "\033[4m"

    # Standard Colors
    BLACK = "\033[30m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"

    # Bright Colors
    BRIGHT_BLACK = "\033[90m"
    BRIGHT_RED = "\033[91m"
    BRIGHT_GREEN = "\033[92m"
    BRIGHT_YELLOW = "\033[93m"
    BRIGHT_BLUE = "\033[94m"
    BRIGHT_MAGENTA = "\033[95m"
    BRIGHT_CYAN = "\033[96m"
    BRIGHT_WHITE = "\033[97m"

    # 256 Colors - Professional Theme
    PRIMARY = "\033[38;5;75m"       # Sky Blue
    SECONDARY = "\033[38;5;183m"    # Light Purple
    ACCENT = "\033[38;5;216m"       # Peach
    SUCCESS = "\033[38;5;114m"      # Soft Green
    WARNING = "\033[38;5;221m"      # Gold
    ERROR = "\033[38;5;203m"        # Coral Red
    INFO = "\033[38;5;117m"         # Light Blue
    MUTED = "\033[38;5;246m"        # Gray
    HIGHLIGHT = "\033[38;5;229m"    # Light Yellow
    ORANGE = "\033[38;5;208m"       # Orange


# =============================================================================
# TERMINAL UTILITIES
# =============================================================================

def get_terminal_width():
    """Get terminal width"""
    try:
        return shutil.get_terminal_size().columns
    except:
        return 80


def clear_screen():
    """Clear the terminal"""
    os.system('cls' if os.name == 'nt' else 'clear')


# =============================================================================
# CLAUDE CLI STYLE INPUT BOX
# =============================================================================

class InputBox:
    """Claude CLI Style Input Box - Ultra Professional 3D Edition

    Supports multiline paste - keeps collecting input until:
    - Empty line + Enter (for pasted content with newlines)
    - Or just Enter on single line input
    """

    def __init__(self, width: int = 70):
        self.width = min(width, get_terminal_width() - 4)

    def _check_stdin_has_data(self) -> bool:
        """Check if stdin has pending data (for paste detection)"""
        try:
            import msvcrt
            return msvcrt.kbhit()
        except ImportError:
            # Non-Windows fallback
            import select
            return select.select([sys.stdin], [], [], 0)[0] != []
        except:
            return False

    def get_input(self, prompt_label: str = "You") -> str:
        """Get user input with 3D professional style box

        Handles paste properly - collects all pasted lines until user presses Enter on empty line
        """
        inner_width = self.width - 4

        # 3D shadow effect header
        print(f"\n{S.MUTED}  {'▄' * (self.width - 2)}{S.RESET}")
        print(f"{S.PRIMARY}╭─{S.RESET} {S.BOLD}{S.BRIGHT_CYAN}▶ {prompt_label}{S.RESET} {S.PRIMARY}{'─' * (inner_width - len(prompt_label) - 4)}╮{S.MUTED}▌{S.RESET}")
        print(f"{S.PRIMARY}│{S.RESET} {S.DIM}(Paste multiline, press Enter twice to send){S.RESET}")
        print(f"{S.PRIMARY}│{S.RESET}{' ' * (self.width - 3)}{S.PRIMARY}│{S.MUTED}▌{S.RESET}")

        # Input line with cursor indicator
        print(f"{S.PRIMARY}│{S.RESET} {S.BRIGHT_WHITE}", end="", flush=True)

        lines = []
        empty_count = 0

        try:
            while True:
                line = input()

                if line == "":
                    empty_count += 1
                    # If first line is empty or two consecutive empty lines, stop
                    if len(lines) == 0 or empty_count >= 2:
                        break
                    lines.append("")
                else:
                    empty_count = 0
                    lines.append(line)

                    # Check if more data is pending (paste operation)
                    if not self._check_stdin_has_data():
                        # No more data pending - if single line, send immediately
                        if len(lines) == 1:
                            break

                # Show continuation prompt for next line
                print(f"{S.PRIMARY}│{S.RESET} {S.BRIGHT_WHITE}", end="", flush=True)

        except EOFError:
            if not lines:
                return "/exit"

        print(f"{S.RESET}", end="")

        # Bottom border with 3D effect
        print(f"{S.PRIMARY}│{S.RESET}{' ' * (self.width - 3)}{S.PRIMARY}│{S.MUTED}▌{S.RESET}")
        print(f"{S.PRIMARY}╰{'─' * (self.width - 2)}╯{S.MUTED}▌{S.RESET}")
        print(f"{S.MUTED}  {'▀' * (self.width - 2)}▘{S.RESET}")

        return "\n".join(lines).strip()

    def get_multiline_input(self, prompt_label: str = "You") -> str:
        """Get multiline input with 3D professional style (press Enter twice to submit)"""
        # Now same as get_input since it handles multiline
        return self.get_input(prompt_label)


# =============================================================================
# RESPONSE BOX
# =============================================================================

class ResponseStream:
    """Simple streaming response display - No box, just clean text with filtering"""

    # Patterns to filter from API responses
    FILTER_PATTERNS = [
        "🌱 `@bonsai:",
        "@bonsai:",
        "routing to stealth",
        "(free premium model)",
        "routing to",
    ]

    def __init__(self):
        self.buffer = ""
        self.filter_active = True
        self.started = False

    def _should_filter(self, text: str) -> bool:
        """Check if text contains filter patterns"""
        for pattern in self.FILTER_PATTERNS:
            if pattern.lower() in text.lower():
                return True
        return False

    def _clean_text(self, text: str) -> str:
        """Remove routing messages from text"""
        import re
        patterns_to_remove = [
            r'🌱\s*`@bonsai:[^`]*`\.?',
            r'🌱\s*@bonsai:[^.]*\.?\s*',
            r'`@bonsai:[^`]*`\.?\s*',
            r'@bonsai:[^.]*\.?\s*',
        ]

        result = text
        for pattern in patterns_to_remove:
            result = re.sub(pattern, '', result, flags=re.IGNORECASE)

        return result.lstrip()

    def start(self, label: str = "NEXUS"):
        """Start response - just print label"""
        print(f"\n{S.SUCCESS}{S.BOLD}◆ {label}:{S.RESET} ", end="", flush=True)
        self.started = True
        self.buffer = ""
        self.filter_active = True

    def write(self, text: str):
        """Write text with filtering"""
        if not self.started:
            self.start()

        if self.filter_active:
            self.buffer += text

            if len(self.buffer) > 100 or (len(self.buffer) > 20 and not self._should_filter(self.buffer[:50])):
                clean_text = self._clean_text(self.buffer)
                self.buffer = ""
                self.filter_active = False
                print(f"{S.BRIGHT_WHITE}{clean_text}{S.RESET}", end="", flush=True)
        else:
            print(f"{S.BRIGHT_WHITE}{text}{S.RESET}", end="", flush=True)

    def flush_buffer(self):
        """Flush any remaining buffer"""
        if self.buffer:
            clean_text = self._clean_text(self.buffer)
            self.buffer = ""
            print(f"{S.BRIGHT_WHITE}{clean_text}{S.RESET}", end="", flush=True)

    def end(self):
        """End response"""
        if self.started:
            self.flush_buffer()
            print("\n")
            self.started = False


# Alias for compatibility
ResponseBox = ResponseStream


# =============================================================================
# PROFESSIONAL BANNER
# =============================================================================

def print_banner():
    """Print ultra professional 3D startup banner"""

    # 3D effect shadow characters
    shadow = f"{S.MUTED}"

    logo = f"""
{shadow}    ▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄{S.RESET}
{S.PRIMARY}{S.BOLD}    ███╗   ██╗███████╗██╗  ██╗██╗   ██╗███████╗{S.RESET}{shadow}▌{S.RESET}
{S.BRIGHT_CYAN}{S.BOLD}    ████╗  ██║██╔════╝╚██╗██╔╝██║   ██║██╔════╝{S.RESET}{shadow}▌{S.RESET}
{S.PRIMARY}{S.BOLD}    ██╔██╗ ██║█████╗   ╚███╔╝ ██║   ██║███████╗{S.RESET}{shadow}▌{S.RESET}
{S.BRIGHT_CYAN}{S.BOLD}    ██║╚██╗██║██╔══╝   ██╔██╗ ██║   ██║╚════██║{S.RESET}{shadow}▌{S.RESET}
{S.PRIMARY}{S.BOLD}    ██║ ╚████║███████╗██╔╝ ╚██╗╚██████╔╝███████║{S.RESET}{shadow}▌{S.RESET}
{S.BRIGHT_CYAN}{S.BOLD}    ╚═╝  ╚═══╝╚══════╝╚═╝   ╚═╝ ╚═════╝ ╚══════╝{S.RESET}{shadow}▌{S.RESET}
{shadow}    ▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▘{S.RESET}
"""

    print(logo)

    # Professional info box with 3D effect
    print(f"{S.MUTED}    ▄{'▄' * 56}{S.RESET}")
    print(f"  {S.SECONDARY}╭{'─' * 56}╮{S.MUTED}▌{S.RESET}")
    print(f"  {S.SECONDARY}│{S.RESET}    {S.BRIGHT_WHITE}{S.BOLD}◆ NEXUS AI Agent{S.RESET} {S.MUTED}v2.0.0 Professional Edition{S.RESET}       {S.SECONDARY}│{S.MUTED}▌{S.RESET}")
    print(f"  {S.SECONDARY}│{S.RESET}    {S.PRIMARY}◈ Powered by TryBons AI{S.RESET} {S.MUTED}(Claude Models){S.RESET}             {S.SECONDARY}│{S.MUTED}▌{S.RESET}")
    print(f"  {S.SECONDARY}│{S.RESET}                                                        {S.SECONDARY}│{S.MUTED}▌{S.RESET}")
    print(f"  {S.SECONDARY}│{S.RESET}    {S.SUCCESS}●{S.RESET} Max Tokens: {S.ORANGE}{DEFAULT_MAX_TOKENS:,}{S.RESET}                              {S.SECONDARY}│{S.MUTED}▌{S.RESET}")
    print(f"  {S.SECONDARY}│{S.RESET}    {S.INFO}●{S.RESET} Timeout:    {S.ORANGE}{DEFAULT_TIMEOUT}s{S.RESET}                                 {S.SECONDARY}│{S.MUTED}▌{S.RESET}")
    print(f"  {S.SECONDARY}╰{'─' * 56}╯{S.MUTED}▌{S.RESET}")
    print(f"{S.MUTED}    ▀{'▀' * 56}▘{S.RESET}")
    print()


# =============================================================================
# STATUS & INFO BOXES
# =============================================================================

def print_status_box(model: str, session_id: str):
    """Print status in a 3D box"""
    now = datetime.now().strftime("%H:%M:%S")
    short_session = session_id[:8]

    print(f"""
{S.MUTED}  ▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄{S.RESET}
{S.INFO}╭{'─' * 60}╮{S.MUTED}▌{S.RESET}
{S.INFO}│{S.RESET}  {S.SUCCESS}◆{S.RESET} {S.BOLD}Status:{S.RESET} {S.BRIGHT_GREEN}Online{S.RESET}          {S.INFO}│{S.RESET}  {S.INFO}◈{S.RESET} {S.BOLD}Time:{S.RESET} {S.BRIGHT_WHITE}{now}{S.RESET}          {S.INFO}│{S.MUTED}▌{S.RESET}
{S.INFO}│{S.RESET}  {S.PRIMARY}◆{S.RESET} {S.BOLD}Model:{S.RESET}  {S.BRIGHT_CYAN}{model:<15}{S.RESET} {S.INFO}│{S.RESET}  {S.WARNING}◈{S.RESET} {S.BOLD}Session:{S.RESET} {S.ORANGE}{short_session}{S.RESET}     {S.INFO}│{S.MUTED}▌{S.RESET}
{S.INFO}╰{'─' * 60}╯{S.MUTED}▌{S.RESET}
{S.MUTED}  ▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▘{S.RESET}
""")


def print_help_box():
    """Print help in a 3D box"""
    print(f"""
{S.MUTED}  ▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄{S.RESET}
{S.WARNING}╭{'─' * 60}╮{S.MUTED}▌{S.RESET}
{S.WARNING}│{S.RESET}  {S.BOLD}{S.BRIGHT_YELLOW}⌘ COMMANDS{S.RESET}                                                 {S.WARNING}│{S.MUTED}▌{S.RESET}
{S.WARNING}├{'─' * 60}┤{S.MUTED}▌{S.RESET}
{S.WARNING}│{S.RESET}                                                            {S.WARNING}│{S.MUTED}▌{S.RESET}
{S.WARNING}│{S.RESET}  {S.BRIGHT_CYAN}/help{S.RESET}        Show this help message                     {S.WARNING}│{S.MUTED}▌{S.RESET}
{S.WARNING}│{S.RESET}  {S.BRIGHT_CYAN}/model{S.RESET}       Change model (e.g., /model claude-opus-4-5){S.WARNING}│{S.MUTED}▌{S.RESET}
{S.WARNING}│{S.RESET}  {S.BRIGHT_CYAN}/models{S.RESET}      List available models                      {S.WARNING}│{S.MUTED}▌{S.RESET}
{S.WARNING}│{S.RESET}  {S.BRIGHT_CYAN}/prompt{S.RESET}      Change system prompt (default/coder/        {S.WARNING}│{S.MUTED}▌{S.RESET}
{S.WARNING}│{S.RESET}               researcher/analyst/python/javascript/        {S.WARNING}│{S.MUTED}▌{S.RESET}
{S.WARNING}│{S.RESET}               academic/data/writing/planning...)           {S.WARNING}│{S.MUTED}▌{S.RESET}
{S.WARNING}│{S.RESET}  {S.BRIGHT_CYAN}/status{S.RESET}      Show current status                        {S.WARNING}│{S.MUTED}▌{S.RESET}
{S.WARNING}│{S.RESET}  {S.BRIGHT_CYAN}/memory{S.RESET}      Show memory statistics                     {S.WARNING}│{S.MUTED}▌{S.RESET}
{S.WARNING}│{S.RESET}  {S.BRIGHT_CYAN}/tools{S.RESET}       List available tools                       {S.WARNING}│{S.MUTED}▌{S.RESET}
{S.WARNING}│{S.RESET}  {S.BRIGHT_CYAN}/clear{S.RESET}       Clear conversation history                 {S.WARNING}│{S.MUTED}▌{S.RESET}
{S.WARNING}│{S.RESET}  {S.BRIGHT_CYAN}/reset{S.RESET}       Reset entire session                       {S.WARNING}│{S.MUTED}▌{S.RESET}
{S.WARNING}│{S.RESET}  {S.BRIGHT_CYAN}/export{S.RESET}      Export conversation to JSON                {S.WARNING}│{S.MUTED}▌{S.RESET}
{S.WARNING}│{S.RESET}  {S.BRIGHT_RED}/exit{S.RESET}        Exit the application                       {S.WARNING}│{S.MUTED}▌{S.RESET}
{S.WARNING}│{S.RESET}                                                            {S.WARNING}│{S.MUTED}▌{S.RESET}
{S.WARNING}╰{'─' * 60}╯{S.MUTED}▌{S.RESET}
{S.MUTED}  ▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▘{S.RESET}
""")


def print_models_box():
    """Print models in a 3D box"""
    print(f"\n{S.MUTED}  ▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄{S.RESET}")
    print(f"{S.INFO}╭{'─' * 60}╮{S.MUTED}▌{S.RESET}")
    print(f"{S.INFO}│{S.RESET}  {S.BOLD}{S.BRIGHT_BLUE}◈ AVAILABLE MODELS{S.RESET}                                         {S.INFO}│{S.MUTED}▌{S.RESET}")
    print(f"{S.INFO}├{'─' * 60}┤{S.MUTED}▌{S.RESET}")

    for model in AVAILABLE_MODELS:
        if model == DEFAULT_MODEL:
            print(f"{S.INFO}│{S.RESET}  {S.SUCCESS}◆{S.RESET} {S.BRIGHT_CYAN}{model}{S.RESET} {S.BRIGHT_GREEN}(default){S.RESET}                   {S.INFO}│{S.MUTED}▌{S.RESET}")
        else:
            print(f"{S.INFO}│{S.RESET}  {S.MUTED}○{S.RESET} {S.WHITE}{model}{S.RESET}                            {S.INFO}│{S.MUTED}▌{S.RESET}")

    print(f"{S.INFO}╰{'─' * 60}╯{S.MUTED}▌{S.RESET}")
    print(f"{S.MUTED}  ▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▘{S.RESET}\n")


def print_metrics_box(metrics: Dict[str, Any]):
    """Print metrics in a 3D box"""
    print(f"""
{S.MUTED}  ▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄{S.RESET}
{S.ORANGE}╭{'─' * 60}╮{S.MUTED}▌{S.RESET}
{S.ORANGE}│{S.RESET}  {S.BOLD}{S.BRIGHT_YELLOW}◈ USAGE METRICS{S.RESET}                                            {S.ORANGE}│{S.MUTED}▌{S.RESET}
{S.ORANGE}├{'─' * 60}┤{S.MUTED}▌{S.RESET}
{S.ORANGE}│{S.RESET}  {S.BRIGHT_WHITE}Total Requests:{S.RESET}     {S.BRIGHT_CYAN}{metrics.get('total_requests', 0):>8}{S.RESET}                        {S.ORANGE}│{S.MUTED}▌{S.RESET}
{S.ORANGE}│{S.RESET}  {S.BRIGHT_WHITE}Total Tokens:{S.RESET}       {S.BRIGHT_CYAN}{metrics.get('total_tokens', 0):>8}{S.RESET}                        {S.ORANGE}│{S.MUTED}▌{S.RESET}
{S.ORANGE}│{S.RESET}  {S.BRIGHT_WHITE}Estimated Cost:{S.RESET}     {S.BRIGHT_GREEN}${metrics.get('total_cost', 0):>8.4f}{S.RESET}                      {S.ORANGE}│{S.MUTED}▌{S.RESET}
{S.ORANGE}╰{'─' * 60}╯{S.MUTED}▌{S.RESET}
{S.MUTED}  ▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▘{S.RESET}
""")


def print_memory_box(stats: Dict[str, Any]):
    """Print memory stats in a 3D box"""
    print(f"""
{S.MUTED}  ▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄{S.RESET}
{S.SECONDARY}╭{'─' * 60}╮{S.MUTED}▌{S.RESET}
{S.SECONDARY}│{S.RESET}  {S.BOLD}{S.BRIGHT_MAGENTA}◈ MEMORY STATUS{S.RESET}                                            {S.SECONDARY}│{S.MUTED}▌{S.RESET}
{S.SECONDARY}├{'─' * 60}┤{S.MUTED}▌{S.RESET}
{S.SECONDARY}│{S.RESET}  {S.BRIGHT_WHITE}Short-term:{S.RESET}   {S.BRIGHT_CYAN}{stats.get('short_term_count', 0):>6}{S.RESET} items                          {S.SECONDARY}│{S.MUTED}▌{S.RESET}
{S.SECONDARY}│{S.RESET}  {S.BRIGHT_WHITE}Long-term:{S.RESET}    {S.BRIGHT_CYAN}{stats.get('long_term_count', 0):>6}{S.RESET} items                          {S.SECONDARY}│{S.MUTED}▌{S.RESET}
{S.SECONDARY}│{S.RESET}  {S.BRIGHT_WHITE}Working:{S.RESET}      {S.BRIGHT_CYAN}{stats.get('working_count', 0):>6}{S.RESET} items                          {S.SECONDARY}│{S.MUTED}▌{S.RESET}
{S.SECONDARY}│{S.RESET}  {S.BRIGHT_WHITE}Total:{S.RESET}        {S.BRIGHT_GREEN}{stats.get('total', 0):>6}{S.RESET} items                          {S.SECONDARY}│{S.MUTED}▌{S.RESET}
{S.SECONDARY}╰{'─' * 60}╯{S.MUTED}▌{S.RESET}
{S.MUTED}  ▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▘{S.RESET}
""")


def print_tools_box(tools: List):
    """Print tools in a 3D box"""
    print(f"\n{S.MUTED}  ▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄{S.RESET}")
    print(f"{S.SUCCESS}╭{'─' * 60}╮{S.MUTED}▌{S.RESET}")
    print(f"{S.SUCCESS}│{S.RESET}  {S.BOLD}{S.BRIGHT_GREEN}◈ AVAILABLE TOOLS{S.RESET}                                          {S.SUCCESS}│{S.MUTED}▌{S.RESET}")
    print(f"{S.SUCCESS}├{'─' * 60}┤{S.MUTED}▌{S.RESET}")

    if tools:
        for t in tools:
            name = getattr(t, 'name', str(t))
            desc = getattr(t, 'description', '')[:33]
            print(f"{S.SUCCESS}│{S.RESET}  {S.PRIMARY}◆{S.RESET} {S.BRIGHT_WHITE}{name:<15}{S.RESET} {S.MUTED}{desc}{S.RESET}        {S.SUCCESS}│{S.MUTED}▌{S.RESET}")
    else:
        print(f"{S.SUCCESS}│{S.RESET}  {S.MUTED}No tools registered{S.RESET}                                     {S.SUCCESS}│{S.MUTED}▌{S.RESET}")

    print(f"{S.SUCCESS}╰{'─' * 60}╯{S.MUTED}▌{S.RESET}")
    print(f"{S.MUTED}  ▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▘{S.RESET}\n")


# =============================================================================
# MESSAGE FUNCTIONS
# =============================================================================

def print_error(message: str):
    """Print error message with 3D styling"""
    print(f"\n{S.MUTED}  ▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄{S.RESET}")
    print(f"{S.ERROR}╭─{S.RESET} {S.BOLD}{S.BRIGHT_RED}✖ ERROR{S.RESET} {S.ERROR}{'─' * 48}╮{S.MUTED}▌{S.RESET}")
    print(f"{S.ERROR}│{S.RESET} {S.BRIGHT_RED}{message}{S.RESET}")
    print(f"{S.ERROR}╰{'─' * 58}╯{S.MUTED}▌{S.RESET}")
    print(f"{S.MUTED}  ▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▘{S.RESET}\n")


def print_success(message: str):
    """Print success message"""
    print(f"\n{S.SUCCESS}◆{S.RESET} {S.BRIGHT_GREEN}{message}{S.RESET}\n")


def print_info(message: str):
    """Print info message"""
    print(f"\n{S.INFO}◈{S.RESET} {S.BRIGHT_CYAN}{message}{S.RESET}\n")


def print_thinking():
    """Print thinking indicator"""
    print(f"\n{S.MUTED}◌ Processing...{S.RESET}", end="", flush=True)


def clear_thinking():
    """Clear thinking indicator"""
    print(f"\r{' ' * 20}\r", end="", flush=True)


def print_goodbye():
    """Print goodbye message with 3D styling"""
    print(f"""
{S.MUTED}  ▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄{S.RESET}
{S.PRIMARY}╭{'─' * 60}╮{S.MUTED}▌{S.RESET}
{S.PRIMARY}│{S.RESET}                                                            {S.PRIMARY}│{S.MUTED}▌{S.RESET}
{S.PRIMARY}│{S.RESET}   {S.BOLD}{S.BRIGHT_CYAN}◆ Thank you for using NEXUS AI Agent!{S.RESET}                   {S.PRIMARY}│{S.MUTED}▌{S.RESET}
{S.PRIMARY}│{S.RESET}   {S.MUTED}◈ Powered by TryBons AI{S.RESET}                                  {S.PRIMARY}│{S.MUTED}▌{S.RESET}
{S.PRIMARY}│{S.RESET}                                                            {S.PRIMARY}│{S.MUTED}▌{S.RESET}
{S.PRIMARY}│{S.RESET}   {S.BRIGHT_GREEN}◆ Session ended successfully{S.RESET}                          {S.PRIMARY}│{S.MUTED}▌{S.RESET}
{S.PRIMARY}│{S.RESET}                                                            {S.PRIMARY}│{S.MUTED}▌{S.RESET}
{S.PRIMARY}╰{'─' * 60}╯{S.MUTED}▌{S.RESET}
{S.MUTED}  ▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▘{S.RESET}
""")


# =============================================================================
# SESSION CONFIGURATION
# =============================================================================

@dataclass
class SessionConfig:
    """Session configuration"""
    model: str = DEFAULT_MODEL
    temperature: float = DEFAULT_TEMPERATURE
    max_tokens: int = DEFAULT_MAX_TOKENS
    timeout: int = DEFAULT_TIMEOUT
    streaming: bool = True
    enable_memory: bool = True
    verbose: bool = False


# =============================================================================
# MAIN APPLICATION CLASS
# =============================================================================

class NexusApp:
    """NEXUS AI Application - Professional Edition"""

    VERSION = "2.0.0"

    def __init__(self, config: Optional[SessionConfig] = None):
        self.config = config or SessionConfig()
        self.session_id = str(uuid.uuid4())
        self.start_time = datetime.now()

        # Core Components
        self.settings: Settings = get_settings()
        self.llm_client: Optional[LLMClient] = None
        self.memory_manager: MemoryManager = MemoryManager()
        self.tool_registry: ToolRegistry = tool_registry
        self.reasoning: ReasoningOrchestrator = reasoning_orchestrator

        # System Prompt - Using DEFAULT_SYSTEM_PROMPT from base_system_prompts.py
        # Model MUST follow this behavior - No default model behavior allowed
        self.system_prompt: str = DEFAULT_SYSTEM_PROMPT

        # Session State
        self.conversation_history: List[Dict[str, str]] = []
        self.running: bool = False
        self.initialized: bool = False
        self.message_count = 0

    async def initialize(self) -> None:
        """Initialize all components"""
        if self.initialized:
            return

        self.llm_client = LLMClient(
            model=self.config.model,
            api_key=API_KEY,
            base_url=API_BASE_URL
        )
        await self.llm_client.initialize()

        self._register_tools()
        self.initialized = True
        logger.info(f"NEXUS initialized - Session: {self.session_id}")

    def _register_tools(self):
        """Register utility tools"""
        @tool(name="datetime", description="Get current date and time", category="utilities")
        def get_datetime() -> str:
            return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        @tool(name="calculate", description="Calculate math expression", category="utilities")
        def calculate(expr: str) -> str:
            try:
                allowed = set('0123456789+-*/.() ')
                if all(c in allowed for c in expr):
                    return str(eval(expr))
                return "Invalid expression"
            except:
                return "Calculation error"

    async def chat_stream(self, message: str):
        """Send message and stream response"""
        self.conversation_history.append({
            "role": "user",
            "content": message
        })

        if self.config.enable_memory:
            self.memory_manager.add(
                message,
                MemoryType.SHORT_TERM,
                metadata={"role": "user"}
            )

        self.message_count += 1
        full_response = ""

        try:
            # Pass system prompt to the model
            async for chunk in self.llm_client.generate_stream(
                messages=self.conversation_history,
                model=self.config.model,
                system=self.system_prompt,  # System prompt connected here!
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens
            ):
                if chunk is not None:
                    full_response += chunk
                    yield chunk

            self.conversation_history.append({
                "role": "assistant",
                "content": full_response
            })

            if self.config.enable_memory:
                self.memory_manager.add(
                    full_response,
                    MemoryType.SHORT_TERM,
                    metadata={"role": "assistant"}
                )

        except Exception as e:
            logger.error(f"Chat error: {e}")
            raise

    async def set_model(self, model: str) -> bool:
        """Change model and switch provider if needed"""
        if model in AVAILABLE_MODELS:
            self.config.model = model
            if self.llm_client:
                await self.llm_client.set_model(model)
            return True
        return False

    def set_system_prompt(self, prompt_type: str = "default") -> bool:
        """
        Change system prompt based on type - Direct connection, no filtering

        Available types:
        - default: DEFAULT_SYSTEM_PROMPT
        - coder: CODER_SYSTEM_PROMPT
        - researcher: RESEARCHER_SYSTEM_PROMPT
        - analyst: ANALYST_SYSTEM_PROMPT
        - assistant: ASSISTANT_SYSTEM_PROMPT
        - python_coder: PYTHON_CODER
        - javascript_coder: JAVASCRIPT_CODER
        - fullstack_coder: FULLSTACK_CODER
        - academic_researcher: ACADEMIC_RESEARCHER
        - market_researcher: MARKET_RESEARCHER
        - technical_researcher: TECHNICAL_RESEARCHER
        - data_analyst: DATA_ANALYST
        - business_analyst: BUSINESS_ANALYST
        - financial_analyst: FINANCIAL_ANALYST
        - general_assistant: GENERAL_ASSISTANT
        - writing_assistant: WRITING_ASSISTANT
        - planning_assistant: PLANNING_ASSISTANT
        """
        prompts = {
            # Base prompts - DEFAULT_SYSTEM_PROMPT from base_system_prompts.py
            "default": DEFAULT_SYSTEM_PROMPT,
            "coder": CODER_SYSTEM_PROMPT,
            "researcher": RESEARCHER_SYSTEM_PROMPT,
            "analyst": ANALYST_SYSTEM_PROMPT,
            "assistant": ASSISTANT_SYSTEM_PROMPT,
            # Specialized coder prompts
            "python_coder": PYTHON_CODER,
            "python": PYTHON_CODER,
            "javascript_coder": JAVASCRIPT_CODER,
            "javascript": JAVASCRIPT_CODER,
            "js": JAVASCRIPT_CODER,
            "fullstack_coder": FULLSTACK_CODER,
            "fullstack": FULLSTACK_CODER,
            # Specialized researcher prompts
            "academic_researcher": ACADEMIC_RESEARCHER,
            "academic": ACADEMIC_RESEARCHER,
            "market_researcher": MARKET_RESEARCHER,
            "market": MARKET_RESEARCHER,
            "technical_researcher": TECHNICAL_RESEARCHER,
            "technical": TECHNICAL_RESEARCHER,
            # Specialized analyst prompts
            "data_analyst": DATA_ANALYST,
            "data": DATA_ANALYST,
            "business_analyst": BUSINESS_ANALYST,
            "business": BUSINESS_ANALYST,
            "financial_analyst": FINANCIAL_ANALYST,
            "financial": FINANCIAL_ANALYST,
            # Specialized assistant prompts
            "general_assistant": GENERAL_ASSISTANT,
            "general": GENERAL_ASSISTANT,
            "writing_assistant": WRITING_ASSISTANT,
            "writing": WRITING_ASSISTANT,
            "writer": WRITING_ASSISTANT,
            "planning_assistant": PLANNING_ASSISTANT,
            "planning": PLANNING_ASSISTANT,
            "planner": PLANNING_ASSISTANT,
        }

        if prompt_type.lower() in prompts:
            self.system_prompt = prompts[prompt_type.lower()]
            logger.info(f"System prompt changed to: {prompt_type}")
            return True
        return False

    def set_custom_system_prompt(self, prompt: str) -> None:
        """Set a custom system prompt"""
        self.system_prompt = prompt
        logger.info("Custom system prompt set")

    def clear_history(self):
        """Clear conversation history"""
        self.conversation_history = []
        self.memory_manager.clear(MemoryType.SHORT_TERM)
        self.message_count = 0

    def reset_session(self):
        """Reset entire session"""
        self.clear_history()
        self.memory_manager.clear()
        self.session_id = str(uuid.uuid4())
        self.start_time = datetime.now()

    def get_metrics(self) -> Dict[str, Any]:
        """Get metrics"""
        llm_metrics = self.llm_client.get_metrics() if self.llm_client else {}
        return {"messages": self.message_count, **llm_metrics}

    def get_memory_stats(self) -> Dict[str, Any]:
        """Get memory stats"""
        return self.memory_manager.get_stats()

    def export_conversation(self, filename: str = None) -> str:
        """Export conversation"""
        if not filename:
            filename = f"nexus_chat_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        data = {
            "session_id": self.session_id,
            "timestamp": datetime.now().isoformat(),
            "model": self.config.model,
            "messages": self.conversation_history,
            "metrics": self.get_metrics()
        }

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        return filename

    async def close(self):
        """Cleanup"""
        if self.llm_client:
            await self.llm_client.close()
        self.initialized = False


# =============================================================================
# INTERACTIVE MODE
# =============================================================================

async def run_interactive(model: str = DEFAULT_MODEL, verbose: bool = False):
    """Run interactive session with Claude CLI style boxes"""

    clear_screen()
    print_banner()

    config = SessionConfig(model=model, verbose=verbose)
    app = NexusApp(config)

    # Create input box and response stream
    input_box = InputBox(width=70)
    response_stream = ResponseStream()

    try:
        print_info("Initializing NEXUS AI Agent...")
        await app.initialize()

        print_status_box(app.config.model, app.session_id)
        print_help_box()

        print(f"{S.SUCCESS}✓{S.RESET} Ready! Type your message in the box below.\n")

        app.running = True

        while app.running:
            try:
                # Get user input with box
                user_input = input_box.get_input("You")

                if not user_input:
                    continue

                # Handle commands
                if user_input.startswith("/"):
                    cmd_parts = user_input.split(maxsplit=1)
                    command = cmd_parts[0].lower()
                    args = cmd_parts[1] if len(cmd_parts) > 1 else ""

                    if command in ["/exit", "/quit", "/q"]:
                        print_info("Shutting down...")
                        break

                    elif command == "/help":
                        print_help_box()
                        continue

                    elif command == "/models":
                        print_models_box()
                        continue

                    elif command == "/model":
                        if args:
                            if await app.set_model(args):
                                print_success(f"Model changed to: {args}")
                            else:
                                print_error(f"Invalid model: {args}")
                                print_models_box()
                        else:
                            print_info(f"Current model: {app.config.model}")
                        continue

                    elif command == "/prompt":
                        if args:
                            if app.set_system_prompt(args):
                                print_success(f"System prompt changed to: {args}")
                            else:
                                print_error(f"Invalid prompt type: {args}")
                                print_info("Available: default, coder, researcher, analyst, assistant,")
                                print_info("          python, javascript, fullstack, academic, market,")
                                print_info("          technical, data, business, financial, general,")
                                print_info("          writing, planning, master, ultimate")
                        else:
                            print_info("Available prompts:")
                            print_info("  Base: default, coder, researcher, analyst, assistant")
                            print_info("  Coder: python, javascript, fullstack")
                            print_info("  Researcher: academic, market, technical")
                            print_info("  Analyst: data, business, financial")
                            print_info("  Assistant: general, writing, planning")
                            print_info("  Combined: master (3 files), ultimate (5 files)")
                            print_info("Usage: /prompt master")
                        continue

                    elif command == "/status":
                        print_status_box(app.config.model, app.session_id)
                        print_metrics_box(app.get_metrics())
                        continue

                    elif command == "/memory":
                        print_memory_box(app.get_memory_stats())
                        continue

                    elif command == "/tools":
                        tools = app.tool_registry.list_tools()
                        print_tools_box(tools)
                        continue

                    elif command == "/clear":
                        app.clear_history()
                        print_success("Conversation cleared!")
                        continue

                    elif command == "/reset":
                        app.reset_session()
                        clear_screen()
                        print_banner()
                        print_status_box(app.config.model, app.session_id)
                        print_success("Session reset!")
                        continue

                    elif command == "/export":
                        filename = app.export_conversation(args if args else None)
                        print_success(f"Exported to: {filename}")
                        continue

                    else:
                        print_error(f"Unknown command: {command}")
                        continue

                # Chat with AI - simple streaming response
                print_thinking()
                clear_thinking()

                response_stream.start("NEXUS")

                async for chunk in app.chat_stream(user_input):
                    response_stream.write(chunk)

                response_stream.end()

            except KeyboardInterrupt:
                print("\n")
                continue

            except Exception as e:
                logger.error(f"Error: {e}")
                print_error(str(e))

    except Exception as e:
        print_error(f"Initialization failed: {e}")
        logger.exception("Fatal error")

    finally:
        await app.close()
        print_goodbye()


# =============================================================================
# SINGLE TASK MODE
# =============================================================================

async def run_single_task(task: str, model: str = DEFAULT_MODEL, stream: bool = True):
    """Run single task"""
    print_banner()
    print_info(f"Processing with model: {model}")

    config = SessionConfig(model=model, streaming=stream)
    app = NexusApp(config)
    response_stream = ResponseStream()

    try:
        await app.initialize()

        response_stream.start("NEXUS")

        async for chunk in app.chat_stream(task):
            response_stream.write(chunk)

        response_stream.end()
        print_metrics_box(app.get_metrics())

    except Exception as e:
        print_error(str(e))

    finally:
        await app.close()


# =============================================================================
# ENTRY POINT
# =============================================================================

def main():
    """Main entry point"""

    parser = argparse.ArgumentParser(
        description="NEXUS AI Agent - Professional AI Assistant",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
{S.BOLD}Available Models:{S.RESET}
  {S.SUCCESS}●{S.RESET} claude-opus-4-5 {S.SUCCESS}(default){S.RESET}
  {S.MUTED}●{S.RESET} claude-opus-4-1-20250805
  {S.MUTED}●{S.RESET} claude-opus-4-5-20251101

{S.BOLD}Configuration:{S.RESET}
  Max Tokens: {S.ORANGE}{DEFAULT_MAX_TOKENS}{S.RESET}
  Timeout:    {S.ORANGE}{DEFAULT_TIMEOUT}s{S.RESET}

{S.BOLD}Examples:{S.RESET}
  {S.GREEN}python main.py{S.RESET}                    # Interactive mode
  {S.GREEN}python main.py -t "Hello AI"{S.RESET}      # Single task
  {S.GREEN}python main.py -m claude-opus-4-5{S.RESET} # Specific model

{S.MUTED}Powered by TryBons AI - https://go.trybons.ai{S.RESET}
        """
    )

    parser.add_argument("-t", "--task", type=str, help="Single task to execute")
    parser.add_argument("-i", "--interactive", action="store_true", help="Interactive mode")
    parser.add_argument("-m", "--model", type=str, default=DEFAULT_MODEL,
                       choices=AVAILABLE_MODELS, help="Model to use")
    parser.add_argument("--no-stream", action="store_true", help="Disable streaming")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    parser.add_argument("--version", action="version",
                       version=f"NEXUS AI Agent v{NexusApp.VERSION}")

    args = parser.parse_args()

    log_level = "DEBUG" if args.verbose else "WARNING"
    setup_logging(log_level)

    try:
        if args.task:
            asyncio.run(run_single_task(
                task=args.task,
                model=args.model,
                stream=not args.no_stream
            ))
        else:
            asyncio.run(run_interactive(
                model=args.model,
                verbose=args.verbose
            ))

    except KeyboardInterrupt:
        print(f"\n{S.WARNING}Interrupted by user.{S.RESET}")
        sys.exit(0)
    except Exception as e:
        print_error(str(e))
        sys.exit(1)


if __name__ == "__main__":
    main()
