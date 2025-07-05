#!/usr/bin/env python3
"""
Quick test script to verify Redis storage implementation.
"""
import asyncio
import sys
from datetime import datetime

async def test_redis():
    try:
        # Import Redis storage
        from tframex.enterprise.storage.redis import RedisStorage
        print("✅ Redis storage module imported successfully")
        
        # Test configuration
        config = {
            "host": "localhost",
            "port": 6379,
            "db": 15,  # Use test database
            "key_prefix": "test_quick:"
        }
        
        # Create storage instance
        storage = RedisStorage(config)
        print("✅ RedisStorage instance created")
        
        # Initialize storage
        try:
            await storage.initialize()
            print("✅ Redis connection established")
        except Exception as e:
            print(f"❌ Failed to connect to Redis: {e}")
            print("\nMake sure Redis is running locally on port 6379")
            print("You can start Redis with: redis-server")
            return False
        
        try:
            # Test conversation operations
            print("\n🧪 Testing conversation operations...")
            conv_id = f"test_conv_{datetime.now().timestamp()}"
            await storage.store_conversation(conv_id, "test_agent", "test_user", {"test": True})
            conv = await storage.get_conversation(conv_id)
            assert conv is not None
            assert conv["agent_id"] == "test_agent"
            print("✅ Conversation storage works")
            
            # Test message operations
            print("\n🧪 Testing message operations...")
            msg_id = await storage.store_message(conv_id, {
                "role": "user",
                "content": "Hello, Redis!"
            })
            messages = await storage.get_messages(conv_id)
            assert len(messages) == 1
            assert messages[0]["content"] == "Hello, Redis!"
            print("✅ Message storage works")
            
            # Test user/role operations
            print("\n🧪 Testing user/role operations...")
            await storage.store_role("test_role", "Test Role", ["read", "write"])
            await storage.store_user("test_user_id", "testuser", "test@example.com", ["test_role"])
            user = await storage.get_user_by_username("testuser")
            assert user is not None
            assert user["email"] == "test@example.com"
            print("✅ User/Role storage works")
            
            # Test session with TTL
            print("\n🧪 Testing session operations...")
            await storage.store_session("test_session", "test_user_id", {"auth": True}, ttl=5)
            session = await storage.get_session("test_session")
            assert session is not None
            print("✅ Session storage works")
            
            # Test health check
            print("\n🧪 Testing health check...")
            healthy, stats = await storage.health_check()
            assert healthy is True
            print(f"✅ Health check passed - Redis version: {stats.get('redis_version')}")
            
            # Get statistics
            print("\n📊 Storage statistics:")
            stats = await storage.get_statistics()
            for key, value in stats.items():
                if key not in ["memory_usage", "total_commands_processed", "instantaneous_ops_per_sec"]:
                    print(f"  - {key}: {value}")
            
            print("\n✅ All tests passed! Redis storage is working correctly.")
            return True
            
        finally:
            # Cleanup test data
            pattern = storage._key("*")
            keys = await storage.redis.keys(pattern)
            if keys:
                await storage.redis.delete(*keys)
            await storage.cleanup()
            print("\n🧹 Test data cleaned up")
            
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("\nMake sure to install Redis dependencies:")
        print("pip install redis[hiredis]")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 Testing Redis Storage Implementation\n")
    success = asyncio.run(test_redis())
    sys.exit(0 if success else 1)