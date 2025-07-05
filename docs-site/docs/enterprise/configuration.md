---
sidebar_position: 2
title: Configuration
---

# Enterprise Configuration

This guide covers configuring TFrameX Enterprise features including security, metrics, storage, and other production settings.

## Configuration Methods

### 1. YAML Configuration File

```yaml
# enterprise_config.yaml
enterprise:
  enabled: true
  environment: production
  
  # Component configurations
  security: { ... }
  metrics: { ... }
  storage: { ... }
  session: { ... }
```

### 2. Python Dictionary

```python
config = {
    "enterprise": {
        "enabled": True,
        "environment": "production",
        "security": { ... },
        "metrics": { ... }
    }
}

app = EnterpriseApp(enterprise_config=config)
```

### 3. Environment Variables

```bash
export TFRAMEX_ENTERPRISE_ENABLED=true
export TFRAMEX_SECURITY_AUTH_PROVIDER=jwt
export TFRAMEX_METRICS_BACKEND=prometheus
export TFRAMEX_STORAGE_BACKEND=postgresql
```

### 4. Programmatic Configuration

```python
from tframex.enterprise import EnterpriseConfig

config = EnterpriseConfig()
config.security.authentication.add_provider("jwt", {...})
config.metrics.add_backend("prometheus", {...})

app = EnterpriseApp(enterprise_config=config)
```

## Complete Configuration Reference

### Root Configuration

```yaml
enterprise:
  # Enable/disable enterprise features
  enabled: true
  
  # Environment name
  environment: production  # development, staging, production
  
  # Application metadata
  app_name: "MyTFrameXApp"
  app_version: "1.0.0"
  
  # Global settings
  debug: false
  log_level: INFO
  timezone: UTC
```

### Security Configuration

```yaml
security:
  # Authentication configuration
  authentication:
    # Enable authentication
    enabled: true
    
    # Session timeout (seconds)
    session_timeout: 3600
    
    # Authentication providers
    providers:
      # JWT Provider
      - type: jwt
        enabled: true
        secret_key: ${JWT_SECRET}
        algorithm: HS256
        token_expiry: 3600
        refresh_enabled: true
        refresh_expiry: 86400
      
      # OAuth2 Provider
      - type: oauth2
        enabled: true
        client_id: ${OAUTH_CLIENT_ID}
        client_secret: ${OAUTH_CLIENT_SECRET}
        authorize_url: https://auth.example.com/authorize
        token_url: https://auth.example.com/token
        scopes: ["read", "write"]
      
      # API Key Provider
      - type: api_key
        enabled: true
        header_name: X-API-Key
        query_param: api_key
        validate_url: https://api.example.com/validate
      
      # Basic Auth Provider
      - type: basic
        enabled: true
        realm: "TFrameX Enterprise"
  
  # Authorization (RBAC) configuration
  rbac:
    enabled: true
    
    # Default role for new users
    default_role: viewer
    
    # Cache permissions for performance
    cache_permissions: true
    cache_ttl: 300
    
    # Role definitions
    roles:
      - name: admin
        description: "Full system access"
        permissions: ["*"]
        inherits: []
      
      - name: operator
        description: "Operate agents and flows"
        permissions:
          - "agent:create"
          - "agent:read"
          - "agent:update"
          - "agent:execute"
          - "tool:*"
          - "flow:*"
        inherits: ["viewer"]
      
      - name: developer
        description: "Develop and test agents"
        permissions:
          - "agent:*"
          - "tool:*"
          - "flow:*"
          - "metrics:read"
        inherits: ["viewer"]
      
      - name: viewer
        description: "Read-only access"
        permissions:
          - "*:read"
          - "metrics:read"
  
  # Audit logging configuration
  audit:
    enabled: true
    
    # Storage backend for audit logs
    storage: postgresql  # postgresql, s3, elasticsearch
    
    # Retention period (days)
    retention_days: 90
    
    # Events to audit
    events:
      - authentication
      - authorization
      - agent_execution
      - tool_execution
      - data_access
      - configuration_change
    
    # Sensitive data handling
    mask_sensitive_data: true
    sensitive_fields:
      - password
      - api_key
      - token
      - secret
```

### Metrics Configuration

```yaml
metrics:
  enabled: true
  
  # Default labels for all metrics
  default_labels:
    app: ${APP_NAME}
    environment: ${ENVIRONMENT}
    region: ${AWS_REGION}
  
  # Metric collection settings
  collection:
    interval: 60  # seconds
    batch_size: 100
    buffer_size: 1000
  
  # Metrics backends
  backends:
    # Prometheus
    prometheus:
      enabled: true
      port: 9090
      path: /metrics
      include_histogram: true
      buckets: [0.1, 0.5, 1.0, 2.5, 5.0, 10.0]
    
    # StatsD
    statsd:
      enabled: true
      host: localhost
      port: 8125
      prefix: tframex
      tags_enabled: true
    
    # OpenTelemetry
    opentelemetry:
      enabled: true
      endpoint: http://otel-collector:4317
      protocol: grpc  # grpc or http
      headers:
        api-key: ${OTEL_API_KEY}
      resource_attributes:
        service.name: tframex-enterprise
        service.version: 1.1.0
    
    # Custom metrics collector
    custom:
      enabled: false
      class: myapp.metrics.CustomCollector
      config:
        custom_param: value
```

### Storage Configuration

```yaml
storage:
  # Default storage backend
  default: postgresql
  
  # Storage backends
  backends:
    # PostgreSQL
    postgresql:
      enabled: true
      connection_string: ${DATABASE_URL}
      # or individual parameters:
      # host: localhost
      # port: 5432
      # database: tframex
      # user: ${DB_USER}
      # password: ${DB_PASSWORD}
      
      # Connection pool settings
      pool_size: 20
      max_overflow: 10
      pool_timeout: 30
      pool_recycle: 3600
      
      # Performance settings
      echo: false
      statement_timeout: 30000
      lock_timeout: 10000
    
    # S3 Storage
    s3:
      enabled: true
      bucket: ${S3_BUCKET}
      region: ${AWS_REGION}
      access_key_id: ${AWS_ACCESS_KEY_ID}
      secret_access_key: ${AWS_SECRET_ACCESS_KEY}
      
      # Optional settings
      endpoint_url: null  # For S3-compatible services
      use_ssl: true
      verify_ssl: true
      
      # Performance settings
      max_pool_connections: 50
      multipart_threshold: 8388608  # 8MB
      multipart_chunksize: 8388608  # 8MB
    
    # SQLite (for development/testing)
    sqlite:
      enabled: false
      path: ./data/tframex.db
      
      # Performance settings
      journal_mode: WAL
      synchronous: NORMAL
      cache_size: -64000  # 64MB
    
    # Redis (for caching/sessions)
    redis:
      enabled: true
      host: ${REDIS_HOST}
      port: 6379
      password: ${REDIS_PASSWORD}
      db: 0
      
      # Connection settings
      socket_timeout: 5
      socket_connect_timeout: 5
      socket_keepalive: true
      
      # Pool settings
      max_connections: 50
      
      # SSL settings
      ssl: false
      ssl_cert_reqs: required
      ssl_ca_certs: /path/to/ca.pem
```

### Session Management Configuration

```yaml
session:
  # Session storage backend
  backend: redis  # memory, redis, database
  
  # Session settings
  timeout: 3600  # seconds
  refresh_enabled: true
  refresh_threshold: 300  # Refresh if less than 5 minutes left
  
  # Cookie settings (for web interface)
  cookie:
    name: tframex_session
    secure: true  # HTTPS only
    httponly: true
    samesite: strict
    max_age: 3600
  
  # Cleanup settings
  cleanup:
    enabled: true
    interval: 3600  # Run cleanup every hour
    batch_size: 100
```

### Advanced Configuration

```yaml
# Performance tuning
performance:
  # Connection pooling
  connection_pool:
    size: 100
    timeout: 30
    retry_attempts: 3
    retry_delay: 1.0
  
  # Caching
  cache:
    enabled: true
    backend: redis
    ttl: 300
    max_size: 10000
  
  # Rate limiting
  rate_limiting:
    enabled: true
    requests_per_minute: 60
    burst_size: 10

# Monitoring and alerting
monitoring:
  # Health checks
  health_check:
    enabled: true
    endpoint: /health
    checks:
      - database
      - redis
      - disk_space
      - memory_usage
  
  # Alerting
  alerting:
    enabled: true
    providers:
      - type: email
        smtp_host: ${SMTP_HOST}
        recipients: ["ops@example.com"]
      - type: slack
        webhook_url: ${SLACK_WEBHOOK}
      - type: pagerduty
        api_key: ${PAGERDUTY_KEY}

# Integration settings
integrations:
  # Webhook notifications
  webhooks:
    enabled: true
    endpoints:
      - url: https://webhook.example.com/tframex
        events: ["agent.completed", "flow.failed"]
        headers:
          Authorization: Bearer ${WEBHOOK_TOKEN}
  
  # External APIs
  external_apis:
    timeout: 30
    retry_attempts: 3
    circuit_breaker:
      enabled: true
      failure_threshold: 5
      recovery_timeout: 60
```

## Configuration Best Practices

### 1. Environment-Specific Configs

```python
# config/development.yaml
enterprise:
  environment: development
  debug: true
  storage:
    default: sqlite

# config/production.yaml
enterprise:
  environment: production
  debug: false
  storage:
    default: postgresql
```

### 2. Secret Management

```yaml
# Use environment variables for secrets
security:
  authentication:
    providers:
      - type: jwt
        secret_key: ${JWT_SECRET}  # From environment

# Or use secret management services
security:
  secrets_manager:
    provider: aws_secrets_manager
    region: us-east-1
```

### 3. Configuration Validation

```python
from tframex.enterprise import validate_config

# Validate configuration before use
config = load_config("enterprise_config.yaml")
errors = validate_config(config)

if errors:
    for error in errors:
        print(f"Configuration error: {error}")
    sys.exit(1)
```

### 4. Dynamic Configuration

```python
from tframex.enterprise import DynamicConfig

# Support runtime configuration changes
dynamic_config = DynamicConfig(
    source="consul",  # or "etcd", "zookeeper"
    watch_changes=True
)

app = EnterpriseApp(enterprise_config=dynamic_config)
```

## Configuration Templates

### Minimal Configuration

```yaml
enterprise:
  enabled: true
  security:
    authentication:
      providers:
        - type: api_key
  storage:
    default: sqlite
```

### High-Security Configuration

```yaml
enterprise:
  enabled: true
  
  security:
    authentication:
      providers:
        - type: jwt
          algorithm: RS256
          public_key_path: /keys/public.pem
          private_key_path: /keys/private.pem
    
    rbac:
      enabled: true
      strict_mode: true
    
    audit:
      enabled: true
      encrypt_logs: true
      
  storage:
    backends:
      postgresql:
        connection_string: ${DATABASE_URL}
        ssl_mode: require
```

### High-Performance Configuration

```yaml
enterprise:
  enabled: true
  
  performance:
    connection_pool:
      size: 200
      timeout: 10
    
    cache:
      enabled: true
      backend: redis
      
  metrics:
    backends:
      statsd:
        enabled: true
        batch_size: 1000
```

## Troubleshooting

### Configuration Not Loading

```python
# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Check configuration path
from pathlib import Path
config_path = Path("enterprise_config.yaml")
print(f"Config exists: {config_path.exists()}")
print(f"Config path: {config_path.absolute()}")
```

### Invalid Configuration

```python
# Use configuration schema validation
from tframex.enterprise import ConfigSchema

schema = ConfigSchema()
errors = schema.validate(config)
for error in errors:
    print(f"Validation error: {error}")
```

### Environment Variables Not Working

```bash
# Check environment variables are set
env | grep TFRAMEX

# Export with correct prefix
export TFRAMEX_ENTERPRISE_ENABLED=true
export TFRAMEX_SECURITY_AUTH_PROVIDER=jwt
```

## Next Steps

- [Security Setup](security/overview) - Configure authentication and authorization
- [Metrics Setup](metrics) - Configure monitoring and metrics
- [Storage Setup](storage) - Configure data persistence
- [Deployment](deployment) - Deploy to production