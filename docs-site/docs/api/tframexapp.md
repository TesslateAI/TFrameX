---
sidebar_position: 2
title: TFrameXApp
---

# TFrameXApp API Reference

The `TFrameXApp` class is the central orchestrator of the TFrameX framework. It manages agents, tools, runtime contexts, and provides the main interface for building AI applications.

## Class Definition

```python
from tframex import TFrameXApp

class TFrameXApp:
    def __init__(
        self,
        memory_backend: Optional[MemoryBackend] = None,
        enable_metrics: bool = False,
        enable_audit: bool = False,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize a TFrameX application.
        
        Args:
            memory_backend: Optional memory backend for state persistence
            enable_metrics: Enable metrics collection
            enable_audit: Enable audit logging
            config: Additional configuration options
        """
```

## Core Methods

### Tool Registration

#### `tool()` Decorator

```python
@app.tool(
    description: str = None,
    name: str = None,
    parameters_schema: Optional[ToolParameters] = None
)
```

Register a function as a tool using decorator syntax.

**Parameters:**
- `description` - Human-readable description of the tool
- `name` - Override the function name (defaults to function name)
- `parameters_schema` - Optional schema for validation

**Example:**

```python
@app.tool(description="Search the web for information")
async def web_search(query: str, max_results: int = 10) -> List[str]:
    # Implementation
    return results
```

#### `register_tool()`

```python
def register_tool(self, tool: Tool) -> None:
    """Register a tool instance directly."""
```

Register a pre-created Tool instance.

**Example:**

```python
from tframex.util.tools import Tool

custom_tool = Tool(
    name="custom_tool",
    func=my_function,
    description="A custom tool"
)

app.register_tool(custom_tool)
```

### Agent Management

#### `register_agent()`

```python
def register_agent(self, agent: Agent) -> None:
    """Register an agent with the application."""
```

Register an agent to make it available for execution.

**Example:**

```python
from tframex.agents.llm_agent import LLMAgent

agent = LLMAgent(
    name="Assistant",
    description="General purpose assistant",
    llm=llm_instance,
    tools=["web_search", "calculator"]
)

app.register_agent(agent)
```

#### `get_agent()`

```python
def get_agent(self, name: str) -> Optional[Agent]:
    """Retrieve a registered agent by name."""
```

Get a registered agent instance.

**Example:**

```python
agent = app.get_agent("Assistant")
if agent:
    print(f"Found agent: {agent.description}")
```

#### `list_agents()`

```python
def list_agents(self) -> List[str]:
    """Return list of registered agent names."""
```

Get all registered agent names.

**Example:**

```python
agents = app.list_agents()
print(f"Available agents: {', '.join(agents)}")
```

### Runtime Context

#### `run_context()`

```python
async def run_context(self) -> RuntimeContext:
    """Create a runtime context for executing agents and flows."""
```

Create an execution context. Must be used with async context manager.

**Example:**

```python
async with app.run_context() as rt:
    # Use runtime to execute agents
    response = await rt.call_agent("Assistant", "Hello!")
```

### Configuration

#### `configure()`

```python
def configure(self, config: Dict[str, Any]) -> None:
    """Update application configuration."""
```

Update configuration after initialization.

**Example:**

```python
app.configure({
    "max_retries": 3,
    "timeout": 30,
    "enable_caching": True
})
```

## Runtime Context Methods

The runtime context provides methods for executing agents and flows.

### `call_agent()`

```python
async def call_agent(
    self,
    agent_name: str,
    prompt: str,
    context: Optional[Dict[str, Any]] = None,
    stream: bool = False
) -> Union[str, AsyncGenerator[str, None]]:
    """
    Call an agent with a prompt.
    
    Args:
        agent_name: Name of the agent to call
        prompt: The prompt/message for the agent
        context: Optional context data
        stream: Enable streaming responses
        
    Returns:
        Agent response as string or async generator if streaming
    """
```

**Example:**

```python
# Simple call
response = await rt.call_agent("Assistant", "What's the weather?")

# With context
response = await rt.call_agent(
    "Assistant", 
    "Analyze this data",
    context={"data": dataset}
)

# Streaming
async for chunk in await rt.call_agent("Writer", "Write a story", stream=True):
    print(chunk, end="")
```

### `run_flow()`

```python
async def run_flow(
    self,
    flow: Flow,
    initial_input: Optional[Dict[str, Any]] = None,
    **kwargs
) -> FlowResult:
    """
    Execute a flow pattern.
    
    Args:
        flow: The flow to execute
        initial_input: Initial input data
        **kwargs: Additional flow arguments
        
    Returns:
        FlowResult with outputs and metadata
    """
```

**Example:**

```python
from tframex.flows import SequentialFlow

flow = SequentialFlow(
    name="content_pipeline",
    steps=[
        ("Researcher", "Research: {topic}"),
        ("Writer", "Write based on: {research_result}")
    ]
)

result = await rt.run_flow(flow, topic="AI ethics")
print(result.final_output)
```

### `interactive_chat()`

```python
async def interactive_chat(
    self,
    agent_name: str = "Assistant",
    welcome_message: Optional[str] = None
) -> None:
    """Start an interactive chat session with an agent."""
```

**Example:**

```python
async with app.run_context() as rt:
    await rt.interactive_chat(
        agent_name="Assistant",
        welcome_message="Hello! How can I help you today?"
    )
```

## Advanced Features

### Memory Integration

```python
from tframex.memory import RedisMemory

# Initialize with memory backend
app = TFrameXApp(
    memory_backend=RedisMemory(host="localhost", port=6379)
)

# Memory is automatically available to agents
@app.tool()
async def remember(key: str, value: str) -> str:
    await app.memory.set(key, value)
    return f"Remembered {key}"

@app.tool()
async def recall(key: str) -> str:
    value = await app.memory.get(key)
    return value or "Not found"
```

### Metrics Collection

```python
# Enable metrics
app = TFrameXApp(enable_metrics=True)

# Access metrics
metrics = app.get_metrics()
print(f"Total agent calls: {metrics['agent_calls']}")
print(f"Average response time: {metrics['avg_response_time']}")
```

### Audit Logging

```python
# Enable audit logging
app = TFrameXApp(enable_audit=True)

# Audit logs are automatically created for:
# - Agent calls
# - Tool executions
# - Flow runs
# - Errors and exceptions

# Access audit logs
logs = app.get_audit_logs(
    start_time=datetime.now() - timedelta(hours=1),
    agent_name="Assistant"
)
```

### Plugin System

```python
from tframex.plugins import Plugin

class CustomPlugin(Plugin):
    def on_app_init(self, app: TFrameXApp):
        # Add custom initialization
        pass
    
    def on_agent_called(self, agent_name: str, prompt: str):
        # Hook into agent calls
        pass

app = TFrameXApp()
app.register_plugin(CustomPlugin())
```

## Error Handling

```python
from tframex.exceptions import (
    TFrameXError,
    AgentNotFoundError,
    ToolExecutionError,
    FlowExecutionError
)

try:
    async with app.run_context() as rt:
        response = await rt.call_agent("NonExistent", "Hello")
except AgentNotFoundError as e:
    print(f"Agent not found: {e}")
except ToolExecutionError as e:
    print(f"Tool failed: {e}")
except TFrameXError as e:
    print(f"Framework error: {e}")
```

## Best Practices

### 1. Application Lifecycle

```python
# Create once, reuse
app = TFrameXApp()

# Register all tools and agents at startup
setup_tools(app)
setup_agents(app)

# Create runtime contexts as needed
async def handle_request(user_input):
    async with app.run_context() as rt:
        return await rt.call_agent("Assistant", user_input)
```

### 2. Tool Organization

```python
# Group related tools
class DataTools:
    @staticmethod
    def register(app: TFrameXApp):
        @app.tool()
        async def read_csv(path: str) -> pd.DataFrame:
            return pd.read_csv(path)
        
        @app.tool()
        async def analyze_data(df: pd.DataFrame) -> dict:
            return {"rows": len(df), "columns": len(df.columns)}

# Register tool groups
DataTools.register(app)
```

### 3. Configuration Management

```python
import os
from dotenv import load_dotenv

load_dotenv()

# Environment-based configuration
config = {
    "openai_api_key": os.getenv("OPENAI_API_KEY"),
    "redis_url": os.getenv("REDIS_URL", "redis://localhost:6379"),
    "enable_metrics": os.getenv("ENABLE_METRICS", "false").lower() == "true"
}

app = TFrameXApp(config=config)
```

### 4. Testing

```python
import pytest
from tframex.testing import MockLLM, TestApp

@pytest.fixture
def test_app():
    app = TestApp()  # Test-friendly app instance
    
    # Register test tools
    @app.tool()
    async def mock_search(query: str) -> str:
        return f"Mock results for: {query}"
    
    # Register test agent
    agent = LLMAgent(
        name="TestAgent",
        llm=MockLLM(responses=["Test response"]),
        tools=["mock_search"]
    )
    app.register_agent(agent)
    
    return app

async def test_agent_call(test_app):
    async with test_app.run_context() as rt:
        response = await rt.call_agent("TestAgent", "Test prompt")
        assert response == "Test response"
```

## Performance Optimization

### Connection Pooling

```python
# Reuse LLM connections
llm_pool = OpenAIChatLLM(
    connection_pool_size=20,
    max_concurrent_requests=10
)

# Share across agents
for i in range(5):
    agent = LLMAgent(
        name=f"Worker{i}",
        llm=llm_pool  # Shared connection pool
    )
    app.register_agent(agent)
```

### Caching

```python
from functools import lru_cache

@app.tool()
@lru_cache(maxsize=100)
async def expensive_operation(param: str) -> str:
    # Cached at tool level
    result = await complex_calculation(param)
    return result
```

### Batch Processing

```python
async def process_batch(app: TFrameXApp, items: List[str]):
    async with app.run_context() as rt:
        # Process in parallel
        tasks = [
            rt.call_agent("Processor", item)
            for item in items
        ]
        results = await asyncio.gather(*tasks)
        return results
```

## Thread Safety

TFrameXApp is designed to be thread-safe for registration operations:

```python
# Safe to call from multiple threads
app.register_agent(agent1)  # Thread 1
app.register_tool(tool1)    # Thread 2

# Runtime contexts should be created per async task
async def worker(app: TFrameXApp, task_id: int):
    async with app.run_context() as rt:
        # Each worker has its own runtime
        result = await rt.call_agent("Worker", f"Task {task_id}")
        return result
```

## Migration Guide

### From v1.0.x to v1.1.0

```python
# Old (v1.0.x)
app = TFrameXApp()
result = app.run_agent("Assistant", "Hello")  # Sync

# New (v1.1.0)
app = TFrameXApp()
async with app.run_context() as rt:
    result = await rt.call_agent("Assistant", "Hello")  # Async
```

## See Also

- [Agents API](agents) - Agent creation and management
- [Tools API](tools) - Tool system reference
- [Flows API](flows) - Workflow orchestration
- [Examples](../examples/overview) - Working code examples