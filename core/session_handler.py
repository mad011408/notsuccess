"""
NEXUS AI Agent - Session Handler
"""

from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime
import uuid
import json
from pathlib import Path

from config.logging_config import get_logger


logger = get_logger(__name__)


@dataclass
class Interaction:
    """Represents a single interaction"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_input: str = ""
    agent_response: str = ""
    timestamp: datetime = field(default_factory=datetime.utcnow)
    tokens_used: int = 0
    latency_ms: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Session:
    """Represents a conversation session"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    interactions: List[Interaction] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    user_id: Optional[str] = None
    agent_id: Optional[str] = None
    title: str = "New Session"
    is_active: bool = True


class SessionHandler:
    """
    Manages conversation sessions

    Handles:
    - Session creation and management
    - Interaction tracking
    - Session persistence
    - History management
    """

    def __init__(
        self,
        session_id: Optional[str] = None,
        persistence_path: Optional[str] = None
    ):
        self._current_session: Optional[Session] = None
        self._persistence_path = Path(persistence_path) if persistence_path else None
        self._sessions_cache: Dict[str, Session] = {}

        if session_id:
            self.load_session(session_id)
        else:
            self.create_session()

    def create_session(
        self,
        user_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Session:
        """Create a new session"""
        session = Session(
            user_id=user_id,
            metadata=metadata or {}
        )
        self._current_session = session
        self._sessions_cache[session.id] = session

        logger.info(f"Session created: {session.id}")
        return session

    def get_session(self) -> Optional[Session]:
        """Get current session"""
        return self._current_session

    def get_session_id(self) -> Optional[str]:
        """Get current session ID"""
        return self._current_session.id if self._current_session else None

    def add_interaction(
        self,
        user_input: str,
        agent_response: str,
        tokens_used: int = 0,
        latency_ms: float = 0.0,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Interaction:
        """Add an interaction to the current session"""
        if not self._current_session:
            self.create_session()

        interaction = Interaction(
            user_input=user_input,
            agent_response=agent_response,
            tokens_used=tokens_used,
            latency_ms=latency_ms,
            metadata=metadata or {}
        )

        self._current_session.interactions.append(interaction)
        self._current_session.updated_at = datetime.utcnow()

        # Auto-generate title from first interaction
        if len(self._current_session.interactions) == 1:
            self._current_session.title = self._generate_title(user_input)

        logger.debug(f"Interaction added to session {self._current_session.id}")

        return interaction

    def get_history(
        self,
        limit: Optional[int] = None,
        as_messages: bool = True
    ) -> List[Dict[str, str]]:
        """
        Get conversation history

        Args:
            limit: Maximum number of interactions to return
            as_messages: Return as message format for LLM

        Returns:
            List of interactions or messages
        """
        if not self._current_session:
            return []

        interactions = self._current_session.interactions
        if limit:
            interactions = interactions[-limit:]

        if as_messages:
            messages = []
            for interaction in interactions:
                messages.append({
                    "role": "user",
                    "content": interaction.user_input
                })
                messages.append({
                    "role": "assistant",
                    "content": interaction.agent_response
                })
            return messages

        return [
            {
                "id": i.id,
                "user_input": i.user_input,
                "agent_response": i.agent_response,
                "timestamp": i.timestamp.isoformat(),
                "tokens_used": i.tokens_used
            }
            for i in interactions
        ]

    def get_last_interaction(self) -> Optional[Interaction]:
        """Get the last interaction"""
        if self._current_session and self._current_session.interactions:
            return self._current_session.interactions[-1]
        return None

    def save_session(self, path: Optional[str] = None) -> bool:
        """Save current session to file"""
        if not self._current_session:
            return False

        save_path = Path(path) if path else self._persistence_path
        if not save_path:
            logger.warning("No persistence path specified")
            return False

        save_path.mkdir(parents=True, exist_ok=True)
        file_path = save_path / f"{self._current_session.id}.json"

        session_data = self._serialize_session(self._current_session)

        with open(file_path, "w") as f:
            json.dump(session_data, f, indent=2, default=str)

        logger.info(f"Session saved: {file_path}")
        return True

    def load_session(self, session_id: str, path: Optional[str] = None) -> Optional[Session]:
        """Load a session from file"""
        # Check cache first
        if session_id in self._sessions_cache:
            self._current_session = self._sessions_cache[session_id]
            return self._current_session

        load_path = Path(path) if path else self._persistence_path
        if not load_path:
            return None

        file_path = load_path / f"{session_id}.json"

        if not file_path.exists():
            logger.warning(f"Session file not found: {file_path}")
            return None

        with open(file_path, "r") as f:
            session_data = json.load(f)

        session = self._deserialize_session(session_data)
        self._current_session = session
        self._sessions_cache[session_id] = session

        logger.info(f"Session loaded: {session_id}")
        return session

    def list_sessions(self, path: Optional[str] = None) -> List[Dict[str, Any]]:
        """List all saved sessions"""
        list_path = Path(path) if path else self._persistence_path
        if not list_path or not list_path.exists():
            return []

        sessions = []
        for file_path in list_path.glob("*.json"):
            try:
                with open(file_path, "r") as f:
                    data = json.load(f)
                sessions.append({
                    "id": data.get("id"),
                    "title": data.get("title"),
                    "created_at": data.get("created_at"),
                    "interaction_count": len(data.get("interactions", []))
                })
            except Exception as e:
                logger.error(f"Error reading session file {file_path}: {e}")

        return sorted(sessions, key=lambda x: x.get("created_at", ""), reverse=True)

    def delete_session(self, session_id: str, path: Optional[str] = None) -> bool:
        """Delete a session"""
        delete_path = Path(path) if path else self._persistence_path
        if not delete_path:
            return False

        file_path = delete_path / f"{session_id}.json"

        if file_path.exists():
            file_path.unlink()
            if session_id in self._sessions_cache:
                del self._sessions_cache[session_id]
            logger.info(f"Session deleted: {session_id}")
            return True

        return False

    def clear(self) -> None:
        """Clear current session"""
        if self._current_session:
            self._current_session.interactions = []
            self._current_session.updated_at = datetime.utcnow()

    def end_session(self) -> None:
        """End current session"""
        if self._current_session:
            self._current_session.is_active = False
            self.save_session()
            self._current_session = None

    def _generate_title(self, first_message: str) -> str:
        """Generate session title from first message"""
        # Take first 50 characters
        title = first_message[:50]
        if len(first_message) > 50:
            title += "..."
        return title

    def _serialize_session(self, session: Session) -> Dict[str, Any]:
        """Serialize session to dictionary"""
        return {
            "id": session.id,
            "created_at": session.created_at.isoformat(),
            "updated_at": session.updated_at.isoformat(),
            "title": session.title,
            "user_id": session.user_id,
            "agent_id": session.agent_id,
            "is_active": session.is_active,
            "metadata": session.metadata,
            "interactions": [
                {
                    "id": i.id,
                    "user_input": i.user_input,
                    "agent_response": i.agent_response,
                    "timestamp": i.timestamp.isoformat(),
                    "tokens_used": i.tokens_used,
                    "latency_ms": i.latency_ms,
                    "metadata": i.metadata
                }
                for i in session.interactions
            ]
        }

    def _deserialize_session(self, data: Dict[str, Any]) -> Session:
        """Deserialize dictionary to session"""
        interactions = [
            Interaction(
                id=i["id"],
                user_input=i["user_input"],
                agent_response=i["agent_response"],
                timestamp=datetime.fromisoformat(i["timestamp"]),
                tokens_used=i.get("tokens_used", 0),
                latency_ms=i.get("latency_ms", 0.0),
                metadata=i.get("metadata", {})
            )
            for i in data.get("interactions", [])
        ]

        return Session(
            id=data["id"],
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            title=data.get("title", ""),
            user_id=data.get("user_id"),
            agent_id=data.get("agent_id"),
            is_active=data.get("is_active", False),
            metadata=data.get("metadata", {}),
            interactions=interactions
        )

    def get_stats(self) -> Dict[str, Any]:
        """Get session statistics"""
        if not self._current_session:
            return {}

        total_tokens = sum(i.tokens_used for i in self._current_session.interactions)
        total_latency = sum(i.latency_ms for i in self._current_session.interactions)

        return {
            "session_id": self._current_session.id,
            "interaction_count": len(self._current_session.interactions),
            "total_tokens": total_tokens,
            "total_latency_ms": total_latency,
            "avg_latency_ms": total_latency / len(self._current_session.interactions) if self._current_session.interactions else 0,
            "created_at": self._current_session.created_at.isoformat(),
            "duration_seconds": (datetime.utcnow() - self._current_session.created_at).total_seconds()
        }
