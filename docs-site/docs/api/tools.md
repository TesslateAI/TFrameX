---
sidebar_position: 4
title: Tools
---

# Tools API Reference

Tools extend agent capabilities by providing access to external functions, APIs, and services. This reference covers the tool system, creation methods, and best practices.

## Tool Class

The core `Tool` class represents a callable function with metadata:

```python
from tframex.util.tools import Tool, ToolParameters

class Tool:
    def __init__(
        self,
        name: str,
        func: Callable,
        description: str,
        parameters_schema: Optional[ToolParameters] = None,
        return_type: Optional[type] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Create a tool.
        
        Args:
            name: Unique tool identifier
            func: The function to execute
            description: Human-readable description
            parameters_schema: Parameter validation schema
            return_type: Expected return type
            metadata: Additional metadata
        """
```

## Creating Tools

### Decorator Method (Recommended)

```python
from tframex import TFrameXApp

app = TFrameXApp()

@app.tool(description="Get current weather for a city")
async def get_weather(city: str, units: str = "celsius") -> dict:
    """
    Get weather information.
    
    Args:
        city: City name
        units: Temperature units (celsius/fahrenheit)
    
    Returns:
        Weather data dictionary
    """
    # Implementation
    return {
        "city": city,
        "temperature": 22,
        "units": units,
        "conditions": "Sunny"
    }
```

### Direct Registration

```python
from tframex.util.tools import Tool

# Define function
async def calculate_stats(numbers: List[float]) -> dict:
    return {
        "mean": sum(numbers) / len(numbers),
        "min": min(numbers),
        "max": max(numbers)
    }

# Create tool
stats_tool = Tool(
    name="calculate_stats",
    func=calculate_stats,
    description="Calculate statistics for a list of numbers"
)

# Register
app.register_tool(stats_tool)
```

### Tool with Schema Validation

```python
from pydantic import BaseModel, Field
from typing import List, Optional

# Define parameter schema
class SearchParams(BaseModel):
    query: str = Field(..., description="Search query")
    max_results: int = Field(10, ge=1, le=100, description="Maximum results")
    filters: Optional[Dict[str, str]] = Field(None, description="Search filters")

@app.tool(description="Advanced search with validation")
async def advanced_search(params: SearchParams) -> List[dict]:
    """
    Perform advanced search with validated parameters.
    """
    # Params are automatically validated
    results = await search_engine.search(
        params.query,
        limit=params.max_results,
        filters=params.filters
    )
    return results
```

## Tool Parameters

### Automatic Schema Generation

TFrameX automatically generates parameter schemas from function signatures:

```python
@app.tool()
async def send_email(
    to: str,
    subject: str,
    body: str,
    cc: Optional[List[str]] = None,
    priority: str = "normal"
) -> bool:
    """Send an email."""
    # Parameter schema is auto-generated from type hints
    pass
```

### Manual Schema Definition

```python
from tframex.util.tools import ToolParameters

schema = ToolParameters(
    properties={
        "query": {
            "type": "string",
            "description": "Search query",
            "minLength": 1
        },
        "limit": {
            "type": "integer",
            "description": "Result limit",
            "minimum": 1,
            "maximum": 100,
            "default": 10
        }
    },
    required=["query"]
)

tool = Tool(
    name="search",
    func=search_function,
    description="Search tool",
    parameters_schema=schema
)
```

## Tool Types

### Synchronous Tools

```python
@app.tool(description="Synchronous calculation")
def calculate_fibonacci(n: int) -> int:
    """Calculate nth Fibonacci number."""
    if n <= 1:
        return n
    return calculate_fibonacci(n-1) + calculate_fibonacci(n-2)
```

### Asynchronous Tools

```python
@app.tool(description="Async API call")
async def fetch_data(endpoint: str) -> dict:
    """Fetch data from API."""
    async with aiohttp.ClientSession() as session:
        async with session.get(f"https://api.example.com/{endpoint}") as resp:
            return await resp.json()
```

### Streaming Tools

```python
@app.tool(description="Stream large dataset")
async def stream_data(query: str) -> AsyncGenerator[dict, None]:
    """Stream data matching query."""
    async with database.stream_query(query) as cursor:
        async for row in cursor:
            yield {"data": row, "timestamp": datetime.now()}
```

### Stateful Tools

```python
class DatabaseTool:
    def __init__(self, connection_string: str):
        self.conn_string = connection_string
        self._connection = None
    
    async def connect(self):
        self._connection = await asyncpg.connect(self.conn_string)
    
    async def query(self, sql: str) -> List[dict]:
        """Execute SQL query."""
        if not self._connection:
            await self.connect()
        
        rows = await self._connection.fetch(sql)
        return [dict(row) for row in rows]

# Create stateful tool instance
db_tool = DatabaseTool("postgresql://localhost/mydb")

# Register the method as a tool
app.register_tool(Tool(
    name="database_query",
    func=db_tool.query,
    description="Execute SQL queries"
))
```

## Advanced Tool Features

### Tool with File Upload

```python
@app.tool(description="Process uploaded file")
async def process_file(
    file_path: str,
    operation: str = "analyze"
) -> dict:
    """
    Process a file with specified operation.
    
    Args:
        file_path: Path to uploaded file
        operation: Operation to perform
    """
    if operation == "analyze":
        with open(file_path, 'r') as f:
            content = f.read()
            return {
                "size": len(content),
                "lines": content.count('\n'),
                "words": len(content.split())
            }
    elif operation == "convert":
        # Conversion logic
        pass
```

### Tool with Progress Reporting

```python
@app.tool(description="Long-running task with progress")
async def process_batch(
    items: List[str],
    callback: Optional[Callable] = None
) -> dict:
    """Process items with progress updates."""
    results = []
    total = len(items)
    
    for i, item in enumerate(items):
        # Process item
        result = await process_single(item)
        results.append(result)
        
        # Report progress
        if callback:
            await callback({
                "current": i + 1,
                "total": total,
                "percentage": (i + 1) / total * 100
            })
    
    return {"processed": total, "results": results}
```

### Tool with Caching

```python
from functools import lru_cache
import hashlib

@app.tool(description="Cached expensive computation")
@lru_cache(maxsize=128)
async def expensive_calculation(input_data: str) -> dict:
    """
    Perform expensive calculation with caching.
    Results are cached based on input.
    """
    # Expensive computation
    result = await complex_algorithm(input_data)
    return result

# Redis-based caching
import aioredis

class CachedTool:
    def __init__(self):
        self.redis = None
    
    async def connect(self):
        self.redis = await aioredis.create_redis_pool('redis://localhost')
    
    async def cached_search(self, query: str) -> dict:
        # Check cache
        cache_key = f"search:{hashlib.md5(query.encode()).hexdigest()}"
        cached = await self.redis.get(cache_key)
        
        if cached:
            return json.loads(cached)
        
        # Perform search
        result = await perform_search(query)
        
        # Cache result
        await self.redis.setex(
            cache_key,
            3600,  # 1 hour TTL
            json.dumps(result)
        )
        
        return result
```

### Tool with Rate Limiting

```python
from aiohttp import ClientSession
from asyncio import Semaphore
import time

class RateLimitedTool:
    def __init__(self, requests_per_minute: int = 60):
        self.semaphore = Semaphore(requests_per_minute)
        self.request_times = []
        self.rpm = requests_per_minute
    
    async def api_call(self, endpoint: str) -> dict:
        """Make rate-limited API call."""
        async with self.semaphore:
            # Ensure rate limit
            now = time.time()
            self.request_times = [t for t in self.request_times if now - t < 60]
            
            if len(self.request_times) >= self.rpm:
                sleep_time = 60 - (now - self.request_times[0])
                await asyncio.sleep(sleep_time)
            
            # Make request
            async with ClientSession() as session:
                async with session.get(endpoint) as response:
                    self.request_times.append(time.time())
                    return await response.json()

# Register rate-limited tool
rate_limited = RateLimitedTool(requests_per_minute=30)
app.register_tool(Tool(
    name="rate_limited_api",
    func=rate_limited.api_call,
    description="Rate-limited API calls"
))
```

## Tool Composition

### Combining Multiple Tools

```python
@app.tool(description="Composite research tool")
async def research_topic(topic: str) -> dict:
    """
    Research a topic using multiple sources.
    Combines web search, Wikipedia, and news APIs.
    """
    # Use other tools
    web_results = await web_search(topic)
    wiki_summary = await wikipedia_search(topic)
    news_articles = await news_search(topic)
    
    # Combine results
    return {
        "topic": topic,
        "web_results": web_results[:5],
        "wikipedia": wiki_summary,
        "recent_news": news_articles[:3],
        "summary": await summarize_findings(web_results, wiki_summary, news_articles)
    }
```

### Tool Pipelines

```python
class ToolPipeline:
    def __init__(self, tools: List[Tool]):
        self.tools = tools
    
    async def execute(self, initial_input: Any) -> Any:
        """Execute tools in sequence."""
        result = initial_input
        
        for tool in self.tools:
            result = await tool.func(result)
        
        return result

# Create pipeline
pipeline = ToolPipeline([
    data_extraction_tool,
    data_cleaning_tool,
    data_analysis_tool,
    report_generation_tool
])

@app.tool(description="Data processing pipeline")
async def process_data_pipeline(raw_data: str) -> dict:
    return await pipeline.execute(raw_data)
```

## Error Handling

### Graceful Degradation

```python
@app.tool(description="Fault-tolerant web search")
async def resilient_search(query: str) -> dict:
    """
    Search with fallback providers.
    """
    providers = [
        ("primary_search", primary_api),
        ("backup_search", backup_api),
        ("emergency_search", emergency_api)
    ]
    
    for name, search_func in providers:
        try:
            results = await search_func(query)
            return {
                "provider": name,
                "results": results,
                "status": "success"
            }
        except Exception as e:
            logger.warning(f"{name} failed: {e}")
            continue
    
    # All providers failed
    return {
        "provider": "none",
        "results": [],
        "status": "all_providers_failed",
        "error": "Unable to perform search"
    }
```

### Input Validation

```python
@app.tool(description="Tool with comprehensive validation")
async def validated_tool(
    email: str,
    age: int,
    preferences: List[str]
) -> dict:
    """
    Tool with input validation.
    """
    # Email validation
    if not re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', email):
        raise ValueError("Invalid email format")
    
    # Age validation
    if not 0 < age < 150:
        raise ValueError("Age must be between 1 and 149")
    
    # Preferences validation
    valid_preferences = ["sports", "music", "reading", "travel"]
    invalid = set(preferences) - set(valid_preferences)
    if invalid:
        raise ValueError(f"Invalid preferences: {invalid}")
    
    # Process valid input
    return {
        "email": email,
        "age": age,
        "preferences": preferences,
        "profile_created": True
    }
```

## Testing Tools

```python
import pytest
from tframex.testing import ToolTestHarness

@pytest.fixture
def test_app():
    app = TFrameXApp()
    
    @app.tool()
    async def test_tool(value: int) -> int:
        return value * 2
    
    return app

async def test_tool_execution(test_app):
    harness = ToolTestHarness(test_app)
    
    # Test tool execution
    result = await harness.execute_tool("test_tool", value=5)
    assert result == 10
    
    # Test with invalid input
    with pytest.raises(TypeError):
        await harness.execute_tool("test_tool", value="not a number")

async def test_tool_schema():
    tool = test_app.get_tool("test_tool")
    schema = tool.parameters_schema
    
    # Verify schema
    assert "value" in schema.properties
    assert schema.properties["value"]["type"] == "integer"
```

## Performance Optimization

### Batch Processing

```python
@app.tool(description="Batch processing tool")
async def batch_process(items: List[dict], batch_size: int = 10) -> List[dict]:
    """
    Process items in batches for efficiency.
    """
    results = []
    
    for i in range(0, len(items), batch_size):
        batch = items[i:i + batch_size]
        
        # Process batch in parallel
        batch_tasks = [process_item(item) for item in batch]
        batch_results = await asyncio.gather(*batch_tasks)
        
        results.extend(batch_results)
    
    return results
```

### Connection Pooling

```python
class PooledDatabaseTool:
    def __init__(self, pool_size: int = 10):
        self.pool = None
        self.pool_size = pool_size
    
    async def initialize(self):
        self.pool = await asyncpg.create_pool(
            'postgresql://localhost/db',
            min_size=2,
            max_size=self.pool_size
        )
    
    async def query(self, sql: str) -> List[dict]:
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(sql)
            return [dict(row) for row in rows]
```

## Best Practices

1. **Clear Descriptions** - Write descriptive tool documentation
2. **Type Hints** - Always use type hints for parameters
3. **Error Messages** - Provide helpful error messages
4. **Validation** - Validate inputs early and clearly
5. **Async When Needed** - Use async for I/O operations
6. **Resource Management** - Clean up resources properly
7. **Testing** - Test tools independently
8. **Documentation** - Document expected inputs/outputs
9. **Monitoring** - Log tool usage and errors
10. **Security** - Validate and sanitize all inputs

## Tool Catalog

Common tool patterns and implementations:

### Web Tools
- Web search
- URL fetching
- API integration
- Web scraping

### Data Tools
- CSV/JSON processing
- Database queries
- Data transformation
- Statistical analysis

### File Tools
- File reading/writing
- Directory operations
- File format conversion
- Archive handling

### Communication Tools
- Email sending
- Slack integration
- SMS messaging
- Webhook calls

### AI/ML Tools
- Image generation
- Text analysis
- Translation
- Sentiment analysis

## See Also

- [TFrameXApp](tframexapp) - Application setup
- [Agents](agents) - Agents that use tools
- [Examples](../examples/tool-examples) - Tool implementation examples
- [Best Practices](../guides/best-practices) - Development guidelines