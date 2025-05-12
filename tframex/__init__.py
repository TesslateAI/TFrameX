# tframex/__init__.py (NEW VERSION)
import os
from dotenv import load_dotenv

# It's generally better for applications to handle dotenv loading.
# load_dotenv()

# Import from subpackages
from .agents import BaseAgent, LLMAgent, ToolAgent
from .app import TFrameXApp, TFrameXRuntimeContext # TFrameXRuntimeContext is now defined in app.py
from .flows import FlowContext, Flow
from .models.primitives import ( # Note the .models path
    FunctionCall,
    Message,
    MessageChunk,
    ToolCall,
    ToolDefinition,
    ToolParameterProperty,
    ToolParameters,
)
from .patterns import ( # Note the .patterns path
    BasePattern,
    DiscussionPattern,
    ParallelPattern,
    RouterPattern,
    SequentialPattern,
)
from .util.engine import Engine # Engine is now directly under util
from .util.llms import BaseLLMWrapper, OpenAIChatLLM
from .util.memory import BaseMemoryStore, InMemoryMemoryStore
from .util.tools import Tool
# setup_logging might be called by TFrameXApp itself, not typically part of public API to re-export
# from .util.logging import setup_logging


__all__ = [
    # Agents
    "BaseAgent",
    "LLMAgent",
    "ToolAgent",
    # App & Runtime
    "TFrameXApp",
    "TFrameXRuntimeContext", # This was TFrameXRuntimeContext in the old __init__
    "Engine", # New public component
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
    # Utilities
    "BaseLLMWrapper",
    "OpenAIChatLLM",
    "BaseMemoryStore",
    "InMemoryMemoryStore",
    "Tool",
    # "setup_logging", # Decide if this should be public
]