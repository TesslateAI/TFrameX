#!/usr/bin/env python3
"""
Test enterprise features with streaming functionality
"""

import asyncio
import logging
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# TFrameX imports
from tframex import TFrameXApp, Message, OpenAIChatLLM
from tframex.enterprise import EnterpriseApp, create_default_config

# LLM Configuration
llm = OpenAIChatLLM(
    model_name=os.getenv("OPENAI_MODEL_NAME", "Llama-4-Maverick-17B-128E-Instruct-FP8"),
    api_base_url=os.getenv("OPENAI_API_BASE", "https://api.llama.com/compat/v1/"),
    api_key=os.getenv("OPENAI_API_KEY", " ")
)

async def test_enterprise_streaming():
    """Test enterprise features with streaming enabled and disabled"""
    logger.info("Testing enterprise features with streaming...")
    
    test_results = []
    
    for streaming in [True, False]:
        mode = "STREAMING" if streaming else "NON-STREAMING"
        logger.info(f"\n{'='*50}")
        logger.info(f"Testing Enterprise {mode} mode")
        logger.info(f"{'='*50}")
        
        # Test 1: Basic enterprise agent with streaming
        try:
            logger.info("1. Testing Basic Enterprise Agent")
            
            config = create_default_config(environment="test")
            app = EnterpriseApp(
                default_llm=llm,
                enterprise_config=config,
                auto_initialize=False
            )
            
            @app.agent(
                name="EnterpriseAgent",
                description="Enterprise test agent",
                system_prompt="You are an enterprise assistant. Provide professional responses.",
                streaming=streaming
            )
            async def enterprise_agent():
                pass
            
            await app.initialize_enterprise()
            await app.start_enterprise()
            
            try:
                async with app.run_context() as ctx:
                    message = Message(role="user", content="Provide a status report")
                    response = await ctx.call_agent("EnterpriseAgent", message)
                    
                    success = response and len(response.content) > 0
                    test_results.append(f"Enterprise Basic Agent {mode}: {'PASS' if success else 'FAIL'}")
                    logger.info(f"Enterprise Basic Agent {mode}: {'PASS' if success else 'FAIL'}")
                    
            finally:
                await app.stop_enterprise()
                
        except Exception as e:
            test_results.append(f"Enterprise Basic Agent {mode}: FAIL - {str(e)}")
            logger.error(f"Enterprise Basic Agent {mode}: FAIL - {str(e)}")
        
        # Test 2: Enterprise agent with authentication context
        try:
            logger.info("2. Testing Enterprise Agent with Auth Context")
            
            config = create_default_config(environment="test")
            app = EnterpriseApp(
                default_llm=llm,
                enterprise_config=config,
                auto_initialize=False
            )
            
            @app.agent(
                name="AuthenticatedAgent",
                description="Authenticated enterprise agent",
                system_prompt="You are an authenticated enterprise assistant. Reference user context when available.",
                streaming=streaming
            )
            async def authenticated_agent():
                pass
            
            await app.initialize_enterprise()
            await app.start_enterprise()
            
            try:
                # Create mock user context
                from tframex.enterprise.models import User
                mock_user = User(
                    id="test-user-123",
                    username="testuser",
                    email="test@example.com",
                    is_active=True
                )
                
                async with app.run_context(user=mock_user) as ctx:
                    message = Message(role="user", content="What services do I have access to?")
                    response = await ctx.call_agent("AuthenticatedAgent", message)
                    
                    success = response and len(response.content) > 0
                    test_results.append(f"Enterprise Auth Agent {mode}: {'PASS' if success else 'FAIL'}")
                    logger.info(f"Enterprise Auth Agent {mode}: {'PASS' if success else 'FAIL'}")
                    
            finally:
                await app.stop_enterprise()
                
        except Exception as e:
            test_results.append(f"Enterprise Auth Agent {mode}: FAIL - {str(e)}")
            logger.error(f"Enterprise Auth Agent {mode}: FAIL - {str(e)}")
        
        # Test 3: Enterprise workflow with multiple agents
        try:
            logger.info("3. Testing Enterprise Workflow")
            
            config = create_default_config(environment="test")
            app = EnterpriseApp(
                default_llm=llm,
                enterprise_config=config,
                auto_initialize=False
            )
            
            @app.agent(
                name="DataProcessor",
                description="Data processing agent",
                system_prompt="You are a data processor. Process and validate data.",
                streaming=streaming
            )
            async def data_processor():
                pass
            
            @app.agent(
                name="ReportGenerator",
                description="Report generation agent",
                system_prompt="You are a report generator. Create professional reports.",
                streaming=streaming
            )
            async def report_generator():
                pass
            
            @app.agent(
                name="WorkflowCoordinator",
                description="Workflow coordinator",
                system_prompt="You are a workflow coordinator. Call other agents to complete workflows.",
                callable_agents=["DataProcessor", "ReportGenerator"],
                streaming=streaming
            )
            async def workflow_coordinator():
                pass
            
            await app.initialize_enterprise()
            await app.start_enterprise()
            
            try:
                async with app.run_context() as ctx:
                    message = Message(role="user", content="Process sales data and generate monthly report")
                    response = await ctx.call_agent("WorkflowCoordinator", message)
                    
                    success = response and len(response.content) > 0
                    test_results.append(f"Enterprise Workflow {mode}: {'PASS' if success else 'FAIL'}")
                    logger.info(f"Enterprise Workflow {mode}: {'PASS' if success else 'FAIL'}")
                    
            finally:
                await app.stop_enterprise()
                
        except Exception as e:
            test_results.append(f"Enterprise Workflow {mode}: FAIL - {str(e)}")
            logger.error(f"Enterprise Workflow {mode}: FAIL - {str(e)}")
        
        # Test 4: Enterprise with metrics and monitoring
        try:
            logger.info("4. Testing Enterprise Metrics")
            
            config = create_default_config(environment="test")
            config.metrics.enabled = True
            app = EnterpriseApp(
                default_llm=llm,
                enterprise_config=config,
                auto_initialize=False
            )
            
            @app.agent(
                name="MetricsAgent",
                description="Agent with metrics",
                system_prompt="You are a metrics-enabled agent. Provide business insights.",
                streaming=streaming
            )
            async def metrics_agent():
                pass
            
            await app.initialize_enterprise()
            await app.start_enterprise()
            
            try:
                async with app.run_context() as ctx:
                    message = Message(role="user", content="Analyze system performance")
                    response = await ctx.call_agent("MetricsAgent", message)
                    
                    # Check if metrics are being collected
                    health = await app.health_check()
                    metrics_working = health.get("metrics", {}).get("enabled", False)
                    
                    success = response and len(response.content) > 0 and metrics_working
                    test_results.append(f"Enterprise Metrics {mode}: {'PASS' if success else 'FAIL'}")
                    logger.info(f"Enterprise Metrics {mode}: {'PASS' if success else 'FAIL'}")
                    
            finally:
                await app.stop_enterprise()
                
        except Exception as e:
            test_results.append(f"Enterprise Metrics {mode}: FAIL - {str(e)}")
            logger.error(f"Enterprise Metrics {mode}: FAIL - {str(e)}")
        
        # Test 5: Enterprise with storage backend
        try:
            logger.info("5. Testing Enterprise Storage")
            
            config = create_default_config(environment="test")
            config.storage.type = "memory"  # Use memory storage for testing
            app = EnterpriseApp(
                default_llm=llm,
                enterprise_config=config,
                auto_initialize=False
            )
            
            @app.agent(
                name="StorageAgent",
                description="Agent with storage access",
                system_prompt="You are a storage-enabled agent. Help with data persistence.",
                streaming=streaming
            )
            async def storage_agent():
                pass
            
            await app.initialize_enterprise()
            await app.start_enterprise()
            
            try:
                async with app.run_context() as ctx:
                    message = Message(role="user", content="Store user preferences")
                    response = await ctx.call_agent("StorageAgent", message)
                    
                    # Check if storage is available
                    health = await app.health_check()
                    storage_working = health.get("storage", {}).get("available", False)
                    
                    success = response and len(response.content) > 0 and storage_working
                    test_results.append(f"Enterprise Storage {mode}: {'PASS' if success else 'FAIL'}")
                    logger.info(f"Enterprise Storage {mode}: {'PASS' if success else 'FAIL'}")
                    
            finally:
                await app.stop_enterprise()
                
        except Exception as e:
            test_results.append(f"Enterprise Storage {mode}: FAIL - {str(e)}")
            logger.error(f"Enterprise Storage {mode}: FAIL - {str(e)}")
    
    # Print summary
    logger.info(f"\n{'='*60}")
    logger.info("ENTERPRISE STREAMING TEST SUMMARY")
    logger.info(f"{'='*60}")
    
    for result in test_results:
        logger.info(result)
    
    passed = len([r for r in test_results if 'PASS' in r])
    total = len(test_results)
    success_rate = (passed / total) * 100 if total > 0 else 0
    
    logger.info(f"\nOverall: {passed}/{total} tests passed ({success_rate:.1f}%)")
    
    if success_rate >= 80:
        logger.info("🎉 Enterprise features work well with streaming!")
    else:
        logger.warning("⚠️ Some enterprise features need attention with streaming")

if __name__ == "__main__":
    asyncio.run(test_enterprise_streaming())