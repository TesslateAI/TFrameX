# tframex/mcp/progress.py
"""
Progress reporting and cancellation support for MCP operations.
Provides long-running operation tracking and status updates.
"""
import asyncio
import logging
import time
from typing import Dict, Any, Optional, Callable, List
from dataclasses import dataclass, field
from enum import Enum
from uuid import uuid4
import weakref

logger = logging.getLogger("tframex.mcp.progress")


class OperationStatus(Enum):
    """Status of a long-running operation."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class ProgressUpdate:
    """Represents a progress update for an operation."""
    operation_id: str
    progress: float  # 0.0 to 1.0
    message: Optional[str] = None
    status: OperationStatus = OperationStatus.RUNNING
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)


@dataclass
class Operation:
    """Represents a long-running operation."""
    id: str
    name: str
    description: Optional[str] = None
    progress: float = 0.0
    status: OperationStatus = OperationStatus.PENDING
    message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    completed_at: Optional[float] = None
    error: Optional[str] = None
    cancellation_token: Optional[asyncio.Event] = None
    progress_callback: Optional[Callable] = None
    
    def update_progress(self, progress: float, message: Optional[str] = None) -> ProgressUpdate:
        """Update operation progress."""
        self.progress = max(0.0, min(1.0, progress))
        self.message = message
        self.updated_at = time.time()
        
        if progress >= 1.0 and self.status == OperationStatus.RUNNING:
            self.status = OperationStatus.COMPLETED
            self.completed_at = time.time()
        
        return ProgressUpdate(
            operation_id=self.id,
            progress=self.progress,
            message=message,
            status=self.status,
            metadata=self.metadata,
            timestamp=self.updated_at
        )
    
    def is_cancelled(self) -> bool:
        """Check if operation was cancelled."""
        if self.cancellation_token:
            return self.cancellation_token.is_set()
        return self.status == OperationStatus.CANCELLED
    
    def cancel(self) -> None:
        """Cancel the operation."""
        self.status = OperationStatus.CANCELLED
        if self.cancellation_token:
            self.cancellation_token.set()
        self.completed_at = time.time()
    
    def fail(self, error: str) -> None:
        """Mark operation as failed."""
        self.status = OperationStatus.FAILED
        self.error = error
        self.completed_at = time.time()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "progress": self.progress,
            "status": self.status.value,
            "message": self.message,
            "metadata": self.metadata,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "completed_at": self.completed_at,
            "error": self.error
        }


class ProgressTracker:
    """
    Tracks progress of long-running operations.
    Provides operation management and progress reporting.
    """
    
    def __init__(self, 
                 max_operations: int = 1000,
                 cleanup_interval: int = 300):
        """
        Initialize progress tracker.
        
        Args:
            max_operations: Maximum tracked operations before cleanup
            cleanup_interval: Seconds between automatic cleanups
        """
        self._operations: Dict[str, Operation] = {}
        self._operation_order: List[str] = []  # For LRU cleanup
        self._max_operations = max_operations
        self._cleanup_interval = cleanup_interval
        self._cleanup_task: Optional[asyncio.Task] = None
        self._listeners: List[weakref.ref] = []
        self._lock = asyncio.Lock()
        
        # Start cleanup task
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
    
    async def create_operation(self, 
                             name: str,
                             description: Optional[str] = None,
                             metadata: Optional[Dict[str, Any]] = None,
                             progress_callback: Optional[Callable] = None) -> Operation:
        """
        Create a new tracked operation.
        
        Args:
            name: Operation name
            description: Operation description
            metadata: Additional metadata
            progress_callback: Callback for progress updates
            
        Returns:
            Operation object
        """
        async with self._lock:
            # Generate unique ID
            operation_id = str(uuid4())
            
            # Create operation
            operation = Operation(
                id=operation_id,
                name=name,
                description=description,
                metadata=metadata or {},
                cancellation_token=asyncio.Event(),
                progress_callback=progress_callback,
                status=OperationStatus.RUNNING
            )
            
            # Store operation
            self._operations[operation_id] = operation
            self._operation_order.append(operation_id)
            
            # Cleanup if needed
            if len(self._operations) > self._max_operations:
                await self._cleanup_old_operations()
            
            # Notify listeners
            await self._notify_listeners(ProgressUpdate(
                operation_id=operation_id,
                progress=0.0,
                status=OperationStatus.RUNNING,
                message=f"Started: {name}"
            ))
            
            logger.info(f"Created operation '{name}' (ID: {operation_id})")
            return operation
    
    async def update_progress(self, 
                            operation_id: str,
                            progress: float,
                            message: Optional[str] = None,
                            metadata_update: Optional[Dict[str, Any]] = None) -> bool:
        """
        Update operation progress.
        
        Args:
            operation_id: Operation ID
            progress: Progress value (0.0 to 1.0)
            message: Progress message
            metadata_update: Metadata to merge
            
        Returns:
            True if update was successful
        """
        async with self._lock:
            operation = self._operations.get(operation_id)
            if not operation:
                logger.warning(f"Operation {operation_id} not found")
                return False
            
            # Update metadata if provided
            if metadata_update:
                operation.metadata.update(metadata_update)
            
            # Update progress
            update = operation.update_progress(progress, message)
            
            # Call operation callback
            if operation.progress_callback:
                try:
                    if asyncio.iscoroutinefunction(operation.progress_callback):
                        await operation.progress_callback(update)
                    else:
                        operation.progress_callback(update)
                except Exception as e:
                    logger.error(f"Progress callback error: {e}")
            
            # Notify listeners
            await self._notify_listeners(update)
            
            return True
    
    async def complete_operation(self, 
                               operation_id: str,
                               message: Optional[str] = None) -> bool:
        """Complete an operation successfully."""
        return await self.update_progress(operation_id, 1.0, message or "Completed")
    
    async def fail_operation(self, 
                           operation_id: str,
                           error: str) -> bool:
        """Mark an operation as failed."""
        async with self._lock:
            operation = self._operations.get(operation_id)
            if not operation:
                return False
            
            operation.fail(error)
            
            # Notify
            await self._notify_listeners(ProgressUpdate(
                operation_id=operation_id,
                progress=operation.progress,
                status=OperationStatus.FAILED,
                message=error
            ))
            
            return True
    
    async def cancel_operation(self, operation_id: str) -> bool:
        """Cancel an operation."""
        async with self._lock:
            operation = self._operations.get(operation_id)
            if not operation:
                return False
            
            operation.cancel()
            
            # Notify
            await self._notify_listeners(ProgressUpdate(
                operation_id=operation_id,
                progress=operation.progress,
                status=OperationStatus.CANCELLED,
                message="Cancelled by user"
            ))
            
            logger.info(f"Cancelled operation {operation_id}")
            return True
    
    def get_operation(self, operation_id: str) -> Optional[Operation]:
        """Get operation by ID."""
        return self._operations.get(operation_id)
    
    def list_operations(self, 
                       status_filter: Optional[OperationStatus] = None,
                       limit: int = 100) -> List[Operation]:
        """
        List tracked operations.
        
        Args:
            status_filter: Filter by status
            limit: Maximum operations to return
            
        Returns:
            List of operations
        """
        operations = list(self._operations.values())
        
        # Filter by status
        if status_filter:
            operations = [op for op in operations if op.status == status_filter]
        
        # Sort by updated time (most recent first)
        operations.sort(key=lambda op: op.updated_at, reverse=True)
        
        return operations[:limit]
    
    def add_listener(self, listener: Callable) -> None:
        """Add a progress listener (weak reference)."""
        self._listeners.append(weakref.ref(listener))
    
    def remove_listener(self, listener: Callable) -> None:
        """Remove a progress listener."""
        self._listeners = [ref for ref in self._listeners 
                          if ref() is not None and ref() != listener]
    
    async def _notify_listeners(self, update: ProgressUpdate) -> None:
        """Notify all listeners of progress update."""
        # Clean up dead references
        self._listeners = [ref for ref in self._listeners if ref() is not None]
        
        # Notify active listeners
        for listener_ref in self._listeners:
            listener = listener_ref()
            if listener:
                try:
                    if asyncio.iscoroutinefunction(listener):
                        await listener(update)
                    else:
                        listener(update)
                except Exception as e:
                    logger.error(f"Progress listener error: {e}")
    
    async def _cleanup_old_operations(self) -> None:
        """Clean up old completed operations."""
        # Keep only recent and active operations
        cutoff_time = time.time() - 3600  # 1 hour
        
        to_remove = []
        for op_id in self._operation_order[:]:
            operation = self._operations.get(op_id)
            if operation and operation.status in [OperationStatus.COMPLETED, 
                                                 OperationStatus.FAILED,
                                                 OperationStatus.CANCELLED]:
                if operation.completed_at and operation.completed_at < cutoff_time:
                    to_remove.append(op_id)
        
        # Remove old operations
        for op_id in to_remove:
            del self._operations[op_id]
            self._operation_order.remove(op_id)
        
        if to_remove:
            logger.debug(f"Cleaned up {len(to_remove)} old operations")
    
    async def _cleanup_loop(self) -> None:
        """Periodic cleanup task."""
        while True:
            try:
                await asyncio.sleep(self._cleanup_interval)
                async with self._lock:
                    await self._cleanup_old_operations()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Cleanup loop error: {e}")
    
    async def shutdown(self) -> None:
        """Shutdown the progress tracker."""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
        
        # Cancel all active operations
        for operation in self._operations.values():
            if operation.status == OperationStatus.RUNNING:
                operation.cancel()
        
        self._operations.clear()
        self._listeners.clear()


class OperationContext:
    """
    Context manager for tracking operation progress.
    Provides automatic progress updates and error handling.
    """
    
    def __init__(self, 
                 tracker: ProgressTracker,
                 name: str,
                 description: Optional[str] = None,
                 total_steps: int = 100):
        """
        Initialize operation context.
        
        Args:
            tracker: Progress tracker instance
            name: Operation name
            description: Operation description
            total_steps: Total steps for progress calculation
        """
        self.tracker = tracker
        self.name = name
        self.description = description
        self.total_steps = total_steps
        self.current_step = 0
        self.operation: Optional[Operation] = None
    
    async def __aenter__(self) -> "OperationContext":
        """Enter context and create operation."""
        self.operation = await self.tracker.create_operation(
            name=self.name,
            description=self.description
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit context and finalize operation."""
        if self.operation:
            if exc_type is not None:
                # Operation failed
                error_msg = f"{exc_type.__name__}: {exc_val}"
                await self.tracker.fail_operation(self.operation.id, error_msg)
            elif self.operation.status == OperationStatus.RUNNING:
                # Complete if still running
                await self.tracker.complete_operation(self.operation.id)
    
    async def step(self, message: Optional[str] = None, steps: int = 1) -> None:
        """
        Advance operation by steps.
        
        Args:
            message: Progress message
            steps: Number of steps to advance
        """
        if not self.operation:
            return
        
        self.current_step = min(self.current_step + steps, self.total_steps)
        progress = self.current_step / self.total_steps
        
        await self.tracker.update_progress(
            self.operation.id,
            progress,
            message
        )
    
    def check_cancellation(self) -> None:
        """
        Check if operation was cancelled.
        Raises CancelledError if cancelled.
        """
        if self.operation and self.operation.is_cancelled():
            raise asyncio.CancelledError(f"Operation '{self.name}' was cancelled")