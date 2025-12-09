"""
NEXUS AI Agent - Stream Processor
"""

from typing import Optional, List, Dict, Any, AsyncGenerator, Callable
from dataclasses import dataclass, field
from datetime import datetime
import asyncio

from config.logging_config import get_logger


logger = get_logger(__name__)


@dataclass
class StreamChunk:
    """Represents a chunk in a stream"""
    content: str
    index: int
    timestamp: datetime = field(default_factory=datetime.utcnow)
    is_final: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class StreamMetrics:
    """Metrics for a stream"""
    total_chunks: int = 0
    total_characters: int = 0
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    avg_chunk_size: float = 0.0
    chunks_per_second: float = 0.0

    def calculate(self) -> None:
        """Calculate derived metrics"""
        if self.total_chunks > 0:
            self.avg_chunk_size = self.total_characters / self.total_chunks

        if self.start_time and self.end_time:
            duration = (self.end_time - self.start_time).total_seconds()
            if duration > 0:
                self.chunks_per_second = self.total_chunks / duration


class StreamBuffer:
    """Buffer for stream processing"""

    def __init__(self, max_size: int = 10000):
        self._buffer: List[str] = []
        self._max_size = max_size
        self._total_size = 0

    def add(self, content: str) -> None:
        """Add content to buffer"""
        self._buffer.append(content)
        self._total_size += len(content)

        # Trim if needed
        while self._total_size > self._max_size and len(self._buffer) > 1:
            removed = self._buffer.pop(0)
            self._total_size -= len(removed)

    def get_content(self) -> str:
        """Get all buffered content"""
        return "".join(self._buffer)

    def clear(self) -> None:
        """Clear buffer"""
        self._buffer = []
        self._total_size = 0

    @property
    def size(self) -> int:
        """Get current buffer size"""
        return self._total_size


class StreamProcessor:
    """
    Processes streaming responses

    Handles:
    - Stream buffering
    - Chunk processing
    - Real-time transformations
    - Stream aggregation
    """

    def __init__(self):
        self._buffer = StreamBuffer()
        self._metrics = StreamMetrics()
        self._transformers: List[Callable[[str], str]] = []
        self._chunk_callbacks: List[Callable[[StreamChunk], None]] = []

    async def process_stream(
        self,
        source: AsyncGenerator[str, None],
        transform: bool = True
    ) -> AsyncGenerator[StreamChunk, None]:
        """
        Process a stream of content

        Args:
            source: Source stream generator
            transform: Whether to apply transformers

        Yields:
            Processed StreamChunk objects
        """
        self._metrics = StreamMetrics()
        self._metrics.start_time = datetime.utcnow()
        self._buffer.clear()
        index = 0

        try:
            async for content in source:
                # Apply transformers
                if transform:
                    for transformer in self._transformers:
                        content = transformer(content)

                # Create chunk
                chunk = StreamChunk(
                    content=content,
                    index=index,
                    is_final=False
                )

                # Update metrics
                self._metrics.total_chunks += 1
                self._metrics.total_characters += len(content)

                # Buffer content
                self._buffer.add(content)

                # Trigger callbacks
                for callback in self._chunk_callbacks:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(chunk)
                    else:
                        callback(chunk)

                yield chunk
                index += 1

            # Final chunk
            final_chunk = StreamChunk(
                content="",
                index=index,
                is_final=True
            )

            self._metrics.end_time = datetime.utcnow()
            self._metrics.calculate()

            yield final_chunk

        except Exception as e:
            logger.error(f"Stream processing error: {e}")
            raise

    async def aggregate_stream(
        self,
        source: AsyncGenerator[str, None]
    ) -> str:
        """
        Aggregate stream into single string

        Args:
            source: Source stream

        Returns:
            Aggregated content
        """
        async for chunk in self.process_stream(source, transform=True):
            pass
        return self._buffer.get_content()

    async def stream_with_progress(
        self,
        source: AsyncGenerator[str, None],
        progress_callback: Callable[[int, int], None]
    ) -> AsyncGenerator[str, None]:
        """
        Stream with progress updates

        Args:
            source: Source stream
            progress_callback: Callback(current, total) for progress

        Yields:
            Content chunks
        """
        chunks_received = 0
        estimated_total = 100  # Estimate

        async for chunk in self.process_stream(source):
            chunks_received += 1
            progress_callback(chunks_received, estimated_total)
            yield chunk.content

    def add_transformer(self, transformer: Callable[[str], str]) -> None:
        """Add a content transformer"""
        self._transformers.append(transformer)

    def add_chunk_callback(self, callback: Callable[[StreamChunk], None]) -> None:
        """Add callback for each chunk"""
        self._chunk_callbacks.append(callback)

    def get_metrics(self) -> Dict[str, Any]:
        """Get stream metrics"""
        return {
            "total_chunks": self._metrics.total_chunks,
            "total_characters": self._metrics.total_characters,
            "avg_chunk_size": self._metrics.avg_chunk_size,
            "chunks_per_second": self._metrics.chunks_per_second,
            "duration_ms": (
                (self._metrics.end_time - self._metrics.start_time).total_seconds() * 1000
                if self._metrics.start_time and self._metrics.end_time
                else 0
            )
        }

    def get_buffered_content(self) -> str:
        """Get current buffered content"""
        return self._buffer.get_content()

    def clear(self) -> None:
        """Clear processor state"""
        self._buffer.clear()
        self._metrics = StreamMetrics()


class StreamSplitter:
    """Splits a stream based on delimiters"""

    def __init__(self, delimiter: str = "\n"):
        self._delimiter = delimiter
        self._buffer = ""

    async def split(
        self,
        source: AsyncGenerator[str, None]
    ) -> AsyncGenerator[str, None]:
        """
        Split stream by delimiter

        Args:
            source: Source stream

        Yields:
            Split segments
        """
        async for chunk in source:
            self._buffer += chunk

            while self._delimiter in self._buffer:
                segment, self._buffer = self._buffer.split(self._delimiter, 1)
                if segment:
                    yield segment

        # Yield remaining buffer
        if self._buffer:
            yield self._buffer
            self._buffer = ""


class StreamMerger:
    """Merges multiple streams"""

    async def merge(
        self,
        *sources: AsyncGenerator[str, None]
    ) -> AsyncGenerator[str, None]:
        """
        Merge multiple streams

        Args:
            sources: Source streams to merge

        Yields:
            Merged content
        """
        pending = set()
        queue = asyncio.Queue()

        async def producer(source, source_id):
            try:
                async for item in source:
                    await queue.put((source_id, item))
            finally:
                await queue.put((source_id, None))

        # Start all producers
        for i, source in enumerate(sources):
            task = asyncio.create_task(producer(source, i))
            pending.add(i)

        # Consume merged stream
        while pending:
            source_id, item = await queue.get()
            if item is None:
                pending.discard(source_id)
            else:
                yield item
