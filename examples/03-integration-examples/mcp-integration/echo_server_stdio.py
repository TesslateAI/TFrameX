# examples/MCP/echo_server_stdio.py
import asyncio
import logging
import os
import sys # For sys.stdout in logging handlers
from mcp.server import Server, NotificationOptions
from mcp.server.models import InitializationOptions
from mcp.types import Tool, TextContent, Resource
import mcp.server.stdio # For stdio_server context manager

# --- Logging Setup ---
# Ensure the 'logs' directory exists in the same directory as this script,
# or adjust the log_file_path.
LOG_DIR = os.path.join(os.path.dirname(__file__), "logs")
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE_PATH = os.path.join(LOG_DIR, 'echo_server_stdio.log')

# Configure logging to write to a file and also to stdout (for direct runs)
logging.basicConfig(
    level=logging.DEBUG, # Set to DEBUG for verbose output
    format="%(asctime)s - ECHO_SRV_STDIO - %(process)d - %(levelname)s - %(filename)s:%(lineno)d - %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE_PATH, mode='w'), # Overwrite log file on each start
        logging.StreamHandler(sys.stdout) # Log to console as well
    ]
)
logger = logging.getLogger("echo_mcp_stdio_srv")

# --- Server Configuration ---
ECHO_PREFIX = os.getenv("ECHO_PREFIX", "[EchoStdioDefault]")

# Create the MCP Server instance
# The server name here is for identification within this process,
# the actual name presented to clients is in InitializationOptions.
server = Server("EchoStdioServerExampleInstance")
logger.debug(f"MCP Server object '{server.name}' created.")

# --- Tool Definitions ---
@server.list_tools()
async def list_tools_impl() -> list[Tool]:
    logger.debug("Handler: list_tools_impl called.")
    return [
        Tool(
            name="echo",
            description="Echoes the input message with a prefix.",
            inputSchema={
                "type": "object",
                "properties": {
                    "message": {"type": "string", "description": "The message to echo."}
                },
                "required": ["message"],
            }
        )
    ]

@server.call_tool()
async def call_tool_impl(name: str, args: dict | None) -> list[TextContent]:
    logger.debug(f"Handler: call_tool_impl called with tool_name='{name}', args={args!r}")
    if name == "echo":
        message_to_echo = args.get("message", "No message provided.") if args else "No message provided."
        response_text = f"{ECHO_PREFIX} {message_to_echo}"
        logger.info(f"Tool 'echo' responding with: '{response_text}'")
        return [TextContent(type="text", text=response_text)]
    logger.warning(f"Handler: call_tool_impl received unknown tool name: '{name}'")
    # According to MCP spec, should ideally raise an error or return an error in CallToolResult.
    # For simplicity, returning empty list for unknown tools.
    return []

# --- Resource Definitions ---
@server.list_resources()
async def list_resources_impl() -> list[Resource]:
    logger.debug("Handler: list_resources_impl called.")
    return [
        Resource(
            uri="echo://status",
            name="Server Status",
            description="Provides the current status and prefix of the echo server.",
            mimeType="text/plain"
        )
    ]

@server.read_resource()
async def read_resource_impl(uri: str) -> str:
    logger.debug(f"Handler: read_resource_impl called with uri='{uri}'")
    if str(uri) == "echo://status":
        status_text = f"Echo server is operational. Current prefix: {ECHO_PREFIX}"
        logger.info(f"Resource 'echo://status' responding with: '{status_text}'")
        return status_text
    logger.warning(f"Handler: read_resource_impl received unknown resource URI: '{uri}'")
    raise ValueError(f"Resource not found: {uri}") # MCP server should handle this and convert to error response

# --- Main Server Logic ---
async def main_echo():
    """Initializes and runs the MCP stdio server."""
    logger.info(f"Echo MCP stdio Server starting up (prefix: {ECHO_PREFIX}). PID: {os.getpid()}")
    try:
        # mcp.server.stdio.stdio_server() provides the binary read/write streams for MCP communication
        async with mcp.server.stdio.stdio_server() as (binary_reader, binary_writer):
            logger.debug("stdio_server context manager entered. Binary reader/writer obtained.")
            
            # Define initialization options for the client
            init_options = InitializationOptions(
                server_name="EchoStdioSrvFriendlyName", # Name presented to clients
                server_version="0.2.0",             # Version of this server
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(receive=False, send=False), # Example: no notifications
                    experimental_capabilities={}  # **FIX APPLIED HERE**
                )
            )
            logger.debug(f"Server capabilities defined for client: {init_options.capabilities!r}")

            # Start the MCP server loop, listening on the provided streams
            await server.run(binary_reader, binary_writer, init_options)
            
            # This line is typically only reached if server.run() exits gracefully (e.g., client disconnects cleanly)
            logger.info("MCP server.run() completed.")

    except asyncio.CancelledError:
        logger.info("main_echo task was cancelled (e.g., during shutdown).")
    except Exception as e:
        # Catch any unexpected errors during server setup or run
        logger.critical(f"CRITICAL ERROR in main_echo: {e!r}", exc_info=True)
        # Re-raise to ensure the process exits with an error, signaling failure to the parent.
        raise
    finally:
        logger.info("main_echo function finished or exited.")

if __name__ == "__main__":
    # This block executes when the script is run directly (e.g., `python echo_server_stdio.py`)
    logger.info(f"Executing echo_server_stdio.py directly. Logging to: {LOG_FILE_PATH}")
    try:
        asyncio.run(main_echo())
    except KeyboardInterrupt:
        logger.info("echo_server_stdio.py terminated by user (KeyboardInterrupt).")
    except Exception as e_main:
        # Catch errors from asyncio.run(main_echo()) itself or unhandled exceptions from main_echo
        logger.critical(f"Unhandled exception in echo_server_stdio.py __main__ block: {e_main!r}", exc_info=True)
    finally:
        logger.info("echo_server_stdio.py process exiting.")