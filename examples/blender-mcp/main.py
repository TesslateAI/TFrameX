# blender_interactive_control.py
import asyncio
import logging
import os
import json
from dotenv import load_dotenv

from tframex import TFrameXApp, OpenAIChatLLM, Message
from tframex.util.logging import setup_logging

# --- Environment and Logging Setup ---
load_dotenv()
setup_logging(level=logging.INFO) # Set TFrameX root logger level

# Configure specific logger levels
logging.getLogger("tframex.app").setLevel(logging.INFO)
logging.getLogger("tframex.mcp").setLevel(logging.INFO)
logging.getLogger("tframex.mcp.server_connector").setLevel(logging.INFO) # DEBUG for connection details
logging.getLogger("tframex.agents.llm_agent").setLevel(logging.DEBUG) # DEBUG for tool call details and LLM thoughts
logging.getLogger("tframex.engine").setLevel(logging.INFO)
logging.getLogger("mcp.client").setLevel(logging.WARNING) # Reduce noise from underlying MCP library

logger = logging.getLogger("TFrameX_Blender_Control")

async def main_blender_chat():
    logger.info("--- TFrameX Blender Interactive Control ---")

    # 1. Configure LLM
    llm_api_key = os.getenv("OPENAI_API_KEY")
    llm_api_base = os.getenv("OPENAI_API_BASE")
    llm_model_name = os.getenv("OPENAI_MODEL_NAME")

    if not all([llm_api_base, llm_model_name]): # API key might be optional for local LLMs
        logger.error("LLM API base or model name missing in .env. Please configure them. Exiting.")
        return

    default_llm = OpenAIChatLLM(
        model_name=llm_model_name,
        api_base_url=llm_api_base,
        api_key=llm_api_key # Will be None if not set, which is fine for some local LLMs
    )
    logger.info(f"Using LLM: {llm_model_name} at {llm_api_base}")

    # 2. Initialize TFrameXApp with MCP configuration
    # Ensure 'servers_config.json' is in the same directory or provide the correct path.
    app = TFrameXApp(
        default_llm=default_llm,
        mcp_config_file="servers_config.json"
    )

    # 3. Define the BlenderAssistant agent
    # The system prompt guides the LLM on how to interact with Blender via MCP tools.
    # It's crucial for the LLM to understand it should use tools prefixed with 'blender_service__'
    # and to break down complex tasks.
    blender_system_prompt = (
        "/no_think You are a Blender AI assistant. You can control a Blender instance using a set of tools. "
        "All Blender-specific tools are prefixed with 'blender_service__'.\n"
        "When asked to perform complex tasks (e.g., 'create a scene with a house, a tree, and a car'), "
        "break them down into a sequence of individual tool calls. "
        "For example, first create the house, then the tree, then the car, then position them. "
        "Confirm intermediate steps if helpful.\n"
        "Always use the provided tools to interact with Blender. Do not try to write Blender Python code directly "
        "unless you are explicitly asked to use a tool like 'blender_service__execute_blender_code' "
        "and you are confident in the code's safety and correctness.\n"
        "Available tools (prefixed with 'blender_service__'): {available_tools_descriptions}\n"
        "REMEMBER: If a tool involves generating assets (like from Hyper3D), it might be a multi-step process: "
        "1. Initiate generation (e.g., `blender_service__generate_hyper3d_model_via_text`). This returns a job/task ID."
        "2. Poll for completion (e.g., `blender_service__poll_rodin_job_status`) using the ID until it's 'Done' or 'COMPLETED'."
        "3. Import the asset (e.g., `blender_service__import_generated_asset`) using the ID."
        "Be patient and guide the user through these steps if necessary or perform them sequentially."
    )

    @app.agent(
        name="BlenderAssistant",
        system_prompt=blender_system_prompt,
        # This agent will only have access to tools from the MCP server aliased as "blender_service"
        # (as defined in your servers_config.json)
        max_tool_iterations=20,
        mcp_tools_from_servers=["blender_service"],
        strip_think_tags=True # Set to False if you want to see <think> tags from the LLM
    )
    async def blender_assistant_placeholder():
        # The logic for an LLMAgent is handled by the TFrameX framework.
        # It will use the system_prompt, configured LLM, and available tools.
        pass

    # 4. Run the interactive chat with the BlenderAssistant
    async with app.run_context() as rt: # MCP servers (Blender) will be initialized here.
        logger.info("Starting interactive chat with 'BlenderAssistant'.")
        logger.info("Ensure Blender is running and the BlenderMCP addon is active and 'Connected'.")
        logger.info("The 'blender_service' MCP server (uvx blender-mcp) will be started by TFrameX.")
        logger.info("Try commands like: 'create a cube', 'get scene info', 'generate a 3D model of a cat using Hyper3D and name it fluffy'.")

        await rt.interactive_chat(default_agent_name="BlenderAssistant")

    # 5. Crucial for stdio MCP servers (like blender-mcp) to terminate properly after chat ends
    logger.info("Interactive chat finished. Shutting down MCP servers...")
    await app.shutdown_mcp_servers()
    logger.info("--- TFrameX Blender Interactive Control Finished ---")

if __name__ == "__main__":
    # Ensure servers_config.json exists
    if not os.path.exists("servers_config.json"):
        logger.warning("'servers_config.json' not found. Creating a default for Blender.")
        default_blender_config = {
            "mcpServers": {
                "blender_service": { # Make sure this alias matches agent config
                    "type": "stdio",
                    "command": "uvx", # For Mac/Linux. For Windows, might need "cmd" with "/c", "uvx"
                    "args": ["blender-mcp"],
                    "env": {},
                    "init_step_timeout": 60.0,
                    "tool_call_timeout": 180.0,
                    "resource_read_timeout": 60.0
                }
            }
        }
        # Check if on Windows to apply the cmd /c pattern as a default
        if os.name == 'nt':
            logger.info("Windows detected, adjusting default Blender MCP command in servers_config.json to use 'cmd /c uvx'.")
            default_blender_config["mcpServers"]["blender_service"]["command"] = "cmd"
            default_blender_config["mcpServers"]["blender_service"]["args"] = ["/c", "uvx", "blender-mcp"]

        with open("servers_config.json", "w") as f:
            json.dump(default_blender_config, f, indent=2)
        logger.info(f"Created default servers_config.json for Blender: {json.dumps(default_blender_config)}")

    # Ensure .env file exists for LLM configuration
    if not os.path.exists(".env"):
        logger.warning(".env file not found. Creating a dummy .env. PLEASE UPDATE IT with your actual LLM details.")
        with open(".env", "w") as f:
            f.write('# Example for a local Ollama setup (most common for Blender experiments)\n')
            f.write('OPENAI_API_BASE="http://localhost:11434/v1"\n')
            f.write('OPENAI_API_KEY="ollama" # Ollama doesn\'t strictly require a key\n')
            f.write('OPENAI_MODEL_NAME="llama3" # Or any model you have pulled in Ollama, e.g., mistral, codellama\n\n')
            f.write('# Example for OpenAI API (if you prefer)\n')
            f.write('# OPENAI_API_KEY="your_actual_openai_api_key"\n')
            f.write('# OPENAI_API_BASE="https://api.openai.com/v1"\n')
            f.write('# OPENAI_MODEL_NAME="gpt-4-turbo-preview"\n') # Or "gpt-3.5-turbo"

    try:
        asyncio.run(main_blender_chat())
    except KeyboardInterrupt:
        logger.info("Application terminated by user (KeyboardInterrupt).")
    except Exception as e:
        logger.critical(f"Unhandled exception in main asyncio run: {e}", exc_info=True)
    finally:
        logger.info("Application exiting process.")