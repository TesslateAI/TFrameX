
# TFrameX API Reference

## Table of Contents
- [Application](#application)
  - [TFrameXApp](#tframexapp)
  - [TFrameXRuntimeContext](#tframexruntimecontext)
- [Engine](#engine)
- [Agents](#agents)
  - [BaseAgent](#baseagent)
  - [LLMAgent](#llmagent)
  - [ToolAgent](#toolagent)
- [Flows](#flows)
  - [Flow](#flow)
  - [FlowContext](#flowcontext)
- [Patterns](#patterns)
  - [BasePattern](#basepattern-1)
  - [SequentialPattern](#sequentialpattern)
  - [ParallelPattern](#parallelpattern)
  - [RouterPattern](#routerpattern)
  - [DiscussionPattern](#discussionpattern)
  - [DelegatePattern](#delegatepattern)
    - [ProcessingMode Enum](#processingmode-enum)
- [Models and Primitives](#models-and-primitives)
  - [Message](#message)
  - [MessageChunk](#messagechunk)
  - [ToolDefinition](#tooldefinition)
  - [ToolParameters](#toolparameters)
  - [ToolParameterProperty](#toolparameterproperty)
  - [ToolCall](#toolcall)
  - [FunctionCall](#functioncall)
- [Utilities](#utilities)
  - [LLM Wrappers](#llm-wrappers)
    - [BaseLLMWrapper](#basellmwrapper)
    - [OpenAIChatLLM](#openaichatllm)
  - [Memory Stores](#memory-stores)
    - [BaseMemoryStore](#basememorystore)
    - [InMemoryMemoryStore](#inmemorymemorystore)
  - [Tools](#tools-1)
    - [Tool](#tool)
  - [Logging](#logging)
    - [setup_logging()](#setup_logging)
    - [LLMInteraction (dataclass)](#llminteraction-dataclass)

## Application

### `TFrameXApp`

The main application container for TFrameX applications. It manages agent registrations, tools, flows, and default configurations.

**Path:** `tframex.app.TFrameXApp`

**Constructor:**
```python
TFrameXApp(
    default_llm: Optional[BaseLLMWrapper] = None,
    default_memory_store_factory: Callable[[], BaseMemoryStore] = InMemoryMemoryStore
)
```
- `default_llm`: An optional default LLM instance to be used by agents if not overridden.
- `default_memory_store_factory`: A callable that returns a new instance of a memory store, defaulting to `InMemoryMemoryStore`.

**Methods:**

#### `tool()`
Decorator to register a Python function as a `Tool` that agents can use.
```python
def tool(
    name: Optional[str] = None,
    description: Optional[str] = None,
    parameters_schema: Optional[Dict[str, Dict[str, Any]]] = None # For explicit Pydantic-like schema
) -> Callable
```
- `name`: Optional name for the tool; defaults to the function name.
- `description`: Optional description of the tool; defaults to the function's docstring.
- `parameters_schema`: Optional dictionary defining the tool's parameters if not inferable from type hints or if more detail is needed. The structure should match Pydantic's `ToolParameters` model.

#### `agent()`
Decorator to register an agent (either a placeholder function for framework-managed agents like `LLMAgent` or a custom `BaseAgent` subclass).
```python
def agent(
    name: Optional[str] = None,
    description: Optional[str] = None,
    callable_agents: Optional[List[str]] = None,
    system_prompt: Optional[str] = None, # System prompt template
    tools: Optional[List[str]] = None, # Names of tools available to this agent
    llm: Optional[BaseLLMWrapper] = None, # Agent-specific LLM override
    memory_store: Optional[BaseMemoryStore] = None, # Agent-specific memory override
    agent_class: type[BaseAgent] = LLMAgent, # Class to instantiate for this agent
    strip_think_tags: bool = True, # Whether to remove <think>...</think> tags from LLM output
    **agent_config: Any # Additional keyword arguments passed to the agent's constructor
) -> Callable
```

#### `get_tool()`
Retrieves a registered `Tool` instance by its name.
```python
def get_tool(name: str) -> Optional[Tool]
```

#### `register_flow()`
Registers a `Flow` instance with the application.
```python
def register_flow(flow_instance: Flow) -> None
```

#### `get_flow()`
Retrieves a registered `Flow` instance by its name.
```python
def get_flow(name: str) -> Optional[Flow]
```

#### `run_context()`
Creates a `TFrameXRuntimeContext` for executing flows and agent calls. This is typically used as an async context manager (`async with app.run_context() as rt:`).
```python
def run_context(
    llm_override: Optional[BaseLLMWrapper] = None,
    context_memory_override: Optional[BaseMemoryStore] = None # Not currently used by Engine for agent memory
) -> TFrameXRuntimeContext
```
- `llm_override`: An LLM instance to use for this specific runtime context, overriding the app's default.
- `context_memory_override`: A memory store for the context (currently less impactful as agents get their own memory).

---

### `TFrameXRuntimeContext`

A runtime environment for executing flows and isolated agent calls. It holds an `Engine` instance.

**Path:** `tframex.app.TFrameXRuntimeContext`

**Constructor:** (Typically not instantiated directly by users; use `TFrameXApp.run_context()`)
```python
TFrameXRuntimeContext(
    app: TFrameXApp,
    llm: Optional[BaseLLMWrapper], # LLM for this context
    context_memory: Optional[BaseMemoryStore] = None
)
```

**Key Properties:**
- `engine: Engine`: The execution engine associated with this runtime context.
- `llm: Optional[BaseLLMWrapper]`: The LLM active for this context (can be overridden per agent).

**Methods:**

#### `run_flow()`
Executes a registered flow.
```python
async def run_flow(
    flow_ref: Union[str, Flow], # Name of the flow or a Flow instance
    initial_input: Message,
    initial_shared_data: Optional[Dict[str, Any]] = None,
    flow_template_vars: Optional[Dict[str, Any]] = None
) -> FlowContext
```
- `flow_template_vars`: Dictionary of variables to be made available for template substitution in agent system prompts within this flow execution.

#### `interactive_chat()`
Starts an interactive command-line chat session to test registered flows.
```python
async def interactive_chat(default_flow_name: Optional[str] = None) -> None
```

#### `call_agent()` (via `engine`)
Convenience to call an agent directly through the context's engine.
```python
# Usage: await rt.engine.call_agent(agent_name, input_message, **kwargs)
# (See Engine.call_agent() for details)
```

---

## Engine

The core execution engine that manages agent instantiation and calls within a `TFrameXRuntimeContext`.

**Path:** `tframex.util.engine.Engine`

**Constructor:** (Typically not instantiated directly by users; created by `TFrameXRuntimeContext`)
```python
Engine(app: TFrameXApp, runtime_context: TFrameXRuntimeContext)
```

**Methods:**

#### `call_agent()`
Retrieves (or instantiates) and runs a registered agent.
```python
async def call_agent(
    agent_name: str,
    input_message: Union[str, Message],
    **kwargs: Any # e.g., template_vars
) -> Message
```

#### `call_tool()`
Executes a registered tool. Typically used internally by agents.
```python
async def call_tool(tool_name: str, arguments_json_str: str) -> Any
```

#### `reset_agent()`
Resets the memory of a specified agent instance within the current engine's scope.
```python
async def reset_agent(agent_name: str) -> None
```

---

## Agents

### `BaseAgent`

Abstract base class for all agents.

**Path:** `tframex.agents.base.BaseAgent`

**Constructor:** (Parameters are typically set by the framework based on `@app.agent` decorator)
```python
BaseAgent(
    agent_id: str,
    description: Optional[str] = None,
    llm: Optional[BaseLLMWrapper] = None,
    tools: Optional[List[Tool]] = None,
    memory: Optional[BaseMemoryStore] = None,
    system_prompt_template: Optional[str] = None,
    callable_agent_definitions: Optional[List[ToolDefinition]] = None,
    strip_think_tags: bool = False,
    **config: Any
)
```

**Key Methods:**

#### `run()` (abstract)
Primary execution method for an agent.
```python
@abstractmethod
async def run(self, input_message: Union[str, Message], **kwargs: Any) -> Message
```

#### `reset_memory()`
Clears the agent's internal memory store.
```python
async def reset_memory(self) -> None
```

#### `_render_system_prompt()`
Internal method to render the system prompt using provided template variables.
```python
def _render_system_prompt(self, **kwargs_for_template: Any) -> Optional[Message]
```
Automatically includes `available_tools_descriptions` and `available_agents_descriptions` in `kwargs_for_template`.

#### `_post_process_llm_response()`
Internal method to apply post-processing, like stripping `<think>` tags.
```python
def _post_process_llm_response(self, message: Message) -> Message
```

---

### `LLMAgent`

An agent powered by a Large Language Model. It can use tools and call other agents.

**Path:** `tframex.agents.llm_agent.LLMAgent` (Subclass of `BaseAgent`)

**Constructor:** (Parameters are typically set by the framework)
```python
LLMAgent(
    agent_id: str,
    llm: BaseLLMWrapper, # Resolved LLM instance
    engine: Engine,      # Engine instance for sub-agent/tool calls
    # ... other BaseAgent parameters ...
    max_tool_iterations: int = 5,
    **config: Any
)
```

**Methods:**

#### `run()`
Executes the agent's logic: processes input, interacts with LLM, handles tool calls (including sub-agents), and manages memory.
```python
async def run(self, input_message: Union[str, Message], **kwargs: Any) -> Message
```
- `kwargs` can include `template_vars` for system prompt rendering.

---

### `ToolAgent`

A stateless agent that directly executes a single pre-configured tool.

**Path:** `tframex.agents.tool_agent.ToolAgent` (Subclass of `BaseAgent`)

**Constructor:** (Parameters are typically set by the framework)
```python
ToolAgent(
    agent_id: str,
    tools: List[Tool], # Must contain exactly one tool, or 'target_tool_name' in config
    # ... other BaseAgent parameters (llm, memory, system_prompt are ignored) ...
    **config: Any # Can include 'target_tool_name'
)
```

**Methods:**

#### `run()`
Parses the input message (expected to be a JSON string or dict of arguments for the tool) and executes the configured tool.
```python
async def run(self, input_message: Union[str, Message, Dict[str, Any]], **kwargs: Any) -> Message
```
Returns a message with the tool's output or an error.

---

## Flows

### `Flow`

Defines a sequence of steps (agents or patterns) to orchestrate a complex task.

**Path:** `tframex.flows.flows.Flow`

**Constructor:**
```python
Flow(flow_name: str, description: Optional[str] = None)
```

**Methods:**

#### `add_step()`
Adds an agent (by name) or a `BasePattern` instance to the flow.
```python
def add_step(self, step: Union[str, BasePattern]) -> Self # Returns self for chaining
```

#### `execute()`
Executes all steps in the flow sequentially.
```python
async def execute(
    initial_input: Message,
    engine: Engine,
    initial_shared_data: Optional[Dict[str, Any]] = None,
    flow_template_vars: Optional[Dict[str, Any]] = None
) -> FlowContext
```

#### `generate_documentation()`
Generates a Mermaid diagram string and a YAML configuration string for the flow.
```python
def generate_documentation(self, app: TFrameXApp) -> Tuple[str, str]
```

---

### `FlowContext`

Holds the state and data being processed during a single execution of a `Flow`.

**Path:** `tframex.flows.flow_context.FlowContext`

**Constructor:**
```python
FlowContext(initial_input: Message, shared_data: Optional[Dict[str, Any]] = None)
```

**Properties:**
- `current_message: Message`: The latest message output by a step.
- `history: list[Message]`: A list of all messages exchanged during the flow execution (including initial input and intermediate messages).
- `shared_data: Dict[str, Any]`: A dictionary for patterns and steps to share arbitrary data or control signals (e.g., `STOP_FLOW: True`).

**Methods:**

#### `update_current_message()`
Updates `current_message` and appends it to `history`.
```python
def update_current_message(self, message: Message) -> None
```

#### `get_all_messages()`
Returns the complete `history` list of messages.
```python
def get_all_messages(self) -> list[Message]
```

---

## Patterns

### `BasePattern`

Abstract base class for all interaction patterns.

**Path:** `tframex.patterns.base_pattern.BasePattern`

**Constructor:**
```python
BasePattern(pattern_name: str)
```

**Methods:**

#### `execute()` (abstract)
Executes the pattern's logic.
```python
@abstractmethod
async def execute(
    flow_ctx: FlowContext,
    engine: Engine,
    agent_call_kwargs: Optional[Dict[str, Any]] = None # For passing template_vars etc.
) -> FlowContext
```

#### `reset_agents()` (abstract)
Resets the memory of all agents managed or invoked by this pattern.
```python
@abstractmethod
async def reset_agents(self, engine: Engine) -> None
```

---

### `SequentialPattern`

Executes a list of steps (agents or other patterns) in sequence. The output of one step becomes the input to the next.

**Path:** `tframex.patterns.sequential_pattern.SequentialPattern`

**Constructor:**
```python
SequentialPattern(pattern_name: str, steps: List[Union[str, BasePattern]])
```

---

### `ParallelPattern`

Executes a list of tasks (agents or other patterns) concurrently with the same initial input. Results are aggregated into the `FlowContext.current_message` and `FlowContext.shared_data`.

**Path:** `tframex.patterns.parallel_pattern.ParallelPattern`

**Constructor:**
```python
ParallelPattern(pattern_name: str, tasks: List[Union[str, BasePattern]])
```
**Note:** When a nested pattern is a task, it receives its own branched `FlowContext` to prevent interference between parallel tasks. Shared data from branches is merged back (last-write-wins).

---

### `RouterPattern`

Uses a specified "router agent" to decide which subsequent agent or pattern (from a defined set of routes) to execute based on the input.

**Path:** `tframex.patterns.router_pattern.RouterPattern`

**Constructor:**
```python
RouterPattern(
    pattern_name: str,
    router_agent_name: str, # Name of the agent that decides the route
    routes: Dict[str, Union[str, BasePattern]], # Mapping of route keys to agent names or patterns
    default_route: Optional[Union[str, BasePattern]] = None # Fallback if no route matches
)
```
The output of the `router_agent_name` is used as the key to select from `routes`. The selected agent/pattern then processes the original input to the `RouterPattern`.

---

### `DiscussionPattern`

Facilitates a multi-round discussion between a list of participant agents. An optional moderator agent can summarize rounds or guide the discussion.

**Path:** `tframex.patterns.discussion_pattern.DiscussionPattern`

**Constructor:**
```python
DiscussionPattern(
    pattern_name: str,
    participant_agent_names: List[str],
    discussion_rounds: int = 1,
    moderator_agent_name: Optional[str] = None,
    stop_phrase: Optional[str] = None # If an agent's output contains this phrase, discussion ends.
)
```

---

### `DelegatePattern`

A delegator agent generates tasks (extracted via regex), and a delegatee agent (or pattern) processes these tasks either sequentially or in parallel. Supports "Chain of Agents" (CoA) style processing with a summary agent.

**Path:** `tframex.patterns.delegate_pattern.DelegatePattern`

**Constructor:**
```python
DelegatePattern(
    pattern_name: str,
    delegator_agent: str, # Name of the agent that generates tasks
    delegatee_agent: Union[str, BasePattern], # Agent name or pattern to process tasks
    processing_mode: ProcessingMode = ProcessingMode.SEQUENTIAL,
    summary_agent: Optional[str] = None, # Agent name for summarizing in CoA mode
    chain_of_agents: bool = False,
    task_extraction_regex: str = r"<task>(.*?)</task>",
    shared_memory_extraction_regex: Optional[str] = None
)
```

#### `ProcessingMode` Enum
**Path:** `tframex.patterns.delegate_pattern.ProcessingMode`
- `ProcessingMode.SEQUENTIAL`
- `ProcessingMode.PARALLEL`

---

## Models and Primitives

These Pydantic models define the data structures used throughout TFrameX.

**Path:** `tframex.models.primitives`

### `Message`
Basic unit of communication.
```python
Message(
    role: Literal["system", "user", "assistant", "tool"],
    content: Optional[str] = None,
    tool_calls: Optional[List[ToolCall]] = None,
    tool_call_id: Optional[str] = None, # For role="tool"
    name: Optional[str] = None # For role="tool", function name
)
```

### `MessageChunk`
Represents a chunk in a streaming LLM response. Inherits from `Message`.

### `ToolDefinition`
OpenAI-compatible tool definition format.
```python
ToolDefinition(
    type: Literal["function"] = "function",
    function: Dict[str, Any] # Contains name, description, parameters
)
```
- `function["parameters"]`: Should conform to `ToolParameters` schema.

### `ToolParameters`
Schema for tool parameters.
```python
ToolParameters(
    type: Literal["object"] = "object",
    properties: Dict[str, ToolParameterProperty] = Field(default_factory=dict),
    required: Optional[List[str]] = Field(default_factory=list)
)
```

### `ToolParameterProperty`
Defines a single parameter property for a tool.
```python
ToolParameterProperty(
    type: str, # e.g., "string", "number", "integer", "boolean"
    description: Optional[str] = None,
    enum: Optional[List[Any]] = None
)
```

### `ToolCall`
Represents an LLM's request to call a tool.
```python
ToolCall(
    id: str, # ID generated by the model for this call
    type: Literal["function"] = "function",
    function: FunctionCall
)
```

### `FunctionCall`
Details of the function to be called by a tool.
```python
FunctionCall(
    name: str,
    arguments: str # JSON string of arguments
)
```

---

## Utilities

### LLM Wrappers

#### `BaseLLMWrapper`
Abstract base class for LLM API wrappers.

**Path:** `tframex.util.llms.BaseLLMWrapper`

**Constructor:**
```python
BaseLLMWrapper(
    model_id: str,
    api_key: Optional[str] = None,
    api_base_url: Optional[str] = None,
    client_kwargs: Optional[Dict[str, Any]] = None # For httpx.AsyncClient
)
```

**Methods:**
- `chat_completion()` (abstract, overloaded for stream/non-stream)
- `close()` (closes underlying HTTP client)

#### `OpenAIChatLLM`
Implementation for OpenAI-compatible chat completion APIs.

**Path:** `tframex.util.llms.OpenAIChatLLM`

**Constructor:**
```python
OpenAIChatLLM(
    model_name: str,
    api_base_url: str,
    api_key: Optional[str] = None,
    default_max_tokens: int = 4096,
    default_temperature: float = 0.7,
    **kwargs: Any # Passed to BaseLLMWrapper.client_kwargs
)
```
Supports streaming and tool/function calling.

---

### Memory Stores

#### `BaseMemoryStore`
Abstract base class for conversation memory.

**Path:** `tframex.util.memory.BaseMemoryStore`

**Methods (abstract):**
- `add_message(self, message: Message) -> None`
- `get_history(self, limit: Optional[int] = None, offset: int = 0, roles: Optional[List[str]] = None) -> List[Message]`
- `clear(self) -> None`

#### `InMemoryMemoryStore`
Simple in-memory list-based implementation of `BaseMemoryStore`.

**Path:** `tframex.util.memory.InMemoryMemoryStore`

**Constructor:**
```python
InMemoryMemoryStore(max_history_size: Optional[int] = None)
```

---

### Tools

#### `Tool`
Represents a callable function that agents can use.

**Path:** `tframex.util.tools.Tool`

**Constructor:**
```python
Tool(
    name: str,
    func: Callable[..., Any], # The Python function (sync or async)
    description: Optional[str] = None,
    parameters_schema: Optional[ToolParameters] = None # Pydantic model for params
)
```
If `parameters_schema` is not provided, it attempts to infer one from the function's type hints.

**Methods:**
- `get_openai_tool_definition() -> ToolDefinition`
- `execute(self, arguments_json_str: str) -> Any` (runs the tool function)

---

### Logging

#### `setup_logging()`
Configures global logging for the TFrameX application.

**Path:** `tframex.util.logging.setup_logging` (also exposed as `tframex.setup_logging`)

```python
def setup_logging(
    level: int = logging.INFO,
    log_format: Optional[str] = None,
    use_colors: bool = True, # For console output
    save_to_file: bool = True # Whether to save logs to files (logs/tframex.log, logs/llm_interactions.log)
) -> None
```
- Initializes colored console logging and optional file logging.
- Creates `logs/tframex.log` for general logs and `logs/llm_interactions.log` for detailed LLM call traces if `save_to_file` is `True`. Log files are cleared on each call to `setup_logging` if `save_to_file` is `True`.

#### `LLMInteraction` (dataclass)
Dataclass used for structured logging of LLM interactions.

**Path:** `tframex.util.logging.LLMInteraction` (also exposed as `tframex.LLMInteraction`)
```python
@dataclass
class LLMInteraction:
    messages: List[Message] # Messages sent to LLM
    response: Message       # Message received from LLM
    agent_name: str
    tools_called: List[ToolCall] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)
```
Used with the `llm_interaction` logger and `LLMInteractionFormatter`.
Example log call:
```python
# llm_logger = logging.getLogger("llm_interaction")
# llm_logger.debug("LLM Call Details", extra={"llm_interaction": LLMInteraction(...)})
```