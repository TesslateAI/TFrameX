# TFrameX Comprehensive Guide

This comprehensive guide provides everything you need to know about TFrameX - from basic concepts to advanced enterprise deployment. This document serves as the definitive reference for developers, architects, and users of the TFrameX framework.

## Table of Contents

1. [Framework Overview](#framework-overview)
2. [Core Concepts](#core-concepts)
3. [Quick Start Guide](#quick-start-guide)
4. [Architecture Deep Dive](#architecture-deep-dive)
5. [Development Patterns](#development-patterns)
6. [Configuration Management](#configuration-management)
7. [MCP Integration](#mcp-integration)
8. [Production Deployment](#production-deployment)
9. [Best Practices](#best-practices)
10. [Troubleshooting](#troubleshooting)
11. [Advanced Topics](#advanced-topics)
12. [API Reference](#api-reference)

---

## Framework Overview

### What is TFrameX?

TFrameX (Task & Flow Orchestration Framework for eXtensible LLM Systems) is a sophisticated Python framework designed for building production-ready multi-agent LLM applications. It provides a comprehensive platform for orchestrating complex AI workflows with advanced integration capabilities.

### Key Features

- **Multi-Agent Orchestration**: Sophisticated agent coordination with configurable patterns
- **MCP Integration**: Full Model Context Protocol support for external service integration
- **Flow Management**: Declarative workflow definition with nested patterns
- **Tool Integration**: Seamless function-to-tool conversion with automatic schema generation
- **Memory Management**: Pluggable conversation storage with persistence options
- **Production Ready**: Comprehensive error handling, logging, and monitoring
- **Type Safety**: Full type hints and Pydantic data validation
- **Extensible Architecture**: Plugin-based design for custom components

### Architecture Philosophy

TFrameX follows these core principles:

1. **Modularity**: Clean separation of concerns with pluggable components
2. **Extensibility**: Easy to extend with custom agents, tools, and patterns
3. **Production Focus**: Built for enterprise deployment with proper error handling
4. **Developer Experience**: Intuitive APIs with comprehensive documentation
5. **Integration First**: Designed for seamless external system integration

---

## Core Concepts

### Agents

Agents are the fundamental units of intelligence in TFrameX. They can be:

- **LLMAgent**: Uses language models for reasoning and decision-making
- **ToolAgent**: Directly executes tools without LLM reasoning
- **Custom Agents**: User-defined agents with specialized behavior

```python
@app.agent(
    name="ContentCreator",
    description="Creates high-quality content",
    tools=["research_tool", "writing_tool"],
    system_prompt="You are an expert content creator..."
)
async def content_creator():
    pass
```

### Tools

Tools are functions that agents can call to perform actions:

```python
@app.tool(description="Search the web for information")
async def web_search(query: str) -> str:
    # Implementation
    return search_results
```

### Flows

Flows define sequences of operations:

```python
flow = Flow("ContentPipeline", "Multi-stage content creation")
flow.add_step("researcher")
flow.add_step("writer")
flow.add_step("editor")
app.register_flow(flow)
```

### Patterns

Patterns define execution strategies:

- **Sequential**: One-by-one execution
- **Parallel**: Concurrent execution
- **Router**: Dynamic routing based on conditions
- **Discussion**: Multi-agent collaboration

### Memory

Memory stores conversation history:

```python
# In-memory storage
memory = InMemoryMemoryStore(max_messages=100)

# Custom storage
class DatabaseMemoryStore(BaseMemoryStore):
    # Implementation
```

---

## Quick Start Guide

### Installation

```bash
pip install tframex
```

### Basic Example

```python
from tframex import TFrameXApp
from tframex.util.llms import OpenAIChatLLM
import asyncio

# Initialize app
app = TFrameXApp(default_llm=OpenAIChatLLM())

# Define a tool
@app.tool(description="Add two numbers")
async def add(a: int, b: int) -> int:
    return a + b

# Define an agent
@app.agent(
    name="MathAgent",
    description="Performs mathematical calculations",
    tools=["add"],
    system_prompt="You are a math expert. Use tools to calculate."
)
async def math_agent():
    pass

# Use the agent
async def main():
    async with app.run_context() as rt:
        result = await rt.execute_agent(
            "MathAgent",
            "What is 5 + 3?"
        )
        print(result)

asyncio.run(main())
```

### Environment Configuration

Create a `.env` file:

```env
OPENAI_API_KEY=your_api_key_here
OPENAI_MODEL_NAME=gpt-4
OPENAI_API_BASE=https://api.openai.com/v1
```

---

## Architecture Deep Dive

### Core Architecture

```
┌─────────────────────────────────────────────────┐
│                 TFrameXApp                      │
│  ┌─────────────────────────────────────────────┐│
│  │         TFrameXRuntimeContext               ││
│  │  ┌─────────────────────────────────────────┐││
│  │  │              Engine                     │││
│  │  │  ┌─────────────────────────────────────┐│││
│  │  │  │        Agent System              │││
│  │  │  │  ┌─────────────────────────────────┐│││
│  │  │  │  │  LLMAgent  │   ToolAgent      ││││
│  │  │  │  └─────────────────────────────────┘│││
│  │  │  └─────────────────────────────────────┘│││
│  │  │  ┌─────────────────────────────────────┐│││
│  │  │  │         Tool System              │││
│  │  │  │  ┌─────────────────────────────────┐│││
│  │  │  │  │  Native │  MCP  │   Meta      ││││
│  │  │  │  └─────────────────────────────────┘│││
│  │  │  └─────────────────────────────────────┘│││
│  │  └─────────────────────────────────────────┘││
│  └─────────────────────────────────────────────┘│
└─────────────────────────────────────────────────┘
```

### Component Responsibilities

- **TFrameXApp**: Application configuration and registry
- **TFrameXRuntimeContext**: Resource management and execution context
- **Engine**: Core execution orchestrator
- **Agents**: Intelligence units with specialized capabilities
- **Tools**: Function execution with automatic schema generation
- **Memory**: Conversation persistence and retrieval
- **MCP**: External system integration

### Execution Flow

1. **Initialization**: App creates runtime context
2. **Agent Resolution**: Engine resolves agent by name
3. **Context Assembly**: Memory and tools are loaded
4. **Execution**: Agent processes input with available tools
5. **Response Processing**: Output is formatted and returned
6. **Cleanup**: Resources are properly released

---

## Development Patterns

### Agent Design Patterns

#### Single Responsibility Agents

```python
@app.agent(
    name="DataAnalyst",
    description="Analyzes data and provides insights",
    tools=["load_data", "analyze_data", "visualize_data"],
    system_prompt="You are a data analyst. Focus on data analysis tasks."
)
async def data_analyst():
    pass
```

#### Coordinator Agents

```python
@app.agent(
    name="ProjectManager",
    description="Coordinates multiple agents",
    callable_agents=["DataAnalyst", "Designer", "Developer"],
    system_prompt="You coordinate project activities across teams."
)
async def project_manager():
    pass
```

#### Specialist Agents

```python
@app.agent(
    name="SecurityExpert",
    description="Provides security analysis",
    tools=["security_scan", "vulnerability_check"],
    system_prompt="You are a cybersecurity expert. Focus on security."
)
async def security_expert():
    pass
```

### Tool Design Patterns

#### Atomic Tools

```python
@app.tool(description="Get current timestamp")
async def get_timestamp() -> str:
    return datetime.now().isoformat()
```

#### Composite Tools

```python
@app.tool(description="Comprehensive data analysis")
async def analyze_dataset(
    data_path: str,
    analysis_type: str = "descriptive"
) -> dict:
    data = load_data(data_path)
    if analysis_type == "descriptive":
        return descriptive_analysis(data)
    elif analysis_type == "predictive":
        return predictive_analysis(data)
    else:
        raise ValueError("Invalid analysis type")
```

#### Error-Handling Tools

```python
@app.tool(description="Safe file operations")
async def safe_file_read(file_path: str) -> str:
    try:
        with open(file_path, 'r') as f:
            return f.read()
    except FileNotFoundError:
        return f"Error: File {file_path} not found"
    except PermissionError:
        return f"Error: Permission denied for {file_path}"
    except Exception as e:
        return f"Error: {str(e)}"
```

### Flow Orchestration Patterns

#### Sequential Processing

```python
flow = Flow("DataPipeline", "Process data sequentially")
flow.add_step("data_collector")
flow.add_step("data_processor")
flow.add_step("data_analyzer")
flow.add_step("report_generator")
```

#### Parallel Processing

```python
analysis_flow = Flow("ParallelAnalysis", "Concurrent analysis")
analysis_flow.add_pattern_step(
    ParallelPattern("analysts", [
        "technical_analyst",
        "business_analyst",
        "risk_analyst"
    ])
)
analysis_flow.add_step("synthesis_agent")
```

#### Conditional Routing

```python
routing_flow = Flow("ConditionalFlow", "Route based on content")
routing_flow.add_step("content_classifier")
routing_flow.add_pattern_step(
    RouterPattern("content_router", {
        "technical": "technical_writer",
        "marketing": "marketing_writer",
        "creative": "creative_writer"
    })
)
```

#### Multi-Round Discussion

```python
discussion_flow = Flow("TeamDiscussion", "Collaborative decision making")
discussion_flow.add_pattern_step(
    DiscussionPattern(
        "team_discussion",
        agents=["architect", "developer", "designer"],
        num_rounds=3,
        moderator_agent="project_manager"
    )
)
```

---

## Configuration Management

### Application Configuration

```python
app = TFrameXApp(
    # Core settings
    default_llm=OpenAIChatLLM(
        model_name="gpt-4",
        api_key=os.getenv("OPENAI_API_KEY")
    ),
    default_memory_store_factory=InMemoryMemoryStore,
    
    # MCP settings
    mcp_config_file="config/servers.json",
    enable_mcp_roots=True,
    enable_mcp_sampling=True,
    mcp_roots_allowed_paths=["/safe/directory"]
)
```

### Environment-Based Configuration

```python
# config/settings.py
import os
from dataclasses import dataclass

@dataclass
class Settings:
    openai_api_key: str = os.getenv("OPENAI_API_KEY")
    openai_model: str = os.getenv("OPENAI_MODEL_NAME", "gpt-3.5-turbo")
    openai_base_url: str = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    max_memory_messages: int = int(os.getenv("MAX_MEMORY_MESSAGES", "100"))

settings = Settings()
```

### Configuration Validation

```python
from pydantic import BaseModel, validator

class AppConfig(BaseModel):
    openai_api_key: str
    openai_model: str
    max_agents: int = 10
    
    @validator('openai_api_key')
    def validate_api_key(cls, v):
        if not v or not v.startswith('sk-'):
            raise ValueError('Invalid OpenAI API key')
        return v
    
    @validator('max_agents')
    def validate_max_agents(cls, v):
        if v < 1 or v > 100:
            raise ValueError('max_agents must be between 1 and 100')
        return v
```

---

## MCP Integration

### MCP Server Configuration

```json
{
    "mcpServers": {
        "sqlite_tools": {
            "type": "stdio",
            "command": "python",
            "args": ["sqlite_mcp_server.py"],
            "env": {
                "DATABASE_PATH": "data/business.db"
            },
            "init_step_timeout": 30.0,
            "tool_call_timeout": 60.0
        },
        "web_service": {
            "type": "streamable-http",
            "url": "https://api.example.com/mcp",
            "headers": {
                "Authorization": "Bearer your_token"
            }
        }
    }
}
```

### MCP Agent Integration

```python
@app.agent(
    name="DataAnalyst",
    description="Analyzes business data",
    mcp_tools_from_servers=["sqlite_tools"],
    system_prompt="You have access to business database tools."
)
async def data_analyst():
    pass

@app.agent(
    name="UniversalAssistant",
    description="Has access to all external tools",
    mcp_tools_from_servers="ALL",
    system_prompt="You can use any available external tool."
)
async def universal_assistant():
    pass
```

### Advanced MCP Features

#### Roots Management

```python
app = TFrameXApp(
    enable_mcp_roots=True,
    mcp_roots_allowed_paths=[
        "/safe/data",
        "/approved/documents"
    ]
)
```

#### Sampling Control

```python
app = TFrameXApp(
    enable_mcp_sampling=True,
    # This enables human-in-the-loop for external LLM requests
)
```

#### Progress Tracking

```python
# MCP servers can report progress on long-running operations
# This is automatically handled by the framework
```

---

## Production Deployment

### Docker Configuration

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

ENV OPENAI_API_KEY=""
ENV LOG_LEVEL="INFO"

CMD ["python", "main.py"]
```

### Kubernetes Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: tframex-app
spec:
  replicas: 3
  selector:
    matchLabels:
      app: tframex-app
  template:
    metadata:
      labels:
        app: tframex-app
    spec:
      containers:
      - name: tframex-app
        image: tframex-app:latest
        ports:
        - containerPort: 8000
        env:
        - name: OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: api-secrets
              key: openai-api-key
        - name: LOG_LEVEL
          value: "INFO"
```

### Monitoring and Observability

```python
import logging
from tframex.util.logging import setup_logging

# Setup comprehensive logging
setup_logging(
    level=logging.INFO,
    log_format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    use_colors=False  # Disable colors in production
)

# Custom metrics
from prometheus_client import Counter, Histogram

agent_executions = Counter('tframex_agent_executions_total', 'Total agent executions')
tool_calls = Counter('tframex_tool_calls_total', 'Total tool calls')
execution_time = Histogram('tframex_execution_seconds', 'Agent execution time')
```

### Health Checks

```python
from fastapi import FastAPI
from tframex import TFrameXApp

app_fastapi = FastAPI()
tframex_app = TFrameXApp()

@app_fastapi.get("/health")
async def health_check():
    try:
        # Test basic functionality
        async with tframex_app.run_context() as rt:
            # Basic health check
            return {"status": "healthy", "timestamp": datetime.now().isoformat()}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}

@app_fastapi.get("/ready")
async def readiness_check():
    # Check if all MCP servers are ready
    if tframex_app.mcp_manager:
        server_status = await tframex_app.mcp_manager.get_server_status()
        if all(status == "ready" for status in server_status.values()):
            return {"status": "ready"}
    return {"status": "not ready"}
```

---

## Best Practices

### Code Organization

```
project/
├── app/
│   ├── __init__.py
│   ├── main.py              # Application entry point
│   ├── config/
│   │   ├── __init__.py
│   │   ├── settings.py      # Configuration management
│   │   └── servers.json     # MCP server configuration
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── specialist.py    # Specialist agents
│   │   └── coordinator.py   # Coordinator agents
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── data_tools.py    # Data processing tools
│   │   └── api_tools.py     # External API tools
│   ├── flows/
│   │   ├── __init__.py
│   │   └── business_flows.py # Business workflow definitions
│   └── utils/
│       ├── __init__.py
│       ├── logging.py       # Logging utilities
│       └── monitoring.py    # Monitoring utilities
├── tests/
├── docker/
├── k8s/
└── docs/
```

### Error Handling

```python
import logging
from typing import Union

logger = logging.getLogger(__name__)

@app.tool(description="Safe data processing")
async def process_data(data: str) -> Union[str, dict]:
    try:
        # Process data
        result = expensive_operation(data)
        logger.info(f"Data processed successfully: {len(result)} items")
        return result
    
    except ValidationError as e:
        logger.error(f"Data validation failed: {e}")
        return {"error": f"Invalid data: {str(e)}"}
    
    except TimeoutError as e:
        logger.error(f"Processing timeout: {e}")
        return {"error": "Processing timed out"}
    
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return {"error": "Internal processing error"}
```

### Performance Optimization

```python
# Use connection pooling
import httpx

class APITool:
    def __init__(self):
        self.client = httpx.AsyncClient(
            limits=httpx.Limits(max_connections=100),
            timeout=httpx.Timeout(10.0)
        )
    
    async def close(self):
        await self.client.aclose()

# Implement caching
from functools import lru_cache
import asyncio

@lru_cache(maxsize=128)
def get_tool_schema(tool_name: str):
    # Expensive schema generation
    return generate_schema(tool_name)

# Use batch operations
async def process_batch(items: list):
    tasks = [process_item(item) for item in items]
    return await asyncio.gather(*tasks)
```

### Security Considerations

```python
import os
from pathlib import Path

@app.tool(description="Safe file operations")
async def safe_file_read(file_path: str) -> str:
    # Validate file path
    safe_path = Path(file_path).resolve()
    allowed_base = Path("/safe/directory").resolve()
    
    if not str(safe_path).startswith(str(allowed_base)):
        return "Error: File access denied"
    
    # Check file size
    if safe_path.stat().st_size > 10 * 1024 * 1024:  # 10MB limit
        return "Error: File too large"
    
    try:
        with open(safe_path, 'r') as f:
            return f.read()
    except Exception as e:
        return f"Error: {str(e)}"

# Sanitize inputs
import re

def sanitize_input(user_input: str) -> str:
    # Remove potentially harmful characters
    cleaned = re.sub(r'[<>"`{}|\\]', '', user_input)
    return cleaned.strip()
```

---

## Troubleshooting

### Common Issues

#### Agent Not Found

```python
# Problem: Agent not found error
# Solution: Check agent registration

@app.agent(name="MyAgent")  # Ensure name matches
async def my_agent():
    pass

# Verify registration
print(app.get_registered_agents())
```

#### Tool Execution Failures

```python
# Problem: Tool execution fails
# Solution: Add proper error handling

@app.tool(description="Robust tool")
async def robust_tool(param: str) -> str:
    try:
        result = risky_operation(param)
        return result
    except Exception as e:
        logger.error(f"Tool error: {e}")
        return f"Error: {str(e)}"
```

#### Memory Issues

```python
# Problem: Memory grows unbounded
# Solution: Configure memory limits

app = TFrameXApp(
    default_memory_store_factory=lambda: InMemoryMemoryStore(max_messages=50)
)
```

#### MCP Connection Problems

```python
# Problem: MCP servers not connecting
# Solution: Check configuration and timeouts

# Check server configuration
{
    "mcpServers": {
        "my_server": {
            "type": "stdio",
            "command": "python",
            "args": ["server.py"],
            "init_step_timeout": 60.0,  # Increase timeout
            "tool_call_timeout": 120.0
        }
    }
}

# Debug MCP issues
logging.getLogger("tframex.mcp").setLevel(logging.DEBUG)
```

### Debugging Tools

```python
# Enable debug logging
import logging

logging.basicConfig(level=logging.DEBUG)
logging.getLogger("tframex").setLevel(logging.DEBUG)

# Use interactive debugging
async def debug_agent():
    async with app.run_context() as rt:
        # Set breakpoint
        import pdb; pdb.set_trace()
        
        result = await rt.execute_agent("MyAgent", "test input")
        print(f"Result: {result}")

# Monitor execution
@app.tool(description="Monitored tool")
async def monitored_tool(param: str) -> str:
    start_time = time.time()
    try:
        result = operation(param)
        execution_time = time.time() - start_time
        logger.info(f"Tool executed in {execution_time:.2f}s")
        return result
    except Exception as e:
        logger.error(f"Tool failed after {time.time() - start_time:.2f}s: {e}")
        raise
```

---

## Advanced Topics

### Custom Agent Classes

```python
class SpecializedAgent(BaseAgent):
    def __init__(self, *args, domain_knowledge: dict = None, **kwargs):
        super().__init__(*args, **kwargs)
        self.domain_knowledge = domain_knowledge or {}
    
    async def run(self, input_message: Union[str, Message], **kwargs) -> Message:
        # Add domain-specific processing
        enhanced_prompt = self.enhance_with_domain_knowledge(input_message)
        
        # Call parent implementation
        return await super().run(enhanced_prompt, **kwargs)
    
    def enhance_with_domain_knowledge(self, message):
        # Domain-specific logic
        return f"Domain context: {self.domain_knowledge}\n\n{message}"

# Use custom agent
@app.agent(
    name="DomainExpert",
    agent_class=SpecializedAgent,
    domain_knowledge={"field": "AI", "expertise": "deep learning"}
)
async def domain_expert():
    pass
```

### Custom Memory Stores

```python
import asyncpg
from typing import List, Optional

class PostgreSQLMemoryStore(BaseMemoryStore):
    def __init__(self, database_url: str):
        self.database_url = database_url
        self.pool = None
    
    async def initialize(self):
        self.pool = await asyncpg.create_pool(self.database_url)
    
    async def add_message(self, message: Message) -> None:
        async with self.pool.acquire() as conn:
            await conn.execute(
                "INSERT INTO messages (role, content, timestamp) VALUES ($1, $2, $3)",
                message.role, message.content, datetime.now()
            )
    
    async def get_history(
        self,
        limit: Optional[int] = None,
        offset: int = 0,
        roles: Optional[List[str]] = None
    ) -> List[Message]:
        async with self.pool.acquire() as conn:
            query = "SELECT role, content FROM messages"
            params = []
            
            if roles:
                query += " WHERE role = ANY($1)"
                params.append(roles)
            
            query += " ORDER BY timestamp DESC"
            
            if limit:
                query += f" LIMIT ${len(params) + 1}"
                params.append(limit)
            
            if offset:
                query += f" OFFSET ${len(params) + 1}"
                params.append(offset)
            
            rows = await conn.fetch(query, *params)
            return [Message(role=row['role'], content=row['content']) for row in rows]
```

### Custom LLM Providers

```python
class CustomLLMProvider(BaseLLMWrapper):
    def __init__(self, model_name: str, api_endpoint: str):
        self.model_name = model_name
        self.api_endpoint = api_endpoint
    
    async def generate_response(
        self,
        messages: List[Message],
        tools: Optional[List[Dict[str, Any]]] = None,
        **kwargs
    ) -> AsyncGenerator[Message, None]:
        # Custom LLM implementation
        response = await self.call_custom_api(messages, tools, **kwargs)
        
        # Yield response
        yield Message(role="assistant", content=response)
    
    async def call_custom_api(self, messages, tools, **kwargs):
        # Implementation specific to your LLM provider
        pass
```

### Plugin System

```python
from abc import ABC, abstractmethod

class TFrameXPlugin(ABC):
    @abstractmethod
    async def initialize(self, app: TFrameXApp):
        pass
    
    @abstractmethod
    async def cleanup(self):
        pass

class MetricsPlugin(TFrameXPlugin):
    async def initialize(self, app: TFrameXApp):
        # Setup metrics collection
        self.metrics_collector = MetricsCollector()
        app.add_middleware(self.metrics_collector)
    
    async def cleanup(self):
        await self.metrics_collector.close()

# Load plugins
app = TFrameXApp()
metrics_plugin = MetricsPlugin()
await metrics_plugin.initialize(app)
```

---

## API Reference

For detailed API documentation, see [API_REFERENCE.md](API_REFERENCE.md).

### Quick Reference

#### Core Classes

- `TFrameXApp`: Main application class
- `TFrameXRuntimeContext`: Runtime execution context
- `BaseAgent`: Base class for agents
- `LLMAgent`: LLM-powered agent
- `ToolAgent`: Direct tool execution agent
- `Flow`: Workflow definition
- `BasePattern`: Base class for execution patterns

#### Decorators

- `@app.agent()`: Register an agent
- `@app.tool()`: Register a tool

#### Patterns

- `SequentialPattern`: Sequential execution
- `ParallelPattern`: Parallel execution
- `RouterPattern`: Conditional routing
- `DiscussionPattern`: Multi-agent discussion

#### Utilities

- `OpenAIChatLLM`: OpenAI LLM wrapper
- `InMemoryMemoryStore`: In-memory storage
- `setup_logging`: Logging configuration

---

## Conclusion

TFrameX provides a comprehensive platform for building sophisticated multi-agent LLM applications. This guide covers everything from basic concepts to advanced deployment scenarios. The framework's modular design and extensive integration capabilities make it suitable for everything from simple chatbots to complex enterprise AI systems.

For additional resources:
- [Architecture Diagrams](ARCHITECTURE_DIAGRAMS.md)
- [MCP Integration Guide](MCP_INTEGRATION.md)
- [API Reference](API_REFERENCE.md)
- [Example Projects](../examples/)

The framework continues to evolve with new features and improvements. Check the GitHub repository for the latest updates and community contributions.