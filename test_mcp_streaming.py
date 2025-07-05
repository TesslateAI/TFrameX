#!/usr/bin/env python3
"""
Test MCP integration with streaming functionality
"""

import asyncio
import logging
import os
import json
from pathlib import Path
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# TFrameX imports
from tframex import TFrameXApp, Message, OpenAIChatLLM

# LLM Configuration
llm = OpenAIChatLLM(
    model_name=os.getenv("OPENAI_MODEL_NAME", "Llama-4-Maverick-17B-128E-Instruct-FP8"),
    api_base_url=os.getenv("OPENAI_API_BASE", "https://api.llama.com/compat/v1/"),
    api_key=os.getenv("OPENAI_API_KEY", " ")
)

def create_minimal_mcp_config():
    """Create a minimal MCP server configuration for testing."""
    # Create a minimal configuration that doesn't depend on external servers
    config = {
        "mcpServers": {
            "echo_server": {
                "command": "python",
                "args": ["-c", """
import json
import sys
import asyncio

# Minimal echo MCP server for testing
async def main():
    # Read initialize request
    line = sys.stdin.readline().strip()
    if line:
        request = json.loads(line)
        if request.get("method") == "initialize":
            response = {
                "jsonrpc": "2.0",
                "id": request.get("id"),
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {
                        "tools": {}
                    },
                    "serverInfo": {
                        "name": "echo-server",
                        "version": "1.0.0"
                    }
                }
            }
            print(json.dumps(response))
            sys.stdout.flush()
    
    # Keep alive
    while True:
        await asyncio.sleep(1)

if __name__ == "__main__":
    asyncio.run(main())
"""],
                "env": {}
            }
        }
    }
    return config

async def test_mcp_streaming():
    """Test MCP integration with streaming enabled and disabled"""
    logger.info("Testing MCP integration with streaming...")
    
    test_results = []
    
    # Create temporary MCP config for testing
    config_path = Path("test_mcp_config.json")
    try:
        config = create_minimal_mcp_config()
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        
        for streaming in [True, False]:
            mode = "STREAMING" if streaming else "NON-STREAMING"
            logger.info(f"\n{'='*50}")
            logger.info(f"Testing MCP {mode} mode")
            logger.info(f"{'='*50}")
            
            # Test 1: Basic MCP agent with streaming
            try:
                logger.info("1. Testing Basic MCP Agent")
                
                app = TFrameXApp(
                    default_llm=llm,
                    mcp_config_file=str(config_path)
                )
                
                @app.agent(
                    name="MCPAgent",
                    description="MCP test agent",
                    system_prompt="You are an MCP-enabled assistant. Use available tools when appropriate.",
                    streaming=streaming,
                    tools=["tframex_list_mcp_servers"]  # Built-in MCP meta-tool
                )
                async def mcp_agent():
                    pass
                
                async with app.run_context() as ctx:
                    message = Message(role="user", content="What MCP servers are available?")
                    response = await ctx.call_agent("MCPAgent", message)
                    
                    success = response and len(response.content) > 0
                    test_results.append(f"MCP Basic Agent {mode}: {'PASS' if success else 'FAIL'}")
                    logger.info(f"MCP Basic Agent {mode}: {'PASS' if success else 'FAIL'}")
                    
            except Exception as e:
                test_results.append(f"MCP Basic Agent {mode}: FAIL - {str(e)}")
                logger.error(f"MCP Basic Agent {mode}: FAIL - {str(e)}")
            
            # Test 2: MCP agent without external servers (fallback test)
            try:
                logger.info("2. Testing MCP Agent without External Servers")
                
                app = TFrameXApp(
                    default_llm=llm
                    # No MCP config file - should work without external servers
                )
                
                @app.agent(
                    name="NoMCPAgent",
                    description="Agent without MCP servers",
                    system_prompt="You are a helpful assistant without MCP capabilities.",
                    streaming=streaming
                )
                async def no_mcp_agent():
                    pass
                
                async with app.run_context() as ctx:
                    message = Message(role="user", content="Hello, how are you?")
                    response = await ctx.call_agent("NoMCPAgent", message)
                    
                    success = response and len(response.content) > 0
                    test_results.append(f"No MCP Agent {mode}: {'PASS' if success else 'FAIL'}")
                    logger.info(f"No MCP Agent {mode}: {'PASS' if success else 'FAIL'}")
                    
            except Exception as e:
                test_results.append(f"No MCP Agent {mode}: FAIL - {str(e)}")
                logger.error(f"No MCP Agent {mode}: FAIL - {str(e)}")
            
            # Test 3: MCP meta-tools functionality
            try:
                logger.info("3. Testing MCP Meta-tools")
                
                app = TFrameXApp(
                    default_llm=llm
                )
                
                @app.agent(
                    name="MetaToolsAgent",
                    description="Agent with MCP meta-tools",
                    system_prompt="You are an assistant with MCP meta-tools. List available MCP functionality.",
                    streaming=streaming,
                    tools=["tframex_list_mcp_servers", "tframex_list_mcp_resources"]
                )
                async def meta_tools_agent():
                    pass
                
                async with app.run_context() as ctx:
                    message = Message(role="user", content="List available MCP functionality")
                    response = await ctx.call_agent("MetaToolsAgent", message)
                    
                    success = response and len(response.content) > 0
                    test_results.append(f"MCP Meta-tools {mode}: {'PASS' if success else 'FAIL'}")
                    logger.info(f"MCP Meta-tools {mode}: {'PASS' if success else 'FAIL'}")
                    
            except Exception as e:
                test_results.append(f"MCP Meta-tools {mode}: FAIL - {str(e)}")
                logger.error(f"MCP Meta-tools {mode}: FAIL - {str(e)}")
            
            # Test 4: Agent with all MCP tools enabled
            try:
                logger.info("4. Testing Agent with All MCP Tools")
                
                app = TFrameXApp(
                    default_llm=llm
                )
                
                @app.agent(
                    name="AllMCPAgent",
                    description="Agent with all MCP tools enabled",
                    system_prompt="You are an assistant with access to all MCP tools and resources.",
                    streaming=streaming,
                    mcp_tools="ALL"  # Enable all MCP tools
                )
                async def all_mcp_agent():
                    pass
                
                async with app.run_context() as ctx:
                    message = Message(role="user", content="What MCP capabilities do you have?")
                    response = await ctx.call_agent("AllMCPAgent", message)
                    
                    success = response and len(response.content) > 0
                    test_results.append(f"All MCP Tools {mode}: {'PASS' if success else 'FAIL'}")
                    logger.info(f"All MCP Tools {mode}: {'PASS' if success else 'FAIL'}")
                    
            except Exception as e:
                test_results.append(f"All MCP Tools {mode}: FAIL - {str(e)}")
                logger.error(f"All MCP Tools {mode}: FAIL - {str(e)}")
            
            # Test 5: MCP agent with custom tool 
            try:
                logger.info("5. Testing MCP Agent with Custom Tools")
                
                app = TFrameXApp(
                    default_llm=llm
                )
                
                @app.tool(description="Get current time")
                async def get_time() -> str:
                    import datetime
                    return datetime.datetime.now().isoformat()
                
                @app.agent(
                    name="CustomMCPAgent",
                    description="Agent with custom and MCP tools",
                    system_prompt="You are an assistant with both custom tools and MCP capabilities.",
                    streaming=streaming,
                    tools=["get_time", "tframex_list_mcp_servers"]
                )
                async def custom_mcp_agent():
                    pass
                
                async with app.run_context() as ctx:
                    message = Message(role="user", content="What time is it and what MCP servers are available?")
                    response = await ctx.call_agent("CustomMCPAgent", message)
                    
                    success = response and len(response.content) > 0
                    test_results.append(f"Custom MCP Tools {mode}: {'PASS' if success else 'FAIL'}")
                    logger.info(f"Custom MCP Tools {mode}: {'PASS' if success else 'FAIL'}")
                    
            except Exception as e:
                test_results.append(f"Custom MCP Tools {mode}: FAIL - {str(e)}")
                logger.error(f"Custom MCP Tools {mode}: FAIL - {str(e)}")
    
    finally:
        # Clean up test config file
        if config_path.exists():
            config_path.unlink()
    
    # Print summary
    logger.info(f"\n{'='*60}")
    logger.info("MCP STREAMING TEST SUMMARY")
    logger.info(f"{'='*60}")
    
    for result in test_results:
        logger.info(result)
    
    passed = len([r for r in test_results if 'PASS' in r])
    total = len(test_results)
    success_rate = (passed / total) * 100 if total > 0 else 0
    
    logger.info(f"\nOverall: {passed}/{total} tests passed ({success_rate:.1f}%)")
    
    if success_rate >= 80:
        logger.info("🎉 MCP integration works well with streaming!")
    else:
        logger.warning("⚠️ Some MCP features need attention with streaming")

if __name__ == "__main__":
    asyncio.run(test_mcp_streaming())