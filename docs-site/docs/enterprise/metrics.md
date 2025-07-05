---
sidebar_position: 3
title: Metrics & Monitoring
---

# Metrics & Monitoring

TFrameX Enterprise provides basic metrics collection for monitoring application performance and usage through Prometheus integration.

## Overview

The metrics system includes:
- **PrometheusCollector** - HTTP server exposing metrics in Prometheus format
- **Base metrics infrastructure** - Foundation classes for building custom collectors
- **Health check endpoints** - Basic application health monitoring

## PrometheusCollector

The main metrics collector that exports metrics via HTTP in Prometheus format:

```python
from tframex.enterprise.metrics import PrometheusCollector

# Create and configure collector
collector = PrometheusCollector({
    "port": 9090,
    "host": "0.0.0.0", 
    "path": "/metrics",
    "namespace": "tframex",
    "subsystem": "app"
})

# Initialize the HTTP server
await collector.initialize()

# Metrics available at http://localhost:9090/metrics
# Health check available at http://localhost:9090/health
```

### Configuration Options

```python
config = {
    "port": 9090,           # HTTP server port (default: 9090)
    "host": "0.0.0.0",      # Host to bind to (default: "0.0.0.0") 
    "path": "/metrics",     # Metrics endpoint path (default: "/metrics")
    "namespace": "tframex", # Metric namespace prefix
    "subsystem": "",        # Metric subsystem prefix
    "registry": None        # Custom Prometheus registry (optional)
}
```

## Supported Metric Types

The PrometheusCollector supports standard Prometheus metric types:

### Counter Metrics

```python
from tframex.enterprise.metrics import MetricEvent, MetricType

# Send counter increment
await collector.send_metric(MetricEvent(
    name="requests_total",
    type=MetricType.COUNTER,
    value=1,
    labels={"method": "GET", "status": "200"},
    description="Total HTTP requests"
))
```

### Gauge Metrics

```python
# Send gauge value
await collector.send_metric(MetricEvent(
    name="memory_usage_bytes", 
    type=MetricType.GAUGE,
    value=1024000,
    labels={"instance": "app-1"},
    description="Current memory usage"
))
```

### Histogram Metrics

```python
# Send histogram observation
await collector.send_metric(MetricEvent(
    name="request_duration_seconds",
    type=MetricType.HISTOGRAM, 
    value=0.125,
    labels={"endpoint": "/api/v1/agents"},
    description="Request duration"
))
```

### Timer Metrics

```python
# Timer metrics are converted to histograms
await collector.send_metric(MetricEvent(
    name="agent_execution_time",
    type=MetricType.TIMER,
    value=1.5,  # seconds
    labels={"agent": "Assistant"},
    description="Agent execution time"
))
```

## Using with Enterprise App

```python
from tframex.enterprise import EnterpriseApp

# Configure metrics in enterprise config
config = {
    "metrics": {
        "enabled": True,
        "prometheus": {
            "port": 9090,
            "path": "/metrics"
        }
    }
}

app = EnterpriseApp(enterprise_config=config)

# Metrics are automatically configured and started
async with app.run_context() as rt:
    # Your application code
    pass
```

## Custom Metrics

Create custom metric collection:

```python
import time
from tframex.enterprise.metrics import PrometheusCollector, MetricEvent, MetricType

class ApplicationMetrics:
    def __init__(self, collector: PrometheusCollector):
        self.collector = collector
    
    async def record_agent_execution(self, agent_name: str, duration: float, success: bool):
        """Record agent execution metrics."""
        # Execution counter
        await self.collector.send_metric(MetricEvent(
            name="agent_executions_total",
            type=MetricType.COUNTER,
            value=1,
            labels={
                "agent": agent_name,
                "status": "success" if success else "error"
            },
            description="Total agent executions"
        ))
        
        # Duration histogram
        await self.collector.send_metric(MetricEvent(
            name="agent_duration_seconds",
            type=MetricType.HISTOGRAM,
            value=duration,
            labels={"agent": agent_name},
            description="Agent execution duration"
        ))
    
    async def update_active_sessions(self, count: int):
        """Update active session count."""
        await self.collector.send_metric(MetricEvent(
            name="active_sessions",
            type=MetricType.GAUGE,
            value=count,
            description="Number of active sessions"
        ))

# Usage
metrics = ApplicationMetrics(collector)
await metrics.record_agent_execution("Assistant", 1.23, True)
await metrics.update_active_sessions(5)
```

## Metric Naming Conventions

The collector automatically builds metric names:

```python
# Input name: "requests_total"
# Namespace: "tframex"  
# Subsystem: "api"
# Result: "tframex_api_requests_total"

collector = PrometheusCollector({
    "namespace": "tframex",
    "subsystem": "api"
})
```

## Health Checks

The collector provides a health check endpoint:

```python
# GET /health returns:
{
    "healthy": true,
    "server_running": true,
    "metrics_count": 15,
    "endpoint": "http://localhost:9090/metrics"
}
```

## Lifecycle Management

```python
# Initialize collector
await collector.initialize()

# Check health
health = await collector.health_check()
print(f"Healthy: {health['healthy']}")

# Get metric count
count = collector.get_metric_count()
print(f"Metrics registered: {count}")

# Clear all metrics (use with caution)
collector.clear_metrics()

# Shutdown
await collector.shutdown()
```

## Integration with Monitoring

### Prometheus Configuration

Add to your `prometheus.yml`:

```yaml
scrape_configs:
  - job_name: 'tframex'
    static_configs:
      - targets: ['localhost:9090']
    scrape_interval: 15s
    metrics_path: /metrics
```

### Grafana Dashboard

Example Grafana queries:

```promql
# Agent execution rate
rate(tframex_agent_executions_total[5m])

# Average agent duration
rate(tframex_agent_duration_seconds_sum[5m]) / 
rate(tframex_agent_duration_seconds_count[5m])

# Active sessions
tframex_active_sessions

# Error rate
rate(tframex_agent_executions_total{status="error"}[5m]) /
rate(tframex_agent_executions_total[5m])
```

## Example Implementation

Complete example with custom metrics:

```python
import asyncio
import time
from tframex import TFrameXApp
from tframex.enterprise.metrics import PrometheusCollector, MetricEvent, MetricType

class MetricsMiddleware:
    def __init__(self, collector: PrometheusCollector):
        self.collector = collector
    
    async def instrument_agent_call(self, agent_name: str, func):
        """Instrument agent calls with metrics."""
        start_time = time.time()
        success = False
        
        try:
            result = await func()
            success = True
            return result
        except Exception as e:
            raise
        finally:
            duration = time.time() - start_time
            
            # Record execution
            await self.collector.send_metric(MetricEvent(
                name="agent_calls_total",
                type=MetricType.COUNTER,
                value=1,
                labels={
                    "agent": agent_name,
                    "status": "success" if success else "error"
                }
            ))
            
            # Record duration
            await self.collector.send_metric(MetricEvent(
                name="agent_call_duration_seconds", 
                type=MetricType.HISTOGRAM,
                value=duration,
                labels={"agent": agent_name}
            ))

async def main():
    # Setup metrics
    collector = PrometheusCollector({"port": 9090})
    await collector.initialize()
    
    middleware = MetricsMiddleware(collector)
    
    # Setup app
    app = TFrameXApp()
    
    @app.agent(name="MetricsAgent")
    async def metrics_agent():
        pass
    
    try:
        async with app.run_context() as rt:
            # Instrument agent call
            async def agent_call():
                return await rt.call_agent("MetricsAgent", "Hello")
            
            result = await middleware.instrument_agent_call(
                "MetricsAgent", 
                agent_call
            )
            
            print(f"Result: {result}")
            
            # Keep server running
            await asyncio.sleep(60)
            
    finally:
        await collector.shutdown()

if __name__ == "__main__":
    asyncio.run(main())
```

## Limitations

The current metrics implementation has these limitations:

- **Prometheus only**: Only Prometheus format is supported
- **No StatsD**: StatsD collector is not implemented  
- **No OpenTelemetry**: OpenTelemetry integration is not available
- **Basic aggregation**: Limited built-in metric aggregation
- **No persistence**: Metrics are lost on restart
- **Single instance**: No distributed metrics collection

## Next Steps

- See [Enterprise Storage](storage) for persistent metrics storage
- Check [Configuration](configuration) for enterprise setup
- Review [Security](security/overview) for metrics security