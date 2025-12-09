"""
NEXUS AI Agent - Response Streamer
"""

from typing import Optional, List, Dict, Any, AsyncGenerator, Callable
from dataclasses import dataclass, field
from datetime import datetime
import asyncio

from config.logging_config import get_logger


logger = get_logger(__name__)


@dataclass
class StreamEvent:
    """Event in a response stream"""
    type: str
    content: str = ""
    delta: str = ""
    index: int = 0
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class StreamState:
    """Current state of stream"""
    is_streaming: bool = False
    content: str = ""
    chunks_received: int = 0
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    error: Optional[str] = None


class ResponseStreamer:
    """
    Handles streaming responses from LLMs

    Features:
    - Stream processing
    - Event emission
    - Progress tracking
    - Buffer management
    """

    def __init__(self):
        self._state = StreamState()
        self._callbacks: Dict[str, List[Callable]] = {
            "on_start": [],
            "on_chunk": [],
            "on_end": [],
            "on_error": [],
        }
        self._buffer: List[str] = []

    async def stream(
        self,
        source: AsyncGenerator[str, None],
        on_chunk: Optional[Callable[[str], None]] = None
    ) -> AsyncGenerator[StreamEvent, None]:
        """
        Process a stream

        Args:
            source: Source stream generator
            on_chunk: Optional callback for each chunk

        Yields:
            StreamEvent objects
        """
        self._state = StreamState(
            is_streaming=True,
            start_time=datetime.utcnow()
        )
        self._buffer = []

        # Emit start event
        yield StreamEvent(type="start", index=0)
        await self._trigger("on_start")

        try:
            async for chunk in source:
                self._state.content += chunk
                self._state.chunks_received += 1
                self._buffer.append(chunk)

                event = StreamEvent(
                    type="chunk",
                    content=self._state.content,
                    delta=chunk,
                    index=self._state.chunks_received
                )

                if on_chunk:
                    if asyncio.iscoroutinefunction(on_chunk):
                        await on_chunk(chunk)
                    else:
                        on_chunk(chunk)

                await self._trigger("on_chunk", chunk)

                yield event

            # End of stream
            self._state.is_streaming = False
            self._state.end_time = datetime.utcnow()

            yield StreamEvent(
                type="end",
                content=self._state.content,
                index=self._state.chunks_received,
                metadata={
                    "total_chunks": self._state.chunks_received,
                    "duration_ms": self._get_duration()
                }
            )

            await self._trigger("on_end", self._state.content)

        except Exception as e:
            self._state.is_streaming = False
            self._state.error = str(e)
            self._state.end_time = datetime.utcnow()

            logger.error(f"Stream error: {e}")
            await self._trigger("on_error", e)

            yield StreamEvent(
                type="error",
                content=str(e),
                index=self._state.chunks_received
            )

    async def stream_to_string(
        self,
        source: AsyncGenerator[str, None]
    ) -> str:
        """
        Stream and collect into string

        Args:
            source: Source stream

        Returns:
            Complete response string
        """
        async for event in self.stream(source):
            if event.type == "end":
                return event.content
            elif event.type == "error":
                raise RuntimeError(event.content)

        return self._state.content

    async def stream_with_callback(
        self,
        source: AsyncGenerator[str, None],
        callback: Callable[[str], None]
    ) -> str:
        """
        Stream with callback for each chunk

        Args:
            source: Source stream
            callback: Called with each chunk

        Returns:
            Complete response
        """
        async for event in self.stream(source, on_chunk=callback):
            if event.type == "error":
                raise RuntimeError(event.content)

        return self._state.content

    async def stream_chunks(
        self,
        source: AsyncGenerator[str, None],
        chunk_size: int = 10
    ) -> AsyncGenerator[str, None]:
        """
        Re-chunk stream into larger chunks

        Args:
            source: Source stream
            chunk_size: Number of original chunks per emitted chunk

        Yields:
            Larger combined chunks
        """
        buffer = []
        count = 0

        async for chunk in source:
            buffer.append(chunk)
            count += 1

            if count >= chunk_size:
                yield "".join(buffer)
                buffer = []
                count = 0

        if buffer:
            yield "".join(buffer)

    async def stream_lines(
        self,
        source: AsyncGenerator[str, None]
    ) -> AsyncGenerator[str, None]:
        """
        Stream line by line

        Args:
            source: Source stream

        Yields:
            Complete lines
        """
        buffer = ""

        async for chunk in source:
            buffer += chunk

            while "\n" in buffer:
                line, buffer = buffer.split("\n", 1)
                yield line

        if buffer:
            yield buffer

    async def stream_words(
        self,
        source: AsyncGenerator[str, None]
    ) -> AsyncGenerator[str, None]:
        """
        Stream word by word

        Args:
            source: Source stream

        Yields:
            Complete words
        """
        buffer = ""

        async for chunk in source:
            buffer += chunk

            while " " in buffer:
                word, buffer = buffer.split(" ", 1)
                if word:
                    yield word

        if buffer:
            yield buffer

    def add_callback(self, event: str, callback: Callable) -> None:
        """Add callback for stream event"""
        if event in self._callbacks:
            self._callbacks[event].append(callback)

    def remove_callback(self, event: str, callback: Callable) -> None:
        """Remove callback"""
        if event in self._callbacks and callback in self._callbacks[event]:
            self._callbacks[event].remove(callback)

    async def _trigger(self, event: str, *args) -> None:
        """Trigger callbacks for event"""
        for callback in self._callbacks.get(event, []):
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(*args)
                else:
                    callback(*args)
            except Exception as e:
                logger.error(f"Callback error: {e}")

    def get_state(self) -> StreamState:
        """Get current stream state"""
        return self._state

    def get_content(self) -> str:
        """Get accumulated content"""
        return self._state.content

    def get_buffer(self) -> List[str]:
        """Get buffer of chunks"""
        return self._buffer.copy()

    def _get_duration(self) -> float:
        """Get stream duration in milliseconds"""
        if self._state.start_time and self._state.end_time:
            return (self._state.end_time - self._state.start_time).total_seconds() * 1000
        return 0.0

    def get_stats(self) -> Dict[str, Any]:
        """Get stream statistics"""
        return {
            "is_streaming": self._state.is_streaming,
            "chunks_received": self._state.chunks_received,
            "content_length": len(self._state.content),
            "duration_ms": self._get_duration(),
            "error": self._state.error,
        }

    def reset(self) -> None:
        """Reset streamer state"""
        self._state = StreamState()
        self._buffer = []


class TypewriterStreamer(ResponseStreamer):
    """Streamer with typewriter effect"""

    def __init__(self, delay_ms: float = 20):
        super().__init__()
        self._delay_ms = delay_ms

    async def stream(
        self,
        source: AsyncGenerator[str, None],
        on_chunk: Optional[Callable[[str], None]] = None
    ) -> AsyncGenerator[StreamEvent, None]:
        """Stream with typewriter delay"""
        async for event in super().stream(source, on_chunk):
            if event.type == "chunk":
                await asyncio.sleep(self._delay_ms / 1000)
            yield event


class BufferedStreamer(ResponseStreamer):
    """Streamer with sentence buffering"""

    def __init__(self, sentence_delimiters: str = ".!?"):
        super().__init__()
        self._delimiters = sentence_delimiters
        self._sentence_buffer = ""

    async def stream_sentences(
        self,
        source: AsyncGenerator[str, None]
    ) -> AsyncGenerator[str, None]:
        """
        Stream complete sentences

        Args:
            source: Source stream

        Yields:
            Complete sentences
        """
        async for chunk in source:
            self._sentence_buffer += chunk

            while any(d in self._sentence_buffer for d in self._delimiters):
                for d in self._delimiters:
                    if d in self._sentence_buffer:
                        sentence, self._sentence_buffer = self._sentence_buffer.split(d, 1)
                        yield sentence + d
                        break

        if self._sentence_buffer.strip():
            yield self._sentence_buffer
