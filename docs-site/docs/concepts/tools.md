---
sidebar_position: 3
title: Tools
---

# Tools

Tools are the bridge between your AI agents and the real world. They enable agents to perform actions, retrieve information, and interact with external systems.

## What is a Tool?

A tool in TFrameX is:
- A Python function that agents can invoke
- Automatically described to the LLM
- Type-safe with parameter validation
- Async-first for optimal performance
- Documented for agent understanding

## Creating Tools

### Basic Tool

The simplest way to create a tool is using the `@app.tool` decorator:

```python
from tframex import TFrameXApp

app = TFrameXApp()

@app.tool(description="Calculate the sum of two numbers")
async def add(a: int, b: int) -> int:
    """Add two numbers together."""
    return a + b
```

### Tool with Complex Parameters

```python
from typing import Optional, List
from datetime import datetime

@app.tool(description="Search for products in the catalog")
async def search_products(
    query: str,
    category: Optional[str] = None,
    max_price: Optional[float] = None,
    limit: int = 10
) -> List[dict]:
    """
    Search for products matching the criteria.
    
    Args:
        query: Search term
        category: Filter by category
        max_price: Maximum price filter
        limit: Number of results to return
    
    Returns:
        List of matching products
    """
    # Implementation here
    results = await database.search(
        query=query,
        filters={
            "category": category,
            "price": {"$lte": max_price} if max_price else None
        },
        limit=limit
    )
    return results
```

### Manual Tool Creation

For more control, create tools manually:

```python
from tframex.util.tools import Tool, ToolParameters, ToolParameterProperty

def create_weather_tool():
    async def get_weather(city: str, units: str = "celsius") -> dict:
        # Implementation
        return {"city": city, "temp": 22, "units": units}
    
    return Tool(
        name="get_weather",
        func=get_weather,
        description="Get current weather for a city",
        parameters_schema=ToolParameters(
            properties={
                "city": ToolParameterProperty(
                    type="string",
                    description="The city name",
                    min_length=1
                ),
                "units": ToolParameterProperty(
                    type="string",
                    description="Temperature units",
                    enum=["celsius", "fahrenheit"],
                    default="celsius"
                )
            },
            required=["city"]
        )
    )

app.register_tool(create_weather_tool())
```

## Tool Patterns

### API Integration

```python
import aiohttp

@app.tool(description="Get stock price information")
async def get_stock_price(symbol: str) -> dict:
    """Fetch real-time stock price."""
    async with aiohttp.ClientSession() as session:
        url = f"https://api.example.com/stocks/{symbol}"
        headers = {"Authorization": f"Bearer {os.getenv('API_KEY')}"}
        
        async with session.get(url, headers=headers) as response:
            if response.status == 200:
                data = await response.json()
                return {
                    "symbol": symbol,
                    "price": data["price"],
                    "change": data["change"],
                    "timestamp": datetime.now().isoformat()
                }
            else:
                return {"error": f"Failed to fetch data: {response.status}"}
```

### Database Operations

```python
import asyncpg

# Connection pool (initialized elsewhere)
db_pool: asyncpg.Pool

@app.tool(description="Look up customer information")
async def get_customer(customer_id: str) -> dict:
    """Retrieve customer details from database."""
    async with db_pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT * FROM customers WHERE id = $1",
            customer_id
        )
        
        if row:
            return dict(row)
        else:
            return {"error": "Customer not found"}

@app.tool(description="Update customer email")
async def update_customer_email(customer_id: str, new_email: str) -> dict:
    """Update customer email address."""
    try:
        async with db_pool.acquire() as conn:
            await conn.execute(
                "UPDATE customers SET email = $1 WHERE id = $2",
                new_email, customer_id
            )
            return {"success": True, "message": "Email updated"}
    except Exception as e:
        return {"success": False, "error": str(e)}
```

### File Operations

```python
from pathlib import Path
import aiofiles

@app.tool(description="Read content from a file")
async def read_file(filename: str) -> str:
    """Read file content from the data directory."""
    # Validate path to prevent directory traversal
    safe_path = Path("data") / Path(filename).name
    
    if not safe_path.exists():
        return f"File not found: {filename}"
    
    try:
        async with aiofiles.open(safe_path, 'r') as f:
            content = await f.read()
        return content
    except Exception as e:
        return f"Error reading file: {str(e)}"

@app.tool(description="Save content to a file")
async def save_file(filename: str, content: str) -> str:
    """Save content to a file in the data directory."""
    # Ensure data directory exists
    Path("data").mkdir(exist_ok=True)
    
    # Validate filename
    safe_filename = Path(filename).name
    filepath = Path("data") / safe_filename
    
    try:
        async with aiofiles.open(filepath, 'w') as f:
            await f.write(content)
        return f"Successfully saved to {safe_filename}"
    except Exception as e:
        return f"Error saving file: {str(e)}"
```

### Computation Tools

```python
import numpy as np
from typing import List

@app.tool(description="Perform statistical analysis on numbers")
async def analyze_numbers(numbers: List[float]) -> dict:
    """Calculate statistics for a list of numbers."""
    if not numbers:
        return {"error": "No numbers provided"}
    
    arr = np.array(numbers)
    
    return {
        "count": len(numbers),
        "mean": float(np.mean(arr)),
        "median": float(np.median(arr)),
        "std_dev": float(np.std(arr)),
        "min": float(np.min(arr)),
        "max": float(np.max(arr)),
        "sum": float(np.sum(arr))
    }

@app.tool(description="Generate a random sample")
async def random_sample(
    size: int, 
    min_value: float = 0, 
    max_value: float = 1
) -> List[float]:
    """Generate random numbers within a range."""
    if size <= 0 or size > 1000:
        return []
    
    return list(np.random.uniform(min_value, max_value, size))
```

## Error Handling

Always handle errors gracefully in tools:

```python
@app.tool(description="Fetch data from external API")
async def fetch_data(endpoint: str, timeout: int = 30) -> dict:
    """Fetch data with comprehensive error handling."""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"https://api.example.com/{endpoint}",
                timeout=aiohttp.ClientTimeout(total=timeout)
            ) as response:
                if response.status == 200:
                    return await response.json()
                elif response.status == 404:
                    return {"error": "Resource not found"}
                elif response.status == 429:
                    return {"error": "Rate limit exceeded, please try again later"}
                else:
                    return {"error": f"HTTP {response.status}: {response.reason}"}
                    
    except asyncio.TimeoutError:
        return {"error": f"Request timed out after {timeout} seconds"}
    except aiohttp.ClientError as e:
        return {"error": f"Network error: {str(e)}"}
    except Exception as e:
        logger.error(f"Unexpected error in fetch_data: {e}")
        return {"error": "An unexpected error occurred"}
```

## Tool Composition

Create higher-level tools from existing ones:

```python
# Base tools
@app.tool(description="Get user by ID")
async def get_user(user_id: str) -> dict:
    # Implementation
    pass

@app.tool(description="Get user orders")
async def get_orders(user_id: str) -> List[dict]:
    # Implementation
    pass

@app.tool(description="Calculate order statistics")
async def calculate_stats(orders: List[dict]) -> dict:
    # Implementation
    pass

# Composite tool
@app.tool(description="Get complete user profile with order history")
async def get_user_profile(user_id: str) -> dict:
    """Fetch user data and order statistics."""
    # Use other tools
    user = await get_user(user_id)
    if "error" in user:
        return user
    
    orders = await get_orders(user_id)
    stats = await calculate_stats(orders)
    
    return {
        "user": user,
        "orders": orders,
        "statistics": stats
    }
```

## Tool Validation

Implement input validation for robustness:

```python
from pydantic import BaseModel, validator
import re

class EmailUpdateRequest(BaseModel):
    email: str
    
    @validator('email')
    def validate_email(cls, v):
        pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
        if not re.match(pattern, v):
            raise ValueError('Invalid email format')
        return v

@app.tool(description="Update user email with validation")
async def update_email(user_id: str, email: str) -> dict:
    """Update email with validation."""
    try:
        # Validate using Pydantic
        request = EmailUpdateRequest(email=email)
        
        # Proceed with update
        # ... implementation ...
        
        return {"success": True, "email": request.email}
    
    except ValueError as e:
        return {"success": False, "error": str(e)}
```

## Performance Optimization

### Caching

```python
from functools import lru_cache
import hashlib

# In-memory cache for expensive operations
cache = {}

@app.tool(description="Get data with caching")
async def get_cached_data(key: str, ttl: int = 300) -> dict:
    """Fetch data with time-based caching."""
    cache_key = hashlib.md5(key.encode()).hexdigest()
    
    # Check cache
    if cache_key in cache:
        cached_data, timestamp = cache[cache_key]
        if time.time() - timestamp < ttl:
            return {"data": cached_data, "cached": True}
    
    # Fetch fresh data
    data = await expensive_operation(key)
    
    # Update cache
    cache[cache_key] = (data, time.time())
    
    return {"data": data, "cached": False}
```

### Batch Operations

```python
@app.tool(description="Process multiple items efficiently")
async def batch_process(items: List[str]) -> List[dict]:
    """Process items in parallel batches."""
    batch_size = 10
    results = []
    
    for i in range(0, len(items), batch_size):
        batch = items[i:i + batch_size]
        
        # Process batch in parallel
        tasks = [process_item(item) for item in batch]
        batch_results = await asyncio.gather(*tasks)
        
        results.extend(batch_results)
    
    return results
```

## Testing Tools

Create comprehensive tests for your tools:

```python
import pytest
from unittest.mock import patch, AsyncMock

@pytest.mark.asyncio
async def test_add_tool():
    result = await add(5, 3)
    assert result == 8

@pytest.mark.asyncio
async def test_weather_tool():
    result = await get_weather("London", "celsius")
    assert "city" in result
    assert result["city"] == "London"

@pytest.mark.asyncio
async def test_api_tool_error_handling():
    with patch('aiohttp.ClientSession.get') as mock_get:
        # Simulate network error
        mock_get.side_effect = aiohttp.ClientError()
        
        result = await fetch_data("test")
        assert "error" in result
        assert "Network error" in result["error"]
```

## Best Practices

### 1. Clear Descriptions
```python
# Good
@app.tool(description="Calculate compound interest for an investment")

# Avoid
@app.tool(description="Do math stuff")
```

### 2. Type Hints
Always use type hints for clarity:
```python
async def process_data(
    data: List[dict],
    filters: Optional[dict] = None
) -> dict[str, Any]:
    """Process with clear types."""
    pass
```

### 3. Idempotency
Make tools idempotent when possible:
```python
@app.tool(description="Ensure user exists")
async def ensure_user(user_id: str, name: str) -> dict:
    """Create user if not exists, otherwise return existing."""
    existing = await get_user(user_id)
    if existing:
        return {"created": False, "user": existing}
    
    new_user = await create_user(user_id, name)
    return {"created": True, "user": new_user}
```

### 4. Meaningful Return Values
Return structured data that agents can understand:
```python
# Good
return {
    "success": True,
    "data": processed_data,
    "count": len(processed_data),
    "timestamp": datetime.now().isoformat()
}

# Avoid
return "OK"
```

## Tool Documentation

Document tools thoroughly for agent understanding:

```python
@app.tool(description="Search knowledge base articles")
async def search_kb(
    query: str,
    category: Optional[str] = None,
    limit: int = 10
) -> List[dict]:
    """
    Search the knowledge base for relevant articles.
    
    This tool searches through technical documentation, FAQs,
    and help articles to find information matching the query.
    
    Args:
        query: Search terms (supports boolean operators)
        category: Filter by category (e.g., 'billing', 'technical')
        limit: Maximum results to return (1-100)
    
    Returns:
        List of articles with title, snippet, url, and relevance score
        
    Example:
        query="password reset", category="account"
        Returns articles about resetting passwords
    """
    # Implementation
    pass
```

## Next Steps

Now that you understand tools:

1. Learn about [Flows](flows) to orchestrate tool usage
2. Explore [Patterns](patterns) for tool coordination
3. Study [MCP Integration](mcp-integration) for external tools
4. Check [API Reference](../api/tools) for detailed documentation

## Examples

For practical tool implementations, see:
- [Basic Tools](../examples/basic-examples#tool-integration)
- [API Integrations](../examples/integration-examples)
- [Advanced Tools](../examples/advanced-examples#complex-tools)