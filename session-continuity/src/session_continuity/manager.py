from __future__ import annotations

import logging
import threading
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


@dataclass
class SessionState:
    """
    Represents the state of a session.
    
    Attributes:
        session_id (str): Unique identifier for the session.
        resume_token (str): Secret token used to resume the session.
        metadata (Dict[str, Any]): arbitrary metadata associated with the session.
        last_seen (float): Timestamp of the last activity.
    """
    session_id: str
    resume_token: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    last_seen: float = field(default_factory=time.time)


class SessionManager:
    """
    Manages user sessions with support for creation, resumption, and expiration.
    Thread-safe.
    
    Attributes:
        ttl (float): Time-to-live for inactive sessions in seconds.
    """

    def __init__(self, ttl_seconds: float = 3600):
        """
        Initialize the SessionManager.

        Args:
            ttl_seconds (float): Time-to-live for inactive sessions in seconds. Defaults to 3600.
        """
        self.ttl = ttl_seconds
        self._sessions: Dict[str, SessionState] = {}
        self._lock = threading.RLock()

    def create(self, metadata: Optional[Dict[str, Any]] = None) -> SessionState:
        """
        Create a new session.

        Args:
            metadata (Optional[Dict[str, Any]]): Initial metadata for the session.

        Returns:
            SessionState: The newly created session state.
        """
        sid = str(uuid.uuid4())
        token = str(uuid.uuid4())
        # Ensure thread safety when writing to the dictionary
        with self._lock:
            state = SessionState(session_id=sid, resume_token=token, metadata=metadata or {})
            self._sessions[sid] = state
            logger.info("Created session: %s", sid)
            return state

    def resume(self, resume_token: str) -> Optional[SessionState]:
        """
        Resume an existing session using its resume token.
        Updates the last_seen timestamp if successful.

        Args:
            resume_token (str): The token provided to the client.

        Returns:
            Optional[SessionState]: The session state if found and valid, else None.
        """
        with self._lock:
            # Linear search is O(N), acceptable for in-memory small-medium scale.
            # For production at scale, a secondary index mapping token -> session_id would be better.
            for state in list(self._sessions.values()):
                if state.resume_token == resume_token:
                    if time.time() - state.last_seen <= self.ttl:
                        state.last_seen = time.time()
                        logger.debug("Resumed session: %s", state.session_id)
                        return state
                    else:
                        # Found but expired
                        logger.debug("Attempted to resume expired session: %s", state.session_id)
            return None

    def touch(self, session_id: str) -> None:
        """
        Update the last_seen timestamp for a session to prevent expiration.

        Args:
            session_id (str): The session ID.
        """
        with self._lock:
            if session_id in self._sessions:
                self._sessions[session_id].last_seen = time.time()
                logger.debug("Touched session: %s", session_id)

    def get_session(self, session_id: str) -> Optional[SessionState]:
        """
        Retrieve session state by ID without updating last_seen.
        
        Args:
            session_id (str): The session ID.
            
        Returns:
            Optional[SessionState]: The session state if found.
        """
        with self._lock:
            return self._sessions.get(session_id)

    def reap_expired(self) -> int:
        """
        Remove all expired sessions.

        Returns:
            int: The number of sessions removed.
        """
        now = time.time()
        with self._lock:
            expired = [sid for sid, st in self._sessions.items() if now - st.last_seen > self.ttl]
            for sid in expired:
                del self._sessions[sid]
            
            if expired:
                logger.info("Reaped %d expired sessions", len(expired))
            return len(expired)
