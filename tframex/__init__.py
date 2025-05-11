import os
from dotenv import load_dotenv

# Load .env file at the earliest point if configurations depend on it
# User's project might also load .env, this ensures library defaults can be set.
# Find project root to load .env from there, if possible, or from current dir.
# This part is tricky for a library. Usually, app config is user's responsibility.
# For now, let's assume .env in user's project root or current dir is loaded by user.
# load_dotenv(find_dotenv(usecwd=True, raise_error_if_not_found=False))


from .primitives import Message, MessageChunk, ToolCall, FunctionCall, ToolParameterProperty, ToolParameters, ToolDefinition
from .llms import BaseLLMWrapper, OpenAIChatLLM
from .tools import Tool
from .memory import BaseMemoryStore, InMemoryMemoryStore
from .agents.base import BaseAgent
from .agents.llm_agent import LLMAgent
from .agents.tool_agent import ToolAgent # Ensure ToolAgent is here if used

from .flow_context import FlowContext # NEW
from .patterns import BasePattern, SequentialPattern, ParallelPattern, RouterPattern, DiscussionPattern # NEW
from .flows import Flow # NEW

from .app import TFrameXApp, TFrameXRuntimeContext

# Create a default 'app' instance for convenience, users can import and use it directly
# Or they can instantiate TFrameXApp() themselves for more control.
# The default LLM configuration here would ideally come from environment variables
# or a more sophisticated config loading mechanism for the library.

# app = TFrameXApp(
#     default_llm=OpenAIChatLLM(
#         model_name=os.getenv("TFRAMEX_MODEL_NAME", "gpt-3.5-turbo"), # Example default
#         api_base_url=os.getenv("TFRAMEX_API_URL", "https://api.openai.com/v1"),
#         api_key=os.getenv("TFRAMEX_API_KEY") # MUST be set by user
#     ) if os.getenv("TFRAMEX_API_KEY") else None # Only init if key is present
# )
# User will likely instantiate their own app with their specific LLM.
# So, just exporting TFrameXApp is cleaner for a library.

__all__ = [
    "Message", "MessageChunk", "ToolCall", "FunctionCall", 
    "ToolParameterProperty", "ToolParameters", "ToolDefinition",
    "BaseLLMWrapper", "OpenAIChatLLM",
    "Tool",
    "BaseMemoryStore", "InMemoryMemoryStore",
    "BaseAgent", "LLMAgent", "ToolAgent",
    
    "FlowContext", # NEW
    "BasePattern", "SequentialPattern", "ParallelPattern", "RouterPattern", "DiscussionPattern", # NEW
    "Flow", # NEW
    
    "TFrameXApp", "TFrameXRuntimeContext"
]