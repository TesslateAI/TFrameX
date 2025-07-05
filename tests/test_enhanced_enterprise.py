#!/usr/bin/env python3
"""
Test Enhanced Enterprise Features

Quick test to validate the enhanced enterprise features.
"""

import asyncio
import os
from pathlib import Path

# Load test environment
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent / ".env.test")

async def test_enhanced_features():
    """Test enhanced enterprise features."""
    print("🧪 Testing enhanced enterprise features...")
    
    try:
        # Test imports
        from tframex.enterprise import (
            create_enhanced_enterprise_app,
            create_default_config,
            User,
            WorkflowTracer,
            AnalyticsDashboard
        )
        print("✅ Enhanced imports successful")
        
        # Test configuration
        config = create_default_config(environment="test")
        print("✅ Configuration created")
        
        # Test enhanced app creation
        app = create_enhanced_enterprise_app(
            enterprise_config=config,
            auto_initialize=False
        )
        print("✅ Enhanced enterprise app created")
        
        # Test initialization
        await app.initialize_enterprise()
        print("✅ Enhanced features initialized")
        
        # Test start/stop
        await app.start_enterprise()
        print("✅ Enhanced services started")
        
        await app.stop_enterprise()
        print("✅ Enhanced services stopped")
        
        print("\n🎉 All enhanced enterprise tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Enhanced enterprise test failed: {e}")
        return False

async def main():
    """Run enhanced enterprise tests."""
    success = await test_enhanced_features()
    if success:
        print("\n✅ Enhanced enterprise features are working correctly!")
    else:
        print("\n❌ Enhanced enterprise features have issues!")

if __name__ == "__main__":
    asyncio.run(main())