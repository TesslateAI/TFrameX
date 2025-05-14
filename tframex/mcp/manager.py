# tframex/mcp/manager.py
import asyncio
import logging
from typing import Dict, Any, List, Optional, Tuple

from .config import load_mcp_server_configs, MCPConfigError
from .server_connector import MCPConnectedServer
from tframex.models.primitives import ToolDefinition # For LLM tool formatting
from mcp.types import ( # Corrected imports
    Tool as ActualMCPTool,
    Resource as ActualMCPResource,
    Prompt as ActualMCPPrompt,
    TextContent, ImageContent, EmbeddedResource # For result parsing
)

logger = logging.getLogger("tframex.mcp.manager")

class MCPManager:
    def __init__(self, mcp_config_file_path: Optional[str] = "servers_config.json"):
        self.config_file_path = mcp_config_file_path
        self.servers: Dict[str, MCPConnectedServer] = {}
        self._is_shutting_down = False # To prevent multiple shutdown attempts

    async def initialize_servers(self):
        if self._is_shutting_down:
            logger.warning("MCPManager is shutting down, cannot initialize servers.")
            return
        if not self.config_file_path:
            logger.info("No MCP config file path provided. Skipping MCP server initialization.")
            return

        try:
            server_configs = load_mcp_server_configs(self.config_file_path)
        except MCPConfigError as e:
            logger.error(f"Failed to load MCP server configurations: {e}")
            return
        except FileNotFoundError:
            return # Already logged by load_mcp_server_configs

        if not server_configs:
            logger.info("No MCP servers defined in configuration.")
            return

        # Filter out already existing server aliases to avoid re-creating
        new_server_configs = {
            alias: config for alias, config in server_configs.items() if alias not in self.servers
        }

        for alias, config in new_server_configs.items():
            self.servers[alias] = MCPConnectedServer(alias, config)
        
        init_tasks_map = { # Only create tasks for servers not yet marked as initialized
            alias: server.initialize() for alias, server in self.servers.items() if not server.is_initialized and alias in new_server_configs
        }
        
        if not init_tasks_map:
            logger.info("All configured MCP servers are already initialized or no new servers to initialize from current config.")
            return

        results = await asyncio.gather(*init_tasks_map.values(), return_exceptions=True)
        
        successful_count = 0
        aliases_to_remove = []
        for i, alias in enumerate(init_tasks_map.keys()):
            init_success_flag_or_exception = results[i]
            if isinstance(init_success_flag_or_exception, Exception):
                logger.error(f"Exception during initialization of MCP server '{alias}': {init_success_flag_or_exception}", exc_info=init_success_flag_or_exception)
                aliases_to_remove.append(alias)
            elif init_success_flag_or_exception is False: # Explicit check for False return
                logger.error(f"Initialization task returned False for MCP server '{alias}', indicating setup failure.")
                aliases_to_remove.append(alias)
            else: # Assuming True means success
                successful_count += 1
        
        for alias in aliases_to_remove:
            if alias in self.servers:
                # The server.initialize() method should call its own cleanup on failure.
                # Here, we just remove it from the manager's active list.
                logger.info(f"Removing failed server '{alias}' from active MCP manager list.")
                del self.servers[alias]
        
        logger.info(f"MCPManager: {successful_count}/{len(init_tasks_map)} new MCP servers initialized successfully.")


    def get_server(self, server_alias: str) -> Optional[MCPConnectedServer]:
        server = self.servers.get(server_alias)
        if server and server.is_initialized:
            return server
        logger.warning(f"MCP Server '{server_alias}' not found or not initialized.")
        return None

    def get_all_mcp_tools_for_llm(self) -> List[ToolDefinition]:
        llm_tool_defs = []
        for server_alias, server in self.servers.items():
            if server.is_initialized and server.tools:
                for mcp_tool_info in server.tools: # mcp_tool_info is ActualMCPTool
                    parameters = mcp_tool_info.inputSchema if mcp_tool_info.inputSchema else {"type": "object", "properties": {}}
                    prefixed_name = f"{server_alias}__{mcp_tool_info.name}"
                    llm_tool_defs.append(
                        ToolDefinition( # This is tframex.models.primitives.ToolDefinition
                            type="function",
                            function={
                                "name": prefixed_name,
                                "description": mcp_tool_info.description or f"Tool '{mcp_tool_info.name}' from MCP server '{server_alias}'.",
                                "parameters": parameters,
                            }
                        )
                    )
        logger.debug(f"MCPManager provides {len(llm_tool_defs)} MCP tools for LLM.")
        return llm_tool_defs

    def get_all_mcp_resource_infos(self) -> Dict[str, List[ActualMCPResource]]:
        all_resources = {}
        for server_alias, server in self.servers.items():
            if server.is_initialized and server.resources:
                all_resources[server_alias] = server.resources
        return all_resources
        
    def get_all_mcp_prompt_infos(self) -> Dict[str, List[ActualMCPPrompt]]:
        all_prompts = {}
        for server_alias, server in self.servers.items():
            if server.is_initialized and server.prompts:
                all_prompts[server_alias] = server.prompts
        return all_prompts

    async def call_mcp_tool_by_prefixed_name(self, prefixed_tool_name: str, arguments: Dict[str, Any]) -> Any: # Returns MCP CallToolResult
        if self._is_shutting_down:
            logger.warning(f"MCPManager is shutting down. Call to '{prefixed_tool_name}' aborted.")
            return {"error": "MCP Manager is shutting down."} # Mimic tool error

        if "__" not in prefixed_tool_name:
            raise ValueError(f"MCP tool name '{prefixed_tool_name}' is not correctly prefixed with 'server_alias__'.")
        
        server_alias, actual_tool_name = prefixed_tool_name.split("__", 1)
        server = self.get_server(server_alias) # This checks is_initialized
        if not server:
            return {"error": f"MCP Server '{server_alias}' for tool '{actual_tool_name}' not available."} 
        
        try:
            # This returns the raw mcp.types.CallToolResult
            return await server.call_mcp_tool(actual_tool_name, arguments)
        except Exception as e:
            logger.error(f"Error calling MCP tool '{actual_tool_name}' on server '{server_alias}': {e}", exc_info=True)
            # Construct a CallToolResult-like error structure for consistency if possible,
            # or a simple error dict that the engine can parse.
            # For now, simple error dict to match other error paths in engine.
            return {"error": f"Failed to call MCP tool '{actual_tool_name}' on '{server_alias}': {str(e)}"}

    async def shutdown_all_servers(self):
        if self._is_shutting_down:
            return
        self._is_shutting_down = True # Set flag immediately
        logger.info("MCPManager: Initiating shutdown for all connected MCP servers...")
        
        servers_to_cleanup = list(self.servers.values()) # Iterate over a copy
        if not servers_to_cleanup:
            logger.info("MCPManager: No servers to shutdown.")
            self._is_shutting_down = False # Reset if nothing to do
            return

        cleanup_tasks = [server.cleanup() for server in servers_to_cleanup]
        results = await asyncio.gather(*cleanup_tasks, return_exceptions=True)
        
        # Log results of cleanup
        original_aliases = list(self.servers.keys()) # Get aliases before clearing
        for i, alias in enumerate(original_aliases):
            if i < len(results): # Check bounds for safety
                if isinstance(results[i], Exception):
                    logger.error(f"Exception during shutdown of MCP server '{alias}': {results[i]}", exc_info=results[i])
                else:
                    logger.info(f"MCP server '{alias}' shutdown process completed/invoked.")
            else: # Should not happen if gather returns for all tasks
                logger.warning(f"Missing cleanup result for MCP server '{alias}'.")

        self.servers.clear() 
        logger.info("MCPManager: All server shutdown procedures completed and list cleared.")
        self._is_shutting_down = False # Reset flag after completion