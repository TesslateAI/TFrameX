import asyncio
import logging
import os

from dotenv import load_dotenv

# Assuming tframex is installed and your environment is set up
from tframex import ParallelPattern  # Import patterns if you use them
from tframex import Flow, OpenAIChatLLM, SequentialPattern, TFrameXApp

# --- Environment and Logging Setup (Optional for just docs, but good practice) ---
load_dotenv()
logging.basicConfig(level=logging.INFO)
logging.getLogger("tframex").setLevel(logging.INFO)

# --- LLM Configuration (Dummy for this example if not running flows) ---
# If you're only generating documentation, the LLM config might not be strictly necessary
# unless agent definitions themselves depend on it during app setup.
# For robustness, provide a minimal configuration.
default_llm_config = OpenAIChatLLM(
    model_name=os.getenv("OPENAI_MODEL_NAME", "gpt-3.5-turbo"),
    api_base_url=os.getenv(
        "OPENAI_API_BASE", "http://localhost:11434/v1"
    ),  # Ollama example
    api_key=os.getenv("OPENAI_API_KEY", "ollama"),
)

# --- Initialize TFrameX Application ---
app = TFrameXApp(default_llm=default_llm_config)


# --- Define some Tools ---
@app.tool(description="A simple echo tool.")
async def echo_tool(text: str) -> str:
    return f"Tool echoed: {text}"


@app.tool(description="Adds two numbers.")
async def add_numbers_tool(a: int, b: int) -> int:
    return a + b


# --- Define some Agents ---
@app.agent(
    name="GreeterAgent",
    description="Greets the user.",
    system_prompt="You are a friendly greeter.",
)
async def greeter_agent_placeholder():
    pass


@app.agent(
    name="CalculatorAgent",
    description="Uses tools to perform calculations.",
    system_prompt="You are a calculator. Use your tools. Available tools: {available_tools_descriptions}",
    tools=["add_numbers_tool"],
)
async def calculator_agent_placeholder():
    pass


@app.agent(
    name="EchoerAgent",
    description="Echoes input using echo_tool.",
    system_prompt="Use the echo_tool.",
    tools=["echo_tool"],
    # Example of an agent calling another agent (if SupervisorAgent was defined and callable)
    # callable_agents=["GreeterAgent"] # For demonstration, let's assume GreeterAgent could be called
)
async def echoer_agent_placeholder():
    pass


@app.agent(
    name="FarewellAgent",
    description="Says goodbye.",
    system_prompt="Bid the user farewell.",
)
async def farewell_agent_placeholder():
    pass


# --- Create a Flow ---
my_complex_flow = Flow(
    flow_name="GreetingAndCalculationFlow",
    description="A flow that greets, uses a tool via an agent, and then says goodbye.",
)

# Add steps to the flow
my_complex_flow.add_step("GreeterAgent")
my_complex_flow.add_step(
    SequentialPattern(
        pattern_name="CalculationSequence", steps=["EchoerAgent", "CalculatorAgent"]
    )
)
my_complex_flow.add_step("FarewellAgent")

# Register the flow with the app (good practice, though not strictly needed for docs if flow is passed directly)
app.register_flow(my_complex_flow)


# --- Generate Documentation ---
def generate_and_save_documentation():
    flow_to_document = app.get_flow(
        "GreetingAndCalculationFlow"
    )  # Or use my_complex_flow directly

    if not flow_to_document:
        print("Flow not found!")
        return

    print(f"Generating documentation for flow: '{flow_to_document.flow_name}'...")

    # The core call:
    mermaid_diagram_string, yaml_config_string = (
        flow_to_document.generate_documentation(app)
    )

    # --- Output or Save the Documentation ---

    # Print to console
    print("\n--- Mermaid Diagram ---")
    print(mermaid_diagram_string)
    print("\n--- YAML Configuration ---")
    print(yaml_config_string)

    # Save to files
    try:
        with open("flow_diagram.md", "w") as f:
            f.write("```mermaid\n")
            f.write(mermaid_diagram_string)
            f.write("\n```")
        print("\nMermaid diagram saved to flow_diagram.md")

        with open("flow_config.yaml", "w") as f:
            f.write(yaml_config_string)
        print("YAML configuration saved to flow_config.yaml")
    except IOError as e:
        print(f"Error saving files: {e}")


# Run the documentation generation
if __name__ == "__main__":
    # No async needed if you're *only* generating docs and not running flows/agents.
    # If your agent/tool definitions had async setup, you might need an event loop.
    # For this specific generate_documentation method, it's synchronous.
    generate_and_save_documentation()
