# tframex/__init__.py
import os

from dotenv import load_dotenv

# Import from subpackages
from .agents import BaseAgent, LLMAgent, ToolAgent
from .app import (
    TFrameXApp,
    TFrameXRuntimeContext,
)
from .flows import Flow, FlowContext
from .models.primitives import (
    FunctionCall,
    Message,
    MessageChunk,
    ToolCall,
    ToolDefinition,
    ToolParameterProperty,
    ToolParameters,
)
from .patterns import ( # Updated import style
    BasePattern,
    DiscussionPattern,
    ParallelPattern,
    RouterPattern,
    SequentialPattern,
    DelegatePattern,    # Added
    ProcessingMode,     # Added
)
from .util.engine import Engine
from .util.llms import BaseLLMWrapper, OpenAIChatLLM
from .util.memory import BaseMemoryStore, InMemoryMemoryStore
from .util.tools import Tool
from .util.logging import setup_logging, LLMInteraction # Expose setup_logging and LLMInteraction

# It's generally better for applications to handle dotenv loading.
# load_dotenv()

__all__ = [
    # Agents
    "BaseAgent",
    "LLMAgent",
    "ToolAgent",
    # App & Runtime
    "TFrameXApp",
    "TFrameXRuntimeContext",
    "Engine",
    # Flows
    "FlowContext",
    "Flow",
    # Models (Primitives)
    "FunctionCall",
    "Message",
    "MessageChunk",
    "ToolCall",
    "ToolDefinition",
    "ToolParameterProperty",
    "ToolParameters",
    # Patterns
    "BasePattern",
    "DiscussionPattern",
    "ParallelPattern",
    "RouterPattern",
    "SequentialPattern",
    "DelegatePattern",    # Added
    "ProcessingMode",     # Added
    # Utilities
    "BaseLLMWrapper",
    "OpenAIChatLLM",
    "BaseMemoryStore",
    "InMemoryMemoryStore",
    "Tool",
    "setup_logging", # Expose setup_logging
    "LLMInteraction",# Expose LLMInteraction for type hinting or direct use
]