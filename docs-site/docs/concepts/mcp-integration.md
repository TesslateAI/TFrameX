---
sidebar_position: 7
title: MCP Integration
---

# MCP Integration

Model Context Protocol (MCP) integration enables TFrameX to connect with external services, tools, and resources through a standardized protocol. This allows your agents to access capabilities beyond what's built into your application.

## What is MCP?

MCP (Model Context Protocol) is:
- A standard protocol for LLM-service communication
- A way to expose tools and resources to AI agents
- A bridge between your agents and external systems
- A secure method for capability extension

![MCP Integration Architecture](/img/03-mcp-integration-architecture.png)

## MCP Architecture in TFrameX

```
TFrameX App
    ├── MCP Manager
    │   ├── Server Connections
    │   ├── Tool Discovery
    │   └── Resource Management
    └── Agents
        └── MCP Tools (dynamically registered)
```

## Setting Up MCP

### Basic Configuration

Create a `servers_config.json` file:

```json
{
  "mcpServers": {
    "weather_service": {
      "command": "python",
      "args": ["weather_server.py"],
      "type": "stdio"
    },
    "database_service": {
      "command": "node",
      "args": ["db-server.js"],
      "type": "stdio",
      "env": {
        "DB_CONNECTION": "postgresql://localhost/mydb"
      }
    },
    "web_api": {
      "type": "streamable-http",
      "url": "https://api.example.com/mcp",
      "headers": {
        "Authorization": "Bearer ${API_TOKEN}"
      }
    }
  }
}
```

### Initialize MCP in TFrameX

```python
from tframex import TFrameXApp
from tframex.mcp import MCPManager, load_mcp_server_configs

# Load configuration
mcp_config = load_mcp_server_configs("servers_config.json")

# Create app with MCP
app = TFrameXApp(
    mcp_config_file="servers_config.json",
    enable_mcp_roots=True,      # Enable file system access
    enable_mcp_sampling=True,    # Enable sampling/prompting
    enable_mcp_experimental=False # Experimental features
)

# Or manual setup
mcp_manager = MCPManager(mcp_config)
app.set_mcp_manager(mcp_manager)
```

## MCP Server Types

### 1. STDIO Servers

Communicate via standard input/output:

```python
# Server implementation (weather_server.py)
import sys
import json

async def handle_tool_call(tool_name, arguments):
    if tool_name == "get_weather":
        city = arguments["city"]
        # Fetch weather data
        return {"temperature": 72, "condition": "sunny"}

# Main server loop
while True:
    request = json.loads(sys.stdin.readline())
    response = await handle_request(request)
    sys.stdout.write(json.dumps(response) + "\n")
    sys.stdout.flush()
```

Configuration:
```json
{
  "weather_service": {
    "command": "python",
    "args": ["weather_server.py"],
    "type": "stdio",
    "init_step_timeout": 30.0,
    "tool_call_timeout": 60.0
  }
}
```

### 2. HTTP Servers

RESTful API servers:

```json
{
  "api_service": {
    "type": "streamable-http",
    "url": "https://api.example.com/mcp",
    "headers": {
      "Authorization": "Bearer ${API_TOKEN}",
      "Content-Type": "application/json"
    },
    "timeout": 30
  }
}
```

### 3. Custom Servers

Using popular MCP servers:

```json
{
  "mcpServers": {
    "filesystem": {
      "command": "uvx",
      "args": ["@modelcontextprotocol/server-filesystem"],
      "type": "stdio"
    },
    "postgres": {
      "command": "uvx",
      "args": ["@modelcontextprotocol/server-postgres", "postgresql://localhost/db"],
      "type": "stdio"
    },
    "github": {
      "command": "uvx", 
      "args": ["@modelcontextprotocol/server-github"],
      "type": "stdio",
      "env": {
        "GITHUB_TOKEN": "${GITHUB_TOKEN}"
      }
    }
  }
}
```

## Using MCP Tools in Agents

### Automatic Tool Discovery

```python
# Agent with all MCP tools
agent = LLMAgent(
    name="UniversalAssistant",
    description="Assistant with access to all MCP tools",
    llm=llm,
    mcp_tools_from_servers="ALL",  # Access all MCP tools
    system_prompt="You have access to various external tools via MCP."
)

# Agent with specific MCP servers
agent = LLMAgent(
    name="DataAnalyst",
    description="Analyst with database access",
    llm=llm,
    mcp_tools_from_servers=["postgres", "filesystem"],
    system_prompt="You can query databases and read files."
)
```

### MCP Tool Naming Convention

MCP tools are named as: `server_alias__tool_name`

```python
# If postgres server has a 'query' tool
# It becomes: postgres__query

agent = LLMAgent(
    name="DBAgent",
    tools=["postgres__query", "postgres__insert"],  # Specific MCP tools
    llm=llm
)
```

## MCP Meta-Tools

TFrameX provides built-in tools for MCP introspection:

### List MCP Servers

```python
@app.tool(description="List all connected MCP servers")
async def list_mcp_servers() -> List[dict]:
    """Returns information about all MCP servers."""
    # Automatically available as tframex_list_mcp_servers
```

### List Resources

```python
@app.tool(description="List resources from MCP server")
async def list_mcp_resources(server_alias: Optional[str] = None) -> List[dict]:
    """List available resources (files, data, etc.)."""
    # Automatically available as tframex_list_mcp_resources
```

### Read Resources

```python
@app.tool(description="Read content from MCP resource")
async def read_mcp_resource(server_alias: str, resource_uri: str) -> str:
    """Read content from a specific resource."""
    # Automatically available as tframex_read_mcp_resource
```

### List and Use Prompts

```python
@app.tool(description="List available prompts")
async def list_mcp_prompts(server_alias: Optional[str] = None) -> List[dict]:
    """List prompt templates from servers."""
    # Automatically available as tframex_list_mcp_prompts

@app.tool(description="Use MCP prompt template")
async def use_mcp_prompt(
    server_alias: str, 
    prompt_name: str, 
    arguments: dict
) -> str:
    """Execute a prompt template with arguments."""
    # Automatically available as tframex_use_mcp_prompt
```

## Advanced MCP Features

### Roots (File System Access)

Enable secure file system access:

```python
app = TFrameXApp(
    enable_mcp_roots=True,
    mcp_roots_allowed_paths=[
        "/home/user/documents",
        "/var/data/shared"
    ]
)

# MCP servers can now access these paths
```

### Sampling (LLM Access)

Allow MCP servers to make LLM calls:

```python
app = TFrameXApp(
    enable_mcp_sampling=True,
    mcp_sampling_config={
        "max_tokens": 1000,
        "temperature": 0.7,
        "allowed_servers": ["trusted_server"]
    }
)
```

### Resource Templates

MCP servers can provide resource templates:

```python
# List available templates
templates = await rt.call_tool("mcp_server__list_templates")

# Use a template
result = await rt.call_tool(
    "mcp_server__create_from_template",
    {
        "template": "invoice",
        "data": {
            "customer": "Acme Corp",
            "amount": 1500.00
        }
    }
)
```

## Creating MCP Servers

### Basic MCP Server

```python
# mcp_server.py
import asyncio
import json
import sys
from typing import Any, Dict

class SimpleMCPServer:
    def __init__(self):
        self.tools = {
            "calculate": self.calculate,
            "get_data": self.get_data
        }
        self.resources = {
            "config": {"type": "text", "content": "Server configuration"}
        }
    
    async def calculate(self, operation: str, a: float, b: float) -> float:
        """Perform calculation."""
        if operation == "add":
            return a + b
        elif operation == "multiply":
            return a * b
        else:
            raise ValueError(f"Unknown operation: {operation}")
    
    async def get_data(self, key: str) -> Any:
        """Retrieve data by key."""
        data_store = {
            "users": ["Alice", "Bob", "Charlie"],
            "status": "active"
        }
        return data_store.get(key, "Not found")
    
    async def handle_request(self, request: Dict) -> Dict:
        """Handle incoming MCP requests."""
        method = request.get("method")
        
        if method == "initialize":
            return {
                "protocolVersion": "1.0",
                "capabilities": {
                    "tools": True,
                    "resources": True
                }
            }
        
        elif method == "tools/list":
            return {
                "tools": [
                    {
                        "name": name,
                        "description": func.__doc__,
                        "inputSchema": self.get_schema(name)
                    }
                    for name, func in self.tools.items()
                ]
            }
        
        elif method == "tools/call":
            tool_name = request["params"]["name"]
            arguments = request["params"]["arguments"]
            
            if tool_name in self.tools:
                result = await self.tools[tool_name](**arguments)
                return {"content": [{"type": "text", "text": str(result)}]}
            else:
                return {"error": f"Unknown tool: {tool_name}"}
        
        elif method == "resources/list":
            return {
                "resources": [
                    {"uri": f"resource://{name}", "name": name}
                    for name in self.resources
                ]
            }
        
        elif method == "resources/read":
            uri = request["params"]["uri"]
            resource_name = uri.split("://")[1]
            
            if resource_name in self.resources:
                return {"contents": [self.resources[resource_name]]}
            else:
                return {"error": f"Resource not found: {uri}"}
    
    def get_schema(self, tool_name: str) -> Dict:
        """Get parameter schema for tool."""
        schemas = {
            "calculate": {
                "type": "object",
                "properties": {
                    "operation": {"type": "string", "enum": ["add", "multiply"]},
                    "a": {"type": "number"},
                    "b": {"type": "number"}
                },
                "required": ["operation", "a", "b"]
            },
            "get_data": {
                "type": "object",
                "properties": {
                    "key": {"type": "string"}
                },
                "required": ["key"]
            }
        }
        return schemas.get(tool_name, {})
    
    async def run(self):
        """Main server loop."""
        while True:
            try:
                line = sys.stdin.readline()
                if not line:
                    break
                
                request = json.loads(line)
                response = await self.handle_request(request)
                
                # Add required fields
                response["jsonrpc"] = "2.0"
                response["id"] = request.get("id")
                
                sys.stdout.write(json.dumps(response) + "\n")
                sys.stdout.flush()
                
            except Exception as e:
                error_response = {
                    "jsonrpc": "2.0",
                    "id": request.get("id"),
                    "error": {
                        "code": -32603,
                        "message": str(e)
                    }
                }
                sys.stdout.write(json.dumps(error_response) + "\n")
                sys.stdout.flush()

if __name__ == "__main__":
    server = SimpleMCPServer()
    asyncio.run(server.run())
```

### Advanced MCP Server Features

```python
class AdvancedMCPServer:
    def __init__(self):
        self.capabilities = {
            "tools": True,
            "resources": True,
            "prompts": True,
            "sampling": True,  # Can call LLMs
            "roots": True      # File system access
        }
    
    async def handle_sampling_request(self, request):
        """Handle LLM sampling requests from agents."""
        messages = request["params"]["messages"]
        max_tokens = request["params"].get("maxTokens", 1000)
        
        # Server can make LLM calls
        response = await self.llm.generate(messages, max_tokens)
        
        return {
            "model": self.model_name,
            "choices": [{
                "message": {"content": response}
            }]
        }
    
    async def handle_roots_request(self, request):
        """Handle file system access."""
        path = request["params"]["path"]
        
        # Check if path is allowed
        if not self.is_path_allowed(path):
            return {"error": "Access denied"}
        
        # Perform file operation
        if request["method"] == "roots/list":
            files = os.listdir(path)
            return {"entries": files}
        elif request["method"] == "roots/read":
            with open(path, 'r') as f:
                content = f.read()
            return {"content": content}
```

## MCP Best Practices

### 1. Server Configuration

```json
{
  "mcpServers": {
    "production_db": {
      "command": "python",
      "args": ["db_server.py"],
      "type": "stdio",
      "env": {
        "DB_HOST": "${DB_HOST}",
        "DB_PASSWORD": "${DB_PASSWORD}"
      },
      "init_step_timeout": 60.0,  // Longer for DB connections
      "tool_call_timeout": 300.0,  // 5 min for complex queries
      "restart_on_failure": true,
      "max_restarts": 3
    }
  }
}
```

### 2. Error Handling

```python
class RobustMCPManager:
    async def call_tool(self, server_alias: str, tool_name: str, arguments: dict):
        try:
            return await self.mcp_manager.call_tool(server_alias, tool_name, arguments)
        except MCPServerNotFoundError:
            logger.error(f"MCP server '{server_alias}' not found")
            return {"error": "Service temporarily unavailable"}
        except MCPToolNotFoundError:
            logger.error(f"Tool '{tool_name}' not found on server '{server_alias}'")
            return {"error": "Feature not available"}
        except MCPTimeoutError:
            logger.error(f"Timeout calling {server_alias}__{tool_name}")
            return {"error": "Operation timed out, please try again"}
        except Exception as e:
            logger.error(f"MCP error: {e}")
            return {"error": "An error occurred"}
```

### 3. Security Considerations

```python
# Secure MCP configuration
app = TFrameXApp(
    # Limit file access
    enable_mcp_roots=True,
    mcp_roots_allowed_paths=[
        "/app/data/public",
        "/app/shared"
    ],
    
    # Control sampling
    enable_mcp_sampling=True,
    mcp_sampling_config={
        "allowed_servers": ["trusted_analyzer"],
        "max_tokens": 500,
        "block_sensitive_content": True
    },
    
    # Disable experimental features in production
    enable_mcp_experimental=False
)
```

### 4. Monitoring and Logging

```python
import logging

# Enable MCP debug logging
logging.getLogger("tframex.mcp").setLevel(logging.DEBUG)

# Custom monitoring
class MonitoredMCPManager(MCPManager):
    async def call_tool(self, server_alias: str, tool_name: str, arguments: dict):
        start_time = time.time()
        
        try:
            result = await super().call_tool(server_alias, tool_name, arguments)
            
            # Log success metrics
            duration = time.time() - start_time
            metrics.record("mcp.tool_call.success", {
                "server": server_alias,
                "tool": tool_name,
                "duration": duration
            })
            
            return result
            
        except Exception as e:
            # Log error metrics
            metrics.record("mcp.tool_call.error", {
                "server": server_alias,
                "tool": tool_name,
                "error": str(e)
            })
            raise
```

## Testing MCP Integration

```python
import pytest
from unittest.mock import Mock, AsyncMock

@pytest.mark.asyncio
async def test_mcp_tool_discovery():
    # Mock MCP server
    mock_server = Mock()
    mock_server.list_tools.return_value = [
        {"name": "test_tool", "description": "Test tool"}
    ]
    
    # Test discovery
    app = TFrameXApp()
    app.mcp_manager.servers["test_server"] = mock_server
    
    tools = await app.mcp_manager.discover_tools("test_server")
    assert len(tools) == 1
    assert tools[0]["name"] == "test_tool"

@pytest.mark.asyncio
async def test_mcp_tool_execution():
    # Test tool execution
    app = TFrameXApp(mcp_config_file="test_servers.json")
    
    async with app.run_context() as rt:
        result = await rt.call_tool(
            "test_server__calculate",
            {"operation": "add", "a": 5, "b": 3}
        )
        assert result == 8
```

## Common MCP Patterns

### Database Access Pattern

```python
# Agent with database access
db_agent = LLMAgent(
    name="DatabaseAnalyst",
    mcp_tools_from_servers=["postgres"],
    system_prompt="""You are a database analyst with access to PostgreSQL.
    
Available tools:
- postgres__query: Execute SELECT queries
- postgres__insert: Insert new records
- postgres__update: Update existing records
- postgres__schema: Get table schemas

Always validate queries before execution."""
)
```

### File System Pattern

```python
# Agent with file access
file_agent = LLMAgent(
    name="FileManager",
    mcp_tools_from_servers=["filesystem"],
    system_prompt="""You manage files and documents.
    
Available tools:
- filesystem__read: Read file contents
- filesystem__write: Write to files
- filesystem__list: List directory contents
- filesystem__search: Search for files

Respect access permissions and handle errors gracefully."""
)
```

### Multi-Service Pattern

```python
# Agent with multiple services
integration_agent = LLMAgent(
    name="IntegrationSpecialist",
    mcp_tools_from_servers=["database", "api", "filesystem"],
    system_prompt="""You integrate data from multiple sources.
    
Workflow:
1. Query database for records
2. Fetch additional data from API
3. Save consolidated report to filesystem

Coordinate between services efficiently."""
)
```

## Next Steps

Now that you understand MCP integration:

1. Learn about [Enterprise Features](../enterprise/overview) for production MCP
2. Explore [MCP Server Examples](../examples/integration-examples)
3. Study [API Reference](../api/mcp) for detailed documentation
4. Check the [MCP Specification](https://modelcontextprotocol.io) for protocol details