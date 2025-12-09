"""NEXUS AI Agent - Text Summarizer"""

import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class Summary:
    """Summarization result"""
    original_text: str
    summary: str
    original_length: int
    summary_length: int
    compression_ratio: float
    key_sentences: List[str]


class Summarizer:
    """Text summarization tool"""

    def __init__(self):
        self._stopwords = set([
            'a', 'an', 'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to',
            'for', 'of', 'with', 'by', 'from', 'is', 'are', 'was', 'were',
            'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did',
            'will', 'would', 'could', 'should', 'may', 'might', 'must', 'shall',
            'it', 'its', 'this', 'that', 'these', 'those', 'i', 'you', 'he',
            'she', 'we', 'they', 'me', 'him', 'her', 'us', 'them'
        ])

    def summarize(
        self,
        text: str,
        ratio: float = 0.3,
        min_sentences: int = 1,
        max_sentences: int = 10
    ) -> Summary:
        """
        Summarize text using extractive summarization

        Args:
            text: Input text
            ratio: Target summary length ratio
            min_sentences: Minimum sentences in summary
            max_sentences: Maximum sentences in summary

        Returns:
            Summary object
        """
        sentences = self._split_sentences(text)

        if not sentences:
            return Summary(
                original_text=text,
                summary="",
                original_length=len(text),
                summary_length=0,
                compression_ratio=0,
                key_sentences=[]
            )

        # Calculate sentence scores
        scores = self._score_sentences(sentences)

        # Determine number of sentences for summary
        num_sentences = max(
            min_sentences,
            min(max_sentences, int(len(sentences) * ratio))
        )

        # Get top sentences (maintaining original order)
        scored_sentences = list(zip(range(len(sentences)), sentences, scores))
        top_sentences = sorted(scored_sentences, key=lambda x: x[2], reverse=True)[:num_sentences]
        top_sentences = sorted(top_sentences, key=lambda x: x[0])

        summary_sentences = [s[1] for s in top_sentences]
        summary_text = ' '.join(summary_sentences)

        return Summary(
            original_text=text,
            summary=summary_text,
            original_length=len(text),
            summary_length=len(summary_text),
            compression_ratio=round(len(summary_text) / len(text), 3) if text else 0,
            key_sentences=summary_sentences
        )

    def _split_sentences(self, text: str) -> List[str]:
        """Split text into sentences"""
        # Simple sentence splitting
        sentence_pattern = r'(?<=[.!?])\s+'
        sentences = re.split(sentence_pattern, text)
        return [s.strip() for s in sentences if s.strip() and len(s.strip()) > 10]

    def _score_sentences(self, sentences: List[str]) -> List[float]:
        """Score sentences for importance"""
        # Build word frequency
        word_freq: Dict[str, int] = {}
        for sentence in sentences:
            words = re.findall(r'\b\w+\b', sentence.lower())
            for word in words:
                if word not in self._stopwords and len(word) > 2:
                    word_freq[word] = word_freq.get(word, 0) + 1

        # Normalize frequencies
        if word_freq:
            max_freq = max(word_freq.values())
            word_freq = {k: v / max_freq for k, v in word_freq.items()}

        # Score sentences
        scores = []
        for i, sentence in enumerate(sentences):
            words = re.findall(r'\b\w+\b', sentence.lower())
            if not words:
                scores.append(0)
                continue

            # Base score from word frequencies
            word_score = sum(word_freq.get(w, 0) for w in words) / len(words)

            # Position bonus (first sentences are often important)
            position_score = 1.0 if i < 3 else 0.5

            # Length penalty (prefer medium-length sentences)
            length_penalty = 1.0 if 10 <= len(words) <= 30 else 0.7

            scores.append(word_score * position_score * length_penalty)

        return scores

    def summarize_by_sentences(self, text: str, num_sentences: int = 3) -> str:
        """Get summary with exact number of sentences"""
        result = self.summarize(
            text,
            ratio=1.0,
            min_sentences=num_sentences,
            max_sentences=num_sentences
        )
        return result.summary

    def summarize_by_words(self, text: str, max_words: int = 100) -> str:
        """Get summary with approximate word limit"""
        sentences = self._split_sentences(text)
        scores = self._score_sentences(sentences)

        # Sort by score
        scored = sorted(zip(range(len(sentences)), sentences, scores),
                       key=lambda x: x[2], reverse=True)

        # Add sentences until word limit
        selected = []
        word_count = 0

        for idx, sentence, score in scored:
            words_in_sentence = len(sentence.split())
            if word_count + words_in_sentence <= max_words:
                selected.append((idx, sentence))
                word_count += words_in_sentence

        # Sort by original order
        selected.sort(key=lambda x: x[0])
        return ' '.join(s[1] for s in selected)

    def get_key_phrases(self, text: str, top_n: int = 5) -> List[str]:
        """
        Extract key phrases from text

        Args:
            text: Input text
            top_n: Number of key phrases

        Returns:
            List of key phrases
        """
        # Extract noun phrases (simplified)
        words = re.findall(r'\b[A-Z][a-z]+(?:\s+[a-z]+)*\b', text)

        # Count phrase frequencies
        from collections import Counter
        phrase_counts = Counter(words)

        # Get top phrases
        return [phrase for phrase, _ in phrase_counts.most_common(top_n)]

    def get_topics(self, text: str, num_topics: int = 3) -> List[str]:
        """
        Extract main topics from text

        Args:
            text: Input text
            num_topics: Number of topics

        Returns:
            List of topic words
        """
        words = re.findall(r'\b\w+\b', text.lower())
        words = [w for w in words if w not in self._stopwords and len(w) > 3]

        from collections import Counter
        word_counts = Counter(words)

        return [word for word, _ in word_counts.most_common(num_topics)]

    def bullet_points(self, text: str, num_points: int = 5) -> List[str]:
        """
        Create bullet point summary

        Args:
            text: Input text
            num_points: Number of bullet points

        Returns:
            List of bullet points
        """
        sentences = self._split_sentences(text)
        scores = self._score_sentences(sentences)

        # Get top sentences
        scored = sorted(zip(sentences, scores), key=lambda x: x[1], reverse=True)
        top_sentences = scored[:num_points]

        # Create bullet points
        bullets = []
        for sentence, _ in top_sentences:
            # Shorten if needed
            words = sentence.split()
            if len(words) > 20:
                sentence = ' '.join(words[:20]) + '...'
            bullets.append(sentence)

        return bullets

    def headline(self, text: str, max_words: int = 10) -> str:
        """
        Generate headline from text

        Args:
            text: Input text
            max_words: Maximum words in headline

        Returns:
            Headline string
        """
        sentences = self._split_sentences(text)
        if not sentences:
            return ""

        # Use first sentence or highest scored
        scores = self._score_sentences(sentences)
        best_idx = scores.index(max(scores))
        best_sentence = sentences[best_idx]

        # Shorten to headline length
        words = best_sentence.split()
        if len(words) > max_words:
            headline = ' '.join(words[:max_words])
            # Try to end at a natural break
            for punct in [',', '-', ':', ';']:
                if punct in headline:
                    headline = headline.split(punct)[0]
                    break
        else:
            headline = best_sentence

        return headline.strip().rstrip('.,;:')

