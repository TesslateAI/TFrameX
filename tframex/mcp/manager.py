# tframex/mcp/manager.py
import asyncio
import logging
from typing import Dict, Any, List, Optional, Tuple, TYPE_CHECKING

from .config import load_mcp_server_configs, MCPConfigError
from .server_connector import MCPConnectedServer
from .roots import RootsManager
from .sampling import SamplingManager, SamplingApprovalHandler
from .notifications import NotificationDispatcher, NotificationParser, ToolsChangedHandler, ResourcesChangedHandler, PromptsChangedHandler, ProgressHandler, LogHandler, NotificationType
from .capabilities import CapabilityManager, ClientCapability, ServerCapability, ProtocolCapability
from .progress import ProgressTracker
from .content import ContentProcessor
from tframex.models.primitives import ToolDefinition # For LLM tool formatting
from mcp.types import ( # Corrected imports
    Tool as ActualMCPTool,
    Resource as ActualMCPResource,
    Prompt as ActualMCPPrompt,
    TextContent, ImageContent, EmbeddedResource # For result parsing
)

if TYPE_CHECKING:
    from tframex.util.llms import BaseLLMWrapper

logger = logging.getLogger("tframex.mcp.manager")

class MCPManager:
    """
    Enhanced MCP Manager with full capability support.
    Manages servers, capabilities, notifications, and client features.
    """
    
    def __init__(self, 
                 mcp_config_file_path: Optional[str] = "servers_config.json",
                 default_llm: Optional["BaseLLMWrapper"] = None,
                 enable_roots: bool = True,
                 enable_sampling: bool = True,
                 enable_experimental: bool = False,
                 roots_allowed_paths: Optional[List[str]] = None):
        """
        Initialize enhanced MCP manager.
        
        Args:
            mcp_config_file_path: Path to MCP configuration file
            default_llm: Default LLM for sampling
            enable_roots: Enable roots capability
            enable_sampling: Enable sampling capability  
            enable_experimental: Enable experimental features
            roots_allowed_paths: Allowed paths for roots
        """
        self.config_file_path = mcp_config_file_path
        self.servers: Dict[str, MCPConnectedServer] = {}
        self._is_shutting_down = False
        
        # Initialize capability management
        self.capability_manager = CapabilityManager(
            enable_roots=enable_roots,
            enable_sampling=enable_sampling,
            enable_experimental=enable_experimental
        )
        
        # Initialize roots management
        self.roots_manager = RootsManager(
            allowed_paths=roots_allowed_paths
        ) if enable_roots else None
        
        # Initialize sampling management
        approval_handler = SamplingApprovalHandler(auto_approve=False)  # TODO: Make configurable
        self.sampling_manager = SamplingManager(
            default_llm=default_llm,
            approval_handler=approval_handler
        ) if enable_sampling else None
        
        # Initialize notification system
        self.notification_dispatcher = NotificationDispatcher()
        self._setup_notification_handlers()
        
        # Initialize progress tracking
        self.progress_tracker = ProgressTracker()
        
        # Initialize content processing
        self.content_processor = ContentProcessor()
        
        # Negotiated capabilities per server
        self._negotiated_capabilities: Dict[str, ProtocolCapability] = {}
    
    def _setup_notification_handlers(self) -> None:
        """Setup notification handlers for different event types."""
        # Tools changed handler
        self.notification_dispatcher.register_handler(
            NotificationType.TOOLS_LIST_CHANGED,
            ToolsChangedHandler(self._on_tools_changed)
        )
        
        # Resources changed handler
        self.notification_dispatcher.register_handler(
            NotificationType.RESOURCES_LIST_CHANGED,
            ResourcesChangedHandler(self._on_resources_changed)
        )
        
        # Prompts changed handler
        self.notification_dispatcher.register_handler(
            NotificationType.PROMPTS_LIST_CHANGED,
            PromptsChangedHandler(self._on_prompts_changed)
        )
        
        # Progress handler
        self.notification_dispatcher.register_handler(
            NotificationType.PROGRESS,
            ProgressHandler(self._on_progress_update)
        )
        
        # Log handler
        self.notification_dispatcher.register_handler(
            NotificationType.LOG_MESSAGE,
            LogHandler(forward_to_logger=True)
        )
    
    async def _on_tools_changed(self) -> None:
        """Handle tools list change notification."""
        logger.info("Server tools changed, refreshing tool cache")
        # Could implement tool cache refresh here
    
    async def _on_resources_changed(self) -> None:
        """Handle resources list change notification."""
        logger.info("Server resources changed, refreshing resource cache")
        # Could implement resource cache refresh here
    
    async def _on_prompts_changed(self) -> None:
        """Handle prompts list change notification."""
        logger.info("Server prompts changed, refreshing prompt cache")
        # Could implement prompt cache refresh here
    
    async def _on_progress_update(self, progress_update) -> None:
        """Handle progress update notification."""
        # Forward to progress tracker or other handlers
        logger.debug(f"Progress update: {progress_update.operation_id} - {progress_update.progress*100:.1f}%")

    async def initialize_servers(self):
        """
        Initialize MCP servers with capability negotiation and notification setup.
        """
        if self._is_shutting_down:
            logger.warning("MCPManager is shutting down, cannot initialize servers.")
            return
        if not self.config_file_path:
            logger.info("No MCP config file path provided. Skipping MCP server initialization.")
            return

        # Start notification dispatcher
        await self.notification_dispatcher.start()

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

        # Create server instances with enhanced capabilities
        for alias, config in new_server_configs.items():
            server = MCPConnectedServer(alias, config)
            
            # Setup notification forwarding for this server
            server.set_notification_callback(self._handle_server_notification)
            
            self.servers[alias] = server
        
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
                # Perform capability negotiation for successful servers
                server = self.servers[alias]
                await self._negotiate_server_capabilities(alias, server)
        
        for alias in aliases_to_remove:
            if alias in self.servers:
                # The server.initialize() method should call its own cleanup on failure.
                # Here, we just remove it from the manager's active list.
                logger.info(f"Removing failed server '{alias}' from active MCP manager list.")
                del self.servers[alias]
        
        logger.info(f"MCPManager: {successful_count}/{len(init_tasks_map)} new MCP servers initialized successfully.")
    
    async def _handle_server_notification(self, server_alias: str, raw_message: Any) -> None:
        """Handle notification from a server."""
        notification = NotificationParser.parse_message(raw_message)
        if notification:
            # Add server context to notification
            if notification.params is None:
                notification.params = {}
            notification.params["server_alias"] = server_alias
            
            await self.notification_dispatcher.dispatch(notification)
    
    async def _negotiate_server_capabilities(self, server_alias: str, server: MCPConnectedServer) -> None:
        """Negotiate capabilities with a server."""
        try:
            # Build client capabilities
            client_cap = self.capability_manager.build_client_capabilities(
                roots_manager=self.roots_manager,
                sampling_manager=self.sampling_manager
            )
            
            # Extract server capabilities
            server_cap = ServerCapability(
                tools=server.capabilities.tools if server.capabilities and hasattr(server.capabilities, 'tools') else None,
                resources=server.capabilities.resources if server.capabilities and hasattr(server.capabilities, 'resources') else None,
                prompts=server.capabilities.prompts if server.capabilities and hasattr(server.capabilities, 'prompts') else None,
                logging=server.capabilities.logging if server.capabilities and hasattr(server.capabilities, 'logging') else None,
                experimental=server.capabilities.experimental if server.capabilities and hasattr(server.capabilities, 'experimental') else {}
            )
            
            # Negotiate capabilities
            negotiated = self.capability_manager.negotiate_capabilities(
                client_cap=client_cap,
                server_cap=server_cap,
                protocol_version="2025-06-18"  # TODO: Get from server
            )
            
            # Store negotiated capabilities
            self._negotiated_capabilities[server_alias] = negotiated
            self.capability_manager.store_server_capabilities(server_alias, server_cap)
            
            logger.info(f"Capabilities negotiated with server '{server_alias}'")
            
        except Exception as e:
            logger.error(f"Error negotiating capabilities with server '{server_alias}': {e}", exc_info=True)


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

    # New capability methods
    
    def get_client_capabilities(self) -> ClientCapability:
        """Get current client capabilities."""
        return self.capability_manager.build_client_capabilities(
            roots_manager=self.roots_manager,
            sampling_manager=self.sampling_manager
        )
    
    def get_negotiated_capabilities(self, server_alias: str) -> Optional[ProtocolCapability]:
        """Get negotiated capabilities for a server."""
        return self._negotiated_capabilities.get(server_alias)
    
    # Roots management methods
    
    async def add_root(self, path: str, name: Optional[str] = None) -> bool:
        """Add a filesystem root."""
        if not self.roots_manager:
            logger.warning("Roots capability not enabled")
            return False
        return await self.roots_manager.add_root(path, name)
    
    async def remove_root(self, uri: str) -> bool:
        """Remove a filesystem root."""
        if not self.roots_manager:
            return False
        return await self.roots_manager.remove_root(uri)
    
    async def list_roots(self) -> List[Any]:
        """List current filesystem roots."""
        if not self.roots_manager:
            return []
        roots = await self.roots_manager.list_roots()
        return [root.to_dict() for root in roots]
    
    async def validate_file_access(self, file_uri: str) -> bool:
        """Validate file access against roots."""
        if not self.roots_manager:
            return True  # Allow if roots not enabled
        return await self.roots_manager.validate_access(file_uri)
    
    # Sampling methods
    
    async def handle_sampling_request(self, request_id: str, server_alias: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle MCP sampling request."""
        if not self.sampling_manager:
            return {
                "error": {
                    "code": -32601,
                    "message": "Sampling capability not enabled"
                }
            }
        return await self.sampling_manager.handle_sampling_request(request_id, server_alias, params)
    
    # Content processing methods
    
    async def process_content(self, raw_content: Any, content_type: Optional[str] = None) -> Any:
        """Process multi-modal content."""
        from .content import ContentType
        ct = ContentType(content_type) if content_type else None
        return await self.content_processor.process_content(raw_content, ct)
    
    # Progress tracking methods
    
    async def create_operation(self, name: str, description: Optional[str] = None) -> str:
        """Create a tracked operation."""
        operation = await self.progress_tracker.create_operation(name, description)
        return operation.id
    
    async def update_operation_progress(self, operation_id: str, progress: float, message: Optional[str] = None) -> bool:
        """Update operation progress."""
        return await self.progress_tracker.update_progress(operation_id, progress, message)
    
    async def complete_operation(self, operation_id: str, message: Optional[str] = None) -> bool:
        """Complete an operation."""
        return await self.progress_tracker.complete_operation(operation_id, message)
    
    async def cancel_operation(self, operation_id: str) -> bool:
        """Cancel an operation."""
        return await self.progress_tracker.cancel_operation(operation_id)
    
    def list_operations(self, limit: int = 100) -> List[Dict[str, Any]]:
        """List tracked operations."""
        operations = self.progress_tracker.list_operations(limit=limit)
        return [op.to_dict() for op in operations]
    
    # Statistics and monitoring
    
    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive statistics."""
        return {
            "servers": {
                alias: {
                    "initialized": server.is_initialized,
                    "tool_count": len(server.tools) if server.tools else 0,
                    "resource_count": len(server.resources) if server.resources else 0,
                    "prompt_count": len(server.prompts) if server.prompts else 0
                }
                for alias, server in self.servers.items()
            },
            "capabilities": {
                "roots_enabled": self.roots_manager is not None,
                "sampling_enabled": self.sampling_manager is not None,
                "negotiated_servers": list(self._negotiated_capabilities.keys())
            },
            "notifications": self.notification_dispatcher.get_stats(),
            "operations": {
                "active_count": len([op for op in self.progress_tracker.list_operations() 
                                   if op.status.value == "running"]),
                "total_count": len(self.progress_tracker.list_operations())
            }
        }

    async def shutdown_all_servers(self):
        """Enhanced shutdown with all component cleanup."""
        if self._is_shutting_down:
            return
        self._is_shutting_down = True # Set flag immediately
        logger.info("MCPManager: Initiating enhanced shutdown for all connected MCP servers and components...")
        
        # Stop notification dispatcher
        await self.notification_dispatcher.stop()
        
        # Shutdown progress tracker
        await self.progress_tracker.shutdown()
        
        # Cleanup sampling manager
        if self.sampling_manager:
            await self.sampling_manager.cleanup()
        
        # Shutdown servers
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
        self._negotiated_capabilities.clear()
        logger.info("MCPManager: All server shutdown procedures completed and list cleared.")
        self._is_shutting_down = False # Reset flag after completion