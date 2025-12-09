"""
NEXUS AI Agent - Semantic Memory Store
"""

from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime
import uuid

from config.logging_config import get_logger


logger = get_logger(__name__)


@dataclass
class Fact:
    """A semantic fact"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    subject: str = ""
    predicate: str = ""
    object: str = ""
    confidence: float = 1.0
    source: str = ""
    timestamp: datetime = field(default_factory=datetime.utcnow)
    embedding: Optional[List[float]] = None


class SemanticStore:
    """
    Semantic memory store

    Stores factual knowledge as subject-predicate-object triples.
    """

    def __init__(self):
        self._facts: Dict[str, Fact] = {}
        self._subject_index: Dict[str, List[str]] = {}
        self._predicate_index: Dict[str, List[str]] = {}

    def store(
        self,
        subject: str,
        predicate: str,
        obj: str,
        confidence: float = 1.0,
        source: str = ""
    ) -> Fact:
        """
        Store a fact

        Args:
            subject: Subject of the fact
            predicate: Relationship/predicate
            obj: Object of the fact
            confidence: Confidence score
            source: Source of the fact

        Returns:
            Created Fact
        """
        fact = Fact(
            subject=subject,
            predicate=predicate,
            object=obj,
            confidence=confidence,
            source=source
        )

        self._facts[fact.id] = fact

        # Update indexes
        if subject not in self._subject_index:
            self._subject_index[subject] = []
        self._subject_index[subject].append(fact.id)

        if predicate not in self._predicate_index:
            self._predicate_index[predicate] = []
        self._predicate_index[predicate].append(fact.id)

        return fact

    def query(
        self,
        subject: Optional[str] = None,
        predicate: Optional[str] = None,
        obj: Optional[str] = None
    ) -> List[Fact]:
        """
        Query facts

        Args:
            subject: Filter by subject
            predicate: Filter by predicate
            obj: Filter by object

        Returns:
            Matching facts
        """
        results = []

        if subject and subject in self._subject_index:
            candidate_ids = set(self._subject_index[subject])
        elif predicate and predicate in self._predicate_index:
            candidate_ids = set(self._predicate_index[predicate])
        else:
            candidate_ids = set(self._facts.keys())

        for fact_id in candidate_ids:
            fact = self._facts.get(fact_id)
            if not fact:
                continue

            if subject and fact.subject != subject:
                continue
            if predicate and fact.predicate != predicate:
                continue
            if obj and fact.object != obj:
                continue

            results.append(fact)

        return results

    def search(self, query: str, limit: int = 10) -> List[Fact]:
        """Search facts by text"""
        results = []
        query_lower = query.lower()

        for fact in self._facts.values():
            if (query_lower in fact.subject.lower() or
                query_lower in fact.predicate.lower() or
                query_lower in fact.object.lower()):
                results.append(fact)

        results.sort(key=lambda f: f.confidence, reverse=True)
        return results[:limit]

    def get_related(self, subject: str, limit: int = 10) -> List[Fact]:
        """Get facts related to a subject"""
        return self.query(subject=subject)[:limit]

    def update_confidence(self, fact_id: str, confidence: float) -> bool:
        """Update fact confidence"""
        if fact_id in self._facts:
            self._facts[fact_id].confidence = confidence
            return True
        return False

    def remove(self, fact_id: str) -> bool:
        """Remove a fact"""
        if fact_id not in self._facts:
            return False

        fact = self._facts[fact_id]

        # Update indexes
        if fact.subject in self._subject_index:
            self._subject_index[fact.subject].remove(fact_id)
        if fact.predicate in self._predicate_index:
            self._predicate_index[fact.predicate].remove(fact_id)

        del self._facts[fact_id]
        return True

    def clear(self) -> None:
        """Clear all facts"""
        self._facts.clear()
        self._subject_index.clear()
        self._predicate_index.clear()

    def __len__(self) -> int:
        return len(self._facts)
