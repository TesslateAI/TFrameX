#!/usr/bin/env python3
"""
Comprehensive Test Suite for TFrameX Enterprise Features

This test suite validates all enterprise components including:
- Storage backends
- Metrics collection
- Security (authentication, authorization, audit)
- Session management
- Integration with core TFrameX
"""

import asyncio
import logging
import os
import tempfile
import unittest
from pathlib import Path
from typing import Dict, Any
from uuid import uuid4

# Load test environment
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env.test")

# Enterprise imports
from tframex.enterprise import (
    EnterpriseApp, EnterpriseConfig, load_enterprise_config,
    create_storage_backend, MetricsManager,
    RBACEngine, SessionManager, AuditLogger,
    User, Role, Permission
)

# Core TFrameX imports
from tframex.util.llms import BaseLLMWrapper
from tframex.models.primitives import Message

# Configure test logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class MockLLM(BaseLLMWrapper):
    """Mock LLM for testing purposes."""
    
    def __init__(self):
        super().__init__(model_id="test-llm")
        self.call_count = 0
    
    async def generate_message(self, messages, **kwargs):
        """Generate a mock response."""
        self.call_count += 1
        return Message(
            role="assistant",
            content=f"Test response #{self.call_count} to your message"
        )


class TestEnterpriseBase(unittest.IsolatedAsyncioTestCase):
    """Base test class with common setup and teardown."""
    
    async def asyncSetUp(self):
        """Set up test environment."""
        # Create temporary directory for test data
        self.test_dir = tempfile.mkdtemp(prefix="tframex_test_")
        self.test_data_dir = Path(self.test_dir)
        
        # Create test configuration
        self.test_config = self._create_test_config()
        
        # Create mock LLM
        self.mock_llm = MockLLM()
        
        logger.info(f"Test setup complete, using directory: {self.test_dir}")
    
    async def asyncTearDown(self):
        """Clean up test environment."""
        # Clean up test directory if requested
        if os.getenv("TFRAMEX_TEST_CLEANUP_ON_EXIT", "true").lower() == "true":
            import shutil
            shutil.rmtree(self.test_dir, ignore_errors=True)
            logger.info(f"Cleaned up test directory: {self.test_dir}")
    
    def _create_test_config(self) -> EnterpriseConfig:
        """Create test enterprise configuration."""
        config_dict = {
            "enabled": True,
            "environment": "test",
            "debug": True,
            
            "storage": {
                "test_sqlite": {
                    "type": "sqlite",
                    "enabled": True,
                    "config": {
                        "database_path": str(self.test_data_dir / "test.db"),
                        "create_tables": True
                    }
                }
            },
            "default_storage": "test_sqlite",
            
            "metrics": {
                "enabled": True,
                "backends": {
                    "test_custom": {
                        "type": "custom",
                        "enabled": True,
                        "backend_class": "tframex.enterprise.metrics.custom.LoggingMetricsBackend",
                        "backend_config": {"log_level": "DEBUG"}
                    }
                },
                "collection_interval": 1,
                "buffer_size": 10
            },
            
            "security": {
                "authentication": {
                    "enabled": True,
                    "providers": {
                        "test_api_key": {
                            "type": "api_key",
                            "enabled": True,
                            "key_length": 32
                        },
                        "test_jwt": {
                            "type": "jwt",
                            "enabled": True,
                            "secret_key": "test-secret-key-123",
                            "expiration": 3600
                        }
                    }
                },
                "authorization": {
                    "enabled": True,
                    "default_role": "test_user",
                    "cache_ttl": 60
                },
                "session": {
                    "enabled": True,
                    "session_timeout": 300,
                    "store_type": "memory"
                },
                "audit": {
                    "enabled": True,
                    "buffer_size": 5,
                    "flush_interval": 1,
                    "retention_days": 1
                }
            }
        }
        
        return EnterpriseConfig(**config_dict)


class TestStorageBackends(TestEnterpriseBase):
    """Test storage backend functionality."""
    
    async def test_sqlite_storage(self):
        """Test SQLite storage backend."""
        logger.info("Testing SQLite storage backend...")
        
        # Create storage backend
        storage_config = {
            "database_path": str(self.test_data_dir / "storage_test.db"),
            "create_tables": True
        }
        
        storage = await create_storage_backend("sqlite", storage_config)
        
        try:
            # Test basic operations
            test_data = {
                "id": str(uuid4()),
                "name": "test_record",
                "value": 42,
                "metadata": {"test": True}
            }
            
            # Insert
            record_id = await storage.insert("test_table", test_data)
            self.assertIsNotNone(record_id)
            
            # Select
            records = await storage.select("test_table", filters={"name": "test_record"})
            self.assertEqual(len(records), 1)
            self.assertEqual(records[0]["name"], "test_record")
            
            # Update
            await storage.update("test_table", record_id, {"value": 84})
            updated_records = await storage.select("test_table", filters={"id": record_id})
            self.assertEqual(updated_records[0]["value"], 84)
            
            # Count
            count = await storage.count("test_table")
            self.assertEqual(count, 1)
            
            # Delete
            await storage.delete("test_table", record_id)
            final_count = await storage.count("test_table")
            self.assertEqual(final_count, 0)
            
            logger.info("SQLite storage test passed")
            
        finally:
            if hasattr(storage, 'close'):
                await storage.close()
    
    async def test_memory_storage(self):
        """Test in-memory storage backend."""
        logger.info("Testing memory storage backend...")
        
        storage = await create_storage_backend("memory", {})
        
        # Test basic operations
        test_data = {"id": "test123", "data": "test_value"}
        
        # Insert and verify
        await storage.insert("memory_test", test_data)
        records = await storage.select("memory_test")
        self.assertEqual(len(records), 1)
        
        # Cleanup
        await storage.delete("memory_test", "test123")
        
        logger.info("Memory storage test passed")


class TestMetricsCollection(TestEnterpriseBase):
    """Test metrics collection system."""
    
    async def test_metrics_manager(self):
        """Test metrics manager functionality."""
        logger.info("Testing metrics manager...")
        
        metrics_config = {
            "enabled": True,
            "backends": {
                "test_custom": {
                    "type": "custom",
                    "enabled": True,
                    "backend_class": "tframex.enterprise.metrics.custom.LoggingMetricsBackend",
                    "backend_config": {"log_level": "DEBUG"}
                }
            },
            "collection_interval": 1,
            "buffer_size": 5
        }
        
        metrics_manager = MetricsManager(metrics_config)
        
        try:
            await metrics_manager.start()
            
            # Test counter
            await metrics_manager.increment_counter(
                "test.counter", 
                value=5,
                labels={"test": "true"}
            )
            
            # Test gauge
            await metrics_manager.set_gauge(
                "test.gauge",
                100.5,
                labels={"component": "test"}
            )
            
            # Test histogram
            await metrics_manager.record_histogram(
                "test.histogram",
                0.25,
                labels={"operation": "test"}
            )
            
            # Test timer
            async with metrics_manager.timer("test.timer"):
                await asyncio.sleep(0.01)
            
            # Wait for metrics to be processed
            await asyncio.sleep(2)
            
            # Verify stats
            stats = metrics_manager.get_stats()
            self.assertTrue(stats["enabled"])
            self.assertTrue(stats["running"])
            self.assertGreater(stats["metrics_collected"], 0)
            
            logger.info("Metrics manager test passed")
            
        finally:
            await metrics_manager.stop()


class TestAuthentication(TestEnterpriseBase):
    """Test authentication system."""
    
    async def test_api_key_authentication(self):
        """Test API key authentication."""
        logger.info("Testing API key authentication...")
        
        from tframex.enterprise.security.auth import APIKeyProvider
        
        # Create mock storage
        storage = await create_storage_backend("memory", {})
        
        # Configure API key provider
        provider_config = {
            "storage": storage,
            "key_length": 32,
            "hash_algorithm": "sha256"
        }
        
        provider = APIKeyProvider(provider_config)
        await provider.initialize()
        
        try:
            # Create test user
            user_id = uuid4()
            test_user = {
                "id": str(user_id),
                "username": "testuser",
                "email": "test@example.com",
                "is_active": True
            }
            await storage.insert("users", test_user)
            
            # Generate API key
            api_key = await provider.create_api_key(user_id)
            self.assertIsNotNone(api_key)
            self.assertEqual(len(api_key), 43)  # Base64 encoded 32 bytes
            
            # Test authentication with API key
            auth_result = await provider.authenticate({"api_key": api_key})
            self.assertTrue(auth_result.success)
            self.assertIsNotNone(auth_result.user)
            self.assertEqual(auth_result.user.username, "testuser")
            
            # Test authentication with invalid key
            invalid_result = await provider.authenticate({"api_key": "invalid_key"})
            self.assertFalse(invalid_result.success)
            
            logger.info("API key authentication test passed")
            
        finally:
            if hasattr(storage, 'close'):
                await storage.close()
    
    async def test_jwt_authentication(self):
        """Test JWT authentication."""
        logger.info("Testing JWT authentication...")
        
        from tframex.enterprise.security.auth import JWTProvider
        
        provider_config = {
            "secret_key": "test-secret-key-12345",
            "algorithm": "HS256",
            "expiration": 3600,
            "issuer": "test"
        }
        
        provider = JWTProvider(provider_config)
        await provider.initialize()
        
        # Create test user
        test_user = User(
            id=uuid4(),
            username="jwtuser",
            email="jwt@example.com",
            is_active=True
        )
        
        # Generate JWT token
        token = provider.generate_token(test_user)
        self.assertIsNotNone(token)
        
        # Validate token
        auth_result = await provider.validate_token(token)
        self.assertTrue(auth_result.success)
        self.assertIsNotNone(auth_result.user)
        self.assertEqual(auth_result.user.username, "jwtuser")
        
        # Test invalid token
        invalid_result = await provider.validate_token("invalid.token.here")
        self.assertFalse(invalid_result.success)
        
        logger.info("JWT authentication test passed")


class TestRBAC(TestEnterpriseBase):
    """Test Role-Based Access Control."""
    
    async def test_rbac_system(self):
        """Test RBAC engine functionality."""
        logger.info("Testing RBAC system...")
        
        # Create storage backend
        storage = await create_storage_backend("memory", {})
        
        # Configure RBAC engine
        rbac_config = {
            "storage": storage,
            "default_role": "test_user",
            "enable_inheritance": True,
            "cache_ttl": 60
        }
        
        rbac_engine = RBACEngine(rbac_config)
        await rbac_engine.initialize()
        
        try:
            # Create test role
            test_role = await rbac_engine.create_role(
                name="test_role",
                display_name="Test Role",
                description="Role for testing",
                permissions=["test:read", "test:write", "test:execute"]
            )
            
            self.assertEqual(test_role.name, "test_role")
            self.assertEqual(len(test_role.permissions), 3)
            
            # Create test user
            test_user = User(
                id=uuid4(),
                username="rbacuser",
                email="rbac@example.com",
                is_active=True
            )
            
            # Store user in storage for RBAC
            await storage.insert("users", test_user.model_dump())
            
            # Assign role to user
            await rbac_engine.assign_role(test_user.id, "test_role")
            
            # Test permission checking
            has_read = await rbac_engine.check_permission(test_user, "test", "read")
            self.assertTrue(has_read)
            
            has_delete = await rbac_engine.check_permission(test_user, "test", "delete")
            self.assertFalse(has_delete)
            
            # Test permission requirement (should pass)
            await rbac_engine.require_permission(test_user, "test", "write")
            
            # Test permission requirement (should fail)
            with self.assertRaises(Exception):
                await rbac_engine.require_permission(test_user, "test", "delete")
            
            # Get user permissions
            permissions = await rbac_engine.get_user_permissions(test_user)
            self.assertIn("test:read", permissions)
            self.assertIn("test:write", permissions)
            
            logger.info("RBAC system test passed")
            
        finally:
            if hasattr(storage, 'close'):
                await storage.close()


class TestSessionManagement(TestEnterpriseBase):
    """Test session management."""
    
    async def test_session_manager(self):
        """Test session manager functionality."""
        logger.info("Testing session management...")
        
        from tframex.enterprise.security.session import SessionManager, MemorySessionStore
        
        # Create session manager with memory store
        session_config = {
            "session_store": MemorySessionStore(),
            "session_timeout": 300,
            "max_sessions_per_user": 3,
            "cleanup_interval": 60
        }
        
        session_manager = SessionManager(session_config)
        await session_manager.start()
        
        try:
            # Create test user
            test_user = User(
                id=uuid4(),
                username="sessionuser",
                email="session@example.com",
                is_active=True
            )
            
            # Create session
            session = await session_manager.create_session(
                test_user,
                data={"test": "session_data"}
            )
            
            self.assertIsNotNone(session)
            self.assertEqual(session.user_id, test_user.id)
            self.assertTrue(session.is_valid)
            
            # Retrieve session
            retrieved_session = await session_manager.get_session(session.session_id)
            self.assertIsNotNone(retrieved_session)
            self.assertEqual(retrieved_session.user_id, test_user.id)
            
            # Update session
            updated = await session_manager.update_session(
                session.session_id,
                {"additional": "data"}
            )
            self.assertTrue(updated)
            
            # Invalidate session
            invalidated = await session_manager.invalidate_session(session.session_id)
            self.assertTrue(invalidated)
            
            # Verify session is gone
            invalid_session = await session_manager.get_session(session.session_id)
            self.assertIsNone(invalid_session)
            
            logger.info("Session management test passed")
            
        finally:
            await session_manager.stop()


class TestAuditLogging(TestEnterpriseBase):
    """Test audit logging system."""
    
    async def test_audit_logger(self):
        """Test audit logger functionality."""
        logger.info("Testing audit logging...")
        
        # Create storage backend
        storage = await create_storage_backend("memory", {})
        
        # Configure audit logger
        audit_config = {
            "storage": storage,
            "enabled": True,
            "buffer_size": 5,
            "flush_interval": 1,
            "retention_days": 1
        }
        
        audit_logger = AuditLogger(audit_config)
        await audit_logger.start()
        
        try:
            # Log various events
            await audit_logger.log_event(
                event_type="authentication",
                user_id=uuid4(),
                action="login",
                outcome="success",
                details={"method": "api_key"}
            )
            
            await audit_logger.log_event(
                event_type="authorization",
                user_id=uuid4(),
                resource="test_resource",
                action="read",
                outcome="success"
            )
            
            await audit_logger.log_event(
                event_type="user_action",
                user_id=uuid4(),
                resource="agent",
                action="call",
                outcome="failure",
                details={"error": "test_error"}
            )
            
            # Wait for events to be flushed
            await asyncio.sleep(2)
            
            # Search for events
            from tframex.enterprise.security.audit import AuditFilter, AuditEventType
            
            filter = AuditFilter(event_types=[AuditEventType.AUTHENTICATION])
            auth_events = await audit_logger.search_events(filter)
            self.assertGreater(len(auth_events), 0)
            
            # Get statistics
            stats = await audit_logger.get_statistics()
            self.assertTrue(stats["enabled"])
            self.assertTrue(stats["running"])
            
            logger.info("Audit logging test passed")
            
        finally:
            await audit_logger.stop()


class TestEnterpriseIntegration(TestEnterpriseBase):
    """Test full enterprise integration."""
    
    async def test_enterprise_app_integration(self):
        """Test complete enterprise application integration."""
        logger.info("Testing enterprise application integration...")
        
        # Create enterprise app
        app = EnterpriseApp(
            default_llm=self.mock_llm,
            enterprise_config=self.test_config,
            auto_initialize=False
        )
        
        try:
            # Initialize enterprise features
            await app.initialize_enterprise()
            await app.start_enterprise()
            
            # Test storage
            storage = app.get_storage()
            self.assertIsNotNone(storage)
            
            # Test metrics
            metrics_manager = app.get_metrics_manager()
            self.assertIsNotNone(metrics_manager)
            
            # Test RBAC
            rbac_engine = app.get_rbac_engine()
            self.assertIsNotNone(rbac_engine)
            
            # Test audit logger
            audit_logger = app.get_audit_logger()
            self.assertIsNotNone(audit_logger)
            
            # Test agent registration and execution
            @app.agent(
                name="test_agent",
                description="Test agent for integration testing",
                system_prompt="You are a test assistant."
            )
            def test_agent(message):
                return f"Test response to: {message}"
            
            # Test enterprise runtime context
            async with app.run_context() as ctx:
                response = await ctx.call_agent("test_agent", "Hello test!")
                self.assertIsNotNone(response)
                
                # Verify LLM was called
                self.assertGreater(self.mock_llm.call_count, 0)
            
            # Test health check
            health = await app.health_check()
            self.assertTrue(health["healthy"])
            self.assertTrue(health["enterprise_enabled"])
            self.assertTrue(health["enterprise_initialized"])
            
            logger.info("Enterprise application integration test passed")
            
        finally:
            await app.stop_enterprise()
    
    async def test_security_integration(self):
        """Test security feature integration."""
        logger.info("Testing security integration...")
        
        app = EnterpriseApp(
            default_llm=self.mock_llm,
            enterprise_config=self.test_config,
            auto_initialize=False
        )
        
        try:
            await app.initialize_enterprise()
            await app.start_enterprise()
            
            # Create test user
            test_user = User(
                id=uuid4(),
                username="integration_user",
                email="integration@example.com",
                is_active=True
            )
            
            # Store user for authentication
            storage = app.get_storage()
            await storage.insert("users", test_user.model_dump())
            
            # Test with security context
            from tframex.enterprise.security.middleware import SecurityContext
            security_context = SecurityContext()
            security_context.user = test_user
            security_context.authenticated = True
            
            async with app.run_context(user=test_user, security_context=security_context) as ctx:
                # This should work with authenticated user
                response = await ctx.call_agent("test_agent", "Secure test!")
                self.assertIsNotNone(response)
            
            logger.info("Security integration test passed")
            
        finally:
            await app.stop_enterprise()


async def run_all_tests():
    """Run all enterprise tests."""
    logger.info("Starting comprehensive enterprise test suite...")
    
    # Create test suite
    test_classes = [
        TestStorageBackends,
        TestMetricsCollection,
        TestAuthentication,
        TestRBAC,
        TestSessionManagement,
        TestAuditLogging,
        TestEnterpriseIntegration
    ]
    
    total_tests = 0
    passed_tests = 0
    failed_tests = 0
    
    for test_class in test_classes:
        logger.info(f"\n{'='*60}")
        logger.info(f"Running {test_class.__name__}")
        logger.info(f"{'='*60}")
        
        # Get test methods
        test_methods = [
            method for method in dir(test_class)
            if method.startswith('test_') and callable(getattr(test_class, method))
        ]
        
        for test_method in test_methods:
            total_tests += 1
            logger.info(f"\nRunning {test_class.__name__}.{test_method}...")
            
            try:
                # Create test instance
                test_instance = test_class()
                await test_instance.asyncSetUp()
                
                try:
                    # Run test method
                    await getattr(test_instance, test_method)()
                    logger.info(f"✅ {test_method} PASSED")
                    passed_tests += 1
                    
                except Exception as e:
                    logger.error(f"❌ {test_method} FAILED: {e}")
                    failed_tests += 1
                    
                finally:
                    await test_instance.asyncTearDown()
                    
            except Exception as e:
                logger.error(f"❌ {test_method} SETUP FAILED: {e}")
                failed_tests += 1
    
    # Print summary
    logger.info(f"\n{'='*60}")
    logger.info(f"TEST SUMMARY")
    logger.info(f"{'='*60}")
    logger.info(f"Total tests: {total_tests}")
    logger.info(f"Passed: {passed_tests}")
    logger.info(f"Failed: {failed_tests}")
    logger.info(f"Success rate: {(passed_tests/total_tests)*100:.1f}%")
    
    return failed_tests == 0


if __name__ == "__main__":
    # Run tests
    success = asyncio.run(run_all_tests())
    exit(0 if success else 1)