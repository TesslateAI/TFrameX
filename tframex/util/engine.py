import inspect
import logging
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Type, Union

from ..agents.base import BaseAgent
from ..agents.llm_agent import (  # Import LLMAgent directly since we need it for runtime
    LLMAgent,
)
from ..models.primitives import Message
from ..util.tools import Tool, ToolDefinition, ToolParameterProperty, ToolParameters

if TYPE_CHECKING:
    from ..agents.llm_agent import LLMAgent

logger = logging.getLogger("tframex.engine")


class Engine:
    def __init__(self, app, runtime_context):
        self._app = app
        self._runtime_context = runtime_context
        self._agent_instances: Dict[str, BaseAgent] = {}

    def _get_agent_instance(self, agent_name: str) -> BaseAgent:
        """
        Get or create an agent instance for the given agent name.

        Args:
            agent_name: Name of the agent to get/create

        Returns:
            BaseAgent: The agent instance

        Raises:
            ValueError: If the agent is not registered with the app
        """
        if agent_name not in self._agent_instances:
            if agent_name not in self._app._agents:
                raise ValueError(
                    f"Agent '{agent_name}' not registered with the TFrameXApp."
                )

            reg_info = self._app._agents[agent_name]
            agent_config_from_registration = reg_info["config"]

            # Resolve LLM: Agent-specific > Context > App-default
            agent_llm = (
                agent_config_from_registration.get("llm_instance_override")
                or self._runtime_context.llm
                or self._app.default_llm
            )

            agent_memory = (
                agent_config_from_registration.get("memory_override")
                or self._app.default_memory_store_factory()
            )

            agent_tools_resolved: List[Tool] = []
            if agent_config_from_registration.get("tool_names"):
                for tool_name_ref in agent_config_from_registration["tool_names"]:
                    tool_obj = self._app.get_tool(tool_name_ref)
                    if tool_obj:
                        agent_tools_resolved.append(tool_obj)
                    else:
                        logger.warning(
                            f"Tool '{tool_name_ref}' for agent '{agent_name}' not found."
                        )

            agent_description = agent_config_from_registration.get("description")
            strip_think_tags_for_agent = agent_config_from_registration.get(
                "strip_think_tags", False
            )

            callable_agent_definitions: List[ToolDefinition] = []
            callable_agent_names = agent_config_from_registration.get(
                "callable_agent_names", []
            )
            for sub_agent_name_to_call in callable_agent_names:
                if sub_agent_name_to_call not in self._app._agents:
                    logger.warning(
                        f"Agent '{agent_name}' configured to call non-existent agent '{sub_agent_name_to_call}'. Skipping."
                    )
                    continue
                sub_agent_reg_info = self._app._agents[sub_agent_name_to_call]
                sub_agent_description = (
                    sub_agent_reg_info["config"].get("description")
                    or f"This agent, '{sub_agent_name_to_call}', performs its designated role. Provide a specific input_message for it."
                )
                agent_tool_params = ToolParameters(
                    properties={
                        "input_message": ToolParameterProperty(
                            type="string",
                            description=f"The specific query, task, or input content to pass to the '{sub_agent_name_to_call}' agent.",
                        ),
                    },
                    required=["input_message"],
                )
                callable_agent_definitions.append(
                    ToolDefinition(
                        type="function",
                        function={
                            "name": sub_agent_name_to_call,
                            "description": sub_agent_description,
                            "parameters": agent_tool_params.model_dump(
                                exclude_none=True
                            ),
                        },
                    )
                )

            instance_id = f"{agent_name}_ctx{id(self._runtime_context)}"
            AgentClassToInstantiate: Type[BaseAgent] = agent_config_from_registration[
                "agent_class_ref"
            ]

            # Keys handled explicitly when preparing agent_init_kwargs or are internal to registration
            internal_config_keys = {
                "llm_instance_override",
                "memory_override",
                "tool_names",
                "system_prompt_template",
                "agent_class_ref",
                "description",
                "callable_agent_names",
                "strip_think_tags",
            }
            additional_constructor_args = {
                k: v
                for k, v in agent_config_from_registration.items()
                if k not in internal_config_keys
            }

            if issubclass(AgentClassToInstantiate, LLMAgent) and not agent_llm:
                raise ValueError(
                    f"Agent '{agent_name}' (type {AgentClassToInstantiate.__name__}) requires an LLM, but none was available."
                )

            agent_init_kwargs = {
                "agent_id": instance_id,
                "description": agent_description,
                "llm": agent_llm,
                "tools": agent_tools_resolved,
                "memory": agent_memory,
                "system_prompt_template": agent_config_from_registration.get(
                    "system_prompt_template"
                ),
                "callable_agent_definitions": callable_agent_definitions,
                "strip_think_tags": strip_think_tags_for_agent,
                **additional_constructor_args,
            }
            if issubclass(AgentClassToInstantiate, LLMAgent):
                agent_init_kwargs["engine"] = self

            self._agent_instances[agent_name] = AgentClassToInstantiate(
                **agent_init_kwargs
            )
            logger.debug(
                f"Instantiated agent '{instance_id}' (Type: {AgentClassToInstantiate.__name__}, "
                f"LLM: {agent_llm.model_id if agent_llm else 'None'}, "
                f"Strip Tags: {strip_think_tags_for_agent})"
            )

        return self._agent_instances[agent_name]

    async def call_agent(
        self, agent_name: str, input_message: Union[str, Message], **kwargs: Any
    ) -> Message:
        """
        Call an agent with the given input message.

        Args:
            agent_name: Name of the agent to call
            input_message: Input message as string or Message object
            **kwargs: Additional arguments to pass to the agent

        Returns:
            Message: The agent's response message
        """
        if isinstance(input_message, str):
            input_msg_obj = Message(role="user", content=input_message)
        else:
            input_msg_obj = input_message
        agent_instance = self._get_agent_instance(agent_name)
        return await agent_instance.run(input_msg_obj, **kwargs)

    async def call_tool(self, tool_name: str, arguments_json_str: str) -> Any:
        """
        Call a tool with the given arguments.

        Args:
            tool_name: Name of the tool to call
            arguments_json_str: JSON string containing the tool arguments

        Returns:
            Any: The tool's execution result
        """
        tool = self._app.get_tool(tool_name)
        if not tool:
            logger.error(f"Attempted to call unregistered tool '{tool_name}'.")
            return {"error": f"Tool '{tool_name}' not found in app registry."}
        return await tool.execute(arguments_json_str)
