"""NEXUS AI Agent - Text Splitter"""

import re
from typing import List, Optional, Callable
from dataclasses import dataclass
from enum import Enum


class SplitStrategy(str, Enum):
    """Text splitting strategies"""
    CHARACTER = "character"
    TOKEN = "token"
    SENTENCE = "sentence"
    PARAGRAPH = "paragraph"
    RECURSIVE = "recursive"
    SEMANTIC = "semantic"


@dataclass
class TextChunk:
    """Text chunk with metadata"""
    content: str
    start_index: int
    end_index: int
    chunk_index: int
    metadata: dict = None


class TextSplitter:
    """Split text into chunks"""

    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        strategy: SplitStrategy = SplitStrategy.RECURSIVE,
        separators: Optional[List[str]] = None
    ):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.strategy = strategy
        self.separators = separators or ["\n\n", "\n", ". ", " ", ""]

    def split(self, text: str) -> List[str]:
        """
        Split text into chunks

        Args:
            text: Text to split

        Returns:
            List of text chunks
        """
        if not text:
            return []

        if self.strategy == SplitStrategy.CHARACTER:
            return self._split_by_character(text)
        elif self.strategy == SplitStrategy.SENTENCE:
            return self._split_by_sentence(text)
        elif self.strategy == SplitStrategy.PARAGRAPH:
            return self._split_by_paragraph(text)
        elif self.strategy == SplitStrategy.RECURSIVE:
            return self._split_recursive(text, self.separators)
        else:
            return self._split_by_character(text)

    def split_with_metadata(self, text: str) -> List[TextChunk]:
        """Split text and return chunks with metadata"""
        chunks = self.split(text)
        result = []
        current_index = 0

        for i, chunk in enumerate(chunks):
            start = text.find(chunk, current_index)
            if start == -1:
                start = current_index

            result.append(TextChunk(
                content=chunk,
                start_index=start,
                end_index=start + len(chunk),
                chunk_index=i
            ))

            current_index = start + len(chunk) - self.chunk_overlap

        return result

    def _split_by_character(self, text: str) -> List[str]:
        """Split by character count"""
        chunks = []
        start = 0

        while start < len(text):
            end = start + self.chunk_size

            # Try to end at a word boundary
            if end < len(text):
                # Look for space to break at
                space_idx = text.rfind(' ', start, end)
                if space_idx > start:
                    end = space_idx

            chunks.append(text[start:end].strip())
            start = end - self.chunk_overlap

        return [c for c in chunks if c]

    def _split_by_sentence(self, text: str) -> List[str]:
        """Split by sentences"""
        sentence_pattern = r'(?<=[.!?])\s+'
        sentences = re.split(sentence_pattern, text)

        chunks = []
        current_chunk = []
        current_length = 0

        for sentence in sentences:
            sentence_length = len(sentence)

            if current_length + sentence_length > self.chunk_size and current_chunk:
                chunks.append(' '.join(current_chunk))
                # Keep some sentences for overlap
                overlap_sentences = []
                overlap_length = 0
                for s in reversed(current_chunk):
                    if overlap_length + len(s) <= self.chunk_overlap:
                        overlap_sentences.insert(0, s)
                        overlap_length += len(s)
                    else:
                        break
                current_chunk = overlap_sentences
                current_length = overlap_length

            current_chunk.append(sentence)
            current_length += sentence_length

        if current_chunk:
            chunks.append(' '.join(current_chunk))

        return chunks

    def _split_by_paragraph(self, text: str) -> List[str]:
        """Split by paragraphs"""
        paragraphs = text.split('\n\n')

        chunks = []
        current_chunk = []
        current_length = 0

        for para in paragraphs:
            para = para.strip()
            if not para:
                continue

            para_length = len(para)

            if current_length + para_length > self.chunk_size and current_chunk:
                chunks.append('\n\n'.join(current_chunk))
                current_chunk = []
                current_length = 0

            current_chunk.append(para)
            current_length += para_length

        if current_chunk:
            chunks.append('\n\n'.join(current_chunk))

        return chunks

    def _split_recursive(
        self,
        text: str,
        separators: List[str]
    ) -> List[str]:
        """Recursively split text"""
        if not separators:
            return self._split_by_character(text)

        separator = separators[0]
        remaining_separators = separators[1:]

        if separator:
            splits = text.split(separator)
        else:
            splits = list(text)

        chunks = []
        current_chunk = []
        current_length = 0

        for split in splits:
            split_length = len(split) + len(separator)

            if current_length + split_length > self.chunk_size:
                if current_chunk:
                    merged = separator.join(current_chunk)
                    if len(merged) > self.chunk_size and remaining_separators:
                        # Recursively split further
                        chunks.extend(self._split_recursive(merged, remaining_separators))
                    else:
                        chunks.append(merged)

                current_chunk = []
                current_length = 0

            current_chunk.append(split)
            current_length += split_length

        if current_chunk:
            merged = separator.join(current_chunk)
            if len(merged) > self.chunk_size and remaining_separators:
                chunks.extend(self._split_recursive(merged, remaining_separators))
            else:
                chunks.append(merged)

        return [c.strip() for c in chunks if c.strip()]

    def merge_chunks(
        self,
        chunks: List[str],
        max_size: int
    ) -> List[str]:
        """Merge small chunks together"""
        merged = []
        current = []
        current_length = 0

        for chunk in chunks:
            if current_length + len(chunk) <= max_size:
                current.append(chunk)
                current_length += len(chunk)
            else:
                if current:
                    merged.append('\n\n'.join(current))
                current = [chunk]
                current_length = len(chunk)

        if current:
            merged.append('\n\n'.join(current))

        return merged

    def count_tokens(self, text: str) -> int:
        """Estimate token count (rough approximation)"""
        # Rough estimate: ~4 characters per token
        return len(text) // 4

