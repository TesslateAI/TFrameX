# TFrameX Enterprise Architecture

This document outlines the enterprise-grade enhancements to TFrameX, including metrics engine, data persistence, and security framework.

## Overview

The enterprise enhancements provide:
1. **Metrics Engine**: Multi-backend monitoring and observability
2. **Data Persistence**: Flexible storage with multiple backends
3. **Security Framework**: Authentication, authorization, and audit logging

## Core Design Principles

1. **Backward Compatibility**: All existing APIs remain unchanged
2. **Pluggable Architecture**: Optional enterprise features via configuration
3. **Performance First**: Minimal overhead when features are disabled
4. **Security by Design**: Zero-trust architecture with audit trails
5. **Scalability**: Support from development to enterprise deployment

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    TFrameX Enterprise                           │
├─────────────────┬─────────────────┬─────────────────┬───────────┤
│   Metrics       │   Persistence   │   Security      │   Core    │
│   Engine        │   Layer         │   Framework     │   TFrameX │
├─────────────────┼─────────────────┼─────────────────┼───────────┤
│ • Prometheus    │ • PostgreSQL    │ • OAuth2        │ • Agents  │
│ • StatsD        │ • SQLite        │ • RBAC          │ • Tools   │
│ • OpenTelemetry │ • S3            │ • API Keys      │ • Flows   │
│ • Custom        │ • InMemory      │ • Audit Logs    │ • MCP     │
├─────────────────┴─────────────────┴─────────────────┴───────────┤
│                    Configuration & Middleware                   │
└─────────────────────────────────────────────────────────────────┘
```

## Component Architecture

### 1. Metrics Engine

#### Core Components
- **MetricsCollector**: Abstract base for metric collection
- **MetricsExporter**: Exports metrics to various backends
- **TracingSystem**: Distributed tracing for multi-agent workflows
- **PerformanceMonitor**: Latency and performance tracking

#### Supported Backends
- **Prometheus**: Production metrics and alerting
- **StatsD**: Real-time metric streaming
- **OpenTelemetry**: Distributed tracing and observability
- **Custom**: User-defined metric backends

#### Key Metrics
- Agent execution time and success/failure rates
- Tool call latency and error rates
- Flow execution metrics and step timing
- System resource utilization
- MCP server performance

### 2. Data Persistence Layer

#### Storage Abstraction
```python
class BaseStorage:
    async def write(self, table: str, data: Dict[str, Any]) -> str
    async def read(self, table: str, filters: Dict[str, Any]) -> List[Dict[str, Any]]
    async def update(self, table: str, id: str, data: Dict[str, Any]) -> bool
    async def delete(self, table: str, id: str) -> bool
```

#### Storage Backends
- **InMemoryStorage**: Development and testing
- **SQLiteStorage**: Single-node deployments
- **PostgreSQLStorage**: Production scalable deployments
- **S3Storage**: Archival and audit log storage

#### Data Models

##### Core Tables
```sql
-- Users and Authentication
CREATE TABLE users (
    id UUID PRIMARY KEY,
    username VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE,
    password_hash VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    is_active BOOLEAN DEFAULT TRUE
);

-- Roles and Permissions
CREATE TABLE roles (
    id UUID PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE permissions (
    id UUID PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    resource VARCHAR(100) NOT NULL,
    action VARCHAR(50) NOT NULL,
    description TEXT
);

CREATE TABLE role_permissions (
    role_id UUID REFERENCES roles(id) ON DELETE CASCADE,
    permission_id UUID REFERENCES permissions(id) ON DELETE CASCADE,
    PRIMARY KEY (role_id, permission_id)
);

CREATE TABLE user_roles (
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    role_id UUID REFERENCES roles(id) ON DELETE CASCADE,
    assigned_at TIMESTAMP DEFAULT NOW(),
    assigned_by UUID REFERENCES users(id),
    PRIMARY KEY (user_id, role_id)
);

-- Conversations and Messages
CREATE TABLE conversations (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    agent_name VARCHAR(255) NOT NULL,
    title VARCHAR(500),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    metadata JSONB
);

CREATE TABLE messages (
    id UUID PRIMARY KEY,
    conversation_id UUID REFERENCES conversations(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL CHECK (role IN ('system', 'user', 'assistant', 'tool')),
    content TEXT,
    tool_calls JSONB,
    tool_call_id VARCHAR(255),
    name VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW(),
    metadata JSONB
);

-- Flow Executions
CREATE TABLE flow_executions (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    flow_name VARCHAR(255) NOT NULL,
    status VARCHAR(50) DEFAULT 'running',
    initial_input TEXT,
    final_output TEXT,
    started_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP,
    error_message TEXT,
    metadata JSONB
);

CREATE TABLE flow_steps (
    id UUID PRIMARY KEY,
    execution_id UUID REFERENCES flow_executions(id) ON DELETE CASCADE,
    step_name VARCHAR(255) NOT NULL,
    step_type VARCHAR(100) NOT NULL,
    input_data TEXT,
    output_data TEXT,
    status VARCHAR(50) DEFAULT 'pending',
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    error_message TEXT,
    step_order INTEGER NOT NULL
);

-- Agent Executions
CREATE TABLE agent_executions (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    conversation_id UUID REFERENCES conversations(id),
    flow_execution_id UUID REFERENCES flow_executions(id),
    agent_name VARCHAR(255) NOT NULL,
    input_message TEXT,
    output_message TEXT,
    execution_time_ms INTEGER,
    tool_calls_count INTEGER DEFAULT 0,
    status VARCHAR(50) DEFAULT 'success',
    error_message TEXT,
    started_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP,
    metadata JSONB
);

-- Tool Calls
CREATE TABLE tool_calls (
    id UUID PRIMARY KEY,
    agent_execution_id UUID REFERENCES agent_executions(id) ON DELETE CASCADE,
    tool_name VARCHAR(255) NOT NULL,
    tool_type VARCHAR(50) NOT NULL, -- 'native', 'mcp', 'agent'
    arguments JSONB,
    result TEXT,
    execution_time_ms INTEGER,
    status VARCHAR(50) DEFAULT 'success',
    error_message TEXT,
    called_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP
);

-- Metrics
CREATE TABLE metrics (
    id UUID PRIMARY KEY,
    metric_name VARCHAR(255) NOT NULL,
    metric_type VARCHAR(50) NOT NULL, -- 'counter', 'gauge', 'histogram', 'timer'
    value DECIMAL,
    labels JSONB,
    timestamp TIMESTAMP DEFAULT NOW(),
    source VARCHAR(100)
);

-- Events and Audit Logs
CREATE TABLE events (
    id UUID PRIMARY KEY,
    event_type VARCHAR(100) NOT NULL,
    event_source VARCHAR(100) NOT NULL,
    user_id UUID REFERENCES users(id),
    resource_type VARCHAR(100),
    resource_id VARCHAR(255),
    action VARCHAR(100) NOT NULL,
    status VARCHAR(50) DEFAULT 'success',
    details JSONB,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE audit_logs (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(100) NOT NULL,
    resource_id VARCHAR(255),
    old_values JSONB,
    new_values JSONB,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);
```

##### Indexes for Performance
```sql
-- Performance indexes
CREATE INDEX idx_conversations_user_created ON conversations(user_id, created_at DESC);
CREATE INDEX idx_messages_conversation_created ON messages(conversation_id, created_at);
CREATE INDEX idx_flow_executions_user_started ON flow_executions(user_id, started_at DESC);
CREATE INDEX idx_flow_steps_execution_order ON flow_steps(execution_id, step_order);
CREATE INDEX idx_agent_executions_started ON agent_executions(started_at DESC);
CREATE INDEX idx_tool_calls_agent_called ON tool_calls(agent_execution_id, called_at);
CREATE INDEX idx_metrics_name_timestamp ON metrics(metric_name, timestamp DESC);
CREATE INDEX idx_events_type_created ON events(event_type, created_at DESC);
CREATE INDEX idx_audit_logs_user_created ON audit_logs(user_id, created_at DESC);
```

### 3. Security Framework

#### Authentication Providers
- **OAuth2Provider**: OAuth 2.0 / OpenID Connect
- **APIKeyProvider**: API key authentication
- **BasicAuthProvider**: Username/password authentication
- **JWTProvider**: JSON Web Token authentication

#### Authorization System
- **RBAC Engine**: Role-based access control
- **Permission Manager**: Fine-grained permissions
- **Resource Guard**: Resource-level access control
- **Audit Logger**: Security event logging

#### Security Middleware
- **AuthenticationMiddleware**: Request authentication
- **AuthorizationMiddleware**: Request authorization
- **AuditMiddleware**: Security audit logging
- **RateLimitMiddleware**: Request rate limiting

#### Default Permissions
```python
PERMISSIONS = {
    # Agent permissions
    "agent.execute": "Execute agents",
    "agent.view": "View agent definitions",
    "agent.manage": "Create/modify agents",
    
    # Tool permissions  
    "tool.call": "Call tools",
    "tool.view": "View tool definitions",
    "tool.manage": "Create/modify tools",
    
    # Flow permissions
    "flow.execute": "Execute flows",
    "flow.view": "View flow definitions", 
    "flow.manage": "Create/modify flows",
    
    # Data permissions
    "data.read": "Read conversation data",
    "data.write": "Write conversation data",
    "data.delete": "Delete data",
    
    # Admin permissions
    "user.manage": "Manage users",
    "role.manage": "Manage roles",
    "system.admin": "System administration",
    "metrics.view": "View metrics",
    "audit.view": "View audit logs"
}

DEFAULT_ROLES = {
    "user": ["agent.execute", "tool.call", "flow.execute", "data.read", "data.write"],
    "developer": ["agent.view", "tool.view", "flow.view", "metrics.view"],
    "admin": ["user.manage", "role.manage", "system.admin", "audit.view"],
    "operator": ["metrics.view", "system.admin"]
}
```

## Integration Strategy

### 1. Backward Compatibility
All enterprise features are optional and enabled via configuration:

```python
app = TFrameXApp(
    # Existing configuration remains unchanged
    default_llm=my_llm,
    
    # New enterprise features (all optional)
    enable_metrics=True,
    metrics_config={
        "backends": ["prometheus", "statsd"],
        "export_interval": 60
    },
    enable_persistence=True,
    persistence_config={
        "backend": "postgresql",
        "connection_string": "postgresql://..."
    },
    enable_security=True,
    security_config={
        "auth_providers": ["oauth2", "api_key"],
        "require_auth": True
    }
)
```

### 2. Middleware Integration
Enterprise features integrate via middleware pattern:

```python
# Automatic middleware registration when features are enabled
app.add_middleware(MetricsMiddleware)      # When metrics enabled
app.add_middleware(PersistenceMiddleware)  # When persistence enabled  
app.add_middleware(SecurityMiddleware)     # When security enabled
```

### 3. Configuration-Driven Features
```yaml
# Enterprise configuration
enterprise:
  metrics:
    enabled: true
    backends:
      prometheus:
        enabled: true
        port: 9090
      statsd:
        enabled: true
        host: "localhost"
        port: 8125
      opentelemetry:
        enabled: true
        endpoint: "http://jaeger:14268/api/traces"
    
  persistence:
    enabled: true
    backend: "postgresql"
    connection_string: "${DATABASE_URL}"
    migrations: true
    
  security:
    enabled: true
    auth_providers:
      oauth2:
        enabled: true
        issuer: "${OAUTH2_ISSUER}"
        client_id: "${OAUTH2_CLIENT_ID}"
      api_key:
        enabled: true
        header_name: "X-API-Key"
    rbac:
      enabled: true
      default_role: "user"
```

## Performance Considerations

### 1. Async by Design
All enterprise features use async/await for non-blocking operations:

```python
async def collect_metrics(self, event: MetricEvent):
    # Non-blocking metric collection
    await self.metrics_collector.record(event)

async def persist_conversation(self, conversation: Conversation):
    # Non-blocking data persistence
    await self.storage.save(conversation)

async def authenticate_user(self, token: str) -> User:
    # Non-blocking authentication
    return await self.auth_provider.verify(token)
```

### 2. Connection Pooling
- Database connection pools for efficient resource usage
- HTTP client pools for external service calls
- Cache pools for frequent data access

### 3. Batch Operations
- Batch metric exports to reduce overhead
- Bulk database operations for high-throughput scenarios
- Streaming for large data transfers

### 4. Caching Strategy
- User authentication cache
- Permission cache with TTL
- Metric aggregation cache
- Conversation metadata cache

## Security Principles

### 1. Zero Trust Architecture
- All requests require authentication
- Least privilege access by default
- Continuous verification and audit

### 2. Defense in Depth
- Multiple security layers
- Input validation at all boundaries
- Output sanitization and encoding

### 3. Audit Everything
- All user actions logged
- Security events tracked
- Data access monitored

### 4. Secure by Default
- Secure default configurations
- Automatic security updates
- Encrypted data in transit and at rest

## Deployment Scenarios

### 1. Development
```python
app = TFrameXApp(
    # Minimal configuration for development
    enable_metrics=False,
    enable_persistence=True,
    persistence_config={"backend": "sqlite"},
    enable_security=False
)
```

### 2. Staging
```python
app = TFrameXApp(
    enable_metrics=True,
    metrics_config={"backends": ["prometheus"]},
    enable_persistence=True,
    persistence_config={"backend": "postgresql"},
    enable_security=True,
    security_config={"auth_providers": ["api_key"]}
)
```

### 3. Production
```python
app = TFrameXApp(
    enable_metrics=True,
    metrics_config={
        "backends": ["prometheus", "opentelemetry"],
        "high_availability": True
    },
    enable_persistence=True,
    persistence_config={
        "backend": "postgresql",
        "read_replicas": True,
        "backup_to_s3": True
    },
    enable_security=True,
    security_config={
        "auth_providers": ["oauth2", "api_key"],
        "rate_limiting": True,
        "audit_level": "full"
    }
)
```

This architecture provides enterprise-grade capabilities while maintaining the simplicity and flexibility that makes TFrameX powerful for development and prototyping.