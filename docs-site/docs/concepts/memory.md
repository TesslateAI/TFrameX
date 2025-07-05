---
sidebar_position: 6
title: Memory
---

# Memory

Memory systems in TFrameX enable agents to maintain conversation context, recall past interactions, and build upon previous knowledge. This is crucial for creating coherent, context-aware AI applications.

## What is Memory?

Memory in TFrameX:
- Stores conversation history between agents and users
- Maintains context across multiple interactions
- Enables agents to reference previous messages
- Supports different storage backends
- Manages memory size and retention

## Memory Architecture

```python
from tframex.util.memory import BaseMemoryStore, Message

# Memory stores implement this interface
class BaseMemoryStore:
    async def add_message(self, message: Message) -> None:
        """Add a message to memory."""
        pass
    
    async def get_history(
        self, 
        limit: Optional[int] = None,
        offset: int = 0,
        roles: Optional[List[str]] = None
    ) -> List[Message]:
        """Retrieve message history."""
        pass
    
    async def clear(self) -> None:
        """Clear all messages."""
        pass
    
    async def get_context_window(
        self, 
        max_tokens: int = 4000
    ) -> List[Message]:
        """Get messages that fit in token limit."""
        pass
```

## Built-in Memory Stores

### InMemoryMemoryStore

The default memory store that keeps messages in RAM:

```python
from tframex.util.memory import InMemoryMemoryStore

# Basic usage
memory = InMemoryMemoryStore()

# With size limit
memory = InMemoryMemoryStore(max_messages=100)

# Use with an agent
agent = LLMAgent(
    name="Assistant",
    llm=llm,
    memory_store=memory
)
```

**Features:**
- Fast access
- Configurable size limits
- FIFO eviction when full
- Thread-safe operations

**Configuration Options:**
```python
memory = InMemoryMemoryStore(
    max_messages=100,        # Maximum messages to store
    max_tokens=8000,        # Maximum tokens to maintain
    eviction_strategy="fifo" # How to remove old messages
)
```

## Custom Memory Stores

### Database Memory Store

Implement persistent memory with a database:

```python
import asyncpg
from datetime import datetime
from typing import List, Optional

class PostgresMemoryStore(BaseMemoryStore):
    def __init__(self, connection_string: str):
        self.conn_string = connection_string
        self.pool = None
    
    async def initialize(self):
        """Create connection pool and tables."""
        self.pool = await asyncpg.create_pool(self.conn_string)
        
        async with self.pool.acquire() as conn:
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS messages (
                    id SERIAL PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT,
                    timestamp TIMESTAMP DEFAULT NOW(),
                    metadata JSONB
                )
            ''')
    
    async def add_message(self, message: Message) -> None:
        async with self.pool.acquire() as conn:
            await conn.execute(
                '''INSERT INTO messages (session_id, role, content, metadata)
                   VALUES ($1, $2, $3, $4)''',
                self.session_id,
                message.role,
                message.content,
                message.metadata
            )
    
    async def get_history(
        self, 
        limit: Optional[int] = None,
        offset: int = 0,
        roles: Optional[List[str]] = None
    ) -> List[Message]:
        query = '''
            SELECT role, content, metadata, timestamp
            FROM messages
            WHERE session_id = $1
        '''
        params = [self.session_id]
        
        if roles:
            query += ' AND role = ANY($2)'
            params.append(roles)
        
        query += ' ORDER BY timestamp DESC'
        
        if limit:
            query += f' LIMIT {limit} OFFSET {offset}'
        
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(query, *params)
            
        return [
            Message(
                role=row['role'],
                content=row['content'],
                metadata=row['metadata']
            )
            for row in reversed(rows)  # Restore chronological order
        ]
```

### Redis Memory Store

Fast, distributed memory with Redis:

```python
import redis.asyncio as redis
import json
from datetime import datetime, timedelta

class RedisMemoryStore(BaseMemoryStore):
    def __init__(
        self, 
        redis_url: str,
        ttl_hours: int = 24,
        max_messages: int = 1000
    ):
        self.redis_url = redis_url
        self.ttl = timedelta(hours=ttl_hours)
        self.max_messages = max_messages
        self.client = None
    
    async def initialize(self):
        self.client = await redis.from_url(self.redis_url)
    
    async def add_message(self, message: Message) -> None:
        key = f"session:{self.session_id}:messages"
        
        # Serialize message
        message_data = {
            "role": message.role,
            "content": message.content,
            "timestamp": datetime.now().isoformat(),
            "metadata": message.metadata
        }
        
        # Add to list
        await self.client.lpush(key, json.dumps(message_data))
        
        # Trim to max size
        await self.client.ltrim(key, 0, self.max_messages - 1)
        
        # Set expiration
        await self.client.expire(key, self.ttl)
    
    async def get_history(self, limit=None, offset=0, roles=None):
        key = f"session:{self.session_id}:messages"
        
        # Get all messages
        messages_data = await self.client.lrange(key, 0, -1)
        
        # Parse messages
        messages = []
        for data in messages_data:
            msg_dict = json.loads(data)
            message = Message(
                role=msg_dict["role"],
                content=msg_dict["content"]
            )
            
            if roles and message.role not in roles:
                continue
                
            messages.append(message)
        
        # Apply offset and limit
        messages = messages[offset:]
        if limit:
            messages = messages[:limit]
        
        return list(reversed(messages))  # Chronological order
```

## Memory Patterns

### Conversation Memory

Standard conversation tracking:

```python
# Agent automatically manages conversation memory
agent = LLMAgent(
    name="ConversationBot",
    llm=llm,
    memory_store=InMemoryMemoryStore(max_messages=50),
    system_prompt="You are a helpful assistant. Reference previous messages when relevant."
)

# Memory is automatically populated during interactions
async with app.run_context() as rt:
    # First message
    response1 = await rt.call_agent("ConversationBot", "My name is Alice")
    # Agent remembers the name
    response2 = await rt.call_agent("ConversationBot", "What's my name?")
    # response2 will reference "Alice"
```

### Shared Memory

Multiple agents sharing memory:

```python
# Create shared memory
shared_memory = InMemoryMemoryStore(max_messages=200)

# Create agents with shared memory
analyst = LLMAgent(
    name="Analyst",
    llm=llm,
    memory_store=shared_memory
)

writer = LLMAgent(
    name="Writer",
    llm=llm,
    memory_store=shared_memory
)

# Both agents see the same conversation history
```

### Scoped Memory

Different memory scopes for different contexts:

```python
class ScopedMemoryStore(BaseMemoryStore):
    def __init__(self):
        self.scopes = {}
    
    def get_scope(self, scope_name: str) -> BaseMemoryStore:
        if scope_name not in self.scopes:
            self.scopes[scope_name] = InMemoryMemoryStore()
        return self.scopes[scope_name]
    
    async def add_message(self, message: Message, scope: str = "default"):
        store = self.get_scope(scope)
        await store.add_message(message)

# Use different scopes
memory = ScopedMemoryStore()
memory.add_message(user_message, scope="user_123")
memory.add_message(system_message, scope="system")
```

## Memory Management

### Token-Based Limits

Manage memory based on token counts:

```python
class TokenLimitedMemoryStore(InMemoryMemoryStore):
    def __init__(self, max_tokens: int = 4000):
        super().__init__()
        self.max_tokens = max_tokens
    
    async def add_message(self, message: Message):
        await super().add_message(message)
        
        # Estimate tokens (rough approximation)
        total_tokens = sum(
            len(msg.content.split()) * 1.3  # Rough token estimate
            for msg in self.messages
        )
        
        # Remove old messages if over limit
        while total_tokens > self.max_tokens and len(self.messages) > 1:
            self.messages.pop(0)
            total_tokens = sum(
                len(msg.content.split()) * 1.3
                for msg in self.messages
            )
```

### Sliding Window Memory

Keep only recent context:

```python
class SlidingWindowMemory(BaseMemoryStore):
    def __init__(self, window_size: int = 10):
        self.window_size = window_size
        self.messages = []
    
    async def add_message(self, message: Message):
        self.messages.append(message)
        
        # Keep only the last window_size messages
        if len(self.messages) > self.window_size:
            self.messages = self.messages[-self.window_size:]
    
    async def get_history(self, limit=None, offset=0, roles=None):
        return self.messages[offset:limit] if limit else self.messages[offset:]
```

### Summary Memory

Compress old conversations into summaries:

```python
class SummaryMemory(BaseMemoryStore):
    def __init__(self, summarizer_agent: str, threshold: int = 50):
        self.recent_messages = []
        self.summaries = []
        self.summarizer_agent = summarizer_agent
        self.threshold = threshold
    
    async def add_message(self, message: Message):
        self.recent_messages.append(message)
        
        # Summarize when threshold reached
        if len(self.recent_messages) >= self.threshold:
            await self.summarize_and_compress()
    
    async def summarize_and_compress(self):
        # Get conversation text
        conversation = "\n".join(
            f"{msg.role}: {msg.content}" 
            for msg in self.recent_messages
        )
        
        # Call summarizer agent
        summary = await self.context.call_agent(
            self.summarizer_agent,
            f"Summarize this conversation:\n{conversation}"
        )
        
        # Store summary
        self.summaries.append(Message(
            role="system",
            content=f"Previous conversation summary: {summary}"
        ))
        
        # Keep only recent messages
        self.recent_messages = self.recent_messages[-10:]
```

## Memory Search and Retrieval

### Semantic Search

Find relevant memories using embeddings:

```python
import numpy as np
from typing import List

class SemanticMemoryStore(BaseMemoryStore):
    def __init__(self, embedding_model):
        self.messages = []
        self.embeddings = []
        self.embedding_model = embedding_model
    
    async def add_message(self, message: Message):
        # Store message
        self.messages.append(message)
        
        # Generate embedding
        embedding = await self.embedding_model.embed(message.content)
        self.embeddings.append(embedding)
    
    async def search(self, query: str, top_k: int = 5) -> List[Message]:
        # Get query embedding
        query_embedding = await self.embedding_model.embed(query)
        
        # Calculate similarities
        similarities = [
            np.dot(query_embedding, emb) / 
            (np.linalg.norm(query_embedding) * np.linalg.norm(emb))
            for emb in self.embeddings
        ]
        
        # Get top k indices
        top_indices = np.argsort(similarities)[-top_k:][::-1]
        
        # Return corresponding messages
        return [self.messages[i] for i in top_indices]
```

### Filtered Retrieval

Retrieve messages based on criteria:

```python
class FilterableMemoryStore(BaseMemoryStore):
    async def get_messages_by_metadata(
        self, 
        **metadata_filters
    ) -> List[Message]:
        """Get messages matching metadata criteria."""
        filtered = []
        
        for message in self.messages:
            if all(
                message.metadata.get(key) == value
                for key, value in metadata_filters.items()
            ):
                filtered.append(message)
        
        return filtered
    
    async def get_messages_by_date_range(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> List[Message]:
        """Get messages within date range."""
        return [
            msg for msg in self.messages
            if start_date <= msg.timestamp <= end_date
        ]
```

## Best Practices

### 1. Choose Appropriate Storage

```python
# Development: In-memory
dev_memory = InMemoryMemoryStore(max_messages=100)

# Production: Persistent
prod_memory = PostgresMemoryStore(connection_string)

# High-performance: Redis
cache_memory = RedisMemoryStore(redis_url)

# Long-term: S3 or similar
archive_memory = S3MemoryStore(bucket_name)
```

### 2. Implement Cleanup Strategies

```python
class AutoCleanupMemory(BaseMemoryStore):
    async def cleanup(self):
        """Regular cleanup tasks."""
        # Remove old messages
        cutoff_date = datetime.now() - timedelta(days=30)
        self.messages = [
            msg for msg in self.messages
            if msg.timestamp > cutoff_date
        ]
        
        # Archive important messages
        important = [
            msg for msg in self.messages
            if msg.metadata.get("important", False)
        ]
        await self.archive(important)
```

### 3. Handle Memory Overflow

```python
class SafeMemoryStore(BaseMemoryStore):
    def __init__(self, max_size: int, overflow_handler):
        self.max_size = max_size
        self.overflow_handler = overflow_handler
        self.messages = []
    
    async def add_message(self, message: Message):
        if len(self.messages) >= self.max_size:
            # Handle overflow
            await self.overflow_handler(self.messages)
            # Keep most recent 80%
            self.messages = self.messages[int(self.max_size * 0.2):]
        
        self.messages.append(message)
```

## Testing Memory

```python
import pytest

@pytest.mark.asyncio
async def test_memory_persistence():
    memory = InMemoryMemoryStore(max_messages=5)
    
    # Add messages
    for i in range(10):
        await memory.add_message(
            Message(role="user", content=f"Message {i}")
        )
    
    # Check only last 5 are kept
    history = await memory.get_history()
    assert len(history) == 5
    assert history[-1].content == "Message 9"

@pytest.mark.asyncio
async def test_memory_filtering():
    memory = FilterableMemoryStore()
    
    # Add messages with metadata
    await memory.add_message(
        Message(
            role="user", 
            content="Important",
            metadata={"priority": "high"}
        )
    )
    
    # Test filtering
    high_priority = await memory.get_messages_by_metadata(priority="high")
    assert len(high_priority) == 1
```

## Enterprise Memory Features

### Audit Trail Memory

```python
class AuditMemoryStore(BaseMemoryStore):
    async def add_message(self, message: Message):
        # Add audit metadata
        message.metadata.update({
            "timestamp": datetime.now().isoformat(),
            "user_id": self.current_user_id,
            "session_id": self.session_id,
            "ip_address": self.request_ip,
            "compliance_flags": self.check_compliance(message)
        })
        
        # Store in both operational and audit stores
        await self.operational_store.add_message(message)
        await self.audit_store.add_message(message)
```

### Encrypted Memory

```python
from cryptography.fernet import Fernet

class EncryptedMemoryStore(BaseMemoryStore):
    def __init__(self, encryption_key: bytes):
        self.cipher = Fernet(encryption_key)
        self.messages = []
    
    async def add_message(self, message: Message):
        # Encrypt content
        encrypted_content = self.cipher.encrypt(
            message.content.encode()
        )
        
        # Store encrypted
        encrypted_message = Message(
            role=message.role,
            content=encrypted_content.decode(),
            metadata=message.metadata
        )
        self.messages.append(encrypted_message)
    
    async def get_history(self, **kwargs):
        # Decrypt on retrieval
        decrypted = []
        for msg in self.messages:
            decrypted_content = self.cipher.decrypt(
                msg.content.encode()
            )
            decrypted.append(Message(
                role=msg.role,
                content=decrypted_content.decode(),
                metadata=msg.metadata
            ))
        return decrypted
```

## Next Steps

Now that you understand memory:

1. Explore [MCP Integration](mcp-integration) for external memory services
2. Learn about [Enterprise Features](../enterprise/overview) for production memory
3. Study [API Reference](../api/memory) for detailed documentation
4. Check [Examples](../examples/advanced-examples#memory-patterns) for implementations