
  

# TFrameX v1.1.0: The Enterprise-Ready Multi-Agent LLM Orchestration Framework 🚀
  
  

![image](https://github.com/user-attachments/assets/031f3b09-34da-4725-bb05-d064f55eec9e)

Please join our discord for support: [Discord](https://discord.gg/DkzMzwBTaw)

[TframeX Documentation Website](https://tframex.tesslate.com/)

[![PyPI version](https://badge.fury.io/py/tframex.svg)](https://badge.fury.io/py/tframex)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
  
  

**TFrameX** empowers you to build sophisticated, multi-agent LLM applications with unparalleled ease and flexibility. Move beyond simple prompt-response interactions and construct complex, dynamic workflows where intelligent agents collaborate, use tools, and adapt to intricate tasks.

## 🔥 **What's NEW in v1.1.0: Enterprise-Grade Power!**

### 🌊 **Revolutionary Streaming Support**
- **Real-Time Agent Responses**: Experience blazing-fast streaming responses from all agents
- **Live Flow Execution**: Watch your multi-agent workflows execute in real-time
- **Seamless Integration**: Zero configuration change needed - just add `streaming=True`

### 🔌 **Next-Level MCP Integration** 
- **Universal Tool Connectivity**: Connect to any MCP-compatible service with zero friction
- **Enhanced Stability**: Rock-solid MCP server management with auto-reconnection
- **Rich Meta-Tools**: Built-in tools for server discovery, resource exploration, and dynamic prompt usage
- **Production Ready**: Battle-tested MCP integration for enterprise deployments

### 🏢 **Enterprise-Grade Features**
- **🔒 Enterprise Security**: Full RBAC, multi-auth (JWT, OAuth2, API keys), audit logging, and session management
- **📊 Advanced Monitoring**: Prometheus, OpenTelemetry, and custom metrics with real-time dashboards  
- **🗄️ Multi-Backend Storage**: SQLite → PostgreSQL → S3 with seamless auto-migration
- **⚡ Production Performance**: Optimized for high-throughput, multi-tenant deployments
- **🛡️ Compliance Ready**: Complete audit trails, data governance, and regulatory compliance features

Perfect for production deployments, enterprise applications, and mission-critical AI systems!

  
  

**Find our Agent Builder Framework Here**: [Tesslate Studio Agent Builder](https://github.com/TesslateAI/Agent-Builder)

![image](https://github.com/user-attachments/assets/8e5b0689-38e6-4832-8de5-07ea03ed1c25)

  

---

  

## ✨ Why TFrameX?

  

* 🧠 **Intelligent Agents, Simplified:** Define specialized agents with unique system prompts, tools, and even dedicated LLM models.

* 🛠️ **Seamless Tool Integration:** Equip your agents with custom tools using a simple decorator. Let them interact with APIs, databases, or any Python function.

* 🌊 **Powerful Flow Orchestration:** Design complex workflows by chaining agents and predefined patterns (Sequential, Parallel, Router, Discussion) using an intuitive `Flow` API.

* ⚡ **Lightning-Fast Streaming:** Experience real-time agent responses with our revolutionary streaming support - just add `streaming=True` for instant responsiveness.

* 🔌 **Universal MCP Connectivity:** Connect to any MCP-compatible service with zero friction - from file systems to databases to external APIs.

* 🧩 **Composable & Modular:** Build reusable components (agents, tools, flows) that can be combined to create increasingly complex applications.

* 🚀 **Agent-as-Tool Paradigm:** Elevate your architecture by enabling agents to call other agents as tools, creating hierarchical and supervised agent structures.

* 🏢 **Enterprise-Ready:** Full RBAC, authentication, audit logging, metrics collection, and multi-backend storage for production deployments.

* 🎨 **Fine-Grained Control:** Customize agent behavior with features like per-agent LLMs and `<think>` tag stripping for cleaner outputs.

* 💬 **Interactive Debugging:** Quickly test your flows and agents with the built-in interactive chat.

* 🔌 **Pluggable LLMs:** Start with `OpenAIChatLLM` (compatible with OpenAI API and many local server UIs like Ollama) and extend to other models easily.

* ⚡ **CLI Tooling:** Complete command-line interface with `tframex basic` for instant interaction, `tframex setup` for project scaffolding, and `tframex serve` for web interfaces.

  

---

## 💡 Core Concepts


[TframeX Documentation Website](https://tframex.tesslate.com/)
  

**TFrameX** is designed to orchestrate complex agent interactions using its powerful `Flow` system, which controls the sequence and logic of operations.

  

Within a `Flow`, you define reusable collaboration structures called **Patterns**—such as `SequentialPattern`, `RouterPattern`, or `DiscussionPattern`. These patterns can be **nested** inside one another. For example, a `ParallelPattern` may contain several `SequentialPattern`s, enabling hierarchical task breakdowns.

  

TFrameX also supports the **agent-as-tool** paradigm: `LLMAgent`s can directly call other registered agents. This enables supervisor-worker relationships and task delegation between agents.

  

Together, **nested patterns** and **inter-agent calling** allow for sophisticated designs—including recursive or cyclical flows. For example, a `DiscussionPattern` creates a controlled loop of interaction. However, to avoid infinite loops, flows must be carefully structured with clear **termination conditions** or managed by **moderator agents**.

  

These entire `Flows`—along with their patterns and agent configurations—can be defined declaratively in **YAML** files. This makes it easy to version, share, and modify agent behaviors programmatically, giving you maximum flexibility in building adaptive, interconnected agent systems.

  
  

TFrameX revolves around a few key concepts:

  

1. 🌟 **Agents (`BaseAgent`, `LLMAgent`, `ToolAgent`)**:

* The core actors in your system.

*  **`LLMAgent`**: Leverages an LLM to reason, respond, and decide when to use tools or call other agents.

*  **`ToolAgent`**: A stateless agent that directly executes a specific tool (useful for simpler, direct tool invocations within a flow).

* Can have their own memory, system prompts, and a dedicated LLM instance.

* Support for `strip_think_tags`: Automatically remove internal "thinking" steps (e.g., `<think>...</think>`) from the final output for cleaner user-facing responses.

  

2. 🔧 **Tools (`@app.tool`)**:

* Python functions (sync or async) that agents can call to perform actions or retrieve information from the outside world (APIs, databases, file systems, etc.).

* Schemas are automatically inferred from type hints or can be explicitly defined.

  

3. 🌊 **Flows (`Flow`)**:

* Define the sequence or graph of operations.

* A flow consists of steps, where each step can be an agent or a **Pattern**.

* Orchestrate how data (as `Message` objects) and control pass between agents.

  

4. 🧩 **Patterns (`SequentialPattern`, `ParallelPattern`, `RouterPattern`, `DiscussionPattern`)**:

* Reusable templates for common multi-agent interaction structures:

*  **`SequentialPattern`**: Executes a series of agents/patterns one after another.

*  **`ParallelPattern`**: Executes multiple agents/patterns concurrently on the same input.

*  **`RouterPattern`**: Uses a "router" agent to decide which subsequent agent/pattern to execute.

*  **`DiscussionPattern`**: Facilitates a multi-round discussion between several agents, optionally moderated.

  

5. 🤝 **Agent-as-Tool (Supervisor Agents)**:

* A powerful feature where one `LLMAgent` can be configured to call other registered agents as if they were tools. This allows for creating supervisor agents that delegate tasks to specialized sub-agents.

  

6. 🤖 **LLMs (`BaseLLMWrapper`, `OpenAIChatLLM`)**:

* Pluggable wrappers for LLM APIs. `OpenAIChatLLM` provides out-of-the-box support for OpenAI-compatible APIs (including many local model servers like Ollama or LiteLLM).

* Agents can use a default LLM provided by the app, or have a specific LLM instance assigned for specialized tasks.

  

7. 💾 **Memory (`InMemoryMemoryStore`)**:

* Provides agents with conversation history. `InMemoryMemoryStore` is available by default, and you can implement custom stores by inheriting from `BaseMemoryStore`.

  


## Getting Started

### 🚀 Quick Start with CLI

The fastest way to get started with TFrameX is using the built-in CLI:

1. **Install TFrameX:**
   ```bash
   pip install tframex
   ```

2. **Start an interactive session:**
   ```bash
   # Set your API key
   export OPENAI_API_KEY="sk-..."
   
   # Launch interactive chat
   tframex basic
   ```

3. **Create your first project:**
   ```bash
   # Generate a complete project structure
   tframex setup my-ai-app
   cd my-ai-app
   
   # Configure environment
   cp .env.example .env
   # Edit .env with your API keys
   
   # Install dependencies and run
   pip install -r requirements.txt
   python main.py
   ```

4. **Try the web interface:**
   ```bash
   # Install web dependencies
   pip install tframex[web]
   
   # Launch web server
   tframex serve
   # Open http://localhost:8000 in your browser
   ```

### 📚 CLI Commands

- **`tframex basic`** - Interactive AI session with built-in tools
- **`tframex setup <project>`** - Complete project scaffolding 
- **`tframex serve`** - Web interface for agent interaction

For complete CLI documentation, see [CLI Guide](docs/CLI_GUIDE.md) and [CLI Reference](docs/CLI_REFERENCE.md).

### 📦 Manual Installation

To use TFrameX in your project manually, install it via pip:
```bash
pip install tframex
```
Core dependencies (like `httpx`, `pydantic`, `PyYAML`, `python-dotenv`, `openai`) are listed in `pyproject.toml` and should be installed automatically. If you plan to run specific examples from the TFrameX repository, you might need additional packages like `aiohttp` (for the Reddit tool example) or `Flask` (for the web app example). You can install these separately: `pip install aiohttp Flask`.

    **For Developers (Contributing to TFrameX or running all examples from source):**

    If you're developing TFrameX itself or want to run examples directly from a cloned repository, we recommend setting up a dedicated virtual environment. You can use [`uv`](https://github.com/astral-sh/uv) for its speed, or `pip` with `venv`.

    **Setting up with `uv` (Recommended):**
    First, install `uv` by following the instructions at [astral.sh/uv](https://astral.sh/uv).
    Then, in your cloned TFrameX repository:
    ```bash
    # Clone the repository (if you haven't already)
    # git clone https://github.com/TesslateAI/TFrameX.git
    # cd TFrameX

    # Create and activate a virtual environment
    uv venv
    source .venv/bin/activate  # On macOS/Linux
    # For Windows PowerShell: .venv\Scripts\Activate.ps1

    # Install TFrameX in editable mode with optional dependencies
    # For core development and running most examples:
    uv pip install -e ".[examples]"
    # To include development tools (linters, formatters):
    # uv pip install -e ".[examples,dev]"
    ```
    This approach uses the `pyproject.toml` file for precise dependency management.

    **Setting up with `pip` and `venv` (Alternative):**
    In your cloned TFrameX repository:
    ```bash
    # Clone the repository (if you haven't already)
    # git clone https://github.com/TesslateAI/TFrameX.git
    # cd TFrameX

    # Create and activate a virtual environment
    python -m venv .venv
    source .venv/bin/activate  # On macOS/Linux
    # For Windows Command Prompt: .venv\Scripts\activate.bat

    # Install TFrameX in editable mode with optional dependencies
    # For core development and running most examples:
    pip install -e ".[examples]"
    # To include development tools:
    # pip install -e ".[examples,dev]"
    ```

2.  **Set up your LLM Environment:**
    Ensure your environment variables for your LLM API are set (e.g., `OPENAI_API_KEY`, `OPENAI_API_BASE`). Create a `.env` file in your project root (TFrameX uses `python-dotenv` to load this):
    ```env
    # Example for Ollama (running locally)
    OPENAI_API_BASE="http://localhost:11434/v1"
    OPENAI_API_KEY="ollama" # Placeholder, as Ollama doesn't require a key by default
    OPENAI_MODEL_NAME="llama3" # Or your preferred model served by Ollama

    # Example for OpenAI API
    # OPENAI_API_KEY="your_openai_api_key"
    # OPENAI_MODEL_NAME="gpt-3.5-turbo"
    # OPENAI_API_BASE="https://api.openai.com/v1" # (Usually default if not set)
    ```

3.  **Your First TFrameX App:**

  
```python
import asyncio
import os
from dotenv import load_dotenv
from tframex import TFrameXApp, OpenAIChatLLM, Message
 
load_dotenv() # Load .env file

# 1. Configure your LLM
# TFrameX will use environment variables for OPENAI_API_BASE, OPENAI_API_KEY, OPENAI_MODEL_NAME by default if available
# You can explicitly pass them too:

my_llm = OpenAIChatLLM(
    model_name=os.getenv("OPENAI_MODEL_NAME", "gpt-3.5-turbo"),
    api_base_url=os.getenv("OPENAI_API_BASE"), # Can be http://localhost:11434/v1 for Ollama
    api_key=os.getenv("OPENAI_API_KEY") # Can be "ollama" for Ollama
)

# 2. Initialize TFrameXApp
app = TFrameXApp(default_llm=my_llm)

# 3. Define a simple agent
@app.agent(
    name="GreeterAgent",
    system_prompt="You are a friendly greeter. Greet the user and mention their name: {user_name}."
)
async def greeter_agent_func(): # The function body can be pass; TFrameX handles logic for LLMAgent
    pass
  

# 4. Run the agent
async def main():
    async with app.run_context() as rt: # Creates a runtime context
        user_input = Message(role="user", content="Hello there!")

        response = await rt.call_agent(
            "GreeterAgent",
            user_input,

            # You can pass template variables to the system prompt

            template_vars={"user_name": "Alex"}
        )

        print(f"GreeterAgent says: {response.content}")

if  __name__ == "__main__":
    # Basic check for LLM configuration
    if not my_llm.api_base_url:
        print("Error: LLM API base URL not configured. Check .env or OpenAIChatLLM instantiation.")
    else:
        asyncio.run(main())
```

### 🌊 **Streaming Agents Example:**

Experience real-time responses with TFrameX's streaming capabilities:

```python
# Enable streaming for lightning-fast responses
@app.agent(
    name="StreamingAssistant",
    system_prompt="You are a helpful assistant. Provide detailed, thoughtful responses.",
    streaming=True  # ✨ Just add this for real-time streaming!
)
async def streaming_assistant():
    pass

async def streaming_demo():
    async with app.run_context() as rt:
        message = Message(role="user", content="Tell me about the future of AI")
        
        # Get streaming response - watch it appear in real-time!
        response = await rt.call_agent("StreamingAssistant", message)
        print(f"Streamed response: {response.content}")
```

### 🔌 **MCP Integration Example:**

Connect to external services with MCP:

```python
# MCP servers auto-discovered and integrated
@app.agent(
    name="MCPAgent",
    system_prompt="You have access to external tools via MCP. Use them to help users.",
    # MCP tools automatically available!
)
async def mcp_agent():
    pass

# Available MCP meta-tools:
# - tframex_list_mcp_servers: Discover available MCP servers
# - tframex_list_mcp_resources: Browse MCP resources
# - tframex_read_mcp_resource: Access MCP resource content
# - tframex_list_mcp_prompts: List available MCP prompts
# - tframex_use_mcp_prompt: Execute MCP prompts
```

---

  

## 🛠️ Building with TFrameX: Code In Action

  

Let's explore how to use TFrameX's features with concrete examples.

  

### 🤖 Defining Agents

  

Agents are the heart of TFrameX. Use the `@app.agent` decorator.

  

```python
# In your app setup (app = TFrameXApp(...))


@app.agent(
    name="EchoAgent",
    description="A simple agent that echoes the user's input.",
    system_prompt="Repeat the user's message verbatim."
)
async def echo_agent_placeholder():  # Function body is a placeholder for LLMAgents
    pass


# An agent that uses a specific, more powerful LLM and strips <think> tags
special_llm_config = OpenAIChatLLM(
    model_name=os.getenv("SPECIAL_MODEL_NAME", "gpt-4-turbo"),  # A different model
    api_base_url=os.getenv("OPENAI_API_BASE_SPECIAL", os.getenv("OPENAI_API_BASE")),
    api_key=os.getenv("OPENAI_API_KEY_SPECIAL", os.getenv("OPENAI_API_KEY"))
)


@app.agent(
    name="CreativeWriterAgent",
    description="A creative writer using a specialized LLM.",
    system_prompt=(
        "You are a highly creative writer. Generate a short, imaginative story based on the user's prompt. "
        "You might use <think>...</think> tags for your internal monologue before the final story. "
        "The final story should be engaging and whimsical."
    ),
    llm=special_llm_config,  # Assign a specific LLM instance
    strip_think_tags=True  # Remove <think>content</think> from final output
)
async def creative_writer_placeholder():
    pass
```

*  **System Prompts:** Guide the LLM's behavior and persona. You can use f-string like template variables (e.g., `{user_name}`) that are filled at runtime.

*  **Per-Agent LLM:** Assign `llm=your_llm_instance` to give an agent a specific model, different from the app's default.

*  **`strip_think_tags=True`:** If your agent's system prompt encourages it to "think out loud" using `<think>...</think>` tags (a common technique for complex reasoning), setting this to `True` will remove those blocks before the final response is returned, keeping the output clean for the end-user.

  

### 🔧 Defining Tools

  

Equip your agents with tools to interact with the world.

  

```python
@app.tool(description="Gets the current weather for a specific location.")
async def get_current_weather(location: str, unit: str = "celsius") -> str:
    # In a real app, this would call a weather API
    if "tokyo" in location.lower():
        return f"The current weather in Tokyo is 25°{unit.upper()[0]} and sunny."
    if "paris" in location.lower():
        return f"The current weather in Paris is 18°{unit.upper()[0]} and cloudy."
    return f"Weather data for {location} is currently unavailable."


# Agent that uses the tool
@app.agent(
    name="WeatherAgent",
    description="Provides weather information using the 'get_current_weather' tool.",
    system_prompt=(
        "You are a Weather Assistant. Use your 'get_current_weather' tool to find the weather. "
        "If the user asks about something other than weather, politely state your purpose. "
        "Tool details: {available_tools_descriptions}"  # TFrameX injects this
    ),
    tools=["get_current_weather"]  # List tool names available to this agent
)
async def weather_agent_placeholder():
    pass
```

TFrameX automatically generates the necessary schema for the LLM to understand how to call your tools based on function signatures and type hints. The `{available_tools_descriptions}` placeholder in the system prompt will be dynamically replaced with the names and descriptions of the tools available to that specific agent.

  

### 🌊 Orchestrating with Flows

  

Flows define how agents and patterns are connected to achieve complex tasks.

  

```python
from tframex import Flow, SequentialPattern, ParallelPattern, RouterPattern, DiscussionPattern

# --- Assume Agents are defined (e.g., EchoAgent, UpperCaseAgent, WeatherAgent, CityInfoAgent, SummarizerAgent) ---

# 1. Sequential Flow: Steps execute one after another
sequential_flow = Flow(
    flow_name="SequentialEchoUpper",
    description="Echoes, then uppercases input."
)
sequential_flow.add_step("EchoAgent").add_step("UpperCaseAgent")
app.register_flow(sequential_flow)

# 2. Parallel Flow: Tasks run concurrently, results are aggregated
@app.agent(name="SummarizerAgent", description="Summarizes input text.", system_prompt="Provide a concise summary of the input text.")
async def summarizer_agent_placeholder(): pass

parallel_flow = Flow(
    flow_name="ParallelInfoSummarize",
    description="Gets weather & city info in parallel, then summarizes."
)
parallel_flow.add_step(
    ParallelPattern(
        pattern_name="GetInfoInParallel",
        tasks=["WeatherAgent", "CityInfoAgent"] # Agent names to run in parallel
    )
)
parallel_flow.add_step("SummarizerAgent") # Summarizes the combined output
app.register_flow(parallel_flow)

# 3. Router Flow: An agent decides the next step
# First, define a router agent:
@app.agent(
    name="TaskRouterAgent",
    description="Classifies query for RouterPattern: 'weather', 'city_info', or 'general'.",
    system_prompt="Analyze user query. Respond with ONE route key: 'weather', 'city_info', or 'general'. NO OTHER TEXT."
)
async def task_router_placeholder(): pass

@app.agent(name="GeneralQA_Agent", system_prompt="You are a helpful assistant. Answer general questions to the best of your ability.")
async def general_qa_placeholder(): pass

router_flow = Flow(flow_name="SmartRouterFlow", description="Routes task using TaskRouterAgent.")
router_flow.add_step(
    RouterPattern(
        pattern_name="MainTaskRouter",
        router_agent_name="TaskRouterAgent", # This agent's output (e.g., "weather") is the route key
        routes={
            "weather": "WeatherAgent",
            "city_info": "CityInfoAgent", # Assuming CityInfoAgent is defined
            "general": "GeneralQA_Agent"
        },
        default_route="GeneralQA_Agent"  # Fallback if route key doesn't match
    )
)
app.register_flow(router_flow)

# 4. Discussion Flow: Multiple agents discuss a topic
@app.agent(name="OptimistAgent", system_prompt="You are the Optimist. Find positive aspects.")
async def optimist_placeholder(): pass
@app.agent(name="PessimistAgent", system_prompt="You are the Pessimist. Point out downsides.")
async def pessimist_placeholder(): pass
@app.agent(name="DiscussionModeratorAgent", system_prompt="Summarize the discussion round, identify key themes, and pose a follow-up question to keep the discussion going.")
async def moderator_placeholder(): pass

discussion_flow = Flow(flow_name="TeamDebateFlow", description="Agents debate a topic.")
discussion_flow.add_step(
    DiscussionPattern(
        pattern_name="TechDebate",
        participant_agent_names=["OptimistAgent", "PessimistAgent"],
        discussion_rounds=2,
        moderator_agent_name="DiscussionModeratorAgent"  # Optional moderator
    )
)
app.register_flow(discussion_flow)

# --- Running a Flow ---
async def main_flow_runner():
    async with app.run_context() as rt:
        # Example: Run the sequential flow
        initial_msg = Message(role="user", content="hello world")
        flow_context = await rt.run_flow("SequentialEchoUpper", initial_msg)
        print(f"Sequential Flow Output: {flow_context.current_message.content}")
        # Expected: Something like "HELLO WORLD" (after echo then uppercase, if agents are so defined)

        # Example: Run the router flow with a weather query
        weather_query = Message(role="user", content="What's the weather in Tokyo?")
        flow_context_route = await rt.run_flow("SmartRouterFlow", weather_query)
        print(f"Router Flow (Weather) Output: {flow_context_route.current_message.content}")
        # Expected: WeatherAgent's response for Tokyo

        # Example: Run discussion flow
        topic = Message(role="user", content="Let's discuss the future of remote work.")
        discussion_context = await rt.run_flow("TeamDebateFlow", topic)
        print(f"Discussion Flow Output:\n{discussion_context.current_message.content}")

if __name__ == "__main__":
    # Ensure app and all agents (EchoAgent, UpperCaseAgent, WeatherAgent, CityInfoAgent,
    # SummarizerAgent, TaskRouterAgent, GeneralQA_Agent, OptimistAgent, PessimistAgent,
    # DiscussionModeratorAgent) are defined and registered with 'app' before running.
    # Also ensure 'my_llm' and 'special_llm_config' are initialized.
    # This is a simplified main guard; a full example would have all definitions.
    import asyncio # Assuming asyncio is needed for async main
    if 'app' in globals() and hasattr(app, 'default_llm') and app.default_llm: # Basic check
        asyncio.run(main_flow_runner())
    else:
        print("Please ensure 'app' and its 'default_llm' are initialized, and all agents are defined.")
```

  

### 🤝 Agent-as-Tool: Building Supervisor Agents

  

One of TFrameX's most powerful features is allowing an `LLMAgent` to call *other registered agents* as if they were tools. This enables hierarchical agent structures where a "supervisor" agent can delegate sub-tasks to specialized "worker" agents.

  

```python
# Assuming WeatherAgent and CityInfoAgent are already defined and registered...


@app.agent(
    name="SmartQueryDelegateAgent",
    description="Supervises WeatherAgent and CityInfoAgent, calling them as tools.",
    system_prompt=(
        "You are a Smart Query Supervisor. Your goal is to understand the user's complete request and "
        "delegate tasks to specialist agents. You have the following specialist agents available:\n"
        "{available_agents_descriptions}\n\n"  # TFrameX populates this!
        "When the user asks a question, first determine if it requires information from one or more specialists. "
        "For each required piece of information, call the appropriate specialist agent. The input to the specialist "
        "agent should be the specific part of the user's query relevant to that agent, passed as 'input_message'. "
        "After gathering all necessary information from the specialists, synthesize their responses into a single, "
        "comprehensive answer for the user. If the user's query is simple and doesn't need a specialist, "
        "answer it directly."
    ),
    callable_agents=["WeatherAgent", "CityInfoAgent"] # List names of agents this agent can call
)
async def smart_query_delegate_placeholder():
    pass


# A flow that uses this supervisor agent
smart_delegate_flow = Flow(flow_name="SmartDelegateFlow", description="Uses SmartQueryDelegateAgent for complex queries.")
smart_delegate_flow.add_step("SmartQueryDelegateAgent")
app.register_flow(smart_delegate_flow)


# --- Running this flow ---
async def main_supervisor():
    async with app.run_context() as rt:
        # This query might require both CityInfoAgent and WeatherAgent
        query = Message(role="user", content="Tell me about the attractions in Paris and what the weather is like there today.")
        flow_context = await rt.run_flow("SmartDelegateFlow", query)
        print(f"Supervisor Agent Output:\n{flow_context.current_message.content}")


if __name__ == "__main__":
    # ... (ensure app, WeatherAgent, CityInfoAgent, SmartQueryDelegateAgent are defined and registered)
    # This is a simplified main guard.
    if 'app' in globals() and app.default_llm:
        import asyncio
        asyncio.run(main_supervisor())
    else:
        print("Please ensure 'app', its 'default_llm', and relevant agents are initialized.")
```

When you specify `callable_agents`, TFrameX makes these agents available to the `SmartQueryDelegateAgent` as functions it can invoke (via the LLM's tool/function calling mechanism). The `{available_agents_descriptions}` template variable in the system prompt will automatically be populated with the names and descriptions of these callable agents, guiding the supervisor LLM on how and when to use them. The supervisor agent will then receive their responses as tool results and can synthesize a final answer.

  

### 💬 Interactive Chat

  

Test your flows quickly using the built-in interactive chat mode.

  

```python
async def main_interactive():
    async with app.run_context() as rt:
        # If you have multiple flows, it will ask you to choose one.
        # Or, you can specify a default flow to start with:
        # await rt.interactive_chat(default_flow_name="SmartDelegateFlow")
        await rt.interactive_chat()


if __name__ == "__main__":
    # ... (ensure app, agents, and flows are defined and registered before running)
    # This is a simplified main guard.
    if 'app' in globals() and app.default_llm:
        import asyncio
        asyncio.run(main_interactive())
    else:
        print("Please ensure 'app' and its 'default_llm' are initialized for interactive chat.")
```


---

## 🏢 Enterprise Features

TFrameX Enterprise provides production-ready features for enterprise deployments:

### 📊 Comprehensive Metrics & Monitoring
- **Multi-Backend Support**: Prometheus, StatsD, OpenTelemetry, and custom collectors
- **Real-Time Metrics**: Track agent performance, tool usage, flow execution times
- **Distributed Tracing**: Full request tracing with OpenTelemetry integration
- **Health Monitoring**: Built-in health checks and performance benchmarks

### 💾 Multi-Backend Data Persistence
- **Storage Abstraction**: Unified interface supporting multiple backends
- **Supported Backends**: SQLite, PostgreSQL, S3, and in-memory storage
- **Auto-Migration**: Seamless data migration between storage backends
- **Scalable Architecture**: From development SQLite to production PostgreSQL

### 🔐 Enterprise Security
- **Authentication**: API Key, JWT, OAuth2, and Basic Auth providers
- **Authorization (RBAC)**: Role-based access control with permission inheritance
- **Session Management**: Secure session handling with rotation and cleanup
- **Audit Logging**: Comprehensive audit trails for compliance and security

### 🛡️ Production-Ready Features
- **Configuration Management**: YAML/JSON configuration with environment override
- **Error Handling**: Graceful degradation and comprehensive error handling
- **Background Services**: Automated cleanup, metrics collection, session management
- **Docker Support**: Ready-to-deploy containerized applications

### 📈 Enterprise Usage

```python
from tframex.enterprise import EnterpriseApp, load_enterprise_config

# Load enterprise configuration
config = load_enterprise_config("enterprise_config.yaml")

# Create enterprise application
app = EnterpriseApp(
    default_llm=my_llm,
    enterprise_config=config
)

# All core TFrameX features plus enterprise capabilities
@app.agent(name="SecureAgent", system_prompt="You are a secure enterprise assistant.")
async def secure_agent(): pass

async def main():
    # Enterprise features initialized automatically
    async with app as enterprise_app:
        # Get enterprise services
        metrics = app.get_metrics_manager()
        storage = app.get_storage()
        rbac = app.get_rbac_engine()
        
        # Use with security context
        async with app.run_context() as ctx:
            # Metrics, security, and audit logging automatically applied
            response = await ctx.call_agent("SecureAgent", "Hello!")
```

See the [Enterprise Examples](examples/) and [Enterprise Documentation](docs/ENTERPRISE.md) for detailed usage guides.

---

  

## 🌟 Use Cases

  

TFrameX is ideal for a wide range of applications:

  

*  **Complex Task Decomposition:** Break down large tasks (e.g., "research the impact of AI on healthcare, find three key papers, summarize them, and draft a blog post") into smaller, manageable sub-tasks handled by specialized agents coordinated by a supervisor.

*  **Multi-Agent Collaboration:**

* Simulate debates (Optimist vs. Pessimist vs. Realist).

* Collaborative problem-solving teams (e.g., Developer Agent, QA Agent, ProductManager Agent working on a feature).

* Creative writing ensembles where different agents contribute different parts of a story.

*  **Tool-Augmented LLM Applications:**

* Customer support bots that can query databases, CRM systems, or knowledge bases.

* Data analysis agents that can execute Python code (via a tool) or fetch real-time financial data.

* Personal assistants that manage calendars, send emails, or control smart home devices.

* A Reddit chatbot that can fetch top posts, analyze sentiment, and engage in discussions (see `examples/redditchatbot` for inspiration).

*  **Dynamic Chatbots:** Create chatbots that can intelligently route user queries to the most appropriate agent or tool based on context and conversation history.

*  **Automated Content Generation Pipelines:** Chain agents for drafting, revising, fact-checking, and formatting content for various platforms.

*  **Educational Tutors:** Agents specializing in different subjects collaborating to provide comprehensive explanations.

*  **Enterprise Applications (with TFrameX Enterprise):**

* **Customer Service Platforms:** Multi-agent support systems with authentication, role-based access, and comprehensive audit trails.

* **Internal Knowledge Systems:** Secure enterprise chatbots with RBAC, session management, and integration with corporate databases.

* **Automated Compliance Systems:** Agent workflows with full audit logging, metrics collection, and regulatory compliance features.

* **Production AI Pipelines:** Scalable agent orchestration with monitoring, error handling, and enterprise-grade reliability.

* **Multi-Tenant SaaS Applications:** Secure, monitored agent services with per-tenant isolation and comprehensive analytics.

  

---

  

## 🔬 Advanced Concepts

  

*  **`TFrameXRuntimeContext` (`rt`):**

* Created when you use `async with app.run_context() as rt:`.

* Manages the lifecycle of agent instances and LLM clients for a given execution scope.

* Provides methods like `rt.call_agent()`, `rt.run_flow()`, `rt.call_tool()`.

* Can have its own LLM override, distinct from the app's default or agent-specific LLMs, useful for setting a context-wide LLM for all operations within that `with` block unless an agent has its own override.

  

*  **`FlowContext`:**

* Passed between steps in a `Flow`.

* Holds `current_message` (the output of the last step), `history` (all messages exchanged in the current flow execution, including intermediate agent calls), and `shared_data` (a dictionary for patterns/steps to pass arbitrary data or control signals like `STOP_FLOW`).

  

*  **Template Variables in Prompts & Flows:**

* System prompts for agents can include placeholders like `{variable_name}`.

* When calling an agent directly or running a flow, you can pass a `template_vars` (for `call_agent`) or `flow_template_vars` (for `run_flow`) dictionary:

```python
# For call_agent
await rt.call_agent(
    "MyAgentWithTemplates",
    input_msg,
    template_vars={"user_name": "Alice", "current_date": "2024-07-15"}

)

# For run_flow
await rt.run_flow(
    "MyFlowWithTemplates",
    initial_msg,
    flow_template_vars={"project_id": "XYZ123", "target_audience": "developers"}
)
```

* These variables are made available during system prompt rendering for all agents invoked within that specific call or flow execution, enhancing dynamic behavior and context-awareness. The `system_prompt_template` in an agent's definition (e.g., `@app.agent(system_prompt="Hello {user_name}")`) will be formatted using these variables.

  

---

  

## 🤝 Contributing

  

Contributions are welcome! We're excited to see how the community extends and builds upon TFrameX. Please feel free to open an issue for discussions, bug reports, or feature requests, or submit a pull request.

  

---


[TframeX Documentation Website](https://tframex.tesslate.com/)

## 📜 License

  

This project is licensed under the MIT License. See the `LICENSE` file for details.
