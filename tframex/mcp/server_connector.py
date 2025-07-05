# tframex/mcp/server_connector.py
import asyncio
import logging
import os
import shutil
from contextlib import AsyncExitStack
from typing import List, Dict, Any, Optional

from mcp import ClientSession, StdioServerParameters, InitializeResult
from mcp.client.stdio import stdio_client
from mcp.client.streamable_http import streamablehttp_client
from .sse_transport import sse_client
from mcp.types import (
    Tool as ActualMCPTool, Resource as ActualMCPResource, Prompt as ActualMCPPrompt,
    # TextContent, ImageContent, EmbeddedResource # Not directly used in this file, but good to know
)

logger = logging.getLogger("tframex.mcp.server_connector")

# Default timeout for critical MCP server initialization steps (e.g., transport, session handshake)
DEFAULT_MCP_SERVER_INIT_STEP_TIMEOUT = 30.0  # seconds

class MCPConnectedServer:
    """
    Manages the connection and interaction with a single MCP server.
    Handles initialization, fetching primitives (tools, resources, prompts),
    calling tools, reading resources, getting prompts, and cleanup.
    """
    def __init__(self, server_alias: str, config: Dict[str, Any]):
        """
        Initializes an MCPConnectedServer instance.

        Args:
            server_alias: A unique alias for this server connection.
            config: The configuration dictionary for this server, typically from servers_config.json.
        """
        self.server_alias: str = server_alias
        self.config: Dict[str, Any] = config
        self.session: Optional[ClientSession] = None
        self.capabilities: Optional[Any] = None # Stores mcp.types.Capabilities
        self.server_info: Optional[Any] = None  # Stores mcp.types.ServerInformation

        self.tools: List[ActualMCPTool] = []
        self.resources: List[ActualMCPResource] = []
        self.prompts: List[ActualMCPPrompt] = []
        
        self._exit_stack: AsyncExitStack = AsyncExitStack()
        self._lock = asyncio.Lock() # Ensures thread-safe operations on initialization/cleanup
        self.is_initialized = False # True if the server has successfully initialized and fetched primitives
        self._notification_listener_task: Optional[asyncio.Task] = None
        self._read_stream_for_listener: Optional[Any] = None
        self._notification_callback: Optional[callable] = None

        # Timeout for individual critical steps during server initialization
        self.init_step_timeout: float = self.config.get(
            "init_step_timeout", DEFAULT_MCP_SERVER_INIT_STEP_TIMEOUT
        )
    
    def set_notification_callback(self, callback: callable) -> None:
        """Set callback for handling server notifications."""
        self._notification_callback = callback

    async def initialize(self) -> bool:
        """
        Initializes the connection to the MCP server.
        This involves:
        1. Establishing the transport (stdio or streamable-http).
        2. Creating an MCP ClientSession.
        3. Performing the MCP handshake (session.initialize()).
        4. Fetching server primitives (tools, resources, prompts).
        5. Setting up a (placeholder) notification listener.

        Returns:
            True if initialization was successful, False otherwise.
        """
        async with self._lock:
            if self.is_initialized:
                logger.debug(f"MCP server '{self.server_alias}' already initialized.")
                return True

            logger.info(f"Attempting initialization for MCP server '{self.server_alias}' (type: {self.config.get('type', 'unknown').lower()}). Timeout per step: {self.init_step_timeout}s.")
            server_type = self.config.get("type", "stdio").lower()
            self._read_stream_for_listener = None 
            write_stream_for_session = None
            initialization_successful = False

            try:
                logger.debug(f"[{self.server_alias}] DEBUG_POINT_0: Start of initialize try block.")
                
                # --- 1. Establish Transport ---
                if server_type == "stdio":
                    command_path_config = self.config.get("command")
                    command_path = None
                    if command_path_config: # Check if config string is not None or empty
                        # Special handling for 'npx' for cross-platform Node.js scripts
                        if command_path_config.lower() == "npx":
                            resolved_npx = shutil.which("npx") or shutil.which("npx.cmd")
                            command_path = resolved_npx
                        else:
                            command_path = shutil.which(command_path_config)
                    
                    if not command_path: 
                        err_cmd_str = command_path_config or "configured command"
                        raise FileNotFoundError(f"Command '{err_cmd_str}' for stdio server '{self.server_alias}' not found in PATH or as absolute path.")
                    
                    logger.debug(f"[{self.server_alias}] Resolved stdio command: {command_path}")
                    env_config = self.config.get("env")
                    # Merge with current process environment, allowing config to override
                    full_env = {**os.environ, **env_config} if env_config else {**os.environ}
                    server_params = StdioServerParameters(command=command_path, args=self.config.get("args", []), env=full_env)
                    logger.debug(f"[{self.server_alias}] StdioServerParameters: {server_params!r}") # Use !r for more detail
                    
                    transport_context = stdio_client(server_params)
                    # Stdio client creation itself is usually fast; timeout more critical for handshake
                    self._read_stream_for_listener, write_stream_for_session = await self._exit_stack.enter_async_context(transport_context)
                    logger.info(f"[{self.server_alias}] Stdio transport established.")

                elif server_type == "streamable-http":
                    url = self.config.get("url")
                    if not url: raise ValueError(f"URL missing for streamable-http server '{self.server_alias}'.")
                    logger.info(f"[{self.server_alias}] Attempting HTTP connection to: {url}")
                    
                    transport_context = streamablehttp_client(url)
                    logger.debug(f"[{self.server_alias}] streamablehttp_client created for {url}.")
                    # The streamablehttp_client's __aenter__ makes the initial HTTP request.
                    # A timeout here protects against unresponsive HTTP servers during initial connection.
                    self._read_stream_for_listener, write_stream_for_session, http_response = \
                        await asyncio.wait_for(
                            self._exit_stack.enter_async_context(transport_context),
                            timeout=self.init_step_timeout
                        )
                    status_code = getattr(http_response, 'status_code', None) or getattr(http_response, 'status', None)
                    logger.info(f"[{self.server_alias}] HTTP transport context entered. Initial HTTP status: {status_code}. Streams obtained.")
                
                elif server_type == "sse":
                    # SSE (Server-Sent Events) transport
                    base_url = self.config.get("url")
                    if not base_url: raise ValueError(f"URL missing for SSE server '{self.server_alias}'.")
                    
                    headers = self.config.get("headers", {})
                    logger.info(f"[{self.server_alias}] Attempting SSE connection to: {base_url}")
                    
                    transport_context = sse_client(base_url, headers)
                    logger.debug(f"[{self.server_alias}] SSE client created for {base_url}.")
                    
                    self._read_stream_for_listener, write_stream_for_session = \
                        await asyncio.wait_for(
                            self._exit_stack.enter_async_context(transport_context),
                            timeout=self.init_step_timeout
                        )
                    logger.info(f"[{self.server_alias}] SSE transport context entered. Streams obtained.")
                
                else:
                    raise ValueError(f"Unsupported server type '{server_type}' for '{self.server_alias}'. Supported: stdio, streamable-http, sse")

                if not self._read_stream_for_listener or not write_stream_for_session:
                    raise ConnectionError(f"Failed to establish read/write streams for '{self.server_alias}'. This should not happen if transport was successful.")
                logger.debug(f"[{self.server_alias}] DEBUG_POINT_1: Transport streams successfully established.")

                # --- 2. Create ClientSession and Perform MCP Handshake ---
                self.session = await self._exit_stack.enter_async_context(
                    ClientSession(self._read_stream_for_listener, write_stream_for_session) 
                )
                logger.debug(f"[{self.server_alias}] DEBUG_POINT_2: ClientSession created. Attempting session.initialize() with timeout {self.init_step_timeout}s.")
                
                init_result: InitializeResult = await asyncio.wait_for(
                    self.session.initialize(), # MCP Handshake
                    timeout=self.init_step_timeout
                )
                self.capabilities = init_result.capabilities
                self.server_info = init_result.serverInfo
                s_name = getattr(self.server_info, 'name', 'N/A_NAME')
                s_version = getattr(self.server_info, 'version', 'N/A_VER')
                logger.info(f"MCP server '{self.server_alias}' session initialized: {s_name} v{s_version}")
                logger.debug(f"[{self.server_alias}] DEBUG_POINT_3: MCP session.initialize() complete. Capabilities: {self.capabilities!r}")
                
                # --- 3. Fetch Server Primitives (Tools, Resources, Prompts) ---
                await self._fetch_server_primitives() # This method has its own internal timeouts/error handling
                logger.debug(f"[{self.server_alias}] DEBUG_POINT_4: Server primitives fetched. Tools: {len(self.tools)}, Resources: {len(self.resources)}, Prompts: {len(self.prompts)}")

                # --- 4. Setup Notification Listener (Placeholder) ---
                # Note: For a robust notification listener, it should handle stream reading carefully.
                # The current one is a placeholder.
                if self._read_stream_for_listener: 
                    self._notification_listener_task = asyncio.create_task(
                        self._listen_for_notifications(self._read_stream_for_listener) 
                    )
                    await asyncio.sleep(0.01) # Give the task a moment to start or fail fast
                    if self._notification_listener_task.done():
                        listener_exc = self._notification_listener_task.exception()
                        if listener_exc:
                           logger.error(f"[{self.server_alias}] Notification listener task failed on startup!", exc_info=listener_exc)
                        else:
                           logger.info(f"[{self.server_alias}] Notification listener task completed very quickly (or was cancelled). Task: {self._notification_listener_task!r}")
                    else:
                        logger.info(f"Placeholder notification listener task created for '{self.server_alias}'. Task: {self._notification_listener_task!r}")
                else:
                    # This case should ideally not be reached if transport setup was successful.
                    logger.warning(f"No raw read stream available for placeholder notification listener for '{self.server_alias}'. This might indicate an issue in transport setup.")
                logger.debug(f"[{self.server_alias}] DEBUG_POINT_5: Notification listener setup attempted.")
                
                initialization_successful = True 
                logger.debug(f"[{self.server_alias}] DEBUG_POINT_6: Reached end of successful try block.")

            except asyncio.TimeoutError as e_timeout:
                logger.error(f"TIMEOUT ({self.init_step_timeout}s) during critical initialization step for MCP server '{self.server_alias}': {e_timeout}", exc_info=False) # exc_info=False to reduce noise for common timeouts
                initialization_successful = False
            except FileNotFoundError as e_fnf:
                logger.error(f"COMMAND NOT FOUND for stdio server '{self.server_alias}': {e_fnf}", exc_info=False)
                initialization_successful = False
            except ConnectionRefusedError as e_conn_refused:
                url_for_error = self.config.get('url', 'configured URL')
                logger.error(f"CONNECTION REFUSED for http server '{self.server_alias}' at {url_for_error}: {e_conn_refused}. Is the server running?", exc_info=False)
                initialization_successful = False
            except Exception as e: # Catch-all for other init errors
                logger.error(f"CRITICAL UNHANDLED ERROR during initialization of MCP server '{self.server_alias}': {e}", exc_info=True)
                initialization_successful = False 
            
            finally:
                if initialization_successful:
                    self.is_initialized = True
                    logger.info(f"MCP Server '{self.server_alias}' FULLY INITIALIZED successfully and marked as ready.")
                else:
                    self.is_initialized = False 
                    logger.error(f"MCP Server '{self.server_alias}' FAILED to initialize fully. is_initialized remains False.")
                    # Perform immediate cleanup if initialization failed to release resources.
                    # The MCPManager will also attempt cleanup if this server is removed.
                    # This ensures resources are released even if manager doesn't get to it.
                    logger.info(f"Performing immediate cleanup for failed server '{self.server_alias}' due to initialization failure.")
                    await self.cleanup(initiated_by_failure=True) # Pass a flag to indicate context
                
                return self.is_initialized

    async def _listen_for_notifications(self, stream_to_listen_on: Any):
        """
        Enhanced notification listener that parses and forwards MCP notifications.
        """
        logger.debug(f"[{self.server_alias}] Enhanced notification listener active on stream: {type(stream_to_listen_on)}.")
        try:
            while self.is_initialized and stream_to_listen_on:
                # Try to receive a message from the stream
                try:
                    if hasattr(stream_to_listen_on, 'receive'):
                        # Standard MCP stream with receive method
                        message = await asyncio.wait_for(
                            stream_to_listen_on.receive(),
                            timeout=5.0  # 5 second timeout
                        )
                        
                        # Parse and forward notification
                        if message and self._notification_callback:
                            try:
                                # Check if it's a notification (no 'id' field)
                                if isinstance(message, dict) and 'id' not in message:
                                    await self._notification_callback(self.server_alias, message)
                            except Exception as e:
                                logger.error(f"Error forwarding notification from '{self.server_alias}': {e}")
                    
                    elif getattr(stream_to_listen_on, 'at_eof', lambda: True)():
                        # Stream reports EOF
                        logger.info(f"[{self.server_alias}] Notification listener: Stream at EOF. Exiting loop.")
                        break
                    else:
                        # Fallback: sleep and check periodically
                        await asyncio.sleep(1)
                
                except asyncio.TimeoutError:
                    # Timeout is normal - just continue listening
                    continue
                except Exception as e:
                    if self.is_initialized:
                        logger.debug(f"Notification receive error for '{self.server_alias}': {e}")
                    await asyncio.sleep(1)  # Brief pause before retry
                    
        except asyncio.CancelledError:
            logger.info(f"Notification listener for '{self.server_alias}' was cancelled.")
        except Exception as e:
            # Only log errors if the server was meant to be initialized and running.
            if self.is_initialized: 
                logger.error(f"Error in notification listener for '{self.server_alias}': {e}", exc_info=True)
        finally:
            logger.info(f"Enhanced notification listener for '{self.server_alias}' stopped.")


    async def _fetch_server_primitives(self):
        """Fetches tools, resources, and prompts from the initialized MCP server session."""
        if not self.session: # self.is_initialized is checked by callers
            logger.warning(f"Cannot fetch primitives for '{self.server_alias}'; session is not available.")
            return
        if not self.capabilities: # Should be set if session.initialize() was successful
             logger.warning(f"Cannot fetch primitives for '{self.server_alias}'; capabilities not populated.")
             return

        cap = self.capabilities # mcp.types.Capabilities
        # Check if capability attributes exist AND are True (or their specific truthy value)
        can_list_tools = hasattr(cap, 'tools') and bool(cap.tools)
        can_list_resources = hasattr(cap, 'resources') and bool(cap.resources)
        can_list_prompts = hasattr(cap, 'prompts') and bool(cap.prompts)

        # Use a short timeout for these list calls, as they should be quick.
        PRIMITIVE_FETCH_TIMEOUT = 15.0

        async def fetch_with_timeout(coro, primitive_name):
            try:
                return await asyncio.wait_for(coro, timeout=PRIMITIVE_FETCH_TIMEOUT)
            except asyncio.TimeoutError:
                logger.warning(f"Timeout fetching {primitive_name} for '{self.server_alias}'.")
            except Exception as e:
                logger.warning(f"Could not fetch {primitive_name} for '{self.server_alias}': {e}", exc_info=False) # exc_info=False to reduce noise
            return None

        if can_list_tools:
            resp = await fetch_with_timeout(self.session.list_tools(), "tools")
            self.tools = resp.tools if resp and hasattr(resp, 'tools') else []
        
        if can_list_resources:
            resp = await fetch_with_timeout(self.session.list_resources(), "resources")
            self.resources = resp.resources if resp and hasattr(resp, 'resources') else []

        if can_list_prompts:
            resp = await fetch_with_timeout(self.session.list_prompts(), "prompts")
            self.prompts = resp.prompts if resp and hasattr(resp, 'prompts') else []
        
        logger.debug(f"[{self.server_alias}] Primitives fetched: {len(self.tools)} tools, {len(self.resources)} resources, {len(self.prompts)} prompts.")

    async def call_mcp_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any: 
        """Calls a tool on the MCP server."""
        if not self.session or not self.is_initialized:
            # This state should ideally be prevented by checks in MCPManager or Engine.
            logger.error(f"Attempted to call tool '{tool_name}' on uninitialized/unavailable server '{self.server_alias}'.")
            raise RuntimeError(f"MCP server '{self.server_alias}' not initialized for tool call.")
        logger.info(f"Calling MCP tool '{tool_name}' on server '{self.server_alias}' with args: {arguments}")
        # Add timeout for the tool call itself, can be configured per server or globally.
        tool_call_timeout = self.config.get("tool_call_timeout", 60.0) # Default 60s
        try:
            return await asyncio.wait_for(
                self.session.call_tool(tool_name, arguments),
                timeout=tool_call_timeout
            )
        except asyncio.TimeoutError:
            logger.error(f"Timeout calling MCP tool '{tool_name}' on '{self.server_alias}' after {tool_call_timeout}s.")
            # Return an MCP-like error structure if possible, or raise specific exception.
            # For now, let it propagate as TimeoutError or wrap in a custom one.
            raise # Re-raise for the engine to handle and convert to a tool error message.

    async def read_mcp_resource(self, uri: str) -> Any: 
        """Reads a resource from the MCP server."""
        if not self.session or not self.is_initialized:
            logger.error(f"Attempted to read resource '{uri}' on uninitialized/unavailable server '{self.server_alias}'.")
            raise RuntimeError(f"MCP server '{self.server_alias}' not initialized for resource read.")
        logger.info(f"Reading MCP resource '{uri}' from server '{self.server_alias}'")
        resource_read_timeout = self.config.get("resource_read_timeout", 30.0)
        try:
            return await asyncio.wait_for(
                self.session.read_resource(uri),
                timeout=resource_read_timeout
            )
        except asyncio.TimeoutError:
            logger.error(f"Timeout reading MCP resource '{uri}' from '{self.server_alias}' after {resource_read_timeout}s.")
            raise

    async def get_mcp_prompt(self, prompt_name: str, arguments: Dict[str, Any]) -> Any: 
        """Gets a prompt (its messages) from the MCP server."""
        if not self.session or not self.is_initialized:
            logger.error(f"Attempted to get prompt '{prompt_name}' on uninitialized/unavailable server '{self.server_alias}'.")
            raise RuntimeError(f"MCP server '{self.server_alias}' not initialized for get prompt.")
        logger.info(f"Getting MCP prompt '{prompt_name}' from server '{self.server_alias}' with args: {arguments}")
        prompt_get_timeout = self.config.get("prompt_get_timeout", 30.0)
        try:
            return await asyncio.wait_for(
                self.session.get_prompt(prompt_name, arguments),
                timeout=prompt_get_timeout
            )
        except asyncio.TimeoutError:
            logger.error(f"Timeout getting MCP prompt '{prompt_name}' from '{self.server_alias}' after {prompt_get_timeout}s.")
            raise

    async def cleanup(self, initiated_by_failure: bool = False):
        """
        Cleans up resources associated with this server connection.
        This includes cancelling the notification listener and closing the AsyncExitStack
        (which handles closing the MCP session and transport).

        Args:
            initiated_by_failure: If True, indicates cleanup is due to initialization failure.
        """
        async with self._lock: # Ensure cleanup is atomic for this instance
            # Check if substantial resources were allocated that need cleaning.
            # If it was never initialized and exit stack is empty, minimal cleanup needed.
            if not self.is_initialized and not initiated_by_failure and not self._exit_stack._exit_callbacks and not self._notification_listener_task and not self.session:
                 logger.debug(f"Cleanup for '{self.server_alias}' skipped (already clean or not substantially initialized).")
                 return
            
            # Log differently based on whether it was a successful run or a failed init
            if initiated_by_failure:
                logger.warning(f"Starting cleanup for MCP server '{self.server_alias}' due to initialization failure...")
            else:
                logger.info(f"Starting cleanup for MCP server '{self.server_alias}'...")
            
            was_initialized_before_cleanup = self.is_initialized 
            self.is_initialized = False # Mark as not initialized immediately to stop dependent operations

            # 1. Cancel and await notification listener task
            if self._notification_listener_task and not self._notification_listener_task.done():
                logger.debug(f"Cancelling notification listener for '{self.server_alias}'...")
                self._notification_listener_task.cancel()
                try:
                    # Wait for a short period; don't let cleanup hang indefinitely on this task.
                    await asyncio.wait_for(self._notification_listener_task, timeout=5.0) 
                except asyncio.CancelledError:
                    logger.debug(f"Notification listener task for '{self.server_alias}' successfully cancelled.")
                except asyncio.TimeoutError:
                    logger.warning(f"Timeout (5s) waiting for notification listener of '{self.server_alias}' to complete cancellation.")
                except Exception as e_task_cancel: # Catch any other errors during task await
                     logger.error(f"Error awaiting notification listener cancellation for '{self.server_alias}': {e_task_cancel}", exc_info=True)
            self._notification_listener_task = None 
            
            # 2. Close the AsyncExitStack (this handles ClientSession.aclose() and transport context aclose())
            try:
                # _exit_stack.aclose() calls __aexit__ on ClientSession and then on the transport context (stdio_client/streamablehttp_client)
                await self._exit_stack.aclose() 
                logger.info(f"AsyncExitStack for '{self.server_alias}' closed successfully (session and transport cleaned).")
            except Exception as e_stack_close: 
                logger.error(f"Error during AsyncExitStack.aclose() for '{self.server_alias}': {e_stack_close}", exc_info=True)
            
            # 3. Reset internal state
            self.session = None # Session is closed by AsyncExitStack
            self.capabilities = None
            self.server_info = None
            self.tools, self.resources, self.prompts = [], [], []
            self._read_stream_for_listener = None 

            # Re-initialize the exit stack for potential future re-initialization (though not typical for a single instance)
            self._exit_stack = AsyncExitStack() 
            
            if initiated_by_failure:
                logger.warning(f"MCP server '{self.server_alias}' cleanup finished (triggered by initialization failure).")
            elif was_initialized_before_cleanup:
                logger.info(f"MCP server '{self.server_alias}' successfully cleaned up (was previously initialized).")
            else: # Cleanup called on an instance that wasn't fully initialized but not due to explicit failure handling
                logger.info(f"MCP server '{self.server_alias}' cleanup finished (was not fully initialized or already partially cleaned).")