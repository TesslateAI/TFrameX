---
sidebar_position: 1
title: API Overview
---

# API Reference Overview

TFrameX provides a comprehensive Python API for building sophisticated multi-agent LLM applications. This reference covers all public APIs, their usage patterns, and best practices.

## API Organization

The TFrameX API is organized into several key modules:

### Core Application
- **[TFrameXApp](tframexapp)** - Main application class for managing agents, tools, and runtime
- **Runtime** - Execution context for running agents and flows

### Agent System
- **[Agents](agents)** - Base classes and implementations for AI agents
- **LLMAgent** - Standard agent powered by language models
- **DelegatorAgent** - Agents that can delegate to other agents

### Tool System
- **[Tools](tools)** - Tool registration and execution framework
- **Tool Decorators** - Simplified tool creation with `@app.tool()`
- **Tool Parameters** - Schema-based parameter validation

### Orchestration
- **[Flows](flows)** - Workflow orchestration patterns
- **[Patterns](patterns)** - Built-in patterns (Sequential, Parallel, Router, Discussion)
- **Custom Patterns** - Creating your own orchestration patterns

### Extensions
- **[MCP Integration](mcp)** - Model Context Protocol support
- **[Memory Systems](memory)** - State persistence and retrieval
- **Enterprise Features** - RBAC, metrics, audit logging

## Quick Reference

### Creating an Application

```python
from tframex import TFrameXApp

app = TFrameXApp()
```

### Defining Tools

```python
@app.tool(description="Get current time")
async def get_time() -> str:
    from datetime import datetime
    return datetime.now().isoformat()
```

### Creating Agents

```python
from tframex.agents.llm_agent import LLMAgent
from tframex.util.llms import OpenAIChatLLM

agent = LLMAgent(
    name="Assistant",
    description="Helpful AI assistant",
    llm=OpenAIChatLLM(),
    tools=["get_time"],
    system_prompt="You are a helpful assistant."
)

app.register_agent(agent)
```

### Running Agents

```python
async with app.run_context() as rt:
    response = await rt.call_agent("Assistant", "What time is it?")
    print(response)
```

### Building Flows

```python
from tframex.flows import SequentialFlow

flow = SequentialFlow(
    name="research_flow",
    description="Research and write content",
    steps=[
        ("Researcher", "Research topic: {topic}"),
        ("Writer", "Write article based on research: {research_result}")
    ]
)

result = await rt.run_flow(flow, topic="AI agents")
```

## API Conventions

### Async-First Design

All agent and tool calls are asynchronous:

```python
# Correct
async def my_tool():
    return await some_async_operation()

# Also correct (sync tools are wrapped automatically)
def simple_tool():
    return "result"
```

### Type Hints

TFrameX uses Python type hints extensively:

```python
from typing import List, Dict, Optional

@app.tool()
async def search(
    query: str,
    max_results: int = 10,
    filters: Optional[Dict[str, str]] = None
) -> List[Dict[str, str]]:
    # Implementation
    pass
```

### Error Handling

```python
from tframex.exceptions import AgentError, ToolError

try:
    result = await rt.call_agent("Agent", "prompt")
except AgentError as e:
    print(f"Agent error: {e}")
except ToolError as e:
    print(f"Tool error: {e}")
```

### Context Managers

Runtime contexts ensure proper resource cleanup:

```python
# Recommended pattern
async with app.run_context() as rt:
    # Use runtime
    pass

# Manual management (not recommended)
rt = await app.run_context().__aenter__()
try:
    # Use runtime
    pass
finally:
    await rt.__aexit__(None, None, None)
```

## Common Patterns

### Tool with Validation

```python
from pydantic import BaseModel, Field

class SearchParams(BaseModel):
    query: str = Field(..., min_length=1)
    max_results: int = Field(10, ge=1, le=100)

@app.tool()
async def validated_search(params: SearchParams) -> list:
    # Automatic validation via Pydantic
    return await search_api(params.query, params.max_results)
```

### Agent with Custom Tools

```python
agent = LLMAgent(
    name="DataAnalyst",
    llm=llm,
    tools=["read_csv", "analyze_data", "create_chart"],
    system_prompt="""You are a data analyst. 
    Use your tools to analyze data and create visualizations."""
)
```

### Hierarchical Agents

```python
supervisor = DelegatorAgent(
    name="Supervisor",
    agents=["Researcher", "Writer", "Editor"],
    system_prompt="Delegate tasks to specialized agents."
)
```

### Flow with Error Handling

```python
flow = SequentialFlow(
    name="safe_flow",
    steps=[...],
    on_error="continue"  # or "stop"
)
```

## Performance Considerations

### Connection Pooling

```python
# Reuse LLM instances
llm = OpenAIChatLLM(
    connection_pool_size=10,
    max_retries=3
)

# Share across agents
agent1 = LLMAgent(name="A1", llm=llm)
agent2 = LLMAgent(name="A2", llm=llm)
```

### Batch Operations

```python
# Process multiple inputs efficiently
async def process_batch(items):
    tasks = [rt.call_agent("Agent", item) for item in items]
    results = await asyncio.gather(*tasks)
    return results
```

### Memory Management

```python
# Use memory backends for large state
from tframex.memory import RedisMemory

app = TFrameXApp(
    memory_backend=RedisMemory(
        host="localhost",
        max_memory_mb=1000
    )
)
```

## Best Practices

1. **Use Type Hints** - Enable better IDE support and validation
2. **Handle Errors** - Wrap agent calls in try-except blocks
3. **Async Tools** - Prefer async functions for I/O operations
4. **Resource Cleanup** - Always use context managers
5. **Validate Input** - Use Pydantic models for complex parameters
6. **Limit Scope** - Give agents specific, focused responsibilities
7. **Test Tools** - Unit test tools independently
8. **Monitor Usage** - Track API costs and performance

## Version Compatibility

This documentation covers TFrameX v1.1.0. The API follows semantic versioning:

- **Major** (1.x.x) - Breaking changes
- **Minor** (x.1.x) - New features, backward compatible
- **Patch** (x.x.1) - Bug fixes

## Getting Help

- **Type Stubs** - Full type information for IDE support
- **Docstrings** - Inline documentation for all public APIs
- **Examples** - Working code in the [examples section](../examples/overview)
- **Source Code** - Open source on [GitHub](https://github.com/TesslateAI/TFrameX)

## Next Steps

Explore specific API sections:

- [TFrameXApp](tframexapp) - Core application API
- [Agents](agents) - Agent creation and management
- [Tools](tools) - Tool system reference
- [Flows](flows) - Workflow orchestration
- [Patterns](patterns) - Built-in patterns
- [MCP](mcp) - Model Context Protocol
- [Memory](memory) - State management