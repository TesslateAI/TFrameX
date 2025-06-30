#!/usr/bin/env python3
"""
TFrameX Hello World Example

This is the simplest possible TFrameX example demonstrating:
- Basic app setup
- Simple agent creation
- Agent interaction
- Interactive chat mode

Author: TFrameX Team
License: MIT
"""

import asyncio
import logging
import os
from dotenv import load_dotenv

from tframex import TFrameXApp, OpenAIChatLLM, Message
from config.agents import setup_agents

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("hello-world")


def create_app() -> TFrameXApp:
    """Create and configure the TFrameX application."""
    
    # Validate required environment variables
    api_key = os.getenv("OPENAI_API_KEY")
    api_base = os.getenv("OPENAI_API_BASE")
    model_name = os.getenv("OPENAI_MODEL_NAME", "gpt-3.5-turbo")
    
    if not api_key or not api_base:
        logger.error("Missing required environment variables. Please check your .env file.")
        logger.error("Required: OPENAI_API_KEY, OPENAI_API_BASE")
        raise ValueError("Missing required environment configuration")
    
    # Create LLM instance
    llm = OpenAIChatLLM(
        model_name=model_name,
        api_base_url=api_base,
        api_key=api_key
    )
    
    # Initialize TFrameX app
    app = TFrameXApp(default_llm=llm)
    
    # Setup agents
    setup_agents(app)
    
    logger.info(f"TFrameX app initialized with model: {model_name}")
    logger.info(f"API endpoint: {api_base}")
    
    return app


async def run_simple_example(app: TFrameXApp):
    """Run a simple example showing basic agent interaction."""
    
    logger.info("=== Running Simple Example ===")
    
    async with app.run_context() as rt:
        # Single interaction
        user_message = Message(role="user", content="Hello! Nice to meet you.")
        
        logger.info(f"User: {user_message.content}")
        
        response = await rt.call_agent("GreeterAgent", user_message)
        
        logger.info(f"Agent: {response.content}")
        
        # Another interaction with template variables
        logger.info("\n=== Example with Template Variables ===")
        
        template_response = await rt.call_agent(
            "GreeterAgent",
            Message(role="user", content="What's my name?"),
            template_vars={"user_name": "Alice"}
        )
        
        logger.info(f"Agent (with template): {template_response.content}")


async def run_interactive_example(app: TFrameXApp):
    """Run interactive chat mode."""
    
    logger.info("=== Starting Interactive Chat ===")
    logger.info("Type 'exit' or 'quit' to end the conversation")
    
    async with app.run_context() as rt:
        await rt.interactive_chat(default_agent_name="GreeterAgent")


async def main():
    """Main application entry point."""
    
    try:
        # Create the app
        app = create_app()
        
        # Ask user what they want to do
        print("\nTFrameX Hello World Example")
        print("==========================")
        print("1. Run simple example (automated)")
        print("2. Run interactive chat")
        print("3. Run both")
        
        choice = input("\nEnter your choice (1-3): ").strip()
        
        if choice in ["1", "3"]:
            await run_simple_example(app)
        
        if choice in ["2", "3"]:
            print("\n" + "="*50)
            await run_interactive_example(app)
        
        if choice not in ["1", "2", "3"]:
            print("Invalid choice. Running simple example...")
            await run_simple_example(app)
            
    except Exception as e:
        logger.error(f"Application error: {e}")
        raise


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Application terminated by user")
    except Exception as e:
        logger.error(f"Unhandled error: {e}")
        exit(1)
    
    logger.info("Hello World example completed successfully!")