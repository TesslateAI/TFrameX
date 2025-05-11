import logging
import json
from typing import Optional, List, Union, Dict, Any

from .base import BaseAgent
from tframex.llms import BaseLLMWrapper
from tframex.tools import Tool, ToolDefinition
from tframex.memory import BaseMemoryStore
from tframex.primitives import Message, ToolCall, FunctionCall
# Forward declaration for TFrameXRuntimeContext
if False: # TYPE_CHECKING
    from tframex.app import TFrameXRuntimeContext


logger = logging.getLogger(__name__)

class LLMAgent(BaseAgent):
    """
    An agent that uses an LLM to decide actions, potentially using tools, callable sub-agents, and memory.
    """
    def __init__(self,
                 agent_id: str,
                 llm: BaseLLMWrapper, # This is the actual resolved LLM the agent will use
                 app_runtime_ref: 'TFrameXRuntimeContext',
                 description: Optional[str] = None,
                 tools: Optional[List[Tool]] = None,
                 memory: Optional[BaseMemoryStore] = None,
                 system_prompt_template: Optional[str] = "You are a helpful assistant.",
                 callable_agent_definitions: Optional[List[ToolDefinition]] = None,
                 strip_think_tags: bool = False, # NEW: Passed to BaseAgent
                 max_tool_iterations: int = 5,
                 **config: Any):
        super().__init__(
            agent_id,
            description=description,
            llm=llm, # Pass the resolved LLM
            tools=tools,
            memory=memory,
            system_prompt_template=system_prompt_template,
            callable_agent_definitions=callable_agent_definitions,
            strip_think_tags=strip_think_tags, # NEW: Pass to BaseAgent
            **config # Pass other configs from decorator
        )
        self.app_runtime = app_runtime_ref
        self.max_tool_iterations = max_tool_iterations
        if not self.llm: # self.llm is inherited from BaseAgent and set by super()
            raise ValueError(f"LLMAgent '{self.agent_id}' requires an LLM instance.")

    async def run(self, input_message: Union[str, Message], **kwargs: Any) -> Message:
        if isinstance(input_message, str):
            current_user_message = Message(role="user", content=input_message)
        else:
            current_user_message = input_message
        
        await self.memory.add_message(current_user_message)

        template_vars_for_prompt = kwargs.get("template_vars", {})

        for iteration_count in range(self.max_tool_iterations + 1):
            history = await self.memory.get_history(limit=self.config.get("history_limit", 10))
            messages_for_llm: List[Message] = []
            
            system_message = self._render_system_prompt(**template_vars_for_prompt)
            if system_message:
                messages_for_llm.append(system_message)
            
            messages_for_llm.extend(history)

            llm_call_kwargs = {k: v for k, v in kwargs.items() if k != "template_vars"}

            all_tool_definitions_for_llm: List[Dict[str, Any]] = []
            if self.tools:
                all_tool_definitions_for_llm.extend(
                    [tool.get_openai_tool_definition().model_dump() for tool in self.tools.values()]
                )
            
            if self.callable_agent_definitions:
                all_tool_definitions_for_llm.extend(
                    [cad.model_dump() for cad in self.callable_agent_definitions]
                )

            if all_tool_definitions_for_llm:
                llm_call_kwargs["tools"] = all_tool_definitions_for_llm
                llm_call_kwargs["tool_choice"] = self.config.get("tool_choice", "auto")

            logger.debug(
                f"Agent '{self.agent_id}' (LLM: {self.llm.model_id}) calling LLM " # UPDATED LOG
                f"(Iter {iteration_count+1}/{self.max_tool_iterations+1}). "
                f"History depth: {len(history)}. "
                f"Regular Tools defined: {len(self.tools)}. "
                f"Callable Agents as Tools defined: {len(self.callable_agent_definitions)}."
            )
            
            assistant_response_message = await self.llm.chat_completion(
                messages_for_llm, stream=False, **llm_call_kwargs
            )
            await self.memory.add_message(assistant_response_message)

            if not assistant_response_message.tool_calls or iteration_count >= self.max_tool_iterations:
                logger.info(f"Agent '{self.agent_id}' concluding with textual response. Iter: {iteration_count+1}.")
                # NEW: Post-process before returning
                return self._post_process_llm_response(assistant_response_message)

            logger.info(f"Agent '{self.agent_id}' LLM requested tool_calls: {len(assistant_response_message.tool_calls)}")
            
            tool_response_messages: List[Message] = []
            for tool_call in assistant_response_message.tool_calls:
                tool_name = tool_call.function.name
                tool_call_id = tool_call.id
                tool_args_json_str = tool_call.function.arguments
                
                is_sub_agent_call = any(cad.function["name"] == tool_name for cad in self.callable_agent_definitions)

                if tool_name in self.tools:
                    logger.info(f"Agent '{self.agent_id}' executing regular tool '{tool_name}'.")
                    tool_to_execute = self.tools[tool_name]
                    tool_result_content = str(await tool_to_execute.execute(tool_args_json_str))
                elif is_sub_agent_call:
                    logger.info(f"Agent '{self.agent_id}' calling sub-agent '{tool_name}' as a tool.")
                    try:
                        sub_agent_args = json.loads(tool_args_json_str)
                        sub_agent_input_content = sub_agent_args.get("input_message", "")
                        if not sub_agent_input_content and isinstance(sub_agent_args, str):
                            sub_agent_input_content = sub_agent_args
                        elif not sub_agent_input_content and tool_args_json_str:
                            sub_agent_input_content = tool_args_json_str

                        sub_agent_input_msg = Message(role="user", content=str(sub_agent_input_content))
                        sub_agent_call_kwargs = {"template_vars": template_vars_for_prompt}

                        sub_agent_response = await self.app_runtime.call_agent(
                            agent_name=tool_name,
                            input_message=sub_agent_input_msg,
                            **sub_agent_call_kwargs
                        )
                        # Sub-agent's response is already post-processed by its own .run() method if it's an LLMAgent
                        tool_result_content = sub_agent_response.content or "[Sub-agent produced no content]"
                        if sub_agent_response.tool_calls:
                            tc_summary = json.dumps([tc.model_dump(exclude_none=True) for tc in sub_agent_response.tool_calls])
                            tool_result_content += f"\n[Sub-agent '{tool_name}' also made tool calls: {tc_summary}]"
                        logger.debug(f"Agent '{self.agent_id}': Sub-agent '{tool_name}' response: {tool_result_content[:200]}")

                    except json.JSONDecodeError as e:
                        logger.error(f"Agent '{self.agent_id}': Invalid JSON arguments for sub-agent '{tool_name}': {tool_args_json_str}. Error: {e}")
                        tool_result_content = f"Error: Invalid JSON arguments for sub-agent '{tool_name}'."
                    except Exception as e:
                        logger.error(f"Agent '{self.agent_id}': Error calling sub-agent '{tool_name}': {e}", exc_info=True)
                        tool_result_content = f"Error: Failed to execute sub-agent '{tool_name}': {str(e)}"
                else:
                    logger.warning(f"Agent '{self.agent_id}': LLM requested unknown tool/agent '{tool_name}'. Available tools: {list(self.tools.keys())}, Callable agents: {[cad.function['name'] for cad in self.callable_agent_definitions]}")
                    tool_result_content = f"Error: Tool or agent '{tool_name}' is not available to me."
                
                tool_response_messages.append(Message(
                    role="tool", tool_call_id=tool_call_id, name=tool_name, content=tool_result_content
                ))
            
            for tr_msg in tool_response_messages:
                await self.memory.add_message(tr_msg)

        logger.error(f"Agent '{self.agent_id}' exceeded max_tool_iterations ({self.max_tool_iterations}). Returning error message.")
        # NEW: Post-process error message too
        error_message = Message(role="assistant", content=f"Error: Agent {self.agent_id} exceeded maximum tool processing iterations.")
        return self._post_process_llm_response(error_message)