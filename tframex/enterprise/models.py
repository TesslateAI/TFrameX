"""
Enterprise Data Models

This module defines Pydantic models for enterprise features including
users, roles, conversations, metrics, and audit logs.
"""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any, Literal
from uuid import UUID, uuid4
from pydantic import BaseModel, Field, ConfigDict, validator
import json


class TimestampMixin(BaseModel):
    """Mixin for models that need timestamp fields."""
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None


class UUIDMixin(BaseModel):
    """Mixin for models that need UUID primary keys."""
    id: UUID = Field(default_factory=uuid4)
    
    @validator('id', pre=True)
    def parse_uuid(cls, v):
        """Parse UUID from string if needed."""
        if isinstance(v, str):
            try:
                return UUID(v)
            except ValueError:
                # If it's not a valid UUID, generate a new one
                return uuid4()
        return v


# User Management Models

class User(UUIDMixin, TimestampMixin):
    """User model for authentication and authorization."""
    model_config = ConfigDict(from_attributes=True)
    
    username: str = Field(..., min_length=3, max_length=255)
    email: Optional[str] = Field(None, max_length=255)
    password_hash: Optional[str] = Field(None, max_length=255)
    is_active: bool = Field(default=True)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class Role(UUIDMixin, TimestampMixin):
    """Role model for RBAC."""
    model_config = ConfigDict(from_attributes=True)
    
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    permissions: List[str] = Field(default_factory=list)
    parent_role: Optional[str] = Field(None, description="Parent role name for inheritance")


class Permission(UUIDMixin):
    """Permission model for fine-grained access control."""
    model_config = ConfigDict(from_attributes=True)
    
    name: str = Field(..., min_length=1, max_length=100)
    resource: str = Field(..., min_length=1, max_length=100)
    action: str = Field(..., min_length=1, max_length=50)
    description: Optional[str] = None


class UserRole(BaseModel):
    """Association between users and roles."""
    model_config = ConfigDict(from_attributes=True)
    
    user_id: UUID
    role_id: UUID
    assigned_at: datetime = Field(default_factory=datetime.utcnow)
    assigned_by: Optional[UUID] = None


# Conversation and Messaging Models

class Conversation(UUIDMixin, TimestampMixin):
    """Conversation model for storing chat sessions."""
    model_config = ConfigDict(from_attributes=True)
    
    user_id: Optional[UUID] = None
    agent_name: str = Field(..., min_length=1, max_length=255)
    title: Optional[str] = Field(None, max_length=500)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class Message(UUIDMixin):
    """Message model for conversation messages."""
    model_config = ConfigDict(from_attributes=True)
    
    conversation_id: UUID
    role: Literal["system", "user", "assistant", "tool"]
    content: Optional[str] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None
    tool_call_id: Optional[str] = None
    name: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)


# Flow Execution Models

class ExecutionStatus(str, Enum):
    """Status enum for executions."""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"


class FlowExecution(UUIDMixin):
    """Flow execution model."""
    model_config = ConfigDict(from_attributes=True)
    
    user_id: Optional[UUID] = None
    flow_name: str = Field(..., min_length=1, max_length=255)
    status: ExecutionStatus = ExecutionStatus.RUNNING
    initial_input: Optional[str] = None
    final_output: Optional[str] = None
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class FlowStep(UUIDMixin):
    """Flow step execution model."""
    model_config = ConfigDict(from_attributes=True)
    
    execution_id: UUID
    step_name: str = Field(..., min_length=1, max_length=255)
    step_type: str = Field(..., min_length=1, max_length=100)
    input_data: Optional[str] = None
    output_data: Optional[str] = None
    status: ExecutionStatus = ExecutionStatus.PENDING
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    step_order: int = Field(..., ge=0)


class AgentExecution(UUIDMixin):
    """Agent execution model."""
    model_config = ConfigDict(from_attributes=True)
    
    user_id: Optional[UUID] = None
    conversation_id: Optional[UUID] = None
    flow_execution_id: Optional[UUID] = None
    agent_name: str = Field(..., min_length=1, max_length=255)
    input_message: Optional[str] = None
    output_message: Optional[str] = None
    execution_time_ms: Optional[int] = Field(None, ge=0)
    tool_calls_count: int = Field(default=0, ge=0)
    status: ExecutionStatus = ExecutionStatus.SUCCESS
    error_message: Optional[str] = None
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ToolCall(UUIDMixin):
    """Tool call execution model."""
    model_config = ConfigDict(from_attributes=True)
    
    agent_execution_id: UUID
    tool_name: str = Field(..., min_length=1, max_length=255)
    tool_type: Literal["native", "mcp", "agent"] = "native"
    arguments: Dict[str, Any] = Field(default_factory=dict)
    result: Optional[str] = None
    execution_time_ms: Optional[int] = Field(None, ge=0)
    status: ExecutionStatus = ExecutionStatus.SUCCESS
    error_message: Optional[str] = None
    called_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None


# Metrics Models

class MetricType(str, Enum):
    """Metric type enumeration."""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    TIMER = "timer"


class Metric(UUIDMixin):
    """Metric model for storing metrics data."""
    model_config = ConfigDict(from_attributes=True)
    
    metric_name: str = Field(..., min_length=1, max_length=255)
    metric_type: MetricType
    value: float
    labels: Dict[str, str] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    source: Optional[str] = Field(None, max_length=100)


# Event and Audit Models

class EventType(str, Enum):
    """Event type enumeration."""
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    AGENT_EXECUTION = "agent_execution"
    TOOL_CALL = "tool_call"
    FLOW_EXECUTION = "flow_execution"
    DATA_ACCESS = "data_access"
    CONFIGURATION = "configuration"
    SECURITY = "security"
    ERROR = "error"


class Event(UUIDMixin):
    """Event model for system events."""
    model_config = ConfigDict(from_attributes=True)
    
    event_type: EventType
    event_source: str = Field(..., min_length=1, max_length=100)
    user_id: Optional[UUID] = None
    resource_type: Optional[str] = Field(None, max_length=100)
    resource_id: Optional[str] = Field(None, max_length=255)
    action: str = Field(..., min_length=1, max_length=100)
    status: ExecutionStatus = ExecutionStatus.SUCCESS
    details: Dict[str, Any] = Field(default_factory=dict)
    ip_address: Optional[str] = Field(None, max_length=45)  # IPv6 max length
    user_agent: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class AuditLog(UUIDMixin):
    """Audit log model for security and compliance."""
    model_config = ConfigDict(from_attributes=True)
    
    user_id: Optional[UUID] = None
    action: str = Field(..., min_length=1, max_length=100)
    resource_type: str = Field(..., min_length=1, max_length=100)
    resource_id: Optional[str] = Field(None, max_length=255)
    old_values: Optional[Dict[str, Any]] = None
    new_values: Optional[Dict[str, Any]] = None
    ip_address: Optional[str] = Field(None, max_length=45)
    user_agent: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


# Configuration Models

class DatabaseConfig(BaseModel):
    """Database configuration model."""
    backend: Literal["memory", "sqlite", "postgresql", "s3"] = "memory"
    connection_string: Optional[str] = None
    pool_size: int = Field(default=10, ge=1, le=100)
    max_overflow: int = Field(default=20, ge=0, le=100)
    pool_timeout: int = Field(default=30, ge=1, le=300)
    migrations: bool = True


class MetricsConfig(BaseModel):
    """Metrics configuration model."""
    enabled: bool = True
    backends: List[Literal["prometheus", "statsd", "opentelemetry", "custom"]] = ["prometheus"]
    export_interval: int = Field(default=60, ge=1, le=3600)
    retention_days: int = Field(default=30, ge=1, le=365)
    
    # Prometheus specific
    prometheus_port: int = Field(default=9090, ge=1024, le=65535)
    prometheus_path: str = "/metrics"
    
    # StatsD specific
    statsd_host: str = "localhost"
    statsd_port: int = Field(default=8125, ge=1024, le=65535)
    
    # OpenTelemetry specific
    otel_endpoint: Optional[str] = None
    otel_service_name: str = "tframex"


class SecurityConfig(BaseModel):
    """Security configuration model."""
    enabled: bool = True
    require_auth: bool = True
    auth_providers: List[Literal["oauth2", "api_key", "basic", "jwt"]] = ["api_key"]
    default_role: str = "user"
    session_timeout: int = Field(default=3600, ge=300, le=86400)  # 5 minutes to 24 hours
    
    # OAuth2 specific
    oauth2_issuer: Optional[str] = None
    oauth2_client_id: Optional[str] = None
    oauth2_client_secret: Optional[str] = None
    
    # API Key specific
    api_key_header: str = "X-API-Key"
    api_key_length: int = Field(default=32, ge=16, le=128)
    
    # Rate limiting
    rate_limit_enabled: bool = True
    rate_limit_requests: int = Field(default=100, ge=1, le=10000)
    rate_limit_window: int = Field(default=60, ge=1, le=3600)


class EnterpriseConfig(BaseModel):
    """Enterprise configuration model."""
    enabled: bool = False
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    metrics: MetricsConfig = Field(default_factory=MetricsConfig)
    security: SecurityConfig = Field(default_factory=SecurityConfig)
    
    # Feature flags
    enable_metrics: bool = True
    enable_persistence: bool = True
    enable_security: bool = True
    enable_audit_logging: bool = True
    
    # Environment
    environment: Literal["development", "staging", "production"] = "development"
    debug: bool = False


# Helper functions for model serialization

def model_to_dict(model: BaseModel, exclude_none: bool = True) -> Dict[str, Any]:
    """Convert a Pydantic model to a dictionary."""
    return model.model_dump(exclude_none=exclude_none)


def dict_to_model(model_class: type, data: Dict[str, Any]) -> BaseModel:
    """Convert a dictionary to a Pydantic model."""
    return model_class.model_validate(data)


def models_to_dict_list(models: List[BaseModel], exclude_none: bool = True) -> List[Dict[str, Any]]:
    """Convert a list of Pydantic models to a list of dictionaries."""
    return [model_to_dict(model, exclude_none) for model in models]


def dict_list_to_models(model_class: type, data_list: List[Dict[str, Any]]) -> List[BaseModel]:
    """Convert a list of dictionaries to a list of Pydantic models."""
    return [dict_to_model(model_class, data) for data in data_list]