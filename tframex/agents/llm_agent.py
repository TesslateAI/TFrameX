# tframex/agents/llm_agent.py
import json
import logging
from typing import TYPE_CHECKING, Any, AsyncGenerator, Dict, List, Optional, Union

from tframex.models.primitives import Message, MessageChunk, ToolCall, ToolDefinition
from tframex.util.llms import BaseLLMWrapper
from tframex.util.memory import BaseMemoryStore
from tframex.util.tools import Tool # Assuming ToolDefinition doesn't need FunctionCall directly here

from .base import BaseAgent

if TYPE_CHECKING:
    from tframex.util.engine import Engine

logger = logging.getLogger("tframex.agents.llm_agent")

class LLMAgent(BaseAgent):
    def __init__(
        self,
        agent_id: str,
        llm: BaseLLMWrapper,
        engine: "Engine",
        description: Optional[str] = None,
        tools: Optional[List[Tool]] = None, # Native TFrameX tools for this agent
        memory: Optional[BaseMemoryStore] = None,
        system_prompt_template: Optional[str] = "You are a helpful assistant.",
        callable_agent_definitions: Optional[List[ToolDefinition]] = None,
        strip_think_tags: bool = False,
        max_tool_iterations: int = 5,
        mcp_tools_from_servers_config: Optional[Union[List[str], str]] = None,
        **config: Any, # Catches other configurations, including those intended for BaseAgent
    ):
        """
        Initializes an LLMAgent.

        Args:
            agent_id: Unique identifier for the agent instance.
            llm: The LLM wrapper instance this agent will use.
            engine: The TFrameX Engine instance for utility functions like tool execution.
            description: An optional description of the agent's purpose.
            tools: A list of native TFrameX Tool objects available to this agent.
            memory: An optional memory store instance for conversation history.
            system_prompt_template: The template for the system prompt.
            callable_agent_definitions: Tool definitions for other agents this agent can call.
            strip_think_tags: Whether to remove <think>...</think> tags from the final LLM response.
            max_tool_iterations: Maximum number of tool execution loops before forcing a final response.
            mcp_tools_from_servers_config: Configuration for which MCP server tools this agent can use
                                           ('ALL' or a list of server aliases).
            **config: Additional configuration parameters passed to the BaseAgent.
        """

        # Prepare arguments for the BaseAgent constructor.
        # `config` collects any arguments passed to LLMAgent's __init__ that are not explicitly named,
        # plus any additional key-value pairs from the agent's registration in TFrameXApp.
        # BaseAgent's __init__ expects specific named arguments like 'description', 'system_prompt_template', etc.
        # If these are in `config`, Python's **kwargs will map them. If they are also LLMAgent's
        # named parameters, those values will be used when constructing `base_agent_super_kwargs`.

        base_agent_super_kwargs = config.copy() # Start with other configs
        # Ensure explicit parameters for BaseAgent are correctly passed or overridden
        base_agent_super_kwargs['description'] = description
        base_agent_super_kwargs['system_prompt_template'] = system_prompt_template
        base_agent_super_kwargs['strip_think_tags'] = strip_think_tags
        # Note: 'llm', 'tools', 'memory', 'callable_agent_definitions' are passed as named args to super()

        super().__init__(
            agent_id=agent_id,
            llm=llm, # LLM for this agent, also passed to BaseAgent
            tools=tools, # Native TFrameX tools, resolved by Engine and passed directly
            memory=memory, # Resolved by Engine and passed directly
            callable_agent_definitions=callable_agent_definitions, # Resolved by Engine
            **base_agent_super_kwargs # Passes description, system_prompt_template, etc., to BaseAgent
        )

        # LLMAgent specific checks and assignments
        if not self.llm: # self.llm is set by BaseAgent from the 'llm' param passed to super()
            raise ValueError(f"LLMAgent '{self.agent_id}' requires an LLM instance.")
        if not engine: # This 'engine' is the one passed to LLMAgent's __init__
            raise ValueError(f"LLMAgent '{self.agent_id}' requires an Engine instance.")

        self.engine = engine
        # Use the direct parameter values for these LLMAgent-specific configurations
        self.max_tool_iterations = max_tool_iterations
        self.mcp_tools_from_servers_config = mcp_tools_from_servers_config


    def _get_all_available_tool_definitions_for_llm(self) -> List[ToolDefinition]:
        """
        Aggregates all tool definitions available to this agent for the LLM.
        This includes native tools, callable agents, and MCP tools.
        """
        all_defs: List[ToolDefinition] = []

        # 1. Native TFrameX tools assigned to this agent (from self.tools, set by BaseAgent)
        if self.tools:
            for tool_obj in self.tools.values():
                all_defs.append(tool_obj.get_openai_tool_definition())

        # 2. Callable sub-agents (from self.callable_agent_definitions, set by BaseAgent)
        if self.callable_agent_definitions:
            all_defs.extend(self.callable_agent_definitions)

        # 3. MCP tools from specified servers (via MCPManager in the engine's runtime context)
        mcp_manager = self.engine._runtime_context.mcp_manager
        if mcp_manager:
            logger.debug(f"Agent '{self.agent_id}': MCP Manager present: True. "
                         f"Configured servers: {list(mcp_manager.servers.keys())}")
            mcp_server_tools: List[ToolDefinition] = []

            if self.mcp_tools_from_servers_config == "ALL":
                mcp_server_tools = mcp_manager.get_all_mcp_tools_for_llm()
                if mcp_server_tools:
                    logger.debug(f"Agent '{self.agent_id}': Processing tools from ALL MCP servers "
                                 f"via mcp_manager.get_all_mcp_tools_for_llm(). Tool count: {len(mcp_server_tools)}")

            elif isinstance(self.mcp_tools_from_servers_config, list):
                for server_alias in self.mcp_tools_from_servers_config:
                    server = mcp_manager.get_server(server_alias)
                    if server and server.is_initialized and server.tools:
                        logger.debug(f"Agent '{self.agent_id}': Processing tools from INITIALIZED MCP server "
                                     f"'{server_alias}'. Tool count: {len(server.tools)}")
                        for mcp_tool_info in server.tools: # mcp_tool_info is ActualMCPTool
                            parameters = mcp_tool_info.inputSchema if mcp_tool_info.inputSchema else {"type": "object", "properties": {}}
                            prefixed_name = f"{server_alias}__{mcp_tool_info.name}"
                            mcp_server_tools.append(ToolDefinition(type="function", function={
                                "name": prefixed_name,
                                "description": mcp_tool_info.description or f"Tool '{mcp_tool_info.name}' from MCP server '{server_alias}'.",
                                "parameters": parameters
                            }))
                            logger.debug(f"Agent '{self.agent_id}': Added MCP tool '{prefixed_name}' from server '{server_alias}'")
                    elif server:
                         logger.debug(f"Agent '{self.agent_id}': MCP Server '{server_alias}' found but not suitable for tool extraction. "
                                      f"Initialized: {server.is_initialized}, Tools defined: {bool(server.tools)}")
                    else: # server is None
                        logger.debug(f"Agent '{self.agent_id}': MCP server alias '{server_alias}' not found in manager's active server list.")
            all_defs.extend(mcp_server_tools)

        # 4. TFrameX MCP Meta-tools: If configured in @app.agent(tools=[...]), they are included in step 1.

        # Ensure uniqueness of tool definitions by name
        final_defs_dict: Dict[str, ToolDefinition] = {td.function["name"]: td for td in all_defs}
        unique_defs = list(final_defs_dict.values())

        logger.debug(f"Agent '{self.agent_id}' resolved {len(unique_defs)} unique tool definitions for LLM: "
                     f"{[d.function['name'] for d in unique_defs]}")
        return unique_defs


    async def run(self, input_message: Union[str, Message], stream: bool = False, **kwargs: Any) -> Union[Message, AsyncGenerator[MessageChunk, None]]:
        """
        Main execution logic for the LLMAgent.
        Handles interaction with the LLM, tool execution, and memory management.
        
        Args:
            input_message: User input as string or Message object
            stream: If True, returns AsyncGenerator[MessageChunk, None] for streaming responses
            **kwargs: Additional parameters passed to LLM
            
        Returns:
            Message for non-streaming, AsyncGenerator[MessageChunk, None] for streaming
        """
        if isinstance(input_message, str):
            current_user_message = Message(role="user", content=input_message)
        elif isinstance(input_message, Message):
            current_user_message = input_message
        else:
            logger.error(f"LLMAgent '{self.agent_id}' received invalid input_message type: {type(input_message)}. "
                         "Expected str or Message.")
            return Message(role="assistant", content="Error: Invalid input type provided to agent.")

        await self.memory.add_message(current_user_message)
        template_vars_for_prompt = kwargs.get("template_vars", {})

        if stream:
            return self._run_streaming(current_user_message, template_vars_for_prompt, **kwargs)
        
        for iteration_count in range(self.max_tool_iterations + 1):
            history = await self.memory.get_history(limit=self.config.get("history_limit", 10))
            messages_for_llm: List[Message] = []

            system_message_rendered = self._render_system_prompt(**template_vars_for_prompt) # From BaseAgent
            if system_message_rendered:
                messages_for_llm.append(system_message_rendered)
            messages_for_llm.extend(history)

            llm_call_kwargs_from_run = {k: v for k, v in kwargs.items() if k not in ["template_vars", "stream"]}
            all_tool_definitions_for_llm = self._get_all_available_tool_definitions_for_llm()

            llm_api_params: Dict[str, Any] = {"stream": stream, **llm_call_kwargs_from_run}
            if all_tool_definitions_for_llm:
                llm_api_params["tools"] = [td.model_dump(exclude_none=True) for td in all_tool_definitions_for_llm]
                llm_api_params["tool_choice"] = self.config.get("tool_choice", "auto")

            logger.info(
                f"Agent '{self.agent_id}' (LLM: {self.llm.model_id}) calling LLM. "
                f"Iteration: {iteration_count+1}/{self.max_tool_iterations + 1}. "
                f"Tool definitions for LLM: {len(all_tool_definitions_for_llm)}."
            )
            # For very detailed debugging, one might enable these:
            # logger.debug(f"Messages for LLM call: {[msg.model_dump(exclude_none=True) for msg in messages_for_llm]}")
            # logger.debug(f"LLM API parameters (excluding messages): {llm_api_params}")

            assistant_response_message = await self.llm.chat_completion(
                messages_for_llm, **llm_api_params
            )
            await self.memory.add_message(assistant_response_message)

            if not assistant_response_message.tool_calls or iteration_count >= self.max_tool_iterations:
                if iteration_count >= self.max_tool_iterations and assistant_response_message.tool_calls:
                    logger.warning(f"Agent '{self.agent_id}' reached max_tool_iterations ({self.max_tool_iterations}) "
                                   "but LLM still requested tool calls. Ignoring further tool calls.")
                logger.info(f"Agent '{self.agent_id}' concluding processing. Iteration: {iteration_count+1}.")
                return self._post_process_llm_response(assistant_response_message) # From BaseAgent

            logger.info(f"Agent '{self.agent_id}': LLM requested {len(assistant_response_message.tool_calls)} tool_calls.")

            tool_response_messages: List[Message] = []
            for tool_call_obj in assistant_response_message.tool_calls: # tool_call_obj is models.primitives.ToolCall
                tool_name_for_llm = tool_call_obj.function.name
                tool_call_id = tool_call_obj.id
                tool_args_json_str = tool_call_obj.function.arguments

                logger.info(f"Agent '{self.agent_id}': Dispatching tool call for '{tool_name_for_llm}' (ID: {tool_call_id}) via Engine.")
                logger.debug(f"Agent '{self.agent_id}': Tool arguments for '{tool_name_for_llm}': {tool_args_json_str}")

                tool_result_content_or_error_dict = await self.engine.execute_tool_by_llm_definition(
                    tool_name_for_llm, tool_args_json_str
                )

                tool_result_content_str = ""
                if isinstance(tool_result_content_or_error_dict, dict) and "error" in tool_result_content_or_error_dict:
                    tool_result_content_str = str(tool_result_content_or_error_dict["error"]) # Ensure it's a string
                    logger.warning(f"Agent '{self.agent_id}': Tool '{tool_name_for_llm}' execution by engine resulted in error: {tool_result_content_str}")
                elif isinstance(tool_result_content_or_error_dict, (str, int, float, bool)):
                    tool_result_content_str = str(tool_result_content_or_error_dict)
                elif tool_result_content_or_error_dict is None:
                     tool_result_content_str = "[Tool executed successfully but returned no specific content]"
                else: # Attempt to serialize other types
                    try:
                        tool_result_content_str = json.dumps(tool_result_content_or_error_dict)
                    except TypeError:
                        tool_result_content_str = (f"[Tool '{tool_name_for_llm}' returned complex non-JSON-serializable data "
                                                   f"of type: {type(tool_result_content_or_error_dict)}]")
                        logger.warning(f"Agent '{self.agent_id}': {tool_result_content_str}")


                logger.debug(f"Agent '{self.agent_id}': Received result for tool '{tool_name_for_llm}' (ID: {tool_call_id}): "
                             f"'{tool_result_content_str[:200]}{'...' if len(tool_result_content_str) > 200 else ''}'")
                tool_response_messages.append(
                    Message(
                        role="tool",
                        tool_call_id=tool_call_id,
                        name=tool_name_for_llm,
                        content=tool_result_content_str,
                    )
                )

            for tr_msg in tool_response_messages:
                await self.memory.add_message(tr_msg)

        # This part is reached if loop completes due to max_tool_iterations without a break
        logger.error(f"Agent '{self.agent_id}' exceeded maximum tool iterations ({self.max_tool_iterations}). "
                     "Returning last assistant message or error.")
        # The last assistant_response_message might still contain tool_calls.
        # We should ideally return a message indicating the iteration limit was hit.
        error_msg_content = (f"Error: Agent '{self.agent_id}' exceeded maximum tool processing iterations "
                             f"({self.max_tool_iterations}). The last planned action involved tools: "
                             f"{[tc.function.name for tc in assistant_response_message.tool_calls if tc.function]}"
                             if assistant_response_message.tool_calls else
                             f"Error: Agent '{self.agent_id}' exceeded maximum tool processing iterations.")

        final_error_message = Message(role="assistant", content=error_msg_content)
        return self._post_process_llm_response(final_error_message)
    
    async def _run_streaming(self, current_user_message: Message, template_vars_for_prompt: Dict[str, Any], **kwargs: Any) -> AsyncGenerator[MessageChunk, None]:
        """
        Streaming version of the main execution logic.
        Yields MessageChunk objects as they arrive while handling tool calls.
        """
        # Main streaming execution loop
        for iteration_count in range(self.max_tool_iterations + 1):
            history = await self.memory.get_history(limit=self.config.get("history_limit", 10))
            messages_for_llm: List[Message] = []

            system_message_rendered = self._render_system_prompt(**template_vars_for_prompt)
            if system_message_rendered:
                messages_for_llm.append(system_message_rendered)
            messages_for_llm.extend(history)

            llm_call_kwargs_from_run = {k: v for k, v in kwargs.items() if k not in ["template_vars", "stream"]}
            all_tool_definitions_for_llm = self._get_all_available_tool_definitions_for_llm()
            
            llm_api_params: Dict[str, Any] = {"stream": True, **llm_call_kwargs_from_run}
            if all_tool_definitions_for_llm:
                llm_api_params["tools"] = [td.model_dump(exclude_none=True) for td in all_tool_definitions_for_llm]
                llm_api_params["tool_choice"] = self.config.get("tool_choice", "auto")

            logger.info(
                f"Agent '{self.agent_id}' (LLM: {self.llm.model_id}) calling LLM [STREAMING]. "
                f"Iteration: {iteration_count+1}/{self.max_tool_iterations + 1}. "
                f"Tool definitions for LLM: {len(all_tool_definitions_for_llm)}."
            )

            # Get streaming response from LLM
            stream_generator = await self.llm.chat_completion(messages_for_llm, **llm_api_params)
            
            # Accumulate streaming chunks into complete message for tool processing
            accumulated_content = ""
            accumulated_tool_calls = []
            current_role = "assistant"
            
            async for chunk in stream_generator:
                # Yield chunk to caller immediately for real-time streaming
                yield chunk
                
                # Accumulate for internal processing and memory
                if chunk.content:
                    accumulated_content += chunk.content
                if chunk.role:
                    current_role = chunk.role
                if chunk.tool_calls:
                    accumulated_tool_calls.extend(chunk.tool_calls)
            
            # Create complete message from accumulated chunks
            complete_assistant_message = Message(
                role=current_role,
                content=accumulated_content if accumulated_content else None,
                tool_calls=accumulated_tool_calls if accumulated_tool_calls else None
            )
                
            # Add complete message to memory
            await self.memory.add_message(complete_assistant_message)

            # Check if we're done (no tool calls or max iterations reached)
            if not complete_assistant_message.tool_calls or iteration_count >= self.max_tool_iterations:
                if iteration_count >= self.max_tool_iterations and complete_assistant_message.tool_calls:
                    logger.warning(f"Agent '{self.agent_id}' reached max_tool_iterations ({self.max_tool_iterations}) "
                                   "but LLM still requested tool calls. Ignoring further tool calls.")
                logger.info(f"Agent '{self.agent_id}' concluding streaming processing. Iteration: {iteration_count+1}.")
                return

            # Execute tool calls
            logger.info(f"Agent '{self.agent_id}': LLM requested {len(complete_assistant_message.tool_calls)} tool_calls in streaming mode.")
            
            tool_response_messages: List[Message] = []
            for tool_call_obj in complete_assistant_message.tool_calls:
                tool_name_for_llm = tool_call_obj.function.name
                tool_call_id = tool_call_obj.id
                tool_args_json_str = tool_call_obj.function.arguments

                logger.info(f"Agent '{self.agent_id}': Dispatching tool call for '{tool_name_for_llm}' (ID: {tool_call_id}) via Engine.")
                
                tool_result_content_or_error_dict = await self.engine.execute_tool_by_llm_definition(
                    tool_name_for_llm, tool_args_json_str
                )

                tool_result_content_str = ""
                if isinstance(tool_result_content_or_error_dict, dict) and "error" in tool_result_content_or_error_dict:
                    tool_result_content_str = str(tool_result_content_or_error_dict["error"])
                    logger.warning(f"Agent '{self.agent_id}': Tool '{tool_name_for_llm}' execution resulted in error: {tool_result_content_str}")
                elif isinstance(tool_result_content_or_error_dict, (str, int, float, bool)):
                    tool_result_content_str = str(tool_result_content_or_error_dict)
                elif tool_result_content_or_error_dict is None:
                    tool_result_content_str = "[Tool executed successfully but returned no specific content]"
                else:
                    try:
                        tool_result_content_str = json.dumps(tool_result_content_or_error_dict)
                    except TypeError:
                        tool_result_content_str = (f"[Tool '{tool_name_for_llm}' returned complex non-JSON-serializable data "
                                                   f"of type: {type(tool_result_content_or_error_dict)}]")
                        logger.warning(f"Agent '{self.agent_id}': {tool_result_content_str}")

                tool_response_messages.append(
                    Message(
                        role="tool",
                        tool_call_id=tool_call_id,
                        name=tool_name_for_llm,
                        content=tool_result_content_str,
                    )
                )

            # Add tool responses to memory
            for tr_msg in tool_response_messages:
                await self.memory.add_message(tr_msg)
        
        # If we reach here, we've exceeded max iterations
        error_content = f"Error: Agent '{self.agent_id}' exceeded maximum tool processing iterations ({self.max_tool_iterations}) in streaming mode."
        error_chunk = MessageChunk(role="assistant", content=error_content)
        yield error_chunk