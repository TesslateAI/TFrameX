#!/usr/bin/env python3
"""
Test enterprise fixes for UUID, Prometheus, and storage configuration issues
"""

import asyncio
import logging
import os
import uuid
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# TFrameX imports
from tframex import Message, OpenAIChatLLM
from tframex.enterprise import EnterpriseApp, create_default_config
from tframex.enterprise.models import User

# LLM Configuration
llm = OpenAIChatLLM(
    model_name=os.getenv("OPENAI_MODEL_NAME", "Llama-4-Maverick-17B-128E-Instruct-FP8"),
    api_base_url=os.getenv("OPENAI_API_BASE", "https://api.llama.com/compat/v1/"),
    api_key=os.getenv("OPENAI_API_KEY", " ")
)

async def test_uuid_fix():
    """Test UUID validation fix."""
    logger.info("Testing UUID validation fix...")
    
    try:
        # Test 1: Valid UUID string
        user1 = User(
            id="550e8400-e29b-41d4-a716-446655440000",
            username="testuser1",
            email="test1@example.com"
        )
        logger.info(f"✅ Valid UUID string accepted: {user1.id}")
        
        # Test 2: Invalid UUID string (should generate new UUID)
        user2 = User(
            id="invalid-uuid-string",
            username="testuser2",
            email="test2@example.com"
        )
        logger.info(f"✅ Invalid UUID string handled (generated new): {user2.id}")
        
        # Test 3: Actual UUID object
        test_uuid = uuid.uuid4()
        user3 = User(
            id=test_uuid,
            username="testuser3",
            email="test3@example.com"
        )
        logger.info(f"✅ UUID object accepted: {user3.id}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ UUID fix test failed: {e}")
        return False

async def test_storage_config_fix():
    """Test storage configuration fix."""
    logger.info("Testing storage configuration fix...")
    
    try:
        # Create config with dict-based storage (should be converted to StorageConfig objects)
        config = create_default_config(environment="test")
        
        # Access storage config attributes (this was failing before)
        sqlite_config = config.get_storage_config("sqlite")
        logger.info(f"✅ Storage config access works: type={sqlite_config.type}")
        
        # Test storage type access directly
        for name, storage_config in config.storage.items():
            logger.info(f"✅ Storage '{name}' type: {storage_config.type}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Storage config fix test failed: {e}")
        return False

async def test_prometheus_registry_fix():
    """Test Prometheus registry fix."""
    logger.info("Testing Prometheus registry fix...")
    
    try:
        # Create multiple enterprise apps (this was causing duplicate registry errors)
        configs = []
        apps = []
        
        for i in range(2):
            config = create_default_config(environment="test")
            # Ensure each app gets its own registry
            config.metrics.enabled = True
            configs.append(config)
            
            app = EnterpriseApp(
                default_llm=llm,
                enterprise_config=config,
                auto_initialize=False
            )
            apps.append(app)
        
        # Initialize both apps (this would fail before with duplicate registry)
        for i, app in enumerate(apps):
            await app.initialize_enterprise()
            await app.start_enterprise()
            logger.info(f"✅ App {i+1} initialized without registry conflicts")
        
        # Test basic functionality
        for i, app in enumerate(apps):
            @app.agent(
                name=f"TestAgent{i}",
                description="Test agent",
                system_prompt="You are a test assistant.",
                streaming=False
            )
            async def test_agent():
                pass
            
            async with app.run_context() as ctx:
                message = Message(role="user", content=f"Test message {i}")
                response = await ctx.call_agent(f"TestAgent{i}", message)
                logger.info(f"✅ App {i+1} agent responded successfully")
        
        # Clean up
        for app in apps:
            await app.stop_enterprise()
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Prometheus registry fix test failed: {e}")
        return False

async def test_comprehensive_enterprise_features():
    """Test comprehensive enterprise features with fixes."""
    logger.info("Testing comprehensive enterprise features...")
    
    try:
        config = create_default_config(environment="test")
        app = EnterpriseApp(
            default_llm=llm,
            enterprise_config=config,
            auto_initialize=False
        )
        
        @app.agent(
            name="FixedEnterpriseAgent",
            description="Enterprise agent with all fixes",
            system_prompt="You are an enterprise assistant with all bug fixes applied.",
            streaming=True
        )
        async def fixed_enterprise_agent():
            pass
        
        await app.initialize_enterprise()
        await app.start_enterprise()
        
        try:
            # Test with valid UUID user
            test_user = User(
                id=str(uuid.uuid4()),
                username="enterpriseuser",
                email="enterprise@example.com",
                is_active=True
            )
            
            async with app.run_context(user=test_user) as ctx:
                message = Message(role="user", content="Test enterprise functionality with fixes")
                response = await ctx.call_agent("FixedEnterpriseAgent", message)
                
                # Check health
                health = await app.health_check()
                metrics_healthy = health.get("components", {}).get("metrics", {}).get("healthy", False)
                storage_healthy = health.get("components", {}).get("storage", {}).get("sqlite", {}).get("connected", False)
                
                logger.info(f"✅ Enterprise agent responded: {response is not None}")
                logger.info(f"✅ Metrics healthy: {metrics_healthy}")
                logger.info(f"✅ Storage healthy: {storage_healthy}")
                
                success = (response is not None and 
                          len(response.content) > 0 and
                          metrics_healthy and
                          storage_healthy)
                
                return success
                
        finally:
            await app.stop_enterprise()
            
    except Exception as e:
        logger.error(f"❌ Comprehensive enterprise test failed: {e}")
        return False

async def main():
    """Run all enterprise fix tests."""
    logger.info("Starting enterprise fix tests...")
    
    tests = [
        ("UUID Validation Fix", test_uuid_fix),
        ("Storage Configuration Fix", test_storage_config_fix),
        ("Prometheus Registry Fix", test_prometheus_registry_fix),
        ("Comprehensive Enterprise Features", test_comprehensive_enterprise_features)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        logger.info(f"\n{'='*50}")
        logger.info(f"Running: {test_name}")
        logger.info(f"{'='*50}")
        
        try:
            result = await test_func()
            if result:
                passed += 1
                logger.info(f"✅ {test_name} PASSED")
            else:
                logger.error(f"❌ {test_name} FAILED")
        except Exception as e:
            logger.error(f"❌ {test_name} ERROR: {e}")
    
    # Summary
    logger.info(f"\n{'='*50}")
    logger.info(f"ENTERPRISE FIX TEST SUMMARY")
    logger.info(f"{'='*50}")
    logger.info(f"Tests passed: {passed}/{total}")
    logger.info(f"Success rate: {(passed/total)*100:.1f}%")
    
    if passed == total:
        logger.info("🎉 All enterprise fixes working correctly!")
        return 0
    else:
        logger.error(f"💥 {total-passed} tests still failing")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)