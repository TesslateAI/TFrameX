"""
Audit Logging

This module provides comprehensive audit logging capabilities
for security events, user actions, and compliance tracking.
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from uuid import UUID, uuid4

from ..models import User, AuditLog
from ..storage.base import BaseStorage

logger = logging.getLogger(__name__)


class AuditEventType(Enum):
    """Types of audit events."""
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    DATA_ACCESS = "data_access"
    DATA_MODIFICATION = "data_modification"
    SYSTEM_ACCESS = "system_access"
    CONFIGURATION_CHANGE = "configuration_change"
    SECURITY_EVENT = "security_event"
    USER_ACTION = "user_action"
    ADMIN_ACTION = "admin_action"
    ERROR = "error"


class AuditOutcome(Enum):
    """Outcomes of audit events."""
    SUCCESS = "success"
    FAILURE = "failure"
    ERROR = "error"
    BLOCKED = "blocked"
    PENDING = "pending"


class AuditLevel(Enum):
    """Audit logging levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AuditEvent:
    """
    Represents an audit event with comprehensive tracking information.
    """
    
    def __init__(
        self,
        event_type: Union[AuditEventType, str],
        user_id: Optional[UUID] = None,
        resource: Optional[str] = None,
        action: Optional[str] = None,
        outcome: Union[AuditOutcome, str] = AuditOutcome.SUCCESS,
        level: Union[AuditLevel, str] = AuditLevel.MEDIUM,
        details: Optional[Dict[str, Any]] = None,
        request_id: Optional[str] = None,
        session_id: Optional[str] = None,
        remote_ip: Optional[str] = None,
        user_agent: Optional[str] = None
    ):
        """
        Initialize audit event.
        
        Args:
            event_type: Type of event
            user_id: User ID associated with event
            resource: Resource being accessed/modified
            action: Action being performed
            outcome: Event outcome
            level: Audit level
            details: Additional event details
            request_id: Request ID for correlation
            session_id: Session ID for tracking
            remote_ip: Remote IP address
            user_agent: User agent string
        """
        self.id = uuid4()
        self.event_type = event_type if isinstance(event_type, AuditEventType) else AuditEventType(event_type)
        self.user_id = user_id
        self.resource = resource
        self.action = action
        self.outcome = outcome if isinstance(outcome, AuditOutcome) else AuditOutcome(outcome)
        self.level = level if isinstance(level, AuditLevel) else AuditLevel(level)
        self.details = details or {}
        self.request_id = request_id
        self.session_id = session_id
        self.remote_ip = remote_ip
        self.user_agent = user_agent
        self.timestamp = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert audit event to dictionary."""
        return {
            "id": str(self.id),
            "event_type": self.event_type.value,
            "user_id": str(self.user_id) if self.user_id else None,
            "resource": self.resource,
            "action": self.action,
            "outcome": self.outcome.value,
            "level": self.level.value,
            "details": self.details,
            "request_id": self.request_id,
            "session_id": self.session_id,
            "remote_ip": self.remote_ip,
            "user_agent": self.user_agent,
            "timestamp": self.timestamp.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AuditEvent':
        """Create audit event from dictionary."""
        event = cls(
            event_type=data["event_type"],
            user_id=UUID(data["user_id"]) if data.get("user_id") else None,
            resource=data.get("resource"),
            action=data.get("action"),
            outcome=data.get("outcome", "success"),
            level=data.get("level", "medium"),
            details=data.get("details", {}),
            request_id=data.get("request_id"),
            session_id=data.get("session_id"),
            remote_ip=data.get("remote_ip"),
            user_agent=data.get("user_agent")
        )
        
        if "timestamp" in data:
            event.timestamp = datetime.fromisoformat(data["timestamp"])
        if "id" in data:
            event.id = UUID(data["id"])
        
        return event


class AuditFilter:
    """
    Filter for audit events based on various criteria.
    """
    
    def __init__(
        self,
        event_types: Optional[List[AuditEventType]] = None,
        user_ids: Optional[List[UUID]] = None,
        resources: Optional[List[str]] = None,
        actions: Optional[List[str]] = None,
        outcomes: Optional[List[AuditOutcome]] = None,
        levels: Optional[List[AuditLevel]] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        request_id: Optional[str] = None,
        session_id: Optional[str] = None
    ):
        """
        Initialize audit filter.
        
        Args:
            event_types: Event types to include
            user_ids: User IDs to include
            resources: Resources to include
            actions: Actions to include
            outcomes: Outcomes to include
            levels: Audit levels to include
            start_time: Start time for filtering
            end_time: End time for filtering
            request_id: Specific request ID
            session_id: Specific session ID
        """
        self.event_types = event_types
        self.user_ids = user_ids
        self.resources = resources
        self.actions = actions
        self.outcomes = outcomes
        self.levels = levels
        self.start_time = start_time
        self.end_time = end_time
        self.request_id = request_id
        self.session_id = session_id
    
    def to_storage_filter(self) -> Dict[str, Any]:
        """Convert to storage filter format."""
        filters = {}
        
        if self.event_types:
            filters["event_type"] = {"$in": [et.value for et in self.event_types]}
        
        if self.user_ids:
            filters["user_id"] = {"$in": [str(uid) for uid in self.user_ids]}
        
        if self.resources:
            filters["resource"] = {"$in": self.resources}
        
        if self.actions:
            filters["action"] = {"$in": self.actions}
        
        if self.outcomes:
            filters["outcome"] = {"$in": [o.value for o in self.outcomes]}
        
        if self.levels:
            filters["level"] = {"$in": [l.value for l in self.levels]}
        
        if self.start_time:
            filters["timestamp"] = filters.get("timestamp", {})
            filters["timestamp"]["$gte"] = self.start_time.isoformat()
        
        if self.end_time:
            filters["timestamp"] = filters.get("timestamp", {})
            filters["timestamp"]["$lte"] = self.end_time.isoformat()
        
        if self.request_id:
            filters["request_id"] = self.request_id
        
        if self.session_id:
            filters["session_id"] = self.session_id
        
        return filters


class AuditLogger:
    """
    Comprehensive audit logging system with multiple backends and compliance features.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize audit logger.
        
        Args:
            config: Configuration with keys:
                - storage: Storage backend for audit logs
                - enabled: Whether audit logging is enabled
                - buffer_size: Size of event buffer before flush
                - flush_interval: Interval to flush buffered events
                - retention_days: Days to retain audit logs
                - compliance_mode: Enable additional compliance features
                - excluded_events: Event types to exclude from logging
                - excluded_users: User IDs to exclude from logging
        """
        self.config = config
        self.storage: BaseStorage = config.get("storage")
        self.enabled = config.get("enabled", True)
        self.buffer_size = config.get("buffer_size", 100)
        self.flush_interval = config.get("flush_interval", 30)
        self.retention_days = config.get("retention_days", 365)
        self.compliance_mode = config.get("compliance_mode", False)
        self.excluded_events = set(config.get("excluded_events", []))
        self.excluded_users = set(config.get("excluded_users", []))
        
        if not self.storage:
            raise ValueError("Storage backend is required for audit logger")
        
        # Event buffer
        self._event_buffer: List[AuditEvent] = []
        self._buffer_lock = asyncio.Lock()
        
        # Background tasks
        self._flush_task: Optional[asyncio.Task] = None
        self._cleanup_task: Optional[asyncio.Task] = None
        self._running = False
        
        # Statistics
        self._events_logged = 0
        self._events_dropped = 0
        self._last_flush_time: Optional[datetime] = None
    
    async def initialize(self) -> None:
        """Initialize audit logger and storage."""
        try:
            # Ensure audit logs table exists
            await self.storage.create_table("audit_logs", {
                "id": "UUID PRIMARY KEY",
                "event_type": "VARCHAR(50) NOT NULL",
                "user_id": "UUID",
                "resource": "VARCHAR(255)",
                "action": "VARCHAR(100)",
                "outcome": "VARCHAR(20) NOT NULL",
                "level": "VARCHAR(20) NOT NULL",
                "details": "JSONB DEFAULT '{}'",
                "request_id": "VARCHAR(128)",
                "session_id": "VARCHAR(128)",
                "remote_ip": "INET",
                "user_agent": "TEXT",
                "timestamp": "TIMESTAMP NOT NULL DEFAULT NOW()",
                "INDEX(user_id)": "",
                "INDEX(event_type)": "",
                "INDEX(timestamp)": "",
                "INDEX(outcome)": "",
                "INDEX(level)": ""
            })
            
            logger.info("Audit logger initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize audit logger: {e}")
            raise
    
    async def start(self) -> None:
        """Start audit logger and background tasks."""
        try:
            if not self.enabled:
                logger.info("Audit logging disabled")
                return
            
            # Initialize storage
            await self.initialize()
            
            # Start background tasks
            self._running = True
            self._flush_task = asyncio.create_task(self._flush_worker())
            self._cleanup_task = asyncio.create_task(self._cleanup_worker())
            
            logger.info("Audit logger started")
            
        except Exception as e:
            logger.error(f"Failed to start audit logger: {e}")
            raise
    
    async def stop(self) -> None:
        """Stop audit logger and flush remaining events."""
        self._running = False
        
        # Cancel background tasks
        if self._flush_task:
            self._flush_task.cancel()
            try:
                await self._flush_task
            except asyncio.CancelledError:
                pass
        
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
        
        # Flush remaining events
        await self._flush_events()
        
        logger.info("Audit logger stopped")
    
    async def log_event(
        self,
        event_type: Union[AuditEventType, str],
        user_id: Optional[UUID] = None,
        resource: Optional[str] = None,
        action: Optional[str] = None,
        outcome: Union[AuditOutcome, str] = AuditOutcome.SUCCESS,
        level: Union[AuditLevel, str] = AuditLevel.MEDIUM,
        details: Optional[Dict[str, Any]] = None,
        request_id: Optional[str] = None,
        session_id: Optional[str] = None,
        remote_ip: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> None:
        """
        Log an audit event.
        
        Args:
            event_type: Type of event
            user_id: User ID associated with event
            resource: Resource being accessed/modified
            action: Action being performed
            outcome: Event outcome
            level: Audit level
            details: Additional event details
            request_id: Request ID for correlation
            session_id: Session ID for tracking
            remote_ip: Remote IP address
            user_agent: User agent string
        """
        try:
            if not self.enabled:
                return
            
            # Check exclusions
            if isinstance(event_type, str):
                event_type = AuditEventType(event_type)
            
            if event_type.value in self.excluded_events:
                return
            
            if user_id and str(user_id) in self.excluded_users:
                return
            
            # Create audit event
            event = AuditEvent(
                event_type=event_type,
                user_id=user_id,
                resource=resource,
                action=action,
                outcome=outcome,
                level=level,
                details=details,
                request_id=request_id,
                session_id=session_id,
                remote_ip=remote_ip,
                user_agent=user_agent
            )
            
            # Add to buffer
            await self._add_to_buffer(event)
            
        except Exception as e:
            logger.error(f"Failed to log audit event: {e}")
            self._events_dropped += 1
    
    async def _add_to_buffer(self, event: AuditEvent) -> None:
        """Add event to buffer and flush if necessary."""
        async with self._buffer_lock:
            self._event_buffer.append(event)
            
            # Flush if buffer is full
            if len(self._event_buffer) >= self.buffer_size:
                await self._flush_events()
    
    async def _flush_events(self) -> None:
        """Flush buffered events to storage."""
        async with self._buffer_lock:
            if not self._event_buffer:
                return
            
            try:
                # Prepare batch data
                batch_data = []
                for event in self._event_buffer:
                    event_data = event.to_dict()
                    batch_data.append(event_data)
                
                # Insert batch
                for event_data in batch_data:
                    await self.storage.insert("audit_logs", event_data)
                
                self._events_logged += len(batch_data)
                self._last_flush_time = datetime.utcnow()
                
                # Clear buffer
                self._event_buffer.clear()
                
                logger.debug(f"Flushed {len(batch_data)} audit events")
                
            except Exception as e:
                logger.error(f"Failed to flush audit events: {e}")
                self._events_dropped += len(self._event_buffer)
                self._event_buffer.clear()
    
    async def _flush_worker(self) -> None:
        """Background worker for periodic event flushing."""
        while self._running:
            try:
                await asyncio.sleep(self.flush_interval)
                
                if not self._running:
                    break
                
                await self._flush_events()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in audit flush worker: {e}")
                await asyncio.sleep(5)
    
    async def _cleanup_worker(self) -> None:
        """Background worker for cleaning up old audit logs."""
        while self._running:
            try:
                # Run cleanup daily
                await asyncio.sleep(86400)  # 24 hours
                
                if not self._running:
                    break
                
                await self._cleanup_old_events()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in audit cleanup worker: {e}")
                await asyncio.sleep(3600)  # Retry in 1 hour
    
    async def _cleanup_old_events(self) -> None:
        """Clean up audit events older than retention period."""
        try:
            # For SQLite compatibility, skip time-based cleanup
            # TODO: Implement proper time-based cleanup for non-SQLite backends
            logger.info("Audit event cleanup skipped for SQLite compatibility")
                
        except Exception as e:
            logger.error(f"Failed to cleanup old audit events: {e}")
    
    async def search_events(
        self,
        filter: Optional[AuditFilter] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[AuditEvent]:
        """
        Search audit events with filtering.
        
        Args:
            filter: Audit filter for searching
            limit: Maximum number of events to return
            offset: Offset for pagination
            
        Returns:
            List of matching audit events
        """
        try:
            # Build filter - use simple dict for SQLite compatibility
            if filter:
                # For now, simplified filter for SQLite compatibility
                # TODO: Add proper filter translation for different storage backends
                storage_filter = {}
                if filter.request_id:
                    storage_filter["request_id"] = filter.request_id
                if filter.session_id:
                    storage_filter["session_id"] = filter.session_id
                
                # Handle list parameters by taking first item (SQLite limitation)
                if filter.event_types:
                    storage_filter["event_type"] = filter.event_types[0].value
                if filter.user_ids:
                    storage_filter["user_id"] = str(filter.user_ids[0])
            else:
                storage_filter = {}
            
            # Query events
            events_data = await self.storage.select(
                "audit_logs",
                filters=storage_filter,
                limit=limit,
                offset=offset,
                order_by="timestamp DESC"
            )
            
            # Convert to AuditEvent objects
            events = []
            for event_data in events_data:
                event = AuditEvent.from_dict(event_data)
                events.append(event)
            
            return events
            
        except Exception as e:
            logger.error(f"Failed to search audit events: {e}")
            return []
    
    async def get_user_activity(
        self,
        user_id: UUID,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100
    ) -> List[AuditEvent]:
        """
        Get audit events for a specific user.
        
        Args:
            user_id: User ID
            start_time: Start time for filtering (currently ignored for SQLite compatibility)
            end_time: End time for filtering (currently ignored for SQLite compatibility)
            limit: Maximum number of events
            
        Returns:
            List of user's audit events
        """
        # Use simple user ID filter for SQLite compatibility
        # TODO: Add proper time filtering for non-SQLite backends
        filter = AuditFilter(user_ids=[user_id])
        
        return await self.search_events(filter, limit=limit)
    
    async def get_security_events(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        level: Optional[AuditLevel] = None
    ) -> List[AuditEvent]:
        """
        Get security-related audit events.
        
        Args:
            start_time: Start time for filtering (currently ignored for SQLite compatibility)
            end_time: End time for filtering (currently ignored for SQLite compatibility)
            level: Minimum audit level (currently ignored for SQLite compatibility)
            
        Returns:
            List of security events
        """
        security_event_types = [
            AuditEventType.AUTHENTICATION,
            AuditEventType.AUTHORIZATION,
            AuditEventType.SECURITY_EVENT
        ]
        
        # Use simple event type filter for SQLite compatibility
        # TODO: Add proper time and level filtering for non-SQLite backends
        filter = AuditFilter(event_types=security_event_types)
        
        return await self.search_events(filter, limit=1000)
    
    async def get_compliance_report(
        self,
        start_time: datetime,
        end_time: datetime
    ) -> Dict[str, Any]:
        """
        Generate compliance report for a time period.
        
        Args:
            start_time: Report start time (currently ignored for SQLite compatibility)
            end_time: Report end time (currently ignored for SQLite compatibility)
            
        Returns:
            Compliance report data
        """
        try:
            # Use no filter for SQLite compatibility
            # TODO: Add proper time filtering for non-SQLite backends
            events = await self.search_events(filter=None, limit=10000)
            
            # Analyze events
            report = {
                "period": {
                    "start": start_time.isoformat(),
                    "end": end_time.isoformat()
                },
                "total_events": len(events),
                "events_by_type": {},
                "events_by_outcome": {},
                "events_by_level": {},
                "unique_users": set(),
                "unique_resources": set(),
                "security_incidents": [],
                "failed_authentications": 0,
                "unauthorized_access_attempts": 0
            }
            
            for event in events:
                # Count by type
                event_type = event.event_type.value
                report["events_by_type"][event_type] = report["events_by_type"].get(event_type, 0) + 1
                
                # Count by outcome
                outcome = event.outcome.value
                report["events_by_outcome"][outcome] = report["events_by_outcome"].get(outcome, 0) + 1
                
                # Count by level
                level = event.level.value
                report["events_by_level"][level] = report["events_by_level"].get(level, 0) + 1
                
                # Track users and resources
                if event.user_id:
                    report["unique_users"].add(str(event.user_id))
                if event.resource:
                    report["unique_resources"].add(event.resource)
                
                # Identify security incidents
                if event.level in [AuditLevel.HIGH, AuditLevel.CRITICAL]:
                    report["security_incidents"].append(event.to_dict())
                
                # Count specific security events
                if (event.event_type == AuditEventType.AUTHENTICATION and 
                    event.outcome == AuditOutcome.FAILURE):
                    report["failed_authentications"] += 1
                
                if (event.event_type == AuditEventType.AUTHORIZATION and 
                    event.outcome in [AuditOutcome.FAILURE, AuditOutcome.BLOCKED]):
                    report["unauthorized_access_attempts"] += 1
            
            # Convert sets to counts
            report["unique_users"] = len(report["unique_users"])
            report["unique_resources"] = len(report["unique_resources"])
            
            return report
            
        except Exception as e:
            logger.error(f"Failed to generate compliance report: {e}")
            return {}
    
    async def get_statistics(self) -> Dict[str, Any]:
        """
        Get audit logger statistics.
        
        Returns:
            Statistics dictionary
        """
        return {
            "enabled": self.enabled,
            "running": self._running,
            "events_logged": self._events_logged,
            "events_dropped": self._events_dropped,
            "buffer_size": len(self._event_buffer),
            "last_flush_time": self._last_flush_time.isoformat() if self._last_flush_time else None,
            "configuration": {
                "buffer_size": self.buffer_size,
                "flush_interval": self.flush_interval,
                "retention_days": self.retention_days,
                "compliance_mode": self.compliance_mode
            }
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on audit logger.
        
        Returns:
            Health status information
        """
        try:
            # Test storage connectivity
            await self.storage.ping()
            
            # Check recent activity with simple query (no time filters for SQLite compatibility)
            recent_events = await self.search_events(
                filter=None,  # Use no filter to avoid SQLite compatibility issues
                limit=1
            )
            
            return {
                "healthy": True,
                "storage_connected": True,
                "recent_activity": len(recent_events) > 0,
                "buffer_size": len(self._event_buffer),
                "stats": await self.get_statistics()
            }
            
        except Exception as e:
            logger.error(f"Audit logger health check failed: {e}")
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


# Convenience functions for common audit events

async def log_authentication_event(
    audit_logger: AuditLogger,
    user_id: Optional[UUID],
    success: bool,
    auth_method: str,
    remote_ip: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None
) -> None:
    """Log authentication event."""
    await audit_logger.log_event(
        event_type=AuditEventType.AUTHENTICATION,
        user_id=user_id,
        action=f"login_{auth_method}",
        outcome=AuditOutcome.SUCCESS if success else AuditOutcome.FAILURE,
        level=AuditLevel.MEDIUM if success else AuditLevel.HIGH,
        remote_ip=remote_ip,
        details=details or {"auth_method": auth_method}
    )


async def log_authorization_event(
    audit_logger: AuditLogger,
    user_id: UUID,
    resource: str,
    action: str,
    allowed: bool,
    remote_ip: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None
) -> None:
    """Log authorization event."""
    await audit_logger.log_event(
        event_type=AuditEventType.AUTHORIZATION,
        user_id=user_id,
        resource=resource,
        action=action,
        outcome=AuditOutcome.SUCCESS if allowed else AuditOutcome.BLOCKED,
        level=AuditLevel.LOW if allowed else AuditLevel.MEDIUM,
        remote_ip=remote_ip,
        details=details
    )


async def log_data_access_event(
    audit_logger: AuditLogger,
    user_id: UUID,
    resource: str,
    action: str = "read",
    details: Optional[Dict[str, Any]] = None
) -> None:
    """Log data access event."""
    await audit_logger.log_event(
        event_type=AuditEventType.DATA_ACCESS,
        user_id=user_id,
        resource=resource,
        action=action,
        outcome=AuditOutcome.SUCCESS,
        level=AuditLevel.LOW,
        details=details
    )