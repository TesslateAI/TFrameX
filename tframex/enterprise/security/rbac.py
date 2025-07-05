"""
Role-Based Access Control (RBAC) Engine

This module provides a comprehensive RBAC system with support for:
- Hierarchical roles and permissions
- Dynamic permission evaluation
- Resource-based authorization
- Policy-based access control
- Audit trail integration
"""

import logging
from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Union
from uuid import UUID, uuid4

from ..models import User, Role, Permission
from ..storage.base import BaseStorage

logger = logging.getLogger(__name__)


class PermissionType(Enum):
    """Permission types for different actions."""
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    EXECUTE = "execute"
    ADMIN = "admin"


class AuthorizationError(Exception):
    """Base exception for authorization errors."""
    pass


class InsufficientPermissionsError(AuthorizationError):
    """Exception raised when user lacks required permissions."""
    pass


class InvalidRoleError(AuthorizationError):
    """Exception raised when role is invalid or doesn't exist."""
    pass


class PolicyViolationError(AuthorizationError):
    """Exception raised when action violates policy."""
    pass


class AccessPolicy(ABC):
    """
    Abstract base class for access policies.
    
    Policies provide additional logic for authorization decisions
    beyond simple permission checks.
    """
    
    @abstractmethod
    async def evaluate(
        self,
        user: User,
        resource: str,
        action: str,
        context: Dict[str, Any]
    ) -> bool:
        """
        Evaluate policy for authorization decision.
        
        Args:
            user: User requesting access
            resource: Resource being accessed
            action: Action being performed
            context: Additional context information
            
        Returns:
            True if access should be granted
        """
        pass
    
    @abstractmethod
    def get_policy_info(self) -> Dict[str, Any]:
        """
        Get information about this policy.
        
        Returns:
            Policy information
        """
        pass


class TimeBasedPolicy(AccessPolicy):
    """
    Policy that restricts access based on time windows.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize time-based policy.
        
        Args:
            config: Configuration with keys:
                - allowed_hours: List of allowed hours (0-23)
                - allowed_days: List of allowed days (0=Monday, 6=Sunday)
                - timezone: Timezone for time evaluation
        """
        self.allowed_hours = set(config.get("allowed_hours", list(range(24))))
        self.allowed_days = set(config.get("allowed_days", list(range(7))))
        self.timezone = config.get("timezone", "UTC")
    
    async def evaluate(
        self,
        user: User,
        resource: str,
        action: str,
        context: Dict[str, Any]
    ) -> bool:
        """
        Evaluate time-based access policy.
        """
        try:
            now = datetime.utcnow()  # In production, use timezone-aware datetime
            
            current_hour = now.hour
            current_day = now.weekday()
            
            hour_allowed = current_hour in self.allowed_hours
            day_allowed = current_day in self.allowed_days
            
            return hour_allowed and day_allowed
            
        except Exception as e:
            logger.error(f"Error evaluating time-based policy: {e}")
            return False
    
    def get_policy_info(self) -> Dict[str, Any]:
        """Get time-based policy information."""
        return {
            "type": "time_based",
            "allowed_hours": list(self.allowed_hours),
            "allowed_days": list(self.allowed_days),
            "timezone": self.timezone
        }


class ResourceOwnershipPolicy(AccessPolicy):
    """
    Policy that grants access based on resource ownership.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize resource ownership policy.
        
        Args:
            config: Configuration with keys:
                - storage: Storage backend for ownership lookup
                - ownership_field: Field name for ownership (default: "owner_id")
        """
        self.storage = config.get("storage")
        self.ownership_field = config.get("ownership_field", "owner_id")
        
        if not self.storage:
            raise ValueError("Storage backend is required for ownership policy")
    
    async def evaluate(
        self,
        user: User,
        resource: str,
        action: str,
        context: Dict[str, Any]
    ) -> bool:
        """
        Evaluate resource ownership policy.
        """
        try:
            resource_id = context.get("resource_id")
            if not resource_id:
                return False
            
            # Look up resource ownership
            resources = await self.storage.select(
                resource,
                filters={"id": resource_id}
            )
            
            if not resources:
                return False
            
            resource_data = resources[0]
            owner_id = resource_data.get(self.ownership_field)
            
            return str(user.id) == str(owner_id)
            
        except Exception as e:
            logger.error(f"Error evaluating ownership policy: {e}")
            return False
    
    def get_policy_info(self) -> Dict[str, Any]:
        """Get ownership policy information."""
        return {
            "type": "resource_ownership",
            "ownership_field": self.ownership_field
        }


class RBACEngine:
    """
    Comprehensive Role-Based Access Control engine.
    
    The RBACEngine provides centralized authorization management with:
    - Role and permission management
    - Hierarchical role inheritance
    - Dynamic permission evaluation
    - Policy-based access control
    - Audit trail integration
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize RBAC engine.
        
        Args:
            config: Configuration dictionary with keys:
                - storage: Storage backend for roles/permissions
                - default_role: Default role for new users
                - enable_inheritance: Whether to enable role inheritance
                - enable_policies: Whether to enable policy evaluation
                - cache_ttl: Cache TTL for permissions (seconds)
        """
        self.config = config
        self.storage: BaseStorage = config.get("storage")
        self.default_role = config.get("default_role", "user")
        self.enable_inheritance = config.get("enable_inheritance", True)
        self.enable_policies = config.get("enable_policies", True)
        self.cache_ttl = config.get("cache_ttl", 300)  # 5 minutes
        
        if not self.storage:
            raise ValueError("Storage backend is required for RBAC engine")
        
        # Policy registry
        self._policies: Dict[str, AccessPolicy] = {}
        
        # Permission cache
        self._permission_cache: Dict[str, Dict[str, Any]] = {}
        
        # Built-in roles and permissions
        self._builtin_roles = {
            "admin": {
                "name": "Administrator",
                "description": "Full system access",
                "permissions": ["*:*"]
            },
            "user": {
                "name": "User",
                "description": "Basic user access",
                "permissions": ["conversations:read", "conversations:create"]
            },
            "viewer": {
                "name": "Viewer",
                "description": "Read-only access",
                "permissions": ["conversations:read"]
            }
        }
    
    async def initialize(self) -> None:
        """
        Initialize RBAC engine and create built-in roles.
        """
        try:
            # Create built-in roles if they don't exist
            await self._create_builtin_roles()
            
            logger.info("RBAC engine initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize RBAC engine: {e}")
            raise
    
    async def _create_builtin_roles(self) -> None:
        """Create built-in roles and permissions."""
        for role_id, role_data in self._builtin_roles.items():
            try:
                # Check if role exists
                existing_roles = await self.storage.select(
                    "roles",
                    filters={"name": role_id}
                )
                
                if not existing_roles:
                    # Create role
                    role = Role(
                        id=uuid4(),
                        name=role_id,
                        display_name=role_data["name"],
                        description=role_data["description"],
                        permissions=role_data["permissions"],
                        is_builtin=True
                    )
                    
                    await self.storage.insert("roles", role.model_dump())
                    logger.debug(f"Created built-in role: {role_id}")
                
            except Exception as e:
                logger.error(f"Failed to create built-in role {role_id}: {e}")
    
    async def assign_role(self, user_id: UUID, role_name: str) -> None:
        """
        Assign a role to a user.
        
        Args:
            user_id: User ID
            role_name: Role name to assign
        """
        try:
            # Verify role exists
            roles = await self.storage.select(
                "roles",
                filters={"name": role_name}
            )
            
            if not roles:
                raise InvalidRoleError(f"Role '{role_name}' does not exist")
            
            role = Role.model_validate(roles[0])
            
            # Update user's roles
            users = await self.storage.select(
                "users",
                filters={"id": str(user_id)}
            )
            
            if not users:
                raise ValueError(f"User {user_id} not found")
            
            user_data = users[0]
            current_roles = user_data.get("roles", [])
            
            if role_name not in current_roles:
                current_roles.append(role_name)
                
                await self.storage.update(
                    "users",
                    str(user_id),
                    {"roles": current_roles}
                )
                
                # Clear permission cache for user
                self._clear_user_cache(user_id)
                
                logger.info(f"Assigned role '{role_name}' to user {user_id}")
            
        except Exception as e:
            logger.error(f"Failed to assign role '{role_name}' to user {user_id}: {e}")
            raise
    
    async def revoke_role(self, user_id: UUID, role_name: str) -> None:
        """
        Revoke a role from a user.
        
        Args:
            user_id: User ID
            role_name: Role name to revoke
        """
        try:
            # Update user's roles
            users = await self.storage.select(
                "users",
                filters={"id": str(user_id)}
            )
            
            if not users:
                raise ValueError(f"User {user_id} not found")
            
            user_data = users[0]
            current_roles = user_data.get("roles", [])
            
            if role_name in current_roles:
                current_roles.remove(role_name)
                
                await self.storage.update(
                    "users",
                    str(user_id),
                    {"roles": current_roles}
                )
                
                # Clear permission cache for user
                self._clear_user_cache(user_id)
                
                logger.info(f"Revoked role '{role_name}' from user {user_id}")
            
        except Exception as e:
            logger.error(f"Failed to revoke role '{role_name}' from user {user_id}: {e}")
            raise
    
    async def check_permission(
        self,
        user: User,
        resource: str,
        action: str,
        context: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Check if user has permission to perform action on resource.
        
        Args:
            user: User to check permissions for
            resource: Resource being accessed
            action: Action being performed
            context: Additional context for policy evaluation
            
        Returns:
            True if user has permission
        """
        try:
            # Get user permissions
            permissions = await self.get_user_permissions(user)
            
            # Check permission
            permission_key = f"{resource}:{action}"
            has_permission = self._check_permission_match(permissions, permission_key)
            
            if not has_permission:
                return False
            
            # Evaluate policies if enabled
            if self.enable_policies and context:
                policy_result = await self._evaluate_policies(user, resource, action, context)
                if not policy_result:
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error checking permission for user {user.id}: {e}")
            return False
    
    async def require_permission(
        self,
        user: User,
        resource: str,
        action: str,
        context: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Require user to have permission, raise exception if not.
        
        Args:
            user: User to check permissions for
            resource: Resource being accessed
            action: Action being performed
            context: Additional context for policy evaluation
            
        Raises:
            InsufficientPermissionsError: If user lacks permission
        """
        has_permission = await self.check_permission(user, resource, action, context)
        
        if not has_permission:
            raise InsufficientPermissionsError(
                f"User {user.username} lacks permission for {resource}:{action}"
            )
    
    async def get_user_permissions(self, user: User) -> List[str]:
        """
        Get all permissions for a user based on their roles.
        
        Args:
            user: User to get permissions for
            
        Returns:
            List of permission strings
        """
        try:
            # Check cache
            cache_key = f"user:{user.id}:permissions"
            cached = self._permission_cache.get(cache_key)
            
            if cached and (datetime.utcnow() - cached["timestamp"]).seconds < self.cache_ttl:
                return cached["permissions"]
            
            # Get user roles
            user_roles = getattr(user, "roles", [])
            if not user_roles:
                user_roles = [self.default_role]
            
            # Collect permissions from all roles
            all_permissions = set()
            
            for role_name in user_roles:
                role_permissions = await self.get_role_permissions(role_name)
                all_permissions.update(role_permissions)
            
            permissions_list = list(all_permissions)
            
            # Cache permissions
            self._permission_cache[cache_key] = {
                "permissions": permissions_list,
                "timestamp": datetime.utcnow()
            }
            
            return permissions_list
            
        except Exception as e:
            logger.error(f"Failed to get permissions for user {user.id}: {e}")
            return []
    
    async def get_role_permissions(self, role_name: str) -> List[str]:
        """
        Get permissions for a specific role.
        
        Args:
            role_name: Role name
            
        Returns:
            List of permission strings
        """
        try:
            # Get role from storage
            roles = await self.storage.select(
                "roles",
                filters={"name": role_name}
            )
            
            if not roles:
                logger.warning(f"Role '{role_name}' not found")
                return []
            
            role = Role.model_validate(roles[0])
            permissions = role.permissions or []
            
            # Handle role inheritance if enabled
            if self.enable_inheritance and role.parent_role:
                parent_permissions = await self.get_role_permissions(role.parent_role)
                permissions.extend(parent_permissions)
            
            return permissions
            
        except Exception as e:
            logger.error(f"Failed to get permissions for role '{role_name}': {e}")
            return []
    
    def _check_permission_match(self, permissions: List[str], required_permission: str) -> bool:
        """
        Check if required permission matches any user permissions.
        
        Args:
            permissions: User's permissions
            required_permission: Required permission (e.g., "conversations:read")
            
        Returns:
            True if permission matches
        """
        # Check for wildcard permissions
        if "*:*" in permissions:
            return True
        
        # Parse required permission
        resource, action = required_permission.split(":", 1)
        
        # Check exact match
        if required_permission in permissions:
            return True
        
        # Check resource wildcard
        resource_wildcard = f"{resource}:*"
        if resource_wildcard in permissions:
            return True
        
        # Check action wildcard
        action_wildcard = f"*:{action}"
        if action_wildcard in permissions:
            return True
        
        return False
    
    async def _evaluate_policies(
        self,
        user: User,
        resource: str,
        action: str,
        context: Dict[str, Any]
    ) -> bool:
        """
        Evaluate all registered policies for access decision.
        
        Args:
            user: User requesting access
            resource: Resource being accessed
            action: Action being performed
            context: Additional context information
            
        Returns:
            True if all policies allow access
        """
        try:
            for policy_name, policy in self._policies.items():
                try:
                    result = await policy.evaluate(user, resource, action, context)
                    if not result:
                        logger.warning(f"Policy '{policy_name}' denied access for user {user.id}")
                        return False
                except Exception as e:
                    logger.error(f"Error evaluating policy '{policy_name}': {e}")
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error evaluating policies: {e}")
            return False
    
    def register_policy(self, name: str, policy: AccessPolicy) -> None:
        """
        Register an access policy.
        
        Args:
            name: Policy name
            policy: Policy instance
        """
        self._policies[name] = policy
        logger.info(f"Registered access policy: {name}")
    
    def unregister_policy(self, name: str) -> None:
        """
        Unregister an access policy.
        
        Args:
            name: Policy name to unregister
        """
        if name in self._policies:
            del self._policies[name]
            logger.info(f"Unregistered access policy: {name}")
    
    async def create_role(
        self,
        name: str,
        display_name: str,
        description: str,
        permissions: List[str],
        parent_role: Optional[str] = None
    ) -> Role:
        """
        Create a new role.
        
        Args:
            name: Role name (unique identifier)
            display_name: Human-readable role name
            description: Role description
            permissions: List of permissions
            parent_role: Parent role for inheritance
            
        Returns:
            Created role
        """
        try:
            # Check if role already exists
            existing_roles = await self.storage.select(
                "roles",
                filters={"name": name}
            )
            
            if existing_roles:
                raise ValueError(f"Role '{name}' already exists")
            
            # Create role
            role = Role(
                id=uuid4(),
                name=name,
                display_name=display_name,
                description=description,
                permissions=permissions,
                parent_role=parent_role,
                is_builtin=False
            )
            
            await self.storage.insert("roles", role.model_dump())
            
            logger.info(f"Created role: {name}")
            return role
            
        except Exception as e:
            logger.error(f"Failed to create role '{name}': {e}")
            raise
    
    async def update_role(
        self,
        role_name: str,
        updates: Dict[str, Any]
    ) -> None:
        """
        Update an existing role.
        
        Args:
            role_name: Role name to update
            updates: Updates to apply
        """
        try:
            # Get existing role
            roles = await self.storage.select(
                "roles",
                filters={"name": role_name}
            )
            
            if not roles:
                raise InvalidRoleError(f"Role '{role_name}' not found")
            
            role_data = roles[0]
            
            # Prevent updating built-in roles
            if role_data.get("is_builtin", False):
                raise ValueError(f"Cannot update built-in role '{role_name}'")
            
            # Apply updates
            await self.storage.update("roles", role_data["id"], updates)
            
            # Clear related caches
            self._clear_role_cache(role_name)
            
            logger.info(f"Updated role: {role_name}")
            
        except Exception as e:
            logger.error(f"Failed to update role '{role_name}': {e}")
            raise
    
    async def delete_role(self, role_name: str) -> None:
        """
        Delete a role.
        
        Args:
            role_name: Role name to delete
        """
        try:
            # Get existing role
            roles = await self.storage.select(
                "roles",
                filters={"name": role_name}
            )
            
            if not roles:
                raise InvalidRoleError(f"Role '{role_name}' not found")
            
            role_data = roles[0]
            
            # Prevent deleting built-in roles
            if role_data.get("is_builtin", False):
                raise ValueError(f"Cannot delete built-in role '{role_name}'")
            
            # Remove role from all users
            users_with_role = await self.storage.select(
                "users",
                filters={"roles": {"$contains": role_name}}
            )
            
            for user_data in users_with_role:
                user_roles = user_data.get("roles", [])
                if role_name in user_roles:
                    user_roles.remove(role_name)
                    await self.storage.update(
                        "users",
                        user_data["id"],
                        {"roles": user_roles}
                    )
            
            # Delete role
            await self.storage.delete("roles", role_data["id"])
            
            # Clear caches
            self._clear_role_cache(role_name)
            
            logger.info(f"Deleted role: {role_name}")
            
        except Exception as e:
            logger.error(f"Failed to delete role '{role_name}': {e}")
            raise
    
    async def list_roles(self) -> List[Role]:
        """
        List all available roles.
        
        Returns:
            List of roles
        """
        try:
            roles_data = await self.storage.select("roles")
            return [Role.model_validate(role) for role in roles_data]
            
        except Exception as e:
            logger.error(f"Failed to list roles: {e}")
            return []
    
    async def get_user_roles(self, user_id: UUID) -> List[str]:
        """
        Get roles assigned to a user.
        
        Args:
            user_id: User ID
            
        Returns:
            List of role names
        """
        try:
            users = await self.storage.select(
                "users",
                filters={"id": str(user_id)}
            )
            
            if not users:
                return []
            
            user_data = users[0]
            return user_data.get("roles", [])
            
        except Exception as e:
            logger.error(f"Failed to get roles for user {user_id}: {e}")
            return []
    
    def _clear_user_cache(self, user_id: UUID) -> None:
        """Clear cached permissions for a user."""
        cache_key = f"user:{user_id}:permissions"
        if cache_key in self._permission_cache:
            del self._permission_cache[cache_key]
    
    def _clear_role_cache(self, role_name: str) -> None:
        """Clear cached data for a role."""
        # Clear permission cache for all users with this role
        keys_to_remove = []
        for cache_key in self._permission_cache:
            if cache_key.startswith("user:"):
                keys_to_remove.append(cache_key)
        
        for key in keys_to_remove:
            del self._permission_cache[key]
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on RBAC engine.
        
        Returns:
            Health status information
        """
        try:
            # Check storage connectivity
            roles_count = await self.storage.count("roles")
            users_count = await self.storage.count("users")
            
            return {
                "healthy": True,
                "storage_connected": True,
                "roles_count": roles_count,
                "users_count": users_count,
                "policies_count": len(self._policies),
                "cache_size": len(self._permission_cache),
                "inheritance_enabled": self.enable_inheritance,
                "policies_enabled": self.enable_policies
            }
            
        except Exception as e:
            logger.error(f"RBAC health check failed: {e}")
            return {
                "healthy": False,
                "error": str(e)
            }
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get RBAC engine statistics.
        
        Returns:
            Statistics dictionary
        """
        return {
            "policies_registered": len(self._policies),
            "permission_cache_size": len(self._permission_cache),
            "inheritance_enabled": self.enable_inheritance,
            "policies_enabled": self.enable_policies,
            "cache_ttl": self.cache_ttl,
            "default_role": self.default_role
        }


# Authorization decorators for easy integration

def require_permission(resource: str, action: str, rbac_engine: RBACEngine):
    """
    Decorator to require specific permission for function execution.
    
    Args:
        resource: Resource name
        action: Action name
        rbac_engine: RBAC engine instance
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Extract user from function arguments or context
            user = kwargs.get("user") or (args[0] if args else None)
            
            if not user or not isinstance(user, User):
                raise AuthorizationError("User context required for authorization")
            
            # Check permission
            await rbac_engine.require_permission(user, resource, action)
            
            # Execute function
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator


def require_role(role_name: str, rbac_engine: RBACEngine):
    """
    Decorator to require specific role for function execution.
    
    Args:
        role_name: Required role name
        rbac_engine: RBAC engine instance
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Extract user from function arguments or context
            user = kwargs.get("user") or (args[0] if args else None)
            
            if not user or not isinstance(user, User):
                raise AuthorizationError("User context required for authorization")
            
            # Check role
            user_roles = await rbac_engine.get_user_roles(user.id)
            
            if role_name not in user_roles:
                raise InsufficientPermissionsError(
                    f"User {user.username} lacks required role: {role_name}"
                )
            
            # Execute function
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator