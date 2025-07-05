# tframex/util/engine.py
import asyncio
import inspect
import json
import logging
from typing import TYPE_CHECKING, Any, AsyncGenerator, Dict, List, Optional, Type, Union

from ..models.primitives import Message, MessageChunk, ToolDefinition, ToolParameters, ToolParameterProperty
from ..util.tools import Tool
# MCP specific types for parsing results if needed, though results are simplified to string/error dict
from mcp.types import TextContent, ImageContent, EmbeddedResource


if TYPE_CHECKING:
    from ..agents.base import BaseAgent
    from ..agents.llm_agent import LLMAgent # For issubclass check
    from ..app import TFrameXApp, TFrameXRuntimeContext 

logger = logging.getLogger("tframex.engine")

class Engine:
    def __init__(self, app: 'TFrameXApp', runtime_context: 'TFrameXRuntimeContext'):
        self._app = app
        self._runtime_context = runtime_context 
        self._agent_instances: Dict[str, 'BaseAgent'] = {}

    def _get_agent_instance(self, agent_name: str) -> 'BaseAgent':
        from ..agents.base import BaseAgent 
        from ..agents.llm_agent import LLMAgent # For issubclass check

        if agent_name not in self._agent_instances:
            if agent_name not in self._app._agents:
                raise ValueError(f"Agent '{agent_name}' not registered.")
            
            reg_info = self._app._agents[agent_name]
            agent_config_from_app = reg_info["config"] # This is the agent's specific config

            agent_llm = (
                agent_config_from_app.get("llm_instance_override")
                or self._runtime_context.llm 
                or self._app.default_llm
            )
            agent_memory = (
                agent_config_from_app.get("memory_override")
                or self._app.default_memory_store_factory()
            )

            resolved_native_tools: List[Tool] = []
            native_tool_names = agent_config_from_app.get("native_tool_names", [])
            for tool_name_ref in native_tool_names:
                tool_obj = self._app.get_tool(tool_name_ref)
                if tool_obj:
                    resolved_native_tools.append(tool_obj)
                else:
                    logger.warning(f"Native tool '{tool_name_ref}' for agent '{agent_name}' not found in app registry.")
            
            callable_agent_defs: List[ToolDefinition] = []
            callable_agent_names_cfg = agent_config_from_app.get("callable_agent_names", [])
            for sub_agent_name_cfg in callable_agent_names_cfg:
                if sub_agent_name_cfg in self._app._agents:
                    sub_agent_reg_info = self._app._agents[sub_agent_name_cfg]
                    sub_agent_desc = sub_agent_reg_info["config"].get("description") or f"Invoke agent '{sub_agent_name_cfg}'."
                    params = ToolParameters(properties={"input_message": ToolParameterProperty(type="string", description="Input for the agent.")}, required=["input_message"])
                    callable_agent_defs.append(ToolDefinition(type="function", function={
                        "name": sub_agent_name_cfg, "description": sub_agent_desc, "parameters": params.model_dump(exclude_none=True)
                    }))
                else:
                    logger.warning(f"Callable agent '{sub_agent_name_cfg}' for agent '{agent_name}' not found.")


            instance_id = f"{agent_name}_ctx{id(self._runtime_context)}"
            AgentClassToInstantiate: Type[BaseAgent] = agent_config_from_app["agent_class_ref"]
            
            # Prepare constructor arguments, excluding those managed internally by engine/app
            constructor_args_from_config = {
                k: v for k, v in agent_config_from_app.items() 
                if k not in [
                    "llm_instance_override", "memory_override", "native_tool_names", 
                    "callable_agent_names", "agent_class_ref", 
                    # "mcp_tools_from_servers_config" is handled by LLMAgent itself using the engine
                ]
            }
            
            # Ensure LLMAgent gets an LLM
            if issubclass(AgentClassToInstantiate, LLMAgent) and not agent_llm:
                raise ValueError(f"Agent '{agent_name}' (type: LLMAgent) requires an LLM, but none resolved.")

            agent_init_kwargs = {
                "agent_id": instance_id,
                "llm": agent_llm,
                "tools": resolved_native_tools, # Native TFrameX tools
                "memory": agent_memory,
                "engine": self, # Pass the engine instance
                "callable_agent_definitions": callable_agent_defs,
                 # Pass the agent's specific desire for MCP tools to its constructor
                "mcp_tools_from_servers_config": agent_config_from_app.get("mcp_tools_from_servers_config"),
                **constructor_args_from_config, # Other configs like system_prompt_template, description, strip_think_tags
            }
            
            self._agent_instances[agent_name] = AgentClassToInstantiate(**agent_init_kwargs)
            logger.debug(f"Instantiated agent '{instance_id}' (Type: {AgentClassToInstantiate.__name__}) for context {id(self._runtime_context)}.")
        return self._agent_instances[agent_name]

    async def call_agent(
        self, agent_name: str, input_message: Union[str, Message], **kwargs: Any
    ) -> Message:
        if isinstance(input_message, str): input_msg_obj = Message(role="user", content=input_message)
        elif isinstance(input_message, Message): input_msg_obj = input_message
        else: raise TypeError(f"input_message must be str or Message, not {type(input_message)}")
        agent_instance = self._get_agent_instance(agent_name)
        return await agent_instance.run(input_msg_obj, **kwargs)
    
    def call_agent_stream(
        self, agent_name: str, input_message: Union[str, Message], **kwargs: Any
    ) -> AsyncGenerator[MessageChunk, None]:
        """Stream response from an agent. Yields MessageChunk objects as they arrive."""
        return self._call_agent_stream_impl(agent_name, input_message, **kwargs)
    
    async def _call_agent_stream_impl(
        self, agent_name: str, input_message: Union[str, Message], **kwargs: Any
    ) -> AsyncGenerator[MessageChunk, None]:
        """Implementation of streaming agent call."""
        if isinstance(input_message, str): input_msg_obj = Message(role="user", content=input_message)
        elif isinstance(input_message, Message): input_msg_obj = input_message
        else: raise TypeError(f"input_message must be str or Message, not {type(input_message)}")
        agent_instance = self._get_agent_instance(agent_name)
        
        # Call agent with streaming enabled - this returns an async generator
        stream_generator = await agent_instance.run(input_msg_obj, stream=True, **kwargs)
        async for chunk in stream_generator:
            yield chunk

    async def execute_tool_by_llm_definition(
        self,
        tool_definition_name: str, 
        arguments_json_str: str
    ) -> Any: # Returns str for LLM or error dict
        logger.info(f"Engine executing by LLM def name: '{tool_definition_name}' with args: {arguments_json_str[:100]}...")
        
        # 1. Handle TFrameX MCP Meta-tools (registered as native tools)
        # These are tools like 'tframex_list_mcp_resources'
        if tool_definition_name.startswith("tframex_"):
            native_tool = self._app.get_tool(tool_definition_name)
            if native_tool:
                logger.debug(f"Executing TFrameX MCP meta-tool: {tool_definition_name}")
                try:
                    parsed_args = json.loads(arguments_json_str)
                    # Meta tools are defined as async def func(rt_ctx: TFrameXRuntimeContext, ...other_args)
                    # The Tool class doesn't auto-inject rt_ctx from engine.
                    # We need to call the underlying function with rt_ctx.
                    if asyncio.iscoroutinefunction(native_tool.func):
                        # Check if 'rt_ctx' is an expected parameter
                        sig = inspect.signature(native_tool.func)
                        if 'rt_ctx' in sig.parameters:
                            return await native_tool.func(rt_ctx=self._runtime_context, **parsed_args)
                        else: # Should not happen for well-defined meta-tools
                            return await native_tool.func(**parsed_args)
                    else: # Should be async
                        return await asyncio.to_thread(native_tool.func, rt_ctx=self._runtime_context, **parsed_args)
                except Exception as e:
                    logger.error(f"Error executing meta-tool '{tool_definition_name}': {e}", exc_info=True)
                    return {"error": f"Error in meta-tool '{tool_definition_name}': {str(e)}"}
            # If not found as native, it might be an error or fall through if a server is named 'tframex_'

        # 2. Handle MCP tools (prefixed with server_alias__)
        if "__" in tool_definition_name and self._runtime_context.mcp_manager:
            mcp_manager = self._runtime_context.mcp_manager
            logger.debug(f"Attempting to execute as MCP tool: {tool_definition_name}")
            try:
                mcp_call_tool_result = await mcp_manager.call_mcp_tool_by_prefixed_name(
                    tool_definition_name, json.loads(arguments_json_str)
                )
                # Convert MCP CallToolResult to string or error dict for LLMAgent
                if hasattr(mcp_call_tool_result, 'isError') and mcp_call_tool_result.isError:
                    error_content = "Unknown MCP tool error"
                    if mcp_call_tool_result.content and isinstance(mcp_call_tool_result.content[0], TextContent) and mcp_call_tool_result.content[0].text:
                        error_content = mcp_call_tool_result.content[0].text
                    return {"error": f"MCP Tool '{tool_definition_name}' error: {error_content}"}
                elif mcp_call_tool_result.content and isinstance(mcp_call_tool_result.content[0], TextContent) and mcp_call_tool_result.content[0].text is not None:
                    return mcp_call_tool_result.content[0].text
                elif mcp_call_tool_result.content and isinstance(mcp_call_tool_result.content[0], ImageContent):
                    return f"[Image from MCP tool '{tool_definition_name}', mime: {mcp_call_tool_result.content[0].mimeType}]" 
                elif mcp_call_tool_result.content and isinstance(mcp_call_tool_result.content[0], EmbeddedResource):
                    res = mcp_call_tool_result.content[0].resource
                    return f"[Resource from MCP tool '{tool_definition_name}', uri: {res.uri}, mime: {res.mimeType}]"
                else:
                    return f"MCP Tool '{tool_definition_name}' executed, but result format not directly parsable to text for LLM."
            except Exception as e:
                logger.error(f"Error dispatching/executing MCP tool '{tool_definition_name}': {e}", exc_info=True)
                return {"error": f"Client-side error executing MCP tool '{tool_definition_name}': {str(e)}"}
        
        # 3. Handle native TFrameX tools (not meta, not MCP prefixed)
        native_tool = self._app.get_tool(tool_definition_name)
        if native_tool: # Check if it's a non-MCP-meta native tool
            logger.debug(f"Executing native TFrameX tool: {tool_definition_name}")
            return await native_tool.execute(arguments_json_str) # Tool.execute expects JSON string

        logger.error(f"Engine: Tool/Function '{tool_definition_name}' not found or MCP manager unavailable for MCP tools.")
        return {"error": f"Tool or function '{tool_definition_name}' could not be resolved or executed."}