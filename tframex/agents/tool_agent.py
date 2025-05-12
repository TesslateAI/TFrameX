import json  # Added
import logging
from typing import Any, Dict, List, Optional, Union  # Added List, Optional, Dict

from tframex.models.primitives import Message
from tframex.util.llms import BaseLLMWrapper  # Added
from tframex.util.memory import BaseMemoryStore  # Added
from tframex.util.tools import Tool

from .base import BaseAgent

logger = logging.getLogger(__name__)


class ToolAgent(BaseAgent):
    """
    A stateless agent that wraps a single Tool for direct execution.
    It does not use an LLM for decision-making itself.
    The agent expects to be configured with exactly one tool.
    Input to its `run` method should be a dictionary of arguments for the tool,
    a JSON string of those arguments, or a Message whose content is that JSON string.
    """

    def __init__(
        self,
        agent_id: str,
        tools: List[
            Tool
        ],  # Will be populated by TFrameXApp based on @app.agent(tools=["tool_name"])
        llm: Optional[BaseLLMWrapper] = None,  # For signature compatibility
        memory: Optional[BaseMemoryStore] = None,  # For signature compatibility
        system_prompt_template: Optional[str] = None,  # For signature compatibility
        **config: Any,
    ):

        # Determine the single tool this agent will run
        # Option 1: Agent is configured with exactly one tool in the 'tools' list.
        # Option 2: Agent is configured with 'target_tool_name' in its **config, if multiple tools are somehow passed.

        self.tool_to_run: Optional[Tool] = None
        effective_tools_for_base: List[Tool] = []

        target_tool_name_from_config = config.get("target_tool_name")

        if target_tool_name_from_config:
            if not tools:
                raise ValueError(
                    f"ToolAgent '{agent_id}' configured with target_tool_name '{target_tool_name_from_config}' but no tools list was provided."
                )
            for t in tools:
                if t.name == target_tool_name_from_config:
                    self.tool_to_run = t
                    break
            if not self.tool_to_run:
                raise ValueError(
                    f"ToolAgent '{agent_id}': Tool '{target_tool_name_from_config}' specified in config not found in the agent's tool list: {[t.name for t in tools]}."
                )
            effective_tools_for_base = [self.tool_to_run]
        elif tools and len(tools) == 1:
            self.tool_to_run = tools[0]
            effective_tools_for_base = tools
        elif tools and len(tools) > 1:
            raise ValueError(
                f"ToolAgent '{agent_id}' was provided with multiple tools ({[t.name for t in tools]}) "
                f"but no 'target_tool_name' was specified in its configuration to select one."
            )
        else:  # No tools provided and no target_tool_name
            raise ValueError(
                f"ToolAgent '{agent_id}' must be configured with exactly one tool. "
                f"Provide one tool in the 'tools' list via @app.agent(tools=['my_tool_name']) "
                f"or specify 'target_tool_name' in agent_config if disambiguation is needed."
            )

        # ToolAgent doesn't use an LLM, its own memory store, or a system prompt in the typical agent sense.
        super().__init__(
            agent_id,
            llm=None,
            tools=effective_tools_for_base,
            memory=None,
            system_prompt_template=None,
            **config,
        )
        # self.tools dict in BaseAgent will contain the single tool. self.tool_to_run is also set.

    async def run(
        self, input_message: Union[str, Message, Dict[str, Any]], **kwargs: Any
    ) -> Message:
        input_args: Dict[str, Any]

        if isinstance(input_message, dict):
            input_args = input_message
        elif isinstance(input_message, Message):
            if input_message.content is None:
                logger.error(
                    f"ToolAgent '{self.agent_id}': Received Message with None content."
                )
                return Message(
                    role="assistant",
                    name=self.tool_to_run.name,
                    content="Error: Input Message has no content.",
                )
            try:
                input_args = json.loads(input_message.content)
            except json.JSONDecodeError as e:
                logger.error(
                    f"ToolAgent '{self.agent_id}': Invalid JSON in Message content: '{input_message.content}'. Error: {e}"
                )
                return Message(
                    role="assistant",
                    name=self.tool_to_run.name,
                    content=f"Error: Invalid JSON input for ToolAgent '{self.agent_id}'. Content was not valid JSON.",
                )
        elif isinstance(input_message, str):
            try:
                input_args = json.loads(input_message)
            except json.JSONDecodeError as e:
                logger.error(
                    f"ToolAgent '{self.agent_id}': Invalid JSON string input: '{input_message}'. Error: {e}"
                )
                return Message(
                    role="assistant",
                    name=self.tool_to_run.name,
                    content=f"Error: Invalid JSON string input for ToolAgent '{self.agent_id}'. Expected a JSON string of arguments.",
                )
        else:
            return Message(
                role="assistant",
                name=self.tool_to_run.name,
                content=f"Error: Invalid input type for ToolAgent '{self.agent_id}'. Expected JSON string, dict, or Message with JSON content.",
            )

        # Tool.execute expects a JSON string of arguments.
        args_json_str_for_tool = json.dumps(input_args)

        logger.info(
            f"ToolAgent '{self.agent_id}' executing tool '{self.tool_to_run.name}' with JSON args: {args_json_str_for_tool[:200]}"
        )
        try:
            tool_result = await self.tool_to_run.execute(args_json_str_for_tool)

            result_content: str
            if isinstance(tool_result, dict) and "error" in tool_result:
                result_content = f"Tool Error: {tool_result['error']}"
            elif isinstance(
                tool_result, (dict, list)
            ):  # If result is complex, stringify as JSON
                result_content = json.dumps(tool_result)
            else:  # Otherwise, simple string conversion
                result_content = str(tool_result)

            return Message(
                role="assistant", name=self.tool_to_run.name, content=result_content
            )
        except Exception as e:
            logger.error(
                f"ToolAgent '{self.agent_id}' error running tool '{self.tool_to_run.name}': {e}",
                exc_info=True,
            )
            return Message(
                role="assistant",
                name=self.tool_to_run.name,
                content=f"Error executing tool '{self.tool_to_run.name}': {str(e)}",
            )
