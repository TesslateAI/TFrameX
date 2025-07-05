"""
TFrameX Enterprise Package

This package provides enterprise-grade features for TFrameX including:
- Comprehensive metrics collection and monitoring
- Multi-backend data persistence
- Authentication and authorization (RBAC)
- Audit logging and compliance
- Session management
- Enterprise-grade security

Usage:
    from tframex.enterprise import EnterpriseApp
    
    app = EnterpriseApp(
        enterprise_config="enterprise_config.yaml",
        default_llm=my_llm
    )
"""

# Core application
from .app import EnterpriseApp, EnterpriseRuntimeContext

# Configuration
from .config import EnterpriseConfig, load_enterprise_config, create_default_config

# Models
from .models import *

# Storage
from .storage.base import BaseStorage
from .storage.memory import InMemoryStorage
from .storage.sqlite import SQLiteStorage
from .storage.factory import (
    create_storage_backend, get_available_storage_types,
    validate_storage_config, get_storage_config_template
)

# Metrics
from .metrics.manager import MetricsManager
from .metrics.base import MetricsCollector, MetricEvent, MetricType
from .metrics.prometheus import PrometheusCollector
from .metrics.statsd import StatsDCollector
from .metrics.opentelemetry import OpenTelemetryCollector
from .metrics.custom import CustomMetricsCollector

# Security
from .security.auth import (
    AuthenticationProvider, AuthenticationResult, AuthenticationError,
    OAuth2Provider, APIKeyProvider, BasicAuthProvider, JWTProvider
)
from .security.rbac import (
    RBACEngine, Permission, Role, AuthorizationError,
    require_permission, require_role
)
from .security.middleware import (
    SecurityMiddleware, SecurityContext, AuthenticationMiddleware,
    AuthorizationMiddleware, AuditMiddleware
)
from .security.session import SessionManager, Session
from .security.audit import (
    AuditLogger, AuditEvent, AuditEventType, AuditOutcome,
    log_authentication_event, log_authorization_event, log_data_access_event
)

# Enhanced Features
from .tracing import WorkflowTracer, trace_workflow
from .analytics import AnalyticsDashboard
from .integration import EnhancedEnterpriseApp, create_enhanced_enterprise_app

__version__ = "1.0.0"

__all__ = [
    # Main application
    "EnterpriseApp", "EnterpriseRuntimeContext",
    
    # Enhanced Features
    "EnhancedEnterpriseApp", "create_enhanced_enterprise_app",
    "WorkflowTracer", "trace_workflow", "AnalyticsDashboard",
    
    # Configuration
    "EnterpriseConfig", "load_enterprise_config", "create_default_config",
    
    # Models
    "User", "Role", "Permission", "Conversation", "Message",
    "FlowExecution", "FlowStep", "AgentExecution", "ToolCall",
    "Metric", "Event", "AuditLog",
    
    # Storage
    "BaseStorage", "InMemoryStorage", "SQLiteStorage",
    "create_storage_backend", "get_available_storage_types",
    "validate_storage_config", "get_storage_config_template",
    
    # Metrics
    "MetricsManager", "MetricsCollector", "MetricEvent", "MetricType",
    "PrometheusCollector", "StatsDCollector", "OpenTelemetryCollector",
    "CustomMetricsCollector",
    
    # Security - Authentication
    "AuthenticationProvider", "AuthenticationResult", "AuthenticationError",
    "OAuth2Provider", "APIKeyProvider", "BasicAuthProvider", "JWTProvider",
    
    # Security - Authorization
    "RBACEngine", "Permission", "Role", "AuthorizationError",
    "require_permission", "require_role",
    
    # Security - Middleware
    "SecurityMiddleware", "SecurityContext", "AuthenticationMiddleware",
    "AuthorizationMiddleware", "AuditMiddleware",
    
    # Security - Session Management
    "SessionManager", "Session",
    
    # Security - Audit Logging
    "AuditLogger", "AuditEvent", "AuditEventType", "AuditOutcome",
    "log_authentication_event", "log_authorization_event", "log_data_access_event"
]