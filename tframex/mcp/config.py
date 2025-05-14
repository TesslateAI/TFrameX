# tframex/mcp/config.py
import json
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger("tframex.mcp.config")

class MCPConfigError(Exception):
    pass

def load_mcp_server_configs(file_path: str = "servers_config.json") -> Dict[str, Dict[str, Any]]:
    """
    Loads MCP server configurations from a JSON file.
    Returns a dictionary where keys are server aliases and values are their configs.
    """
    logger.info(f"Loading MCP server configurations from '{file_path}'...")
    try:
        with open(file_path, "r") as f:
            data = json.load(f)
    except FileNotFoundError:
        logger.warning(f"MCP server configuration file '{file_path}' not found. No MCP servers will be loaded.")
        return {}
    except json.JSONDecodeError as e:
        logger.error(f"Error decoding JSON from MCP server config '{file_path}': {e}")
        raise MCPConfigError(f"Invalid JSON in {file_path}: {e}") from e

    if not isinstance(data, dict) or "mcpServers" not in data:
        raise MCPConfigError(f"'mcpServers' key not found or not a dictionary in '{file_path}'.")

    server_configs = data["mcpServers"]
    if not isinstance(server_configs, dict):
        raise MCPConfigError(f"'mcpServers' value must be a dictionary in '{file_path}'.")

    validated_configs: Dict[str, Dict[str, Any]] = {}
    for server_alias, config in server_configs.items():
        if not isinstance(config, dict):
            logger.warning(f"Skipping invalid config for MCP server '{server_alias}': not a dictionary.")
            continue
        if "type" not in config:
            logger.warning(f"Skipping MCP server '{server_alias}': 'type' (stdio/streamable-http) missing.")
            continue
        
        config_type = str(config["type"]).lower()
        if config_type == "stdio":
            if "command" not in config or not config["command"]:
                logger.warning(f"Skipping stdio MCP server '{server_alias}': 'command' is missing or empty.")
                continue
        elif config_type == "streamable-http":
            if "url" not in config or not config["url"]:
                logger.warning(f"Skipping streamable-http MCP server '{server_alias}': 'url' is missing or empty.")
                continue
        else:
            logger.warning(f"Skipping MCP server '{server_alias}': unknown type '{config['type']}'.")
            continue
        
        validated_configs[server_alias] = config
        logger.info(f"Validated MCP server config for '{server_alias}' (type: {config_type}).")

    if not validated_configs:
        logger.info(f"No valid MCP server configurations found in '{file_path}'.")
    return validated_configs