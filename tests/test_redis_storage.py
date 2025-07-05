"""
Tests for Redis storage backend.

Tests all Redis storage operations including:
- Connection management
- CRUD operations
- TTL functionality
- Health checks
- Data migration
"""
import asyncio
import json
import os
import pytest
from datetime import datetime, timezone
from typing import Dict, Any

# Skip tests if redis is not installed
try:
    import redis.asyncio as redis
    from tframex.enterprise.storage.redis import RedisStorage
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

# Test configuration
TEST_REDIS_CONFIG = {
    "host": os.getenv("TEST_REDIS_HOST", "localhost"),
    "port": int(os.getenv("TEST_REDIS_PORT", 6379)),
    "db": int(os.getenv("TEST_REDIS_DB", 15)),  # Use DB 15 for tests
    "password": os.getenv("TEST_REDIS_PASSWORD"),
    "key_prefix": "test_tframex:",
    "ttl": {
        "sessions": 2,  # 2 seconds for testing
        "temp_data": 1  # 1 second for testing
    }
}


@pytest.mark.skipif(not REDIS_AVAILABLE, reason="Redis not installed")
class TestRedisStorage:
    """Test suite for Redis storage backend."""
    
    @pytest.fixture
    async def storage(self):
        """Create a Redis storage instance for testing."""
        storage = RedisStorage(TEST_REDIS_CONFIG)
        await storage.initialize()
        
        # Clean up any existing test data
        pattern = storage._key("*")
        keys = await storage.redis.keys(pattern)
        if keys:
            await storage.redis.delete(*keys)
        
        yield storage
        
        # Cleanup after test
        pattern = storage._key("*")
        keys = await storage.redis.keys(pattern)
        if keys:
            await storage.redis.delete(*keys)
        
        await storage.cleanup()
    
    @pytest.mark.asyncio
    async def test_initialization(self, storage):
        """Test Redis storage initialization."""
        assert storage.redis is not None
        assert storage.pool is not None
        
        # Test connection
        pong = await storage.redis.ping()
        assert pong is True
        
        # Check meta keys
        version = await storage.redis.get(storage._key("meta", "version"))
        assert version == "1.0"
    
    @pytest.mark.asyncio
    async def test_conversation_operations(self, storage):
        """Test conversation CRUD operations."""
        # Store conversation
        conv_id = "test_conv_123"
        agent_id = "test_agent"
        user_id = "test_user"
        metadata = {"source": "test", "priority": "high"}
        
        await storage.store_conversation(conv_id, agent_id, user_id, metadata)
        
        # Retrieve conversation
        conv = await storage.get_conversation(conv_id)
        assert conv is not None
        assert conv["conversation_id"] == conv_id
        assert conv["agent_id"] == agent_id
        assert conv["user_id"] == user_id
        assert conv["metadata"] == metadata
        
        # List conversations by user
        user_convs = await storage.list_conversations(user_id=user_id)
        assert len(user_convs) == 1
        assert user_convs[0]["conversation_id"] == conv_id
        
        # List conversations by agent
        agent_convs = await storage.list_conversations(agent_id=agent_id)
        assert len(agent_convs) == 1
        assert agent_convs[0]["conversation_id"] == conv_id
    
    @pytest.mark.asyncio
    async def test_message_operations(self, storage):
        """Test message storage and retrieval."""
        conv_id = "test_conv_456"
        await storage.store_conversation(conv_id, "agent1", "user1")
        
        # Store multiple messages
        messages = []
        for i in range(5):
            message = {
                "role": "user" if i % 2 == 0 else "assistant",
                "content": f"Test message {i}",
                "metadata": {"index": i}
            }
            msg_id = await storage.store_message(conv_id, message)
            message["id"] = msg_id
            messages.append(message)
            
            # Add small delay to ensure different timestamps
            await asyncio.sleep(0.01)
        
        # Retrieve messages
        retrieved = await storage.get_messages(conv_id)
        assert len(retrieved) == 5
        
        # Check order (should be oldest first)
        for i, msg in enumerate(retrieved):
            assert msg["content"] == f"Test message {i}"
            assert msg["metadata"]["index"] == i
        
        # Test pagination
        paginated = await storage.get_messages(conv_id, limit=2, offset=1)
        assert len(paginated) == 2
        assert paginated[0]["content"] == "Test message 1"
        assert paginated[1]["content"] == "Test message 2"
    
    @pytest.mark.asyncio
    async def test_flow_operations(self, storage):
        """Test flow execution storage."""
        flow_id = "test_flow_789"
        flow_name = "TestFlow"
        
        # Store successful flow execution
        await storage.store_flow_execution(
            flow_id=flow_id,
            flow_name=flow_name,
            status="completed",
            result={"output": "Success", "metrics": {"duration": 1.5}},
            metadata={"triggered_by": "test"}
        )
        
        # Retrieve flow execution
        flow = await storage.get_flow_execution(flow_id)
        assert flow is not None
        assert flow["flow_id"] == flow_id
        assert flow["flow_name"] == flow_name
        assert flow["status"] == "completed"
        assert flow["result"]["output"] == "Success"
        assert flow["metadata"]["triggered_by"] == "test"
        
        # Store failed flow execution
        error_flow_id = "test_flow_error"
        await storage.store_flow_execution(
            flow_id=error_flow_id,
            flow_name=flow_name,
            status="failed",
            error="Test error message"
        )
        
        error_flow = await storage.get_flow_execution(error_flow_id)
        assert error_flow["status"] == "failed"
        assert error_flow["error"] == "Test error message"
    
    @pytest.mark.asyncio
    async def test_audit_logging(self, storage):
        """Test audit log operations."""
        # Store audit logs
        for i in range(3):
            await storage.store_audit_log(
                event_type="test_event",
                user_id=f"user_{i}",
                resource_type="conversation",
                resource_id=f"conv_{i}",
                action="create",
                details={"test": True, "index": i},
                ip_address="127.0.0.1",
                user_agent="TestAgent/1.0"
            )
            await asyncio.sleep(0.01)
        
        # Retrieve all audit logs
        logs = await storage.get_audit_logs()
        assert len(logs) >= 3
        
        # Filter by user
        user_logs = await storage.get_audit_logs(user_id="user_1")
        assert len(user_logs) == 1
        assert user_logs[0]["user_id"] == "user_1"
        
        # Filter by event type
        event_logs = await storage.get_audit_logs(event_type="test_event")
        assert len(event_logs) >= 3
        assert all(log["event_type"] == "test_event" for log in event_logs)
    
    @pytest.mark.asyncio
    async def test_user_role_operations(self, storage):
        """Test user and role management."""
        # Store role
        role_id = "test_role_admin"
        await storage.store_role(
            role_id=role_id,
            role_name="Test Admin",
            permissions=["read", "write", "delete"],
            metadata={"description": "Test admin role"}
        )
        
        # Retrieve role
        role = await storage.get_role(role_id)
        assert role is not None
        assert role["role_name"] == "Test Admin"
        assert "write" in role["permissions"]
        
        # Store user
        user_id = "test_user_123"
        username = "testuser"
        email = "test@example.com"
        
        await storage.store_user(
            user_id=user_id,
            username=username,
            email=email,
            role_ids=[role_id],
            metadata={"department": "Testing"}
        )
        
        # Retrieve user
        user = await storage.get_user(user_id)
        assert user is not None
        assert user["username"] == username
        assert user["email"] == email
        assert role_id in user["role_ids"]
        
        # Retrieve by username
        user_by_name = await storage.get_user_by_username(username)
        assert user_by_name is not None
        assert user_by_name["user_id"] == user_id
    
    @pytest.mark.asyncio
    async def test_session_management(self, storage):
        """Test session storage with TTL."""
        session_id = "test_session_123"
        user_id = "test_user"
        session_data = {
            "auth_token": "test_token",
            "permissions": ["read", "write"],
            "metadata": {"login_time": datetime.now(timezone.utc).isoformat()}
        }
        
        # Store session with short TTL
        await storage.store_session(session_id, user_id, session_data, ttl=2)
        
        # Retrieve immediately
        session = await storage.get_session(session_id)
        assert session is not None
        assert session["user_id"] == user_id
        assert session["data"]["auth_token"] == "test_token"
        
        # Wait for TTL to expire
        await asyncio.sleep(3)
        
        # Session should be expired
        expired_session = await storage.get_session(session_id)
        assert expired_session is None
        
        # Test session deletion
        await storage.store_session("delete_test", user_id, {"test": True})
        await storage.delete_session("delete_test")
        deleted = await storage.get_session("delete_test")
        assert deleted is None
    
    @pytest.mark.asyncio
    async def test_health_check(self, storage):
        """Test health check functionality."""
        healthy, stats = await storage.health_check()
        
        assert healthy is True
        assert stats["status"] == "healthy"
        assert "redis_version" in stats
        assert "connected_clients" in stats
        assert "total_keys" in stats
    
    @pytest.mark.asyncio
    async def test_statistics(self, storage):
        """Test statistics gathering."""
        # Create some test data
        await storage.store_conversation("stat_conv", "agent1", "user1")
        await storage.store_user("stat_user", "statuser", "stat@test.com", [])
        await storage.store_role("stat_role", "StatRole", ["read"])
        await storage.store_session("stat_session", "stat_user", {"test": True})
        
        # Get statistics
        stats = await storage.get_statistics()
        
        assert stats["conversations"] >= 1
        assert stats["users"] >= 1
        assert stats["roles"] >= 1
        assert stats["active_sessions"] >= 1
        assert "memory_usage" in stats
    
    @pytest.mark.asyncio
    async def test_export_import(self, storage, tmp_path):
        """Test data export and import."""
        # Create test data
        await storage.store_role("export_role", "ExportRole", ["read"])
        await storage.store_user("export_user", "exportuser", "export@test.com", ["export_role"])
        await storage.store_conversation("export_conv", "agent1", "export_user")
        await storage.store_message("export_conv", {"content": "Export test"})
        
        # Export data
        export_file = tmp_path / "export.json"
        await storage.export_data(str(export_file))
        
        assert export_file.exists()
        
        # Read exported data
        with open(export_file, 'r') as f:
            exported = json.load(f)
        
        assert len(exported["roles"]) >= 1
        assert len(exported["users"]) >= 1
        assert len(exported["conversations"]) >= 1
        assert len(exported["messages"]) >= 1
        
        # Clear data
        pattern = storage._key("*")
        keys = await storage.redis.keys(pattern)
        if keys:
            await storage.redis.delete(*keys)
        
        # Import data back
        await storage.import_data(str(export_file))
        
        # Verify imported data
        role = await storage.get_role("export_role")
        assert role is not None
        assert role["role_name"] == "ExportRole"
        
        user = await storage.get_user("export_user")
        assert user is not None
        assert user["username"] == "exportuser"
        
        conv = await storage.get_conversation("export_conv")
        assert conv is not None
        assert conv["agent_id"] == "agent1"
    
    @pytest.mark.asyncio
    async def test_concurrent_operations(self, storage):
        """Test concurrent operations for thread safety."""
        # Create multiple conversations concurrently
        tasks = []
        for i in range(10):
            task = storage.store_conversation(
                f"concurrent_conv_{i}",
                f"agent_{i % 3}",
                f"user_{i % 5}"
            )
            tasks.append(task)
        
        await asyncio.gather(*tasks)
        
        # Verify all conversations were created
        all_convs = await storage.list_conversations()
        concurrent_convs = [c for c in all_convs if c["conversation_id"].startswith("concurrent_conv_")]
        assert len(concurrent_convs) == 10
    
    @pytest.mark.asyncio
    async def test_error_handling(self, storage):
        """Test error handling in various scenarios."""
        # Test getting non-existent data
        none_conv = await storage.get_conversation("non_existent")
        assert none_conv is None
        
        none_user = await storage.get_user("non_existent")
        assert none_user is None
        
        none_role = await storage.get_role("non_existent")
        assert none_role is None
        
        none_flow = await storage.get_flow_execution("non_existent")
        assert none_flow is None
        
        # Test empty message list
        empty_messages = await storage.get_messages("non_existent_conv")
        assert empty_messages == []


@pytest.mark.skipif(not REDIS_AVAILABLE, reason="Redis not installed")
class TestRedisIntegration:
    """Integration tests for Redis storage with other components."""
    
    @pytest.mark.asyncio
    async def test_with_enterprise_app(self):
        """Test Redis storage integration with enterprise app."""
        from tframex.enterprise.app import EnterpriseApp
        from tframex.enterprise.config import EnterpriseConfig
        
        # Create enterprise config with Redis storage
        config = EnterpriseConfig({
            "storage": {
                "type": "redis",
                "config": TEST_REDIS_CONFIG
            }
        })
        
        # Create enterprise app
        app = EnterpriseApp(config=config)
        
        try:
            # Initialize app (which initializes storage)
            await app.initialize()
            
            # Verify storage is Redis
            assert isinstance(app.storage, RedisStorage)
            
            # Test basic operation through app
            storage = app.storage
            await storage.store_conversation("app_test_conv", "agent1", "user1")
            conv = await storage.get_conversation("app_test_conv")
            assert conv is not None
            
        finally:
            await app.cleanup()


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])