#!/usr/bin/env python3
"""
test-project - TFrameX Project

Generated with: tframex setup test-project
"""
import asyncio
import os
from pathlib import Path

from tframex import TFrameXApp
from config.agents import setup_agents
from config.tools import setup_tools


def create_app() -> TFrameXApp:
    """Create and configure the TFrameX application."""
    app = TFrameXApp()
    
    # Setup tools and agents
    setup_tools(app)
    setup_agents(app)
    
    return app


async def main():
    """Main application entry point."""
    print(f"🚀 Starting {project_name}")
    print("=" * 50)
    
    app = create_app()
    
    # Run interactive session
    async with app.run_context() as rt:
        await rt.interactive_chat()


if __name__ == "__main__":
    asyncio.run(main())
