# TFrameX MCP Integration Guide

## Overview

This guide provides comprehensive documentation for the Model Context Protocol (MCP) integration in TFrameX. MCP enables TFrameX agents to connect to external services, tools, and resources through a standardized protocol, significantly expanding the framework's capabilities.

## Table of Contents

1. [What is MCP?](#what-is-mcp)
2. [Integration Architecture](#integration-architecture)
3. [Configuration](#configuration)
4. [Agent Integration](#agent-integration)
5. [Available Meta-Tools](#available-meta-tools)
6. [Examples](#examples)
7. [Best Practices](#best-practices)
8. [Troubleshooting](#troubleshooting)

## What is MCP?

The Model Context Protocol (MCP) is a standardized communication protocol that enables LLM applications to connect to external services and resources. It follows a client-server architecture where:

- **MCP Servers**: Provide tools, resources, and prompts
- **MCP Clients**: Connect to servers and use their capabilities
- **Communication**: JSON-RPC 2.0 over various transports (stdio, HTTP)

### Key Benefits

- **Standardization**: Uniform interface for external integrations
- **Extensibility**: Easy addition of new capabilities
- **Security**: Controlled access to external resources
- **Flexibility**: Support for various transport mechanisms

## Integration Architecture

### Core Components

```
TFrameX Application
├── MCPManager
│   ├── Server Configuration Loading
│   ├── Connection Management
│   ├── Tool/Resource Aggregation
│   └── Error Handling
├── MCPConnectedServer
│   ├── Protocol Negotiation
│   ├── Transport Management (stdio/HTTP)
│   ├── Capability Discovery
│   └── Request/Response Handling
└── Meta-Tools
    ├── Server Introspection
    ├── Resource Access
    └── Prompt Management
```

### Integration Points

1. **Application Level**: MCP manager initialization
2. **Agent Level**: Tool and resource access
3. **Engine Level**: Request routing and execution
4. **Runtime Level**: Connection lifecycle management

## Configuration

### Server Configuration File

Create a `servers_config.json` file in your project root:

```json
{
  "mcpServers": {
    "math_server": {
      "type": "streamable-http",
      "url": "http://localhost:8000/mcp",
      "init_step_timeout": 30.0,
      "tool_call_timeout": 60.0
    },
    "sqlite_server": {
      "type": "stdio",
      "command": "uvx",
      "args": ["mcp-server-sqlite", "--db-path", "./example.db"],
      "env": {
        "UV_INDEX_STRATEGY": "unsafe-best-match"
      },
      "init_step_timeout": 30.0,
      "tool_call_timeout": 60.0
    },
    "local_echo": {
      "type": "stdio",
      "command": "python",
      "args": ["echo_server_stdio.py"],
      "init_step_timeout": 10.0,
      "tool_call_timeout": 30.0
    }
  }
}
```

### Configuration Options

#### Server Types

**stdio servers:**
- `command`: Executable command
- `args`: Command line arguments
- `env`: Environment variables

**streamable-http servers:**
- `url`: Server endpoint URL

**Common options:**
- `init_step_timeout`: Server initialization timeout (seconds)
- `tool_call_timeout`: Individual tool call timeout (seconds)

### Application Setup

```python
from tframex import TFrameXApp, OpenAIChatLLM

# Initialize app with MCP configuration
app = TFrameXApp(
    default_llm=my_llm,
    mcp_config_file="servers_config.json"  # Optional, defaults to "servers_config.json"
)

# Explicit MCP server initialization (optional)
async def main():
    await app.initialize_mcp_servers()  # Usually auto-initialized on first use
    
    async with app.run_context() as rt:
        # Use agents with MCP tools
        pass
    
    await app.shutdown_mcp_servers()  # Cleanup (usually auto-handled)
```

## Agent Integration

### MCP Tool Configuration

Agents can access MCP tools through configuration:

```python
# Access tools from all connected MCP servers
@app.agent(
    name="UniversalAgent",
    mcp_tools_from_servers="ALL",
    system_prompt="You have access to tools from all MCP servers. Use them to help users."
)
async def universal_agent():
    pass

# Access tools from specific servers
@app.agent(
    name="DataAgent",
    mcp_tools_from_servers=["sqlite_server", "math_server"],
    system_prompt="You can access database and math tools. Help users with data analysis."
)
async def data_agent():
    pass

# Combine with native tools and other agents
@app.agent(
    name="SupervisorAgent",
    tools=["native_tool"],  # Native TFrameX tools
    callable_agents=["SpecialistAgent"],  # Other agents as tools
    mcp_tools_from_servers=["utility_server"],  # MCP tools
    system_prompt="You coordinate between native tools, other agents, and MCP services."
)
async def supervisor_agent():
    pass
```

### Tool Naming Convention

MCP tools are prefixed with their server alias to avoid naming conflicts:

```
Original MCP tool: "add"
In TFrameX: "math_server__add"

Original MCP tool: "query"
In TFrameX: "sqlite_server__query"
```

## Available Meta-Tools

TFrameX provides built-in meta-tools for MCP server introspection and management:

### 1. `tframex_list_mcp_servers`

Lists all configured MCP servers and their status.

```python
# Available automatically to all agents
# No parameters required
```

### 2. `tframex_list_mcp_resources`

Lists available resources from MCP servers.

**Parameters:**
- `server_alias` (optional): Specific server to query

```python
# List resources from all servers
await agent.call_tool("tframex_list_mcp_resources", {})

# List resources from specific server
await agent.call_tool("tframex_list_mcp_resources", {
    "server_alias": "data_server"
})
```

### 3. `tframex_read_mcp_resource`

Reads content from an MCP resource.

**Parameters:**
- `server_alias` (required): Server containing the resource
- `resource_uri` (required): URI of the resource to read

```python
await agent.call_tool("tframex_read_mcp_resource", {
    "server_alias": "file_server",
    "resource_uri": "file:///path/to/document.txt"
})
```

### 4. `tframex_list_mcp_prompts`

Lists available prompts from MCP servers.

**Parameters:**
- `server_alias` (optional): Specific server to query

```python
# List prompts from all servers
await agent.call_tool("tframex_list_mcp_prompts", {})
```

### 5. `tframex_use_mcp_prompt`

Uses a server-defined prompt.

**Parameters:**
- `server_alias` (required): Server containing the prompt
- `prompt_name` (required): Name of the prompt
- `arguments` (required): Key-value arguments for the prompt

```python
await agent.call_tool("tframex_use_mcp_prompt", {
    "server_alias": "template_server",
    "prompt_name": "generate_report",
    "arguments": {
        "title": "Monthly Sales",
        "data_source": "sales_db"
    }
})
```

## Examples

### Basic MCP Integration

```python
import asyncio
import os
from dotenv import load_dotenv
from tframex import TFrameXApp, OpenAIChatLLM, Message

load_dotenv()

# Configure LLM
my_llm = OpenAIChatLLM(
    model_name=os.getenv("OPENAI_MODEL_NAME", "gpt-3.5-turbo"),
    api_base_url=os.getenv("OPENAI_API_BASE"),
    api_key=os.getenv("OPENAI_API_KEY")
)

# Initialize app with MCP support
app = TFrameXApp(
    default_llm=my_llm,
    mcp_config_file="servers_config.json"
)

# Define an agent with MCP tools
@app.agent(
    name="MathAgent",
    mcp_tools_from_servers=["math_server"],
    system_prompt=(
        "You are a mathematical assistant with access to advanced calculation tools. "
        "Use the available tools to perform complex calculations and help users with math problems."
    )
)
async def math_agent():
    pass

async def main():
    async with app.run_context() as rt:
        # The agent can now use MCP tools automatically
        response = await rt.call_agent(
            "MathAgent",
            Message(role="user", content="Calculate the square root of 144 and then multiply by 3.14159")
        )
        print(f"Math Agent: {response.content}")

if __name__ == "__main__":
    asyncio.run(main())
```

### Database Integration Example

```python
@app.agent(
    name="DatabaseAgent",
    mcp_tools_from_servers=["sqlite_server"],
    tools=["tframex_list_mcp_resources"],  # Add meta-tools explicitly if needed
    system_prompt=(
        "You are a database assistant. You can query databases and analyze data. "
        "Available tools: {available_tools_descriptions}"
    )
)
async def database_agent():
    pass

async def database_example():
    async with app.run_context() as rt:
        # Agent can introspect available resources
        response = await rt.call_agent(
            "DatabaseAgent",
            Message(role="user", content="What database tables are available?")
        )
        print(f"Database Agent: {response.content}")
```

### Multi-Server Integration

```python
@app.agent(
    name="PowerAgent",
    mcp_tools_from_servers="ALL",  # Access all server tools
    system_prompt=(
        "You are a powerful assistant with access to multiple external services. "
        "You can perform calculations, query databases, access files, and more. "
        "Use the appropriate tools based on the user's request."
    )
)
async def power_agent():
    pass

@app.agent(
    name="SupervisorAgent",
    callable_agents=["MathAgent", "DatabaseAgent", "PowerAgent"],
    tools=["tframex_list_mcp_servers"],
    system_prompt=(
        "You are a supervisor agent that delegates tasks to specialist agents. "
        "Available specialists: {available_agents_descriptions}"
    )
)
async def supervisor_agent():
    pass
```

## Best Practices

### 1. Server Configuration

- **Timeouts**: Set appropriate timeouts for server initialization and tool calls
- **Environment**: Use environment variables for sensitive configuration
- **Error Handling**: Gracefully handle server startup failures
- **Resource Limits**: Consider resource usage of stdio processes

### 2. Agent Design

- **Tool Selection**: Be selective about which servers each agent accesses
- **System Prompts**: Include tool descriptions for better LLM understanding
- **Error Handling**: Handle tool execution failures gracefully
- **Permissions**: Follow principle of least privilege

### 3. Performance

- **Connection Pooling**: Reuse connections when possible
- **Timeout Management**: Set reasonable timeouts for operations
- **Parallel Execution**: Use parallel patterns for independent operations
- **Resource Cleanup**: Ensure proper cleanup of resources

### 4. Security

- **Input Validation**: Validate all inputs to MCP tools
- **Credential Management**: Store credentials securely
- **Network Security**: Use HTTPS for remote MCP servers
- **Audit Logging**: Log MCP tool usage for security auditing

## Troubleshooting

### Common Issues

#### 1. Server Connection Failures

**Symptoms:**
- "Failed to initialize MCP server" errors
- Timeouts during server startup

**Solutions:**
- Check server configuration syntax
- Verify command paths and arguments
- Increase `init_step_timeout` values
- Check server dependencies

#### 2. Tool Not Found

**Symptoms:**
- "Tool not found" errors when agent tries to use MCP tools

**Solutions:**
- Verify server is initialized successfully
- Check `mcp_tools_from_servers` configuration
- Ensure server actually provides the expected tools
- Use `tframex_list_mcp_servers` to debug

#### 3. Tool Execution Timeouts

**Symptoms:**
- Tool calls hanging or timing out

**Solutions:**
- Increase `tool_call_timeout` values
- Check MCP server responsiveness
- Verify tool parameters are correct
- Monitor server logs

#### 4. Permission Errors

**Symptoms:**
- Permission denied errors for stdio servers

**Solutions:**
- Check file permissions for executables
- Verify environment variables
- Use absolute paths for commands
- Check user permissions

### Debugging Tools

#### 1. Enable Debug Logging

```python
import logging
from tframex import setup_logging

setup_logging(level=logging.DEBUG)
```

#### 2. Server Introspection

```python
# Use meta-tools to debug MCP integration
@app.agent(
    name="DebugAgent",
    tools=[
        "tframex_list_mcp_servers",
        "tframex_list_mcp_resources",
        "tframex_list_mcp_prompts"
    ],
    system_prompt="You help debug MCP integration issues."
)
async def debug_agent():
    pass
```

#### 3. Manual Server Testing

Test MCP servers independently before integrating:

```bash
# Test stdio server manually
python echo_server_stdio.py

# Test HTTP server
curl -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}}'
```

### Error Codes and Messages

| Error Code | Description | Solution |
|------------|-------------|----------|
| `MCPConfigError` | Configuration file issues | Check JSON syntax and required fields |
| `ConnectionTimeout` | Server connection timeout | Increase timeout or check server availability |
| `ToolNotFound` | MCP tool not available | Verify server provides the tool |
| `InvalidParameters` | Wrong tool parameters | Check tool parameter requirements |
| `ServerNotInitialized` | Server not ready | Wait for initialization or check server status |

This comprehensive integration enables TFrameX agents to leverage external services seamlessly while maintaining the framework's ease of use and robust error handling.