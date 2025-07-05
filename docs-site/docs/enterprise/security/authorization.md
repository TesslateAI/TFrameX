---
sidebar_position: 3
title: Authorization (RBAC)
---

# Authorization - Role-Based Access Control

TFrameX Enterprise implements a comprehensive Role-Based Access Control (RBAC) system with hierarchical roles, fine-grained permissions, and dynamic policies.

## RBAC Overview

The RBAC system controls access to TFrameX resources:
- **Agents** - Who can create, modify, and execute agents
- **Tools** - Tool access and execution permissions  
- **Flows** - Flow creation and orchestration rights
- **Data** - Memory and storage access controls
- **Configuration** - System configuration permissions

## Core Concepts

### Permissions

Permissions follow the format: `resource:action`

```python
# Permission examples
"agent:read"      # View agent details
"agent:create"    # Create new agents
"agent:update"    # Modify agents
"agent:delete"    # Remove agents
"agent:execute"   # Run agents

"tool:*"          # All tool permissions
"*:read"          # Read all resources
"*"               # Full admin access
```

### Roles

Roles are collections of permissions that can be assigned to users.

```python
from tframex.enterprise.security.rbac import Role

# Define roles
admin_role = Role(
    name="admin",
    description="Full system administrator",
    permissions=["*"]  # All permissions
)

developer_role = Role(
    name="developer",
    description="Agent and tool developer",
    permissions=[
        "agent:*",
        "tool:*",
        "flow:*",
        "metrics:read"
    ]
)

operator_role = Role(
    name="operator",
    description="Execute agents and monitor system",
    permissions=[
        "agent:read",
        "agent:execute",
        "tool:read",
        "tool:execute",
        "flow:read",
        "flow:execute",
        "metrics:read"
    ],
    inherits=["viewer"]  # Inherit viewer permissions
)

viewer_role = Role(
    name="viewer",
    description="Read-only access",
    permissions=[
        "*:read"
    ]
)
```

### Users

Users are assigned one or more roles.

```python
from tframex.enterprise.models import User

user = User(
    username="john.doe",
    email="john@example.com",
    roles=["developer", "operator"],
    
    # Optional: Direct permissions (beyond roles)
    additional_permissions=["admin:metrics"],
    
    # Optional: Deny specific permissions
    denied_permissions=["agent:delete"]
)
```

## Configuring RBAC

### Basic Configuration

```python
# Configure RBAC in enterprise config
config = {
    "enterprise": {
        "security": {
            "rbac": {
                "enabled": True,
                "default_role": "viewer",
                "strict_mode": True,  # Deny by default
                
                "roles": [
                    {
                        "name": "admin",
                        "permissions": ["*"]
                    },
                    {
                        "name": "developer",
                        "permissions": [
                            "agent:*",
                            "tool:*",
                            "flow:*"
                        ]
                    },
                    {
                        "name": "operator",
                        "permissions": [
                            "agent:read",
                            "agent:execute",
                            "tool:read",
                            "tool:execute"
                        ],
                        "inherits": ["viewer"]
                    },
                    {
                        "name": "viewer",
                        "permissions": ["*:read"]
                    }
                ]
            }
        }
    }
}

app = EnterpriseApp(enterprise_config=config)
```

### Advanced RBAC Setup

```python
from tframex.enterprise.security.rbac import RBACEngine

# Create RBAC engine with advanced features
rbac = RBACEngine(
    storage_backend=app.storage,
    
    # Performance settings
    cache_permissions=True,
    cache_ttl=300,
    
    # Security settings
    strict_mode=True,
    audit_all_checks=True,
    
    # Dynamic permissions
    enable_dynamic_permissions=True,
    permission_evaluator=custom_evaluator
)

# Add custom roles
rbac.add_role(
    Role(
        name="data_scientist",
        description="ML model development and data analysis",
        permissions=[
            "agent:create",
            "agent:read",
            "agent:update",
            "agent:execute",
            "tool:*",
            "flow:*",
            "data:read",
            "data:write",
            "model:*"
        ],
        constraints={
            "max_agents": 50,
            "max_concurrent_executions": 10,
            "allowed_models": ["gpt-3.5-turbo", "gpt-4"]
        }
    )
)
```

## Using RBAC

### Protecting Resources

```python
from tframex.enterprise.security.rbac import require_permission, require_role

# Protect functions with decorators
@require_permission("agent:create")
async def create_agent(agent_config):
    """Only users with agent:create permission can call this."""
    return await app.create_agent(agent_config)

@require_role("admin")
async def delete_all_data():
    """Only admins can call this."""
    return await app.storage.clear_all()

# Multiple permissions (AND logic)
@require_permission(["agent:create", "tool:create"])
async def create_agent_with_tools(config):
    """Requires both permissions."""
    pass

# Multiple permissions (OR logic)
@require_permission(["admin:*", "agent:delete"], require_all=False)
async def delete_agent(agent_id):
    """Requires either admin or specific delete permission."""
    pass
```

### Manual Permission Checks

```python
# Check permissions manually
async def process_request(user, action, resource):
    # Check single permission
    if await rbac.has_permission(user, f"{resource}:{action}"):
        # Allowed
        return await perform_action(resource, action)
    else:
        # Denied
        raise AuthorizationError(f"Permission denied: {resource}:{action}")

# Check multiple permissions
permissions_needed = ["agent:read", "tool:execute"]
if await rbac.has_all_permissions(user, permissions_needed):
    # Has all permissions
    pass

# Check any permission
if await rbac.has_any_permission(user, ["admin:*", "agent:execute"]):
    # Has at least one permission
    pass
```

### Context-Aware Authorization

```python
from tframex.enterprise.security.rbac import AuthorizationContext

# Create context for authorization
context = AuthorizationContext(
    user=user,
    resource="agent",
    action="execute",
    
    # Additional context
    resource_id="agent-123",
    resource_owner="user-456",
    environment="production",
    time_of_day="business_hours"
)

# Check with context
is_allowed = await rbac.authorize(context)

# Custom context evaluator
async def custom_evaluator(context: AuthorizationContext) -> bool:
    # Owner can always access their resources
    if context.user.id == context.resource_owner:
        return True
    
    # Production restrictions
    if context.environment == "production":
        if context.action in ["delete", "update"]:
            return context.user.has_role("admin")
    
    # Time-based restrictions
    if context.time_of_day == "after_hours":
        return context.user.has_role("on_call")
    
    # Default to role-based check
    return await rbac.default_authorize(context)

rbac.set_context_evaluator(custom_evaluator)
```

## Dynamic Permissions

### Resource-Based Permissions

```python
# Define resource-specific permissions
class ResourcePermission:
    def __init__(self, resource_type, resource_id, permissions):
        self.resource_type = resource_type
        self.resource_id = resource_id
        self.permissions = permissions

# Grant resource-specific permission
await rbac.grant_resource_permission(
    user_id="user-123",
    resource=ResourcePermission(
        resource_type="agent",
        resource_id="agent-456",
        permissions=["read", "execute"]
    )
)

# Check resource permission
can_execute = await rbac.has_resource_permission(
    user=user,
    resource_type="agent",
    resource_id="agent-456",
    action="execute"
)
```

### Temporary Permissions

```python
from datetime import datetime, timedelta

# Grant temporary permission
await rbac.grant_temporary_permission(
    user_id="user-123",
    permission="agent:delete",
    expires_at=datetime.utcnow() + timedelta(hours=2),
    reason="Emergency maintenance"
)

# Temporary role assignment
await rbac.assign_temporary_role(
    user_id="user-123",
    role="admin",
    expires_at=datetime.utcnow() + timedelta(days=1),
    granted_by="user-admin",
    reason="Coverage for admin vacation"
)
```

### Conditional Permissions

```python
# Define conditional permissions
class ConditionalPermission:
    def __init__(self, permission, condition):
        self.permission = permission
        self.condition = condition

# Add conditional permission to role
await rbac.add_conditional_permission(
    role="operator",
    permission=ConditionalPermission(
        permission="agent:delete",
        condition=lambda ctx: ctx.resource_owner == ctx.user.id
    )
)

# Time-based conditions
await rbac.add_conditional_permission(
    role="developer",
    permission=ConditionalPermission(
        permission="production:deploy",
        condition=lambda ctx: (
            datetime.utcnow().hour >= 9 and 
            datetime.utcnow().hour <= 17 and
            datetime.utcnow().weekday() < 5  # Monday-Friday
        )
    )
)
```

## Access Control Policies

### Policy-Based Access Control

```python
from tframex.enterprise.security.rbac import AccessPolicy

# Define custom access policy
class DataClassificationPolicy(AccessPolicy):
    async def evaluate(self, user, resource, action, context):
        # Get data classification
        classification = await self.get_data_classification(resource)
        
        if classification == "top_secret":
            return user.has_clearance("top_secret")
        elif classification == "confidential":
            return user.has_clearance("secret") or user.has_clearance("top_secret")
        else:
            return True
    
    async def get_data_classification(self, resource):
        # Implement classification logic
        pass

# Add policy to RBAC
rbac.add_policy(DataClassificationPolicy())

# Geographic restriction policy
class GeographicPolicy(AccessPolicy):
    async def evaluate(self, user, resource, action, context):
        user_location = await self.get_user_location(context.ip_address)
        allowed_regions = ["US", "EU"]
        
        return user_location.country_code in allowed_regions
```

### Combining Policies

```python
from tframex.enterprise.security.rbac import PolicyCombiner

# AND combiner - all policies must pass
and_combiner = PolicyCombiner(
    policies=[
        DataClassificationPolicy(),
        GeographicPolicy(),
        TimeBasedPolicy()
    ],
    combination_logic="AND"
)

# OR combiner - at least one policy must pass
or_combiner = PolicyCombiner(
    policies=[
        OwnershipPolicy(),
        AdminOverridePolicy()
    ],
    combination_logic="OR"
)

# Custom combination logic
def custom_logic(policy_results):
    # Require classification AND (geographic OR time-based)
    return (
        policy_results["DataClassification"] and
        (policy_results["Geographic"] or policy_results["TimeBased"])
    )

custom_combiner = PolicyCombiner(
    policies=[...],
    combination_logic=custom_logic
)
```

## Permission Inheritance

### Role Hierarchy

```python
# Define role hierarchy
role_hierarchy = {
    "super_admin": {
        "inherits": ["admin"],
        "permissions": ["system:*"]
    },
    "admin": {
        "inherits": ["developer", "operator"],
        "permissions": ["admin:*"]
    },
    "developer": {
        "inherits": ["operator"],
        "permissions": ["develop:*"]
    },
    "operator": {
        "inherits": ["viewer"],
        "permissions": ["operate:*"]
    },
    "viewer": {
        "permissions": ["*:read"]
    }
}

# User inherits all permissions from assigned roles and their parents
user = User(
    username="jane.doe",
    roles=["developer"]
    # Automatically has: develop:*, operate:*, *:read
)
```

### Permission Delegation

```python
# Allow users to delegate their permissions
class PermissionDelegation:
    async def delegate_permission(
        self,
        delegator: User,
        delegatee: User,
        permission: str,
        expires_at: datetime,
        can_redelegate: bool = False
    ):
        # Verify delegator has the permission
        if not await rbac.has_permission(delegator, permission):
            raise AuthorizationError("Cannot delegate permission you don't have")
        
        # Create delegation record
        delegation = {
            "delegator_id": delegator.id,
            "delegatee_id": delegatee.id,
            "permission": permission,
            "expires_at": expires_at,
            "can_redelegate": can_redelegate,
            "created_at": datetime.utcnow()
        }
        
        await self.storage.save_delegation(delegation)
        
        # Grant temporary permission
        await rbac.grant_temporary_permission(
            user_id=delegatee.id,
            permission=permission,
            expires_at=expires_at
        )
```

## RBAC Administration

### Role Management

```python
from tframex.enterprise.security.rbac import RoleManager

role_manager = RoleManager(rbac)

# Create new role
new_role = await role_manager.create_role(
    name="ml_engineer",
    description="Machine Learning Engineer",
    permissions=[
        "agent:*",
        "model:*",
        "data:read",
        "compute:gpu"
    ]
)

# Update role permissions
await role_manager.add_permission_to_role("ml_engineer", "data:write")
await role_manager.remove_permission_from_role("ml_engineer", "agent:delete")

# Clone role
await role_manager.clone_role(
    source_role="developer",
    new_role_name="senior_developer",
    additional_permissions=["review:*", "mentor:*"]
)

# Delete role (with safety checks)
await role_manager.delete_role(
    "obsolete_role",
    reassign_users_to="viewer"
)
```

### User Permission Management

```python
from tframex.enterprise.security.rbac import UserPermissionManager

perm_manager = UserPermissionManager(rbac)

# View effective permissions
effective_perms = await perm_manager.get_effective_permissions(user)
print(f"User has {len(effective_perms)} permissions")

# Audit permission source
perm_sources = await perm_manager.trace_permission_source(
    user=user,
    permission="agent:execute"
)
# Returns: {"source": "role", "role": "developer", "inherited_from": "operator"}

# Bulk permission operations
await perm_manager.bulk_grant_permissions(
    user_ids=["user1", "user2", "user3"],
    permissions=["special:feature"],
    expires_at=datetime.utcnow() + timedelta(days=7),
    reason="Feature testing"
)
```

## RBAC Monitoring

### Permission Analytics

```python
from tframex.enterprise.security.rbac import RBACAnalytics

analytics = RBACAnalytics(rbac)

# Most used permissions
top_permissions = await analytics.get_top_permissions(
    time_range="7d",
    limit=10
)

# Permission denial patterns
denials = await analytics.get_permission_denials(
    time_range="24h",
    group_by="user"
)

# Unused permissions (for cleanup)
unused = await analytics.find_unused_permissions(
    since=datetime.utcnow() - timedelta(days=90)
)

# Over-privileged users
over_privileged = await analytics.find_over_privileged_users(
    threshold=0.2  # Users using less than 20% of their permissions
)
```

### RBAC Alerts

```python
from tframex.enterprise.security.rbac import RBACAlerting

alerting = RBACAlerting(rbac)

# Alert on suspicious permission usage
@alerting.on_suspicious_activity
async def handle_suspicious(event):
    if event.type == "privilege_escalation_attempt":
        await security_team.notify(
            f"User {event.user_id} attempted privilege escalation"
        )

# Alert on permission changes
@alerting.on_permission_change
async def handle_permission_change(event):
    if event.role in ["admin", "super_admin"]:
        await audit_logger.log_critical(
            f"Admin permission change: {event.change_type}"
        )
```

## Testing RBAC

```python
import pytest
from tframex.enterprise.testing import RBACTestHarness

@pytest.fixture
def rbac_harness():
    return RBACTestHarness()

async def test_role_permissions(rbac_harness):
    # Create test user with role
    user = await rbac_harness.create_user_with_role("developer")
    
    # Test allowed permissions
    assert await rbac_harness.can_perform(user, "agent:create")
    assert await rbac_harness.can_perform(user, "tool:execute")
    
    # Test denied permissions
    assert not await rbac_harness.can_perform(user, "admin:delete")
    assert not await rbac_harness.can_perform(user, "system:shutdown")

async def test_permission_inheritance(rbac_harness):
    # Test role inheritance
    admin = await rbac_harness.create_user_with_role("admin")
    
    # Admin should inherit developer permissions
    assert await rbac_harness.can_perform(admin, "agent:create")
    assert await rbac_harness.can_perform(admin, "develop:*")
```

## Best Practices

### 1. Principle of Least Privilege

```python
# Start with minimal permissions
base_role = Role(
    name="base_user",
    permissions=["profile:read", "profile:update"]
)

# Add permissions as needed
if user.needs_agent_access:
    await rbac.grant_permission(user, "agent:read")
```

### 2. Regular Permission Audits

```python
# Schedule regular audits
async def audit_permissions():
    # Find users with excessive permissions
    for user in await get_all_users():
        used_perms = await analytics.get_used_permissions(user, days=30)
        granted_perms = await rbac.get_user_permissions(user)
        
        unused_ratio = len(granted_perms - used_perms) / len(granted_perms)
        if unused_ratio > 0.5:
            await notify_admin(f"User {user.id} has {unused_ratio:.0%} unused permissions")
```

### 3. Permission Namespacing

```python
# Use clear namespaces
permissions = [
    "production.agent:execute",    # Environment-specific
    "team.alpha.tool:create",     # Team-specific
    "project.x.data:read",        # Project-specific
    "personal.workspace:*"        # Personal resources
]
```

## Next Steps

- [Audit Logging](audit) - Track all authorization decisions
- [Session Management](sessions) - Manage user sessions
- [Security Policies](policies) - Implement custom security policies
- [Compliance](compliance) - Meet regulatory requirements