"""
OpenTelemetry Metrics Collector

This module provides OpenTelemetry integration for comprehensive
observability including metrics, traces, and logs.
"""

import asyncio
import logging
from typing import Any, Dict, Optional, Union

try:
    from opentelemetry import metrics, trace
    from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
    from opentelemetry.exporter.prometheus import PrometheusMetricReader
    from opentelemetry.instrumentation.requests import RequestsInstrumentor
    from opentelemetry.instrumentation.urllib3 import URLLib3Instrumentor
    from opentelemetry.sdk.metrics import MeterProvider
    from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor
    from opentelemetry.semconv.resource import ResourceAttributes
    OPENTELEMETRY_AVAILABLE = True
except ImportError:
    OPENTELEMETRY_AVAILABLE = False

from .base import MetricsCollector, MetricEvent, MetricType

logger = logging.getLogger(__name__)


class OpenTelemetryCollector(MetricsCollector):
    """
    OpenTelemetry collector for comprehensive observability including
    metrics, distributed tracing, and correlation.
    
    This collector provides:
    - Metric collection and export
    - Distributed tracing
    - Automatic instrumentation
    - Context propagation
    - Integration with OTLP-compatible backends
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize OpenTelemetry collector.
        
        Args:
            config: Configuration dictionary with keys:
                - endpoint: OTLP endpoint URL
                - service_name: Service name for identification
                - service_version: Service version
                - environment: Environment (dev, staging, prod)
                - headers: Additional headers for OTLP export
                - insecure: Whether to use insecure connection
                - export_interval: Metric export interval in seconds
                - enable_tracing: Whether to enable distributed tracing
                - enable_auto_instrumentation: Whether to enable auto instrumentation
        """
        super().__init__(config)
        
        if not OPENTELEMETRY_AVAILABLE:
            raise ImportError(
                "opentelemetry packages are required for OpenTelemetry metrics. "
                "Install with: pip install opentelemetry-api opentelemetry-sdk "
                "opentelemetry-exporter-otlp opentelemetry-instrumentation"
            )
        
        self.endpoint = config.get("endpoint", "http://localhost:4317")
        self.service_name = config.get("service_name", "tframex")
        self.service_version = config.get("service_version", "0.1.0")
        self.environment = config.get("environment", "development")
        self.headers = config.get("headers", {})
        self.insecure = config.get("insecure", True)
        self.export_interval = config.get("export_interval", 30)
        self.enable_tracing = config.get("enable_tracing", True)
        self.enable_auto_instrumentation = config.get("enable_auto_instrumentation", True)
        
        # OpenTelemetry components
        self._resource: Optional[Resource] = None
        self._meter_provider: Optional[MeterProvider] = None
        self._tracer_provider: Optional[TracerProvider] = None
        self._meter = None
        self._tracer = None
        
        # Metric instruments
        self._counters: Dict[str, Any] = {}
        self._gauges: Dict[str, Any] = {}
        self._histograms: Dict[str, Any] = {}
        
        # Span tracking for correlation
        self._active_spans: Dict[str, Any] = {}
    
    async def initialize(self) -> None:
        """
        Initialize OpenTelemetry collector with resource, providers, and exporters.
        """
        try:
            # Create resource with service information
            self._resource = Resource.create({
                ResourceAttributes.SERVICE_NAME: self.service_name,
                ResourceAttributes.SERVICE_VERSION: self.service_version,
                ResourceAttributes.DEPLOYMENT_ENVIRONMENT: self.environment,
                "telemetry.sdk.name": "tframex-enterprise",
                "telemetry.sdk.language": "python"
            })
            
            # Initialize metrics
            await self._initialize_metrics()
            
            # Initialize tracing if enabled
            if self.enable_tracing:
                await self._initialize_tracing()
            
            # Enable auto-instrumentation if configured
            if self.enable_auto_instrumentation:
                await self._setup_auto_instrumentation()
            
            logger.info(f"OpenTelemetry collector initialized with endpoint: {self.endpoint}")
            
        except Exception as e:
            logger.error(f"Failed to initialize OpenTelemetry collector: {e}")
            raise
    
    async def _initialize_metrics(self) -> None:
        """Initialize OpenTelemetry metrics provider and exporter."""
        try:
            # Create OTLP metric exporter
            otlp_exporter = OTLPMetricExporter(
                endpoint=self.endpoint,
                headers=self.headers,
                insecure=self.insecure
            )
            
            # Create periodic metric reader
            metric_reader = PeriodicExportingMetricReader(
                exporter=otlp_exporter,
                export_interval_millis=self.export_interval * 1000
            )
            
            # Create meter provider
            self._meter_provider = MeterProvider(
                resource=self._resource,
                metric_readers=[metric_reader]
            )
            
            # Set global meter provider
            metrics.set_meter_provider(self._meter_provider)
            
            # Get meter for this service
            self._meter = metrics.get_meter(
                name=self.service_name,
                version=self.service_version
            )
            
            logger.debug("OpenTelemetry metrics initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize OpenTelemetry metrics: {e}")
            raise
    
    async def _initialize_tracing(self) -> None:
        """Initialize OpenTelemetry tracing provider and exporter."""
        try:
            # Create OTLP trace exporter
            otlp_trace_exporter = OTLPSpanExporter(
                endpoint=self.endpoint,
                headers=self.headers,
                insecure=self.insecure
            )
            
            # Create span processor
            span_processor = BatchSpanProcessor(otlp_trace_exporter)
            
            # Create tracer provider
            self._tracer_provider = TracerProvider(resource=self._resource)
            self._tracer_provider.add_span_processor(span_processor)
            
            # Set global tracer provider
            trace.set_tracer_provider(self._tracer_provider)
            
            # Get tracer for this service
            self._tracer = trace.get_tracer(
                name=self.service_name,
                version=self.service_version
            )
            
            logger.debug("OpenTelemetry tracing initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize OpenTelemetry tracing: {e}")
            raise
    
    async def _setup_auto_instrumentation(self) -> None:
        """Setup automatic instrumentation for common libraries."""
        try:
            # Instrument HTTP libraries
            RequestsInstrumentor().instrument()
            URLLib3Instrumentor().instrument()
            
            logger.debug("OpenTelemetry auto-instrumentation enabled")
            
        except Exception as e:
            logger.warning(f"Failed to setup auto-instrumentation: {e}")
    
    async def shutdown(self) -> None:
        """
        Shutdown OpenTelemetry collector and force export of pending data.
        """
        try:
            # Force export of pending metrics
            if self._meter_provider:
                self._meter_provider.force_flush(timeout_millis=5000)
                self._meter_provider.shutdown(timeout_millis=5000)
            
            # Force export of pending spans
            if self._tracer_provider:
                self._tracer_provider.force_flush(timeout_millis=5000)
                self._tracer_provider.shutdown()
            
            logger.info("OpenTelemetry collector shutdown")
            
        except Exception as e:
            logger.error(f"Error during OpenTelemetry shutdown: {e}")
    
    async def send_metric(self, metric: MetricEvent) -> None:
        """
        Send metric to OpenTelemetry.
        
        Args:
            metric: Metric event to send
        """
        try:
            if not self._meter:
                logger.warning("OpenTelemetry meter not initialized")
                return
            
            # Create attributes from labels
            attributes = metric.labels or {}
            
            # Add metric source information
            attributes.update({
                "metric.source": "tframex",
                "metric.timestamp": metric.timestamp.isoformat() if metric.timestamp else ""
            })
            
            # Handle different metric types
            if metric.type == MetricType.COUNTER:
                counter = self._get_or_create_counter(metric.name, metric.description)
                counter.add(metric.value, attributes)
            
            elif metric.type == MetricType.GAUGE:
                # OpenTelemetry doesn't have gauges, use up-down counter
                gauge = self._get_or_create_gauge(metric.name, metric.description)
                gauge.add(metric.value, attributes)
            
            elif metric.type in [MetricType.HISTOGRAM, MetricType.TIMER]:
                histogram = self._get_or_create_histogram(metric.name, metric.description)
                histogram.record(metric.value, attributes)
            
            else:
                logger.warning(f"Unsupported metric type for OpenTelemetry: {metric.type}")
        
        except Exception as e:
            logger.error(f"Failed to send metric {metric.name} to OpenTelemetry: {e}")
            raise
    
    def _get_or_create_counter(self, name: str, description: Optional[str] = None):
        """Get or create an OpenTelemetry Counter."""
        if name not in self._counters:
            self._counters[name] = self._meter.create_counter(
                name=name,
                description=description or f"Counter metric {name}",
                unit="1"
            )
        return self._counters[name]
    
    def _get_or_create_gauge(self, name: str, description: Optional[str] = None):
        """Get or create an OpenTelemetry UpDownCounter (gauge equivalent)."""
        if name not in self._gauges:
            self._gauges[name] = self._meter.create_up_down_counter(
                name=name,
                description=description or f"Gauge metric {name}",
                unit="1"
            )
        return self._gauges[name]
    
    def _get_or_create_histogram(self, name: str, description: Optional[str] = None):
        """Get or create an OpenTelemetry Histogram."""
        if name not in self._histograms:
            self._histograms[name] = self._meter.create_histogram(
                name=name,
                description=description or f"Histogram metric {name}",
                unit="1"
            )
        return self._histograms[name]
    
    def start_span(
        self,
        name: str,
        attributes: Optional[Dict[str, Any]] = None,
        kind: Optional[str] = None
    ) -> Any:
        """
        Start a new OpenTelemetry span for distributed tracing.
        
        Args:
            name: Span name
            attributes: Span attributes
            kind: Span kind (server, client, internal, producer, consumer)
            
        Returns:
            OpenTelemetry span object
        """
        if not self._tracer:
            logger.warning("OpenTelemetry tracer not initialized")
            return None
        
        try:
            span = self._tracer.start_span(name)
            
            # Set attributes if provided
            if attributes:
                for key, value in attributes.items():
                    span.set_attribute(key, value)
            
            # Set span kind if provided
            if kind:
                from opentelemetry.trace import SpanKind
                span_kinds = {
                    "server": SpanKind.SERVER,
                    "client": SpanKind.CLIENT,
                    "internal": SpanKind.INTERNAL,
                    "producer": SpanKind.PRODUCER,
                    "consumer": SpanKind.CONSUMER
                }
                if kind in span_kinds:
                    span._kind = span_kinds[kind]
            
            return span
            
        except Exception as e:
            logger.error(f"Failed to start span {name}: {e}")
            return None
    
    def end_span(self, span: Any, status: Optional[str] = None, error: Optional[Exception] = None) -> None:
        """
        End an OpenTelemetry span.
        
        Args:
            span: OpenTelemetry span to end
            status: Span status (ok, error, cancelled)
            error: Exception that occurred (if any)
        """
        if not span:
            return
        
        try:
            # Set status if provided
            if status or error:
                from opentelemetry.trace import Status, StatusCode
                
                if error:
                    span.record_exception(error)
                    span.set_status(Status(StatusCode.ERROR, str(error)))
                elif status == "error":
                    span.set_status(Status(StatusCode.ERROR))
                elif status == "cancelled":
                    span.set_status(Status(StatusCode.ERROR, "Cancelled"))
                else:
                    span.set_status(Status(StatusCode.OK))
            
            span.end()
            
        except Exception as e:
            logger.error(f"Failed to end span: {e}")
    
    def trace_agent_execution(self, agent_name: str, input_message: str):
        """
        Create a context manager for tracing agent execution.
        
        Args:
            agent_name: Name of the agent being executed
            input_message: Input message to the agent
            
        Returns:
            Context manager for the span
        """
        if not self._tracer:
            return _NoOpSpanContext()
        
        return _AgentExecutionSpan(
            self,
            agent_name,
            input_message
        )
    
    def trace_tool_call(self, tool_name: str, tool_type: str, arguments: Dict[str, Any]):
        """
        Create a context manager for tracing tool calls.
        
        Args:
            tool_name: Name of the tool being called
            tool_type: Type of tool (native, mcp, agent)
            arguments: Tool arguments
            
        Returns:
            Context manager for the span
        """
        if not self._tracer:
            return _NoOpSpanContext()
        
        return _ToolCallSpan(
            self,
            tool_name,
            tool_type,
            arguments
        )
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform health check specific to OpenTelemetry collector.
        
        Returns:
            Health status information
        """
        base_health = await super().health_check()
        
        otel_health = {
            "endpoint": self.endpoint,
            "service_name": self.service_name,
            "tracing_enabled": self.enable_tracing,
            "auto_instrumentation": self.enable_auto_instrumentation,
            "meter_initialized": self._meter is not None,
            "tracer_initialized": self._tracer is not None
        }
        
        base_health.update(otel_health)
        return base_health


class _NoOpSpanContext:
    """No-op context manager when tracing is disabled."""
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass


class _AgentExecutionSpan:
    """Context manager for agent execution tracing."""
    
    def __init__(self, collector: OpenTelemetryCollector, agent_name: str, input_message: str):
        self.collector = collector
        self.agent_name = agent_name
        self.input_message = input_message
        self.span = None
    
    async def __aenter__(self):
        self.span = self.collector.start_span(
            f"agent.{self.agent_name}",
            attributes={
                "agent.name": self.agent_name,
                "agent.input_length": len(self.input_message),
                "tframex.component": "agent"
            },
            kind="internal"
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        status = "error" if exc_type else "ok"
        error = exc_val if exc_type else None
        self.collector.end_span(self.span, status, error)


class _ToolCallSpan:
    """Context manager for tool call tracing."""
    
    def __init__(
        self,
        collector: OpenTelemetryCollector,
        tool_name: str,
        tool_type: str,
        arguments: Dict[str, Any]
    ):
        self.collector = collector
        self.tool_name = tool_name
        self.tool_type = tool_type
        self.arguments = arguments
        self.span = None
    
    async def __aenter__(self):
        self.span = self.collector.start_span(
            f"tool.{self.tool_name}",
            attributes={
                "tool.name": self.tool_name,
                "tool.type": self.tool_type,
                "tool.argument_count": len(self.arguments),
                "tframex.component": "tool"
            },
            kind="internal"
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        status = "error" if exc_type else "ok"
        error = exc_val if exc_type else None
        self.collector.end_span(self.span, status, error)