"""
Enterprise Workflow Tracing

This module provides comprehensive distributed tracing capabilities
for multi-agent workflows with full observability and analytics.
"""

import asyncio
import json
import logging
import time
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Union
from uuid import uuid4

try:
    from opentelemetry import trace
    from opentelemetry.trace import Status, StatusCode
    OTEL_AVAILABLE = True
except ImportError:
    OTEL_AVAILABLE = False

from .models import User
from .storage.base import BaseStorage

logger = logging.getLogger(__name__)


@dataclass
class SpanInfo:
    """Information about a single span in a workflow trace."""
    span_id: str
    parent_span_id: Optional[str]
    operation_name: str
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_ms: Optional[float] = None
    status: str = "running"  # running, success, error
    tags: Dict[str, Any] = field(default_factory=dict)
    logs: List[Dict[str, Any]] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert span info to dictionary."""
        return {
            "span_id": self.span_id,
            "parent_span_id": self.parent_span_id,
            "operation_name": self.operation_name,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration_ms": self.duration_ms,
            "status": self.status,
            "tags": self.tags,
            "logs": self.logs
        }


@dataclass
class WorkflowTrace:
    """Complete workflow trace containing all spans and metadata."""
    trace_id: str
    workflow_name: str
    user_id: Optional[str]
    start_time: datetime
    end_time: Optional[datetime] = None
    status: str = "running"  # running, success, error, cancelled
    spans: List[SpanInfo] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert workflow trace to dictionary."""
        return {
            "trace_id": self.trace_id,
            "workflow_name": self.workflow_name,
            "user_id": self.user_id,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "status": self.status,
            "spans": [span.to_dict() for span in self.spans],
            "metadata": self.metadata
        }


class WorkflowTracer:
    """
    Enterprise workflow tracer with comprehensive distributed tracing.
    
    Provides complete observability for multi-agent workflows including:
    - Agent execution tracing
    - Tool call tracing
    - Flow execution tracing
    - Performance metrics
    - Error tracking
    - Cost analysis
    """
    
    def __init__(self, storage: Optional[BaseStorage] = None, 
                 enable_opentelemetry: bool = True):
        """
        Initialize workflow tracer.
        
        Args:
            storage: Storage backend for persisting traces
            enable_opentelemetry: Whether to integrate with OpenTelemetry
        """
        self.storage = storage
        self.enable_opentelemetry = enable_opentelemetry and OTEL_AVAILABLE
        self._active_traces: Dict[str, WorkflowTrace] = {}
        self._active_spans: Dict[str, SpanInfo] = {}
        
        if self.enable_opentelemetry:
            self.tracer = trace.get_tracer(__name__)
        else:
            self.tracer = None
        
        logger.info(f"Workflow tracer initialized (OpenTelemetry: {self.enable_opentelemetry})")
    
    async def start_workflow_trace(self, workflow_name: str, 
                                 user: Optional[User] = None,
                                 metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Start a new workflow trace.
        
        Args:
            workflow_name: Name of the workflow being traced
            user: User executing the workflow
            metadata: Additional metadata for the trace
            
        Returns:
            Trace ID for the new workflow trace
        """
        trace_id = str(uuid4())
        
        workflow_trace = WorkflowTrace(
            trace_id=trace_id,
            workflow_name=workflow_name,
            user_id=str(user.id) if user else None,
            start_time=datetime.now(timezone.utc),
            metadata=metadata or {}
        )
        
        self._active_traces[trace_id] = workflow_trace
        
        logger.debug(f"Started workflow trace: {trace_id} ({workflow_name})")
        return trace_id
    
    async def finish_workflow_trace(self, trace_id: str, 
                                  status: str = "success",
                                  error: Optional[Exception] = None) -> None:
        """
        Finish a workflow trace.
        
        Args:
            trace_id: ID of the trace to finish
            status: Final status of the workflow
            error: Error that occurred (if any)
        """
        if trace_id not in self._active_traces:
            logger.warning(f"Attempted to finish unknown trace: {trace_id}")
            return
        
        workflow_trace = self._active_traces[trace_id]
        workflow_trace.end_time = datetime.now(timezone.utc)
        workflow_trace.status = status
        
        if error:
            workflow_trace.metadata["error"] = {
                "type": error.__class__.__name__,
                "message": str(error)
            }
        
        # Persist trace if storage is available
        if self.storage:
            try:
                await self.storage.insert("workflow_traces", workflow_trace.to_dict())
            except Exception as e:
                logger.error(f"Failed to persist workflow trace: {e}")
        
        # Remove from active traces
        del self._active_traces[trace_id]
        
        logger.debug(f"Finished workflow trace: {trace_id} (status: {status})")
    
    @asynccontextmanager
    async def trace_operation(self, trace_id: str, operation_name: str,
                            parent_span_id: Optional[str] = None,
                            tags: Optional[Dict[str, Any]] = None):
        """
        Context manager for tracing individual operations within a workflow.
        
        Args:
            trace_id: ID of the parent workflow trace
            operation_name: Name of the operation being traced
            parent_span_id: ID of the parent span (if any)
            tags: Additional tags for the span
        """
        span_id = str(uuid4())
        start_time = datetime.now(timezone.utc)
        
        span_info = SpanInfo(
            span_id=span_id,
            parent_span_id=parent_span_id,
            operation_name=operation_name,
            start_time=start_time,
            tags=tags or {}
        )
        
        self._active_spans[span_id] = span_info
        
        # Add span to workflow trace
        if trace_id in self._active_traces:
            self._active_traces[trace_id].spans.append(span_info)
        
        # Start OpenTelemetry span if available
        otel_span = None
        if self.tracer:
            otel_span = self.tracer.start_span(operation_name)
            if tags:
                for key, value in tags.items():
                    otel_span.set_attribute(key, str(value))
        
        try:
            yield span_info
            
            # Mark span as successful
            span_info.status = "success"
            if otel_span:
                otel_span.set_status(Status(StatusCode.OK))
                
        except Exception as e:
            # Mark span as error
            span_info.status = "error"
            span_info.tags["error"] = {
                "type": e.__class__.__name__,
                "message": str(e)
            }
            
            if otel_span:
                otel_span.set_status(Status(StatusCode.ERROR, str(e)))
            
            raise
            
        finally:
            # Finish span
            end_time = datetime.now(timezone.utc)
            span_info.end_time = end_time
            span_info.duration_ms = (end_time - start_time).total_seconds() * 1000
            
            if otel_span:
                otel_span.end()
            
            # Remove from active spans
            if span_id in self._active_spans:
                del self._active_spans[span_id]
    
    async def add_span_log(self, span_id: str, message: str, 
                          level: str = "info", **kwargs) -> None:
        """
        Add a log entry to a span.
        
        Args:
            span_id: ID of the span to add log to
            message: Log message
            level: Log level (debug, info, warning, error)
            **kwargs: Additional log fields
        """
        if span_id not in self._active_spans:
            return
        
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": level,
            "message": message,
            **kwargs
        }
        
        self._active_spans[span_id].logs.append(log_entry)
    
    async def get_workflow_trace(self, trace_id: str) -> Optional[WorkflowTrace]:
        """
        Get a workflow trace by ID.
        
        Args:
            trace_id: ID of the trace to retrieve
            
        Returns:
            Workflow trace if found, None otherwise
        """
        # Check active traces first
        if trace_id in self._active_traces:
            return self._active_traces[trace_id]
        
        # Check storage
        if self.storage:
            try:
                records = await self.storage.select(
                    "workflow_traces",
                    filters={"trace_id": trace_id}
                )
                if records:
                    # Convert back to WorkflowTrace object
                    data = records[0]
                    return WorkflowTrace(
                        trace_id=data["trace_id"],
                        workflow_name=data["workflow_name"],
                        user_id=data.get("user_id"),
                        start_time=datetime.fromisoformat(data["start_time"]),
                        end_time=datetime.fromisoformat(data["end_time"]) if data.get("end_time") else None,
                        status=data["status"],
                        spans=[SpanInfo(**span) for span in data.get("spans", [])],
                        metadata=data.get("metadata", {})
                    )
            except Exception as e:
                logger.error(f"Failed to retrieve workflow trace: {e}")
        
        return None
    
    async def search_workflow_traces(self, 
                                   workflow_name: Optional[str] = None,
                                   user_id: Optional[str] = None,
                                   status: Optional[str] = None,
                                   start_time: Optional[datetime] = None,
                                   end_time: Optional[datetime] = None,
                                   limit: int = 100) -> List[WorkflowTrace]:
        """
        Search for workflow traces.
        
        Args:
            workflow_name: Filter by workflow name
            user_id: Filter by user ID
            status: Filter by status
            start_time: Filter by start time (after)
            end_time: Filter by end time (before)
            limit: Maximum number of traces to return
            
        Returns:
            List of matching workflow traces
        """
        if not self.storage:
            return []
        
        try:
            filters = {}
            if workflow_name:
                filters["workflow_name"] = workflow_name
            if user_id:
                filters["user_id"] = user_id
            if status:
                filters["status"] = status
            
            records = await self.storage.select(
                "workflow_traces",
                filters=filters,
                limit=limit
            )
            
            traces = []
            for data in records:
                # Apply time filters
                trace_start = datetime.fromisoformat(data["start_time"])
                if start_time and trace_start < start_time:
                    continue
                if end_time and trace_start > end_time:
                    continue
                
                traces.append(WorkflowTrace(
                    trace_id=data["trace_id"],
                    workflow_name=data["workflow_name"],
                    user_id=data.get("user_id"),
                    start_time=trace_start,
                    end_time=datetime.fromisoformat(data["end_time"]) if data.get("end_time") else None,
                    status=data["status"],
                    spans=[SpanInfo(**span) for span in data.get("spans", [])],
                    metadata=data.get("metadata", {})
                ))
            
            return traces
            
        except Exception as e:
            logger.error(f"Failed to search workflow traces: {e}")
            return []
    
    async def get_workflow_analytics(self, 
                                   workflow_name: Optional[str] = None,
                                   time_window_hours: int = 24) -> Dict[str, Any]:
        """
        Get analytics for workflow executions.
        
        Args:
            workflow_name: Specific workflow to analyze (or all if None)
            time_window_hours: Time window for analysis
            
        Returns:
            Analytics data including performance metrics, success rates, etc.
        """
        if not self.storage:
            return {}
        
        try:
            since_time = datetime.now(timezone.utc) - timedelta(hours=time_window_hours)
            
            traces = await self.search_workflow_traces(
                workflow_name=workflow_name,
                start_time=since_time
            )
            
            if not traces:
                return {"message": "No traces found for the specified criteria"}
            
            # Calculate analytics
            total_traces = len(traces)
            successful_traces = len([t for t in traces if t.status == "success"])
            failed_traces = len([t for t in traces if t.status == "error"])
            
            durations = []
            for trace in traces:
                if trace.end_time:
                    duration = (trace.end_time - trace.start_time).total_seconds() * 1000
                    durations.append(duration)
            
            analytics = {
                "summary": {
                    "total_executions": total_traces,
                    "success_rate": (successful_traces / total_traces * 100) if total_traces > 0 else 0,
                    "failure_rate": (failed_traces / total_traces * 100) if total_traces > 0 else 0,
                    "time_window_hours": time_window_hours
                },
                "performance": {
                    "avg_duration_ms": sum(durations) / len(durations) if durations else 0,
                    "min_duration_ms": min(durations) if durations else 0,
                    "max_duration_ms": max(durations) if durations else 0,
                    "median_duration_ms": sorted(durations)[len(durations)//2] if durations else 0
                },
                "workflows": {}
            }
            
            # Per-workflow breakdown
            workflow_stats = {}
            for trace in traces:
                wf_name = trace.workflow_name
                if wf_name not in workflow_stats:
                    workflow_stats[wf_name] = {
                        "total": 0, "success": 0, "error": 0, "durations": []
                    }
                
                workflow_stats[wf_name]["total"] += 1
                if trace.status == "success":
                    workflow_stats[wf_name]["success"] += 1
                elif trace.status == "error":
                    workflow_stats[wf_name]["error"] += 1
                
                if trace.end_time:
                    duration = (trace.end_time - trace.start_time).total_seconds() * 1000
                    workflow_stats[wf_name]["durations"].append(duration)
            
            for wf_name, stats in workflow_stats.items():
                success_rate = (stats["success"] / stats["total"] * 100) if stats["total"] > 0 else 0
                avg_duration = sum(stats["durations"]) / len(stats["durations"]) if stats["durations"] else 0
                
                analytics["workflows"][wf_name] = {
                    "executions": stats["total"],
                    "success_rate": success_rate,
                    "avg_duration_ms": avg_duration
                }
            
            return analytics
            
        except Exception as e:
            logger.error(f"Failed to get workflow analytics: {e}")
            return {"error": str(e)}


def trace_workflow(workflow_name: str, tracer: Optional[WorkflowTracer] = None):
    """
    Decorator for automatically tracing workflow functions.
    
    Args:
        workflow_name: Name of the workflow
        tracer: Workflow tracer instance (uses global if not provided)
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            if tracer is None:
                # Execute without tracing if no tracer available
                return await func(*args, **kwargs)
            
            # Extract user from arguments if available
            user = kwargs.get('user') or (args[0] if args and hasattr(args[0], 'user') else None)
            
            trace_id = await tracer.start_workflow_trace(
                workflow_name=workflow_name,
                user=user,
                metadata={"function": func.__name__}
            )
            
            try:
                async with tracer.trace_operation(
                    trace_id=trace_id,
                    operation_name=f"workflow:{workflow_name}",
                    tags={"function": func.__name__}
                ):
                    result = await func(*args, **kwargs)
                    await tracer.finish_workflow_trace(trace_id, "success")
                    return result
                    
            except Exception as e:
                await tracer.finish_workflow_trace(trace_id, "error", e)
                raise
        
        return wrapper
    return decorator