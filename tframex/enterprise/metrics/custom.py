"""
Custom Metrics Collector

This module provides a framework for implementing custom metrics
backends that can integrate with proprietary or specialized
monitoring systems.
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, List, Optional

from .base import MetricsCollector, MetricEvent, MetricType

logger = logging.getLogger(__name__)


class CustomMetricsBackend(ABC):
    """
    Abstract base class for custom metrics backends.
    
    Users can implement this interface to create custom metrics
    backends that integrate with their existing monitoring infrastructure.
    """
    
    @abstractmethod
    async def initialize(self, config: Dict[str, Any]) -> None:
        """
        Initialize the custom metrics backend.
        
        Args:
            config: Backend configuration dictionary
        """
        pass
    
    @abstractmethod
    async def send_metric(self, metric: MetricEvent) -> None:
        """
        Send a metric to the custom backend.
        
        Args:
            metric: Metric event to send
        """
        pass
    
    @abstractmethod
    async def send_batch(self, metrics: List[MetricEvent]) -> None:
        """
        Send a batch of metrics to the custom backend.
        
        Args:
            metrics: List of metric events to send
        """
        pass
    
    @abstractmethod
    async def shutdown(self) -> None:
        """
        Shutdown the custom metrics backend.
        """
        pass
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform a health check on the custom backend.
        
        Returns:
            Health status information
        """
        return {"healthy": True, "backend": self.__class__.__name__}


class CustomMetricsCollector(MetricsCollector):
    """
    Custom metrics collector that delegates to user-provided backends.
    
    This collector allows users to implement their own metrics backends
    while leveraging the TFrameX metrics collection infrastructure.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize custom metrics collector.
        
        Args:
            config: Configuration dictionary with keys:
                - backend_class: Custom backend class or instance
                - backend_config: Configuration for the custom backend
                - transform_func: Optional function to transform metrics
                - filter_func: Optional function to filter metrics
        """
        super().__init__(config)
        
        self.backend_class = config.get("backend_class")
        self.backend_config = config.get("backend_config", {})
        self.transform_func = config.get("transform_func")
        self.filter_func = config.get("filter_func")
        
        self._backend: Optional[CustomMetricsBackend] = None
        
        if not self.backend_class:
            raise ValueError("backend_class is required for custom metrics collector")
    
    async def initialize(self) -> None:
        """
        Initialize the custom metrics collector and backend.
        """
        try:
            # Resolve backend class from string if needed
            if isinstance(self.backend_class, str):
                if self.backend_class == "tframex.enterprise.metrics.custom.LoggingMetricsBackend":
                    # Use local LoggingMetricsBackend
                    backend_class = LoggingMetricsBackend
                else:
                    # Try to import the class dynamically
                    module_name, class_name = self.backend_class.rsplit('.', 1)
                    import importlib
                    module = importlib.import_module(module_name)
                    backend_class = getattr(module, class_name)
            else:
                backend_class = self.backend_class
            
            # Create backend instance if class was provided
            if isinstance(backend_class, type):
                self._backend = backend_class()
            else:
                self._backend = backend_class
            
            if not isinstance(self._backend, CustomMetricsBackend):
                raise TypeError(
                    "Backend must implement CustomMetricsBackend interface"
                )
            
            # Initialize the backend
            await self._backend.initialize(self.backend_config)
            
            logger.info(f"Custom metrics collector initialized with backend: {self._backend.__class__.__name__}")
            
        except Exception as e:
            logger.error(f"Failed to initialize custom metrics collector: {e}")
            raise
    
    async def shutdown(self) -> None:
        """
        Shutdown the custom metrics collector.
        """
        try:
            if self._backend:
                await self._backend.shutdown()
            
            logger.info("Custom metrics collector shutdown")
            
        except Exception as e:
            logger.error(f"Error during custom metrics shutdown: {e}")
    
    async def send_metric(self, metric: MetricEvent) -> None:
        """
        Send metric to custom backend with optional transformation and filtering.
        
        Args:
            metric: Metric event to send
        """
        try:
            if not self._backend:
                logger.warning("Custom metrics backend not initialized")
                return
            
            # Apply filter if configured
            if self.filter_func and not self.filter_func(metric):
                return
            
            # Apply transformation if configured
            processed_metric = metric
            if self.transform_func:
                processed_metric = self.transform_func(metric)
                if not processed_metric:
                    return
            
            # Send to backend
            await self._backend.send_metric(processed_metric)
            
        except Exception as e:
            logger.error(f"Failed to send metric {metric.name} to custom backend: {e}")
            raise
    
    async def _send_batch(self, metrics: List[MetricEvent]) -> None:
        """
        Send batch of metrics to custom backend.
        
        Args:
            metrics: List of metrics to send
        """
        try:
            if not self._backend:
                logger.warning("Custom metrics backend not initialized")
                return
            
            # Apply filtering and transformation
            processed_metrics = []
            for metric in metrics:
                # Apply filter if configured
                if self.filter_func and not self.filter_func(metric):
                    continue
                
                # Apply transformation if configured
                processed_metric = metric
                if self.transform_func:
                    processed_metric = self.transform_func(metric)
                    if not processed_metric:
                        continue
                
                processed_metrics.append(processed_metric)
            
            # Send batch to backend
            if processed_metrics:
                await self._backend.send_batch(processed_metrics)
            
        except Exception as e:
            logger.error(f"Failed to send metrics batch to custom backend: {e}")
            raise
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on custom metrics collector.
        
        Returns:
            Health status information
        """
        base_health = await super().health_check()
        
        if self._backend:
            try:
                backend_health = await self._backend.health_check()
                base_health.update(backend_health)
            except Exception as e:
                base_health["backend_health_error"] = str(e)
        else:
            base_health["backend_initialized"] = False
        
        return base_health


# Example custom backend implementations

class LoggingMetricsBackend(CustomMetricsBackend):
    """
    Example custom backend that logs metrics to a file or logger.
    
    This is useful for debugging or simple metric collection scenarios.
    """
    
    def __init__(self):
        self.logger = logging.getLogger("tframex.metrics.custom.logging")
        self.file_handler: Optional[logging.FileHandler] = None
    
    async def initialize(self, config: Dict[str, Any]) -> None:
        """
        Initialize logging backend.
        
        Args:
            config: Configuration with optional 'log_file' key
        """
        log_file = config.get("log_file")
        log_level = config.get("log_level", "INFO")
        
        # Set log level
        self.logger.setLevel(getattr(logging, log_level.upper()))
        
        # Add file handler if specified
        if log_file:
            self.file_handler = logging.FileHandler(log_file)
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            self.file_handler.setFormatter(formatter)
            self.logger.addHandler(self.file_handler)
        
        self.logger.info("Logging metrics backend initialized")
    
    async def send_metric(self, metric: MetricEvent) -> None:
        """Log a single metric."""
        metric_data = metric.to_dict()
        self.logger.info(f"METRIC: {metric_data}")
    
    async def send_batch(self, metrics: List[MetricEvent]) -> None:
        """Log a batch of metrics."""
        for metric in metrics:
            await self.send_metric(metric)
    
    async def shutdown(self) -> None:
        """Shutdown logging backend."""
        if self.file_handler:
            self.file_handler.close()
            self.logger.removeHandler(self.file_handler)
        
        self.logger.info("Logging metrics backend shutdown")


class DatabaseMetricsBackend(CustomMetricsBackend):
    """
    Example custom backend that stores metrics in a database.
    
    This demonstrates how to implement persistence for metrics data.
    """
    
    def __init__(self):
        self.storage = None
        self.table_name = "custom_metrics"
    
    async def initialize(self, config: Dict[str, Any]) -> None:
        """
        Initialize database backend.
        
        Args:
            config: Configuration with 'storage' key containing storage instance
        """
        self.storage = config.get("storage")
        self.table_name = config.get("table_name", "custom_metrics")
        
        if not self.storage:
            raise ValueError("Storage instance required for database metrics backend")
        
        # Ensure table exists
        await self.storage.create_table(self.table_name, {
            "id": "UUID PRIMARY KEY",
            "metric_name": "VARCHAR(255) NOT NULL",
            "metric_type": "VARCHAR(50) NOT NULL",
            "value": "DECIMAL",
            "labels": "JSONB",
            "timestamp": "TIMESTAMP DEFAULT NOW()",
            "unit": "VARCHAR(50)",
            "description": "TEXT"
        })
        
        logger.info("Database metrics backend initialized")
    
    async def send_metric(self, metric: MetricEvent) -> None:
        """Store a single metric in database."""
        if not self.storage:
            raise RuntimeError("Storage not initialized")
        
        metric_data = {
            "metric_name": metric.name,
            "metric_type": metric.type.value,
            "value": float(metric.value),
            "labels": metric.labels,
            "timestamp": metric.timestamp.isoformat() if metric.timestamp else None,
            "unit": metric.unit,
            "description": metric.description
        }
        
        await self.storage.insert(self.table_name, metric_data)
    
    async def send_batch(self, metrics: List[MetricEvent]) -> None:
        """Store a batch of metrics in database."""
        if not self.storage:
            raise RuntimeError("Storage not initialized")
        
        # Prepare batch data
        batch_data = []
        for metric in metrics:
            metric_data = {
                "metric_name": metric.name,
                "metric_type": metric.type.value,
                "value": float(metric.value),
                "labels": metric.labels,
                "timestamp": metric.timestamp.isoformat() if metric.timestamp else None,
                "unit": metric.unit,
                "description": metric.description
            }
            batch_data.append(metric_data)
        
        # Insert batch (using individual inserts for simplicity)
        for data in batch_data:
            await self.storage.insert(self.table_name, data)
    
    async def shutdown(self) -> None:
        """Shutdown database backend."""
        logger.info("Database metrics backend shutdown")
    
    async def health_check(self) -> Dict[str, Any]:
        """Check database backend health."""
        health = await super().health_check()
        
        if self.storage:
            try:
                # Test database connectivity
                await self.storage.ping()
                health["database_connected"] = True
                
                # Get metrics count
                count = await self.storage.count(self.table_name)
                health["stored_metrics_count"] = count
                
            except Exception as e:
                health["database_connected"] = False
                health["database_error"] = str(e)
        else:
            health["database_connected"] = False
        
        return health


class WebhookMetricsBackend(CustomMetricsBackend):
    """
    Example custom backend that sends metrics to a webhook endpoint.
    
    This is useful for integrating with external systems or APIs.
    """
    
    def __init__(self):
        self.webhook_url: Optional[str] = None
        self.headers: Dict[str, str] = {}
        self.http_client = None
    
    async def initialize(self, config: Dict[str, Any]) -> None:
        """
        Initialize webhook backend.
        
        Args:
            config: Configuration with 'webhook_url' and optional 'headers'
        """
        import aiohttp
        
        self.webhook_url = config.get("webhook_url")
        self.headers = config.get("headers", {})
        
        if not self.webhook_url:
            raise ValueError("webhook_url is required for webhook metrics backend")
        
        # Set default headers
        if "Content-Type" not in self.headers:
            self.headers["Content-Type"] = "application/json"
        
        # Create HTTP client
        self.http_client = aiohttp.ClientSession()
        
        logger.info(f"Webhook metrics backend initialized: {self.webhook_url}")
    
    async def send_metric(self, metric: MetricEvent) -> None:
        """Send a single metric to webhook."""
        if not self.http_client or not self.webhook_url:
            raise RuntimeError("Webhook backend not initialized")
        
        payload = {
            "metrics": [metric.to_dict()],
            "timestamp": metric.timestamp.isoformat() if metric.timestamp else None
        }
        
        async with self.http_client.post(
            self.webhook_url,
            json=payload,
            headers=self.headers
        ) as response:
            if response.status >= 400:
                logger.error(f"Webhook request failed: {response.status}")
    
    async def send_batch(self, metrics: List[MetricEvent]) -> None:
        """Send a batch of metrics to webhook."""
        if not self.http_client or not self.webhook_url:
            raise RuntimeError("Webhook backend not initialized")
        
        payload = {
            "metrics": [metric.to_dict() for metric in metrics],
            "batch_size": len(metrics),
            "timestamp": metrics[0].timestamp.isoformat() if metrics else None
        }
        
        async with self.http_client.post(
            self.webhook_url,
            json=payload,
            headers=self.headers
        ) as response:
            if response.status >= 400:
                logger.error(f"Webhook batch request failed: {response.status}")
    
    async def shutdown(self) -> None:
        """Shutdown webhook backend."""
        if self.http_client:
            await self.http_client.close()
        
        logger.info("Webhook metrics backend shutdown")
    
    async def health_check(self) -> Dict[str, Any]:
        """Check webhook backend health."""
        health = await super().health_check()
        health["webhook_url"] = self.webhook_url
        
        # Test webhook connectivity
        if self.http_client and self.webhook_url:
            try:
                async with self.http_client.get(self.webhook_url, timeout=5) as response:
                    health["webhook_reachable"] = True
                    health["webhook_status"] = response.status
            except Exception as e:
                health["webhook_reachable"] = False
                health["webhook_error"] = str(e)
        
        return health


# Utility functions for creating custom metrics configurations

def create_logging_config(log_file: Optional[str] = None, log_level: str = "INFO") -> Dict[str, Any]:
    """
    Create configuration for logging metrics backend.
    
    Args:
        log_file: Optional log file path
        log_level: Log level (DEBUG, INFO, WARNING, ERROR)
        
    Returns:
        Configuration dictionary
    """
    return {
        "backend_class": LoggingMetricsBackend,
        "backend_config": {
            "log_file": log_file,
            "log_level": log_level
        }
    }


def create_database_config(storage, table_name: str = "custom_metrics") -> Dict[str, Any]:
    """
    Create configuration for database metrics backend.
    
    Args:
        storage: Storage instance
        table_name: Database table name
        
    Returns:
        Configuration dictionary
    """
    return {
        "backend_class": DatabaseMetricsBackend,
        "backend_config": {
            "storage": storage,
            "table_name": table_name
        }
    }


def create_webhook_config(webhook_url: str, headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    """
    Create configuration for webhook metrics backend.
    
    Args:
        webhook_url: Webhook endpoint URL
        headers: Optional HTTP headers
        
    Returns:
        Configuration dictionary
    """
    return {
        "backend_class": WebhookMetricsBackend,
        "backend_config": {
            "webhook_url": webhook_url,
            "headers": headers or {}
        }
    }