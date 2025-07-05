---
sidebar_position: 1
title: Overview
---

# Core Concepts Overview

TFrameX is built on a few powerful core concepts that work together to create sophisticated AI applications. Understanding these concepts will help you build better agents and workflows.

## The TFrameX Architecture

![Core Component Architecture](/img/02-core-component-architecture.png)

At its heart, TFrameX follows a clean, layered architecture:

1. **Application Layer** (`TFrameXApp`) - Configuration and registry
2. **Runtime Layer** (`TFrameXRuntimeContext`) - Execution environment
3. **Engine Layer** (`Engine`) - Core orchestration logic
4. **Component Layer** - Agents, Tools, Flows, and Patterns

## Key Concepts

### 🤖 Agents

Agents are the intelligent actors in your system. They can:
- Process natural language inputs
- Make decisions using LLMs
- Execute tools to interact with external systems
- Collaborate with other agents

**Types of Agents:**
- **LLMAgent**: Uses a language model for reasoning and decision-making
- **ToolAgent**: Directly executes a specific tool without LLM reasoning
- **Custom Agents**: Extend `BaseAgent` for specialized behavior

[Learn more about Agents →](agents)

### 🛠️ Tools

Tools give agents the ability to interact with the world. They are:
- Python functions that agents can call
- Automatically described to the LLM
- Type-safe with parameter validation
- Async-first for performance

**Example Tools:**
- API integrations
- Database operations
- File system access
- Calculations and data processing

[Learn more about Tools →](tools)

### 🌊 Flows

Flows orchestrate complex multi-step workflows. They:
- Chain multiple agent interactions
- Support conditional logic
- Enable parallel processing
- Maintain context across steps

**Flow Capabilities:**
- Sequential execution
- Parallel processing
- Conditional routing
- Nested patterns

[Learn more about Flows →](flows)

### 🎨 Patterns

Patterns are reusable workflow templates that solve common problems:

- **Sequential Pattern**: Execute agents one after another
- **Parallel Pattern**: Run multiple agents simultaneously
- **Router Pattern**: Choose execution path based on conditions
- **Discussion Pattern**: Multi-agent collaborative discussions

[Learn more about Patterns →](patterns)

### 💾 Memory

Memory systems maintain conversation context and agent state:
- Conversation history
- Tool execution results
- Cross-agent communication
- Persistent storage options

[Learn more about Memory →](memory)

### 🔌 MCP Integration

Model Context Protocol (MCP) enables connection to external services:
- Standardized tool interface
- Server discovery and management
- Resource access (files, data)
- Prompt templates

![MCP Integration Architecture](/img/03-mcp-integration-architecture.png)

[Learn more about MCP →](mcp-integration)

## How Components Work Together

### 1. Agent-Tool Interaction

```python
# Tool definition
@app.tool(description="Get weather data")
async def get_weather(city: str) -> str:
    return f"Weather in {city}: Sunny, 72°F"

# Agent uses tool
agent = LLMAgent(
    name="WeatherBot",
    tools=["get_weather"],
    system_prompt="You help users with weather information."
)
```

### 2. Agent-Agent Communication

```python
# Agents can call other agents
coordinator = LLMAgent(
    name="Coordinator",
    callable_agents=["Researcher", "Writer"],
    system_prompt="You coordinate research and writing tasks."
)
```

### 3. Flow Orchestration

```python
# Complex workflow with patterns
flow = Flow("ContentPipeline")
flow.add_step("researcher")
flow.add_pattern_step(
    ParallelPattern("reviewers", ["editor", "fact_checker"])
)
flow.add_step("publisher")
```

## Execution Model

Understanding how TFrameX executes your code is crucial:

### 1. Initialization Phase
```python
app = TFrameXApp()  # Create application
app.register_agent(agent)  # Register components
app.register_tool(tool)
```

### 2. Runtime Phase
```python
async with app.run_context() as rt:  # Enter runtime
    result = await rt.call_agent("AgentName", "input")  # Execute
```

### 3. Context Management
- Automatic resource cleanup
- Connection pooling
- Error handling
- State management

## Design Principles

TFrameX follows these core principles:

### 1. **Composability**
Build complex systems from simple, reusable components.

### 2. **Flexibility**
Support multiple LLMs, tools, and deployment options.

### 3. **Type Safety**
Leverage Python's type system for better development experience.

### 4. **Async-First**
Built for performance with native async/await support.

### 5. **Production-Ready**
Include enterprise features like monitoring, security, and scalability.

## Common Patterns

### Simple Assistant
```python
# Single agent with tools
app = TFrameXApp()

@app.tool(description="Calculate sum")
async def add(a: int, b: int) -> int:
    return a + b

agent = LLMAgent(
    name="Assistant",
    tools=["add"],
    llm=OpenAIChatLLM()
)
app.register_agent(agent)
```

### Multi-Agent System
```python
# Specialized agents working together
researcher = LLMAgent(name="Researcher", ...)
writer = LLMAgent(name="Writer", ...)
editor = LLMAgent(name="Editor", ...)

coordinator = LLMAgent(
    name="Coordinator",
    callable_agents=["Researcher", "Writer", "Editor"]
)
```

### Workflow Automation
```python
# Automated content pipeline
flow = Flow("ContentCreation")
flow.add_step("topic_analyzer")
flow.add_pattern_step(
    RouterPattern("content_type", {
        "technical": "tech_writer",
        "marketing": "marketing_writer"
    })
)
flow.add_step("editor")
flow.add_step("publisher")
```

## Best Practices

### 1. Start Simple
Begin with a single agent and gradually add complexity.

### 2. Use Type Hints
```python
async def process_data(data: list[dict]) -> dict[str, Any]:
    """Process data with clear types."""
    pass
```

### 3. Handle Errors Gracefully
```python
@app.tool(description="Safe operation")
async def safe_operation(param: str) -> str:
    try:
        result = risky_operation(param)
        return f"Success: {result}"
    except Exception as e:
        return f"Error: {str(e)}"
```

### 4. Log Important Events
```python
import logging
logger = logging.getLogger(__name__)

@app.tool()
async def important_operation(param: str) -> str:
    logger.info(f"Starting operation with {param}")
    result = do_work(param)
    logger.info(f"Operation completed: {result}")
    return result
```

## Next Steps

Now that you understand the core concepts:

1. Deep dive into [Agents](agents) to master agent creation
2. Explore [Tools](tools) to extend agent capabilities
3. Learn about [Flows](flows) for complex workflows
4. Study [Patterns](patterns) for reusable solutions
5. Understand [Memory](memory) for stateful applications
6. Integrate with [MCP Servers](mcp-integration) for external services

## Visual Learning

For visual learners, here's how data flows through the system:

![Agent Execution Flow](/img/04-agent-execution-flow.png)

This diagram shows:
1. User input enters the system
2. TFrameXApp routes to the appropriate agent
3. Agent processes with LLM and tools
4. Results return to the user

## Getting Help

- 📖 [API Reference](../api/overview) for detailed documentation
- 💬 [Discord Community](https://discord.gg/DkzMzwBTaw) for questions
- 🎯 [Examples](../examples/overview) for practical implementations