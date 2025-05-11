import asyncio
import logging
import os
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv

from tframex import (
    DiscussionPattern,
    Flow,
    InMemoryMemoryStore,
    Message,
    OpenAIChatLLM,
    ParallelPattern,
    RouterPattern,
    SequentialPattern,
    TFrameXApp,
    TFrameXRuntimeContext,
)

# --- Environment and Logging Setup ---
load_dotenv()
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - [%(funcName)s] - %(message)s",
)
logging.getLogger("tframex").setLevel(logging.INFO)
# For more detailed logs:
logging.getLogger("tframex.agents.llm_agent").setLevel(logging.DEBUG)
# logging.getLogger("tframex.agents.base").setLevel(logging.DEBUG)
# logging.getLogger("tframex.app").setLevel(logging.DEBUG)

# --- LLM Configurations ---
# Default LLM (e.g., a local, faster model for general tasks)
default_llm_config = OpenAIChatLLM(
    model_name=os.getenv("OPENAI_MODEL_NAME", "gpt-3.5-turbo"),  # Your default model
    api_base_url=os.getenv("OPENAI_API_BASE", "http://localhost:11434"),
    api_key=os.getenv("OPENAI_API_KEY", "ollama"),
)

# A more powerful/specialized LLM for specific agents
# Ensure you have another model configured if you use this (e.g., OPENAI_GPT4_MODEL_NAME)
# For this example, we'll just use a different name but point to the same base URL.
# In a real scenario, api_base_url or model_name would differ.
special_llm_config = OpenAIChatLLM(
    model_name=os.getenv("SPECIAL_MODEL_NAME", "gpt-4"),  # A different model
    api_base_url=os.getenv(
        "OPENAI_API_BASE_SPECIAL",
        os.getenv("OPENAI_API_BASE", "http://localhost:11434"),
    ),
    api_key=os.getenv("OPENAI_API_KEY_SPECIAL", os.getenv("OPENAI_API_KEY", "ollama")),
)

if not default_llm_config.api_base_url:
    print("Error: OPENAI_API_BASE not set for default LLM.")
    exit(1)
if not special_llm_config.api_base_url:  # Check if you intend to use a special LLM
    print(
        "Warning: OPENAI_API_BASE_SPECIAL not set for special LLM. It will use the default base if not overridden."
    )


# --- Initialize TFrameX Application ---
app = TFrameXApp(default_llm=default_llm_config)


# --- Tool Definitions (Unchanged) ---
@app.tool(description="Gets the current weather for a specific location.")
async def get_current_weather(location: str, unit: str = "celsius") -> str:
    logging.info(
        f"TOOL EXECUTED: get_current_weather(location='{location}', unit='{unit}')"
    )
    if "tokyo" in location.lower():
        return f"The current weather in Tokyo is 25°{unit.upper()[0]} and sunny."
    if "paris" in location.lower():
        return f"The current weather in Paris is 18°{unit.upper()[0]} and cloudy."
    return f"Weather data for {location} is currently unavailable."


@app.tool(description="Retrieves general information about a city.")
async def get_city_info(city_name: str, info_type: str = "population") -> str:
    logging.info(
        f"TOOL EXECUTED: get_city_info(city_name='{city_name}', info_type='{info_type}')"
    )
    if "paris" in city_name.lower():
        if info_type == "population":
            return "Population of Paris is approximately 2.1 million."
        if info_type == "attractions":
            return "Main attractions: Eiffel Tower, Louvre Museum."
    if "tokyo" in city_name.lower():
        if info_type == "population":
            return "Population of Tokyo is approximately 14 million."
        if info_type == "attractions":
            return "Main attractions: Tokyo Skytree, Senso-ji Temple."
    return f"Information of type '{info_type}' for {city_name} not found."


# --- Agent Definitions ---


# Basic Agents
@app.agent(
    name="EchoAgent",
    description="Repeats the input.",
    system_prompt="Repeat the user's message verbatim.",
)
async def echo_agent_placeholder():
    pass


@app.agent(
    name="UpperCaseAgent",
    description="Converts input to uppercase.",
    system_prompt="Convert user's message to uppercase. ONLY respond with uppercased text.",
)
async def uppercase_agent_placeholder():
    pass


@app.agent(
    name="ReverseAgent",
    description="Reverses the input text.",
    system_prompt="Reverse the text of user's message. ONLY respond with reversed text.",
)
async def reverse_agent_placeholder():
    pass


# Tool-using Agents
@app.agent(
    name="WeatherAgent",
    description="Provides weather information using the 'get_current_weather' tool.",
    system_prompt="You are a Weather Assistant. Use 'get_current_weather' for the location. If not about weather, state your purpose.",
    tools=["get_current_weather"],
)
async def weather_agent_placeholder():
    pass


@app.agent(
    name="CityInfoAgent",
    description="Provides city details using 'get_city_info' tool.",
    system_prompt="You are a City Information Provider. Use 'get_city_info'. Infer 'info_type' or default to 'attractions'. If not about city info, state purpose.",
    tools=["get_city_info"],
)
async def city_info_agent_placeholder():
    pass


# Summarizer Agent
@app.agent(
    name="SummarizerAgent",
    description="Summarizes input text.",
    system_prompt="Provide a concise summary of the input text.",
)
async def summarizer_agent_placeholder():
    pass


# Agent for Router Pattern (Old way)
@app.agent(
    name="TaskRouterAgent",
    description="Classifies query for RouterPattern: 'weather', 'city_info', or 'echo'.",
    system_prompt="Analyze user query. Respond with ONE route key: 'weather', 'city_info', or 'echo'. NO OTHER TEXT.",
)
async def task_router_placeholder():
    pass


# NEW: Supervisor Agent using "Agent as Tool"
@app.agent(
    name="SmartQueryDelegateAgent",
    description="Supervises WeatherAgent and CityInfoAgent, calling them as tools.",
    system_prompt=(
        "You are a Smart Query Supervisor. Delegate to specialist agents based on user's request.\n"
        "Available specialist agents (call as functions):\n{available_agents_descriptions}\n\n"
        "Call the appropriate agent with user's query as 'input_message'. Present their response."
    ),
    callable_agents=["WeatherAgent", "CityInfoAgent"],
)
async def smart_query_delegate_placeholder():
    pass


# NEW: Agent with a specific LLM and think tag stripping
@app.agent(
    name="CreativeWriterAgent",
    description="A creative writer that uses a specialized LLM and might have thinking steps.",
    system_prompt=(
        "You are a highly creative writer. Generate a short, imaginative story based on the user's prompt. "
        "You might use <think>...</think> tags for your internal monologue before the final story. "
        "The final story should be engaging and whimsical."
    ),
    llm=special_llm_config,  # Uses the special_llm_config
)
async def creative_writer_placeholder():
    pass


# Agents for Discussion Pattern
@app.agent(
    name="OptimistAgent",
    description="Optimistic discussant.",
    system_prompt="You are the Optimist. Find positive aspects. Start with 'As an optimist, I see that...'",
)
async def optimist_placeholder():
    pass


@app.agent(
    name="PessimistAgent",
    description="Pessimistic discussant.",
    system_prompt="You are the Pessimist. Point out downsides. Start with 'However, from a pessimistic view, ...'",
)
async def pessimist_placeholder():
    pass


@app.agent(
    name="RealistAgent",
    description="Realistic discussant.",
    system_prompt="You are the Realist. Provide a balanced view. Start with 'Realistically speaking, ...'",
)
async def realist_placeholder():
    pass


@app.agent(
    name="DiscussionModeratorAgent",
    description="Moderates discussions.",
    system_prompt="Summarize discussion round, identify themes, pose follow-up question.",
)
async def discussion_moderator_placeholder():
    pass


# --- Flow Definitions ---

# 1. Sequential Flow
sequential_flow = Flow(
    flow_name="SequentialEchoUpperReverse",
    description="Echoes, uppercases, then reverses input.",
)
sequential_flow.add_step("EchoAgent").add_step("UpperCaseAgent").add_step(
    "ReverseAgent"
)
app.register_flow(sequential_flow)

# 2. Parallel Flow
parallel_flow = Flow(
    flow_name="ParallelWeatherCityInfoSummarize",
    description="Gets weather & city info in parallel, then summarizes.",
)
parallel_flow.add_step(
    ParallelPattern(
        pattern_name="GetInfoInParallel", tasks=["WeatherAgent", "CityInfoAgent"]
    )
)
parallel_flow.add_step("SummarizerAgent")
app.register_flow(parallel_flow)

# 3. Router Flow (Old method)
router_flow_old = Flow(
    flow_name="RouterFlow_OldMethod", description="Routes task using TaskRouterAgent."
)
router_flow_old.add_step(
    RouterPattern(
        pattern_name="MainTaskRouter",
        router_agent_name="TaskRouterAgent",
        routes={
            "weather": "WeatherAgent",
            "city_info": "CityInfoAgent",
            "echo": "EchoAgent",
        },
        default_route="EchoAgent",
    )
)
app.register_flow(router_flow_old)

# 4. Discussion Flow
discussion_flow_example = Flow(
    flow_name="TeamDebateFlow",
    description="Optimist, Pessimist, Realist discuss a topic.",
)
discussion_flow_example.add_step(
    DiscussionPattern(
        pattern_name="TeamDebateOnTopic",
        participant_agent_names=["OptimistAgent", "PessimistAgent", "RealistAgent"],
        discussion_rounds=2,
        moderator_agent_name="DiscussionModeratorAgent",
        stop_phrase="end discussion now",
    )
)
app.register_flow(discussion_flow_example)

# 5. NEW: Flow using Agent-as-Tool (Supervisor Agent)
smart_delegate_flow = Flow(
    flow_name="SmartDelegateFlow_NewMethod", description="Uses SmartQueryDelegateAgent."
)
smart_delegate_flow.add_step("SmartQueryDelegateAgent")
app.register_flow(smart_delegate_flow)

# 6. NEW: Flow demonstrating per-agent LLM and think tag stripping
creative_writing_flow = Flow(
    flow_name="CreativeWriterFlow",
    description="Demonstrates specialized LLM and think tag stripping.",
)
creative_writing_flow.add_step(
    "CreativeWriterAgent"
)  # This agent has its own LLM and strip_think_tags=True
app.register_flow(creative_writing_flow)


# 7. Flow demonstrating template variables (No changes from before, just for completeness)
@app.agent(
    name="GreetingAgent",
    description="Greets a user by name.",
    system_prompt="User's name: {user_name}. Greet them for query: '{user_query}'.",
)
async def greeting_agent_placeholder():
    pass


templated_flow_example = Flow(
    flow_name="TemplatedGreetingFlow", description="Greets a user by name via template."
)
templated_flow_example.add_step("GreetingAgent")
app.register_flow(templated_flow_example)


# --- Main Application CLI ---
async def main():
    async with app.run_context(
        llm_override=None
    ) as rt:  # Can override context LLM here if needed
        # Example of running a specific flow directly (e.g., creative writer)
        # print("\n--- Testing CreativeWriterFlow ---")
        # creative_input = Message(role="user", content="Tell me a story about a mischievous cloud.")
        # creative_context = await rt.run_flow("CreativeWriterFlow", creative_input)
        # print("Creative Writer Output:", creative_context.current_message.content)
        # print("---------------------------------")

        # Example of running templated flow
        # print("\n--- Testing TemplatedGreetingFlow ---")
        # greet_input = Message(role="user", content="I want to know about LLMs.")
        # greet_context = await rt.run_flow(
        #     "TemplatedGreetingFlow",
        #     greet_input,
        #     flow_template_vars={"user_name": "Valued Customer", "user_query": greet_input.content}
        # )
        # print("Templated Greeting Output:", greet_context.current_message.content)
        # print("---------------------------------")

        await rt.interactive_chat()


if __name__ == "__main__":
    if not default_llm_config.api_base_url:  # Check the default LLM used by TFrameXApp
        print(
            "FATAL: OPENAI_API_BASE environment variable is not set for the default LLM."
        )
    else:
        asyncio.run(main())
