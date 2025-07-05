#!/usr/bin/env python3
"""
TFrameX Sequential Pattern Example

Demonstrates step-by-step agent execution where each agent
processes the output of the previous agent in sequence.

Use cases:
- Content creation pipelines
- Data processing workflows
- Multi-stage analysis
- Document review processes

Author: TFrameX Team
License: MIT
"""

import asyncio
import logging
import os
from dotenv import load_dotenv

from tframex import TFrameXApp, OpenAIChatLLM, Message, Flow, SequentialPattern

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("sequential-pattern")


def create_app() -> TFrameXApp:
    """Create and configure the TFrameX application."""
    
    api_key = os.getenv("OPENAI_API_KEY")
    api_base = os.getenv("OPENAI_API_BASE")
    model_name = os.getenv("OPENAI_MODEL_NAME", "gpt-3.5-turbo")
    
    if not api_key or not api_base:
        raise ValueError("Missing required environment configuration")
    
    llm = OpenAIChatLLM(
        model_name=model_name,
        api_base_url=api_base,
        api_key=api_key
    )
    
    app = TFrameXApp(default_llm=llm)
    
    # Define agents for sequential processing
    @app.agent(
        name="ContentPlanner",
        description="Plans content structure and key points",
        system_prompt=(
            "You are a Content Planner. Your job is to analyze the topic and create a structured plan. "
            "Provide:\n"
            "1. Main theme and key message\n"
            "2. Target audience\n"
            "3. Key points to cover\n"
            "4. Suggested structure\n"
            "Keep your output organized and pass it to the next agent."
        )
    )
    async def content_planner():
        pass
    
    @app.agent(
        name="ContentWriter",
        description="Writes content based on the plan",
        system_prompt=(
            "You are a Content Writer. Take the content plan from the previous step and write engaging content. "
            "Follow the structure provided and expand on each key point. "
            "Write in a clear, engaging style appropriate for the target audience. "
            "Create complete, well-structured content."
        )
    )
    async def content_writer():
        pass
    
    @app.agent(
        name="ContentEditor",
        description="Reviews and improves the content",
        system_prompt=(
            "You are a Content Editor. Review the written content and improve it by:\n"
            "1. Checking grammar and style\n"
            "2. Improving clarity and flow\n"
            "3. Ensuring consistency\n"
            "4. Adding polish and refinement\n"
            "Provide the final, publication-ready version."
        )
    )
    async def content_editor():
        pass
    
    # Create sequential flow
    content_flow = Flow(
        flow_name="ContentCreationFlow",
        description="Sequential content creation from planning to final edit"
    )
    
    content_flow.add_step("ContentPlanner")
    content_flow.add_step("ContentWriter") 
    content_flow.add_step("ContentEditor")
    
    app.register_flow(content_flow)
    
    return app


async def demo_content_creation(app: TFrameXApp):
    """Demonstrate sequential content creation."""
    
    logger.info("=== Sequential Content Creation Demo ===")
    
    async with app.run_context() as rt:
        topic = Message(
            role="user",
            content="Create a blog post about the benefits of renewable energy for small businesses"
        )
        
        flow_result = await rt.run_flow("ContentCreationFlow", topic)
        
        print("\n" + "="*60)
        print("FINAL CONTENT:")
        print("="*60)
        print(flow_result.current_message.content)
        print("="*60)


async def demo_step_by_step(app: TFrameXApp):
    """Demonstrate each step individually to show the sequential process."""
    
    logger.info("=== Step-by-Step Sequential Demo ===")
    
    async with app.run_context() as rt:
        topic = "Explain the impact of artificial intelligence on modern healthcare"
        
        # Step 1: Planning
        print("\n🔹 STEP 1: Content Planning")
        print("-" * 40)
        plan_result = await rt.call_agent("ContentPlanner", Message(role="user", content=topic))
        print(plan_result.content)
        
        # Step 2: Writing
        print("\n🔹 STEP 2: Content Writing")
        print("-" * 40)
        write_result = await rt.call_agent("ContentWriter", plan_result)
        print(write_result.content)
        
        # Step 3: Editing
        print("\n🔹 STEP 3: Content Editing")
        print("-" * 40)
        edit_result = await rt.call_agent("ContentEditor", write_result)
        print(edit_result.content)


async def main():
    """Main application entry point."""
    
    try:
        app = create_app()
        
        print("\nTFrameX Sequential Pattern Example")
        print("==================================")
        print("1. Run content creation flow")
        print("2. Show step-by-step process")
        print("3. Interactive chat")
        
        choice = input("\nEnter your choice (1-3): ").strip()
        
        if choice == "1":
            await demo_content_creation(app)
        elif choice == "2":
            await demo_step_by_step(app)
        elif choice == "3":
            async with app.run_context() as rt:
                await rt.interactive_chat(default_agent_name="ContentPlanner")
        else:
            print("Running content creation flow...")
            await demo_content_creation(app)
            
    except Exception as e:
        logger.error(f"Application error: {e}")
        raise


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Sequential Pattern example terminated by user")
    except Exception as e:
        logger.error(f"Unhandled error: {e}")
        exit(1)