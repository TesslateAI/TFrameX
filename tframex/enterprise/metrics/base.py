"""
Base Metrics Classes

This module defines the abstract base classes and data structures
for the metrics collection system.
"""

import asyncio
import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union

logger = logging.getLogger(__name__)


class MetricType(str, Enum):
    """Enumeration of supported metric types."""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    TIMER = "timer"
    SET = "set"


@dataclass
class MetricEvent:
    """
    Represents a metric event to be collected.
    """
    name: str
    type: MetricType
    value: Union[int, float]
    labels: Dict[str, str] = field(default_factory=dict)
    timestamp: Optional[datetime] = None
    unit: Optional[str] = None
    description: Optional[str] = None
    
    def __post_init__(self):
        """Set default timestamp if not provided."""
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert metric event to dictionary."""
        return {
            "name": self.name,
            "type": self.type.value,
            "value": self.value,
            "labels": self.labels,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "unit": self.unit,
            "description": self.description
        }


class MetricsCollector(ABC):
    """
    Abstract base class for all metrics collectors.
    
    Metrics collectors are responsible for receiving metric events
    and forwarding them to specific monitoring backends like
    Prometheus, StatsD, OpenTelemetry, etc.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the metrics collector.
        
        Args:
            config: Backend-specific configuration
        """
        self.config = config
        self.enabled = config.get("enabled", True)
        self._running = False
        self._metrics_queue: asyncio.Queue = asyncio.Queue()
        self._worker_task: Optional[asyncio.Task] = None
        self._stats = {
            "metrics_collected": 0,
            "metrics_sent": 0,
            "errors": 0,
            "last_error": None
        }
    
    @abstractmethod
    async def initialize(self) -> None:
        """
        Initialize the metrics collector backend.
        
        This method should establish connections, validate configuration,
        and prepare the collector for receiving metrics.
        """
        pass
    
    @abstractmethod
    async def shutdown(self) -> None:
        """
        Shutdown the metrics collector and cleanup resources.
        """
        pass
    
    @abstractmethod
    async def send_metric(self, metric: MetricEvent) -> None:
        """
        Send a metric event to the backend.
        
        Args:
            metric: Metric event to send
        """
        pass
    
    async def collect(self, metric: MetricEvent) -> None:
        """
        Collect a metric event for processing.
        
        Args:
            metric: Metric event to collect
        """
        if not self.enabled:
            return
        
        try:
            await self._metrics_queue.put(metric)
            self._stats["metrics_collected"] += 1
        except Exception as e:
            logger.error(f"Failed to queue metric {metric.name}: {e}")
            self._stats["errors"] += 1
            self._stats["last_error"] = str(e)
    
    async def start(self) -> None:
        """
        Start the metrics collector worker.
        """
        if self._running:
            return
        
        try:
            await self.initialize()
            self._running = True
            self._worker_task = asyncio.create_task(self._worker())
            logger.info(f"Started {self.__class__.__name__}")
        except Exception as e:
            logger.error(f"Failed to start {self.__class__.__name__}: {e}")
            raise
    
    async def stop(self) -> None:
        """
        Stop the metrics collector worker.
        """
        if not self._running:
            return
        
        self._running = False
        
        if self._worker_task:
            self._worker_task.cancel()
            try:
                await self._worker_task
            except asyncio.CancelledError:
                pass
            self._worker_task = None
        
        await self.shutdown()
        logger.info(f"Stopped {self.__class__.__name__}")
    
    async def _worker(self) -> None:
        """
        Background worker that processes metric events.
        """
        batch_size = self.config.get("batch_size", 10)
        batch_timeout = self.config.get("batch_timeout", 5.0)
        
        while self._running:
            try:
                metrics_batch = []
                batch_start = time.time()
                
                # Collect metrics for batch processing
                while (
                    len(metrics_batch) < batch_size and
                    (time.time() - batch_start) < batch_timeout and
                    self._running
                ):
                    try:
                        metric = await asyncio.wait_for(
                            self._metrics_queue.get(),
                            timeout=batch_timeout
                        )
                        metrics_batch.append(metric)
                    except asyncio.TimeoutError:
                        break
                
                # Send batch if we have metrics
                if metrics_batch:
                    await self._send_batch(metrics_batch)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in metrics worker: {e}")
                self._stats["errors"] += 1
                self._stats["last_error"] = str(e)
                await asyncio.sleep(1)  # Brief pause before retrying
    
    async def _send_batch(self, metrics: List[MetricEvent]) -> None:
        """
        Send a batch of metrics to the backend.
        
        Args:
            metrics: List of metrics to send
        """
        try:
            for metric in metrics:
                await self.send_metric(metric)
                self._stats["metrics_sent"] += 1
        except Exception as e:
            logger.error(f"Failed to send metrics batch: {e}")
            self._stats["errors"] += 1
            self._stats["last_error"] = str(e)
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get collector statistics.
        
        Returns:
            Dictionary with collector statistics
        """
        return {
            **self._stats,
            "enabled": self.enabled,
            "running": self._running,
            "queue_size": self._metrics_queue.qsize(),
            "backend": self.__class__.__name__
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on the metrics collector.
        
        Returns:
            Health status information
        """
        return {
            "healthy": self._running and self.enabled,
            "backend": self.__class__.__name__,
            "stats": self.get_stats(),
            "timestamp": datetime.utcnow().isoformat()
        }


class MetricTimer:
    """
    Context manager for timing operations and automatically
    recording the duration as a metric.
    """
    
    def __init__(
        self,
        collector: MetricsCollector,
        metric_name: str,
        labels: Optional[Dict[str, str]] = None,
        unit: str = "seconds"
    ):
        """
        Initialize metric timer.
        
        Args:
            collector: Metrics collector to send timing data to
            metric_name: Name of the timing metric
            labels: Optional labels for the metric
            unit: Unit of measurement (default: seconds)
        """
        self.collector = collector
        self.metric_name = metric_name
        self.labels = labels or {}
        self.unit = unit
        self.start_time: Optional[float] = None
    
    async def __aenter__(self):
        """Start timing."""
        self.start_time = time.time()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Stop timing and record metric."""
        if self.start_time is not None:
            duration = time.time() - self.start_time
            
            # Add error label if exception occurred
            labels = dict(self.labels)
            if exc_type is not None:
                labels["error"] = "true"
                labels["error_type"] = exc_type.__name__
            else:
                labels["error"] = "false"
            
            # Record timing metric
            metric = MetricEvent(
                name=self.metric_name,
                type=MetricType.TIMER,
                value=duration,
                labels=labels,
                unit=self.unit
            )
            
            await self.collector.collect(metric)


class MetricDecorator:
    """
    Decorator for automatically collecting metrics on function calls.
    """
    
    def __init__(
        self,
        collector: MetricsCollector,
        metric_name: Optional[str] = None,
        labels: Optional[Dict[str, str]] = None,
        record_duration: bool = True,
        record_calls: bool = True
    ):
        """
        Initialize metric decorator.
        
        Args:
            collector: Metrics collector to send data to
            metric_name: Base name for metrics (defaults to function name)
            labels: Optional labels for all metrics
            record_duration: Whether to record function duration
            record_calls: Whether to record function call count
        """
        self.collector = collector
        self.metric_name = metric_name
        self.labels = labels or {}
        self.record_duration = record_duration
        self.record_calls = record_calls
    
    def __call__(self, func):
        """Apply decorator to function."""
        metric_name = self.metric_name or f"function.{func.__name__}"
        
        if asyncio.iscoroutinefunction(func):
            async def async_wrapper(*args, **kwargs):
                # Record function call
                if self.record_calls:
                    call_metric = MetricEvent(
                        name=f"{metric_name}.calls",
                        type=MetricType.COUNTER,
                        value=1,
                        labels=self.labels
                    )
                    await self.collector.collect(call_metric)
                
                # Time function execution
                if self.record_duration:
                    async with MetricTimer(
                        self.collector,
                        f"{metric_name}.duration",
                        self.labels
                    ):
                        return await func(*args, **kwargs)
                else:
                    return await func(*args, **kwargs)
            
            return async_wrapper
        else:
            def sync_wrapper(*args, **kwargs):
                # For sync functions, we can't use async collectors directly
                # This would need to be handled differently in a real implementation
                return func(*args, **kwargs)
            
            return sync_wrapper


# Utility functions for common metric patterns

async def increment_counter(
    collector: MetricsCollector,
    name: str,
    value: Union[int, float] = 1,
    labels: Optional[Dict[str, str]] = None
) -> None:
    """
    Increment a counter metric.
    
    Args:
        collector: Metrics collector
        name: Metric name
        value: Value to increment by
        labels: Optional metric labels
    """
    metric = MetricEvent(
        name=name,
        type=MetricType.COUNTER,
        value=value,
        labels=labels or {}
    )
    await collector.collect(metric)


async def set_gauge(
    collector: MetricsCollector,
    name: str,
    value: Union[int, float],
    labels: Optional[Dict[str, str]] = None
) -> None:
    """
    Set a gauge metric value.
    
    Args:
        collector: Metrics collector
        name: Metric name
        value: Gauge value
        labels: Optional metric labels
    """
    metric = MetricEvent(
        name=name,
        type=MetricType.GAUGE,
        value=value,
        labels=labels or {}
    )
    await collector.collect(metric)


async def record_histogram(
    collector: MetricsCollector,
    name: str,
    value: Union[int, float],
    labels: Optional[Dict[str, str]] = None
) -> None:
    """
    Record a histogram metric observation.
    
    Args:
        collector: Metrics collector
        name: Metric name
        value: Observed value
        labels: Optional metric labels
    """
    metric = MetricEvent(
        name=name,
        type=MetricType.HISTOGRAM,
        value=value,
        labels=labels or {}
    )
    await collector.collect(metric)