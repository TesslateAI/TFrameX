# TFrameX Extension Guide

## Table of Contents
1. [Introduction](#introduction)
2. [Custom Agents](#custom-agents)
3. [Custom Patterns](#custom-patterns)
4. [Custom LLM Wrappers](#custom-llm-wrappers)
5. [Custom Memory Stores](#custom-memory-stores)
6. [Custom Tools](#custom-tools)
7. [Best Practices](#best-practices)

## Introduction

TFrameX is designed to be highly extensible, allowing developers to customize and expand its capabilities. This guide covers the key extension points and best practices for extending TFrameX to meet your specific requirements.

## Custom Agents

Agents are the building blocks of TFrameX applications. You can extend the base agent functionality in several ways:

### 1. Creating a Custom Agent Class

To create a custom agent type with specialized behavior, extend the `BaseAgent` class:

```python
from tframex.agents.base import BaseAgent
from tframex.models.primitives import Message

class MyCustomAgent(BaseAgent):
    def __init__(
        self, 
        name: str, 
        description: str = None, 
        system_prompt_template: str = None,
        custom_param: Any = None
    ):
        super().__init__(name, description, system_prompt_template)
        self.custom_param = custom_param

    async def process(self, input_message: Message, engine_ref=None, **kwargs) -> Message:
        # Custom logic here
        processed_content = f"Custom processing: {input_message.content}"
        
        return Message(
            role="assistant",
            content=processed_content
        )

# Register the agent with the application
@app.agent(
    name="CustomAgentInstance",
    description="My specialized agent",
    agent_class=MyCustomAgent,
    custom_param="extra_config"  # Additional params passed to constructor
)
async def custom_agent_placeholder():
    pass
```

### 2. Adding Agent Capabilities

You can also extend existing agent classes like `LLMAgent` to add new capabilities:

```python
from tframex.agents.llm_agent import LLMAgent
from tframex.models.primitives import Message

class EnhancedLLMAgent(LLMAgent):
    async def process(self, input_message: Message, engine_ref=None, **kwargs) -> Message:
        # Pre-processing
        enhanced_input = self._preprocess_input(input_message)
        
        # Use parent's processing
        result = await super().process(enhanced_input, engine_ref, **kwargs)
        
        # Post-processing
        enhanced_result = self._postprocess_output(result)
        
        return enhanced_result
    
    def _preprocess_input(self, message: Message) -> Message:
        # Add preprocessing logic here
        return message
    
    def _postprocess_output(self, message: Message) -> Message:
        # Add postprocessing logic here
        return message
```

### 3. Agent State Management

For agents that need to maintain state across invocations:

```python
class StatefulAgent(BaseAgent):
    def __init__(self, name, description=None, system_prompt_template=None):
        super().__init__(name, description, system_prompt_template)
        self.state = {}
    
    async def process(self, input_message: Message, engine_ref=None, **kwargs) -> Message:
        # Access and update state
        if 'counter' not in self.state:
            self.state['counter'] = 0
        self.state['counter'] += 1
        
        return Message(
            role="assistant",
            content=f"Processed message. I've been called {self.state['counter']} times."
        )
```

## Custom Patterns

Patterns define how agents interact with each other. You can create custom patterns to implement specialized agent interaction flows:

### 1. Creating a Custom Pattern

Extend `BasePattern` to create a custom interaction pattern:

```python
from tframex.patterns.base_pattern import BasePattern
from tframex.flows.flow_context import FlowContext
from tframex.util.engine import Engine
import logging

logger = logging.getLogger(__name__)

class IterativeRefinementPattern(BasePattern):
    def __init__(
        self, 
        pattern_name: str, 
        creator_agent: str, 
        refiner_agent: str, 
        iterations: int = 3
    ):
        super().__init__(pattern_name)
        self.creator_agent = creator_agent
        self.refiner_agent = refiner_agent
        self.iterations = iterations
    
    async def execute(
        self, 
        flow_ctx: FlowContext, 
        engine: Engine, 
        agent_call_kwargs=None
    ) -> FlowContext:
        logger.info(f"Starting IterativeRefinementPattern '{self.pattern_name}' with {self.iterations} iterations")
        
        # Initial creation
        try:
            creator_result = await engine.call_agent(
                self.creator_agent, 
                flow_ctx.current_message,
                **(agent_call_kwargs or {})
            )
            flow_ctx.update_current_message(creator_result)
            
            # Iterative refinement
            for i in range(self.iterations):
                logger.info(f"IterativeRefinementPattern '{self.pattern_name}' - Iteration {i+1}/{self.iterations}")
                refiner_result = await engine.call_agent(
                    self.refiner_agent,
                    flow_ctx.current_message,
                    **(agent_call_kwargs or {})
                )
                flow_ctx.update_current_message(refiner_result)
                
                # Optional: Store intermediate results in shared data
                flow_ctx.update_shared_data({
                    f"iteration_{i+1}_result": refiner_result.content
                })
                
        except Exception as e:
            logger.error(f"Error in IterativeRefinementPattern '{self.pattern_name}': {e}", exc_info=True)
            # Handle error case
            
        return flow_ctx
```

### 2. Using the Custom Pattern

```python
from tframex import Flow, TFrameXApp

app = TFrameXApp(...)

# Define agents
@app.agent(name="ContentCreator", system_prompt="Create initial content based on the request.")
async def creator_placeholder():
    pass

@app.agent(name="ContentRefiner", system_prompt="Refine and improve the content.")
async def refiner_placeholder():
    pass

# Create a flow with the custom pattern
refinement_pattern = IterativeRefinementPattern(
    "ContentRefinement",
    creator_agent="ContentCreator",
    refiner_agent="ContentRefiner",
    iterations=3
)

refinement_flow = Flow("RefinementFlow", refinement_pattern)
app.register_flow(refinement_flow)
```

### 3. Combining Multiple Patterns

You can create complex flows by nesting patterns within each other:

```python
from tframex import Flow, SequentialPattern, ParallelPattern, RouterPattern

# Create component patterns
initial_analysis = ParallelPattern(
    "InitialAnalysis",
    agents=["DataAnalyst", "InsightGenerator"],
    aggregator_agent="AnalysisAggregator"
)

content_generation = SequentialPattern(
    "ContentGeneration",
    steps=["Outliner", "ContentWriter", "Editor"]
)

feedback_collection = DiscussionPattern(
    "FeedbackCollection",
    participants=["CriticA", "CriticB", "CriticC"],
    moderator="FeedbackModerator",
    rounds=1
)

# Combine patterns into a main flow
main_workflow = Flow(
    "CompleteWorkflow",
    SequentialPattern(
        "MainSequence",
        steps=[initial_analysis, content_generation, feedback_collection]
    )
)

app.register_flow(main_workflow)
```

## Custom LLM Wrappers

TFrameX allows you to integrate with different LLM providers by creating custom LLM wrappers:

### 1. Creating a Custom LLM Wrapper

Extend `BaseLLMWrapper` to support a new LLM provider:

```python
from tframex.util.llms import BaseLLMWrapper
from tframex.models.primitives import ToolCall, ToolDefinition
from typing import List, Dict, Any, Tuple, Optional, Union, AsyncIterator
import aiohttp
import json
import logging

logger = logging.getLogger(__name__)

class CustomLLMWrapper(BaseLLMWrapper):
    def __init__(
        self,
        api_url: str,
        api_key: str,
        model_name: str = "default-model"
    ):
        super().__init__()
        self.api_url = api_url
        self.api_key = api_key
        self.model_name = model_name
        self.model_id = f"custom-{model_name}"  # For logging/identification
    
    async def generate_response(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        tools: Optional[List[ToolDefinition]] = None,
        **kwargs
    ) -> Tuple[str, Optional[List[ToolCall]]]:
        """Generate a response from the custom LLM service."""
        try:
            # Prepare request payload for your API
            payload = {
                "messages": messages,
                "temperature": temperature,
                "model": self.model_name
            }
            
            if max_tokens:
                payload["max_tokens"] = max_tokens
                
            if tools:
                # Convert tools to the format expected by your API
                payload["tools"] = [self._convert_tool_def(tool) for tool in tools]
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.api_url,
                    headers=headers,
                    json=payload
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"LLM API error: {response.status} - {error_text}")
                        return f"Error: Failed to generate response ({response.status})", None
                    
                    result = await response.json()
                    
                    # Extract content and tool calls based on your API's response format
                    content = result.get("content", "")
                    
                    # Parse tool calls if present
                    tool_calls = []
                    if "tool_calls" in result:
                        for tc in result["tool_calls"]:
                            tool_calls.append(
                                ToolCall(
                                    id=tc.get("id", "unknown"),
                                    name=tc.get("name", ""),
                                    arguments=tc.get("arguments", {})
                                )
                            )
                    
                    return content, tool_calls if tool_calls else None
                    
        except Exception as e:
            logger.error(f"Error generating response: {str(e)}", exc_info=True)
            return f"Error: {str(e)}", None
    
    async def generate_response_stream(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        tools: Optional[List[ToolDefinition]] = None,
        **kwargs
    ) -> AsyncIterator[Union[str, ToolCall]]:
        """Generate a streaming response from the custom LLM service."""
        # Implement streaming logic for your API
        # This will depend on how your API handles streaming
        # Yield string content chunks or ToolCall objects
        pass
    
    def _convert_tool_def(self, tool_def: ToolDefinition) -> Dict[str, Any]:
        """Convert TFrameX tool definition to API-specific format."""
        # Implement conversion logic specific to your API
        return {
            "name": tool_def.name,
            "description": tool_def.description,
            "parameters": {
                # Convert parameters based on your API's expected format
            }
        }
```

### 2. Using the Custom LLM Wrapper

```python
from tframex import TFrameXApp

# Initialize with custom LLM
custom_llm = CustomLLMWrapper(
    api_url="https://api.customllmprovider.com/generate",
    api_key="your-api-key",
    model_name="large-language-model"
)

app = TFrameXApp(default_llm=custom_llm)

# Or use it for specific agents
@app.agent(
    name="SpecializedAgent",
    description="Uses the custom LLM provider",
    llm=custom_llm
)
async def specialized_agent_placeholder():
    pass
```

## Custom Memory Stores

Memory stores in TFrameX manage conversation history. You can create custom memory stores to integrate with different storage backends:

### 1. Creating a Custom Memory Store

Extend `BaseMemoryStore` to implement custom memory storage:

```python
from tframex.util.memory import BaseMemoryStore
from tframex.models.primitives import Message
from typing import Dict, List, Optional, Union
import aioredis
import json
import uuid

class RedisMemoryStore(BaseMemoryStore):
    def __init__(self, redis_url: str, ttl_seconds: int = 3600):
        self.redis_url = redis_url
        self.ttl_seconds = ttl_seconds
        self.redis = None
    
    async def initialize(self):
        """Initialize Redis connection."""
        self.redis = await aioredis.from_url(self.redis_url)
    
    async def add_message(
        self, 
        message: Union[Dict, Message], 
        conversation_id: Optional[str] = None
    ) -> None:
        """Add a message to the Redis store."""
        if self.redis is None:
            await self.initialize()
        
        # Generate conversation ID if not provided
        if not conversation_id:
            conversation_id = str(uuid.uuid4())
        
        # Convert Message object to dict if needed
        if isinstance(message, Message):
            message_dict = {
                "role": message.role,
                "content": message.content,
                "message_type": message.message_type,
                "metadata": message.metadata
            }
        else:
            message_dict = message
        
        # Add timestamp if not present
        if "timestamp" not in message_dict:
            message_dict["timestamp"] = time.time()
        
        # Store message in Redis
        message_key = f"conversation:{conversation_id}:messages"
        await self.redis.rpush(message_key, json.dumps(message_dict))
        
        # Set expiration if not already set
        await self.redis.expire(message_key, self.ttl_seconds)
    
    async def get_messages(
        self, 
        conversation_id: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[Dict]:
        """Retrieve messages from Redis store."""
        if self.redis is None:
            await self.initialize()
        
        if not conversation_id:
            return []
        
        message_key = f"conversation:{conversation_id}:messages"
        
        # Get all messages
        message_count = await self.redis.llen(message_key)
        if message_count == 0:
            return []
        
        # Apply limit if specified
        start_idx = 0
        end_idx = -1
        if limit and limit > 0:
            start_idx = max(0, message_count - limit)
        
        # Retrieve messages
        message_jsons = await self.redis.lrange(message_key, start_idx, end_idx)
        
        # Parse and return
        return [json.loads(msg) for msg in message_jsons]
    
    async def clear_conversation(self, conversation_id: str) -> None:
        """Clear a conversation's messages."""
        if self.redis is None:
            await self.initialize()
        
        message_key = f"conversation:{conversation_id}:messages"
        await self.redis.delete(message_key)
    
    async def close(self):
        """Close Redis connection."""
        if self.redis:
            await self.redis.close()
```

### 2. Using the Custom Memory Store

```python
from tframex import TFrameXApp

# Create memory store factory function
def redis_memory_store_factory():
    return RedisMemoryStore(redis_url="redis://localhost:6379")

# Use as default memory store
app = TFrameXApp(
    default_llm=your_llm,
    default_memory_store_factory=redis_memory_store_factory
)

# Or use for a specific agent
redis_store = RedisMemoryStore(redis_url="redis://localhost:6379")

@app.agent(
    name="PersistentAgent",
    memory_store=redis_store
)
async def persistent_agent_placeholder():
    pass
```

## Custom Tools

Tools allow agents to interact with external systems. You can create custom tools to extend the capabilities of your agents:

### 1. Creating Basic Tools

The simplest way to create tools is using the `@app.tool` decorator:

```python
from tframex import TFrameXApp
import requests

app = TFrameXApp(...)

@app.tool(
    name="fetch_stock_price",
    description="Fetches current stock price for a given ticker symbol",
    parameters_schema={
        "properties": {
            "ticker": {
                "type": "string",
                "description": "Stock ticker symbol (e.g., AAPL, MSFT)"
            },
            "exchange": {
                "type": "string",
                "description": "Stock exchange (default: NASDAQ)"
            }
        },
        "required": ["ticker"]
    }
)
async def fetch_stock_price(ticker: str, exchange: str = "NASDAQ") -> str:
    """Fetch stock price from an API."""
    try:
        # In a real implementation, use a proper financial API
        response = requests.get(
            f"https://api.example.com/stocks/{exchange}/{ticker}"
        )
        data = response.json()
        return f"Current price of {ticker} on {exchange}: ${data['price']:.2f}"
    except Exception as e:
        return f"Error fetching stock price: {str(e)}"
```

### 2. Creating Tool Classes

For more complex tools, you can create dedicated tool classes:

```python
from tframex.util.tools import Tool, ToolParameters, ToolParameterProperty
from typing import Dict, Any, Optional, Callable
import logging

logger = logging.getLogger(__name__)

class DatabaseQueryTool(Tool):
    def __init__(
        self,
        name: str,
        db_connection,
        description: Optional[str] = None,
    ):
        # Define parameters schema
        parameters = ToolParameters(
            properties={
                "query": ToolParameterProperty(
                    type="string",
                    description="SQL query to execute (SELECT only)"
                ),
                "limit": ToolParameterProperty(
                    type="integer",
                    description="Maximum number of rows to return"
                )
            },
            required=["query"]
        )
        
        # Create executor function
        async def execute_query(query: str, limit: int = 100) -> str:
            try:
                # Safety check (basic - would need more robust validation)
                if not query.lower().strip().startswith("select"):
                    return "Error: Only SELECT queries are allowed"
                
                # Add limit if not already in query
                if "limit" not in query.lower():
                    query = f"{query} LIMIT {limit}"
                
                # Execute query
                cursor = db_connection.cursor()
                cursor.execute(query)
                results = cursor.fetchall()
                
                # Format results
                if not results:
                    return "Query returned no results"
                
                columns = [desc[0] for desc in cursor.description]
                result_str = "Results:\n"
                result_str += " | ".join(columns) + "\n"
                result_str += "-" * len(result_str) + "\n"
                
                for row in results:
                    result_str += " | ".join(str(cell) for cell in row) + "\n"
                
                return result_str
                
            except Exception as e:
                logger.error(f"Database query error: {str(e)}", exc_info=True)
                return f"Error executing query: {str(e)}"
        
        # Initialize the tool with the function and parameters
        super().__init__(
            name=name,
            func=execute_query,
            description=description or "Execute a database query",
            parameters_schema=parameters
        )

# Register with the app
db_connection = get_database_connection()  # Your database connection logic
db_tool = DatabaseQueryTool(
    name="query_database",
    db_connection=db_connection,
    description="Query the application database (read-only)"
)

# Register manually instead of using decorator
app._tools["query_database"] = db_tool

# Then use in an agent
@app.agent(
    name="DatabaseAnalyst",
    description="Analyzes data from the database",
    tools=["query_database"],
    system_prompt="You are a database analyst. Use the query_database tool to retrieve and analyze data."
)
async def db_analyst_placeholder():
    pass
```

## Best Practices

### Modular Design

- **Separation of Concerns**: Keep agent definitions, tool implementations, and pattern logic separate.
- **Reusable Components**: Design patterns and agents to be reusable across different flows.
- **Configuration Over Code**: Use template variables and shared data to configure behavior instead of hardcoding.

### Error Handling

- **Graceful Degradation**: Have fallback strategies when agents or tools fail.
- **Comprehensive Logging**: Log important events and errors for debugging.
- **Validate Inputs**: Validate inputs to tools and agents to prevent unexpected behavior.

```python
# Example of defensive tool implementation
@app.tool(description="Process sensitive data")
async def process_data(data_id: str, options: Optional[Dict[str, Any]] = None) -> str:
    try:
        # Validate input
        if not data_id or not isinstance(data_id, str):
            return "Error: Invalid data_id provided"
        
        # Validate options if provided
        if options and not isinstance(options, dict):
            return "Error: Options must be a dictionary"
            
        # Process with appropriate error handling
        result = await actual_processing_function(data_id, options)
        return result
    except Exception as e:
        logging.error(f"Error processing data: {str(e)}", exc_info=True)
        # Return user-friendly error without exposing internals
        return "An error occurred while processing the data. Please try again or contact support."
```

### Performance Optimization

- **Minimize LLM Calls**: LLM calls are often the bottleneck, so minimize unnecessary calls.
- **Parallel Processing**: Use ParallelPattern when tasks can be executed independently.
- **Caching**: Consider implementing caching for expensive operations or frequent LLM queries.

```python
# Example of a caching decorator for tools
import functools
import asyncio
from typing import Any, Callable, Dict, Tuple, Awaitable

# Simple cache implementation
cache = {}
cache_lock = asyncio.Lock()

def cached_tool(ttl_seconds: int = 300):
    """Decorator to cache tool results."""
    def decorator(func: Callable[..., Awaitable[Any]]):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Create cache key from args and kwargs
            key_parts = [str(arg) for arg in args]
            key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
            cache_key = func.__name__ + ":" + ":".join(key_parts)
            
            # Check cache
            async with cache_lock:
                if cache_key in cache:
                    entry_time, result = cache[cache_key]
                    # Check if entry is still valid
                    if time.time() - entry_time < ttl_seconds:
                        return result
            
            # Execute function if not in cache or expired
            result = await func(*args, **kwargs)
            
            # Store in cache
            async with cache_lock:
                cache[cache_key] = (time.time(), result)
            
            return result
        return wrapper
    return decorator

# Usage example
@app.tool(description="Fetch external data")
@cached_tool(ttl_seconds=60)  # Cache for 1 minute
async def fetch_external_data(query: str) -> str:
    # Expensive external API call
    response = await make_api_request(query)
    return response
```

### Security

- **Input Validation**: Always validate and sanitize inputs for tools.
- **Least Privilege**: Give tools only the permissions they need.
- **Safe Defaults**: Use safe defaults for optional parameters.
- **Content Safety**: Implement content filtering or validation where appropriate.

```python
# Example of input sanitization for a file operation tool
import os
import re
from pathlib import Path

@app.tool(description="Read file content")
async def read_file_safe(file_path: str) -> str:
    # Sanitize the path to prevent directory traversal
    file_path = os.path.normpath(file_path)
    
    # Ensure the path is within the allowed directory
    allowed_dir = "/app/safe_files"
    full_path = os.path.join(allowed_dir, file_path)
    
    # Verify it's still within the allowed directory
    if not Path(full_path).resolve().is_relative_to(Path(allowed_dir).resolve()):
        return "Error: Access denied. Path is outside the allowed directory."
    
    # Check file extension
    allowed_extensions = ['.txt', '.md', '.csv']
    if not any(full_path.endswith(ext) for ext in allowed_extensions):
        return f"Error: Only files with extensions {', '.join(allowed_extensions)} are allowed."
    
    # Check if file exists
    if not os.path.isfile(full_path):
        return f"Error: File not found."
    
    # Now it's safe to read the file
    try:
        with open(full_path, 'r') as f:
            content = f.read()
        return content
    except Exception as e:
        return f"Error reading file: {str(e)}"
```

### Testing

- **Unit Testing**: Test individual components (agents, tools, patterns) in isolation.
- **Integration Testing**: Test how components work together.
- **Mocking LLMs**: Use mock LLMs for testing to avoid API costs and ensure deterministic results.

```python
# Example of a mock LLM for testing
from tframex.util.llms import BaseLLMWrapper
from tframex.models.primitives import ToolCall

class MockLLMWrapper(BaseLLMWrapper):
    def __init__(self, responses=None):
        super().__init__()
        self.model_id = "mock-llm"
        self.responses = responses or {}
        self.call_history = []
    
    async def generate_response(self, messages, **kwargs):
        # Record the call
        self.call_history.append({"messages": messages, "kwargs": kwargs})
        
        # Get the last user message to use as the key
        last_message = None
        for msg in reversed(messages):
            if msg["role"] == "user":
                last_message = msg["content"]
                break
        
        # Check if we have a predefined response
        if last_message in self.responses:
            resp = self.responses[last_message]
            if isinstance(resp, tuple):
                return resp  # (content, tool_calls)
            return resp, None
        
        # Default mock response
        return f"MOCK RESPONSE: I received: {last_message}", None
    
    async def generate_response_stream(self, messages, **kwargs):
        content, tool_calls = await self.generate_response(messages, **kwargs)
        yield content
        if tool_calls:
            for tc in tool_calls:
                yield tc

# Usage in tests
import unittest
from tframex import TFrameXApp, Message

class TestAgentFlow(unittest.TestCase):
    def setUp(self):
        # Set up mock responses
        mock_responses = {
            "What's the weather?": ("It's sunny today!", None),
            "Calculate 2+2": ("", [ToolCall(id="1", name="calculate", arguments={"expression": "2+2"})])
        }
        
        self.mock_llm = MockLLMWrapper(responses=mock_responses)
        self.app = TFrameXApp(default_llm=self.mock_llm)
        
        # Register test agents and flows
        # ...
    
    async def test_weather_agent(self):
        async with self.app.run_context() as ctx:
            result = await ctx.run_flow(
                "TestFlow",
                Message(role="user", content="What's the weather?")
            )
            self.assertEqual(result.current_message.content, "It's sunny today!") 