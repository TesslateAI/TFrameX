"""
Prometheus Metrics Collector

This module provides Prometheus integration for exposing metrics
via the standard Prometheus exposition format.
"""

import asyncio
import logging
from typing import Any, Dict, Optional

try:
    from prometheus_client import (
        Counter, Gauge, Histogram, Summary, CollectorRegistry,
        generate_latest, CONTENT_TYPE_LATEST, start_http_server
    )
    from prometheus_client.core import REGISTRY
    import aiohttp
    from aiohttp import web
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False

from .base import MetricsCollector, MetricEvent, MetricType

logger = logging.getLogger(__name__)


class PrometheusCollector(MetricsCollector):
    """
    Prometheus metrics collector that exposes metrics via HTTP endpoint.
    
    This collector creates Prometheus metric objects and starts an HTTP
    server to expose metrics in the Prometheus exposition format.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize Prometheus collector.
        
        Args:
            config: Configuration dictionary with keys:
                - port: HTTP server port (default: 9090)
                - host: HTTP server host (default: "0.0.0.0")
                - path: Metrics endpoint path (default: "/metrics")
                - registry: Custom Prometheus registry (optional)
                - namespace: Metric namespace prefix
                - subsystem: Metric subsystem prefix
        """
        super().__init__(config)
        
        if not PROMETHEUS_AVAILABLE:
            raise ImportError(
                "prometheus_client and aiohttp are required for Prometheus metrics. "
                "Install with: pip install prometheus_client aiohttp"
            )
        
        self.port = config.get("port", 9090)
        self.host = config.get("host", "0.0.0.0")
        self.path = config.get("path", "/metrics")
        self.namespace = config.get("namespace", "tframex")
        self.subsystem = config.get("subsystem", "")
        
        # Use custom registry or create a new one to avoid conflicts
        self.registry = config.get("registry")
        if self.registry is None:
            # Create a new registry to avoid duplicate metrics errors
            self.registry = CollectorRegistry()
        
        # Storage for Prometheus metric objects
        self._counters: Dict[str, Counter] = {}
        self._gauges: Dict[str, Gauge] = {}
        self._histograms: Dict[str, Histogram] = {}
        self._summaries: Dict[str, Summary] = {}
        
        # HTTP server components
        self._app: Optional[web.Application] = None
        self._runner: Optional[web.AppRunner] = None
        self._site: Optional[web.TCPSite] = None
    
    async def initialize(self) -> None:
        """
        Initialize Prometheus collector and start HTTP server.
        """
        try:
            # Create aiohttp application
            self._app = web.Application()
            self._app.router.add_get(self.path, self._metrics_handler)
            self._app.router.add_get("/health", self._health_handler)
            
            # Start HTTP server
            self._runner = web.AppRunner(self._app)
            await self._runner.setup()
            
            self._site = web.TCPSite(
                self._runner,
                host=self.host,
                port=self.port
            )
            await self._site.start()
            
            logger.info(
                f"Prometheus metrics server started on "
                f"http://{self.host}:{self.port}{self.path}"
            )
            
        except Exception as e:
            logger.error(f"Failed to initialize Prometheus collector: {e}")
            raise
    
    async def shutdown(self) -> None:
        """
        Shutdown Prometheus HTTP server.
        """
        try:
            if self._site:
                await self._site.stop()
                self._site = None
            
            if self._runner:
                await self._runner.cleanup()
                self._runner = None
            
            self._app = None
            
            logger.info("Prometheus metrics server stopped")
            
        except Exception as e:
            logger.error(f"Error during Prometheus shutdown: {e}")
    
    async def send_metric(self, metric: MetricEvent) -> None:
        """
        Send metric to Prometheus.
        
        Args:
            metric: Metric event to process
        """
        try:
            metric_name = self._build_metric_name(metric.name)
            label_names = list(metric.labels.keys()) if metric.labels else []
            label_values = list(metric.labels.values()) if metric.labels else []
            
            if metric.type == MetricType.COUNTER:
                counter = self._get_or_create_counter(
                    metric_name, label_names, metric.description
                )
                if label_values:
                    counter.labels(*label_values).inc(metric.value)
                else:
                    counter.inc(metric.value)
            
            elif metric.type == MetricType.GAUGE:
                gauge = self._get_or_create_gauge(
                    metric_name, label_names, metric.description
                )
                if label_values:
                    gauge.labels(*label_values).set(metric.value)
                else:
                    gauge.set(metric.value)
            
            elif metric.type == MetricType.HISTOGRAM:
                histogram = self._get_or_create_histogram(
                    metric_name, label_names, metric.description
                )
                if label_values:
                    histogram.labels(*label_values).observe(metric.value)
                else:
                    histogram.observe(metric.value)
            
            elif metric.type == MetricType.TIMER:
                # Treat timers as histograms in Prometheus
                histogram = self._get_or_create_histogram(
                    metric_name, label_names, metric.description,
                    buckets=self._get_duration_buckets()
                )
                if label_values:
                    histogram.labels(*label_values).observe(metric.value)
                else:
                    histogram.observe(metric.value)
            
            else:
                logger.warning(f"Unsupported metric type for Prometheus: {metric.type}")
        
        except Exception as e:
            logger.error(f"Failed to send metric {metric.name} to Prometheus: {e}")
            raise
    
    def _build_metric_name(self, name: str) -> str:
        """
        Build full Prometheus metric name with namespace and subsystem.
        
        Args:
            name: Base metric name
            
        Returns:
            Full metric name
        """
        parts = []
        
        if self.namespace:
            parts.append(self.namespace)
        
        if self.subsystem:
            parts.append(self.subsystem)
        
        parts.append(name.replace(".", "_").replace("-", "_"))
        
        return "_".join(parts)
    
    def _get_or_create_counter(
        self,
        name: str,
        label_names: list,
        description: Optional[str] = None
    ) -> Counter:
        """Get or create a Prometheus Counter."""
        key = f"{name}:{':'.join(label_names)}"
        
        if key not in self._counters:
            self._counters[key] = Counter(
                name=name,
                documentation=description or f"Counter metric {name}",
                labelnames=label_names,
                registry=self.registry
            )
        
        return self._counters[key]
    
    def _get_or_create_gauge(
        self,
        name: str,
        label_names: list,
        description: Optional[str] = None
    ) -> Gauge:
        """Get or create a Prometheus Gauge."""
        key = f"{name}:{':'.join(label_names)}"
        
        if key not in self._gauges:
            self._gauges[key] = Gauge(
                name=name,
                documentation=description or f"Gauge metric {name}",
                labelnames=label_names,
                registry=self.registry
            )
        
        return self._gauges[key]
    
    def _get_or_create_histogram(
        self,
        name: str,
        label_names: list,
        description: Optional[str] = None,
        buckets: Optional[tuple] = None
    ) -> Histogram:
        """Get or create a Prometheus Histogram."""
        key = f"{name}:{':'.join(label_names)}"
        
        if key not in self._histograms:
            kwargs = {
                "name": name,
                "documentation": description or f"Histogram metric {name}",
                "labelnames": label_names,
                "registry": self.registry
            }
            
            if buckets:
                kwargs["buckets"] = buckets
            
            self._histograms[key] = Histogram(**kwargs)
        
        return self._histograms[key]
    
    def _get_duration_buckets(self) -> tuple:
        """Get histogram buckets suitable for duration metrics."""
        return (
            0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5,
            1.0, 2.5, 5.0, 10.0, 25.0, 50.0, 100.0, float("inf")
        )
    
    async def _metrics_handler(self, request: web.Request) -> web.Response:
        """
        HTTP handler for metrics endpoint.
        
        Args:
            request: HTTP request
            
        Returns:
            HTTP response with Prometheus metrics
        """
        try:
            # Generate Prometheus metrics in exposition format
            metrics_data = generate_latest(self.registry)
            
            return web.Response(
                body=metrics_data,
                content_type=CONTENT_TYPE_LATEST,
                headers={
                    "Cache-Control": "no-cache, no-store, must-revalidate",
                    "Pragma": "no-cache",
                    "Expires": "0"
                }
            )
        
        except Exception as e:
            logger.error(f"Error generating Prometheus metrics: {e}")
            return web.Response(
                text=f"Error generating metrics: {e}",
                status=500
            )
    
    async def _health_handler(self, request: web.Request) -> web.Response:
        """
        HTTP handler for health check endpoint.
        
        Args:
            request: HTTP request
            
        Returns:
            HTTP response with health status
        """
        try:
            health_info = await self.health_check()
            
            return web.json_response(
                health_info,
                status=200 if health_info["healthy"] else 500
            )
        
        except Exception as e:
            logger.error(f"Error in health check: {e}")
            return web.json_response(
                {"healthy": False, "error": str(e)},
                status=500
            )
    
    def get_metric_count(self) -> int:
        """
        Get total number of registered Prometheus metrics.
        
        Returns:
            Number of metrics
        """
        return (
            len(self._counters) +
            len(self._gauges) +
            len(self._histograms) +
            len(self._summaries)
        )
    
    def clear_metrics(self) -> None:
        """
        Clear all registered metrics.
        
        Warning: This will remove all metrics from the registry.
        Use with caution in production environments.
        """
        try:
            # Clear internal metric storage
            for metric_dict in [self._counters, self._gauges, self._histograms, self._summaries]:
                for metric in metric_dict.values():
                    try:
                        self.registry.unregister(metric)
                    except KeyError:
                        pass  # Metric already unregistered
                metric_dict.clear()
            
            logger.info("Cleared all Prometheus metrics")
            
        except Exception as e:
            logger.error(f"Error clearing Prometheus metrics: {e}")
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform health check specific to Prometheus collector.
        
        Returns:
            Health status information
        """
        base_health = await super().health_check()
        
        prometheus_health = {
            "server_running": self._site is not None,
            "metrics_count": self.get_metric_count(),
            "endpoint": f"http://{self.host}:{self.port}{self.path}"
        }
        
        base_health.update(prometheus_health)
        return base_health