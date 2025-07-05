#!/usr/bin/env python3
"""
TFrameX Enterprise Integration Example

This example demonstrates how to integrate and use TFrameX Enterprise
features including metrics, security, and audit logging.
"""

import asyncio
import logging
from pathlib import Path

# TFrameX Enterprise imports
from tframex.enterprise import (
    EnterpriseApp, 
    load_enterprise_config,
    create_default_config
)

# Core TFrameX imports (example LLM)
from tframex.util.llms import BaseLLMWrapper
from tframex.models.primitives import Message

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MockLLM(BaseLLMWrapper):
    """Mock LLM for demonstration purposes."""
    
    def __init__(self):
        super().__init__(model_id="mock-llm")
    
    async def generate_message(self, messages, **kwargs):
        """Generate a mock response."""
        return Message(
            role="assistant",
            content="This is a mock response from the LLM for demonstration purposes."
        )


async def setup_enterprise_app():
    """
    Set up TFrameX Enterprise application with configuration.
    """
    logger.info("Setting up TFrameX Enterprise application...")
    
    # Option 1: Load from configuration file
    config_path = Path(__file__).parent / "enterprise_config.yaml"
    if config_path.exists():
        logger.info(f"Loading configuration from: {config_path}")
        enterprise_config = load_enterprise_config(config_path)
    else:
        # Option 2: Create default configuration
        logger.info("Creating default enterprise configuration")
        enterprise_config = create_default_config(environment="development")
    
    # Create mock LLM
    mock_llm = MockLLM()
    
    # Create enterprise application
    app = EnterpriseApp(
        default_llm=mock_llm,
        enterprise_config=enterprise_config,
        auto_initialize=False  # We'll initialize manually for demonstration
    )
    
    return app


async def demonstrate_enterprise_features(app: EnterpriseApp):
    """
    Demonstrate various enterprise features.
    """
    logger.info("Demonstrating enterprise features...")
    
    # 1. Initialize enterprise features
    logger.info("Initializing enterprise features...")
    await app.initialize_enterprise()
    await app.start_enterprise()
    
    try:
        # 2. Demonstrate storage
        logger.info("Testing storage backend...")
        storage = app.get_storage()
        
        # Create a test user
        test_user_data = {
            "id": "user123",
            "username": "testuser",
            "email": "test@example.com",
            "is_active": True,
            "roles": ["user"]
        }
        
        # Store user data
        await storage.insert("users", test_user_data)
        logger.info("User data stored successfully")
        
        # Retrieve user data
        users = await storage.select("users", filters={"username": "testuser"})
        logger.info(f"Retrieved user data: {users}")
        
        # 3. Demonstrate metrics collection
        logger.info("Testing metrics collection...")
        metrics_manager = app.get_metrics_manager()
        if metrics_manager:
            # Record some metrics
            await metrics_manager.increment_counter(
                "demo.operations.total",
                labels={"operation": "user_creation"}
            )
            
            await metrics_manager.set_gauge(
                "demo.active_users.count",
                1,
                labels={"environment": "demo"}
            )
            
            # Use timer context manager
            async with metrics_manager.timer("demo.operation.duration"):
                await asyncio.sleep(0.1)  # Simulate operation
            
            logger.info("Metrics recorded successfully")
        
        # 4. Demonstrate RBAC
        logger.info("Testing RBAC system...")
        rbac_engine = app.get_rbac_engine()
        if rbac_engine:
            # Create a test role
            test_role = await rbac_engine.create_role(
                name="demo_role",
                display_name="Demo Role",
                description="Role for demonstration",
                permissions=["demo:read", "demo:write"]
            )
            logger.info(f"Created test role: {test_role.name}")
            
            # List all roles
            roles = await rbac_engine.list_roles()
            logger.info(f"Available roles: {[role.name for role in roles]}")
        
        # 5. Demonstrate audit logging
        logger.info("Testing audit logging...")
        audit_logger = app.get_audit_logger()
        if audit_logger:
            # Log some audit events
            await audit_logger.log_event(
                event_type="user_action",
                resource="demo",
                action="create",
                outcome="success",
                details={"demo": "integration_test"}
            )
            logger.info("Audit event logged successfully")
        
        # 6. Demonstrate enterprise runtime context
        logger.info("Testing enterprise runtime context...")
        async with app.run_context() as ctx:
            # Register a simple agent for testing
            @app.agent(
                name="demo_agent",
                description="Demo agent for testing",
                system_prompt="You are a helpful demo assistant."
            )
            def demo_agent(message):
                return f"Demo response to: {message}"
            
            # Call the agent
            response = await ctx.call_agent("demo_agent", "Hello, enterprise!")
            logger.info(f"Agent response: {response}")
        
        # 7. Health check
        logger.info("Performing enterprise health check...")
        health_status = await app.health_check()
        logger.info(f"Health status: {health_status['healthy']}")
        
        if not health_status['healthy']:
            logger.warning("Some enterprise components are unhealthy:")
            for component, status in health_status.get('components', {}).items():
                if not status.get('healthy', True):
                    logger.warning(f"  {component}: {status}")
    
    finally:
        # Clean up
        logger.info("Stopping enterprise services...")
        await app.stop_enterprise()


async def demonstrate_security_features(app: EnterpriseApp):
    """
    Demonstrate security features (requires authentication setup).
    """
    logger.info("Demonstrating security features...")
    
    try:
        # Get security components
        rbac_engine = app.get_rbac_engine()
        audit_logger = app.get_audit_logger()
        
        if not rbac_engine:
            logger.warning("RBAC engine not available")
            return
        
        # Create test user
        from tframex.enterprise.models import User
        from uuid import uuid4
        
        test_user = User(
            id=uuid4(),
            username="demo_user",
            email="demo@example.com",
            is_active=True
        )
        
        # Test permission checking
        has_permission = await rbac_engine.check_permission(
            test_user,
            resource="demo",
            action="read"
        )
        logger.info(f"User has demo:read permission: {has_permission}")
        
        # Assign role to user
        await rbac_engine.assign_role(test_user.id, "user")
        logger.info("Assigned 'user' role to test user")
        
        # Get user permissions
        permissions = await rbac_engine.get_user_permissions(test_user)
        logger.info(f"User permissions: {permissions}")
        
        # Log security event
        if audit_logger:
            await audit_logger.log_event(
                event_type="security_event",
                user_id=test_user.id,
                resource="demo",
                action="permission_check",
                outcome="success",
                details={"permissions_checked": permissions}
            )
            logger.info("Security audit event logged")
    
    except Exception as e:
        logger.error(f"Error demonstrating security features: {e}")


async def main():
    """
    Main demonstration function.
    """
    logger.info("Starting TFrameX Enterprise integration demonstration")
    
    try:
        # Set up enterprise application
        app = await setup_enterprise_app()
        
        # Demonstrate core enterprise features
        await demonstrate_enterprise_features(app)
        
        # Demonstrate security features
        await demonstrate_security_features(app)
        
        logger.info("Enterprise integration demonstration completed successfully!")
    
    except Exception as e:
        logger.error(f"Demonstration failed: {e}", exc_info=True)
        return 1
    
    return 0


if __name__ == "__main__":
    # Run the demonstration
    exit_code = asyncio.run(main())
    exit(exit_code)