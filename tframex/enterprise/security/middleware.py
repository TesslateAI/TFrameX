"""
Security Middleware

This module provides comprehensive security middleware components
for integrating authentication, authorization, and audit logging
into the TFrameX request/response pipeline.
"""

import asyncio
import json
import logging
import time
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Union
from uuid import uuid4

from ..models import User, AuditLog
from ..storage.base import BaseStorage
from .auth import AuthenticationProvider, AuthenticationResult, AuthenticationError
from .rbac import RBACEngine, AuthorizationError
from .audit import AuditLogger
from .session import SessionManager

logger = logging.getLogger(__name__)


class SecurityContext:
    """
    Security context for request processing.
    
    Contains authentication and authorization information
    for the current request.
    """
    
    def __init__(self):
        self.user: Optional[User] = None
        self.authenticated: bool = False
        self.auth_method: Optional[str] = None
        self.session_id: Optional[str] = None
        self.permissions: List[str] = []
        self.roles: List[str] = []
        self.request_id: str = str(uuid4())
        self.timestamp: datetime = datetime.utcnow()
        self.metadata: Dict[str, Any] = {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert security context to dictionary."""
        return {
            "user_id": str(self.user.id) if self.user else None,
            "username": self.user.username if self.user else None,
            "authenticated": self.authenticated,
            "auth_method": self.auth_method,
            "session_id": self.session_id,
            "permissions": self.permissions,
            "roles": self.roles,
            "request_id": self.request_id,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata
        }


class BaseMiddleware:
    """
    Base middleware class with common functionality.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize base middleware.
        
        Args:
            config: Middleware configuration
        """
        self.config = config
        self.enabled = config.get("enabled", True)
        self.name = config.get("name", self.__class__.__name__)
    
    async def process_request(self, request: Any, context: SecurityContext) -> bool:
        """
        Process incoming request.
        
        Args:
            request: Request object
            context: Security context
            
        Returns:
            True to continue processing, False to halt
        """
        return True
    
    async def process_response(self, request: Any, response: Any, context: SecurityContext) -> None:
        """
        Process outgoing response.
        
        Args:
            request: Request object
            response: Response object
            context: Security context
        """
        pass
    
    async def handle_error(self, request: Any, error: Exception, context: SecurityContext) -> None:
        """
        Handle middleware error.
        
        Args:
            request: Request object
            error: Exception that occurred
            context: Security context
        """
        logger.error(f"Error in middleware {self.name}: {error}")


class AuthenticationMiddleware(BaseMiddleware):
    """
    Authentication middleware that extracts and validates credentials
    from incoming requests.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize authentication middleware.
        
        Args:
            config: Configuration with keys:
                - providers: List of authentication providers
                - optional_paths: Paths that don't require authentication
                - header_name: Authentication header name
                - cookie_name: Authentication cookie name
                - extract_methods: Methods to extract credentials
        """
        super().__init__(config)
        
        self.providers: List[AuthenticationProvider] = config.get("providers", [])
        self.optional_paths = set(config.get("optional_paths", []))
        self.header_name = config.get("header_name", "Authorization")
        self.cookie_name = config.get("cookie_name", "auth_token")
        self.extract_methods = config.get("extract_methods", ["header", "cookie", "query"])
        
        # Provider by name mapping
        self._provider_map = {
            provider.name: provider for provider in self.providers
        }
    
    async def process_request(self, request: Any, context: SecurityContext) -> bool:
        """
        Process authentication for incoming request.
        
        Args:
            request: Request object
            context: Security context
            
        Returns:
            True to continue processing, False to halt
        """
        try:
            if not self.enabled:
                return True
            
            # Check if path requires authentication
            request_path = getattr(request, "path", "/")
            if request_path in self.optional_paths:
                return True
            
            # Extract credentials from request
            credentials = await self._extract_credentials(request)
            
            if not credentials:
                logger.warning(f"No credentials found in request {context.request_id}")
                return False
            
            # Try authentication with each provider
            auth_result = await self._authenticate_with_providers(credentials)
            
            if auth_result.success and auth_result.user:
                # Update security context
                context.user = auth_result.user
                context.authenticated = True
                context.auth_method = auth_result.metadata.get("auth_method")
                context.metadata.update(auth_result.metadata)
                
                logger.debug(f"User {auth_result.user.username} authenticated via {context.auth_method}")
                return True
            else:
                logger.warning(f"Authentication failed: {auth_result.error}")
                return False
        
        except Exception as e:
            await self.handle_error(request, e, context)
            return False
    
    async def _extract_credentials(self, request: Any) -> Optional[Dict[str, Any]]:
        """
        Extract authentication credentials from request.
        
        Args:
            request: Request object
            
        Returns:
            Credentials dictionary or None
        """
        credentials = {}
        
        try:
            # Extract from headers
            if "header" in self.extract_methods:
                auth_header = getattr(request, "headers", {}).get(self.header_name)
                if auth_header:
                    if auth_header.startswith("Bearer "):
                        credentials["token"] = auth_header[7:]
                        credentials["type"] = "bearer"
                    elif auth_header.startswith("Basic "):
                        credentials["token"] = auth_header[6:]
                        credentials["type"] = "basic"
                    elif auth_header.startswith("API-Key "):
                        credentials["api_key"] = auth_header[8:]
                        credentials["type"] = "api_key"
            
            # Extract from cookies
            if "cookie" in self.extract_methods:
                cookies = getattr(request, "cookies", {})
                auth_cookie = cookies.get(self.cookie_name)
                if auth_cookie:
                    credentials["token"] = auth_cookie
                    credentials["type"] = "cookie"
            
            # Extract from query parameters
            if "query" in self.extract_methods:
                query_params = getattr(request, "query_params", {})
                api_key = query_params.get("api_key")
                if api_key:
                    credentials["api_key"] = api_key
                    credentials["type"] = "query"
            
            # Extract from request body for OAuth flows
            if hasattr(request, "json") and callable(request.json):
                try:
                    body = await request.json()
                    if isinstance(body, dict):
                        if "authorization_code" in body:
                            credentials["authorization_code"] = body["authorization_code"]
                            credentials["type"] = "oauth2"
                        elif "username" in body and "password" in body:
                            credentials["username"] = body["username"]
                            credentials["password"] = body["password"]
                            credentials["type"] = "credentials"
                except:
                    pass
            
            return credentials if credentials else None
            
        except Exception as e:
            logger.error(f"Error extracting credentials: {e}")
            return None
    
    async def _authenticate_with_providers(self, credentials: Dict[str, Any]) -> AuthenticationResult:
        """
        Try authentication with available providers.
        
        Args:
            credentials: Extracted credentials
            
        Returns:
            Authentication result
        """
        last_error = "No suitable authentication provider found"
        
        for provider in self.providers:
            try:
                if not provider.enabled:
                    continue
                
                # Try authentication based on credential type
                if credentials.get("type") == "api_key" and "APIKey" in provider.__class__.__name__:
                    result = await provider.authenticate(credentials)
                elif credentials.get("type") == "basic" and "Basic" in provider.__class__.__name__:
                    result = await provider.validate_token(credentials["token"])
                elif credentials.get("type") == "bearer" and "JWT" in provider.__class__.__name__:
                    result = await provider.validate_token(credentials["token"])
                elif credentials.get("type") == "oauth2" and "OAuth2" in provider.__class__.__name__:
                    result = await provider.authenticate(credentials)
                elif credentials.get("type") == "credentials" and "Basic" in provider.__class__.__name__:
                    result = await provider.authenticate(credentials)
                else:
                    # Try generic authentication
                    result = await provider.authenticate(credentials)
                
                if result.success:
                    return result
                else:
                    last_error = result.error or "Authentication failed"
            
            except Exception as e:
                last_error = str(e)
                logger.error(f"Error in provider {provider.name}: {e}")
        
        return AuthenticationResult(success=False, error=last_error)


class AuthorizationMiddleware(BaseMiddleware):
    """
    Authorization middleware that enforces access control
    using the RBAC engine.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize authorization middleware.
        
        Args:
            config: Configuration with keys:
                - rbac_engine: RBAC engine instance
                - resource_mapping: Function to map requests to resources
                - action_mapping: Function to map requests to actions
                - public_paths: Paths that don't require authorization
        """
        super().__init__(config)
        
        self.rbac_engine: RBACEngine = config.get("rbac_engine")
        self.resource_mapping = config.get("resource_mapping", self._default_resource_mapping)
        self.action_mapping = config.get("action_mapping", self._default_action_mapping)
        self.public_paths = set(config.get("public_paths", []))
        
        if not self.rbac_engine:
            raise ValueError("RBAC engine is required for authorization middleware")
    
    async def process_request(self, request: Any, context: SecurityContext) -> bool:
        """
        Process authorization for incoming request.
        
        Args:
            request: Request object
            context: Security context
            
        Returns:
            True to continue processing, False to halt
        """
        try:
            if not self.enabled:
                return True
            
            # Check if path requires authorization
            request_path = getattr(request, "path", "/")
            if request_path in self.public_paths:
                return True
            
            # Require authentication for authorization
            if not context.authenticated or not context.user:
                logger.warning(f"Authorization attempted without authentication for request {context.request_id}")
                return False
            
            # Map request to resource and action
            resource = await self.resource_mapping(request)
            action = await self.action_mapping(request)
            
            if not resource or not action:
                logger.warning(f"Could not determine resource/action for request {context.request_id}")
                return False
            
            # Create authorization context
            auth_context = {
                "request_id": context.request_id,
                "request_path": request_path,
                "user_agent": getattr(request, "headers", {}).get("User-Agent"),
                "remote_ip": getattr(request, "client", {}).get("host")
            }
            
            # Check authorization
            has_permission = await self.rbac_engine.check_permission(
                context.user,
                resource,
                action,
                auth_context
            )
            
            if has_permission:
                # Update context with permissions
                context.permissions = await self.rbac_engine.get_user_permissions(context.user)
                context.roles = await self.rbac_engine.get_user_roles(context.user.id)
                
                logger.debug(f"User {context.user.username} authorized for {resource}:{action}")
                return True
            else:
                logger.warning(f"User {context.user.username} denied access to {resource}:{action}")
                return False
        
        except AuthorizationError as e:
            logger.warning(f"Authorization error: {e}")
            return False
        except Exception as e:
            await self.handle_error(request, e, context)
            return False
    
    async def _default_resource_mapping(self, request: Any) -> str:
        """
        Default resource mapping based on request path.
        
        Args:
            request: Request object
            
        Returns:
            Resource name
        """
        path = getattr(request, "path", "/")
        path_parts = path.strip("/").split("/")
        
        if len(path_parts) >= 2:
            return path_parts[1]  # e.g., /api/conversations -> conversations
        elif len(path_parts) == 1 and path_parts[0]:
            return path_parts[0]
        else:
            return "api"
    
    async def _default_action_mapping(self, request: Any) -> str:
        """
        Default action mapping based on HTTP method.
        
        Args:
            request: Request object
            
        Returns:
            Action name
        """
        method = getattr(request, "method", "GET").upper()
        
        action_map = {
            "GET": "read",
            "POST": "create",
            "PUT": "update",
            "PATCH": "update",
            "DELETE": "delete",
            "HEAD": "read",
            "OPTIONS": "read"
        }
        
        return action_map.get(method, "execute")


class AuditMiddleware(BaseMiddleware):
    """
    Audit middleware that logs security events and user actions.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize audit middleware.
        
        Args:
            config: Configuration with keys:
                - audit_logger: Audit logger instance
                - log_requests: Whether to log all requests
                - log_responses: Whether to log responses
                - excluded_paths: Paths to exclude from audit logging
                - include_request_body: Whether to include request body
                - include_response_body: Whether to include response body
        """
        super().__init__(config)
        
        self.audit_logger: AuditLogger = config.get("audit_logger")
        self.log_requests = config.get("log_requests", True)
        self.log_responses = config.get("log_responses", False)
        self.excluded_paths = set(config.get("excluded_paths", []))
        self.include_request_body = config.get("include_request_body", False)
        self.include_response_body = config.get("include_response_body", False)
        
        if not self.audit_logger:
            raise ValueError("Audit logger is required for audit middleware")
    
    async def process_request(self, request: Any, context: SecurityContext) -> bool:
        """
        Log request audit event.
        
        Args:
            request: Request object
            context: Security context
            
        Returns:
            True (always continue processing)
        """
        try:
            if not self.enabled:
                return True
            
            request_path = getattr(request, "path", "/")
            if request_path in self.excluded_paths:
                return True
            
            if self.log_requests:
                # Prepare audit data
                audit_data = {
                    "request_id": context.request_id,
                    "method": getattr(request, "method", "UNKNOWN"),
                    "path": request_path,
                    "user_agent": getattr(request, "headers", {}).get("User-Agent"),
                    "remote_ip": getattr(request, "client", {}).get("host"),
                    "query_params": dict(getattr(request, "query_params", {}))
                }
                
                # Include request body if configured
                if self.include_request_body:
                    try:
                        if hasattr(request, "json") and callable(request.json):
                            body = await request.json()
                            # Filter sensitive fields
                            filtered_body = self._filter_sensitive_data(body)
                            audit_data["request_body"] = filtered_body
                    except:
                        pass
                
                # Log audit event
                await self.audit_logger.log_event(
                    event_type="request",
                    user_id=context.user.id if context.user else None,
                    resource="http_request",
                    action=audit_data["method"].lower(),
                    outcome="initiated",
                    details=audit_data,
                    request_id=context.request_id
                )
        
        except Exception as e:
            await self.handle_error(request, e, context)
        
        return True
    
    async def process_response(self, request: Any, response: Any, context: SecurityContext) -> None:
        """
        Log response audit event.
        
        Args:
            request: Request object
            response: Response object
            context: Security context
        """
        try:
            if not self.enabled:
                return
            
            request_path = getattr(request, "path", "/")
            if request_path in self.excluded_paths:
                return
            
            if self.log_responses:
                # Prepare audit data
                audit_data = {
                    "request_id": context.request_id,
                    "status_code": getattr(response, "status_code", 0),
                    "response_size": len(getattr(response, "body", b"")),
                    "duration_ms": (datetime.utcnow() - context.timestamp).total_seconds() * 1000
                }
                
                # Include response body if configured
                if self.include_response_body:
                    try:
                        body = getattr(response, "body", b"")
                        if isinstance(body, bytes):
                            body = body.decode("utf-8", errors="ignore")
                        # Filter sensitive data
                        filtered_body = self._filter_sensitive_data(body)
                        audit_data["response_body"] = filtered_body
                    except:
                        pass
                
                # Determine outcome
                status_code = audit_data["status_code"]
                if status_code < 400:
                    outcome = "success"
                elif status_code < 500:
                    outcome = "client_error"
                else:
                    outcome = "server_error"
                
                # Log audit event
                await self.audit_logger.log_event(
                    event_type="response",
                    user_id=context.user.id if context.user else None,
                    resource="http_response",
                    action="respond",
                    outcome=outcome,
                    details=audit_data,
                    request_id=context.request_id
                )
        
        except Exception as e:
            logger.error(f"Error logging response audit: {e}")
    
    def _filter_sensitive_data(self, data: Any) -> Any:
        """
        Filter sensitive data from audit logs.
        
        Args:
            data: Data to filter
            
        Returns:
            Filtered data
        """
        if not data:
            return data
        
        sensitive_fields = {
            "password", "token", "secret", "key", "authorization",
            "api_key", "access_token", "refresh_token", "jwt"
        }
        
        if isinstance(data, dict):
            filtered = {}
            for key, value in data.items():
                if key.lower() in sensitive_fields:
                    filtered[key] = "[REDACTED]"
                elif isinstance(value, (dict, list)):
                    filtered[key] = self._filter_sensitive_data(value)
                else:
                    filtered[key] = value
            return filtered
        elif isinstance(data, list):
            return [self._filter_sensitive_data(item) for item in data]
        elif isinstance(data, str):
            # Check if string contains sensitive patterns
            for field in sensitive_fields:
                if field in data.lower():
                    return "[REDACTED]"
            return data
        else:
            return data


class SecurityMiddleware(BaseMiddleware):
    """
    Comprehensive security middleware that combines authentication,
    authorization, and audit logging.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize security middleware.
        
        Args:
            config: Configuration with keys:
                - auth_middleware: Authentication middleware
                - authz_middleware: Authorization middleware
                - audit_middleware: Audit middleware
                - session_manager: Session manager
                - rate_limiter: Rate limiter (optional)
        """
        super().__init__(config)
        
        self.auth_middleware: AuthenticationMiddleware = config.get("auth_middleware")
        self.authz_middleware: AuthorizationMiddleware = config.get("authz_middleware")
        self.audit_middleware: AuditMiddleware = config.get("audit_middleware")
        self.session_manager: SessionManager = config.get("session_manager")
        
        # Order of middleware execution
        self.middleware_chain = [
            self.audit_middleware,  # Log requests first
            self.auth_middleware,   # Then authenticate
            self.authz_middleware   # Finally authorize
        ]
        
        # Filter out None middleware
        self.middleware_chain = [mw for mw in self.middleware_chain if mw]
    
    async def process_request(self, request: Any, context: SecurityContext) -> bool:
        """
        Process request through security middleware chain.
        
        Args:
            request: Request object
            context: Security context
            
        Returns:
            True to continue processing, False to halt
        """
        try:
            # Execute middleware chain
            for middleware in self.middleware_chain:
                if not await middleware.process_request(request, context):
                    return False
            
            # Update session if available
            if self.session_manager and context.authenticated:
                await self._update_session(context)
            
            return True
        
        except Exception as e:
            await self.handle_error(request, e, context)
            return False
    
    async def process_response(self, request: Any, response: Any, context: SecurityContext) -> None:
        """
        Process response through security middleware chain.
        
        Args:
            request: Request object
            response: Response object
            context: Security context
        """
        try:
            # Execute middleware chain in reverse order
            for middleware in reversed(self.middleware_chain):
                await middleware.process_response(request, response, context)
        
        except Exception as e:
            logger.error(f"Error processing response in security middleware: {e}")
    
    async def _update_session(self, context: SecurityContext) -> None:
        """
        Update user session information.
        
        Args:
            context: Security context
        """
        try:
            if context.user and self.session_manager:
                session_data = {
                    "last_activity": datetime.utcnow(),
                    "request_count": 1,
                    "auth_method": context.auth_method
                }
                
                await self.session_manager.update_session(
                    context.user.id,
                    session_data
                )
        
        except Exception as e:
            logger.error(f"Error updating session: {e}")


# Utility functions for middleware integration

async def create_security_middleware_stack(config: Dict[str, Any]) -> SecurityMiddleware:
    """
    Create a complete security middleware stack with all components.
    
    Args:
        config: Configuration for all middleware components
        
    Returns:
        Configured security middleware
    """
    # Create individual middleware components
    auth_middleware = AuthenticationMiddleware(config.get("authentication", {}))
    authz_middleware = AuthorizationMiddleware(config.get("authorization", {}))
    audit_middleware = AuditMiddleware(config.get("audit", {}))
    
    # Create security middleware
    security_config = {
        "auth_middleware": auth_middleware,
        "authz_middleware": authz_middleware,
        "audit_middleware": audit_middleware,
        "session_manager": config.get("session_manager")
    }
    
    return SecurityMiddleware(security_config)


def extract_user_from_context(context: SecurityContext) -> Optional[User]:
    """
    Extract user from security context.
    
    Args:
        context: Security context
        
    Returns:
        User object or None
    """
    return context.user if context.authenticated else None


def require_authentication(func: Callable) -> Callable:
    """
    Decorator to require authentication for function execution.
    
    Args:
        func: Function to protect
        
    Returns:
        Protected function
    """
    async def wrapper(*args, **kwargs):
        context = kwargs.get("security_context")
        
        if not context or not context.authenticated:
            raise AuthenticationError("Authentication required")
        
        return await func(*args, **kwargs)
    
    return wrapper


def require_authorization(resource: str, action: str) -> Callable:
    """
    Decorator to require specific authorization for function execution.
    
    Args:
        resource: Resource name
        action: Action name
        
    Returns:
        Authorization decorator
    """
    def decorator(func: Callable) -> Callable:
        async def wrapper(*args, **kwargs):
            context = kwargs.get("security_context")
            
            if not context or not context.authenticated:
                raise AuthenticationError("Authentication required")
            
            # Check if user has required permission
            permission_key = f"{resource}:{action}"
            if permission_key not in context.permissions and "*:*" not in context.permissions:
                raise AuthorizationError(f"Insufficient permissions for {resource}:{action}")
            
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator