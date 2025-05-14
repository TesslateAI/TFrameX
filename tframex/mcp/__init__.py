# tframex/mcp/__init__.py
import logging

from .config import MCPConfigError, load_mcp_server_configs
from .manager import MCPManager
from .server_connector import MCPConnectedServer
from .meta_tools import (
    tframex_list_mcp_servers,
    tframex_list_mcp_resources,
    tframex_read_mcp_resource,
    tframex_list_mcp_prompts,
    tframex_use_mcp_prompt
)

logger = logging.getLogger("tframex.mcp")

__all__ = [
    "MCPManager",
    "MCPConnectedServer",
    "MCPConfigError",
    "load_mcp_server_configs",
    "tframex_list_mcp_servers",
    "tframex_list_mcp_resources",
    "tframex_read_mcp_resource",
    "tframex_list_mcp_prompts",
    "tframex_use_mcp_prompt",
]

logger.debug("TFrameX MCP Integration package initialized.")