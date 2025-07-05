# tframex/mcp/notifications.py
"""
Enhanced MCP notification handling for TFrameX.
Provides real-time capability updates and change notifications.
"""
import asyncio
import json
import logging
from typing import Dict, Any, List, Optional, Callable, Union
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger("tframex.mcp.notifications")


class NotificationType(Enum):
    """MCP notification types."""
    # Resource notifications
    RESOURCES_LIST_CHANGED = "notifications/resources/list_changed"
    
    # Tool notifications  
    TOOLS_LIST_CHANGED = "notifications/tools/list_changed"
    
    # Prompt notifications
    PROMPTS_LIST_CHANGED = "notifications/prompts/list_changed"
    
    # Root notifications (client-side)
    ROOTS_LIST_CHANGED = "notifications/roots/list_changed"
    
    # Progress notifications
    PROGRESS = "notifications/progress"
    
    # Log notifications
    LOG_MESSAGE = "notifications/log"
    
    # Custom notifications
    CUSTOM = "notifications/custom"


@dataclass
class Notification:
    """Represents an MCP notification."""
    method: str
    params: Optional[Dict[str, Any]] = None
    
    @property
    def notification_type(self) -> Optional[NotificationType]:
        """Get the notification type enum if recognized."""
        try:
            return NotificationType(self.method)
        except ValueError:
            return NotificationType.CUSTOM


@dataclass
class ProgressNotification:
    """Progress notification data."""
    operation_id: str
    progress: float  # 0.0 to 1.0
    message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class LogNotification:
    """Log message notification data."""
    level: str  # "debug", "info", "warning", "error"
    message: str
    logger_name: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class NotificationHandler:
    """Base class for notification handlers."""
    
    async def handle(self, notification: Notification) -> None:
        """Handle a notification. Override in subclasses."""
        pass


class NotificationDispatcher:
    """
    Dispatches MCP notifications to appropriate handlers.
    Central hub for all notification processing.
    """
    
    def __init__(self):
        """Initialize the notification dispatcher."""
        self._handlers: Dict[NotificationType, List[NotificationHandler]] = {
            notification_type: [] for notification_type in NotificationType
        }
        self._global_handlers: List[Callable] = []
        self._notification_queue: asyncio.Queue = asyncio.Queue()
        self._dispatcher_task: Optional[asyncio.Task] = None
        self._running = False
        self._stats = {
            "total_notifications": 0,
            "notifications_by_type": {},
            "errors": 0
        }
    
    def register_handler(self, notification_type: NotificationType, 
                        handler: NotificationHandler) -> None:
        """Register a handler for a specific notification type."""
        self._handlers[notification_type].append(handler)
        logger.debug(f"Registered handler for {notification_type.value}")
    
    def register_global_handler(self, handler: Callable) -> None:
        """Register a handler that receives all notifications."""
        self._global_handlers.append(handler)
    
    async def dispatch(self, notification: Notification) -> None:
        """
        Dispatch a notification to registered handlers.
        Non-blocking - adds to queue for processing.
        """
        await self._notification_queue.put(notification)
    
    async def start(self) -> None:
        """Start the notification dispatcher."""
        if self._running:
            logger.warning("Notification dispatcher already running")
            return
        
        self._running = True
        self._dispatcher_task = asyncio.create_task(self._dispatch_loop())
        logger.info("Notification dispatcher started")
    
    async def stop(self) -> None:
        """Stop the notification dispatcher."""
        self._running = False
        
        if self._dispatcher_task:
            # Add sentinel to wake up dispatcher
            await self._notification_queue.put(None)
            
            try:
                await asyncio.wait_for(self._dispatcher_task, timeout=5.0)
            except asyncio.TimeoutError:
                logger.warning("Notification dispatcher stop timeout")
                self._dispatcher_task.cancel()
            
            self._dispatcher_task = None
        
        logger.info("Notification dispatcher stopped")
    
    async def _dispatch_loop(self) -> None:
        """Main dispatch loop."""
        while self._running:
            try:
                # Get notification from queue
                notification = await self._notification_queue.get()
                
                # Check for stop sentinel
                if notification is None:
                    break
                
                # Update stats
                self._stats["total_notifications"] += 1
                notification_type = notification.notification_type
                if notification_type:
                    type_key = notification_type.value
                    self._stats["notifications_by_type"][type_key] = \
                        self._stats["notifications_by_type"].get(type_key, 0) + 1
                
                # Dispatch to handlers
                await self._process_notification(notification)
                
            except Exception as e:
                logger.error(f"Error in notification dispatch loop: {e}", exc_info=True)
                self._stats["errors"] += 1
    
    async def _process_notification(self, notification: Notification) -> None:
        """Process a single notification."""
        # Dispatch to global handlers
        for handler in self._global_handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(notification)
                else:
                    handler(notification)
            except Exception as e:
                logger.error(f"Global notification handler error: {e}", exc_info=True)
        
        # Dispatch to type-specific handlers
        notification_type = notification.notification_type
        if notification_type and notification_type in self._handlers:
            for handler in self._handlers[notification_type]:
                try:
                    await handler.handle(notification)
                except Exception as e:
                    logger.error(f"Notification handler error for {notification_type.value}: {e}", 
                               exc_info=True)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get notification statistics."""
        return dict(self._stats)


class NotificationParser:
    """Parses raw MCP protocol messages into notifications."""
    
    @staticmethod
    def parse_message(message: Union[str, bytes, Dict[str, Any]]) -> Optional[Notification]:
        """
        Parse a raw message into a notification.
        
        Args:
            message: Raw message (JSON string, bytes, or dict)
            
        Returns:
            Notification if valid, None otherwise
        """
        try:
            # Parse JSON if needed
            if isinstance(message, (str, bytes)):
                data = json.loads(message)
            else:
                data = message
            
            # Check if it's a notification (no id field)
            if "id" in data:
                return None  # It's a request or response, not a notification
            
            # Validate JSON-RPC 2.0 format
            if data.get("jsonrpc") != "2.0":
                logger.warning(f"Invalid JSON-RPC version: {data.get('jsonrpc')}")
                return None
            
            # Extract method and params
            method = data.get("method")
            if not method:
                logger.warning("Notification missing method")
                return None
            
            params = data.get("params")
            
            return Notification(method=method, params=params)
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse notification JSON: {e}")
            return None
        except Exception as e:
            logger.error(f"Error parsing notification: {e}", exc_info=True)
            return None


# Built-in notification handlers

class ToolsChangedHandler(NotificationHandler):
    """Handles tool list change notifications."""
    
    def __init__(self, callback: Callable):
        self.callback = callback
    
    async def handle(self, notification: Notification) -> None:
        """Handle tools list changed notification."""
        logger.info("Tools list changed notification received")
        await self.callback()


class ResourcesChangedHandler(NotificationHandler):
    """Handles resource list change notifications."""
    
    def __init__(self, callback: Callable):
        self.callback = callback
    
    async def handle(self, notification: Notification) -> None:
        """Handle resources list changed notification."""
        logger.info("Resources list changed notification received")
        await self.callback()


class PromptsChangedHandler(NotificationHandler):
    """Handles prompt list change notifications."""
    
    def __init__(self, callback: Callable):
        self.callback = callback
    
    async def handle(self, notification: Notification) -> None:
        """Handle prompts list changed notification."""
        logger.info("Prompts list changed notification received")
        await self.callback()


class ProgressHandler(NotificationHandler):
    """Handles progress notifications."""
    
    def __init__(self, progress_callback: Optional[Callable] = None):
        self.progress_callback = progress_callback
        self.active_operations: Dict[str, ProgressNotification] = {}
    
    async def handle(self, notification: Notification) -> None:
        """Handle progress notification."""
        if not notification.params:
            return
        
        params = notification.params
        progress_notif = ProgressNotification(
            operation_id=params.get("operationId", "unknown"),
            progress=params.get("progress", 0.0),
            message=params.get("message"),
            metadata=params.get("metadata")
        )
        
        # Track active operations
        if progress_notif.progress >= 1.0:
            self.active_operations.pop(progress_notif.operation_id, None)
        else:
            self.active_operations[progress_notif.operation_id] = progress_notif
        
        # Call callback if provided
        if self.progress_callback:
            await self.progress_callback(progress_notif)
        
        logger.debug(f"Progress: {progress_notif.operation_id} - "
                    f"{progress_notif.progress*100:.1f}% - {progress_notif.message}")


class LogHandler(NotificationHandler):
    """Handles log message notifications from servers."""
    
    def __init__(self, forward_to_logger: bool = True):
        self.forward_to_logger = forward_to_logger
        self.log_history: List[LogNotification] = []
        self.max_history = 1000
    
    async def handle(self, notification: Notification) -> None:
        """Handle log notification."""
        if not notification.params:
            return
        
        params = notification.params
        log_notif = LogNotification(
            level=params.get("level", "info"),
            message=params.get("message", ""),
            logger_name=params.get("logger"),
            metadata=params.get("metadata")
        )
        
        # Add to history
        self.log_history.append(log_notif)
        if len(self.log_history) > self.max_history:
            self.log_history.pop(0)
        
        # Forward to Python logger if enabled
        if self.forward_to_logger:
            server_logger = logging.getLogger(
                f"mcp.server.{log_notif.logger_name or 'unknown'}"
            )
            
            level_map = {
                "debug": logging.DEBUG,
                "info": logging.INFO,
                "warning": logging.WARNING,
                "error": logging.ERROR
            }
            
            log_level = level_map.get(log_notif.level, logging.INFO)
            server_logger.log(log_level, log_notif.message, 
                            extra={"mcp_metadata": log_notif.metadata})