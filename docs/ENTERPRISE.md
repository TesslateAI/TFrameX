# TFrameX Enterprise Documentation

Welcome to TFrameX Enterprise - the production-ready extension of TFrameX that adds comprehensive enterprise features for scalable, secure, and monitored AI agent applications.

## Table of Contents

1. [Quick Start](#quick-start)
2. [Architecture Overview](#architecture-overview)
3. [Configuration](#configuration)
4. [Storage Backends](#storage-backends)
5. [Metrics & Monitoring](#metrics--monitoring)
6. [Security Features](#security-features)
7. [Deployment Guide](#deployment-guide)
8. [API Reference](#api-reference)
9. [Examples](#examples)
10. [Migration Guide](#migration-guide)

## Quick Start

### Installation

```bash
# Install TFrameX with enterprise dependencies
pip install tframex[enterprise]

# Or install individual enterprise dependencies as needed
pip install tframex prometheus-client asyncpg aioboto3 cryptography PyJWT
```

### Basic Enterprise Setup

```python
from tframex.enterprise import EnterpriseApp, create_default_config

# Create enterprise configuration
config = create_default_config(environment="development")

# Create enterprise application
app = EnterpriseApp(
    default_llm=your_llm,
    enterprise_config=config
)

# Define agents (same as core TFrameX)
@app.agent(name="MyAgent", system_prompt="You are a helpful assistant.")
async def my_agent(): pass

async def main():
    # Initialize and start enterprise features
    async with app:
        # Enterprise features (metrics, security, audit) are now active
        async with app.run_context() as ctx:
            response = await ctx.call_agent("MyAgent", "Hello!")
            print(response.content)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
```

### Configuration File Setup

Create `enterprise_config.yaml`:

```yaml
# Basic enterprise configuration
enabled: true
environment: development

storage:
  sqlite:
    type: sqlite
    enabled: true
    config:
      database_path: "data/tframex.db"

metrics:
  enabled: true
  backends:
    prometheus:
      type: prometheus
      enabled: true
      port: 8090

security:
  authentication:
    enabled: true
    providers:
      api_key:
        type: api_key
        enabled: true
  authorization:
    enabled: true
  audit:
    enabled: true
```

Load the configuration:

```python
from tframex.enterprise import EnterpriseApp, load_enterprise_config

config = load_enterprise_config("enterprise_config.yaml")
app = EnterpriseApp(enterprise_config=config)
```

## Architecture Overview

TFrameX Enterprise extends the core framework with additional layers:

```
┌─────────────────────────────────────────────────────────────┐
│                    TFrameX Core                             │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────────────────┐ │
│  │   Agents    │ │    Tools    │ │        Flows            │ │
│  └─────────────┘ └─────────────┘ └─────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────────┐
│                TFrameX Enterprise                           │
│ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────┐ │
│ │  Metrics &  │ │   Storage   │ │  Security   │ │  Audit  │ │
│ │ Monitoring  │ │  Backends   │ │   & RBAC    │ │Logging  │ │
│ └─────────────┘ └─────────────┘ └─────────────┘ └─────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### Key Components

1. **EnterpriseApp**: Extended TFrameX application with enterprise features
2. **Storage Layer**: Unified interface for data persistence across multiple backends
3. **Metrics Engine**: Comprehensive metrics collection and export
4. **Security Framework**: Authentication, authorization, and session management
5. **Audit System**: Complete audit logging for compliance and monitoring

## Configuration

### Configuration Sources

TFrameX Enterprise supports multiple configuration sources with the following priority:

1. **Direct Configuration Object**: `EnterpriseConfig` instance
2. **Configuration File**: YAML or JSON files
3. **Environment Variables**: `TFRAMEX_ENTERPRISE_*` prefixed variables
4. **Defaults**: Built-in sensible defaults

### Configuration Structure

```python
from tframex.enterprise import EnterpriseConfig

config = EnterpriseConfig(
    enabled=True,
    environment="production",
    debug=False,
    
    storage={
        "postgresql": {
            "type": "postgresql",
            "enabled": True,
            "config": {
                "host": "localhost",
                "database": "tframex",
                "username": "tframex_user",
                "password": "secure_password"
            }
        }
    },
    
    metrics={
        "enabled": True,
        "backends": {
            "prometheus": {
                "type": "prometheus",
                "enabled": True,
                "port": 8090
            }
        }
    },
    
    security={
        "authentication": {
            "enabled": True,
            "providers": {
                "jwt": {
                    "type": "jwt",
                    "enabled": True,
                    "secret_key": "your-jwt-secret"
                }
            }
        },
        "authorization": {
            "enabled": True,
            "default_role": "user"
        }
    }
)
```

### Environment Variables

Set enterprise configuration via environment variables:

```bash
# Core settings
export TFRAMEX_ENTERPRISE_ENABLED=true
export TFRAMEX_ENTERPRISE_ENVIRONMENT=production

# Storage configuration
export TFRAMEX_ENTERPRISE_STORAGE_TYPE=postgresql
export TFRAMEX_ENTERPRISE_STORAGE_HOST=db.example.com
export TFRAMEX_ENTERPRISE_STORAGE_DATABASE=tframex_prod

# Security configuration
export TFRAMEX_ENTERPRISE_SECURITY_JWT_SECRET_KEY=your-production-secret
export TFRAMEX_ENTERPRISE_SECURITY_AUTHENTICATION_ENABLED=true
```

## Storage Backends

TFrameX Enterprise provides a unified storage abstraction supporting multiple backends:

### Available Backends

#### 1. SQLite (Development)
```yaml
storage:
  sqlite:
    type: sqlite
    config:
      database_path: "data/tframex.db"
      pool_size: 10
      wal_mode: true
```

#### 2. PostgreSQL (Production)
```yaml
storage:
  postgresql:
    type: postgresql
    config:
      host: "localhost"
      port: 5432
      database: "tframex"
      username: "tframex_user"
      password: "secure_password"
      pool_size: 20
      ssl_mode: "require"
```

#### 3. S3 (Archive/Scale)
```yaml
storage:
  s3:
    type: s3
    config:
      bucket_name: "tframex-data"
      region: "us-east-1"
      prefix: "tframex/"
      encryption: true
```

#### 4. In-Memory (Testing)
```yaml
storage:
  memory:
    type: memory
    config:
      max_size: 10000
```

### Storage Usage

```python
# Get default storage backend
storage = app.get_storage()

# Store data
await storage.insert("conversations", {
    "id": "conv_123",
    "user_id": "user_456",
    "messages": [],
    "created_at": datetime.utcnow().isoformat()
})

# Query data
conversations = await storage.select(
    "conversations",
    filters={"user_id": "user_456"},
    limit=10
)

# Update data
await storage.update("conversations", "conv_123", {
    "updated_at": datetime.utcnow().isoformat()
})
```

### Data Migration

Migrate data between storage backends:

```python
from tframex.enterprise.storage.factory import migrate_storage

await migrate_storage(
    source_type="sqlite",
    source_config={"database_path": "old.db"},
    target_type="postgresql",
    target_config=postgresql_config,
    tables=["conversations", "users", "audit_logs"]
)
```

## Metrics & Monitoring

### Supported Backends

#### 1. Prometheus
```yaml
metrics:
  backends:
    prometheus:
      type: prometheus
      enabled: true
      port: 8090
      host: "0.0.0.0"
```

Access metrics at `http://localhost:8090/metrics`

#### 2. StatsD
```yaml
metrics:
  backends:
    statsd:
      type: statsd
      enabled: true
      host: "localhost"
      port: 8125
      prefix: "tframex"
```

#### 3. OpenTelemetry
```yaml
metrics:
  backends:
    opentelemetry:
      type: opentelemetry
      enabled: true
      endpoint: "http://jaeger:4317"
      service_name: "tframex-app"
      enable_tracing: true
```

#### 4. Custom Backends
```python
from tframex.enterprise.metrics.custom import CustomMetricsBackend

class MyCustomBackend(CustomMetricsBackend):
    async def send_metric(self, metric):
        # Send to your custom system
        pass

# Register in configuration
config.metrics.backends["custom"] = {
    "type": "custom",
    "backend_class": MyCustomBackend,
    "backend_config": {}
}
```

### Using Metrics

```python
# Get metrics manager
metrics = app.get_metrics_manager()

# Record metrics
await metrics.increment_counter(
    "agent_calls_total",
    labels={"agent_name": "MyAgent"}
)

await metrics.set_gauge(
    "active_sessions",
    session_count
)

# Time operations
async with metrics.timer("agent_response_time"):
    response = await ctx.call_agent("MyAgent", message)
```

### Built-in Metrics

TFrameX Enterprise automatically collects:

- `tframex_agent_calls_total`: Total agent invocations
- `tframex_agent_errors_total`: Agent execution errors
- `tframex_tool_calls_total`: Tool usage statistics
- `tframex_flow_executions_total`: Flow execution counts
- `tframex_response_time_seconds`: Response time histograms
- `tframex_active_sessions`: Current active sessions
- `tframex_storage_operations_total`: Storage operation counts

## Security Features

### Authentication

TFrameX Enterprise supports multiple authentication methods:

#### 1. API Key Authentication
```python
from tframex.enterprise.security.auth import APIKeyProvider

# Create API key for user
provider = app.get_auth_provider("api_key")
api_key = await provider.create_api_key(user_id)

# Authenticate requests
auth_result = await provider.authenticate({"api_key": api_key})
```

#### 2. JWT Authentication
```python
from tframex.enterprise.security.auth import JWTProvider

provider = app.get_auth_provider("jwt")
token = provider.generate_token(user)

# Validate token
auth_result = await provider.validate_token(token)
```

#### 3. OAuth2 Authentication
```yaml
security:
  authentication:
    providers:
      oauth2_google:
        type: oauth2
        client_id: "your-client-id"
        client_secret: "your-client-secret"
        issuer: "https://accounts.google.com"
```

### Authorization (RBAC)

Role-Based Access Control with hierarchical permissions:

```python
rbac = app.get_rbac_engine()

# Create roles
await rbac.create_role(
    name="agent_user",
    display_name="Agent User",
    description="Can use agents",
    permissions=["agents:call", "tools:use"]
)

await rbac.create_role(
    name="admin",
    display_name="Administrator", 
    description="Full access",
    permissions=["*:*"]
)

# Assign roles
await rbac.assign_role(user.id, "agent_user")

# Check permissions
has_permission = await rbac.check_permission(
    user, 
    resource="agents", 
    action="call"
)

# Require permissions (raises exception if denied)
await rbac.require_permission(user, "agents", "call")
```

### Session Management

Secure session handling with automatic cleanup:

```python
session_manager = app.get_session_manager()

# Create session
session = await session_manager.create_session(
    user,
    data={"preferences": {"theme": "dark"}}
)

# Validate session
session = await session_manager.get_session(session_id)
if session and session.is_valid:
    # Session is active
    pass

# Update session
await session_manager.update_session(
    session_id,
    {"last_activity": datetime.utcnow()}
)
```

### Security Middleware

Automatic security enforcement:

```python
# Security is automatically applied to enterprise contexts
async with app.run_context(user=authenticated_user) as ctx:
    # All calls automatically include:
    # - Authentication verification
    # - Authorization checks
    # - Audit logging
    # - Session management
    response = await ctx.call_agent("SecureAgent", message)
```

## Audit Logging

Comprehensive audit trails for compliance:

```python
audit_logger = app.get_audit_logger()

# Log events
await audit_logger.log_event(
    event_type="user_action",
    user_id=user.id,
    resource="agent",
    action="call",
    outcome="success",
    details={"agent_name": "MyAgent"}
)

# Search audit logs
from tframex.enterprise.security.audit import AuditFilter

filter = AuditFilter(
    user_ids=[user.id],
    start_time=datetime.utcnow() - timedelta(days=7)
)
events = await audit_logger.search_events(filter)

# Generate compliance reports
report = await audit_logger.get_compliance_report(
    start_time=datetime.utcnow() - timedelta(days=30),
    end_time=datetime.utcnow()
)
```

### Automatic Audit Events

TFrameX Enterprise automatically logs:

- Authentication attempts (success/failure)
- Authorization decisions
- Agent invocations
- Tool usage
- Flow executions
- Data access operations
- Configuration changes
- Security events

## Deployment Guide

### Docker Deployment

```dockerfile
FROM python:3.11

# Install TFrameX Enterprise
RUN pip install tframex[enterprise]

# Copy application
COPY . /app
WORKDIR /app

# Run application
CMD ["python", "app.py"]
```

### Docker Compose with PostgreSQL and Prometheus

```yaml
version: '3.8'

services:
  tframex-app:
    build: .
    environment:
      - TFRAMEX_ENTERPRISE_STORAGE_TYPE=postgresql
      - TFRAMEX_ENTERPRISE_STORAGE_HOST=postgres
      - TFRAMEX_ENTERPRISE_STORAGE_DATABASE=tframex
      - TFRAMEX_ENTERPRISE_STORAGE_USERNAME=tframex
      - TFRAMEX_ENTERPRISE_STORAGE_PASSWORD=secure_password
    depends_on:
      - postgres
      - prometheus
    ports:
      - "8000:8000"
      - "8090:8090"  # Metrics endpoint

  postgres:
    image: postgres:15
    environment:
      - POSTGRES_DB=tframex
      - POSTGRES_USER=tframex
      - POSTGRES_PASSWORD=secure_password
    volumes:
      - postgres_data:/var/lib/postgresql/data

  prometheus:
    image: prom/prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml

volumes:
  postgres_data:
```

### Kubernetes Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: tframex-enterprise
spec:
  replicas: 3
  selector:
    matchLabels:
      app: tframex-enterprise
  template:
    metadata:
      labels:
        app: tframex-enterprise
    spec:
      containers:
      - name: tframex
        image: tframex-enterprise:latest
        env:
        - name: TFRAMEX_ENTERPRISE_ENVIRONMENT
          value: "production"
        - name: TFRAMEX_ENTERPRISE_STORAGE_TYPE
          value: "postgresql"
        ports:
        - containerPort: 8000
        - containerPort: 8090
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
```

### Production Considerations

1. **Database**: Use PostgreSQL or managed database service
2. **Secrets**: Use environment variables or secret management
3. **Monitoring**: Set up Prometheus/Grafana dashboards
4. **Logging**: Configure structured logging with log aggregation
5. **Backup**: Regular database backups and disaster recovery
6. **Scaling**: Horizontal scaling with load balancers
7. **Security**: Network security, TLS/SSL, and security scanning

## API Reference

### EnterpriseApp

```python
class EnterpriseApp(TFrameXApp):
    def __init__(
        self,
        default_llm: Optional[BaseLLMWrapper] = None,
        enterprise_config: Optional[Union[str, Path, Dict, EnterpriseConfig]] = None,
        auto_initialize: bool = True
    )
    
    async def initialize_enterprise(self) -> None
    async def start_enterprise(self) -> None
    async def stop_enterprise(self) -> None
    
    def get_storage(self, name: Optional[str] = None) -> BaseStorage
    def get_metrics_manager(self) -> Optional[MetricsManager]
    def get_rbac_engine(self) -> Optional[RBACEngine]
    def get_session_manager(self) -> Optional[SessionManager]
    def get_audit_logger(self) -> Optional[AuditLogger]
    
    async def health_check(self) -> Dict[str, Any]
```

### Storage Interface

```python
class BaseStorage:
    async def insert(self, table: str, data: Dict[str, Any]) -> str
    async def select(self, table: str, filters: Optional[Dict] = None) -> List[Dict]
    async def update(self, table: str, id: str, data: Dict[str, Any]) -> None
    async def delete(self, table: str, id: str) -> None
    async def count(self, table: str, filters: Optional[Dict] = None) -> int
```

### Metrics Interface

```python
class MetricsManager:
    async def increment_counter(self, name: str, value: float = 1, labels: Optional[Dict] = None)
    async def set_gauge(self, name: str, value: float, labels: Optional[Dict] = None)
    async def record_histogram(self, name: str, value: float, labels: Optional[Dict] = None)
    async def record_timer(self, name: str, duration: float, labels: Optional[Dict] = None)
    
    def timer(self, name: str, labels: Optional[Dict] = None) -> MetricTimer
```

## Examples

### Complete Enterprise Application

```python
import asyncio
from tframex.enterprise import EnterpriseApp, load_enterprise_config
from tframex.util.llms import OpenAIChatLLM

async def main():
    # Load configuration
    config = load_enterprise_config("enterprise_config.yaml")
    
    # Create LLM
    llm = OpenAIChatLLM(model_name="gpt-3.5-turbo")
    
    # Create enterprise app
    app = EnterpriseApp(
        default_llm=llm,
        enterprise_config=config
    )
    
    # Define secure agent
    @app.agent(
        name="SecureAssistant",
        description="Enterprise assistant with full audit trail",
        system_prompt="You are a secure enterprise assistant. Help users with their requests."
    )
    async def secure_assistant():
        pass
    
    # Start enterprise services
    async with app:
        # Create authenticated user context
        from tframex.enterprise.models import User
        user = User(username="admin", email="admin@company.com")
        
        # Use enterprise context
        async with app.run_context(user=user) as ctx:
            # This call is automatically:
            # - Authenticated and authorized
            # - Metered and monitored
            # - Audit logged
            response = await ctx.call_agent(
                "SecureAssistant", 
                "What can you help me with?"
            )
            print(f"Response: {response.content}")
            
            # Check health
            health = await app.health_check()
            print(f"System healthy: {health['healthy']}")

if __name__ == "__main__":
    asyncio.run(main())
```

### Custom Authentication Provider

```python
from tframex.enterprise.security.auth import AuthenticationProvider, AuthenticationResult

class LDAPAuthProvider(AuthenticationProvider):
    async def authenticate(self, credentials: Dict[str, Any]) -> AuthenticationResult:
        username = credentials.get("username")
        password = credentials.get("password")
        
        # Implement LDAP authentication logic
        if self.validate_ldap_credentials(username, password):
            user = await self.get_user_from_ldap(username)
            return AuthenticationResult(success=True, user=user)
        else:
            return AuthenticationResult(success=False, error="Invalid credentials")
    
    async def validate_token(self, token: str) -> AuthenticationResult:
        # Implement token validation if needed
        pass

# Use in configuration
config.security.authentication.providers["ldap"] = {
    "type": "custom",
    "provider_class": LDAPAuthProvider,
    "config": {"ldap_server": "ldap://company.com"}
}
```

### Custom Metrics Backend

```python
from tframex.enterprise.metrics.custom import CustomMetricsBackend

class DatadogMetricsBackend(CustomMetricsBackend):
    async def send_metric(self, metric):
        # Send to Datadog API
        await self.datadog_client.send_metric(
            metric.name,
            metric.value,
            tags=list(metric.labels.items())
        )

# Use in configuration
config.metrics.backends["datadog"] = {
    "type": "custom",
    "backend_class": DatadogMetricsBackend,
    "backend_config": {"api_key": "your-datadog-key"}
}
```

## Migration Guide

### From Core TFrameX to Enterprise

1. **Update imports**:
```python
# Before
from tframex import TFrameXApp

# After
from tframex.enterprise import EnterpriseApp
```

2. **Update app initialization**:
```python
# Before
app = TFrameXApp(default_llm=llm)

# After
from tframex.enterprise import create_default_config
config = create_default_config()
app = EnterpriseApp(default_llm=llm, enterprise_config=config)
```

3. **Add enterprise context**:
```python
# Before
async with app.run_context() as ctx:
    response = await ctx.call_agent("MyAgent", message)

# After
async with app:  # Starts enterprise services
    async with app.run_context() as ctx:
        response = await ctx.call_agent("MyAgent", message)
```

### Gradual Enterprise Adoption

You can gradually adopt enterprise features:

```python
# Start with basic enterprise app
config = EnterpriseConfig(
    enabled=True,
    storage={"memory": {"type": "memory", "enabled": True}},
    metrics={"enabled": False},  # Disable initially
    security={"authentication": {"enabled": False}}  # Disable initially
)

app = EnterpriseApp(enterprise_config=config)
```

Then enable features incrementally:
1. Enable metrics collection
2. Add authentication
3. Enable authorization
4. Add audit logging
5. Switch to production storage

### Performance Considerations

Enterprise features add minimal overhead:

- **Storage**: ~1ms per operation (varies by backend)
- **Metrics**: ~0.1ms per metric (async collection)
- **Security**: ~2ms per request (with caching)
- **Audit**: ~0.5ms per event (with buffering)

Total overhead: ~3-5ms per agent call, with comprehensive enterprise features.

## Support

For enterprise support:

- 📧 Email: enterprise@tesslate.ai
- 💬 Discord: [TFrameX Discord](https://discord.gg/DkzMzwBTaw)
- 📚 Documentation: [TFrameX Docs](https://tframex.tesslate.com/)
- 🐛 Issues: [GitHub Issues](https://github.com/TesslateAI/TFrameX/issues)

Enterprise customers receive priority support, dedicated consultation, and custom feature development.