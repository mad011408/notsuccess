"""NEXUS AI Agent - Few Shot Selector"""
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

@dataclass
class Example:
    input: str
    output: str
    metadata: Dict[str, Any] = None

class FewShotSelector:
    def __init__(self):
        self._examples: List[Example] = []

    def add_example(self, input: str, output: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        self._examples.append(Example(input=input, output=output, metadata=metadata or {}))

    def select(self, query: str, k: int = 3) -> List[Example]:
        """Select k most relevant examples"""
        # Simple keyword matching (could use embeddings)
        query_words = set(query.lower().split())
        scored = []
        for ex in self._examples:
            ex_words = set(ex.input.lower().split())
            score = len(query_words & ex_words)
            scored.append((score, ex))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [ex for _, ex in scored[:k]]

    def format_examples(self, examples: List[Example]) -> str:
        return "\n\n".join([f"Input: {ex.input}\nOutput: {ex.output}" for ex in examples])
