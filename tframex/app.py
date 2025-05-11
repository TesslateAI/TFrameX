import asyncio
import inspect
import logging
import os # Already present, used in __init__
from typing import Any, Callable, Coroutine, Dict, List, Optional, Union, Type

from .llms import BaseLLMWrapper
from .tools import Tool, ToolParameters, ToolParameterProperty, ToolDefinition # ToolDefinition already present
from .memory import BaseMemoryStore, InMemoryMemoryStore
from .primitives import Message, MessageChunk # MessageChunk already present
from .agents.llm_agent import LLMAgent
from .agents.base import BaseAgent
from .agents.tool_agent import ToolAgent
from .flows import Flow
from .patterns import BasePattern
from .flow_context import FlowContext


logger = logging.getLogger("tframex.app")

class TFrameXApp:
    def __init__(self, default_llm: Optional[BaseLLMWrapper] = None,
                 default_memory_store_factory: Callable[[], BaseMemoryStore] = InMemoryMemoryStore):

        self._tools: Dict[str, Tool] = {}
        self._agents: Dict[str, Dict[str, Any]] = {} # Stores registration info: ref, config
        self._flows: Dict[str, Flow] = {}

        self.default_llm = default_llm
        self.default_memory_store_factory = default_memory_store_factory

        if not default_llm and not os.getenv("TFRAMEX_ALLOW_NO_DEFAULT_LLM"):
            logger.warning("TFrameXApp initialized without a default LLM. LLM must be provided to run_context or agent if they don't have an override.")

    def tool(self, name: Optional[str] = None, description: Optional[str] = None,
             parameters_schema: Optional[Dict[str, Dict[str, Any]]] = None) -> Callable:
        def decorator(func: Callable[..., Any]) -> Callable:
            tool_name = name or func.__name__
            if tool_name in self._tools:
                raise ValueError(f"Tool '{tool_name}' already registered.")

            parsed_params_schema = None
            if parameters_schema:
                props = {
                    p_name: ToolParameterProperty(**p_def)
                    for p_name, p_def in parameters_schema.get("properties", {}).items()
                }
                parsed_params_schema = ToolParameters(
                    properties=props,
                    required=parameters_schema.get("required")
                )

            self._tools[tool_name] = Tool(
                name=tool_name,
                func=func,
                description=description,
                parameters_schema=parsed_params_schema
            )
            logger.debug(f"Registered tool: '{tool_name}'")
            return func
        return decorator

    def agent(self, name: Optional[str] = None,
              description: Optional[str] = None,
              callable_agents: Optional[List[str]] = None,
              system_prompt: Optional[str] = None,
              tools: Optional[List[str]] = None,
              llm: Optional[BaseLLMWrapper] = None, # This is the agent-specific LLM override
              memory_store: Optional[BaseMemoryStore] = None,
              agent_class: type[BaseAgent] = LLMAgent,
              strip_think_tags: bool = False, # NEW: Agent-specific setting
              **agent_config: Any
              ) -> Callable:
        def decorator(target: Union[Callable, type]) -> Union[Callable, type]:
            agent_name = name or getattr(target, '__name__', str(target))
            if agent_name in self._agents:
                raise ValueError(f"Agent '{agent_name}' already registered.")

            final_config = {
                "description": description,
                "callable_agent_names": callable_agents or [],
                "system_prompt_template": system_prompt,
                "tool_names": tools or [],
                "llm_instance_override": llm, # CHANGED key from llm_override
                "memory_override": memory_store,
                "agent_class_ref": agent_class,
                "strip_think_tags": strip_think_tags, # NEW: Storing the setting
                **agent_config
            }

            is_class_based_agent = inspect.isclass(target) and issubclass(target, BaseAgent)
            agent_class_to_log = target.__name__ if is_class_based_agent else agent_class.__name__

            self._agents[agent_name] = {
                "type": "custom_class_agent" if is_class_based_agent else "framework_managed_agent",
                "ref": target,
                "config": final_config
            }
            logger.debug(
                f"Registered agent: '{agent_name}' (Description: '{description}', "
                f"Class: {agent_class_to_log}, "
                f"LLM Override: {llm.model_id if llm else 'None'}, "
                f"Callable Agents: {callable_agents or []}, "
                f"Strip Think Tags: {strip_think_tags})"
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

    def run_context(self, llm_override: Optional[BaseLLMWrapper] = None,
                    context_memory_override: Optional[BaseMemoryStore] = None
                    ) -> "TFrameXRuntimeContext":
        ctx_llm = llm_override or self.default_llm
        ctx_memory = context_memory_override
        return TFrameXRuntimeContext(self, llm=ctx_llm, context_memory=ctx_memory)


class TFrameXRuntimeContext:
    def __init__(self, app: TFrameXApp, llm: Optional[BaseLLMWrapper],
                 context_memory: Optional[BaseMemoryStore] = None):
        self._app = app
        self.llm = llm # Context-level LLM
        self.context_memory = context_memory
        self._agent_instances: Dict[str, BaseAgent] = {}

    async def __aenter__(self) -> "TFrameXRuntimeContext":
        llm_id = self.llm.model_id if self.llm else "None"
        ctx_mem_type = type(self.context_memory).__name__ if self.context_memory else "None"
        logger.info(f"TFrameXRuntimeContext entered. LLM: {llm_id}. Context Memory: {ctx_mem_type}")
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        # Close own LLM if it has a close method (some LLM wrappers might need this)
        if self.llm and hasattr(self.llm, 'close') and inspect.iscoroutinefunction(self.llm.close):
            await self.llm.close()
            logger.info(f"TFrameXRuntimeContext exited. Context LLM client closed for {self.llm.model_id}.")
        elif self.llm:
            logger.info(f"TFrameXRuntimeContext exited. Context LLM {self.llm.model_id} did not require async close.")
        else:
            logger.info("TFrameXRuntimeContext exited. No context LLM client to close.")
        # Note: Agent-specific LLMs are not closed here; they are managed by the agent or assumed to share lifetime with context/app LLM.
        # If agent LLMs need explicit closing, agent's __del__ or a specific cleanup phase would handle it.

    def _get_agent_instance(self, agent_name: str) -> BaseAgent:
        if agent_name not in self._agent_instances:
            if agent_name not in self._app._agents:
                raise ValueError(f"Agent '{agent_name}' not registered with the TFrameXApp.")

            reg_info = self._app._agents[agent_name]
            agent_config_from_registration = reg_info["config"]

            # Resolve LLM: Agent-specific > Context > App-default
            agent_llm = agent_config_from_registration.get("llm_instance_override") or \
                        self.llm or \
                        self._app.default_llm
            
            agent_memory = agent_config_from_registration.get("memory_override") or \
                           self._app.default_memory_store_factory()

            agent_tools_resolved: List[Tool] = []
            if agent_config_from_registration.get("tool_names"):
                for tool_name_ref in agent_config_from_registration["tool_names"]:
                    tool_obj = self._app.get_tool(tool_name_ref)
                    if tool_obj:
                        agent_tools_resolved.append(tool_obj)
                    else:
                        logger.warning(f"Tool '{tool_name_ref}' for agent '{agent_name}' not found.")

            agent_description = agent_config_from_registration.get("description")
            strip_think_tags_for_agent = agent_config_from_registration.get("strip_think_tags", False) # NEW

            callable_agent_definitions: List[ToolDefinition] = []
            callable_agent_names = agent_config_from_registration.get("callable_agent_names", [])
            for sub_agent_name_to_call in callable_agent_names:
                if sub_agent_name_to_call not in self._app._agents:
                    logger.warning(f"Agent '{agent_name}' configured to call non-existent agent '{sub_agent_name_to_call}'. Skipping.")
                    continue
                sub_agent_reg_info = self._app._agents[sub_agent_name_to_call]
                sub_agent_description = sub_agent_reg_info["config"].get("description") or \
                                        f"This agent, '{sub_agent_name_to_call}', performs its designated role. Provide a specific input_message for it."
                agent_tool_params = ToolParameters(
                    properties={
                        "input_message": ToolParameterProperty(
                            type="string",
                            description=f"The specific query, task, or input content to pass to the '{sub_agent_name_to_call}' agent."
                        ),
                    },
                    required=["input_message"]
                )
                callable_agent_definitions.append(
                    ToolDefinition(
                        type="function",
                        function={
                            "name": sub_agent_name_to_call,
                            "description": sub_agent_description,
                            "parameters": agent_tool_params.model_dump(exclude_none=True)
                        }
                    )
                )

            instance_id = f"{agent_name}_ctx{id(self)}"
            AgentClassToInstantiate: Type[BaseAgent] = agent_config_from_registration["agent_class_ref"]

            # Keys handled explicitly when preparing agent_init_kwargs or are internal to registration
            internal_config_keys = {
                "llm_instance_override", "memory_override", "tool_names",
                "system_prompt_template", "agent_class_ref", "description",
                "callable_agent_names", "strip_think_tags" # NEW: Add strip_think_tags here
            }
            additional_constructor_args = {
                k: v for k, v in agent_config_from_registration.items() if k not in internal_config_keys
            }

            if issubclass(AgentClassToInstantiate, LLMAgent) and not agent_llm:
                 raise ValueError(f"Agent '{agent_name}' (type {AgentClassToInstantiate.__name__}) requires an LLM, but none was available.")

            agent_init_kwargs = {
                "agent_id": instance_id,
                "description": agent_description,
                "llm": agent_llm,
                "tools": agent_tools_resolved,
                "memory": agent_memory,
                "system_prompt_template": agent_config_from_registration.get("system_prompt_template"),
                "callable_agent_definitions": callable_agent_definitions,
                "strip_think_tags": strip_think_tags_for_agent, # NEW: Pass to agent constructor
                **additional_constructor_args
            }
            if issubclass(AgentClassToInstantiate, LLMAgent): # Or any agent needing runtime context
                agent_init_kwargs["app_runtime_ref"] = self

            self._agent_instances[agent_name] = AgentClassToInstantiate(**agent_init_kwargs)
            logger.debug(
                f"Instantiated agent '{instance_id}' (Type: {AgentClassToInstantiate.__name__}, "
                f"LLM: {agent_llm.model_id if agent_llm else 'None'}, "
                f"Strip Tags: {strip_think_tags_for_agent})" # NEW: Log strip_think_tags status
            )
        
        return self._agent_instances[agent_name]

    async def call_agent(self, agent_name: str, input_message: Union[str, Message], **kwargs: Any) -> Message:
        if isinstance(input_message, str):
            input_msg_obj = Message(role="user", content=input_message)
        else:
            input_msg_obj = input_message
        agent_instance = self._get_agent_instance(agent_name)
        return await agent_instance.run(input_msg_obj, **kwargs)

    async def call_tool(self, tool_name: str, arguments_json_str: str) -> Any:
        tool = self._app.get_tool(tool_name)
        if not tool:
            logger.error(f"Attempted to call unregistered tool '{tool_name}'.")
            return {"error": f"Tool '{tool_name}' not found in app registry."}
        return await tool.execute(arguments_json_str)

    async def run_flow(self, flow_ref: Union[str, Flow], 
                       initial_input: Message,
                       initial_shared_data: Optional[Dict[str, Any]] = None,
                       flow_template_vars: Optional[Dict[str, Any]] = None
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
        return await flow_to_run.execute(initial_input, self, 
                                         initial_shared_data=initial_shared_data, 
                                         flow_template_vars=flow_template_vars)

    async def interactive_chat(self, default_flow_name: Optional[str] = None) -> None:
        print("\n--- TFrameX Interactive Flow Chat ---")
        
        flow_to_use: Optional[Flow] = None
        if default_flow_name:
            flow_to_use = self._app.get_flow(default_flow_name)
            if flow_to_use:
                print(f"Default flow: '{default_flow_name}'")
            else:
                print(f"Warning: Default flow '{default_flow_name}' not found.")
        
        if not flow_to_use:
            if not self._app._flows:
                print("No flows registered in the application. Exiting interactive chat.")
                return
            
            print("Available flows:")
            flow_names_list = list(self._app._flows.keys())
            for i, name in enumerate(flow_names_list):
                print(f"  {i+1}. {name}")
            
            while True:
                try:
                    choice_str = await asyncio.to_thread(input, "Select a flow to chat with (number or name, or 'exit'): ")
                    if choice_str.lower() == 'exit': return
                    
                    selected_flow_name: Optional[str] = None
                    if choice_str.isdigit():
                        choice_idx = int(choice_str) - 1
                        if 0 <= choice_idx < len(flow_names_list):
                            selected_flow_name = flow_names_list[choice_idx]
                    else: 
                        if choice_str in self._app._flows:
                            selected_flow_name = choice_str
                    
                    if selected_flow_name:
                        flow_to_use = self._app.get_flow(selected_flow_name)
                        break
                    else:
                        print("Invalid selection. Please try again.")
                except ValueError:
                    print("Invalid input. Please enter a number or flow name.")
                except KeyboardInterrupt:
                    print("\nExiting.")
                    return

        if not flow_to_use: 
            print("No flow selected. Exiting.")
            return

        print(f"\n--- Chatting with Flow: '{flow_to_use.flow_name}' ---")
        print(f"Description: {flow_to_use.description or 'No description'}")
        print("Type 'exit' or 'quit' to end this chat session.")

        while True:
            try:
                user_input_str = await asyncio.to_thread(input, "\nYou: ")
                if user_input_str.lower() in ["exit", "quit"]:
                    break
                if not user_input_str.strip():
                    continue
                
                initial_message = Message(role="user", content=user_input_str)
                
                logger.info(f"CLI: Running flow '{flow_to_use.flow_name}' with input: '{user_input_str}'")
                final_flow_context: FlowContext = await self.run_flow(flow_to_use, initial_message)

                final_output_message = final_flow_context.current_message
                
                print(f"\nFlow Output ({final_output_message.role}):")
                if final_output_message.content:
                    print(f"  Content: {final_output_message.content}")
                
                if final_output_message.tool_calls:
                    print(f"  Final Message Tool Calls (Unprocessed by Flow): {final_output_message.tool_calls}")
                
                if final_flow_context.shared_data:
                    print("  Flow Shared Data (at end of execution):")
                    for key, value in final_flow_context.shared_data.items():
                        value_str = str(value)
                        print(f"    {key}: {value_str[:200]}{'...' if len(value_str) > 200 else ''}")

            except KeyboardInterrupt:
                print("\nExiting chat session.")
                break
            except Exception as e:
                print(f"Error during interactive chat with flow '{flow_to_use.flow_name}': {e}")
                logger.error(f"Error in interactive_chat with flow '{flow_to_use.flow_name}'", exc_info=True)
        
        print(f"--- Ended chat with Flow: '{flow_to_use.flow_name}' ---")