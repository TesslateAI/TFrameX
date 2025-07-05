"""
Enterprise Security Package

This package provides comprehensive security features including:
- Authentication providers (OAuth2, API Key, Basic Auth, JWT)
- Role-based access control (RBAC)
- Authorization middleware
- Audit logging
- Session management
"""

from .auth import (
    AuthenticationProvider, AuthenticationResult, AuthenticationError,
    OAuth2Provider, APIKeyProvider, BasicAuthProvider, JWTProvider
)
from .rbac import RBACEngine, Permission, Role, AuthorizationError
from .middleware import (
    AuthenticationMiddleware, AuthorizationMiddleware, 
    AuditMiddleware, SecurityMiddleware
)
from .session import SessionManager, Session
from .audit import AuditLogger

__all__ = [
    # Authentication
    "AuthenticationProvider", "AuthenticationResult", "AuthenticationError",
    "OAuth2Provider", "APIKeyProvider", "BasicAuthProvider", "JWTProvider",
    
    # Authorization
    "RBACEngine", "Permission", "Role", "AuthorizationError",
    
    # Middleware
    "AuthenticationMiddleware", "AuthorizationMiddleware", 
    "AuditMiddleware", "SecurityMiddleware",
    
    # Session Management
    "SessionManager", "Session",
    
    # Audit
    "AuditLogger"
]