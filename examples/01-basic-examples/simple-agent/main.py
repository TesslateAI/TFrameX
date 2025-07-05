#!/usr/bin/env python3
"""
TFrameX Simple Agent Example

Demonstrates agents with tools, memory, and sophisticated interactions.

Features:
- Multiple agents with different specializations
- Tool integration and execution
- Memory management
- Template variables
- Error handling

Author: TFrameX Team
License: MIT
"""

import asyncio
import logging
import os
from dotenv import load_dotenv

from tframex import TFrameXApp, OpenAIChatLLM, Message
from config.agents import setup_agents
from config.tools import setup_tools

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("simple-agent")


def create_app() -> TFrameXApp:
    """Create and configure the TFrameX application."""
    
    # Validate environment
    api_key = os.getenv("OPENAI_API_KEY")
    api_base = os.getenv("OPENAI_API_BASE")
    model_name = os.getenv("OPENAI_MODEL_NAME", "gpt-3.5-turbo")
    
    if not api_key or not api_base:
        logger.error("Missing required environment variables. Check your .env file.")
        raise ValueError("Missing required environment configuration")
    
    # Create LLM instance
    llm = OpenAIChatLLM(
        model_name=model_name,
        api_base_url=api_base,
        api_key=api_key
    )
    
    # Initialize TFrameX app
    app = TFrameXApp(default_llm=llm)
    
    # Setup tools and agents
    setup_tools(app)
    setup_agents(app)
    
    logger.info(f"Simple Agent app initialized with model: {model_name}")
    
    return app


async def demo_calculator_agent(app: TFrameXApp):
    """Demonstrate the calculator agent with math tools."""
    
    logger.info("=== Calculator Agent Demo ===")
    
    async with app.run_context() as rt:
        # Simple calculation
        calc_request = Message(
            role="user", 
            content="Please calculate 25 * 8 + 47 and save the result"
        )
        
        response = await rt.call_agent("CalculatorAgent", calc_request)
        logger.info(f"Calculator: {response.content}")
        
        # Follow-up question
        followup = Message(
            role="user",
            content="What was the result of the previous calculation?"
        )
        
        response2 = await rt.call_agent("CalculatorAgent", followup)
        logger.info(f"Calculator (memory): {response2.content}")


async def demo_file_manager_agent(app: TFrameXApp):
    """Demonstrate the file manager agent with file operations."""
    
    logger.info("=== File Manager Agent Demo ===")
    
    async with app.run_context() as rt:
        # File operations
        file_request = Message(
            role="user",
            content="Create a file called 'demo.txt' with the content 'Hello from TFrameX!' and then read it back"
        )
        
        response = await rt.call_agent("FileManagerAgent", file_request)
        logger.info(f"File Manager: {response.content}")
        
        # List files
        list_request = Message(
            role="user",
            content="List all files in the current directory"
        )
        
        response2 = await rt.call_agent("FileManagerAgent", list_request)
        logger.info(f"File Manager (list): {response2.content}")


async def demo_personal_assistant(app: TFrameXApp):
    """Demonstrate the personal assistant with memory and personalization."""
    
    logger.info("=== Personal Assistant Demo ===")
    
    async with app.run_context() as rt:
        # Introduction with template variables
        intro = Message(
            role="user",
            content="Hi, I'm new here. Can you help me?"
        )
        
        response = await rt.call_agent(
            "PersonalAssistant",
            intro,
            template_vars={"user_name": "Alice", "user_role": "Developer"}
        )
        logger.info(f"Assistant: {response.content}")
        
        # Task with tools
        task = Message(
            role="user",
            content="I need to calculate my weekly budget. I earn $5000 per month and spend $1200 on rent, $400 on food, and $200 on utilities. What's left for savings?"
        )
        
        response2 = await rt.call_agent("PersonalAssistant", task)
        logger.info(f"Assistant (calculation): {response2.content}")


async def run_interactive_mode(app: TFrameXApp):
    """Run interactive mode with agent selection."""
    
    agents = ["CalculatorAgent", "FileManagerAgent", "PersonalAssistant"]
    
    print("\nAvailable Agents:")
    for i, agent in enumerate(agents, 1):
        print(f"{i}. {agent}")
    
    choice = input("\nSelect an agent (1-3) or press Enter for PersonalAssistant: ").strip()
    
    agent_map = {
        "1": "CalculatorAgent",
        "2": "FileManagerAgent", 
        "3": "PersonalAssistant",
        "": "PersonalAssistant"
    }
    
    selected_agent = agent_map.get(choice, "PersonalAssistant")
    
    logger.info(f"Starting interactive chat with {selected_agent}")
    
    async with app.run_context() as rt:
        await rt.interactive_chat(default_agent_name=selected_agent)


async def main():
    """Main application entry point."""
    
    try:
        app = create_app()
        
        print("\nTFrameX Simple Agent Example")
        print("============================")
        print("1. Run calculator demo")
        print("2. Run file manager demo")
        print("3. Run personal assistant demo")
        print("4. Run all demos")
        print("5. Interactive chat")
        
        choice = input("\nEnter your choice (1-5): ").strip()
        
        if choice == "1":
            await demo_calculator_agent(app)
        elif choice == "2":
            await demo_file_manager_agent(app)
        elif choice == "3":
            await demo_personal_assistant(app)
        elif choice == "4":
            await demo_calculator_agent(app)
            await demo_file_manager_agent(app)
            await demo_personal_assistant(app)
        elif choice == "5":
            await run_interactive_mode(app)
        else:
            print("Invalid choice. Running all demos...")
            await demo_calculator_agent(app)
            await demo_file_manager_agent(app)
            await demo_personal_assistant(app)
            
    except Exception as e:
        logger.error(f"Application error: {e}")
        raise


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Simple Agent example terminated by user")
    except Exception as e:
        logger.error(f"Unhandled error: {e}")
        exit(1)
    
    logger.info("Simple Agent example completed successfully!")