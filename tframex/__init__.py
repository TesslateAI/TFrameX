# tframex/__init__.py
import os
# from dotenv import load_dotenv # Application should handle this
# load_dotenv()

__version__ = "1.1.0"

from .agents import BaseAgent, LLMAgent, ToolAgent
from .app import TFrameXApp, TFrameXRuntimeContext 
from .flows import FlowContext, Flow
from .models.primitives import (
    FunctionCall, Message, MessageChunk, ToolCall,
    ToolDefinition, ToolParameterProperty, ToolParameters,
)
from .patterns import (
    BasePattern, DiscussionPattern, ParallelPattern,
    RouterPattern, SequentialPattern,
)
from .util.engine import Engine 
from .util.llms import BaseLLMWrapper, OpenAIChatLLM
from .util.memory import BaseMemoryStore, InMemoryMemoryStore
from .util.tools import Tool
from .util.logging import setup_logging # Make setup_logging available if users want to call it

# --- MCP Integration Exports ---
from .mcp import (
    MCPManager,
    MCPConnectedServer,
    MCPConfigError,
    load_mcp_server_configs,
    # Meta tools are usually not called directly by library users, but by agents.
    # No harm in exporting if they might be useful for direct use in advanced scenarios.
    tframex_list_mcp_servers,
    tframex_list_mcp_resources,
    tframex_read_mcp_resource,
    tframex_list_mcp_prompts,
    tframex_use_mcp_prompt,
)

__all__ = [
    "BaseAgent", "LLMAgent", "ToolAgent",
    "TFrameXApp", "TFrameXRuntimeContext", 
    "Engine", 
    "FlowContext", "Flow",
    "FunctionCall", "Message", "MessageChunk", "ToolCall",
    "ToolDefinition", "ToolParameterProperty", "ToolParameters",
    "BasePattern", "DiscussionPattern", "ParallelPattern",
    "RouterPattern", "SequentialPattern",
    "BaseLLMWrapper", "OpenAIChatLLM",
    "BaseMemoryStore", "InMemoryMemoryStore",
    "Tool",
    "setup_logging", # Export logging setup

    # MCP Integration
    "MCPManager", "MCPConnectedServer", "MCPConfigError", "load_mcp_server_configs",
    "tframex_list_mcp_servers", "tframex_list_mcp_resources",
    "tframex_read_mcp_resource", "tframex_list_mcp_prompts", "tframex_use_mcp_prompt",
]