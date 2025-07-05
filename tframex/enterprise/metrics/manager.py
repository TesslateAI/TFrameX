"""
Metrics Manager

This module provides a unified interface for managing multiple
metrics collectors and coordinating metric collection across
different backends.
"""

import asyncio
import logging
import time
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from .base import MetricsCollector, MetricEvent, MetricType, MetricTimer
from .prometheus import PrometheusCollector
from .statsd import StatsDCollector
from .opentelemetry import OpenTelemetryCollector
from .custom import CustomMetricsCollector

logger = logging.getLogger(__name__)


class MetricsManager:
    """
    Centralized manager for all metrics collection in TFrameX.
    
    The MetricsManager coordinates multiple metrics collectors,
    handles metric routing, and provides unified APIs for metric
    collection across the application.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize metrics manager.
        
        Args:
            config: Configuration dictionary with keys:
                - enabled: Whether metrics collection is enabled
                - backends: List of backend configurations
                - default_labels: Labels to add to all metrics
                - collection_interval: Metric collection interval
                - buffer_size: Internal metrics buffer size
                - error_handling: Error handling strategy ("ignore", "log", "raise")
        """
        self.config = config
        self.enabled = config.get("enabled", True)
        self.default_labels = config.get("default_labels", {})
        self.collection_interval = config.get("collection_interval", 60)
        self.buffer_size = config.get("buffer_size", 1000)
        self.error_handling = config.get("error_handling", "log")
        
        # Metrics collectors
        self._collectors: Dict[str, MetricsCollector] = {}
        self._running = False
        
        # Internal metrics tracking
        self._metrics_count = 0
        self._errors_count = 0
        self._last_collection_time: Optional[datetime] = None
        
        # Background tasks
        self._collection_task: Optional[asyncio.Task] = None
        
        # Initialize collectors from config
        self._initialize_collectors()
    
    def _initialize_collectors(self) -> None:
        """Initialize metrics collectors from configuration."""
        if not self.enabled:
            logger.info("Metrics collection disabled")
            return
        
        backends_config = self.config.get("backends", {})
        
        for backend_name, backend_config in backends_config.items():
            if not backend_config.get("enabled", True):
                continue
            
            try:
                collector = self._create_collector(backend_name, backend_config)
                if collector:
                    self._collectors[backend_name] = collector
                    logger.info(f"Initialized metrics collector: {backend_name}")
            except Exception as e:
                logger.error(f"Failed to initialize {backend_name} collector: {e}")
                if self.error_handling == "raise":
                    raise
    
    def _create_collector(self, backend_name: str, config: Dict[str, Any]) -> Optional[MetricsCollector]:
        """
        Create a metrics collector based on backend type.
        
        Args:
            backend_name: Name of the backend
            config: Backend configuration
            
        Returns:
            Metrics collector instance or None
        """
        backend_type = config.get("type", backend_name.lower())
        
        if backend_type == "prometheus":
            return PrometheusCollector(config)
        elif backend_type == "statsd":
            return StatsDCollector(config)
        elif backend_type == "opentelemetry":
            return OpenTelemetryCollector(config)
        elif backend_type == "custom":
            return CustomMetricsCollector(config)
        else:
            logger.warning(f"Unknown metrics backend type: {backend_type}")
            return None
    
    async def start(self) -> None:
        """
        Start the metrics manager and all collectors.
        """
        if not self.enabled or self._running:
            return
        
        try:
            # Start all collectors
            start_tasks = []
            for name, collector in self._collectors.items():
                try:
                    start_tasks.append(collector.start())
                except Exception as e:
                    logger.error(f"Failed to start collector {name}: {e}")
                    if self.error_handling == "raise":
                        raise
            
            if start_tasks:
                await asyncio.gather(*start_tasks, return_exceptions=True)
            
            # Start background collection task
            self._collection_task = asyncio.create_task(self._collection_worker())
            
            self._running = True
            logger.info(f"Metrics manager started with {len(self._collectors)} collectors")
            
        except Exception as e:
            logger.error(f"Failed to start metrics manager: {e}")
            raise
    
    async def stop(self) -> None:
        """
        Stop the metrics manager and all collectors.
        """
        if not self._running:
            return
        
        self._running = False
        
        # Stop background task
        if self._collection_task:
            self._collection_task.cancel()
            try:
                await self._collection_task
            except asyncio.CancelledError:
                pass
            self._collection_task = None
        
        # Stop all collectors
        stop_tasks = []
        for name, collector in self._collectors.items():
            try:
                stop_tasks.append(collector.stop())
            except Exception as e:
                logger.error(f"Error stopping collector {name}: {e}")
        
        if stop_tasks:
            await asyncio.gather(*stop_tasks, return_exceptions=True)
        
        logger.info("Metrics manager stopped")
    
    async def collect_metric(
        self,
        name: str,
        value: Union[int, float],
        metric_type: MetricType = MetricType.COUNTER,
        labels: Optional[Dict[str, str]] = None,
        unit: Optional[str] = None,
        description: Optional[str] = None,
        timestamp: Optional[datetime] = None
    ) -> None:
        """
        Collect a metric and send it to all configured backends.
        
        Args:
            name: Metric name
            value: Metric value
            metric_type: Type of metric
            labels: Metric labels
            unit: Unit of measurement
            description: Metric description
            timestamp: Metric timestamp (defaults to current time)
        """
        if not self.enabled or not self._collectors:
            return
        
        try:
            # Merge with default labels
            all_labels = {**self.default_labels, **(labels or {})}
            
            # Create metric event
            metric = MetricEvent(
                name=name,
                type=metric_type,
                value=value,
                labels=all_labels,
                timestamp=timestamp,
                unit=unit,
                description=description
            )
            
            # Send to all collectors
            await self._send_to_collectors(metric)
            
            self._metrics_count += 1
            self._last_collection_time = datetime.utcnow()
            
        except Exception as e:
            self._errors_count += 1
            logger.error(f"Failed to collect metric {name}: {e}")
            if self.error_handling == "raise":
                raise
    
    async def _send_to_collectors(self, metric: MetricEvent) -> None:
        """
        Send metric to all active collectors.
        
        Args:
            metric: Metric event to send
        """
        tasks = []
        for name, collector in self._collectors.items():
            try:
                tasks.append(collector.collect(metric))
            except Exception as e:
                logger.error(f"Error sending metric to {name}: {e}")
                if self.error_handling == "raise":
                    raise
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    async def increment_counter(
        self,
        name: str,
        value: Union[int, float] = 1,
        labels: Optional[Dict[str, str]] = None
    ) -> None:
        """
        Increment a counter metric.
        
        Args:
            name: Counter name
            value: Value to increment by
            labels: Optional labels
        """
        await self.collect_metric(
            name=name,
            value=value,
            metric_type=MetricType.COUNTER,
            labels=labels
        )
    
    async def set_gauge(
        self,
        name: str,
        value: Union[int, float],
        labels: Optional[Dict[str, str]] = None
    ) -> None:
        """
        Set a gauge metric value.
        
        Args:
            name: Gauge name
            value: Gauge value
            labels: Optional labels
        """
        await self.collect_metric(
            name=name,
            value=value,
            metric_type=MetricType.GAUGE,
            labels=labels
        )
    
    async def record_histogram(
        self,
        name: str,
        value: Union[int, float],
        labels: Optional[Dict[str, str]] = None
    ) -> None:
        """
        Record a histogram observation.
        
        Args:
            name: Histogram name
            value: Observed value
            labels: Optional labels
        """
        await self.collect_metric(
            name=name,
            value=value,
            metric_type=MetricType.HISTOGRAM,
            labels=labels
        )
    
    async def record_timer(
        self,
        name: str,
        duration: float,
        labels: Optional[Dict[str, str]] = None
    ) -> None:
        """
        Record a timing measurement.
        
        Args:
            name: Timer name
            duration: Duration in seconds
            labels: Optional labels
        """
        await self.collect_metric(
            name=name,
            value=duration,
            metric_type=MetricType.TIMER,
            labels=labels,
            unit="seconds"
        )
    
    def timer(
        self,
        name: str,
        labels: Optional[Dict[str, str]] = None
    ) -> MetricTimer:
        """
        Create a context manager for timing operations.
        
        Args:
            name: Timer name
            labels: Optional labels
            
        Returns:
            Timer context manager
        """
        return MetricTimer(
            collector=self,
            metric_name=name,
            labels=labels
        )
    
    async def _collection_worker(self) -> None:
        """
        Background worker for periodic metric collection.
        
        This worker collects internal metrics about the metrics system itself.
        """
        while self._running:
            try:
                await asyncio.sleep(self.collection_interval)
                
                if not self._running:
                    break
                
                # Collect internal metrics
                await self._collect_internal_metrics()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in metrics collection worker: {e}")
                await asyncio.sleep(5)  # Brief pause before retrying
    
    async def _collect_internal_metrics(self) -> None:
        """Collect metrics about the metrics system itself."""
        try:
            # System metrics
            await self.set_gauge(
                "tframex.metrics.collectors.count",
                len(self._collectors)
            )
            
            await self.set_gauge(
                "tframex.metrics.total_collected",
                self._metrics_count
            )
            
            await self.set_gauge(
                "tframex.metrics.errors.total",
                self._errors_count
            )
            
            # Collector-specific metrics
            for name, collector in self._collectors.items():
                try:
                    stats = collector.get_stats()
                    collector_labels = {"collector": name}
                    
                    await self.set_gauge(
                        "tframex.metrics.collector.metrics_collected",
                        stats.get("metrics_collected", 0),
                        collector_labels
                    )
                    
                    await self.set_gauge(
                        "tframex.metrics.collector.metrics_sent",
                        stats.get("metrics_sent", 0),
                        collector_labels
                    )
                    
                    await self.set_gauge(
                        "tframex.metrics.collector.errors",
                        stats.get("errors", 0),
                        collector_labels
                    )
                    
                    await self.set_gauge(
                        "tframex.metrics.collector.queue_size",
                        stats.get("queue_size", 0),
                        collector_labels
                    )
                    
                except Exception as e:
                    logger.error(f"Error collecting metrics for {name}: {e}")
        
        except Exception as e:
            logger.error(f"Error collecting internal metrics: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get comprehensive metrics manager statistics.
        
        Returns:
            Statistics dictionary
        """
        collector_stats = {}
        for name, collector in self._collectors.items():
            try:
                collector_stats[name] = collector.get_stats()
            except Exception as e:
                collector_stats[name] = {"error": str(e)}
        
        return {
            "enabled": self.enabled,
            "running": self._running,
            "collectors_count": len(self._collectors),
            "metrics_collected": self._metrics_count,
            "errors_count": self._errors_count,
            "last_collection_time": (
                self._last_collection_time.isoformat()
                if self._last_collection_time else None
            ),
            "collectors": collector_stats
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform comprehensive health check on metrics system.
        
        Returns:
            Health status information
        """
        overall_healthy = True
        collector_health = {}
        
        for name, collector in self._collectors.items():
            try:
                health = await collector.health_check()
                collector_health[name] = health
                if not health.get("healthy", False):
                    overall_healthy = False
            except Exception as e:
                collector_health[name] = {
                    "healthy": False,
                    "error": str(e)
                }
                overall_healthy = False
        
        return {
            "healthy": overall_healthy and self._running,
            "enabled": self.enabled,
            "running": self._running,
            "collectors": collector_health,
            "stats": self.get_stats(),
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def get_collector(self, name: str) -> Optional[MetricsCollector]:
        """
        Get a specific metrics collector by name.
        
        Args:
            name: Collector name
            
        Returns:
            Metrics collector or None if not found
        """
        return self._collectors.get(name)
    
    def list_collectors(self) -> List[str]:
        """
        Get list of active collector names.
        
        Returns:
            List of collector names
        """
        return list(self._collectors.keys())
    
    async def add_collector(self, name: str, collector: MetricsCollector) -> None:
        """
        Add a new metrics collector at runtime.
        
        Args:
            name: Collector name
            collector: Metrics collector instance
        """
        try:
            if self._running:
                await collector.start()
            
            self._collectors[name] = collector
            logger.info(f"Added metrics collector: {name}")
            
        except Exception as e:
            logger.error(f"Failed to add collector {name}: {e}")
            raise
    
    async def remove_collector(self, name: str) -> None:
        """
        Remove a metrics collector.
        
        Args:
            name: Collector name to remove
        """
        if name not in self._collectors:
            logger.warning(f"Collector {name} not found")
            return
        
        try:
            collector = self._collectors[name]
            await collector.stop()
            del self._collectors[name]
            logger.info(f"Removed metrics collector: {name}")
            
        except Exception as e:
            logger.error(f"Failed to remove collector {name}: {e}")
            raise
    
    # Context manager support
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.start()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.stop()