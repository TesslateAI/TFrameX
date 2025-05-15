
import json
import logging
import os
import sys
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from tframex.models.primitives import Message, ToolCall


class MessageRole(Enum):
    SYSTEM = "System"
    USER = "User"
    ASSISTANT = "Assistant"
    TOOL = "Tool"


@dataclass
class LLMInteraction:
    messages: List[Message]
    response: Message
    agent_name: str
    tools_called: List[ToolCall] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)


# Global flag to control color use in console_handler, set by setup_logging
use_colors_in_console = True

class ColoredFormatter(logging.Formatter):
    COLORS = {
        "DEBUG": "\033[36m",
        "INFO": "\033[32m",
        "WARNING": "\033[33m",
        "ERROR": "\033[31m",
        "CRITICAL": "\033[41m",
        "RESET": "\033[0m",
    }

    def format(self, record: logging.LogRecord) -> str:
        levelname = record.levelname
        # Check global flag for console coloring
        if use_colors_in_console and sys.stdout.isatty() and levelname in self.COLORS :
            record.levelname = (
                f"{self.COLORS[levelname]}{levelname}{self.COLORS['RESET']}"
            )
        # For file logs, we don't want color codes, so if not use_colors_in_console or not a tty,
        # ensure original levelname is used if it was modified.
        # This specific formatter is typically for console, so the check might be more direct.
        # Let's assume this formatter is ONLY used for console_handler if colors are enabled.
        
        formatted = super().format(record)
        # Reset levelname if it was colored to avoid issues if record is processed by other formatters
        if hasattr(record, '_original_levelname'):
            record.levelname = record._original_levelname
            del record._original_levelname
        elif use_colors_in_console and sys.stdout.isatty() and record.levelname.startswith("\033"): # if it got colored
             record.levelname = levelname # reset for other handlers
        return formatted


class LLMInteractionFormatter(logging.Formatter):
    def _format_message(self, message: Message, index: int = None) -> str:
        prefix = f"  [{index}] " if index is not None else "  "
        role_prefix = f"[{message.role.title()}]"
        if message.role == "tool" and message.name:
            role_prefix = f"[{message.role.title()}: {message.name}]"
        
        content_str = str(message.content) if message.content is not None else "[No Content]"
        return f"{prefix}{role_prefix} {content_str}"

    def _format_tool_call(self, tool_call: ToolCall) -> str:
        tool_name = tool_call.function.name
        try:
            params_obj = json.loads(tool_call.function.arguments)
            # Indent arguments for better readability under the tool name
            params_str = json.dumps(params_obj, indent=4)
            # Further indent each line of the JSON string
            params_str = "\n".join(["    " + line for line in params_str.splitlines()])
        except (json.JSONDecodeError, TypeError):
            params_str = f"    {tool_call.function.arguments}" # Basic indent if not JSON
        
        return f"  Tool: {tool_name}\n  Arguments:\n{params_str}"


    def format(self, record: logging.LogRecord) -> str:
        interaction = getattr(record, "llm_interaction", None)
        if not interaction or not isinstance(interaction, LLMInteraction):
            return super().format(record)

        timestamp_str = interaction.timestamp.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]

        messages_str_list = [
            self._format_message(msg, i + 1)
            for i, msg in enumerate(interaction.messages)
        ]
        messages_formatted = "Messages:\n" + "\n".join(messages_str_list)

        response_formatted = f"Response:\n{self._format_message(interaction.response)}"

        if interaction.tools_called:
            tools_str_list = [
                self._format_tool_call(tool_call)
                for tool_call in interaction.tools_called
            ]
            tools_formatted = "Tools Called:\n" + "\n".join(tools_str_list)
        else:
            tools_formatted = "Tools Called:\n  No tools were called."

        formatted_log = (
            f"\n{'=' * 80}\n"
            f"LLM Interaction Log\n"
            f"Timestamp: {timestamp_str}\n"
            f"Agent: {interaction.agent_name}\n"
            f"{messages_formatted}\n"
            f"{response_formatted}\n"
            f"{tools_formatted}\n"
            f"{'=' * 80}\n"
        )
        return formatted_log


def setup_logging(
    level: int = logging.INFO, 
    log_format: Optional[str] = None, 
    use_colors: bool = True,
    save_to_file: bool = True
) -> None:
    global use_colors_in_console
    use_colors_in_console = use_colors # Set for ColoredFormatter

    root_logger = logging.getLogger()
    # Detach existing handlers to avoid issues during re-configuration
    for handler in list(root_logger.handlers): # Iterate over a copy
        handler.close()
        root_logger.removeHandler(handler)
    
    # Also for llm_interaction logger
    llm_interaction_logger = logging.getLogger("llm_interaction")
    for handler in list(llm_interaction_logger.handlers):
        handler.close()
        llm_interaction_logger.removeHandler(handler)

    root_logger.setLevel(level) # Set level after clearing handlers

    # Console Handler (always added)
    console_handler = logging.StreamHandler(sys.stdout)
    default_log_format = "%(asctime)s | %(levelname)-8s | %(name)-25s | %(message)s"
    effective_log_format = log_format or default_log_format

    if use_colors and sys.stdout.isatty(): # Only use colors if TTY
        console_formatter = ColoredFormatter(effective_log_format, datefmt="%Y-%m-%d %H:%M:%S")
    else:
        console_formatter = logging.Formatter(effective_log_format, datefmt="%Y-%m-%d %H:%M:%S")
    
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)

    if save_to_file:
        try:
            os.makedirs("logs", exist_ok=True)
        except OSError as e:
            root_logger.error(f"Could not create logs directory: {e}")
            # Optionally, decide if this is fatal or if logging should proceed without files
            return # Or raise

        general_log_file = "logs/tframex.log"
        try:
            # Attempt to open in 'w' mode to truncate. If it fails due to permissions,
            # it will be caught by the FileHandler instantiation attempt.
            # This pre-emptive removal is often problematic on Windows if logger still holds file.
            if os.path.exists(general_log_file):
                 # Ensure no handlers are attached before trying to remove
                pass # Handlers are closed above
            file_handler = logging.FileHandler(general_log_file, mode='w')
            file_formatter = logging.Formatter(effective_log_format, datefmt="%Y-%m-%d %H:%M:%S")
            file_handler.setFormatter(file_formatter)
            root_logger.addHandler(file_handler)
        except Exception as e:
            root_logger.error(f"Failed to set up general file log handler for {general_log_file}: {e}")


        llm_interaction_logger.propagate = False 
        llm_interaction_logger.setLevel(level)

        llm_log_file = "logs/llm_interactions.log"
        try:
            if os.path.exists(llm_log_file):
                pass # Handlers closed above
            llm_file_handler = logging.FileHandler(llm_log_file, mode='w')
            llm_file_handler.setFormatter(LLMInteractionFormatter())
            llm_interaction_logger.addHandler(llm_file_handler)
        except Exception as e:
            root_logger.error(f"Failed to set up LLM interaction file log handler for {llm_log_file}: {e}")
    else:
        # If not saving to file, ensure llm_interaction logger still logs to console if desired (via propagation)
        llm_interaction_logger.propagate = True
        llm_interaction_logger.setLevel(level)

