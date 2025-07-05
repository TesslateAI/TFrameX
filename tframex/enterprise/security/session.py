"""
Session Management

This module provides comprehensive session management capabilities
including session creation, validation, expiration, and cleanup.
"""

import asyncio
import hashlib
import logging
import secrets
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union
from uuid import UUID, uuid4

from ..models import User
from ..storage.base import BaseStorage

logger = logging.getLogger(__name__)


class Session:
    """
    Represents a user session with authentication and tracking information.
    """
    
    def __init__(
        self,
        session_id: str,
        user_id: UUID,
        created_at: datetime,
        expires_at: datetime,
        data: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize session.
        
        Args:
            session_id: Unique session identifier
            user_id: User ID associated with session
            created_at: Session creation timestamp
            expires_at: Session expiration timestamp
            data: Additional session data
        """
        self.session_id = session_id
        self.user_id = user_id
        self.created_at = created_at
        self.expires_at = expires_at
        self.last_activity = created_at
        self.data = data or {}
        self.is_active = True
    
    @property
    def is_expired(self) -> bool:
        """Check if session is expired."""
        return datetime.utcnow() > self.expires_at
    
    @property
    def is_valid(self) -> bool:
        """Check if session is valid (active and not expired)."""
        return self.is_active and not self.is_expired
    
    @property
    def age(self) -> timedelta:
        """Get session age."""
        return datetime.utcnow() - self.created_at
    
    @property
    def time_since_activity(self) -> timedelta:
        """Get time since last activity."""
        return datetime.utcnow() - self.last_activity
    
    def update_activity(self) -> None:
        """Update last activity timestamp."""
        self.last_activity = datetime.utcnow()
    
    def extend_expiration(self, duration: timedelta) -> None:
        """
        Extend session expiration.
        
        Args:
            duration: Duration to extend by
        """
        self.expires_at = datetime.utcnow() + duration
    
    def invalidate(self) -> None:
        """Invalidate the session."""
        self.is_active = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert session to dictionary."""
        return {
            "session_id": self.session_id,
            "user_id": str(self.user_id),
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat(),
            "last_activity": self.last_activity.isoformat(),
            "is_active": self.is_active,
            "data": self.data
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Session':
        """Create session from dictionary."""
        session = cls(
            session_id=data["session_id"],
            user_id=UUID(data["user_id"]),
            created_at=datetime.fromisoformat(data["created_at"]),
            expires_at=datetime.fromisoformat(data["expires_at"]),
            data=data.get("data", {})
        )
        
        session.last_activity = datetime.fromisoformat(data["last_activity"])
        session.is_active = data.get("is_active", True)
        
        return session


class SessionStore:
    """
    Abstract interface for session storage backends.
    """
    
    async def create_session(self, session: Session) -> None:
        """
        Create a new session.
        
        Args:
            session: Session to create
        """
        raise NotImplementedError
    
    async def get_session(self, session_id: str) -> Optional[Session]:
        """
        Get session by ID.
        
        Args:
            session_id: Session ID
            
        Returns:
            Session object or None if not found
        """
        raise NotImplementedError
    
    async def update_session(self, session: Session) -> None:
        """
        Update existing session.
        
        Args:
            session: Session to update
        """
        raise NotImplementedError
    
    async def delete_session(self, session_id: str) -> None:
        """
        Delete session by ID.
        
        Args:
            session_id: Session ID to delete
        """
        raise NotImplementedError
    
    async def get_user_sessions(self, user_id: UUID) -> List[Session]:
        """
        Get all sessions for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            List of user sessions
        """
        raise NotImplementedError
    
    async def cleanup_expired_sessions(self) -> int:
        """
        Clean up expired sessions.
        
        Returns:
            Number of sessions cleaned up
        """
        raise NotImplementedError


class DatabaseSessionStore(SessionStore):
    """
    Database-backed session store implementation.
    """
    
    def __init__(self, storage: BaseStorage, table_name: str = "sessions"):
        """
        Initialize database session store.
        
        Args:
            storage: Storage backend
            table_name: Table name for sessions
        """
        self.storage = storage
        self.table_name = table_name
    
    async def initialize(self) -> None:
        """Initialize session storage table."""
        try:
            # Ensure sessions table exists
            await self.storage.create_table(self.table_name, {
                "session_id": "VARCHAR(128) PRIMARY KEY",
                "user_id": "UUID NOT NULL",
                "created_at": "TIMESTAMP NOT NULL",
                "expires_at": "TIMESTAMP NOT NULL",
                "last_activity": "TIMESTAMP NOT NULL",
                "is_active": "BOOLEAN DEFAULT TRUE",
                "data": "JSONB DEFAULT '{}'",
                "INDEX(user_id)": "",
                "INDEX(expires_at)": ""
            })
            
            logger.info("Database session store initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize session store: {e}")
            raise
    
    async def create_session(self, session: Session) -> None:
        """Create a new session in database."""
        try:
            session_data = {
                "session_id": session.session_id,
                "user_id": str(session.user_id),
                "created_at": session.created_at.isoformat(),
                "expires_at": session.expires_at.isoformat(),
                "last_activity": session.last_activity.isoformat(),
                "is_active": session.is_active,
                "data": session.data
            }
            
            await self.storage.insert(self.table_name, session_data)
            
        except Exception as e:
            logger.error(f"Failed to create session {session.session_id}: {e}")
            raise
    
    async def get_session(self, session_id: str) -> Optional[Session]:
        """Get session from database."""
        try:
            sessions = await self.storage.select(
                self.table_name,
                filters={"session_id": session_id}
            )
            
            if not sessions:
                return None
            
            session_data = sessions[0]
            return Session.from_dict(session_data)
            
        except Exception as e:
            logger.error(f"Failed to get session {session_id}: {e}")
            return None
    
    async def update_session(self, session: Session) -> None:
        """Update session in database."""
        try:
            update_data = {
                "last_activity": session.last_activity.isoformat(),
                "expires_at": session.expires_at.isoformat(),
                "is_active": session.is_active,
                "data": session.data
            }
            
            await self.storage.update(
                self.table_name,
                session.session_id,
                update_data,
                key_field="session_id"
            )
            
        except Exception as e:
            logger.error(f"Failed to update session {session.session_id}: {e}")
            raise
    
    async def delete_session(self, session_id: str) -> None:
        """Delete session from database."""
        try:
            await self.storage.delete(
                self.table_name,
                session_id,
                key_field="session_id"
            )
            
        except Exception as e:
            logger.error(f"Failed to delete session {session_id}: {e}")
            raise
    
    async def get_user_sessions(self, user_id: UUID) -> List[Session]:
        """Get all sessions for a user from database."""
        try:
            sessions_data = await self.storage.select(
                self.table_name,
                filters={"user_id": str(user_id), "is_active": True}
            )
            
            sessions = []
            for session_data in sessions_data:
                session = Session.from_dict(session_data)
                if session.is_valid:
                    sessions.append(session)
            
            return sessions
            
        except Exception as e:
            logger.error(f"Failed to get sessions for user {user_id}: {e}")
            return []
    
    async def cleanup_expired_sessions(self) -> int:
        """Clean up expired sessions from database."""
        try:
            # Get expired sessions
            now = datetime.utcnow().isoformat()
            expired_sessions = await self.storage.select(
                self.table_name,
                filters={"expires_at": {"$lt": now}}
            )
            
            # Delete expired sessions
            count = 0
            for session_data in expired_sessions:
                await self.storage.delete(
                    self.table_name,
                    session_data["session_id"],
                    key_field="session_id"
                )
                count += 1
            
            if count > 0:
                logger.info(f"Cleaned up {count} expired sessions")
            
            return count
            
        except Exception as e:
            logger.error(f"Failed to cleanup expired sessions: {e}")
            return 0


class MemorySessionStore(SessionStore):
    """
    In-memory session store implementation for development/testing.
    """
    
    def __init__(self):
        """Initialize memory session store."""
        self._sessions: Dict[str, Session] = {}
    
    async def create_session(self, session: Session) -> None:
        """Create session in memory."""
        self._sessions[session.session_id] = session
    
    async def get_session(self, session_id: str) -> Optional[Session]:
        """Get session from memory."""
        return self._sessions.get(session_id)
    
    async def update_session(self, session: Session) -> None:
        """Update session in memory."""
        if session.session_id in self._sessions:
            self._sessions[session.session_id] = session
    
    async def delete_session(self, session_id: str) -> None:
        """Delete session from memory."""
        if session_id in self._sessions:
            del self._sessions[session_id]
    
    async def get_user_sessions(self, user_id: UUID) -> List[Session]:
        """Get all sessions for a user from memory."""
        return [
            session for session in self._sessions.values()
            if session.user_id == user_id and session.is_valid
        ]
    
    async def cleanup_expired_sessions(self) -> int:
        """Clean up expired sessions from memory."""
        expired_ids = [
            session_id for session_id, session in self._sessions.items()
            if session.is_expired
        ]
        
        for session_id in expired_ids:
            del self._sessions[session_id]
        
        return len(expired_ids)


class SessionManager:
    """
    Comprehensive session manager with creation, validation, and cleanup.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize session manager.
        
        Args:
            config: Configuration with keys:
                - session_store: Session store implementation
                - session_timeout: Session timeout in seconds
                - max_sessions_per_user: Maximum sessions per user
                - cleanup_interval: Cleanup interval in seconds
                - session_id_length: Length of session IDs
                - enable_session_rotation: Whether to rotate session IDs
        """
        self.config = config
        self.session_store: SessionStore = config.get("session_store")
        self.session_timeout = config.get("session_timeout", 3600)  # 1 hour
        self.max_sessions_per_user = config.get("max_sessions_per_user", 5)
        self.cleanup_interval = config.get("cleanup_interval", 300)  # 5 minutes
        self.session_id_length = config.get("session_id_length", 64)
        self.enable_rotation = config.get("enable_session_rotation", True)
        
        if not self.session_store:
            raise ValueError("Session store is required for session manager")
        
        # Background cleanup task
        self._cleanup_task: Optional[asyncio.Task] = None
        self._running = False
    
    async def start(self) -> None:
        """Start session manager and background cleanup."""
        try:
            # Initialize session store
            if hasattr(self.session_store, "initialize"):
                await self.session_store.initialize()
            
            # Start cleanup task
            self._running = True
            self._cleanup_task = asyncio.create_task(self._cleanup_worker())
            
            logger.info("Session manager started")
            
        except Exception as e:
            logger.error(f"Failed to start session manager: {e}")
            raise
    
    async def stop(self) -> None:
        """Stop session manager and cleanup task."""
        self._running = False
        
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
            self._cleanup_task = None
        
        logger.info("Session manager stopped")
    
    async def create_session(
        self,
        user: User,
        data: Optional[Dict[str, Any]] = None
    ) -> Session:
        """
        Create a new session for a user.
        
        Args:
            user: User to create session for
            data: Additional session data
            
        Returns:
            Created session
        """
        try:
            # Check session limit
            existing_sessions = await self.session_store.get_user_sessions(user.id)
            
            if len(existing_sessions) >= self.max_sessions_per_user:
                # Remove oldest session
                oldest_session = min(existing_sessions, key=lambda s: s.created_at)
                await self.invalidate_session(oldest_session.session_id)
            
            # Generate session ID
            session_id = self._generate_session_id()
            
            # Create session
            now = datetime.utcnow()
            expires_at = now + timedelta(seconds=self.session_timeout)
            
            session = Session(
                session_id=session_id,
                user_id=user.id,
                created_at=now,
                expires_at=expires_at,
                data=data
            )
            
            # Store session
            await self.session_store.create_session(session)
            
            logger.debug(f"Created session {session_id} for user {user.username}")
            return session
            
        except Exception as e:
            logger.error(f"Failed to create session for user {user.id}: {e}")
            raise
    
    async def get_session(self, session_id: str) -> Optional[Session]:
        """
        Get session by ID and validate it.
        
        Args:
            session_id: Session ID
            
        Returns:
            Valid session or None
        """
        try:
            session = await self.session_store.get_session(session_id)
            
            if not session:
                return None
            
            if not session.is_valid:
                # Clean up invalid session
                await self.session_store.delete_session(session_id)
                return None
            
            return session
            
        except Exception as e:
            logger.error(f"Failed to get session {session_id}: {e}")
            return None
    
    async def update_session(
        self,
        session_id: str,
        data: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Update session activity and data.
        
        Args:
            session_id: Session ID to update
            data: Optional data to merge into session
            
        Returns:
            True if session was updated
        """
        try:
            session = await self.get_session(session_id)
            if not session:
                return False
            
            # Update activity
            session.update_activity()
            
            # Extend expiration
            session.extend_expiration(timedelta(seconds=self.session_timeout))
            
            # Merge data
            if data:
                session.data.update(data)
            
            # Save changes
            await self.session_store.update_session(session)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to update session {session_id}: {e}")
            return False
    
    async def invalidate_session(self, session_id: str) -> bool:
        """
        Invalidate a session.
        
        Args:
            session_id: Session ID to invalidate
            
        Returns:
            True if session was invalidated
        """
        try:
            await self.session_store.delete_session(session_id)
            logger.debug(f"Invalidated session {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to invalidate session {session_id}: {e}")
            return False
    
    async def invalidate_user_sessions(self, user_id: UUID) -> int:
        """
        Invalidate all sessions for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            Number of sessions invalidated
        """
        try:
            sessions = await self.session_store.get_user_sessions(user_id)
            count = 0
            
            for session in sessions:
                if await self.invalidate_session(session.session_id):
                    count += 1
            
            logger.info(f"Invalidated {count} sessions for user {user_id}")
            return count
            
        except Exception as e:
            logger.error(f"Failed to invalidate sessions for user {user_id}: {e}")
            return 0
    
    async def rotate_session(self, session_id: str) -> Optional[Session]:
        """
        Rotate session ID for security.
        
        Args:
            session_id: Current session ID
            
        Returns:
            New session with rotated ID
        """
        try:
            if not self.enable_rotation:
                return await self.get_session(session_id)
            
            # Get current session
            session = await self.get_session(session_id)
            if not session:
                return None
            
            # Create new session with new ID
            new_session_id = self._generate_session_id()
            
            # Create new session
            new_session = Session(
                session_id=new_session_id,
                user_id=session.user_id,
                created_at=session.created_at,
                expires_at=session.expires_at,
                data=session.data.copy()
            )
            new_session.last_activity = session.last_activity
            
            # Store new session and delete old one
            await self.session_store.create_session(new_session)
            await self.session_store.delete_session(session_id)
            
            logger.debug(f"Rotated session {session_id} to {new_session_id}")
            return new_session
            
        except Exception as e:
            logger.error(f"Failed to rotate session {session_id}: {e}")
            return None
    
    def _generate_session_id(self) -> str:
        """
        Generate a secure session ID.
        
        Returns:
            Session ID string
        """
        # Generate random bytes
        random_bytes = secrets.token_bytes(self.session_id_length // 2)
        
        # Add timestamp for uniqueness
        timestamp = str(int(time.time())).encode()
        
        # Combine and hash
        combined = random_bytes + timestamp
        session_id = hashlib.sha256(combined).hexdigest()[:self.session_id_length]
        
        return session_id
    
    async def _cleanup_worker(self) -> None:
        """Background worker for cleaning up expired sessions."""
        while self._running:
            try:
                await asyncio.sleep(self.cleanup_interval)
                
                if not self._running:
                    break
                
                # Clean up expired sessions
                count = await self.session_store.cleanup_expired_sessions()
                
                if count > 0:
                    logger.debug(f"Cleaned up {count} expired sessions")
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in session cleanup worker: {e}")
                await asyncio.sleep(5)
    
    async def get_session_stats(self) -> Dict[str, Any]:
        """
        Get session statistics.
        
        Returns:
            Statistics dictionary
        """
        try:
            # This would require additional queries to the session store
            # For now, return basic configuration info
            return {
                "session_timeout": self.session_timeout,
                "max_sessions_per_user": self.max_sessions_per_user,
                "cleanup_interval": self.cleanup_interval,
                "rotation_enabled": self.enable_rotation,
                "running": self._running
            }
            
        except Exception as e:
            logger.error(f"Failed to get session stats: {e}")
            return {}
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on session manager.
        
        Returns:
            Health status information
        """
        try:
            # Test session store connectivity
            test_session_id = "health_check_test"
            await self.session_store.get_session(test_session_id)
            
            return {
                "healthy": True,
                "running": self._running,
                "session_store_type": self.session_store.__class__.__name__,
                "configuration": {
                    "session_timeout": self.session_timeout,
                    "max_sessions_per_user": self.max_sessions_per_user,
                    "cleanup_interval": self.cleanup_interval
                }
            }
            
        except Exception as e:
            logger.error(f"Session manager health check failed: {e}")
            return {
                "healthy": False,
                "error": str(e)
            }
    
    # Context manager support
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.start()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.stop()