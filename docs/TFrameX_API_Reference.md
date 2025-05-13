# TFrameX API Reference

## Table of Contents
- [Application](#application)
  - [TFrameXApp](#tframexapp)
  - [TFrameXRuntimeContext](#tframexruntimecontext)
- [Agents](#agents)
  - [BaseAgent](#baseagent)
  - [LLMAgent](#llmagent)
  - [ToolAgent](#toolagent)
- [Flows](#flows)
  - [Flow](#flow)
  - [FlowContext](#flowcontext)
- [Patterns](#patterns)
  - [BasePattern](#basepattern)
  - [SequentialPattern](#sequentialpattern)
  - [ParallelPattern](#parallelpattern)
  - [RouterPattern](#routerpattern)
  - [DiscussionPattern](#discussionpattern)
  - [DelegatePattern](#delegatepattern)
- [Models and Primitives](#models-and-primitives)
  - [Message](#message)
  - [MessageChunk](#messagechunk)
  - [ToolDefinition](#tooldefinition)
  - [ToolParameters](#toolparameters)
  - [ToolCall](#toolcall)
  - [FunctionCall](#functioncall)
- [Utilities](#utilities)
  - [Engine](#engine)
  - [LLM Wrappers](#llm-wrappers)
  - [Memory Stores](#memory-stores)
  - [Tools](#tools)

## Application

### TFrameXApp

The main application container for TFrameX applications.

**Constructor:**
```python
TFrameXApp(
    default_llm: Optional[BaseLLMWrapper] = None,
    default_memory_store_factory: Callable[[], BaseMemoryStore] = InMemoryMemoryStore
)
```

**Methods:**

#### `tool()`
Registers a function as a tool that can be used by agents.

```python
def tool(
    name: Optional[str] = None,
    description: Optional[str] = None,
    parameters_schema: Optional[Dict[str, Dict[str, Any]]] = None
) -> Callable
```

#### `agent()`
Registers a function as an agent.

```python
def agent(
    name: Optional[str] = None,
    description: Optional[str] = None,
    callable_agents: Optional[List[str]] = None,
    system_prompt: Optional[str] = None,
    tools: Optional[List[str]] = None,
    llm: Optional[BaseLLMWrapper] = None,
    memory_store: Optional[BaseMemoryStore] = None,
    agent_class: type[BaseAgent] = LLMAgent,
    strip_think_tags: bool = True,
    **agent_config: Any
) -> Callable
```

#### `get_tool()`
Retrieves a tool by name.

```python
def get_tool(name: str) -> Optional[Tool]
```

#### `register_flow()`
Registers a flow instance.

```python
def register_flow(flow_instance: Flow) -> None
```

#### `get_flow()`
Retrieves a flow by name.

```python
def get_flow(name: str) -> Optional[Flow]
```

#### `run_context()`
Creates a runtime context for executing flows.

```python
def run_context(
    llm_override: Optional[BaseLLMWrapper] = None,
    context_memory_override: Optional[BaseMemoryStore] = None
) -> TFrameXRuntimeContext
```

### TFrameXRuntimeContext

Runtime context for executing flows.

**Constructor:**
```python
TFrameXRuntimeContext(
    app: TFrameXApp,
    llm: Optional[BaseLLMWrapper],
    context_memory: Optional[BaseMemoryStore] = None
)
```

**Methods:**

#### `run_flow()`
Executes a flow with the specified input.

```python
async def run_flow(
    flow_ref: Union[str, Flow],
    initial_input: Message,
    initial_shared_data: Optional[Dict[str, Any]] = None,
    flow_template_vars: Optional[Dict[str, Any]] = None
) -> FlowContext
```

#### `interactive_chat()`
Starts an interactive chat session.

```python
async def interactive_chat(default_flow_name: Optional[str] = None) -> None
```

## Agents

### BaseAgent

Base class for all agents.

**Constructor:**
```python
BaseAgent(
    name: str,
    description: Optional[str] = None,
    system_prompt_template: Optional[str] = None
)
```

**Key Methods:**

#### `process()`
Process an input message and produce a response.

```python
async def process(
    input_message: Message,
    engine_ref: Optional[Any] = None,
    **kwargs
) -> Message
```

#### `get_system_prompt()`
Returns the rendered system prompt with template variables.

```python
def get_system_prompt(
    template_vars: Optional[Dict[str, Any]] = None
) -> Optional[str]
```

### LLMAgent

Agent that uses an LLM for processing.

**Constructor:**
```python
LLMAgent(
    name: str,
    description: Optional[str] = None,
    system_prompt_template: Optional[str] = None,
    llm_instance: Optional[BaseLLMWrapper] = None,
    tools: Optional[List[Tool]] = None,
    memory: Optional[BaseMemoryStore] = None,
    strip_think_tags: bool = True
)
```

**Key Methods:**

#### `process()`
Process an input message using the LLM and produce a response.

```python
async def process(
    input_message: Message,
    engine_ref: Optional[Engine] = None,
    template_vars: Optional[Dict[str, Any]] = None,
    **kwargs
) -> Message
```

### ToolAgent

Agent that wraps a tool function.

**Constructor:**
```python
ToolAgent(
    name: str,
    tool_function: Callable,
    description: Optional[str] = None
)
```

**Key Methods:**

#### `process()`
Process an input message by calling the wrapped tool function.

```python
async def process(
    input_message: Message,
    engine_ref: Optional[Engine] = None,
    **kwargs
) -> Message
```

## Flows

### Flow

Defines a sequence of agent interactions.

**Constructor:**
```python
Flow(
    flow_name: str,
    steps: Union[BasePattern, str, List[Union[BasePattern, str]]],
    description: Optional[str] = None
)
```

**Key Methods:**

#### `execute()`
Execute the flow with the specified input.

```python
async def execute(
    initial_input: Message,
    engine: Engine,
    initial_shared_data: Optional[Dict[str, Any]] = None,
    flow_template_vars: Optional[Dict[str, Any]] = None
) -> FlowContext
```

### FlowContext

Context for flow execution.

**Constructor:**
```python
FlowContext(
    initial_message: Message,
    shared_data: Optional[Dict[str, Any]] = None,
    template_vars: Optional[Dict[str, Any]] = None
)
```

**Properties:**
- `current_message`: The current message in the flow.
- `shared_data`: Dictionary of data shared across agents in the flow.
- `template_vars`: Template variables for agent system prompts.

**Methods:**

#### `update_current_message()`
Updates the current message.

```python
def update_current_message(message: Message) -> None
```

#### `update_shared_data()`
Updates the shared data dictionary.

```python
def update_shared_data(data_updates: Dict[str, Any]) -> None
```

## Patterns

### BasePattern

Base class for all patterns.

**Constructor:**
```python
BasePattern(pattern_name: str)
```

**Key Methods:**

#### `execute()`
Execute the pattern.

```python
async def execute(
    flow_ctx: FlowContext,
    engine: Engine,
    agent_call_kwargs: Optional[Dict[str, Any]] = None
) -> FlowContext
```

### SequentialPattern

Pattern that executes agents in sequence.

**Constructor:**
```python
SequentialPattern(
    pattern_name: str,
    steps: List[Union[str, BasePattern]]
)
```

**Key Methods:**

#### `execute()`
Execute the pattern's steps in sequence.

```python
async def execute(
    flow_ctx: FlowContext,
    engine: Engine,
    agent_call_kwargs: Optional[Dict[str, Any]] = None
) -> FlowContext
```

### ParallelPattern

Pattern that executes agents in parallel.

**Constructor:**
```python
ParallelPattern(
    pattern_name: str,
    agents: List[str],
    aggregator_agent: Optional[str] = None,
    aggregator_system_prompt_override: Optional[str] = None
)
```

**Key Methods:**

#### `execute()`
Execute the pattern's agents in parallel.

```python
async def execute(
    flow_ctx: FlowContext,
    engine: Engine,
    agent_call_kwargs: Optional[Dict[str, Any]] = None
) -> FlowContext
```

### RouterPattern

Pattern that dynamically routes to different agents based on input.

**Constructor:**
```python
RouterPattern(
    pattern_name: str,
    router_agent: str,
    routes: Dict[str, Union[str, BasePattern]],
    default_route: Optional[Union[str, BasePattern]] = None,
    router_system_prompt_override: Optional[str] = None
)
```

**Key Methods:**

#### `execute()`
Execute the pattern by routing to the appropriate agent or pattern.

```python
async def execute(
    flow_ctx: FlowContext,
    engine: Engine,
    agent_call_kwargs: Optional[Dict[str, Any]] = None
) -> FlowContext
```

### DiscussionPattern

Pattern that creates a multi-agent discussion.

**Constructor:**
```python
DiscussionPattern(
    pattern_name: str,
    participants: List[str],
    moderator: str,
    rounds: int = 1,
    include_input_in_first_message: bool = True,
    moderator_system_prompt_override: Optional[str] = None
)
```

**Key Methods:**

#### `execute()`
Execute the pattern by conducting a multi-agent discussion.

```python
async def execute(
    flow_ctx: FlowContext,
    engine: Engine,
    agent_call_kwargs: Optional[Dict[str, Any]] = None
) -> FlowContext
```

### DelegatePattern

Pattern that allows a supervisor agent to call other agents as tools.

This pattern is implemented through the callable_agents parameter of the agent decorator.

## Models and Primitives

### Message

Represents a message in the system.

**Constructor:**
```python
Message(
    role: str,
    content: str,
    message_type: str = "text",
    metadata: Optional[Dict[str, Any]] = None
)
```

**Properties:**
- `role`: The role of the message sender (e.g., "user", "assistant").
- `content`: The text content of the message.
- `message_type`: The type of message (e.g., "text").
- `metadata`: Additional metadata for the message.

### MessageChunk

Represents a chunk of a streaming message.

**Constructor:**
```python
MessageChunk(
    role: str,
    content: str,
    is_complete: bool = False,
    message_type: str = "text",
    metadata: Optional[Dict[str, Any]] = None
)
```

**Properties:**
- `role`: The role of the message sender.
- `content`: The text content of the chunk.
- `is_complete`: Whether this is the final chunk of the message.
- `message_type`: The type of message.
- `metadata`: Additional metadata for the message chunk.

### ToolDefinition

Represents the definition of a tool.

**Constructor:**
```python
ToolDefinition(
    name: str,
    description: Optional[str] = None,
    parameters: Optional[ToolParameters] = None
)
```

**Properties:**
- `name`: The name of the tool.
- `description`: Description of the tool's functionality.
- `parameters`: Schema for the tool's parameters.

### ToolParameters

Represents the parameters schema for a tool.

**Constructor:**
```python
ToolParameters(
    properties: Dict[str, ToolParameterProperty],
    required: Optional[List[str]] = None
)
```

**Properties:**
- `properties`: Dictionary of parameter properties.
- `required`: List of required parameter names.

### ToolCall

Represents a call to a tool.

**Constructor:**
```python
ToolCall(
    id: str,
    name: str,
    arguments: Dict[str, Any]
)
```

**Properties:**
- `id`: The unique identifier for the tool call.
- `name`: The name of the tool being called.
- `arguments`: The arguments passed to the tool.

### FunctionCall

Represents a function call (alias for ToolCall in some contexts).

**Constructor:**
```python
FunctionCall(
    name: str,
    arguments: Dict[str, Any]
)
```

**Properties:**
- `name`: The name of the function being called.
- `arguments`: The arguments passed to the function.

## Utilities

### Engine

Core execution engine for TFrameX.

**Constructor:**
```python
Engine(
    app_ref: TFrameXApp,
    runtime_context: TFrameXRuntimeContext
)
```

**Key Methods:**

#### `call_agent()`
Call an agent to process a message.

```python
async def call_agent(
    agent_name: str,
    input_message: Message,
    template_vars: Optional[Dict[str, Any]] = None,
    **kwargs
) -> Message
```

#### `call_agent_streaming()`
Call an agent to process a message with streaming response.

```python
async def call_agent_streaming(
    agent_name: str,
    input_message: Message,
    template_vars: Optional[Dict[str, Any]] = None,
    **kwargs
) -> AsyncIterator[MessageChunk]
```

#### `call_tool()`
Call a tool with the specified arguments.

```python
async def call_tool(
    tool_name: str,
    arguments: Dict[str, Any]
) -> str
```

### LLM Wrappers

#### BaseLLMWrapper

Base class for LLM wrappers.

**Constructor:**
```python
BaseLLMWrapper()
```

**Key Methods:**

#### `generate_response()`
Generate a response from the LLM.

```python
async def generate_response(
    messages: List[Dict[str, str]],
    temperature: float = 0.7,
    max_tokens: Optional[int] = None,
    tools: Optional[List[ToolDefinition]] = None,
    **kwargs
) -> Tuple[str, Optional[List[ToolCall]]]
```

#### `generate_response_stream()`
Generate a streaming response from the LLM.

```python
async def generate_response_stream(
    messages: List[Dict[str, str]],
    temperature: float = 0.7,
    max_tokens: Optional[int] = None,
    tools: Optional[List[ToolDefinition]] = None,
    **kwargs
) -> AsyncIterator[Union[str, ToolCall]]
```

#### OpenAIChatLLM

OpenAI chat model wrapper.

**Constructor:**
```python
OpenAIChatLLM(
    model_name: str = "gpt-3.5-turbo",
    api_key: Optional[str] = None,
    api_base_url: Optional[str] = None,
    organization_id: Optional[str] = None
)
```

**Methods:**
Same as BaseLLMWrapper, with implementation specific to OpenAI's API.

### Memory Stores

#### BaseMemoryStore

Base class for memory stores.

**Key Methods:**

#### `add_message()`
Add a message to the memory store.

```python
async def add_message(
    message: Union[Dict, Message],
    conversation_id: Optional[str] = None
) -> None
```

#### `get_messages()`
Get messages from the memory store.

```python
async def get_messages(
    conversation_id: Optional[str] = None,
    limit: Optional[int] = None
) -> List[Dict]
```

#### InMemoryMemoryStore

In-memory implementation of memory store.

**Constructor:**
```python
InMemoryMemoryStore()
```

**Methods:**
Same as BaseMemoryStore, with in-memory implementation.

### Tools

#### Tool

Represents a tool with associated function.

**Constructor:**
```python
Tool(
    name: str,
    func: Callable,
    description: Optional[str] = None,
    parameters_schema: Optional[ToolParameters] = None
)
```

**Properties:**
- `name`: The name of the tool.
- `description`: Description of the tool's functionality.
- `func`: The function implementing the tool.
- `parameters_schema`: Schema for the tool's parameters.

**Methods:**

#### `to_tool_definition()`
Convert to ToolDefinition format.

```python
def to_tool_definition() -> ToolDefinition
```

#### `execute()`
Execute the tool with the specified arguments.

```python
async def execute(
    arguments: Dict[str, Any]
) -> Any
``` 