import json
import logging
import os
import sys
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from tframex.models.primitives import Message, ToolCall


class MessageRole(Enum):
    """Enum for different types of messages in an LLM interaction."""

    SYSTEM = "System"
    USER = "User"
    ASSISTANT = "Assistant"
    TOOL = "Tool"


@dataclass
class LLMInteraction:
    """Data class to hold LLM interaction information."""

    messages: List[Message]
    response: Message
    agent_name: str
    tools_called: List[ToolCall] = None
    timestamp: datetime = None

    def __post_init__(self):
        if self.tools_called is None:
            self.tools_called = []
        if self.timestamp is None:
            self.timestamp = datetime.now()


class ColoredFormatter(logging.Formatter):
    """Custom formatter that adds colors to log messages."""

    # ANSI color codes
    COLORS = {
        "DEBUG": "\033[36m",  # Cyan
        "INFO": "\033[32m",  # Green
        "WARNING": "\033[33m",  # Yellow
        "ERROR": "\033[31m",  # Red
        "CRITICAL": "\033[41m",  # Red background
        "RESET": "\033[0m",  # Reset
    }

    def format(self, record: logging.LogRecord) -> str:
        # Add color to the level name
        levelname = record.levelname
        if levelname in self.COLORS:
            record.levelname = (
                f"{self.COLORS[levelname]}{levelname}{self.COLORS['RESET']}"
            )

        # Format the message with timestamp
        formatted = super().format(record)
        return formatted


class LLMInteractionFormatter(logging.Formatter):
    """Custom formatter for LLM interaction logs that formats messages, responses, and tool calls."""

    def _format_message(self, message: Message, index: int = None) -> str:
        """Format a single message with optional index and role information."""
        prefix = f"[{index}] " if index is not None else ""
        role_prefix = f"[{message.role.title()}]"
        if message.role == "tool" and message.name:
            role_prefix = f"[{message.role.title()}: {message.name}]"
        return f"{prefix}{role_prefix} {message.content}"

    def _format_tool_call(self, tool_call: ToolCall) -> str:
        """Format a single tool call with its parameters."""
        tool_name = tool_call.function.name
        try:
            params = json.loads(tool_call.function.arguments)
            params_str = "\n    ".join([f"{k}: {v}" for k, v in params.items()])
        except json.JSONDecodeError:
            params_str = tool_call.function.arguments
        return f"Tool: {tool_name}\n    Parameters:\n    {params_str}"

    def format(self, record: logging.LogRecord) -> str:
        # Get the LLMInteraction object from the record
        interaction = getattr(record, "llm_interaction", None)
        if not interaction:
            return super().format(record)

        # Format timestamp
        timestamp = interaction.timestamp.strftime("%Y-%m-%d %H:%M:%S")

        # Format messages
        messages_str = "\nMessages:\n" + "\n".join(
            [
                self._format_message(msg, i + 1)
                for i, msg in enumerate(interaction.messages)
            ]
        )

        # Format response
        response_str = f"\nResponse:\n{self._format_message(interaction.response)}"

        # Format tools called
        if interaction.tools_called:
            tools_str = "\nTools Called:\n" + "\n".join(
                [
                    self._format_tool_call(tool_call)
                    for tool_call in interaction.tools_called
                ]
            )
        else:
            tools_str = "\nTools Called:\nNo tools were called."

        # Combine all parts with clear separation
        formatted = (
            f"\n{'=' * 80}\n"
            f"Timestamp: {timestamp}\n"
            f"Agent: {interaction.agent_name}\n"
            f"{messages_str}\n"
            f"{response_str}\n"
            f"{tools_str}\n"
            f"{'=' * 80}\n"
        )
        return formatted


def setup_logging(
    level: int = logging.INFO, log_format: Optional[str] = None, use_colors: bool = True
) -> None:
    """
    Configure logging with colors and custom formatting.

    Args:
        level: The logging level (default: INFO)
        log_format: Custom log format string (optional)
        use_colors: Whether to use colored output (default: True)
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Create logs directory if it doesn't exist
    os.makedirs("logs", exist_ok=True)

    # Delete existing log file if it exists
    log_file = "logs/tframex.log"
    if os.path.exists(log_file):
        os.remove(log_file)

    # Create new empty log file
    open(log_file, "a").close()

    # Create console and file handler
    console_handler = logging.StreamHandler(sys.stdout)
    file_handler = logging.FileHandler("logs/tframex.log")

    # Set format
    if log_format is None:
        log_format = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"

    if use_colors:
        formatter = ColoredFormatter(log_format, datefmt="%Y-%m-%d %H:%M:%S")
    else:
        formatter = logging.Formatter(log_format, datefmt="%Y-%m-%d %H:%M:%S")

    console_handler.setFormatter(formatter)
    file_handler.setFormatter(
        logging.Formatter(log_format, datefmt="%Y-%m-%d %H:%M:%S")
    )

    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)

    # Setup specialized handler for llm_interaction logger
    llm_logger = logging.getLogger("llm_interaction")
    llm_logger.setLevel(level)

    # Create a separate log file for LLM interactions
    llm_log_file = "logs/llm_interactions.log"
    if os.path.exists(llm_log_file):
        os.remove(llm_log_file)
    open(llm_log_file, "a").close()

    # Create and configure the LLM interaction handler
    llm_handler = logging.FileHandler(llm_log_file)
    llm_handler.setFormatter(LLMInteractionFormatter())
    llm_logger.addHandler(llm_handler)
