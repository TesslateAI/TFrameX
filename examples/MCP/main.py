# mcp_chatbot_main.py
import asyncio
import logging
import os
import json 
from dotenv import load_dotenv

from tframex import TFrameXApp, OpenAIChatLLM, Message # TFrameXRuntimeContext is used internally by app.run_context()
# from tframex.util.llms import BaseLLMWrapper # Not directly needed for this script

load_dotenv() 

from tframex.util.logging import setup_logging
setup_logging(level=logging.INFO)
logging.getLogger("tframex.app").setLevel(logging.INFO)
logging.getLogger("tframex.mcp").setLevel(logging.INFO)
logging.getLogger("tframex.mcp.server_connector").setLevel(logging.INFO)
logging.getLogger("tframex.agents.llm_agent").setLevel(logging.INFO) # Set to DEBUG for tool call details
logging.getLogger("tframex.engine").setLevel(logging.INFO)
logging.getLogger("mcp.client").setLevel(logging.WARNING)

logger = logging.getLogger("TFrameX_MCP_Chatbot")

async def main():
    logger.info("--- TFrameX with MCP - Interactive Chatbot Example ---")

    # 1. Configure LLM
    llm_api_key = os.getenv("OPENAI_API_KEY")
    llm_api_base = os.getenv("OPENAI_API_BASE")
    llm_model_name = os.getenv("OPENAI_MODEL_NAME")

    if not all([llm_api_key, llm_api_base, llm_model_name]):
        logger.error("LLM configuration missing in .env. Exiting.")
        return

    default_llm = OpenAIChatLLM(
        model_name=llm_model_name,
        api_base_url=llm_api_base,
        api_key=llm_api_key
    )
    logger.info(f"Using LLM: {llm_model_name} at {llm_api_base}")

    # 2. Initialize TFrameXApp with MCP configuration
    app = TFrameXApp(
        default_llm=default_llm,
        mcp_config_file="servers_config.json" 
    )

    # MCP servers will be initialized when app.run_context() is entered,
    # or can be done explicitly here if needed before agent registration (not typical).
    # await app.initialize_mcp_servers() # Optional explicit call

    # 3. Define a native TFrameX tool
    @app.tool(description="Gets the current date and time.")
    async def get_current_datetime() -> str:
        from datetime import datetime
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        logger.info(f"NATIVE TOOL: get_current_datetime executed, returning: {now_str}")
        return now_str

    # 4. Define the UniversalAssistant agent
    @app.agent(
        name="UniversalAssistant",
        system_prompt=(
            "You are UniversalAssistant, a helpful AI. You have access to tools for time, MCP server introspection, and specific MCP server functionalities.\n"
            "MCP server tools are prefixed (e.g., 'math_http_service__add', 'echo_stdio_service__echo').\n"
            "Use 'tframex_read_mcp_resource' to read MCP resources if you know the server_alias and resource_uri.\n"
            "Carefully choose tools and provide arguments. Available tools: {available_tools_descriptions}"
        ),
        tools=[ # Native TFrameX tools + MCP meta-tools
            "get_current_datetime",
            "tframex_list_mcp_servers",
            "tframex_list_mcp_resources",
            "tframex_read_mcp_resource",
            "tframex_list_mcp_prompts",
            "tframex_use_mcp_prompt",
        ],
        mcp_tools_from_servers="ALL" # Agent can use tools from ALL connected MCP servers
    )
    async def universal_assistant_placeholder():
        pass # Logic is handled by LLMAgent base class

    # 5. Run the built-in interactive chat with the UniversalAssistant
    # TFrameXRuntimeContext is created and managed by app.run_context()
    async with app.run_context() as rt: # MCP servers will be initialized here.
        logger.info("Starting interactive chat with 'UniversalAssistant'.")
        logger.info("MCP Servers should connect now if not already.")
        logger.info("Try asking about time, math (e.g., '10 + 5'), or echoing (e.g., 'echo hello from stdio').")
        logger.info("You can also ask it to 'list mcp servers' or 'list resources from echo_stdio_service'.")
        
        await rt.interactive_chat(default_agent_name="UniversalAssistant")
        # The interactive_chat method in TFrameXRuntimeContext will handle the
        # user input loop and calling the specified agent.

    # Crucial for stdio MCP servers to terminate properly after chat ends
    logger.info("Interactive chat finished. Shutting down MCP servers...")
    await app.shutdown_mcp_servers()
    logger.info("--- TFrameX MCP Chatbot Example Finished ---")

if __name__ == "__main__":
    # Setup dummy/example config files if they don't exist
    # Ensure 'echo_server_stdio.py' is in the same directory or adjust paths in 'servers_config.json'
    if not os.path.exists("echo_server_stdio.py"):
        logger.error("echo_server_stdio.py not found. Please create it or update servers_config.json.")
        # For the example to run without manual setup, you might choose to exit or simplify servers_config
    
    if not os.path.exists("servers_config.json"):
        logger.warning("servers_config.json not found. Creating a dummy config with only math_http_service.")
        dummy_config = {
            "mcpServers": {
                "math_http_service": {"type": "streamable-http", "url": "http://localhost:8000/mcp/"}
                # Add echo_stdio_service here if echo_server_stdio.py exists
                # "echo_stdio_service": {
                #     "type": "stdio",
                #     "command": "python",
                #     "args": ["./echo_server_stdio.py"], # Assuming it's in the same dir
                #     "env": {"ECHO_PREFIX": "[EchoStdioFromChat]"}
                # }
            }
        }
        # Check again if echo_server_stdio.py exists before adding to dummy config
        if os.path.exists("echo_server_stdio.py") and "echo_stdio_service" not in dummy_config["mcpServers"] :
             dummy_config["mcpServers"]["echo_stdio_service"] = {
                "type": "stdio",
                "command": "python", # Assuming python is in PATH
                "args": ["./echo_server_stdio.py"], # Path relative to where this script is run
                "env": {"ECHO_PREFIX": "[EchoStdioExample]"}
            }
        else:
            logger.warning("echo_server_stdio.py not found, dummy config will not include it.")

        with open("servers_config.json", "w") as f:
            json.dump(dummy_config, f, indent=2)
        logger.info(f"Created/updated dummy servers_config.json: {dummy_config}")

    if not os.path.exists(".env"):
        logger.warning(".env file not found. Creating a dummy .env. PLEASE UPDATE IT with your actual LLM details.")
        with open(".env", "w") as f:
            f.write('OPENAI_API_KEY="your_llm_api_key_here"\n')
            f.write('OPENAI_API_BASE="your_llm_api_base_here_e.g.http://localhost:8080/v1"\n')
            f.write('OPENAI_MODEL_NAME="your_llm_model_name_here"\n')
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Application terminated by user (KeyboardInterrupt).")
    except Exception as e:
        logger.critical("Unhandled exception in main asyncio run.", exc_info=True)
    finally:
        logger.info("Application exiting process.")