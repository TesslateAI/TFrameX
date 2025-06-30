# TFrameX Architecture Documentation

## Overview

**TFrameX** (The Extensible Task & Flow Orchestration Framework for LLMs) is a Python framework designed to build sophisticated, multi-agent LLM applications with complex workflows. This document provides a comprehensive overview of the framework's architecture, design patterns, and core components.

## Table of Contents

1. [Core Architecture](#core-architecture)
2. [Component Overview](#component-overview)
3. [Design Patterns](#design-patterns)
4. [Data Flow](#data-flow)
5. [Extension Points](#extension-points)
6. [Integration Architecture](#integration-architecture)

## Core Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                       TFrameX Application                       │
├─────────────────┬─────────────────┬─────────────────┬───────────┤
│   Agent Layer   │   Flow Layer    │   Tool Layer    │ MCP Layer │
├─────────────────┼─────────────────┼─────────────────┼───────────┤
│ • LLMAgent      │ • Flow          │ • Native Tools  │ • Manager │
│ • ToolAgent     │ • Patterns      │ • Meta Tools    │ • Servers │
│ • BaseAgent     │ • FlowContext   │ • Agent-as-Tool │ • Connectors│
├─────────────────┴─────────────────┴─────────────────┴───────────┤
│                    Runtime Context & Engine                     │
├─────────────────────────────────────────────────────────────────┤
│                         LLM Layer                               │
│              • OpenAI API • Local Models • Plugins             │
├─────────────────────────────────────────────────────────────────┤
│                        Memory Layer                             │
│                  • In-Memory • Custom Stores                   │
└─────────────────────────────────────────────────────────────────┘
```

### Core Principles

1. **Modularity**: Clear separation of concerns between components
2. **Extensibility**: Plugin architecture for LLMs, memory stores, and tools
3. **Composability**: Agents, patterns, and flows can be nested and combined
4. **Asynchronicity**: Full async/await support throughout the stack
5. **Type Safety**: Pydantic models for reliable data handling

## Component Overview

### 1. Application Layer (`TFrameXApp`)

The central registry and configuration manager for the entire framework.

**Key Responsibilities:**
- Agent and tool registration via decorators
- Default LLM and memory store configuration
- Runtime context creation
- MCP server management

**Key Methods:**
```python
@app.agent(name="MyAgent", tools=["tool1"], mcp_tools_from_servers=["server1"])
@app.tool(name="my_tool", description="...")
app.register_flow(flow_instance)
app.run_context(llm_override=None)
```

### 2. Runtime Context (`TFrameXRuntimeContext`)

Manages the execution environment for agents and flows with proper resource lifecycle management.

**Key Responsibilities:**
- LLM client lifecycle management
- MCP server initialization and cleanup
- Flow and agent execution coordination
- Resource cleanup on context exit

**Usage Pattern:**
```python
async with app.run_context() as rt:
    response = await rt.call_agent("AgentName", message)
    flow_result = await rt.run_flow("FlowName", initial_message)
```

### 3. Execution Engine (`Engine`)

Core execution engine that manages agent instantiation, tool routing, and execution.

**Key Responsibilities:**
- Lazy agent instantiation with dependency resolution
- LLM instance resolution (Agent → Context → App)
- Tool routing and execution
- Agent-as-tool orchestration

**Tool Routing Logic:**
1. MCP meta-tools (prefixed with `tframex_`)
2. MCP server tools (prefixed with `server_alias__`)
3. Native TFrameX tools
4. Callable agents

### 4. Agent Architecture

#### BaseAgent
Abstract base class providing common functionality:

```python
class BaseAgent:
    def __init__(self, agent_id, llm, tools, memory, callable_agent_definitions, **config):
        self.agent_id = agent_id
        self.llm = llm
        self.tools = tools  # Dict[str, Tool]
        self.memory = memory
        self.callable_agent_definitions = callable_agent_definitions
        self.config = config
    
    async def run(self, input_message, **kwargs) -> Message:
        # Abstract method to be implemented by subclasses
        pass
    
    def _render_system_prompt(self, **template_vars) -> Message:
        # Template variable substitution
        pass
    
    def _post_process_llm_response(self, response) -> Message:
        # Think tag stripping and post-processing
        pass
```

#### LLMAgent
Primary agent type for LLM-based decision making:

**Key Features:**
- Iterative tool calling with configurable max iterations
- MCP tool integration
- Memory management
- Error handling and fallbacks

**Execution Flow:**
1. Add user message to memory
2. Render system prompt with template variables
3. Prepare tool definitions (native + MCP + callable agents)
4. Call LLM with messages and tools
5. Process tool calls iteratively
6. Return final response

#### ToolAgent
Lightweight agent for direct tool execution without LLM involvement.

### 5. Flow System

#### Flow
Defines sequences of operations with step-by-step execution:

```python
flow = Flow(flow_name="MyFlow", description="...")
flow.add_step("AgentName")
flow.add_step(PatternInstance)
```

#### FlowContext
Carries state between flow steps:

```python
class FlowContext:
    current_message: Message      # Output of last step
    history: List[Message]        # All flow messages
    shared_data: Dict[str, Any]   # Step-to-step data sharing
```

#### Patterns
Reusable multi-agent interaction templates:

- **SequentialPattern**: Execute tasks in order
- **ParallelPattern**: Execute tasks concurrently
- **RouterPattern**: Dynamic routing based on agent decision
- **DiscussionPattern**: Multi-round agent discussions

### 6. Tool System

#### Tool Registration and Execution
```python
@app.tool(description="Tool description")
async def my_tool(param1: str, param2: int = 5) -> str:
    return f"Result: {param1} * {param2}"
```

#### Tool Definition Generation
- Automatic schema inference from function signatures
- Type hint processing for parameter validation
- OpenAI function calling format compatibility

#### Agent-as-Tool Paradigm
Agents can call other registered agents as tools:

```python
@app.agent(callable_agents=["SpecialistAgent"])
async def supervisor_agent():
    pass
```

### 7. Memory System

#### BaseMemoryStore Interface
```python
class BaseMemoryStore:
    async def add_message(self, message: Message) -> None
    async def get_history(self, limit: Optional[int] = None) -> List[Message]
    async def clear(self) -> None
```

#### InMemoryMemoryStore
Default implementation with:
- Rolling window support
- Role-based filtering
- Message limit enforcement

### 8. LLM Integration

#### BaseLLMWrapper Interface
```python
class BaseLLMWrapper:
    async def chat_completion(self, messages: List[Message], **kwargs) -> Message
    async def close(self) -> None
    @property
    def model_id(self) -> str
```

#### OpenAIChatLLM
Production-ready implementation supporting:
- OpenAI API compatibility
- Local server support (Ollama, LiteLLM)
- Streaming and non-streaming responses
- Tool calling integration
- Robust error handling with retries

## Design Patterns

### 1. Dependency Injection
- LLM resolution: Agent override → Context override → App default
- Memory resolution: Agent override → App factory
- Tool resolution: Engine resolves from app registry

### 2. Decorator Pattern
Clean registration API:
```python
@app.agent(name="MyAgent", tools=["tool1"])
@app.tool(description="My tool")
```

### 3. Strategy Pattern
- Pluggable LLM providers
- Custom memory stores
- Extensible tool system

### 4. Template Method Pattern
- BaseAgent defines execution template
- Subclasses implement specific behavior
- Common post-processing in base class

### 5. Composite Pattern
- Flows contain patterns and agents
- Patterns can contain other patterns
- Hierarchical task decomposition

## Data Flow

### Agent Execution Flow

```
User Input → Runtime Context → Engine → Agent Instance
                                          ↓
Template Variables → System Prompt Rendering
                                          ↓
Memory Retrieval → Message Preparation → LLM Call
                                          ↓
Tool Call Processing → Engine Tool Routing → Tool Execution
                                          ↓
Tool Results → Memory Update → Response Post-processing
                                          ↓
Final Response ← Runtime Context ← Engine ← Agent Instance
```

### Flow Execution Flow

```
Initial Message → Flow → Step 1 (Agent/Pattern)
                          ↓
FlowContext Update → Step 2 (Agent/Pattern)
                          ↓
FlowContext Update → ... → Final Step
                          ↓
Final FlowContext ← Flow ← Last Step
```

## Extension Points

### 1. Custom Agents
Extend `BaseAgent` or `LLMAgent`:
```python
class CustomAgent(BaseAgent):
    async def run(self, input_message, **kwargs):
        # Custom logic
        pass
```

### 2. Custom LLM Providers
Implement `BaseLLMWrapper`:
```python
class CustomLLM(BaseLLMWrapper):
    async def chat_completion(self, messages, **kwargs):
        # Custom LLM integration
        pass
```

### 3. Custom Memory Stores
Implement `BaseMemoryStore`:
```python
class DatabaseMemoryStore(BaseMemoryStore):
    async def add_message(self, message):
        # Database persistence
        pass
```

### 4. Custom Tools
Simple function decoration:
```python
@app.tool()
async def custom_tool(param: str) -> str:
    # Tool implementation
    return result
```

### 5. Custom Patterns
Extend pattern classes:
```python
class CustomPattern(BasePattern):
    async def execute(self, context, engine):
        # Custom execution logic
        pass
```

## Integration Architecture

### MCP Integration Layer

The Model Context Protocol (MCP) integration adds external service connectivity:

```
TFrameX Application
├── MCP Manager
│   ├── Server Connectors (stdio, HTTP)
│   ├── Tool Aggregation
│   └── Resource/Prompt Management
├── Meta Tools (tframex_list_mcp_servers, etc.)
└── Agent MCP Configuration
```

**Key Integration Points:**
1. **App Level**: MCP manager initialization and lifecycle
2. **Agent Level**: MCP tool selection and configuration
3. **Engine Level**: MCP tool routing and execution
4. **Runtime Level**: MCP server connection management

### External Service Integration

TFrameX supports multiple integration patterns:

1. **Native Tools**: Direct Python function integration
2. **MCP Servers**: Standardized protocol for external services
3. **Agent-as-Tool**: Internal agent delegation
4. **API Integration**: HTTP/REST service calls via tools

## Performance Considerations

### 1. Lazy Loading
- Agents instantiated only when needed
- Per-context agent instances for isolation
- On-demand tool resolution

### 2. Concurrent Execution
- Parallel pattern execution
- Async/await throughout
- Non-blocking I/O operations

### 3. Resource Management
- Automatic LLM client cleanup
- MCP connection pooling
- Memory store optimization

### 4. Caching
- Agent instance caching per context
- Tool definition caching
- Template compilation caching

## Security Considerations

### 1. Input Validation
- Pydantic model validation
- Tool parameter sanitization
- Template variable escaping

### 2. Execution Isolation
- Per-context agent instances
- Tool execution sandboxing
- Memory isolation between contexts

### 3. Credential Management
- Environment variable usage
- Secure MCP server configuration
- No credential logging

This architecture provides a robust, extensible foundation for building sophisticated multi-agent LLM applications while maintaining clean separation of concerns and supporting various integration patterns.