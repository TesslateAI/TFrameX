---
sidebar_position: 1
title: Enterprise Overview
---

# Enterprise Features Overview

TFrameX Enterprise provides production-ready features for deploying AI agent systems with persistent storage, basic monitoring, and security foundations.

## Available Features

### 💾 Enterprise Storage
- **Multiple Backends** - PostgreSQL, SQLite, S3, Redis storage implementations
- **Data Persistence** - Store conversations, user data, and application state
- **Connection Management** - Connection pooling and health monitoring
- **Migration Support** - Basic database migration capabilities

### 📊 Basic Monitoring
- **Prometheus Integration** - HTTP metrics endpoint for monitoring
- **Health Checks** - Application health status endpoints
- **Custom Metrics** - Define application-specific metrics

### 🔧 Configuration Management
- **YAML Configuration** - Structured configuration for enterprise features
- **Environment Integration** - Support for environment-based configuration
- **Storage Factory** - Centralized storage backend management

## Quick Start

```python
from tframex.enterprise import EnterpriseApp

# Create enterprise app with configuration
app = EnterpriseApp(
    enterprise_config={
        "storage": {
            "default": "postgresql",
            "backends": {
                "postgresql": {
                    "connection_string": "postgresql://user:pass@localhost/tframex"
                }
            }
        }
    },
    default_llm=my_llm
)
```

## Enterprise vs Standard

| Feature | Standard | Enterprise |
|---------|----------|------------|
| Basic Agents & Tools | ✅ | ✅ |
| MCP Integration | ✅ | ✅ |
| In-Memory Storage | ✅ | ✅ |
| Multiple Storage Backends | ❌ | ✅ |
| Prometheus Metrics | ❌ | ✅ |
| Enterprise Configuration | ❌ | ✅ |

## Configuration Examples

### Basic Storage Configuration

```yaml
# enterprise_config.yaml
storage:
  default: postgresql
  backends:
    postgresql:
      connection_string: "postgresql://user:pass@localhost/tframex"
      pool_size: 10
      max_overflow: 20
    
    redis:
      host: localhost
      port: 6379
      db: 0
      
    s3:
      bucket_name: "tframex-data"
      region: "us-east-1"
      access_key_id: "${AWS_ACCESS_KEY_ID}"
      secret_access_key: "${AWS_SECRET_ACCESS_KEY}"
```

### Metrics Configuration

```yaml
# enterprise_config.yaml  
metrics:
  enabled: true
  prometheus:
    port: 9090
    path: "/metrics"
    namespace: "tframex"
```

## Storage Backends

The enterprise module provides several storage backend implementations:

### PostgreSQL Storage
```python
from tframex.enterprise.storage import PostgreSQLStorage

storage = PostgreSQLStorage({
    "connection_string": "postgresql://user:pass@localhost/tframex",
    "pool_size": 10,
    "max_overflow": 20
})
```

### Redis Storage  
```python
from tframex.enterprise.storage import RedisStorage

storage = RedisStorage({
    "host": "localhost",
    "port": 6379,
    "db": 0,
    "password": "optional-password"
})
```

### S3 Storage
```python
from tframex.enterprise.storage import S3Storage

storage = S3Storage({
    "bucket_name": "tframex-data", 
    "region": "us-east-1",
    "access_key_id": "your-key",
    "secret_access_key": "your-secret"
})
```

### SQLite Storage
```python
from tframex.enterprise.storage import SQLiteStorage

storage = SQLiteStorage({
    "database_path": "/path/to/database.db",
    "timeout": 30
})
```

## Usage Examples

### Complete Enterprise Setup

```python
import asyncio
from tframex.enterprise import EnterpriseApp
from tframex.util.llms import OpenAIChatLLM

async def main():
    # Enterprise configuration
    config = {
        "storage": {
            "default": "postgresql",
            "backends": {
                "postgresql": {
                    "connection_string": "postgresql://user:pass@localhost/tframex",
                    "pool_size": 5
                }
            }
        },
        "metrics": {
            "enabled": True,
            "prometheus": {
                "port": 9090,
                "path": "/metrics"
            }
        }
    }
    
    # Create enterprise app
    app = EnterpriseApp(
        enterprise_config=config,
        default_llm=OpenAIChatLLM(
            api_key="your-openai-key",
            model_name="gpt-3.5-turbo"
        )
    )
    
    @app.agent(name="Assistant")
    async def assistant():
        pass
    
    # Run application
    async with app.run_context() as rt:
        result = await rt.call_agent("Assistant", "Hello!")
        print(f"Response: {result}")

if __name__ == "__main__":
    asyncio.run(main())
```

## Architecture

Enterprise features integrate with the core TFrameX framework:

```
┌─────────────────────────────────────────────────────┐
│               Enterprise Module                      │
├─────────────────────────────────────────────────────┤
│    Storage    │    Metrics    │    Configuration    │
├─────────────────────────────────────────────────────┤
│                  Core TFrameX                        │
│     Agents │ Tools │ Flows │ Memory │ MCP           │
└─────────────────────────────────────────────────────┘
```

## Next Steps

1. **[Storage](storage)** - Configure persistent storage backends
2. **[Metrics](metrics)** - Set up monitoring and metrics collection
3. **[Configuration](configuration)** - Learn about enterprise configuration options

## Limitations

Current enterprise features are foundational and include:

- **Storage backends** - Multiple persistent storage options
- **Basic metrics** - Prometheus integration only  
- **Configuration management** - YAML-based enterprise config
- **No authentication** - Security features not yet implemented
- **No RBAC** - Authorization features not yet implemented
- **No audit logging** - Compliance features not yet implemented