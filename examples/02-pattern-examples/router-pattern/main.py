#!/usr/bin/env python3
"""
TFrameX Router Pattern Example

Demonstrates intelligent routing where requests are dynamically routed to 
specialized agents based on content analysis. Perfect for handling diverse 
inputs that require different types of expertise.

This example shows:
- Dynamic routing based on content analysis
- Specialized agents for different domains
- Intelligent request classification
- Fallback handling for unmatched requests
"""

import asyncio
import logging
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from tframex import TFrameX, Message, Flow
from tframex.llms import OpenAILLM
from tframex.memory import InMemoryMemoryStore

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize TFrameX app
app = TFrameX(
    default_llm=OpenAILLM(),
    default_memory_store_factory=InMemoryMemoryStore
)

# ===== ROUTING AGENTS =====

@app.agent(
    name="RequestRouter",
    description="Analyzes incoming requests and routes them to appropriate specialist agents",
    system_prompt="""
    You are an intelligent request router. Analyze the incoming request and determine which specialist should handle it:
    
    ROUTING RULES:
    - Technical/coding questions → route to "TechnicalAgent"
    - Creative writing/content → route to "CreativeAgent" 
    - Business/strategy questions → route to "BusinessAgent"
    - Data analysis/math → route to "DataAgent"
    - General questions → route to "GeneralAgent"
    
    Respond with ONLY the agent name that should handle this request.
    If unsure, default to "GeneralAgent".
    
    Examples:
    - "How do I optimize database queries?" → TechnicalAgent
    - "Write a product description" → CreativeAgent
    - "What's our market positioning?" → BusinessAgent
    - "Analyze this data trend" → DataAgent
    - "What's the weather like?" → GeneralAgent
    """
)
async def request_router():
    """Routes requests to appropriate specialist agents."""
    pass

@app.agent(
    name="TechnicalAgent", 
    description="Handles technical and programming-related questions",
    system_prompt="""
    You are a senior technical expert specializing in:
    - Software development and programming
    - System architecture and design
    - Database optimization
    - DevOps and infrastructure
    - Technical problem-solving
    
    Provide detailed, practical technical solutions with code examples when appropriate.
    Focus on best practices, performance, and maintainability.
    """
)
async def technical_agent():
    """Handles technical and programming questions."""
    pass

@app.agent(
    name="CreativeAgent",
    description="Handles creative writing and content creation tasks", 
    system_prompt="""
    You are a creative writing specialist focused on:
    - Content creation and copywriting
    - Creative storytelling
    - Marketing and promotional content
    - Blog posts and articles
    - Creative problem-solving
    
    Produce engaging, well-structured content that captures the right tone and style.
    Be creative, compelling, and audience-focused.
    """
)
async def creative_agent():
    """Handles creative writing and content creation."""
    pass

@app.agent(
    name="BusinessAgent",
    description="Handles business strategy and management questions",
    system_prompt="""
    You are a business strategy consultant specializing in:
    - Strategic planning and analysis
    - Market research and positioning
    - Business development
    - Operations and management
    - Financial planning
    
    Provide strategic insights with practical business recommendations.
    Focus on ROI, market dynamics, and competitive advantages.
    """
)
async def business_agent():
    """Handles business and strategy questions."""
    pass

@app.agent(
    name="DataAgent", 
    description="Handles data analysis and mathematical questions",
    system_prompt="""
    You are a data analysis expert specializing in:
    - Statistical analysis and interpretation
    - Data visualization and insights
    - Mathematical modeling
    - Research methodology
    - Quantitative analysis
    
    Provide clear data-driven insights with proper statistical reasoning.
    Use charts, graphs, and numerical analysis when helpful.
    """
)
async def data_agent():
    """Handles data analysis and mathematical questions."""
    pass

@app.agent(
    name="GeneralAgent",
    description="Handles general questions and fallback scenarios",
    system_prompt="""
    You are a knowledgeable general assistant that can help with:
    - General knowledge questions
    - Basic advice and guidance
    - Information lookup
    - Simple task assistance
    - Fallback support for unclear requests
    
    Provide helpful, accurate information in a friendly and approachable manner.
    If you're not sure about something, be honest about limitations.
    """
)
async def general_agent():
    """Handles general questions and serves as fallback."""
    pass

# ===== ROUTER FLOW =====

# Create the intelligent router flow
router_flow = Flow(
    flow_name="IntelligentRouterFlow",
    description="Routes requests to specialized agents based on content analysis"
)

# Add routing step - first determine which agent to use
router_flow.add_step("RequestRouter")

# The routing logic will be handled in the flow execution
app.register_flow(router_flow)

# ===== DEMO FUNCTIONS =====

async def demo_router_flow():
    """Demonstrate the router pattern with various types of requests."""
    print("🔀 TFrameX Router Pattern Demo")
    print("=" * 50)
    
    # Example requests that should be routed to different agents
    test_requests = [
        "How can I optimize my PostgreSQL database queries for better performance?",
        "Write a compelling product description for a new AI-powered fitness app",
        "What market research should we do before launching in Asia?", 
        "Analyze the correlation between these sales figures and marketing spend",
        "What's the best way to stay productive while working from home?"
    ]
    
    async with app.run_context() as rt:
        for i, request in enumerate(test_requests, 1):
            print(f"\n📝 Request {i}: {request}")
            print("-" * 60)
            
            # First, get routing decision
            router_input = Message(role="user", content=request)
            router_result = await rt.call_agent("RequestRouter", router_input)
            selected_agent = router_result.current_message.content.strip()
            
            print(f"🎯 Routed to: {selected_agent}")
            
            # Then call the selected agent
            agent_result = await rt.call_agent(selected_agent, router_input)
            print(f"💬 Response: {agent_result.current_message.content[:200]}...")
            print()

async def demo_individual_routing():
    """Show individual routing decisions."""
    print("\n🔍 Individual Routing Analysis")
    print("=" * 50)
    
    requests = [
        "Fix this Python error: 'list index out of range'",
        "Create a social media campaign for our new product launch",
        "Should we expand into international markets this quarter?",
        "Calculate the mean and standard deviation of this dataset",
        "What's a good recipe for chocolate chip cookies?"
    ]
    
    async with app.run_context() as rt:
        for request in requests:
            router_input = Message(role="user", content=request)
            result = await rt.call_agent("RequestRouter", router_input)
            selected_agent = result.current_message.content.strip()
            
            print(f"📝 '{request[:50]}...'")
            print(f"   ➡️  Routed to: {selected_agent}")
            print()

async def demo_interactive_chat():
    """Interactive chat with automatic routing."""
    print("\n💬 Interactive Router Chat")
    print("=" * 50)
    print("Ask any question and watch it get routed to the right specialist!")
    print("Type 'quit' to exit.\n")
    
    async with app.run_context() as rt:
        while True:
            user_input = input("You: ").strip()
            if user_input.lower() in ['quit', 'exit', 'q']:
                break
                
            if not user_input:
                continue
                
            try:
                # Route the request
                router_input = Message(role="user", content=user_input)
                router_result = await rt.call_agent("RequestRouter", router_input)
                selected_agent = router_result.current_message.content.strip()
                
                print(f"🎯 Routing to: {selected_agent}")
                
                # Get response from selected agent
                agent_result = await rt.call_agent(selected_agent, router_input)
                print(f"{selected_agent}: {agent_result.current_message.content}\n")
                
            except Exception as e:
                print(f"❌ Error: {e}\n")

# ===== MAIN DEMO =====

async def main():
    """Main demo function with user choices."""
    print("🔀 TFrameX Router Pattern Example")
    print("=" * 50)
    print("This example demonstrates intelligent request routing")
    print("where different types of requests are automatically")
    print("routed to specialized expert agents.\n")
    
    while True:
        print("Choose a demo:")
        print("1. 🔀 Router Flow Demo (automated routing)")
        print("2. 🔍 Individual Routing Analysis")
        print("3. 💬 Interactive Chat with Routing")
        print("4. ❌ Exit")
        
        choice = input("\nEnter your choice (1-4): ").strip()
        
        if choice == "1":
            await demo_router_flow()
        elif choice == "2":
            await demo_individual_routing()
        elif choice == "3":
            await demo_interactive_chat()
        elif choice == "4":
            print("👋 Goodbye!")
            break
        else:
            print("❌ Invalid choice. Please try again.\n")

if __name__ == "__main__":
    asyncio.run(main())