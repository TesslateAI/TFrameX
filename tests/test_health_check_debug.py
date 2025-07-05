#!/usr/bin/env python3
"""
Debug enterprise health check issues
"""

import asyncio
import logging
import os
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# TFrameX imports
from tframex import OpenAIChatLLM
from tframex.enterprise import EnterpriseApp, create_default_config

# LLM Configuration
llm = OpenAIChatLLM(
    model_name=os.getenv("OPENAI_MODEL_NAME", "Llama-4-Maverick-17B-128E-Instruct-FP8"),
    api_base_url=os.getenv("OPENAI_API_BASE", "https://api.llama.com/compat/v1/"),
    api_key=os.getenv("OPENAI_API_KEY", "LLM|724781956865705|0pfHARu1VlHMu-wxkjIHDL4KqRU")
)

async def debug_health_check():
    """Debug health check issues."""
    logger.info("Starting health check debug...")
    
    try:
        config = create_default_config(environment="test")
        app = EnterpriseApp(
            default_llm=llm,
            enterprise_config=config,
            auto_initialize=False
        )
        
        await app.initialize_enterprise()
        await app.start_enterprise()
        
        # Get detailed health check
        health = await app.health_check()
        logger.info(f"Full health check result: {health}")
        
        # Check specific components
        if app.enterprise_manager:
            logger.info("Enterprise manager exists")
            
            # Check metrics
            if app.enterprise_manager.metrics_manager:
                logger.info("Metrics manager exists")
                metrics_health = await app.enterprise_manager.metrics_manager.health_check()
                logger.info(f"Metrics health: {metrics_health}")
            else:
                logger.warning("No metrics manager")
            
            # Check storage
            if app.enterprise_manager.storage_manager:
                logger.info("Storage manager exists")
                storage_health = await app.enterprise_manager.storage_manager.health_check()
                logger.info(f"Storage health: {storage_health}")
            else:
                logger.warning("No storage manager")
            
            # Check audit
            if app.enterprise_manager.audit_logger:
                logger.info("Audit logger exists")
                audit_health = await app.enterprise_manager.audit_logger.health_check()
                logger.info(f"Audit health: {audit_health}")
            else:
                logger.warning("No audit logger")
        else:
            logger.warning("No enterprise manager")
        
        await app.stop_enterprise()
        
    except Exception as e:
        logger.error(f"Debug failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_health_check())