
#  TFrameX: The Extensible Task & Flow Orchestration Framework for LLMs 

[![PyPI version](https://badge.fury.io/py/tframex.svg)](https://badge.fury.io/py/tframex) <!-- Replace with actual badge if/when published -->
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT) <!-- Replace with actual license -->
<!-- Add other badges: build status, coverage, etc. -->

![image](https://github.com/user-attachments/assets/031f3b09-34da-4725-bb05-d064f55eec9e)


**TFrameX** empowers you to build sophisticated, multi-agent LLM applications with unparalleled ease and flexibility. Move beyond simple prompt-response interactions and construct complex, dynamic workflows where intelligent agents collaborate, use tools, and adapt to intricate tasks.

---

## ✨ Why TFrameX?

*   🧠 **Intelligent Agents, Simplified:** Define specialized agents with unique system prompts, tools, and even dedicated LLM models.
*   🛠️ **Seamless Tool Integration:** Equip your agents with custom tools using a simple decorator. Let them interact with APIs, databases, or any Python function.
*   🌊 **Powerful Flow Orchestration:** Design complex workflows by chaining agents and predefined patterns (Sequential, Parallel, Router, Discussion) using an intuitive `Flow` API.
*   🧩 **Composable & Modular:** Build reusable components (agents, tools, flows) that can be combined to create increasingly complex applications.
*   🚀 **Agent-as-Tool Paradigm:** Elevate your architecture by enabling agents to call other agents as tools, creating hierarchical and supervised agent structures.
*   🎨 **Fine-Grained Control:** Customize agent behavior with features like per-agent LLMs and `<think>` tag stripping for cleaner outputs.
*   💬 **Interactive Debugging:** Quickly test your flows and agents with the built-in interactive chat.
*   🔌 **Pluggable LLMs:** Start with `OpenAIChatLLM` (compatible with OpenAI API and many local server UIs like Ollama) and extend to other models easily.

---

## 💡 Core Concepts

TFrameX revolves around a few key concepts:

1.  🌟 **Agents (`BaseAgent`, `LLMAgent`, `ToolAgent`)**:
    *   The core actors in your system.
    *   **`LLMAgent`**: Leverages an LLM to reason, respond, and decide when to use tools or call other agents.
    *   **`ToolAgent`**: A stateless agent that directly executes a specific tool (useful for simpler, direct tool invocations within a flow).
    *   Can have their own memory, system prompts, and a dedicated LLM instance.
    *   Support for `strip_think_tags`: Automatically remove internal "thinking" steps (e.g., `<think>...</think>`) from the final output for cleaner user-facing responses.

2.  🔧 **Tools (`@app.tool`)**:
    *   Python functions (sync or async) that agents can call to perform actions or retrieve information from the outside world (APIs, databases, file systems, etc.).
    *   Schemas are automatically inferred from type hints or can be explicitly defined.

3.  🌊 **Flows (`Flow`)**:
    *   Define the sequence or graph of operations.
    *   A flow consists of steps, where each step can be an agent or a **Pattern**.
    *   Orchestrate how data (as `Message` objects) and control pass between agents.

4.  🧩 **Patterns (`SequentialPattern`, `ParallelPattern`, `RouterPattern`, `DiscussionPattern`)**:
    *   Reusable templates for common multi-agent interaction structures:
        *   **`SequentialPattern`**: Executes a series of agents/patterns one after another.
        *   **`ParallelPattern`**: Executes multiple agents/patterns concurrently on the same input.
        *   **`RouterPattern`**: Uses a "router" agent to decide which subsequent agent/pattern to execute.
        *   **`DiscussionPattern`**: Facilitates a multi-round discussion between several agents, optionally moderated.

5.  🤝 **Agent-as-Tool (Supervisor Agents)**:
    *   A powerful feature where one `LLMAgent` can be configured to call other registered agents as if they were tools. This allows for creating supervisor agents that delegate tasks to specialized sub-agents.

6.  🤖 **LLMs (`BaseLLMWrapper`, `OpenAIChatLLM`)**:
    *   Pluggable wrappers for LLM APIs. `OpenAIChatLLM` provides out-of-the-box support for OpenAI-compatible APIs (including many local model servers like Ollama or LiteLLM).
    *   Agents can use a default LLM provided by the app, or have a specific LLM instance assigned for specialized tasks.

7.  💾 **Memory (`InMemoryMemoryStore`)**:
    *   Provides agents with conversation history. `InMemoryMemoryStore` is available by default, and you can implement custom stores by inheriting from `BaseMemoryStore`.

---

## Getting Started

1.  **Installation:**
    ```bash
    pip install tframex
    ```
    (You might also need specific LLM client libraries, e.g., `openai` or `httpx` if not already bundled or if you use `aiohttp` as in some examples: `pip install httpx aiohttp python-dotenv`)

2.  **Set up your LLM Environment:**
    Ensure your environment variables for your LLM API are set (e.g., `OPENAI_API_KEY`, `OPENAI_API_BASE`). Create a `.env` file in your project root:
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
        api_key=os.getenv("OPENAI_API_KEY")        # Can be "ollama" for Ollama
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

    if __name__ == "__main__":
        # Basic check for LLM configuration
        if not my_llm.api_base_url:
            print("Error: LLM API base URL not configured. Check .env or OpenAIChatLLM instantiation.")
        else:
            asyncio.run(main())
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
async def echo_agent_placeholder(): # Function body is a placeholder for LLMAgents
    pass

# An agent that uses a specific, more powerful LLM and strips <think> tags
special_llm_config = OpenAIChatLLM(
    model_name=os.getenv("SPECIAL_MODEL_NAME", "gpt-4-turbo"), # A different model
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
    strip_think_tags=True    # Remove <think>content</think> from final output
)
async def creative_writer_placeholder():
    pass
```
*   **System Prompts:** Guide the LLM's behavior and persona. You can use f-string like template variables (e.g., `{user_name}`) that are filled at runtime.
*   **Per-Agent LLM:** Assign `llm=your_llm_instance` to give an agent a specific model, different from the app's default.
*   **`strip_think_tags=True`:** If your agent's system prompt encourages it to "think out loud" using `<think>...</think>` tags (a common technique for complex reasoning), setting this to `True` will remove those blocks before the final response is returned, keeping the output clean for the end-user.

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
        "Tool details: {available_tools_descriptions}" # TFrameX injects this
    ),
    tools=["get_current_weather"] # List tool names available to this agent
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
        default_route="GeneralQA_Agent" # Fallback if route key doesn't match
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
        moderator_agent_name="DiscussionModeratorAgent" # Optional moderator
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
    if 'app' in globals() and app.default_llm: # Basic check
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
        "{available_agents_descriptions}\n\n" # TFrameX populates this!
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
        asyncio.run(main_interactive())
    else:
        print("Please ensure 'app' and its 'default_llm' are initialized for interactive chat.")
```

---

## 🌟 Use Cases

TFrameX is ideal for a wide range of applications:

*   **Complex Task Decomposition:** Break down large tasks (e.g., "research the impact of AI on healthcare, find three key papers, summarize them, and draft a blog post") into smaller, manageable sub-tasks handled by specialized agents coordinated by a supervisor.
*   **Multi-Agent Collaboration:**
    *   Simulate debates (Optimist vs. Pessimist vs. Realist).
    *   Collaborative problem-solving teams (e.g., Developer Agent, QA Agent, ProductManager Agent working on a feature).
    *   Creative writing ensembles where different agents contribute different parts of a story.
*   **Tool-Augmented LLM Applications:**
    *   Customer support bots that can query databases, CRM systems, or knowledge bases.
    *   Data analysis agents that can execute Python code (via a tool) or fetch real-time financial data.
    *   Personal assistants that manage calendars, send emails, or control smart home devices.
    *   A Reddit chatbot that can fetch top posts, analyze sentiment, and engage in discussions (see `examples/redditchatbot` for inspiration).
*   **Dynamic Chatbots:** Create chatbots that can intelligently route user queries to the most appropriate agent or tool based on context and conversation history.
*   **Automated Content Generation Pipelines:** Chain agents for drafting, revising, fact-checking, and formatting content for various platforms.
*   **Educational Tutors:** Agents specializing in different subjects collaborating to provide comprehensive explanations.

---

## 🔬 Advanced Concepts

*   **`TFrameXRuntimeContext` (`rt`):**
    *   Created when you use `async with app.run_context() as rt:`.
    *   Manages the lifecycle of agent instances and LLM clients for a given execution scope.
    *   Provides methods like `rt.call_agent()`, `rt.run_flow()`, `rt.call_tool()`.
    *   Can have its own LLM override, distinct from the app's default or agent-specific LLMs, useful for setting a context-wide LLM for all operations within that `with` block unless an agent has its own override.

*   **`FlowContext`:**
    *   Passed between steps in a `Flow`.
    *   Holds `current_message` (the output of the last step), `history` (all messages exchanged in the current flow execution, including intermediate agent calls), and `shared_data` (a dictionary for patterns/steps to pass arbitrary data or control signals like `STOP_FLOW`).

*   **Template Variables in Prompts & Flows:**
    *   System prompts for agents can include placeholders like `{variable_name}`.
    *   When calling an agent directly or running a flow, you can pass a `template_vars` (for `call_agent`) or `flow_template_vars` (for `run_flow`) dictionary:
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
    *   These variables are made available during system prompt rendering for all agents invoked within that specific call or flow execution, enhancing dynamic behavior and context-awareness. The `system_prompt_template` in an agent's definition (e.g., `@app.agent(system_prompt="Hello {user_name}")`) will be formatted using these variables.

---

## 🤝 Contributing

Contributions are welcome! We're excited to see how the community extends and builds upon TFrameX. Please feel free to open an issue for discussions, bug reports, or feature requests, or submit a pull request.

(Consider adding more details: Contribution guidelines, development setup, code of conduct.)

---

## 📜 License

This project is licensed under the MIT License. See the `LICENSE` file for details.
(You'll need to add a `LICENSE` file to your repository, typically containing the MIT License text.)
