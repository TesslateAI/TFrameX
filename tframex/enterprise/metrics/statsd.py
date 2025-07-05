"""
StatsD Metrics Collector

This module provides StatsD integration for real-time metric streaming
to StatsD-compatible servers like Graphite, InfluxDB, or DataDog.
"""

import asyncio
import logging
import socket
from typing import Any, Dict, Optional

from .base import MetricsCollector, MetricEvent, MetricType

logger = logging.getLogger(__name__)


class StatsDCollector(MetricsCollector):
    """
    StatsD metrics collector that sends metrics to a StatsD server
    over UDP for real-time monitoring and alerting.
    
    Supports standard StatsD metric types: counters, gauges, timers,
    histograms, and sets.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize StatsD collector.
        
        Args:
            config: Configuration dictionary with keys:
                - host: StatsD server host (default: "localhost")
                - port: StatsD server port (default: 8125)
                - prefix: Metric name prefix
                - tags_format: Tag format ("datadog", "telegraf", or "none")
                - sample_rate: Default sample rate (0.0 to 1.0)
                - socket_timeout: Socket timeout in seconds
                - max_udp_size: Maximum UDP packet size
        """
        super().__init__(config)
        
        self.host = config.get("host", "localhost")
        self.port = config.get("port", 8125)
        self.prefix = config.get("prefix", "tframex")
        self.tags_format = config.get("tags_format", "datadog")  # datadog, telegraf, none
        self.sample_rate = config.get("sample_rate", 1.0)
        self.socket_timeout = config.get("socket_timeout", 5.0)
        self.max_udp_size = config.get("max_udp_size", 1400)
        
        self._socket: Optional[socket.socket] = None
        self._connected = False
    
    async def initialize(self) -> None:
        """
        Initialize StatsD collector and create UDP socket.
        """
        try:
            # Create UDP socket
            self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self._socket.settimeout(self.socket_timeout)
            
            # Test connection by sending a test metric
            await self._send_raw_metric("tframex.statsd.connection_test:1|c")
            
            self._connected = True
            logger.info(f"StatsD collector connected to {self.host}:{self.port}")
            
        except Exception as e:
            logger.error(f"Failed to initialize StatsD collector: {e}")
            if self._socket:
                self._socket.close()
                self._socket = None
            raise
    
    async def shutdown(self) -> None:
        """
        Shutdown StatsD collector and close socket.
        """
        try:
            if self._socket:
                # Send shutdown metric
                await self._send_raw_metric("tframex.statsd.shutdown:1|c")
                
                self._socket.close()
                self._socket = None
            
            self._connected = False
            logger.info("StatsD collector shutdown")
            
        except Exception as e:
            logger.error(f"Error during StatsD shutdown: {e}")
    
    async def send_metric(self, metric: MetricEvent) -> None:
        """
        Send metric to StatsD server.
        
        Args:
            metric: Metric event to send
        """
        try:
            if not self._connected or not self._socket:
                logger.warning("StatsD collector not connected")
                return
            
            # Format metric for StatsD protocol
            metric_string = self._format_metric(metric)
            
            # Send metric
            await self._send_raw_metric(metric_string)
            
        except Exception as e:
            logger.error(f"Failed to send metric {metric.name} to StatsD: {e}")
            raise
    
    def _format_metric(self, metric: MetricEvent) -> str:
        """
        Format metric event into StatsD protocol format.
        
        Args:
            metric: Metric event to format
            
        Returns:
            StatsD formatted metric string
        """
        # Build metric name
        metric_name = self._build_metric_name(metric.name)
        
        # Format based on metric type
        if metric.type == MetricType.COUNTER:
            metric_line = f"{metric_name}:{metric.value}|c"
        
        elif metric.type == MetricType.GAUGE:
            metric_line = f"{metric_name}:{metric.value}|g"
        
        elif metric.type in [MetricType.TIMER, MetricType.HISTOGRAM]:
            # Convert to milliseconds if unit is seconds
            value = metric.value
            if metric.unit == "seconds":
                value = metric.value * 1000
            metric_line = f"{metric_name}:{value}|ms"
        
        elif metric.type == MetricType.SET:
            metric_line = f"{metric_name}:{metric.value}|s"
        
        else:
            # Default to gauge for unknown types
            metric_line = f"{metric_name}:{metric.value}|g"
        
        # Add sample rate if not 1.0
        if self.sample_rate < 1.0:
            metric_line += f"|@{self.sample_rate}"
        
        # Add tags if configured
        if metric.labels and self.tags_format != "none":
            tags_string = self._format_tags(metric.labels)
            if tags_string:
                metric_line += tags_string
        
        return metric_line
    
    def _build_metric_name(self, name: str) -> str:
        """
        Build full metric name with prefix.
        
        Args:
            name: Base metric name
            
        Returns:
            Full metric name
        """
        # Convert dots and dashes to underscores for StatsD compatibility
        clean_name = name.replace("-", "_").replace(".", "_")
        
        if self.prefix:
            return f"{self.prefix}.{clean_name}"
        else:
            return clean_name
    
    def _format_tags(self, labels: Dict[str, str]) -> str:
        """
        Format labels as tags based on configured format.
        
        Args:
            labels: Metric labels
            
        Returns:
            Formatted tags string
        """
        if not labels:
            return ""
        
        if self.tags_format == "datadog":
            # DataDog format: |#tag1:value1,tag2:value2
            tag_pairs = [f"{key}:{value}" for key, value in labels.items()]
            return f"|#{','.join(tag_pairs)}"
        
        elif self.tags_format == "telegraf":
            # Telegraf format: ;tag1=value1;tag2=value2
            tag_pairs = [f"{key}={value}" for key, value in labels.items()]
            return f";{';'.join(tag_pairs)}"
        
        else:
            return ""
    
    async def _send_raw_metric(self, metric_string: str) -> None:
        """
        Send raw metric string to StatsD server.
        
        Args:
            metric_string: StatsD formatted metric string
        """
        try:
            if not self._socket:
                raise RuntimeError("Socket not initialized")
            
            # Encode and send
            data = metric_string.encode('utf-8')
            
            # Check packet size
            if len(data) > self.max_udp_size:
                logger.warning(
                    f"Metric packet size ({len(data)}) exceeds max UDP size "
                    f"({self.max_udp_size}), truncating"
                )
                data = data[:self.max_udp_size]
            
            # Send via UDP
            await asyncio.get_event_loop().run_in_executor(
                None,
                self._socket.sendto,
                data,
                (self.host, self.port)
            )
            
        except Exception as e:
            logger.error(f"Failed to send raw metric to StatsD: {e}")
            # Try to reconnect on socket errors
            if isinstance(e, (socket.error, socket.timeout)):
                await self._reconnect()
            raise
    
    async def _reconnect(self) -> None:
        """
        Attempt to reconnect to StatsD server.
        """
        try:
            logger.info("Attempting to reconnect to StatsD server...")
            
            if self._socket:
                self._socket.close()
            
            self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self._socket.settimeout(self.socket_timeout)
            
            # Test connection
            await self._send_raw_metric("tframex.statsd.reconnection_test:1|c")
            
            self._connected = True
            logger.info("Successfully reconnected to StatsD server")
            
        except Exception as e:
            logger.error(f"Failed to reconnect to StatsD server: {e}")
            self._connected = False
            if self._socket:
                self._socket.close()
                self._socket = None
    
    async def send_batch(self, metrics: list) -> None:
        """
        Send multiple metrics in a single UDP packet for efficiency.
        
        Args:
            metrics: List of metric events to send
        """
        try:
            if not self._connected or not self._socket:
                logger.warning("StatsD collector not connected")
                return
            
            # Format all metrics
            metric_strings = []
            total_size = 0
            
            for metric in metrics:
                metric_string = self._format_metric(metric)
                metric_size = len(metric_string.encode('utf-8'))
                
                # Check if adding this metric would exceed UDP size limit
                if total_size + metric_size + 1 > self.max_udp_size:  # +1 for newline
                    # Send current batch
                    if metric_strings:
                        batch_data = '\n'.join(metric_strings)
                        await self._send_raw_metric(batch_data)
                        metric_strings = []
                        total_size = 0
                
                metric_strings.append(metric_string)
                total_size += metric_size + 1  # +1 for newline
            
            # Send remaining metrics
            if metric_strings:
                batch_data = '\n'.join(metric_strings)
                await self._send_raw_metric(batch_data)
            
        except Exception as e:
            logger.error(f"Failed to send metrics batch to StatsD: {e}")
            raise
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform health check specific to StatsD collector.
        
        Returns:
            Health status information
        """
        base_health = await super().health_check()
        
        statsd_health = {
            "connected": self._connected,
            "server": f"{self.host}:{self.port}",
            "tags_format": self.tags_format,
            "sample_rate": self.sample_rate
        }
        
        # Test connection
        try:
            if self._connected:
                await self._send_raw_metric("tframex.statsd.health_check:1|c")
                statsd_health["connectivity"] = "ok"
            else:
                statsd_health["connectivity"] = "disconnected"
        except Exception as e:
            statsd_health["connectivity"] = f"error: {e}"
        
        base_health.update(statsd_health)
        return base_health
    
    def get_connection_info(self) -> Dict[str, Any]:
        """
        Get connection information.
        
        Returns:
            Connection details
        """
        return {
            "host": self.host,
            "port": self.port,
            "connected": self._connected,
            "prefix": self.prefix,
            "tags_format": self.tags_format,
            "sample_rate": self.sample_rate,
            "socket_timeout": self.socket_timeout,
            "max_udp_size": self.max_udp_size
        }