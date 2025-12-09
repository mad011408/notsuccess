"""
NEXUS AI Agent - Response Generator
"""

from typing import Optional, List, Dict, Any, AsyncGenerator
from dataclasses import dataclass, field
from enum import Enum

from config.logging_config import get_logger


logger = get_logger(__name__)


class ResponseType(str, Enum):
    """Types of responses"""
    TEXT = "text"
    JSON = "json"
    MARKDOWN = "markdown"
    CODE = "code"
    ERROR = "error"
    STREAMING = "streaming"


class ResponseFormat(str, Enum):
    """Response format options"""
    PLAIN = "plain"
    STRUCTURED = "structured"
    CONVERSATIONAL = "conversational"
    TECHNICAL = "technical"


@dataclass
class ResponseMetadata:
    """Metadata for a response"""
    tokens_used: int = 0
    latency_ms: float = 0.0
    model: str = ""
    finish_reason: str = ""
    sources: List[str] = field(default_factory=list)


@dataclass
class Response:
    """Represents a generated response"""
    content: str
    response_type: ResponseType
    format: ResponseFormat
    metadata: ResponseMetadata = field(default_factory=ResponseMetadata)
    raw_response: Optional[Dict[str, Any]] = None


class ResponseGenerator:
    """
    Generates and formats responses

    Handles:
    - Response formatting
    - Content structuring
    - Output transformation
    - Response enhancement
    """

    def __init__(self):
        self._formatters: Dict[ResponseFormat, callable] = {
            ResponseFormat.PLAIN: self._format_plain,
            ResponseFormat.STRUCTURED: self._format_structured,
            ResponseFormat.CONVERSATIONAL: self._format_conversational,
            ResponseFormat.TECHNICAL: self._format_technical
        }
        self._default_format = ResponseFormat.CONVERSATIONAL

    def generate(
        self,
        content: str,
        response_type: ResponseType = ResponseType.TEXT,
        format: Optional[ResponseFormat] = None,
        metadata: Optional[ResponseMetadata] = None
    ) -> Response:
        """
        Generate a formatted response

        Args:
            content: Raw content
            response_type: Type of response
            format: Desired format
            metadata: Response metadata

        Returns:
            Formatted Response object
        """
        format = format or self._default_format

        # Apply formatting
        formatter = self._formatters.get(format, self._format_plain)
        formatted_content = formatter(content, response_type)

        return Response(
            content=formatted_content,
            response_type=response_type,
            format=format,
            metadata=metadata or ResponseMetadata()
        )

    async def generate_stream(
        self,
        content_generator: AsyncGenerator[str, None],
        response_type: ResponseType = ResponseType.STREAMING,
        format: Optional[ResponseFormat] = None
    ) -> AsyncGenerator[str, None]:
        """
        Generate streaming response

        Args:
            content_generator: Async generator of content chunks
            response_type: Type of response
            format: Desired format

        Yields:
            Formatted content chunks
        """
        buffer = ""

        async for chunk in content_generator:
            buffer += chunk

            # For streaming, yield chunks directly
            # Post-processing happens after stream completes
            yield chunk

    def format_error(
        self,
        error: Exception,
        include_traceback: bool = False
    ) -> Response:
        """Format an error response"""
        import traceback as tb

        error_content = f"Error: {str(error)}"
        if include_traceback:
            error_content += f"\n\nTraceback:\n{tb.format_exc()}"

        return Response(
            content=error_content,
            response_type=ResponseType.ERROR,
            format=ResponseFormat.PLAIN
        )

    def format_code(
        self,
        code: str,
        language: str = "python",
        include_explanation: bool = False,
        explanation: str = ""
    ) -> Response:
        """Format a code response"""
        content = f"```{language}\n{code}\n```"

        if include_explanation and explanation:
            content = f"{explanation}\n\n{content}"

        return Response(
            content=content,
            response_type=ResponseType.CODE,
            format=ResponseFormat.TECHNICAL
        )

    def format_json(
        self,
        data: Dict[str, Any],
        pretty: bool = True
    ) -> Response:
        """Format a JSON response"""
        import json

        if pretty:
            content = json.dumps(data, indent=2)
        else:
            content = json.dumps(data)

        return Response(
            content=f"```json\n{content}\n```",
            response_type=ResponseType.JSON,
            format=ResponseFormat.STRUCTURED
        )

    def format_list(
        self,
        items: List[str],
        numbered: bool = False,
        title: str = ""
    ) -> str:
        """Format a list of items"""
        if numbered:
            formatted_items = [f"{i + 1}. {item}" for i, item in enumerate(items)]
        else:
            formatted_items = [f"- {item}" for item in items]

        content = "\n".join(formatted_items)

        if title:
            content = f"**{title}**\n\n{content}"

        return content

    def format_table(
        self,
        headers: List[str],
        rows: List[List[str]]
    ) -> str:
        """Format a markdown table"""
        # Calculate column widths
        widths = [len(h) for h in headers]
        for row in rows:
            for i, cell in enumerate(row):
                if i < len(widths):
                    widths[i] = max(widths[i], len(str(cell)))

        # Build table
        header_row = " | ".join(h.ljust(widths[i]) for i, h in enumerate(headers))
        separator = " | ".join("-" * w for w in widths)

        data_rows = []
        for row in rows:
            data_row = " | ".join(
                str(cell).ljust(widths[i]) if i < len(widths) else str(cell)
                for i, cell in enumerate(row)
            )
            data_rows.append(data_row)

        return f"| {header_row} |\n| {separator} |\n" + "\n".join(f"| {r} |" for r in data_rows)

    def _format_plain(self, content: str, response_type: ResponseType) -> str:
        """Plain text formatting"""
        return content.strip()

    def _format_structured(self, content: str, response_type: ResponseType) -> str:
        """Structured formatting with sections"""
        # Add structure markers if needed
        if response_type == ResponseType.JSON:
            return content

        # Check if already structured
        if any(marker in content for marker in ["##", "**", "- ", "1. "]):
            return content

        # Add basic structure
        paragraphs = content.split("\n\n")
        if len(paragraphs) > 1:
            return "\n\n".join(paragraphs)

        return content

    def _format_conversational(self, content: str, response_type: ResponseType) -> str:
        """Conversational formatting"""
        # Make response more conversational
        content = content.strip()

        # Don't modify code blocks
        if response_type == ResponseType.CODE:
            return content

        # Add natural flow
        if not content.endswith((".", "!", "?", ":", "```")):
            content += "."

        return content

    def _format_technical(self, content: str, response_type: ResponseType) -> str:
        """Technical documentation formatting"""
        # Add technical formatting
        if response_type == ResponseType.CODE:
            return content

        # Highlight technical terms
        lines = content.split("\n")
        formatted_lines = []

        for line in lines:
            # Add code formatting for inline code
            if "`" not in line:
                words = line.split()
                for i, word in enumerate(words):
                    # Technical terms to highlight
                    if word.endswith("()") or word.startswith("_"):
                        words[i] = f"`{word}`"
                line = " ".join(words)
            formatted_lines.append(line)

        return "\n".join(formatted_lines)

    def add_sources(self, content: str, sources: List[str]) -> str:
        """Add source citations to content"""
        if not sources:
            return content

        source_section = "\n\n---\n**Sources:**\n"
        source_section += "\n".join(f"- {source}" for source in sources)

        return content + source_section

    def truncate(
        self,
        content: str,
        max_length: int,
        suffix: str = "..."
    ) -> str:
        """Truncate content to max length"""
        if len(content) <= max_length:
            return content

        return content[:max_length - len(suffix)] + suffix

    def set_default_format(self, format: ResponseFormat) -> None:
        """Set default response format"""
        self._default_format = format
