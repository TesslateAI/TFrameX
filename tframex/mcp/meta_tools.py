# tframex/mcp/meta_tools.py
import logging
from typing import Dict, Any, Optional, List, Union, TYPE_CHECKING # Import TYPE_CHECKING

# from tframex.app import TFrameXRuntimeContext # REMOVE THIS DIRECT IMPORT
from .manager import MCPManager # To access the manager
from mcp.types import TextContent, ImageContent, EmbeddedResource 

# Conditional import for type hinting to avoid circular import
if TYPE_CHECKING:
    from tframex.app import TFrameXRuntimeContext

logger = logging.getLogger("tframex.mcp.meta_tools")

# These functions will be wrapped by @app.tool() in TFrameXApp setup.
# They need access to the MCPManager, which can be passed via TFrameXRuntimeContext.

# Use string literal for the type hint if TYPE_CHECKING is False at runtime
async def tframex_list_mcp_servers(rt_ctx: 'TFrameXRuntimeContext') -> str:
    """Lists all configured and initialized MCP servers."""
    # Ensure rt_ctx has mcp_manager (runtime check)
    if not hasattr(rt_ctx, 'mcp_manager') or not rt_ctx.mcp_manager:
        return "MCP integration is not initialized in the application's runtime context."
    
    manager: MCPManager = rt_ctx.mcp_manager # Type cast if needed, or rely on duck typing
    output = "Connected MCP Servers:\n"
    if not manager.servers:
        return "No MCP servers are currently configured or connected."
    
    for alias, server_obj in manager.servers.items():
        status = "Initialized" if server_obj.is_initialized else "Failed/Not Initialized"
        s_info = server_obj.server_info
        name_version = f"{s_info.name} v{s_info.version}" if s_info and hasattr(s_info, 'name') and hasattr(s_info, 'version') else "N/A"
        output += f"  - Alias: {alias} (Name: {name_version}, Status: {status})\n"
        if server_obj.is_initialized and server_obj.capabilities:
            caps = server_obj.capabilities
            output += f"    Capabilities: Tools={hasattr(caps, 'tools') and bool(caps.tools)}, Resources={hasattr(caps, 'resources') and bool(caps.resources)}, Prompts={hasattr(caps, 'prompts') and bool(caps.prompts)}\n"
    return output

async def tframex_list_mcp_resources(rt_ctx: 'TFrameXRuntimeContext', server_alias: Optional[str] = None) -> Union[str, Dict[str, List[Dict[str, Any]]]]:
    """
    Lists available resources from a specific MCP server or all initialized MCP servers.
    Args:
        rt_ctx: The TFrameX runtime context.
        server_alias: The alias of the MCP server. If None, lists from all.
    Returns:
        A string listing resources or a dictionary if server_alias is None.
    """
    if not hasattr(rt_ctx, 'mcp_manager') or not rt_ctx.mcp_manager:
        return "MCP integration is not initialized."
    manager: MCPManager = rt_ctx.mcp_manager
    infos_by_server: Dict[str, List[Dict[str, Any]]] = {}
    servers_to_query = []
    if server_alias:
        server = manager.get_server(server_alias) # get_server checks for initialization
        if server:
            servers_to_query.append(server)
        else:
            return f"Error: MCP Server '{server_alias}' not found or not initialized."
    else:
        servers_to_query = [s for s in manager.servers.values() if s.is_initialized]

    if not servers_to_query:
        return "No MCP servers available to list resources from."

    for server_obj in servers_to_query:
        # Ensure capabilities and resources attribute exist before accessing
        if server_obj.capabilities and hasattr(server_obj.capabilities, 'resources') and server_obj.capabilities.resources and server_obj.resources:
            infos_by_server[server_obj.server_alias] = [
                {"uri": str(r.uri), "name": r.name, "description": r.description, "mimeType": r.mimeType}
                for r in server_obj.resources # server_obj.resources should be List[ActualMCPResource]
            ]
        else:
            infos_by_server[server_obj.server_alias] = [] 

    if server_alias: 
        res_list = infos_by_server.get(server_alias, [])
        if not res_list: return f"No resources found or resource capability missing on server '{server_alias}'."
        output = f"Resources from MCP server '{server_alias}':\n"
        for r_info in res_list:
            output += f"  - URI: {r_info['uri']}\n    Name: {r_info['name']}\n    Desc: {r_info['description']}\n    MIME: {r_info['mimeType']}\n"
        return output
    else: 
        return infos_by_server


async def tframex_read_mcp_resource(rt_ctx: 'TFrameXRuntimeContext', server_alias: str, resource_uri: str) -> str:
    """
    Reads content from a specific resource on a specific MCP server.
    Args:
        rt_ctx: The TFrameX runtime context.
        server_alias: The alias of the MCP server.
        resource_uri: The URI of the resource to read.
    Returns:
        The resource content as a string, or an error message.
    """
    if not hasattr(rt_ctx, 'mcp_manager') or not rt_ctx.mcp_manager:
        return "MCP integration is not initialized."
    manager: MCPManager = rt_ctx.mcp_manager
    server = manager.get_server(server_alias)
    if not server:
        return f"Error: MCP Server '{server_alias}' not found or not initialized."
    if not (server.capabilities and hasattr(server.capabilities, 'resources') and server.capabilities.resources):
        return f"Error: Server '{server_alias}' does not support resources."

    try:
        content_result = await server.read_mcp_resource(resource_uri)
        
        if isinstance(content_result, str): return content_result
        if isinstance(content_result, TextContent) and content_result.text is not None: return content_result.text
        if isinstance(content_result, ImageContent): return f"[Image content from MCP resource '{resource_uri}', mime: {content_result.mimeType}]"
        if isinstance(content_result, EmbeddedResource): return f"[Embedded resource from MCP resource '{resource_uri}', uri: {content_result.resource.uri}]"
        
        if hasattr(content_result, 'text') and content_result.text is not None: return content_result.text
        
        return f"[Non-textual or complex content received from resource '{resource_uri}'. Type: {type(content_result)}]"
    except Exception as e:
        logger.error(f"Error reading MCP resource '{resource_uri}' from '{server_alias}': {e}", exc_info=True)
        return f"Error reading resource '{resource_uri}' from '{server_alias}': {str(e)}"

async def tframex_list_mcp_prompts(rt_ctx: 'TFrameXRuntimeContext', server_alias: Optional[str] = None) -> Union[str, Dict[str, List[Dict[str, Any]]]]:
    """Lists available prompts from a specific or all MCP servers."""
    if not hasattr(rt_ctx, 'mcp_manager') or not rt_ctx.mcp_manager:
        return "MCP integration is not initialized."
    manager: MCPManager = rt_ctx.mcp_manager
    infos_by_server: Dict[str, List[Dict[str, Any]]] = {}
    servers_to_query = []

    if server_alias:
        server = manager.get_server(server_alias)
        if server: servers_to_query.append(server)
        else: return f"Error: MCP Server '{server_alias}' not found or not initialized."
    else:
        servers_to_query = [s for s in manager.servers.values() if s.is_initialized]

    if not servers_to_query: return "No MCP servers to list prompts from."

    for server_obj in servers_to_query:
        if server_obj.capabilities and hasattr(server_obj.capabilities, 'prompts') and server_obj.capabilities.prompts and server_obj.prompts:
            infos_by_server[server_obj.server_alias] = [
                {
                    "name": p.name, 
                    "description": p.description, 
                    "arguments": [{"name": arg.name, "description": arg.description, "required": arg.required} for arg in p.arguments] if p.arguments else []
                }
                for p in server_obj.prompts # server_obj.prompts should be List[ActualMCPPrompt]
            ]
        else: infos_by_server[server_obj.server_alias] = []
    
    if server_alias:
        p_list = infos_by_server.get(server_alias, [])
        if not p_list: return f"No prompts found or prompt capability missing on server '{server_alias}'."
        output = f"Prompts from MCP server '{server_alias}':\n"
        for p_info in p_list:
            args_str = ", ".join([f"{a['name']}{' (req)' if a['required'] else ''}" for a in p_info['arguments']])
            output += f"  - Name: {p_info['name']}\n    Desc: {p_info['description']}\n    Args: {args_str}\n"
        return output
    else:
        return infos_by_server


async def tframex_use_mcp_prompt(rt_ctx: 'TFrameXRuntimeContext', server_alias: str, prompt_name: str, arguments: Dict[str, Any]) -> List[Dict[str, str]]:
    """
    Gets messages from a server-defined MCP prompt. The LLMAgent should then use these.
    Args:
        rt_ctx: The TFrameX runtime context.
        server_alias: The alias of the MCP server.
        prompt_name: The name of the prompt.
        arguments: Arguments for the prompt.
    Returns:
        A list of message dictionaries (e.g., [{"role": "user", "content": "..."}]), or an error message list.
    """
    if not hasattr(rt_ctx, 'mcp_manager') or not rt_ctx.mcp_manager:
        return [{"role": "system", "content": "MCP integration is not initialized."}] 
    manager: MCPManager = rt_ctx.mcp_manager
    # ... (rest of the function as before)
    server = manager.get_server(server_alias)
    if not server:
        return [{"role": "system", "content": f"Error: MCP Server '{server_alias}' not found or not initialized."}]
    if not (server.capabilities and hasattr(server.capabilities, 'prompts') and server.capabilities.prompts):
        return [{"role": "system", "content": f"Error: Server '{server_alias}' does not support prompts."}]

    try:
        prompt_result = await server.get_mcp_prompt(prompt_name, arguments) 
        messages = []
        if prompt_result and hasattr(prompt_result, 'messages'):
            for mcp_msg in prompt_result.messages: 
                content_text = ""
                if isinstance(mcp_msg.content, TextContent): content_text = mcp_msg.content.text or ""
                elif isinstance(mcp_msg.content, ImageContent): content_text = f"[Image from prompt: {mcp_msg.content.mimeType}]"
                elif isinstance(mcp_msg.content, EmbeddedResource): content_text = f"[Resource from prompt: {mcp_msg.content.resource.uri}]"
                else: content_text = str(mcp_msg.content) if mcp_msg.content else ""
                messages.append({"role": mcp_msg.role, "content": content_text})
            return messages
        else:
            logger.error(f"MCP prompt '{prompt_name}' from '{server_alias}' returned invalid result: {prompt_result}")
            return [{"role": "system", "content": f"Error: Prompt '{prompt_name}' from '{server_alias}' returned an empty or invalid result."}]
    except Exception as e:
        logger.error(f"Error using MCP prompt '{prompt_name}' from '{server_alias}': {e}", exc_info=True)
        return [{"role": "system", "content": f"Error getting prompt '{prompt_name}' from '{server_alias}': {str(e)}"}]