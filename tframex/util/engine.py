# tframex/engine.py

"""
Core execution engine for TFrameX agents and tools within a specific runtime context.

This module defines the `Engine` class, responsible for managing the lifecycle
and execution of agents registered within a TFrameXApp instance. It handles
agent instantiation, configuration resolution (LLM, memory, tools), and
delegates calls to the appropriate agent or tool methods.
"""

import inspect
import logging
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Type, Union

# Import primitives and utilities - generally safe from circular dependencies
from ..models.primitives import Message
from ..util.tools import Tool, ToolDefinition, ToolParameterProperty, ToolParameters

# Use TYPE_CHECKING block for imports needed only for static analysis
# This avoids runtime circular imports.
if TYPE_CHECKING:
    from ..agents.base import BaseAgent
    from ..agents.llm_agent import LLMAgent
    from ..app import TFrameXApp  # Assuming app type for better hinting
    from ..runtime import RuntimeContext # Assuming context type for better hinting


logger = logging.getLogger("tframex.engine")


class Engine:
    """
    Manages agent instantiation and execution within a TFrameX runtime context.

    An Engine instance is typically created per request or session (via RuntimeContext)
    and provides the necessary environment for agents to run, resolving dependencies
    like LLMs, memory stores, and tools based on application defaults, context
    overrides, and agent-specific configurations.
    """

    def __init__(self, app: 'TFrameXApp', runtime_context: 'RuntimeContext'):
        """
        Initializes the Engine.

        Args:
            app: The main TFrameXApp instance containing agent/tool registrations.
            runtime_context: The specific runtime context for this engine instance,
                             potentially holding session-specific state or overrides (e.g., LLM).
        """
        self._app = app
        self._runtime_context = runtime_context
        # Use string literal for type hint to avoid import at class definition time
        # Stores agent instances, keyed by agent name. Instantiated lazily.
        self._agent_instances: Dict[str, 'BaseAgent'] = {}

    def _get_agent_instance(self, agent_name: str) -> 'BaseAgent':
        """
        Retrieves or lazily instantiates an agent based on its registered configuration.

        This method handles the core logic of agent creation:
        1. Checks if an instance for the given `agent_name` already exists for this engine.
        2. If not, retrieves the agent's registration info from the `TFrameXApp`.
        3. Resolves the LLM instance (Agent config > Context > App default).
        4. Resolves the MemoryStore instance (Agent config > App default factory).
        5. Resolves the Tools list based on registered `tool_names`.
        6. Gathers other configuration: description, `strip_think_tags`, callable agents.
        7. Creates ToolDefinitions for any specified `callable_agent_names`.
        8. Determines the correct agent class to instantiate.
        9. Filters registration config to pass only valid constructor arguments.
        10. Validates required dependencies (e.g., LLM for LLMAgents).
        11. Instantiates the agent class with the resolved configuration.
        12. Stores and returns the new agent instance.

        Args:
            agent_name: The registered name of the agent to get or create.

        Returns:
            The agent instance corresponding to the `agent_name`.

        Raises:
            ValueError: If the `agent_name` is not registered in the app.
            ValueError: If an LLMAgent is required but no LLM is available.
        """
        # Import agent classes here, INSIDE the method, only when needed for instantiation
        # This prevents module-level circular dependencies.
        from ..agents.base import BaseAgent
        from ..agents.llm_agent import LLMAgent

        if agent_name not in self._agent_instances:
            # --- Agent Registration Lookup ---
            if agent_name not in self._app._agents:
                raise ValueError(
                    f"Agent '{agent_name}' not registered with the TFrameXApp."
                )
            reg_info = self._app._agents[agent_name]
            agent_config = reg_info["config"] # Use a shorter alias

            # --- Dependency Resolution ---
            # Resolve LLM: Agent-specific config > Context > App default
            agent_llm = (
                agent_config.get("llm_instance_override")
                or self._runtime_context.llm
                or self._app.default_llm
            )

            # Resolve Memory: Agent-specific config > App default factory
            agent_memory = (
                agent_config.get("memory_override")
                or self._app.default_memory_store_factory() # Ensure factory provides a new instance
            )

            # Resolve Tools: Look up tools by name from app registry
            agent_tools_resolved: List[Tool] = []
            tool_names = agent_config.get("tool_names", [])
            if tool_names:
                for tool_name_ref in tool_names:
                    tool_obj = self._app.get_tool(tool_name_ref)
                    if tool_obj:
                        agent_tools_resolved.append(tool_obj)
                    else:
                        logger.warning(
                            f"Tool '{tool_name_ref}' specified for agent '{agent_name}' "
                            f"not found in the app registry. Skipping."
                        )

            # --- Agent Configuration ---
            agent_description = agent_config.get("description")
            strip_think_tags_for_agent = agent_config.get(
                "strip_think_tags", False # Default to False if not specified in config
            )

            # --- Callable Agent Definitions ---
            # Define other agents this agent can call as tools
            callable_agent_definitions: List[ToolDefinition] = []
            callable_agent_names = agent_config.get("callable_agent_names", [])
            for sub_agent_name in callable_agent_names:
                if sub_agent_name not in self._app._agents:
                    logger.warning(
                        f"Agent '{agent_name}' configured to call non-existent agent "
                        f"'{sub_agent_name}'. Skipping definition."
                    )
                    continue

                # Fetch sub-agent info to create a tool-like definition
                sub_agent_reg_info = self._app._agents[sub_agent_name]
                sub_agent_description = (
                    sub_agent_reg_info["config"].get("description")
                    or f"Invoke the '{sub_agent_name}' agent. Provide the specific input message for it."
                )

                # Define standard parameters for calling another agent
                agent_tool_params = ToolParameters(
                    properties={
                        "input_message": ToolParameterProperty(
                            type="string",
                            description=f"The specific query, task, or input content to pass to the '{sub_agent_name}' agent.",
                        ),
                    },
                    required=["input_message"],
                )

                callable_agent_definitions.append(
                    ToolDefinition(
                        type="function",
                        function={
                            "name": sub_agent_name, # The name the primary agent uses to call
                            "description": sub_agent_description,
                            "parameters": agent_tool_params.model_dump(exclude_none=True),
                        },
                    )
                )

            # --- Agent Instantiation ---
            instance_id = f"{agent_name}_ctx{id(self._runtime_context)}"
            AgentClassToInstantiate: Type[BaseAgent] = agent_config["agent_class_ref"]

            # Identify keys used internally for setup vs. those passed to the constructor
            internal_config_keys = {
                "llm_instance_override", "memory_override", "tool_names",
                "system_prompt_template", "agent_class_ref", "description",
                "callable_agent_names", "strip_think_tags"
            }
            additional_constructor_args = {
                k: v
                for k, v in agent_config.items()
                if k not in internal_config_keys
            }

            # Runtime check: LLMAgent requires an LLM
            if issubclass(AgentClassToInstantiate, LLMAgent) and not agent_llm:
                raise ValueError(
                    f"Agent '{agent_name}' (type: {AgentClassToInstantiate.__name__}) "
                    f"requires an LLM, but none could be resolved (check agent config, "
                    f"runtime context, and app defaults)."
                )

            # Prepare arguments for the agent's constructor
            agent_init_kwargs = {
                "agent_id": instance_id,
                "description": agent_description,
                "llm": agent_llm,
                "tools": agent_tools_resolved,
                "memory": agent_memory,
                "system_prompt_template": agent_config.get("system_prompt_template"),
                "callable_agent_definitions": callable_agent_definitions,
                "strip_think_tags": strip_think_tags_for_agent,
                **additional_constructor_args, # Include any other config values
            }

            # Inject engine dependency specifically for LLMAgents (if needed by their impl)
            # Check inheritance dynamically using the imported LLMAgent class
            if issubclass(AgentClassToInstantiate, LLMAgent):
                agent_init_kwargs["engine"] = self # Pass self (the engine)

            # Create the agent instance
            self._agent_instances[agent_name] = AgentClassToInstantiate(**agent_init_kwargs)

            logger.debug(
                f"Instantiated agent '{instance_id}' "
                f"(Name: '{agent_name}', Type: {AgentClassToInstantiate.__name__}, "
                f"LLM: {agent_llm.model_id if agent_llm else 'None'}, "
                f"Memory: {type(agent_memory).__name__}, "
                f"Tools: {[t.name for t in agent_tools_resolved]}, "
                f"Callable Agents: {callable_agent_names}, "
                f"Strip Tags: {strip_think_tags_for_agent})"
            )

        # Return the existing or newly created instance
        return self._agent_instances[agent_name]

    async def call_agent(
        self, agent_name: str, input_message: Union[str, Message], **kwargs: Any
    ) -> Message:
        """
        Executes a registered agent with the given input.

        This method retrieves (or instantiates) the specified agent and calls its
        `run` method.

        Args:
            agent_name: The registered name of the agent to call.
            input_message: The input message for the agent, either as a string
                           (which will be wrapped in a 'user' Message) or a Message object.
            **kwargs: Additional keyword arguments to be passed directly to the
                      agent's `run` method.

        Returns:
            The response Message object from the agent's execution.

        Raises:
            ValueError: If the agent is not registered.
            (Potentially others depending on the agent's `run` method)
        """
        # Ensure input is a Message object
        if isinstance(input_message, str):
            input_msg_obj = Message(role="user", content=input_message)
        elif isinstance(input_message, Message):
            input_msg_obj = input_message
        else:
            # Add type checking for clarity, though Union hint covers it
             raise TypeError(f"input_message must be str or Message, not {type(input_message).__name__}")

        # Get the agent instance (will create if first time for this engine)
        agent_instance = self._get_agent_instance(agent_name)

        # Execute the agent's primary run logic
        return await agent_instance.run(input_msg_obj, **kwargs)

    async def call_tool(self, tool_name: str, arguments_json_str: str) -> Any:
        """
        Executes a registered tool with the provided arguments.

        This method looks up the tool in the application's registry and calls
        its `execute` method. This is typically used internally by agents that
        decide to use a tool.

        Args:
            tool_name: The registered name of the tool to execute.
            arguments_json_str: A JSON string containing the arguments for the tool,
                                as expected by the tool's definition.

        Returns:
            The result returned by the tool's `execute` method. This can be of Any type.
            Returns an error dictionary if the tool is not found.
        """
        tool = self._app.get_tool(tool_name)
        if not tool:
            logger.error(
                f"Engine requested to call tool '{tool_name}', but it was not "
                f"found in the app registry."
            )
            # Return a consistent error format that agents might handle
            return {"error": f"Tool '{tool_name}' not found."}

        logger.debug(f"Engine executing tool '{tool_name}' with args: {arguments_json_str}")
        # Execute the tool
        try:
             result = await tool.execute(arguments_json_str)
             logger.debug(f"Tool '{tool_name}' executed successfully.")
             return result
        except Exception as e:
             logger.error(f"Error executing tool '{tool_name}': {e}", exc_info=True)
             # Propagate error in a structured way if possible
             return {"error": f"Error executing tool '{tool_name}': {str(e)}"}