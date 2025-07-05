# tframex/app.py
import asyncio
import inspect
import logging
import os
from typing import Any, Callable, Coroutine, Dict, List, Optional, Type, Union

try:
    from typing import AsyncGenerator
except ImportError:
    from typing_extensions import AsyncGenerator

from .agents.base import BaseAgent
from .agents.llm_agent import LLMAgent
from .flows.flow_context import FlowContext
from .flows.flows import Flow
from .models.primitives import Message, MessageChunk, ToolDefinition, ToolParameters, ToolParameterProperty
from .util.engine import Engine
from .util.llms import BaseLLMWrapper
from .util.logging.logging_config import setup_logging # Assuming this is your setup
from .util.memory import BaseMemoryStore, InMemoryMemoryStore
from .util.tools import Tool

# --- MCP Integration Imports ---
from .mcp.manager import MCPManager
from .mcp.meta_tools import (
    tframex_list_mcp_servers,
    tframex_list_mcp_resources,
    tframex_read_mcp_resource,
    tframex_list_mcp_prompts,
    tframex_use_mcp_prompt
)

# Call setup_logging here or ensure it's called by the application using the library
# setup_logging(level=logging.INFO) # Example: if you want TFrameX to set a default
logger = logging.getLogger("tframex.app")

class TFrameXApp:
    def __init__(
        self,
        default_llm: Optional[BaseLLMWrapper] = None,
        default_memory_store_factory: Callable[[], BaseMemoryStore] = InMemoryMemoryStore,
        mcp_config_file: Optional[str] = "servers_config.json",
        enable_mcp_roots: bool = True,
        enable_mcp_sampling: bool = True,
        enable_mcp_experimental: bool = False,
        mcp_roots_allowed_paths: Optional[List[str]] = None,
    ):
        self._tools: Dict[str, Tool] = {}
        self._agents: Dict[str, Dict[str, Any]] = {}
        self._flows: Dict[str, Flow] = {}

        self.default_llm = default_llm
        self.default_memory_store_factory = default_memory_store_factory

        self._mcp_manager: Optional[MCPManager] = None
        if mcp_config_file:
            try:
                self._mcp_manager = MCPManager(
                    mcp_config_file_path=mcp_config_file,
                    default_llm=default_llm,
                    enable_roots=enable_mcp_roots,
                    enable_sampling=enable_mcp_sampling,
                    enable_experimental=enable_mcp_experimental,
                    roots_allowed_paths=mcp_roots_allowed_paths
                )
                logger.info(f"Enhanced MCPManager initialized with config file: {mcp_config_file}")
                logger.info(f"MCP capabilities: roots={enable_mcp_roots}, sampling={enable_mcp_sampling}, experimental={enable_mcp_experimental}")
            except Exception as e:
                logger.error(f"Failed to initialize MCPManager with {mcp_config_file}: {e}", exc_info=True)
        else:
            logger.info("No MCP config file provided, MCP integration will be limited or disabled.")

        if not default_llm and not os.getenv("TFRAMEX_ALLOW_NO_DEFAULT_LLM"): # Example env var check
            logger.warning(
                "TFrameXApp initialized without a default LLM. LLM must be provided to run_context or agent for LLM-based agents to function."
            )
        
        self._register_mcp_meta_tools()

    def _register_mcp_meta_tools(self):
        """Registers client-side functions for interacting with MCP as native TFrameX tools."""
        if not self._mcp_manager: # Only register if MCP manager is set up
            logger.debug("MCP meta-tools registration skipped: MCPManager not available.")
            return

        logger.debug("Registering MCP meta-tools...")
        
        self.tool(name="tframex_list_mcp_servers", description="Lists all configured and initialized MCP servers.")(tframex_list_mcp_servers)
        
        list_resources_params = ToolParameters(
            properties={
                "server_alias": ToolParameterProperty(type="string", description="Optional. The alias of a specific MCP server. If omitted, lists from all connected servers.")
            }, required=[] )
        self.tool(name="tframex_list_mcp_resources", description="Lists available resources from MCP server(s).", parameters_schema=list_resources_params)(tframex_list_mcp_resources)

        read_resource_params = ToolParameters(
            properties={
                "server_alias": ToolParameterProperty(type="string", description="The alias of the MCP server."),
                "resource_uri": ToolParameterProperty(type="string", description="The URI of the MCP resource to read.")
            }, required=["server_alias", "resource_uri"])
        self.tool(name="tframex_read_mcp_resource", description="Reads content from a specific MCP resource.", parameters_schema=read_resource_params)(tframex_read_mcp_resource)

        list_prompts_params = ToolParameters(
             properties={ "server_alias": ToolParameterProperty(type="string", description="Optional. Alias of a specific MCP server.") }, required=[])
        self.tool(name="tframex_list_mcp_prompts", description="Lists available prompts from MCP server(s).", parameters_schema=list_prompts_params)(tframex_list_mcp_prompts)

        use_prompt_params = ToolParameters(
            properties={
                "server_alias": ToolParameterProperty(type="string", description="Alias of the MCP server."),
                "prompt_name": ToolParameterProperty(type="string", description="Name of the MCP prompt."),
                "arguments": ToolParameterProperty(type="object", description="Key-value arguments for the prompt.")
            }, required=["server_alias", "prompt_name", "arguments"])
        self.tool(name="tframex_use_mcp_prompt", description="Uses a server-defined MCP prompt, returning its messages for the LLM.", parameters_schema=use_prompt_params)(tframex_use_mcp_prompt)
        logger.info("MCP meta-tools registered.")

    async def initialize_mcp_servers(self):
        if self._mcp_manager:
            logger.info("TFrameXApp: Explicitly initializing MCP servers...")
            await self._mcp_manager.initialize_servers()
        else:
            logger.info("TFrameXApp: No MCP manager to initialize servers from.")

    async def shutdown_mcp_servers(self):
        if self._mcp_manager:
            logger.info("TFrameXApp: Initiating shutdown of MCP servers...")
            await self._mcp_manager.shutdown_all_servers()
        else:
            logger.info("TFrameXApp: No MCP manager to shutdown.")

    def tool(
        self,
        name: Optional[str] = None,
        description: Optional[str] = None,
        parameters_schema: Optional[ToolParameters] = None, 
    ) -> Callable:
        def decorator(func: Callable[..., Any]) -> Callable:
            tool_name = name or func.__name__
            if tool_name in self._tools:
                if tool_name.startswith("tframex_"): # Allow re-registration for meta-tools
                     logger.debug(f"Re-registering MCP meta-tool: '{tool_name}'")
                else:
                    raise ValueError(f"Tool '{tool_name}' already registered.")

            parsed_params_obj = None
            if isinstance(parameters_schema, ToolParameters):
                parsed_params_obj = parameters_schema
            elif isinstance(parameters_schema, dict): 
                props = {
                    p_name: ToolParameterProperty(**p_def)
                    for p_name, p_def in parameters_schema.get("properties", {}).items()
                }
                required_list = parameters_schema.get("required")
                parsed_params_obj = ToolParameters(
                    properties=props, required=required_list if isinstance(required_list, list) else []
                )
            
            self._tools[tool_name] = Tool(
                name=tool_name,
                func=func,
                description=description,
                parameters_schema=parsed_params_obj, 
            )
            logger.debug(f"Registered tool: '{tool_name}'")
            return func
        return decorator

    def agent(
        self,
        name: Optional[str] = None,
        description: Optional[str] = None,
        callable_agents: Optional[List[str]] = None,
        system_prompt: Optional[str] = None,
        tools: Optional[List[str]] = None, 
        mcp_tools_from_servers: Optional[Union[List[str], str]] = None, 
        llm: Optional[BaseLLMWrapper] = None,
        memory_store: Optional[BaseMemoryStore] = None,
        agent_class: type[BaseAgent] = LLMAgent,
        strip_think_tags: bool = True,
        **agent_config: Any,
    ) -> Callable:
        def decorator(target: Union[Callable, type]) -> Union[Callable, type]:
            agent_name = name or getattr(target, "__name__", str(target))
            if agent_name in self._agents:
                raise ValueError(f"Agent '{agent_name}' already registered.")

            final_config = {
                "description": description,
                "callable_agent_names": callable_agents or [],
                "system_prompt_template": system_prompt,
                "native_tool_names": tools or [], 
                "mcp_tools_from_servers_config": mcp_tools_from_servers, # Store the user's preference
                "llm_instance_override": llm,
                "memory_override": memory_store,
                "agent_class_ref": agent_class,
                "strip_think_tags": strip_think_tags,
                **agent_config,
            }
            
            is_class_based_agent = inspect.isclass(target) and issubclass(target, BaseAgent)
            agent_class_to_log = target.__name__ if is_class_based_agent else agent_class.__name__

            self._agents[agent_name] = {
                "type": "custom_class_agent" if is_class_based_agent else "framework_managed_agent",
                "ref": target, # For class agents, this is the class itself
                "config": final_config,
            }
            logger.info(
                f"Registered agent: '{agent_name}' (Class: {agent_class_to_log}). "
                f"Native Tools: {final_config['native_tool_names']}. "
                f"MCP Tools from config: {mcp_tools_from_servers or 'None'}."
            )
            return target
        return decorator

    def get_tool(self, name: str) -> Optional[Tool]:
        return self._tools.get(name)

    def register_flow(self, flow_instance: Flow) -> None:
        if not isinstance(flow_instance, Flow):
            raise TypeError("Can only register an instance of the Flow class.")
        if flow_instance.flow_name in self._flows:
            raise ValueError(f"Flow with name '{flow_instance.flow_name}' already registered.")
        self._flows[flow_instance.flow_name] = flow_instance
        logger.debug(f"Registered flow: '{flow_instance.flow_name}' with {len(flow_instance.steps)} steps.")

    def get_flow(self, name: str) -> Optional[Flow]:
        return self._flows.get(name)

    def run_context(
        self,
        llm_override: Optional[BaseLLMWrapper] = None,
        # context_memory_override: Optional[BaseMemoryStore] = None, # Not used by context currently
    ) -> "TFrameXRuntimeContext":
        ctx_llm = llm_override or self.default_llm
        ctx_mcp_manager = self._mcp_manager 
        return TFrameXRuntimeContext(self, llm=ctx_llm, mcp_manager=ctx_mcp_manager)

class TFrameXRuntimeContext:
    def __init__(
        self,
        app: TFrameXApp,
        llm: Optional[BaseLLMWrapper], # LLM for this context
        mcp_manager: Optional[MCPManager] = None,
    ):
        self._app = app
        self.llm = llm 
        self.mcp_manager = mcp_manager 
        self.engine = Engine(app, self) # Engine gets this context instance

    async def __aenter__(self) -> "TFrameXRuntimeContext":
        llm_id = self.llm.model_id if self.llm else "None (App Default/Agent Specific)"
        logger.info(f"TFrameXRuntimeContext entered. Context LLM: {llm_id}.")
        if self.mcp_manager:
            if not self.mcp_manager.servers or \
                any(not s.is_initialized for s in self.mcp_manager.servers.values()):
                logger.info("RuntimeContext: Initializing MCP servers on enter (first time or some not ready)...")
                await self.mcp_manager.initialize_servers()
            else:
                logger.debug("RuntimeContext: All configured MCP servers already initialized by app or previous context.")
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        if (self.llm and hasattr(self.llm, "close") and inspect.iscoroutinefunction(self.llm.close)):
            try:
                await self.llm.close()
                logger.info(f"Context LLM client for {self.llm.model_id} closed.")
            except Exception as e:
                logger.error(f"Error closing context LLM client for {self.llm.model_id}: {e}")
        logger.info("TFrameXRuntimeContext exited.")
        
    async def run_flow(
        self,
        flow_ref: Union[str, Flow],
        initial_input: Message,
        initial_shared_data: Optional[Dict[str, Any]] = None,
        flow_template_vars: Optional[Dict[str, Any]] = None,
    ) -> FlowContext:
        flow_to_run: Optional[Flow] = None
        if isinstance(flow_ref, str):
            flow_to_run = self._app.get_flow(flow_ref)
            if not flow_to_run:
                raise ValueError(f"Flow with name '{flow_ref}' not found.")
        elif isinstance(flow_ref, Flow):
            flow_to_run = flow_ref
        else:
            raise TypeError("flow_ref must be a flow name (str) or a Flow instance.")
        return await flow_to_run.execute(
            initial_input,
            self.engine, 
            initial_shared_data=initial_shared_data,
            flow_template_vars=flow_template_vars,
        )

    async def call_agent(
        self, agent_name: str, input_message: Union[str, Message], **kwargs: Any
    ) -> Message:
        return await self.engine.call_agent(agent_name, input_message, **kwargs)
    
    async def call_agent_stream(
        self, agent_name: str, input_message: Union[str, Message], **kwargs: Any
    ) -> AsyncGenerator[MessageChunk, None]:
        """
        Stream response from an agent. Yields MessageChunk objects as they arrive.
        
        Args:
            agent_name: Name of the agent to call
            input_message: User input as string or Message object  
            **kwargs: Additional parameters passed to agent
            
        Yields:
            MessageChunk: Individual chunks of the streaming response
        """
        async for chunk in self.engine.call_agent_stream(agent_name, input_message, **kwargs):
            yield chunk

    async def interactive_chat(self, default_agent_name: Optional[str] = None) -> None:
        print("\n--- TFrameX Interactive Agent Chat (with MCP) ---")

        agent_to_chat_with = default_agent_name
        if not agent_to_chat_with:
            if not self._app._agents:
                print("No agents registered. Exiting interactive chat.")
                return
            print("Available agents:")
            agent_names_list = list(self._app._agents.keys())
            for i, name in enumerate(agent_names_list): print(f"  {i + 1}. {name}")
            while True:
                try:
                    choice = await asyncio.to_thread(input, "Select an agent (number or name): ")
                    if choice.isdigit() and 0 <= int(choice) - 1 < len(agent_names_list):
                        agent_to_chat_with = agent_names_list[int(choice) - 1]
                        break
                    elif choice in agent_names_list:
                        agent_to_chat_with = choice
                        break
                    else: print("Invalid selection.")
                except ValueError: print("Invalid input.")
                except KeyboardInterrupt: print("\nExiting."); return
        
        if not agent_to_chat_with: print("No agent selected. Exiting."); return

        print(f"\nChatting with Agent: '{agent_to_chat_with}'. Type 'exit' or 'quit'.")
        # For a persistent chat, you'd use the agent's memory.
        # This loop makes independent calls for simplicity.
        while True:
            try:
                user_input_str = await asyncio.to_thread(input, "\nYou: ")
                if user_input_str.lower() in ["exit", "quit"]: break
                if not user_input_str.strip(): continue
                
                print("Assistant: Thinking...")
                response_message = await self.call_agent(agent_to_chat_with, Message(role="user", content=user_input_str))
                
                print(f"\nAssistant ({response_message.role}):")
                if response_message.content: print(f"  Content: {response_message.content}")
                if response_message.tool_calls: print(f"  Final Tool Calls (should be processed by agent): {response_message.tool_calls}")
            except KeyboardInterrupt: break
            except Exception as e: print(f"Error: {e}"); logger.error("Chat Error", exc_info=True)
        print(f"--- Ended chat with Agent: '{agent_to_chat_with}' ---")