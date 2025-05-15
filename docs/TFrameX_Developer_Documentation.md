# TFrameX Developer Documentation

## Table of Contents
1. [Introduction](#introduction)
2. [Core Concepts](#core-concepts)
3. [Getting Started](#getting-started)
   - [Installation](#installation)
   - [Basic Example](#basic-example)
4. [Architecture Overview](#architecture-overview)
5. [Key Components In-Depth](#key-components-in-depth)
   - [TFrameXApp](#tframexapp)
   - [TFrameXRuntimeContext](#tframexruntimecontext)
   - [Engine](#engine)
   - [Agents (BaseAgent, LLMAgent, ToolAgent)](#agents)
   - [Tools](#tools)
   - [Flows](#flows)
   - [FlowContext](#flowcontext)
   - [Patterns](#patterns)
     - [SequentialPattern](#sequentialpattern)
     - [ParallelPattern](#parallelpattern)
     - [RouterPattern](#routerpattern)
     - [DiscussionPattern](#discussionpattern)
     - [DelegatePattern](#delegatepattern)
   - [LLM Integration (BaseLLMWrapper, OpenAIChatLLM)](#llm-integration)
   - [Memory Management (BaseMemoryStore, InMemoryMemoryStore)](#memory-management)
   - [Logging](#logging)
6. [Building Agentic Systems](#building-agentic-systems)
   - [Defining Agents](#defining-agents)
   - [Defining Tools](#defining-tools)
   - [Orchestrating with Flows and Patterns](#orchestrating-with-flows-and-patterns)
   - [Agent-as-Tool (Supervisor Agents)](#agent-as-tool-supervisor-agents)
   - [Managing Agent Memory](#managing-agent-memory)
   - [Using Template Variables](#using-template-variables)
7. [Extending TFrameX](#extending-tframex)
   - [Custom Agents](#custom-agents)
   - [Custom Patterns](#custom-patterns)
   - [Custom LLM Wrappers](#custom-llm-wrappers)
   - [Custom Memory Stores](#custom-memory-stores)
8. [Testing](#testing)
9. [Examples](#examples)

## 1. Introduction

TFrameX is a Python framework designed for building complex, multi-agent applications powered by Large Language Models (LLMs). It provides a structured way to define intelligent agents, equip them with tools, and orchestrate their interactions through flexible workflows called "Flows" and "Patterns." TFrameX aims to simplify the development of sophisticated AI systems where multiple agents collaborate to achieve complex goals.

Key features include:
- Modular agent definition with customizable prompts, tools, and LLMs.
- Seamless integration of custom Python functions as tools for agents.
- Powerful flow and pattern system for orchestrating agent interactions (sequential, parallel, routing, discussions, delegation).
- Agent-as-Tool paradigm for hierarchical agent structures.
- Pluggable LLM wrappers and memory stores.
- Enhanced logging for observability, including detailed LLM interaction traces.

## 2. Core Concepts

- **Agent:** An autonomous entity, typically powered by an LLM, capable of reasoning, using tools, and communicating.
- **Tool:** A Python function that an agent can call to interact with external systems or perform specific computations.
- **Flow:** A defined sequence or graph of operations, orchestrating how agents and patterns interact to process an initial input and produce a final output.
- **Pattern:** A reusable template for common multi-agent interaction structures (e.g., `SequentialPattern`, `DelegatePattern`). Patterns are steps within a Flow.
- **Message:** The primary data structure for communication between agents and components, based on an OpenAI-like schema.
- **FlowContext:** An object that holds the state (`current_message`, `history`, `shared_data`) during a single execution of a Flow.
- **Engine:** The core execution mechanism within a `TFrameXRuntimeContext` that instantiates and runs agents.
- **LLM Wrapper:** An abstraction layer for interacting with different LLM APIs.
- **Memory Store:** A component responsible for storing and retrieving conversation history for agents.

## 3. Getting Started

### Installation
Install TFrameX using pip:
```bash
pip install tframex
```
Ensure you have Python 3.8+ installed. Core dependencies are listed in `pyproject.toml`. For examples, you might need additional packages like `aiohttp` or `Flask`.

For development, clone the repository and install in editable mode:
```bash
# Using uv (recommended)
uv venv
source .venv/bin/activate # or .venv\Scripts\Activate.ps1
uv pip install -e ".[examples,dev]"

# Or using pip
python -m venv .venv
source .venv/bin/activate
pip install -e ".[examples,dev]"
```

Set up your LLM environment variables (e.g., in a `.env` file):
```env
OPENAI_API_BASE="http://localhost:11434/v1" # For Ollama
OPENAI_API_KEY="ollama"
OPENAI_MODEL_NAME="llama3"
```

### Basic Example

```python
import asyncio
import os
from dotenv import load_dotenv
from tframex import TFrameXApp, OpenAIChatLLM, Message, Flow, SequentialPattern

load_dotenv()

# 1. Initialize LLM (uses environment variables if not passed explicitly)
my_llm = OpenAIChatLLM(
    model_name=os.getenv("OPENAI_MODEL_NAME", "gpt-3.5-turbo"),
    api_base_url=os.getenv("OPENAI_API_BASE"),
    api_key=os.getenv("OPENAI_API_KEY")
)

# 2. Initialize TFrameXApp
app = TFrameXApp(default_llm=my_llm)

# 3. Define Agents
@app.agent(name="Greeter", system_prompt="Greet the user warmly.")
async def greeter_placeholder(): pass

@app.agent(name="Responder", system_prompt="Respond to the user's greeting.")
async def responder_placeholder(): pass

# 4. Define a Flow
greeting_flow = Flow(flow_name="SimpleGreeting")
greeting_flow.add_step(
    SequentialPattern(pattern_name="GreetAndRespond", steps=["Greeter", "Responder"])
)
app.register_flow(greeting_flow)

# 5. Run the Flow
async def main():
    async with app.run_context() as rt: # TFrameXRuntimeContext
        initial_msg = Message(role="user", content="Hello")
        flow_context = await rt.run_flow("SimpleGreeting", initial_msg)
        print(f"Final Response: {flow_context.current_message.content}")

if __name__ == "__main__":
    if not my_llm.api_base_url:
        print("LLM not configured. Check .env or OpenAIChatLLM parameters.")
    else:
        asyncio.run(main())
```

## 4. Architecture Overview

TFrameX's architecture is designed for modularity and extensibility:
- **`TFrameXApp`**: Central registry and configuration hub.
- **`TFrameXRuntimeContext`**: Session-specific environment, creating an `Engine`.
- **`Engine`**: Handles agent instantiation (resolving LLMs, memory, tools based on app, context, and agent configs) and execution.
- **`Flow`**: Contains a list of steps (agent names or `BasePattern` instances).
- **`BasePattern` subclasses**: Implement specific interaction logic, calling agents via the `Engine`.
- **`BaseAgent` subclasses**: Define agent behavior, with `LLMAgent` being the primary LLM-driven actor.
- **`Message`**: Data model for all communication.
- **Utilities**: `BaseLLMWrapper`, `BaseMemoryStore`, `Tool` provide abstractions.

## 5. Key Components In-Depth

Refer to the [TFrameX API Reference](./TFrameX_API_Reference.md) for detailed API specifications of each component.

### `TFrameXApp`
Manages global configurations (default LLM, memory factory) and registries for tools, agents, and flows.

### `TFrameXRuntimeContext`
Provides an isolated environment for a single execution run (e.g., a user session or a single request). It's an async context manager.

### `Engine`
Created by `TFrameXRuntimeContext`. Responsible for:
- Lazily instantiating agent objects.
- Resolving an agent's LLM (Agent Config > Context LLM > App Default LLM).
- Resolving an agent's memory (Agent Config > App Default Memory Factory).
- Providing registered tools to agents.
- Defining callable sub-agents as tools for a primary agent.
- Executing `agent.run()` and `tool.execute()`.
- Resetting agent memory via `engine.reset_agent()`.

### Agents (`BaseAgent`, `LLMAgent`, `ToolAgent`)
- **`BaseAgent`**: Abstract class defining the agent interface (`run()`, `reset_memory()`). Handles system prompt rendering and `<think>` tag stripping.
- **`LLMAgent`**: The workhorse. Interacts with an LLM, manages conversation history (via its `memory` attribute), can use `tools`, and can call other `callable_agents`. Features `max_tool_iterations`.
- **`ToolAgent`**: A simple agent that directly executes one specific tool. Useful for direct, non-LLM-mediated tool calls within a flow.

### Tools
Python functions (sync or async) decorated with `@app.tool`. Schemas are auto-inferred or can be explicitly defined.

### Flows
Instances of the `Flow` class. Define a multi-step process. Each step is an agent name or a `BasePattern` instance.

### `FlowContext`
Carries the `current_message`, `history` of all messages in the flow, and `shared_data` dictionary through flow execution.

### Patterns
Subclasses of `BasePattern`. They implement specific multi-agent interaction logic. All patterns must implement `execute()` and `reset_agents()`.
- **`SequentialPattern`**: Linear execution.
- **`ParallelPattern`**: Concurrent execution of tasks on the same input. Branched `FlowContexts` are used for isolation.
- **`RouterPattern`**: A router agent's output determines the next step.
- **`DiscussionPattern`**: Manages conversational turns between participants, with an optional moderator.
- **`DelegatePattern`**: A delegator agent generates tasks (strings) which are then processed by a delegatee agent or pattern. Supports `SEQUENTIAL` or `PARALLEL` processing of tasks and an optional "Chain of Agents" (CoA) style summarization for sequential tasks. Can extract a `shared_context` for all delegatees.

### LLM Integration (`BaseLLMWrapper`, `OpenAIChatLLM`)
`OpenAIChatLLM` supports OpenAI-compatible APIs, including features like tool calling and streaming.

### Memory Management (`BaseMemoryStore`, `InMemoryMemoryStore`)
Agents get their own memory instances. `InMemoryMemoryStore` is the default.

### Logging
- `setup_logging()`: Configures console and optional file logging.
- `logs/tframex.log`: General application logs.
- `logs/llm_interactions.log`: Detailed traces of LLM calls (messages, responses, tools called) using `LLMInteractionFormatter` if `save_to_file=True` in `setup_logging`.

## 6. Building Agentic Systems

### Defining Agents
Use `@app.agent`. Key parameters:
- `name`: Unique identifier.
- `system_prompt`: Can include `{template_vars}`, `{available_tools_descriptions}`, `{available_agents_descriptions}`.
- `tools`: List of tool names this agent can use.
- `callable_agents`: List of other agent names this agent can call as tools.
- `llm`: Override default LLM.
- `strip_think_tags`: Default `True`. Set `False` to keep `<think>...</think>` blocks in output.

### Defining Tools
Use `@app.tool`. Provide clear `description` and type hints for auto-schema generation.

### Orchestrating with Flows and Patterns
1. Instantiate `Flow("flow_name")`.
2. Instantiate `Pattern` objects (e.g., `SequentialPattern(...)`).
3. Use `flow.add_step("AgentName")` or `flow.add_step(pattern_instance)`.
4. Register flow: `app.register_flow(my_flow)`.
5. Execute: `await rt.run_flow("flow_name", initial_message)`.

### Agent-as-Tool (Supervisor Agents)
An `LLMAgent` can supervise others by listing them in its `callable_agents` parameter. TFrameX makes these callable agents appear as tools to the supervisor. The supervisor's system prompt should guide it on when and how to delegate (e.g., using `{available_agents_descriptions}`).

### Managing Agent Memory
- Each agent instance within an `Engine` gets its own memory store.
- `InMemoryMemoryStore` is default, configurable via `TFrameXApp` or per-agent.
- Call `await engine.reset_agent("AgentName")` to clear a specific agent's memory.
- Patterns that manage agents should implement `reset_agents(engine)` to allow recursive memory reset (e.g., before rerunning a flow with persistent agent instances within a long-lived `RuntimeContext`).

### Using Template Variables
Pass `template_vars` to `engine.call_agent()` or `flow_template_vars` to `rt.run_flow()`. These are substituted into system prompts.

## 7. Extending TFrameX

Refer to the [TFrameX Extension Guide](./TFrameX_Extension_Guide.md) for detailed instructions on creating custom components.
- **Custom Agents**: Inherit from `BaseAgent` or `LLMAgent`.
- **Custom Patterns**: Inherit from `BasePattern`.
- **Custom LLM Wrappers**: Inherit from `BaseLLMWrapper`.
- **Custom Memory Stores**: Inherit from `BaseMemoryStore`.

## 8. Testing
TFrameX is designed to be testable.
- Use `pytest` with `pytest-asyncio` and `pytest-mock`.
- **Unit tests**: Mock LLM responses and tool execution to test agent logic, pattern orchestration, etc.
- **Integration tests**: Test interactions between components.
- The `conftest.py` in the repository provides examples of mock LLM fixtures and app setup for testing.
- See `tests/` directory for example test structures.

## 9. Examples
The `examples/` directory in the TFrameX repository showcases various use cases:
- `all_design_patterns/`: Demonstrates all core patterns.
- `documentation_generator/`: Shows how to use `flow.generate_documentation()`.
- `redditchatbot/`: A Flask web application with a Reddit analyst agent.
- `website_designer/`:
    - `designer.py`: A sequential flow for designing a website.
    - `designer-updated.py`: An advanced example using the `DelegatePattern` for page-by-page website generation.

This documentation provides a developer-focused overview. For API specifics, consult the [TFrameX API Reference](./TFrameX_API_Reference.md).