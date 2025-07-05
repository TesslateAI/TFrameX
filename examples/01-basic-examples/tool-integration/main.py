#!/usr/bin/env python3
"""
TFrameX Tool Integration Example

Demonstrates advanced tool integration including:
- External API calls
- Database operations
- Web scraping
- Email sending
- Image processing
- Advanced async operations

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
logger = logging.getLogger("tool-integration")


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
    
    logger.info(f"Tool Integration app initialized with model: {model_name}")
    
    return app


async def demo_api_agent(app: TFrameXApp):
    """Demonstrate the API integration agent."""
    
    logger.info("=== API Integration Agent Demo ===")
    
    async with app.run_context() as rt:
        # Weather API example
        weather_request = Message(
            role="user",
            content="Can you get the current weather for London and tell me if I should bring an umbrella?"
        )
        
        response = await rt.call_agent("APIAgent", weather_request)
        logger.info(f"API Agent (Weather): {response.content}")
        
        # News API example
        news_request = Message(
            role="user",
            content="Get me the latest news about artificial intelligence"
        )
        
        response2 = await rt.call_agent("APIAgent", news_request)
        logger.info(f"API Agent (News): {response2.content}")


async def demo_database_agent(app: TFrameXApp):
    """Demonstrate the database integration agent."""
    
    logger.info("=== Database Integration Agent Demo ===")
    
    async with app.run_context() as rt:
        # Create and populate database
        setup_request = Message(
            role="user",
            content="Create a users table and add some sample data for testing"
        )
        
        response = await rt.call_agent("DatabaseAgent", setup_request)
        logger.info(f"Database Agent (Setup): {response.content}")
        
        # Query data
        query_request = Message(
            role="user",
            content="Show me all users in the database and their information"
        )
        
        response2 = await rt.call_agent("DatabaseAgent", query_request)
        logger.info(f"Database Agent (Query): {response2.content}")


async def demo_web_agent(app: TFrameXApp):
    """Demonstrate the web scraping agent."""
    
    logger.info("=== Web Scraping Agent Demo ===")
    
    async with app.run_context() as rt:
        # Web scraping example
        scrape_request = Message(
            role="user",
            content="Can you scrape the latest Python news from python.org and summarize the key points?"
        )
        
        response = await rt.call_agent("WebAgent", scrape_request)
        logger.info(f"Web Agent: {response.content}")


async def demo_integration_coordinator(app: TFrameXApp):
    """Demonstrate the integration coordinator using multiple tool types."""
    
    logger.info("=== Integration Coordinator Demo ===")
    
    async with app.run_context() as rt:
        # Complex task requiring multiple tools
        complex_request = Message(
            role="user",
            content=(
                "I'm planning a trip to Paris. Can you:\n"
                "1. Get the current weather for Paris\n"
                "2. Find recent news about Paris tourism\n"
                "3. Save this information to a file called 'paris_trip_info.txt'\n"
                "4. Store the trip details in our database"
            )
        )
        
        response = await rt.call_agent("IntegrationCoordinator", complex_request)
        logger.info(f"Integration Coordinator: {response.content}")


async def run_interactive_mode(app: TFrameXApp):
    """Run interactive mode with agent selection."""
    
    agents = [
        "APIAgent", 
        "DatabaseAgent", 
        "WebAgent", 
        "IntegrationCoordinator"
    ]
    
    print("\nAvailable Agents:")
    for i, agent in enumerate(agents, 1):
        print(f"{i}. {agent}")
    
    choice = input("\nSelect an agent (1-4) or press Enter for IntegrationCoordinator: ").strip()
    
    agent_map = {
        "1": "APIAgent",
        "2": "DatabaseAgent",
        "3": "WebAgent",
        "4": "IntegrationCoordinator",
        "": "IntegrationCoordinator"
    }
    
    selected_agent = agent_map.get(choice, "IntegrationCoordinator")
    
    logger.info(f"Starting interactive chat with {selected_agent}")
    
    async with app.run_context() as rt:
        await rt.interactive_chat(default_agent_name=selected_agent)


async def main():
    """Main application entry point."""
    
    try:
        app = create_app()
        
        print("\nTFrameX Tool Integration Example")
        print("================================")
        print("1. API Integration demo")
        print("2. Database Integration demo")
        print("3. Web Scraping demo")
        print("4. Integration Coordinator demo")
        print("5. Run all demos")
        print("6. Interactive chat")
        
        choice = input("\nEnter your choice (1-6): ").strip()
        
        if choice == "1":
            await demo_api_agent(app)
        elif choice == "2":
            await demo_database_agent(app)
        elif choice == "3":
            await demo_web_agent(app)
        elif choice == "4":
            await demo_integration_coordinator(app)
        elif choice == "5":
            await demo_api_agent(app)
            await demo_database_agent(app)
            await demo_web_agent(app)
            await demo_integration_coordinator(app)
        elif choice == "6":
            await run_interactive_mode(app)
        else:
            print("Invalid choice. Running integration coordinator demo...")
            await demo_integration_coordinator(app)
            
    except Exception as e:
        logger.error(f"Application error: {e}")
        raise


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Tool Integration example terminated by user")
    except Exception as e:
        logger.error(f"Unhandled error: {e}")
        exit(1)
    
    logger.info("Tool Integration example completed successfully!")