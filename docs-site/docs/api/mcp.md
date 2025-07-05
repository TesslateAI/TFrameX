---
sidebar_position: 7
title: MCP Integration
---

# MCP (Model Context Protocol) API Reference

The Model Context Protocol (MCP) integration in TFrameX v1.1.0 provides seamless connectivity to external services, tools, and data sources through a standardized protocol.

## Overview

MCP enables TFrameX agents to:
- Connect to external databases and APIs
- Access file systems and cloud storage
- Integrate with third-party tools
- Share context across different systems

## MCP Client

The core MCP client manages connections to MCP servers:

```python
from tframex.mcp import MCPClient, MCPConfig

# Basic MCP client setup
config = MCPConfig(
    server_url="http://localhost:8080",
    api_key="your-api-key",
    timeout=30,
    retry_attempts=3
)

client = MCPClient(config)
await client.connect()
```

### Advanced Configuration

```python
# Full configuration options
config = MCPConfig(
    server_url="https://mcp.example.com",
    api_key="your-api-key",
    
    # Connection settings
    timeout=30,
    retry_attempts=3,
    retry_delay=1.0,
    max_connections=10,
    
    # SSL/TLS settings
    verify_ssl=True,
    client_cert="/path/to/cert.pem",
    client_key="/path/to/key.pem",
    
    # Authentication
    auth_method="bearer",  # or "basic", "oauth2"
    refresh_token="refresh-token",
    
    # Performance
    enable_compression=True,
    connection_pool_size=5,
    keepalive_interval=60
)
```

## MCP Tools

Convert MCP resources into TFrameX tools:

```python
from tframex.mcp import MCPToolAdapter

# Connect to MCP server
mcp_client = MCPClient(config)
await mcp_client.connect()

# Discover available tools
tools = await mcp_client.list_tools()

# Create TFrameX tools from MCP
adapter = MCPToolAdapter(mcp_client)

# Convert all MCP tools
for tool_info in tools:
    tframex_tool = await adapter.create_tool(tool_info)
    app.register_tool(tframex_tool)

# Or convert specific tools
database_tool = await adapter.create_tool("mcp://database/query")
app.register_tool(database_tool)
```

### Tool Discovery

```python
# Discover tools by capability
database_tools = await mcp_client.discover_tools(
    capability="database",
    tags=["sql", "nosql"]
)

# Discover tools by protocol
api_tools = await mcp_client.discover_tools(
    protocol="rest",
    version="2.0"
)

# Get tool metadata
tool_info = await mcp_client.get_tool_info("mcp://service/tool")
print(f"Tool: {tool_info.name}")
print(f"Description: {tool_info.description}")
print(f"Parameters: {tool_info.parameters}")
```

## MCP Resources

Access external resources through MCP:

```python
from tframex.mcp import MCPResource

# Access a database
db_resource = MCPResource(
    client=mcp_client,
    uri="mcp://database/production",
    type="postgresql"
)

# Query the database
result = await db_resource.execute(
    "SELECT * FROM users WHERE created_at > ?",
    params=["2024-01-01"]
)

# Access a file system
fs_resource = MCPResource(
    client=mcp_client,
    uri="mcp://filesystem/shared",
    type="s3"
)

# Read a file
content = await fs_resource.read("documents/report.pdf")

# List files
files = await fs_resource.list("documents/", recursive=True)
```

### Resource Types

```python
# API Resource
api_resource = MCPResource(
    client=mcp_client,
    uri="mcp://api/weather",
    type="rest"
)

weather = await api_resource.get("/current", params={"city": "London"})

# Key-Value Store
kv_resource = MCPResource(
    client=mcp_client,
    uri="mcp://cache/redis",
    type="keyvalue"
)

await kv_resource.set("user:123", {"name": "Alice", "role": "admin"})
user = await kv_resource.get("user:123")

# Message Queue
mq_resource = MCPResource(
    client=mcp_client,
    uri="mcp://queue/events",
    type="messagequeue"
)

await mq_resource.publish("user.created", {"id": 123, "email": "alice@example.com"})
```

## MCP Integration with Agents

Enable agents to use MCP tools:

```python
# Create agent with MCP tools
agent = LLMAgent(
    name="DataAnalyst",
    description="Analyzes data from multiple sources",
    llm=llm,
    tools=["mcp://database/query", "mcp://api/analytics"],
    system_prompt="You can access databases and analytics APIs through MCP."
)

# Register MCP-aware agent
app.register_agent(agent)

# Agent automatically uses MCP tools
async with app.run_context() as rt:
    result = await rt.call_agent(
        "DataAnalyst",
        "Analyze sales data for Q4 2023"
    )
```

### Dynamic Tool Loading

```python
class MCPAgent(LLMAgent):
    """Agent that dynamically loads MCP tools."""
    
    def __init__(self, *args, mcp_client: MCPClient, **kwargs):
        super().__init__(*args, **kwargs)
        self.mcp_client = mcp_client
        self._tool_cache = {}
    
    async def run(self, prompt: str, runtime: Runtime) -> str:
        # Analyze prompt to determine needed tools
        needed_tools = await self.analyze_tool_needs(prompt)
        
        # Dynamically load MCP tools
        for tool_uri in needed_tools:
            if tool_uri not in self._tool_cache:
                tool = await self.load_mcp_tool(tool_uri)
                self._tool_cache[tool_uri] = tool
                runtime.register_tool(tool)
        
        # Execute with loaded tools
        return await super().run(prompt, runtime)
```

## MCP Streams

Handle streaming data through MCP:

```python
from tframex.mcp import MCPStream

# Create a stream
stream = MCPStream(
    client=mcp_client,
    uri="mcp://stream/events",
    buffer_size=1000
)

# Subscribe to stream
async with stream.subscribe() as subscription:
    async for event in subscription:
        print(f"Event: {event.type} - {event.data}")
        
        # Process event
        if event.type == "data_update":
            await process_update(event.data)

# Publish to stream
await stream.publish({
    "type": "user_action",
    "user_id": 123,
    "action": "login"
})
```

### Stream Processing

```python
# Filtered stream
stream = MCPStream(
    client=mcp_client,
    uri="mcp://stream/logs"
)

# Subscribe with filters
async with stream.subscribe(
    filters={
        "level": ["error", "critical"],
        "service": "api"
    }
) as subscription:
    async for log in subscription:
        await handle_error_log(log)

# Windowed stream processing
async def process_window(events: List[Dict]):
    """Process a window of events."""
    summary = summarize_events(events)
    await store_summary(summary)

await stream.process_windowed(
    window_size=100,
    window_duration=60,  # seconds
    processor=process_window
)
```

## MCP Security

Secure MCP connections and data:

```python
from tframex.mcp import MCPSecurity

# Configure security
security = MCPSecurity(
    encryption_key="your-encryption-key",
    signing_key="your-signing-key",
    allowed_servers=["https://trusted-mcp.example.com"],
    validate_schemas=True
)

# Secure client
secure_client = MCPClient(
    config=config,
    security=security
)

# Encrypted resource access
secure_resource = MCPResource(
    client=secure_client,
    uri="mcp://secure/sensitive-data",
    encrypt_transport=True,
    encrypt_at_rest=True
)
```

### Authentication Methods

```python
# OAuth2 authentication
from tframex.mcp.auth import OAuth2Auth

auth = OAuth2Auth(
    client_id="your-client-id",
    client_secret="your-client-secret",
    token_url="https://auth.example.com/token",
    scopes=["read:data", "write:data"]
)

client = MCPClient(config, auth=auth)

# API Key authentication
from tframex.mcp.auth import APIKeyAuth

auth = APIKeyAuth(
    api_key="your-api-key",
    header_name="X-API-Key"
)

# Certificate authentication
from tframex.mcp.auth import CertAuth

auth = CertAuth(
    cert_file="/path/to/client.crt",
    key_file="/path/to/client.key",
    ca_bundle="/path/to/ca-bundle.crt"
)
```

## MCP Monitoring

Monitor MCP connections and usage:

```python
from tframex.mcp import MCPMonitor

# Create monitor
monitor = MCPMonitor(client)

# Get connection status
status = await monitor.get_status()
print(f"Connected: {status.connected}")
print(f"Latency: {status.latency_ms}ms")
print(f"Requests/min: {status.rpm}")

# Monitor tool usage
usage = await monitor.get_tool_usage("mcp://database/query")
print(f"Calls: {usage.total_calls}")
print(f"Avg duration: {usage.avg_duration_ms}ms")
print(f"Error rate: {usage.error_rate}%")

# Set up alerts
monitor.add_alert(
    name="high_latency",
    condition=lambda s: s.latency_ms > 1000,
    callback=lambda: notify_ops("High MCP latency detected")
)

# Export metrics
metrics = await monitor.export_metrics(format="prometheus")
```

## MCP Middleware

Add custom middleware to MCP operations:

```python
from tframex.mcp import MCPMiddleware

class LoggingMiddleware(MCPMiddleware):
    """Log all MCP operations."""
    
    async def before_request(self, request):
        logger.info(f"MCP Request: {request.method} {request.uri}")
        return request
    
    async def after_response(self, response):
        logger.info(f"MCP Response: {response.status}")
        return response

class CachingMiddleware(MCPMiddleware):
    """Cache MCP responses."""
    
    def __init__(self, cache_ttl=300):
        self.cache = {}
        self.ttl = cache_ttl
    
    async def before_request(self, request):
        if request.method == "GET":
            cache_key = f"{request.uri}:{request.params}"
            if cache_key in self.cache:
                return self.cache[cache_key]
        return request

# Apply middleware
client = MCPClient(config)
client.add_middleware(LoggingMiddleware())
client.add_middleware(CachingMiddleware(cache_ttl=600))
```

## MCP Patterns

Common patterns for MCP integration:

### Service Discovery

```python
class MCPServiceDiscovery:
    """Discover and manage MCP services."""
    
    def __init__(self, discovery_server: str):
        self.discovery_server = discovery_server
        self.services = {}
    
    async def discover_services(self, service_type: str = None):
        """Discover available services."""
        client = MCPClient(MCPConfig(server_url=self.discovery_server))
        
        services = await client.discover_services(
            type=service_type,
            health_check=True
        )
        
        for service in services:
            self.services[service.name] = service
        
        return services
    
    async def get_service_client(self, service_name: str) -> MCPClient:
        """Get client for a specific service."""
        if service_name not in self.services:
            await self.discover_services()
        
        service = self.services.get(service_name)
        if not service:
            raise ValueError(f"Service {service_name} not found")
        
        return MCPClient(MCPConfig(
            server_url=service.url,
            api_key=service.api_key
        ))
```

### Circuit Breaker

```python
class MCPCircuitBreaker:
    """Circuit breaker for MCP connections."""
    
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 60
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failures = 0
        self.last_failure = None
        self.state = "closed"  # closed, open, half-open
    
    async def call(self, func, *args, **kwargs):
        if self.state == "open":
            if time.time() - self.last_failure > self.recovery_timeout:
                self.state = "half-open"
            else:
                raise Exception("Circuit breaker is open")
        
        try:
            result = await func(*args, **kwargs)
            if self.state == "half-open":
                self.state = "closed"
                self.failures = 0
            return result
        except Exception as e:
            self.failures += 1
            self.last_failure = time.time()
            
            if self.failures >= self.failure_threshold:
                self.state = "open"
            
            raise e
```

### Load Balancing

```python
class MCPLoadBalancer:
    """Load balance across multiple MCP servers."""
    
    def __init__(self, servers: List[str], strategy: str = "round_robin"):
        self.servers = servers
        self.strategy = strategy
        self.current = 0
        self.clients = {}
    
    async def get_client(self) -> MCPClient:
        """Get next available client."""
        if self.strategy == "round_robin":
            server = self.servers[self.current % len(self.servers)]
            self.current += 1
        elif self.strategy == "random":
            server = random.choice(self.servers)
        elif self.strategy == "least_connections":
            server = await self.get_least_loaded_server()
        
        if server not in self.clients:
            self.clients[server] = MCPClient(
                MCPConfig(server_url=server)
            )
            await self.clients[server].connect()
        
        return self.clients[server]
```

## Testing MCP Integration

```python
import pytest
from tframex.mcp.testing import MockMCPServer, MCPTestClient

@pytest.fixture
async def mock_mcp_server():
    server = MockMCPServer()
    
    # Add mock tools
    server.add_tool("database/query", lambda sql: [{"id": 1, "name": "Test"}])
    server.add_tool("api/weather", lambda city: {"temp": 22, "condition": "sunny"})
    
    # Add mock resources
    server.add_resource("filesystem/docs", {"files": ["doc1.txt", "doc2.txt"]})
    
    await server.start()
    yield server
    await server.stop()

async def test_mcp_tool_execution(mock_mcp_server):
    client = MCPTestClient(mock_mcp_server.url)
    
    # Test tool execution
    result = await client.execute_tool(
        "database/query",
        "SELECT * FROM users"
    )
    
    assert len(result) == 1
    assert result[0]["name"] == "Test"

async def test_mcp_resource_access(mock_mcp_server):
    client = MCPTestClient(mock_mcp_server.url)
    
    # Test resource access
    resource = await client.get_resource("filesystem/docs")
    files = await resource.list()
    
    assert len(files) == 2
    assert "doc1.txt" in files
```

## Best Practices

1. **Connection Management** - Reuse MCP clients and connections
2. **Error Handling** - Implement retry logic and circuit breakers
3. **Security** - Always use encryption and authentication
4. **Monitoring** - Track latency, errors, and usage
5. **Caching** - Cache frequently accessed data
6. **Timeouts** - Set appropriate timeouts for operations
7. **Resource Cleanup** - Properly close connections
8. **Testing** - Test with mock MCP servers
9. **Documentation** - Document MCP endpoints and schemas
10. **Versioning** - Handle protocol version compatibility

## Common Issues

### Connection Timeouts

```python
# Increase timeout for slow connections
config = MCPConfig(
    server_url="https://slow-mcp.example.com",
    timeout=60,  # 60 seconds
    connect_timeout=10
)
```

### Authentication Failures

```python
# Refresh tokens automatically
class TokenRefreshMiddleware(MCPMiddleware):
    async def before_request(self, request):
        if self.token_expired():
            new_token = await self.refresh_token()
            request.headers["Authorization"] = f"Bearer {new_token}"
        return request
```

### Rate Limiting

```python
# Handle rate limits
from tframex.mcp import RateLimitHandler

handler = RateLimitHandler(
    max_requests_per_minute=60,
    burst_size=10
)

client = MCPClient(config, rate_limit_handler=handler)
```

## See Also

- [Tools](tools) - Converting MCP tools to TFrameX tools
- [Agents](agents) - Using MCP tools with agents
- [Enterprise](../enterprise/mcp-integration) - Enterprise MCP features
- [Examples](../examples/mcp-examples) - MCP integration examples