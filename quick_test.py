#!/usr/bin/env python3
"""
Quick Enterprise Feature Validation
"""

import asyncio
import os
from pathlib import Path

# Load test environment
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent / ".env.test")

async def test_storage():
    """Test basic storage functionality."""
    print("Testing storage...")
    try:
        from tframex.enterprise.storage.factory import create_storage_backend
        
        # Test memory storage
        storage = await create_storage_backend("memory", {})
        
        # Insert test record
        record_id = await storage.insert("test_table", {
            "name": "test",
            "value": 123
        })
        print(f"✅ Inserted record: {record_id}")
        
        # Select records
        records = await storage.select("test_table")
        print(f"✅ Retrieved {len(records)} records")
        
        await storage.disconnect()
        return True
        
    except Exception as e:
        print(f"❌ Storage test failed: {e}")
        return False

async def test_metrics():
    """Test basic metrics functionality."""
    print("Testing metrics...")
    try:
        from tframex.enterprise.metrics.manager import MetricsManager
        
        config = {
            "enabled": True,
            "backends": {
                "test_custom": {
                    "type": "custom",
                    "enabled": True,
                    "backend_class": "tframex.enterprise.metrics.custom.LoggingMetricsBackend",
                    "backend_config": {}
                }
            }
        }
        
        manager = MetricsManager(config)
        await manager.start()
        
        # Record some metrics
        await manager.increment_counter("test.counter", value=1)
        await manager.set_gauge("test.gauge", value=100)
        
        await manager.stop()
        print("✅ Metrics test passed")
        return True
        
    except Exception as e:
        print(f"❌ Metrics test failed: {e}")
        return False

async def test_enterprise_app():
    """Test enterprise app creation."""
    print("Testing enterprise app...")
    try:
        from tframex.enterprise import EnterpriseApp, create_default_config
        
        config = create_default_config(environment="test")
        app = EnterpriseApp(enterprise_config=config, auto_initialize=False)
        
        print("✅ Enterprise app created")
        return True
        
    except Exception as e:
        print(f"❌ Enterprise app test failed: {e}")
        return False

async def main():
    """Run quick validation tests."""
    print("🚀 Starting quick enterprise validation...\n")
    
    tests = [
        ("Storage", test_storage),
        ("Metrics", test_metrics),
        ("Enterprise App", test_enterprise_app),
    ]
    
    results = []
    for name, test_func in tests:
        print(f"Testing {name}...")
        try:
            result = await asyncio.wait_for(test_func(), timeout=10.0)
            results.append(result)
        except asyncio.TimeoutError:
            print(f"❌ {name} test timed out")
            results.append(False)
        except Exception as e:
            print(f"❌ {name} test error: {e}")
            results.append(False)
        print()
    
    passed = sum(results)
    total = len(results)
    print(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All quick tests passed!")
    else:
        print("⚠️  Some tests failed")

if __name__ == "__main__":
    asyncio.run(main())