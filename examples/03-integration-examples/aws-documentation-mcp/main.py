#!/usr/bin/env python3
"""
AWS Documentation MCP Integration Example
=========================================

This example demonstrates TFrameX integration with the AWS Documentation MCP Server
to create an intelligent AWS documentation assistant.

Features:
- AWS documentation reading and searching
- Content recommendations
- Service discovery
- Interactive chat interface
"""

import asyncio
import logging
import os
from datetime import datetime
from typing import Dict, Any, Optional

from dotenv import load_dotenv
from tframex import TFrameXApp, OpenAIChatLLM, Message
from tframex.util.logging import setup_logging

# Load environment variables
load_dotenv()

# Configure logging
setup_logging(level=logging.INFO)
logger = logging.getLogger("aws_docs_assistant")

# Configure component logging - add detailed debugging
logging.getLogger("tframex.app").setLevel(logging.INFO)
logging.getLogger("tframex.mcp").setLevel(logging.INFO)
logging.getLogger("tframex.agents").setLevel(logging.DEBUG)
logging.getLogger("tframex.agents.llm_agent").setLevel(logging.DEBUG)
logging.getLogger("tframex.util.llms").setLevel(logging.DEBUG)
logging.getLogger("tframex.util.tools").setLevel(logging.DEBUG)
logging.getLogger("mcp.client").setLevel(logging.WARNING)


class AWSDocumentationAssistant:
    """AWS Documentation Assistant using TFrameX and MCP."""
    
    def __init__(self):
        """Initialize the AWS Documentation Assistant."""
        self.app = None
        self.llm = self._setup_llm()
        
    def _setup_llm(self) -> OpenAIChatLLM:
        """Set up the LLM with credentials from environment variables."""
        api_key = os.getenv("LLAMA_API_KEY")
        if not api_key:
            raise ValueError("LLAMA_API_KEY environment variable is required")
            
        return OpenAIChatLLM(
            model_name=os.getenv("LLAMA_MODEL", "Llama-4-Maverick-17B-128E-Instruct-FP8"),
            api_base_url=os.getenv("LLAMA_BASE_URL", "https://api.llama.com/compat/v1/"),
            api_key=api_key,
            parse_text_tool_calls=True  # Enable text tool call parsing for Llama models
        )
    
    def _setup_app(self) -> TFrameXApp:
        """Set up TFrameX application with MCP integration."""
        app = TFrameXApp(
            default_llm=self.llm,
            mcp_config_file="servers_config.json",
            enable_mcp_roots=True,
            enable_mcp_sampling=True,
            enable_mcp_experimental=False
        )
        
        # Register native tools
        self._register_native_tools(app)
        
        # Register agents
        self._register_agents(app)
        
        return app
    
    def _register_native_tools(self, app: TFrameXApp):
        """Register native TFrameX tools."""
        
        @app.tool(
            name="get_current_time",
            description="Get the current date and time"
        )
        async def get_current_time() -> str:
            """Get current timestamp."""
            return datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
        
        @app.tool(
            name="format_aws_url",
            description="Format AWS documentation URLs for better readability"
        )
        async def format_aws_url(url: str) -> str:
            """Format AWS documentation URL."""
            if "docs.aws.amazon.com" in url:
                parts = url.split("/")
                if len(parts) >= 5:
                    service = parts[4] if len(parts) > 4 else "unknown"
                    return f"📚 AWS {service.upper()} Documentation: {url}"
            return f"🔗 AWS Documentation: {url}"
    
    def _register_agents(self, app: TFrameXApp):
        """Register TFrameX agents."""
        
        @app.agent(
            name="AWSDocsExpert",
            description="Expert AWS documentation assistant with access to official AWS docs",
            system_prompt="""You are an expert AWS documentation assistant with access to AWS documentation tools.

Your approach:
1. Use available tools to help users with AWS-related questions
2. After calling tools, provide a helpful summary or explanation based on the results
3. For "list mcp servers" questions -> use tframex_list_mcp_servers() then explain what servers are available
4. For AWS documentation searches -> use aws_docs__search_documentation() then summarize the findings
5. For time questions -> use get_current_time() then tell the user the current time

IMPORTANT: After calling a tool, always provide a helpful response to the user based on the tool's output.

Available tools: {available_tools_descriptions}""",
            tools=[
                "get_current_time",
                "format_aws_url",
                "tframex_list_mcp_servers",
                "tframex_list_mcp_resources", 
                "tframex_read_mcp_resource",
                "tframex_list_mcp_prompts",
                "tframex_use_mcp_prompt"
            ],
            mcp_tools_from_servers=["aws_docs"],  # Specific server
            strip_think_tags=True,
            tool_choice="auto"  # Allow text responses after tool calls
        )
        async def aws_docs_expert():
            """AWS Documentation Expert agent."""
            pass
        
        @app.agent(
            name="AWSArchitect", 
            description="AWS solutions architect with documentation access",
            system_prompt="""You are an AWS Solutions Architect with deep knowledge of AWS services and architecture patterns. 

Your approach:
1. Use AWS documentation tools to provide accurate, up-to-date information
2. Design well-architected solutions considering the 5 pillars: operational excellence, security, reliability, performance efficiency, and cost optimization
3. When users ask for architecture advice, search relevant AWS documentation first
4. Provide practical, implementable recommendations with explanations

Your capabilities:
- Design AWS architectures and solutions
- Provide best practices and recommendations  
- Access official AWS documentation for accurate information
- Help with service selection and configuration
- Explain AWS concepts and relationships

Guidelines:
- Always base recommendations on official AWS documentation
- Consider the AWS Well-Architected Framework
- Explain the reasoning behind architectural decisions
- Provide specific implementation guidance
- Use aws_docs__search_documentation() for current best practices

Available tools: {available_tools_descriptions}""",
            tools=[
                "get_current_time",
                "format_aws_url",
                "tframex_list_mcp_servers"
            ],
            mcp_tools_from_servers="ALL",  # All MCP servers
            strip_think_tags=True
        )
        async def aws_architect():
            """AWS Solutions Architect agent."""
            pass
    
    async def run_interactive_chat(self):
        """Run interactive chat interface."""
        self.app = self._setup_app()
        
        logger.info("🚀 Starting AWS Documentation Assistant...")
        logger.info("💭 Powered by TFrameX + AWS Documentation MCP Server")
        logger.info("🤖 Using Llama-4-Maverick-17B model")
        
        async with self.app.run_context() as ctx:
            logger.info("✅ AWS Documentation MCP Server connected!")
            logger.info("🎯 Available agents: AWSDocsExpert, AWSArchitect")
            logger.info("📚 Try asking about AWS services, documentation, or architecture!")
            
            print("\n" + "="*70)
            print("🚀 AWS Documentation Assistant")
            print("🔹 Powered by TFrameX + AWS MCP Server + Llama-4-Maverick")
            print("="*70)
            print("\n🎯 Available Agents:")
            print("  • AWSDocsExpert - AWS documentation search and reading")
            print("  • AWSArchitect  - Solutions architecture and best practices")
            print("\n💡 Example queries:")
            print("  • 'Search for S3 bucket policies'")
            print("  • 'Read EC2 instance types documentation'") 
            print("  • 'What are AWS Lambda best practices?'")
            print("  • 'Design a serverless architecture for e-commerce'")
            print("  • 'List available AWS services'")
            print("  • 'What time is it?' (test native tools)")
            print("  • 'list mcp servers' (check MCP integration)")
            print("\n⚡ Commands:")
            print("  • 'exit' or 'quit' - Exit the application")
            print("  • 'switch' - Change between agents")
            print("  • 'help' - Show this help again")
            print("="*70)
            
            await ctx.interactive_chat(default_agent_name="AWSDocsExpert")
        
        logger.info("🛑 Shutting down AWS Documentation Assistant...")
        await self.app.shutdown_mcp_servers()
        logger.info("✅ Shutdown complete!")
    
    async def demo_capabilities(self):
        """Demonstrate AWS Documentation Assistant capabilities."""
        self.app = self._setup_app()
        
        logger.info("🧪 Running AWS Documentation Assistant Demo...")
        
        async with self.app.run_context() as ctx:
            # Demo queries
            demo_queries = [
                "List the available MCP servers",
                "Search for 'S3 bucket naming' in AWS documentation",
                "What AWS services are available?",
            ]
            
            for query in demo_queries:
                print(f"\n🔍 Query: {query}")
                print("-" * 50)
                
                response = await ctx.call_agent(
                    "AWSDocsExpert", 
                    Message(role="user", content=query)
                )
                
                print(f"🤖 Response: {response.content}")
                print("-" * 50)
        
        await self.app.shutdown_mcp_servers()


async def main():
    """Main application entry point."""
    assistant = AWSDocumentationAssistant()
    
    # Check for demo mode
    if "--demo" in os.sys.argv:
        await assistant.demo_capabilities()
    else:
        await assistant.run_interactive_chat()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("👋 Application terminated by user")
    except Exception as e:
        logger.error(f"❌ Application error: {e}", exc_info=True)
    finally:
        logger.info("🏁 Application exiting")