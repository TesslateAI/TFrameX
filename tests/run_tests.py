#!/usr/bin/env python3
"""
TFrameX Enterprise Test Runner

Simple test runner script that validates enterprise features.
"""

import asyncio
import logging
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load test environment
from dotenv import load_dotenv
load_dotenv(project_root / ".env.test")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_basic_enterprise_setup():
    """Test basic enterprise setup and configuration."""
    logger.info("Testing basic enterprise setup...")
    
    try:
        from tframex.enterprise import EnterpriseApp, create_default_config
        
        # Create default config
        config = create_default_config(environment="test")
        logger.info("✅ Default configuration created")
        
        # Create enterprise app
        app = EnterpriseApp(enterprise_config=config, auto_initialize=False)
        logger.info("✅ Enterprise app created")
        
        # Test initialization
        await app.initialize_enterprise()
        logger.info("✅ Enterprise features initialized")
        
        await app.start_enterprise()
        logger.info("✅ Enterprise services started")
        
        # Test health check
        health = await app.health_check()
        if health["healthy"]:
            logger.info("✅ Health check passed")
        else:
            logger.warning("⚠️ Health check issues detected")
        
        await app.stop_enterprise()
        logger.info("✅ Enterprise services stopped")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Basic setup test failed: {e}")
        return False


async def test_storage_backends():
    """Test storage backend functionality."""
    logger.info("Testing storage backends...")
    
    try:
        from tframex.enterprise.storage.factory import (
            create_storage_backend, get_available_storage_types
        )
        
        # Check available storage types
        available_types = get_available_storage_types()
        logger.info(f"Available storage types: {list(available_types.keys())}")
        
        # Test memory storage
        storage = await create_storage_backend("memory", {})
        
        # Test basic operations
        test_data = {"id": "test123", "name": "test", "value": 42}
        await storage.insert("test_table", test_data)
        
        records = await storage.select("test_table")
        assert len(records) == 1
        assert records[0]["name"] == "test"
        
        logger.info("✅ Storage backend test passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Storage test failed: {e}")
        return False


async def test_metrics_collection():
    """Test metrics collection."""
    logger.info("Testing metrics collection...")
    
    try:
        from tframex.enterprise.metrics.manager import MetricsManager
        
        config = {
            "enabled": True,
            "backends": {
                "test_custom": {
                    "type": "custom",
                    "enabled": True,
                    "backend_class": "tframex.enterprise.metrics.custom.LoggingMetricsBackend",
                    "backend_config": {"log_level": "INFO"}
                }
            },
            "collection_interval": 1,
            "buffer_size": 5
        }
        
        metrics_manager = MetricsManager(config)
        await metrics_manager.start()
        
        # Record some metrics
        await metrics_manager.increment_counter("test.counter", 1)
        await metrics_manager.set_gauge("test.gauge", 100)
        
        # Wait a bit for processing
        await asyncio.sleep(1)
        
        stats = metrics_manager.get_stats()
        assert stats["enabled"]
        assert stats["running"]
        
        await metrics_manager.stop()
        
        logger.info("✅ Metrics collection test passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Metrics test failed: {e}")
        return False


async def test_security_features():
    """Test security features."""
    logger.info("Testing security features...")
    
    try:
        from tframex.enterprise.security.auth import APIKeyProvider
        from tframex.enterprise.security.rbac import RBACEngine
        from tframex.enterprise.storage.factory import create_storage_backend
        from tframex.enterprise.models import User
        from uuid import uuid4
        
        # Test storage
        storage = await create_storage_backend("memory", {})
        
        # Test API key authentication
        auth_config = {"storage": storage, "key_length": 32}
        auth_provider = APIKeyProvider(auth_config)
        await auth_provider.initialize()
        
        # Create test user
        user_id = uuid4()
        test_user_data = {
            "id": str(user_id),
            "username": "testuser",
            "email": "test@example.com",
            "is_active": True
        }
        await storage.insert("users", test_user_data)
        
        # Generate and test API key
        api_key = await auth_provider.create_api_key(user_id)
        auth_result = await auth_provider.authenticate({"api_key": api_key})
        assert auth_result.success
        
        # Test RBAC
        rbac_config = {"storage": storage, "default_role": "user"}
        rbac_engine = RBACEngine(rbac_config)
        await rbac_engine.initialize()
        
        # Create test role
        test_role = await rbac_engine.create_role(
            name="test_role",
            display_name="Test Role",
            description="Test role",
            permissions=["test:read"]
        )
        assert test_role.name == "test_role"
        
        logger.info("✅ Security features test passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Security test failed: {e}")
        return False


async def test_llm_integration():
    """Test LLM integration with environment variables."""
    logger.info("Testing LLM integration...")
    
    try:
        # Check if LLM environment variables are set
        api_key = os.getenv("OPENAI_API_KEY")
        api_base = os.getenv("OPENAI_API_BASE")
        model_name = os.getenv("OPENAI_MODEL_NAME")
        
        if not all([api_key, api_base, model_name]):
            logger.warning("⚠️ LLM environment variables not fully set, skipping LLM test")
            return True
        
        logger.info(f"Using LLM: {model_name} at {api_base}")
        
        # Create OpenAI-compatible LLM
        from tframex.util.llms import OpenAIChatLLM
        
        llm = OpenAIChatLLM(
            model_name=model_name,
            api_key=api_key,
            api_base_url=api_base
        )
        
        # Test enterprise app with real LLM
        from tframex.enterprise import EnterpriseApp, create_default_config
        
        config = create_default_config(environment="test")
        app = EnterpriseApp(
            default_llm=llm,
            enterprise_config=config,
            auto_initialize=False
        )
        
        await app.initialize_enterprise()
        await app.start_enterprise()
        
        try:
            # Register a simple agent
            @app.agent(
                name="test_agent",
                description="Simple test agent",
                system_prompt="You are a helpful test assistant. Respond briefly."
            )
            def test_agent():
                pass
            
            # Test agent call
            async with app.run_context() as ctx:
                response = await ctx.call_agent("test_agent", "Say hello!")
                assert response is not None
                logger.info(f"LLM Response: {response.content[:100]}...")
            
            logger.info("✅ LLM integration test passed")
            return True
            
        finally:
            await app.stop_enterprise()
        
    except Exception as e:
        logger.error(f"❌ LLM integration test failed: {e}")
        return False


async def main():
    """Run all validation tests."""
    logger.info("Starting TFrameX Enterprise validation tests...")
    
    tests = [
        ("Basic Enterprise Setup", test_basic_enterprise_setup),
        ("Storage Backends", test_storage_backends),
        ("Metrics Collection", test_metrics_collection),
        ("Security Features", test_security_features),
        ("LLM Integration", test_llm_integration),
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
    logger.info(f"VALIDATION SUMMARY")
    logger.info(f"{'='*50}")
    logger.info(f"Tests passed: {passed}/{total}")
    logger.info(f"Success rate: {(passed/total)*100:.1f}%")
    
    if passed == total:
        logger.info("🎉 All validation tests passed!")
        return 0
    else:
        logger.error(f"💥 {total-passed} tests failed")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)