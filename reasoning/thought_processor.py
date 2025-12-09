"""
NEXUS AI Agent - Thought Processor
"""

from typing import Optional, List, Dict, Any
from dataclasses import dataclass

from config.logging_config import get_logger


logger = get_logger(__name__)


@dataclass
class ProcessedThought:
    """A processed thought"""
    original: str
    cleaned: str
    key_points: List[str]
    entities: List[str]
    sentiment: str
    confidence: float


class ThoughtProcessor:
    """
    Processes and analyzes thoughts in reasoning chains
    """

    def __init__(self):
        pass

    def process(self, thought: str) -> ProcessedThought:
        """Process a thought"""
        cleaned = self._clean_thought(thought)
        key_points = self._extract_key_points(thought)
        entities = self._extract_entities(thought)
        sentiment = self._analyze_sentiment(thought)

        return ProcessedThought(
            original=thought,
            cleaned=cleaned,
            key_points=key_points,
            entities=entities,
            sentiment=sentiment,
            confidence=0.8
        )

    def _clean_thought(self, thought: str) -> str:
        """Clean and normalize thought text"""
        # Remove extra whitespace
        cleaned = " ".join(thought.split())
        # Remove common filler phrases
        fillers = ["I think", "Let me", "So,", "Well,", "Okay,"]
        for filler in fillers:
            if cleaned.startswith(filler):
                cleaned = cleaned[len(filler):].strip()
        return cleaned

    def _extract_key_points(self, thought: str) -> List[str]:
        """Extract key points from thought"""
        # Simple extraction based on punctuation
        sentences = thought.replace("!", ".").replace("?", ".").split(".")
        key_points = [s.strip() for s in sentences if len(s.strip()) > 20]
        return key_points[:5]  # Return top 5

    def _extract_entities(self, thought: str) -> List[str]:
        """Extract entities from thought"""
        # Simple capitalized word extraction
        words = thought.split()
        entities = []
        for word in words:
            clean_word = word.strip(".,!?\"'")
            if clean_word and clean_word[0].isupper() and len(clean_word) > 2:
                if clean_word not in ["The", "This", "That", "These", "Those", "It"]:
                    entities.append(clean_word)
        return list(set(entities))

    def _analyze_sentiment(self, thought: str) -> str:
        """Analyze sentiment of thought"""
        lower = thought.lower()
        positive = ["good", "great", "excellent", "correct", "right", "yes"]
        negative = ["bad", "wrong", "error", "incorrect", "no", "fail"]

        pos_count = sum(1 for w in positive if w in lower)
        neg_count = sum(1 for w in negative if w in lower)

        if pos_count > neg_count:
            return "positive"
        elif neg_count > pos_count:
            return "negative"
        return "neutral"

    def summarize_chain(self, thoughts: List[str]) -> str:
        """Summarize a chain of thoughts"""
        if not thoughts:
            return ""

        processed = [self.process(t) for t in thoughts]
        all_key_points = []
        for p in processed:
            all_key_points.extend(p.key_points)

        # Take most important points
        summary = " ".join(all_key_points[:5])
        return summary

    def find_contradictions(self, thoughts: List[str]) -> List[tuple]:
        """Find contradictions in thought chain"""
        contradictions = []
        # Simple heuristic: look for negation patterns
        for i, t1 in enumerate(thoughts):
            for j, t2 in enumerate(thoughts[i+1:], i+1):
                if self._might_contradict(t1, t2):
                    contradictions.append((i, j, t1, t2))
        return contradictions

    def _might_contradict(self, t1: str, t2: str) -> bool:
        """Check if two thoughts might contradict"""
        # Very simple check - could be enhanced with NLP
        negations = ["not", "isn't", "aren't", "doesn't", "don't", "never"]
        t1_has_neg = any(n in t1.lower() for n in negations)
        t2_has_neg = any(n in t2.lower() for n in negations)
        return t1_has_neg != t2_has_neg
