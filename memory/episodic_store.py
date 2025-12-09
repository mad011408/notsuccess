"""
NEXUS AI Agent - Episodic Memory Store
"""

from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime
import uuid

from config.logging_config import get_logger


logger = get_logger(__name__)


@dataclass
class Episode:
    """An episodic memory"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    description: str = ""
    outcome: str = ""
    context: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    importance: float = 0.5
    tags: List[str] = field(default_factory=list)
    embedding: Optional[List[float]] = None


class EpisodicStore:
    """
    Episodic memory store

    Stores experiences and their outcomes for learning.
    """

    def __init__(self, max_episodes: int = 1000):
        self._episodes: Dict[str, Episode] = {}
        self._max_episodes = max_episodes

    def store(
        self,
        description: str,
        outcome: str,
        context: Optional[Dict[str, Any]] = None,
        importance: float = 0.5,
        tags: Optional[List[str]] = None
    ) -> Episode:
        """Store an episode"""
        episode = Episode(
            description=description,
            outcome=outcome,
            context=context or {},
            importance=importance,
            tags=tags or []
        )

        self._episodes[episode.id] = episode

        # Cleanup if over limit
        self._cleanup()

        return episode

    def recall(
        self,
        query: str,
        limit: int = 5,
        tags: Optional[List[str]] = None
    ) -> List[Episode]:
        """
        Recall similar episodes

        Args:
            query: Search query
            limit: Max results
            tags: Filter by tags

        Returns:
            List of matching episodes
        """
        results = []
        query_lower = query.lower()

        for episode in self._episodes.values():
            # Tag filter
            if tags and not any(t in episode.tags for t in tags):
                continue

            # Simple text matching
            if query_lower in episode.description.lower() or \
               query_lower in episode.outcome.lower():
                results.append(episode)

        # Sort by importance and recency
        results.sort(
            key=lambda e: (e.importance, e.timestamp.timestamp()),
            reverse=True
        )

        return results[:limit]

    def recall_by_tags(self, tags: List[str], limit: int = 10) -> List[Episode]:
        """Recall episodes by tags"""
        results = []
        for episode in self._episodes.values():
            if any(t in episode.tags for t in tags):
                results.append(episode)

        results.sort(key=lambda e: e.timestamp, reverse=True)
        return results[:limit]

    def get_recent(self, limit: int = 10) -> List[Episode]:
        """Get most recent episodes"""
        episodes = sorted(
            self._episodes.values(),
            key=lambda e: e.timestamp,
            reverse=True
        )
        return episodes[:limit]

    def update_importance(self, episode_id: str, importance: float) -> bool:
        """Update episode importance"""
        if episode_id in self._episodes:
            self._episodes[episode_id].importance = importance
            return True
        return False

    def _cleanup(self) -> None:
        """Remove least important episodes if over limit"""
        if len(self._episodes) <= self._max_episodes:
            return

        # Sort by importance (ascending)
        sorted_episodes = sorted(
            self._episodes.items(),
            key=lambda x: x[1].importance
        )

        # Remove lowest importance episodes
        to_remove = len(self._episodes) - self._max_episodes
        for episode_id, _ in sorted_episodes[:to_remove]:
            del self._episodes[episode_id]

    def clear(self) -> None:
        """Clear all episodes"""
        self._episodes.clear()

    def __len__(self) -> int:
        return len(self._episodes)
