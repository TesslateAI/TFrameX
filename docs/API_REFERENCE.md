# TFrameX API Reference

This document provides a comprehensive reference for all APIs, configuration options, and specifications in the TFrameX framework.

## Table of Contents
1. [Core APIs](#core-apis)
2. [Agent APIs](#agent-apis)
3. [Tool APIs](#tool-apis)
4. [Flow APIs](#flow-apis)
5. [Pattern APIs](#pattern-apis)
6. [MCP APIs](#mcp-apis)
7. [Utility APIs](#utility-apis)
8. [Configuration Options](#configuration-options)
9. [Data Models](#data-models)
10. [Environment Variables](#environment-variables)

---

## Core APIs

### TFrameXApp

Primary application class for framework initialization and configuration.

```python
class TFrameXApp:
    def __init__(
        self,
        default_llm: Optional[BaseLLMWrapper] = None,
        default_memory_store_factory: Callable[[], BaseMemoryStore] = InMemoryMemoryStore,
        mcp_config_file: Optional[str] = "servers_config.json",
        enable_mcp_roots: bool = True,
        enable_mcp_sampling: bool = True,
        enable_mcp_experimental: bool = False,
        mcp_roots_allowed_paths: Optional[List[str]] = None
    )
```

**Parameters:**
- `default_llm`: Default LLM wrapper for all agents
- `default_memory_store_factory`: Factory function for creating memory stores
- `mcp_config_file`: Path to MCP server configuration file
- `enable_mcp_roots`: Enable MCP roots capability
- `enable_mcp_sampling`: Enable MCP sampling capability
- `enable_mcp_experimental`: Enable experimental MCP features
- `mcp_roots_allowed_paths`: Allowed paths for MCP roots access

**Methods:**

#### `@app.agent()`
Decorator for registering agents.

```python
@app.agent(
    name: str,
    description: str = "",
    callable_agents: Optional[List[str]] = None,
    system_prompt: Optional[str] = None,
    tools: Optional[List[str]] = None,
    mcp_tools_from_servers: Optional[Union[str, List[str]]] = None,
    llm: Optional[BaseLLMWrapper] = None,
    memory_store: Optional[BaseMemoryStore] = None,
    agent_class: Type[BaseAgent] = LLMAgent,
    strip_think_tags: bool = True,
    max_tool_iterations: int = 10,
    additional_prompt_variables: Optional[Dict[str, Any]] = None
)
```

**Parameters:**
- `name`: Unique agent identifier
- `description`: Agent description for documentation
- `callable_agents`: List of other agents this agent can call
- `system_prompt`: System prompt template
- `tools`: List of tool names this agent can use
- `mcp_tools_from_servers`: MCP servers to use ("ALL" or specific list)
- `llm`: Custom LLM wrapper for this agent
- `memory_store`: Custom memory store for this agent
- `agent_class`: Agent class (LLMAgent or ToolAgent)
- `strip_think_tags`: Whether to remove <think> tags from responses
- `max_tool_iterations`: Maximum tool execution iterations
- `additional_prompt_variables`: Additional template variables

#### `@app.tool()`
Decorator for registering tools.

```python
@app.tool(
    name: Optional[str] = None,
    description: Optional[str] = None,
    enabled: bool = True
)
```

**Parameters:**
- `name`: Tool name (defaults to function name)
- `description`: Tool description (defaults to function docstring)
- `enabled`: Whether the tool is enabled

#### `register_flow()`
Register a flow with the application.

```python
def register_flow(self, flow: Flow) -> None
```

#### `run_context()`
Create a runtime context for agent execution.

```python
async def run_context(self, **template_variables) -> TFrameXRuntimeContext
```

**Parameters:**
- `**template_variables`: Variables available to all agents in this context

### TFrameXRuntimeContext

Runtime execution context managing agent instances and resources.

```python
class TFrameXRuntimeContext:
    async def execute_agent(
        self,
        agent_name: str,
        input_message: Union[str, Message],
        **kwargs
    ) -> str
    
    async def execute_flow(
        self,
        flow_name: str,
        initial_input: Union[str, Message],
        **kwargs
    ) -> FlowContext
    
    async def chat_with_agent(
        self,
        agent_name: str,
        max_iterations: int = 100
    ) -> None
```

---

## Agent APIs

### BaseAgent

Abstract base class for all agents.

```python
class BaseAgent:
    def __init__(
        self,
        name: str,
        description: str = "",
        system_prompt: Optional[str] = None,
        tools: Optional[List[str]] = None,
        callable_agents: Optional[List[str]] = None,
        llm: Optional[BaseLLMWrapper] = None,
        memory_store: Optional[BaseMemoryStore] = None,
        strip_think_tags: bool = True,
        max_tool_iterations: int = 10,
        additional_prompt_variables: Optional[Dict[str, Any]] = None
    )
    
    async def run(
        self,
        input_message: Union[str, Message],
        **kwargs
    ) -> Message
```

### LLMAgent

Agent that uses LLM for reasoning and decision-making.

```python
class LLMAgent(BaseAgent):
    async def run(
        self,
        input_message: Union[str, Message],
        **kwargs
    ) -> Message
```

**Features:**
- Tool calling capability
- Memory management
- Think tag processing
- Multi-turn conversation support
- Agent-as-tool delegation

### ToolAgent

Agent that directly executes tools without LLM reasoning.

```python
class ToolAgent(BaseAgent):
    async def run(
        self,
        input_message: Union[str, Message],
        **kwargs
    ) -> Message
```

---

## Tool APIs

### Tool Registration

Tools are registered using the `@app.tool()` decorator or by function signature inference.

```python
@app.tool(description="Calculate the sum of two numbers")
async def add_numbers(a: int, b: int) -> int:
    """Add two numbers together."""
    return a + b

@app.tool(description="Read file contents")
async def read_file(file_path: str) -> str:
    """Read and return file contents."""
    with open(file_path, 'r') as f:
        return f.read()
```

### Tool Schema

Tools automatically generate JSON schemas from function signatures:

```python
{
    "type": "function",
    "function": {
        "name": "add_numbers",
        "description": "Calculate the sum of two numbers",
        "parameters": {
            "type": "object",
            "properties": {
                "a": {"type": "integer", "description": "First number"},
                "b": {"type": "integer", "description": "Second number"}
            },
            "required": ["a", "b"]
        }
    }
}
```

### Meta Tools

Special tools for framework introspection:

- `list_available_tools()`: List all available tools
- `get_tool_schema(tool_name)`: Get tool schema
- `list_available_agents()`: List all available agents
- `get_agent_info(agent_name)`: Get agent information

---

## Flow APIs

### Flow

Container for defining sequential workflows.

```python
class Flow:
    def __init__(self, name: str, description: str = "")
    
    def add_step(self, step: Union[str, BasePattern]) -> 'Flow'
    def add_agent_step(self, agent_name: str) -> 'Flow'
    def add_pattern_step(self, pattern: BasePattern) -> 'Flow'
    
    async def execute(
        self,
        initial_input: Union[str, Message],
        engine: 'Engine',
        **kwargs
    ) -> FlowContext
    
    def to_yaml(self) -> str
    def to_mermaid(self) -> str
```

### FlowContext

Carries state and data between flow steps.

```python
class FlowContext:
    def __init__(self, flow_name: str, initial_input: Union[str, Message])
    
    def add_step_result(self, step_name: str, result: Union[str, Message])
    def get_step_result(self, step_name: str) -> Optional[Union[str, Message]]
    def get_all_results(self) -> Dict[str, Union[str, Message]]
    def get_messages(self) -> List[Message]
    def set_template_variables(self, variables: Dict[str, Any])
    def get_template_variables(self) -> Dict[str, Any]
```

---

## Pattern APIs

### BasePattern

Abstract base class for execution patterns.

```python
class BasePattern:
    def __init__(self, name: str, description: str = "")
    
    async def execute(
        self,
        flow_ctx: FlowContext,
        engine: 'Engine',
        agent_call_kwargs: Optional[Dict[str, Any]] = None
    ) -> FlowContext
```

### SequentialPattern

Execute agents one after another.

```python
class SequentialPattern(BasePattern):
    def __init__(
        self,
        name: str,
        agents: List[Union[str, BasePattern]],
        description: str = ""
    )
```

### ParallelPattern

Execute agents concurrently.

```python
class ParallelPattern(BasePattern):
    def __init__(
        self,
        name: str,
        agents: List[Union[str, BasePattern]],
        description: str = ""
    )
```

### RouterPattern

Route execution to specific agents based on router decision.

```python
class RouterPattern(BasePattern):
    def __init__(
        self,
        name: str,
        router_agent: str,
        route_options: Dict[str, Union[str, BasePattern]],
        description: str = ""
    )
```

### DiscussionPattern

Multi-agent discussion with optional moderation.

```python
class DiscussionPattern(BasePattern):
    def __init__(
        self,
        name: str,
        agents: List[str],
        num_rounds: int = 1,
        moderator_agent: Optional[str] = None,
        description: str = ""
    )
```

---

## MCP APIs

### MCPManager

Manages MCP server connections and capabilities.

```python
class MCPManager:
    def __init__(
        self,
        config_file: str = "servers_config.json",
        enable_roots: bool = True,
        enable_sampling: bool = True,
        enable_experimental: bool = False,
        roots_allowed_paths: Optional[List[str]] = None
    )
    
    async def initialize_servers(self) -> None
    async def get_available_tools(self) -> List[Dict[str, Any]]
    async def call_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        server_name: Optional[str] = None
    ) -> Any
    async def cleanup(self) -> None
```

### MCP Server Configuration

MCP servers are configured via JSON:

```json
{
    "mcpServers": {
        "server_name": {
            "type": "stdio",
            "command": "python",
            "args": ["server.py"],
            "env": {"KEY": "value"},
            "init_step_timeout": 30.0,
            "tool_call_timeout": 60.0
        },
        "http_server": {
            "type": "streamable-http",
            "url": "https://api.example.com/mcp",
            "headers": {"Authorization": "Bearer token"}
        }
    }
}
```

**Server Types:**
- `stdio`: Process-based server with stdin/stdout communication
- `streamable-http`: HTTP-based server with streaming support

**Configuration Options:**
- `command`: Executable command (stdio only)
- `args`: Command arguments (stdio only)
- `env`: Environment variables (stdio only)
- `url`: Server URL (HTTP only)
- `headers`: HTTP headers (HTTP only)
- `init_step_timeout`: Server initialization timeout
- `tool_call_timeout`: Tool execution timeout
- `resource_read_timeout`: Resource read timeout

### MCP Capabilities

Advanced MCP features:

#### Roots Management
```python
from tframex.mcp.roots import MCPRootsManager

# Enable file system access
roots_manager = MCPRootsManager(allowed_paths=["/safe/path"])
```

#### Sampling Control
```python
from tframex.mcp.sampling import MCPSamplingManager

# Enable human-in-the-loop for LLM requests
sampling_manager = MCPSamplingManager(require_approval=True)
```

#### Progress Tracking
```python
from tframex.mcp.progress import MCPProgressManager

# Track long-running operations
progress_manager = MCPProgressManager()
```

---

## Utility APIs

### LLM Wrappers

#### OpenAIChatLLM

OpenAI-compatible LLM wrapper.

```python
class OpenAIChatLLM(BaseLLMWrapper):
    def __init__(
        self,
        model_name: str = "gpt-3.5-turbo",
        api_key: Optional[str] = None,
        api_base_url: str = "https://api.openai.com/v1",
        default_max_tokens: int = 4096,
        default_temperature: float = 0.7,
        parse_text_tool_calls: bool = False,
        **kwargs
    )
    
    async def generate_response(
        self,
        messages: List[Message],
        tools: Optional[List[Dict[str, Any]]] = None,
        **kwargs
    ) -> AsyncGenerator[Message, None]
```

**Parameters:**
- `model_name`: Model identifier
- `api_key`: API key (defaults to OPENAI_API_KEY env var)
- `api_base_url`: API base URL
- `default_max_tokens`: Default token limit
- `default_temperature`: Default temperature
- `parse_text_tool_calls`: Parse text-based tool calls
- `**kwargs`: Additional parameters passed to API

### Memory Stores

#### InMemoryMemoryStore

Simple in-memory conversation storage.

```python
class InMemoryMemoryStore(BaseMemoryStore):
    def __init__(self, max_messages: int = 100)
    
    async def add_message(self, message: Message) -> None
    async def get_history(
        self,
        limit: Optional[int] = None,
        offset: int = 0,
        roles: Optional[List[str]] = None
    ) -> List[Message]
    async def clear(self) -> None
```

#### Custom Memory Store

Implement custom memory stores:

```python
class CustomMemoryStore(BaseMemoryStore):
    async def add_message(self, message: Message) -> None:
        # Custom implementation
        pass
    
    async def get_history(
        self,
        limit: Optional[int] = None,
        offset: int = 0,
        roles: Optional[List[str]] = None
    ) -> List[Message]:
        # Custom implementation
        pass
```

### Logging

#### Setup Logging

```python
from tframex.util.logging import setup_logging

setup_logging(
    level=logging.INFO,
    log_format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    use_colors=True
)
```

**Parameters:**
- `level`: Logging level
- `log_format`: Log message format
- `use_colors`: Enable colored output

---

## Configuration Options

### Application Configuration

```python
app = TFrameXApp(
    # Core Configuration
    default_llm=OpenAIChatLLM(model_name="gpt-4"),
    default_memory_store_factory=InMemoryMemoryStore,
    
    # MCP Configuration
    mcp_config_file="servers_config.json",
    enable_mcp_roots=True,
    enable_mcp_sampling=True,
    enable_mcp_experimental=False,
    mcp_roots_allowed_paths=["/safe/path"]
)
```

### Agent Configuration

```python
@app.agent(
    name="my_agent",
    description="Agent description",
    
    # Capabilities
    tools=["tool1", "tool2"],
    callable_agents=["agent1", "agent2"],
    mcp_tools_from_servers="ALL",
    
    # Behavior
    system_prompt="You are a helpful assistant...",
    strip_think_tags=True,
    max_tool_iterations=10,
    
    # Resources
    llm=custom_llm,
    memory_store=custom_memory,
    agent_class=LLMAgent,
    
    # Template Variables
    additional_prompt_variables={"context": "value"}
)
```

### Flow Configuration

```python
flow = Flow("my_flow", "Flow description")
flow.add_step("agent1")
flow.add_pattern_step(ParallelPattern("parallel", ["agent2", "agent3"]))
flow.add_step("agent4")
```

---

## Data Models

### Message

Represents a conversation message.

```python
@dataclass
class Message:
    role: Literal["system", "user", "assistant", "tool"]
    content: Optional[str] = None
    tool_calls: Optional[List[ToolCall]] = None
    tool_call_id: Optional[str] = None
    name: Optional[str] = None
```

### ToolCall

Represents a tool call request.

```python
@dataclass
class ToolCall:
    id: str
    type: Literal["function"] = "function"
    function: FunctionCall
```

### FunctionCall

Represents a function call.

```python
@dataclass
class FunctionCall:
    name: str
    arguments: str  # JSON string
```

### ToolDefinition

Represents a tool definition.

```python
@dataclass
class ToolDefinition:
    type: Literal["function"] = "function"
    function: Dict[str, Any]
```

### ToolParameters

Represents tool parameters schema.

```python
@dataclass
class ToolParameters:
    type: Literal["object"] = "object"
    properties: Dict[str, ToolParameterProperty]
    required: Optional[List[str]] = None
```

### ToolParameterProperty

Represents a tool parameter property.

```python
@dataclass
class ToolParameterProperty:
    type: str
    description: Optional[str] = None
    enum: Optional[List[str]] = None
    default: Optional[Any] = None
```

---

## Environment Variables

### Core Framework Variables

```bash
# LLM Configuration
OPENAI_API_KEY=sk-...                          # OpenAI API key
OPENAI_API_BASE=https://api.openai.com/v1      # OpenAI API base URL
OPENAI_MODEL_NAME=gpt-3.5-turbo                # Default model name

# Framework Configuration
TFRAMEX_ALLOW_NO_DEFAULT_LLM=false             # Allow apps without default LLM

# Logging Configuration
TFRAMEX_LOG_LEVEL=INFO                         # Framework log level
MCP_LOG_LEVEL=INFO                             # MCP log level
```

### Local Development Variables

```bash
# Local LLM Configuration (Ollama)
OPENAI_API_BASE=http://localhost:11434/v1
OPENAI_API_KEY=ollama
OPENAI_MODEL_NAME=llama3

# Development Settings
LOG_LEVEL=DEBUG
DEBUG_MODE=true
```

### Example-Specific Variables

```bash
# Web Application
FLASK_ENV=development
FLASK_DEBUG=true

# External APIs
REDDIT_CLIENT_ID=your_reddit_client_id
REDDIT_CLIENT_SECRET=your_reddit_client_secret

# Database
DATABASE_URL=postgresql://user:pass@localhost/db
```

---

## Error Handling

### Standard Error Format

All APIs return errors in a consistent format:

```python
{
    "error": "Error message description",
    "error_type": "ValidationError",
    "details": {
        "field": "field_name",
        "value": "invalid_value"
    }
}
```

### Common Error Types

- `ValidationError`: Input validation failed
- `ConfigurationError`: Configuration issue
- `AgentNotFoundError`: Agent not found
- `ToolNotFoundError`: Tool not found
- `LLMError`: LLM execution error
- `MCPError`: MCP server error
- `TimeoutError`: Operation timeout
- `MemoryError`: Memory store error

### Error Handling Best Practices

```python
try:
    result = await agent.run(input_message)
except ValidationError as e:
    logger.error(f"Validation failed: {e}")
    return {"error": str(e)}
except TimeoutError as e:
    logger.error(f"Operation timed out: {e}")
    return {"error": "Operation timed out"}
except Exception as e:
    logger.error(f"Unexpected error: {e}")
    return {"error": "Internal server error"}
```

---

## API Versioning

TFrameX follows semantic versioning:

- **Major version**: Breaking changes
- **Minor version**: New features, backward compatible
- **Patch version**: Bug fixes, backward compatible

Current version: `0.1.3`

### Compatibility Matrix

| TFrameX Version | Python Version | MCP Version |
|-----------------|----------------|-------------|
| 0.1.x           | >=3.8          | >=1.0.0     |
| 0.2.x           | >=3.9          | >=1.1.0     |
| 1.0.x           | >=3.9          | >=2.0.0     |

---

## Performance Considerations

### Async Best Practices

- Use `async`/`await` for all I/O operations
- Batch concurrent operations with `asyncio.gather()`
- Use connection pooling for HTTP clients
- Implement proper resource cleanup

### Memory Management

- Configure memory store limits
- Use rolling window for conversation history
- Implement conversation summarization
- Monitor memory usage in production

### Caching Strategies

- Cache tool schemas
- Cache agent instances
- Cache MCP server connections
- Implement result caching for expensive operations

---

This comprehensive API reference provides complete coverage of the TFrameX framework's capabilities, configuration options, and specifications. Use this document as a reference for building applications with TFrameX.