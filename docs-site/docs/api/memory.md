---
sidebar_position: 4
title: Memory API
---

# Memory API

TFrameX provides a simple memory system for storing conversation history. The current implementation focuses on basic storage and retrieval functionality.

## Overview

The memory system consists of:
- **BaseMemoryStore**: Abstract base class for memory implementations
- **InMemoryMemoryStore**: Simple in-memory storage implementation

## BaseMemoryStore

Abstract base class that defines the memory interface:

```python
from tframex import BaseMemoryStore, Message
from typing import List, Optional

class BaseMemoryStore:
    async def add_message(self, message: Message) -> None:
        """Add a message to memory storage."""
        pass
    
    async def get_history(
        self, 
        limit: Optional[int] = None,
        offset: int = 0,
        roles: Optional[List[str]] = None
    ) -> List[Message]:
        """Retrieve message history with optional filtering."""
        pass
    
    async def clear(self) -> None:
        """Clear all stored messages."""
        pass
```

## InMemoryMemoryStore

Basic in-memory implementation with size limits:

```python
from tframex import InMemoryMemoryStore

# Create with default settings (100 message limit)
memory = InMemoryMemoryStore()

# Create with custom message limit
memory = InMemoryMemoryStore(max_messages=50)

# Use in app
from tframex import TFrameXApp

app = TFrameXApp(
    default_memory_store_factory=lambda: InMemoryMemoryStore(max_messages=200)
)
```

### Features

- **Automatic cleanup**: Old messages are removed when limit is exceeded
- **Thread-safe**: Safe for concurrent access
- **Simple interface**: Easy to use and understand

### Limitations

- **No persistence**: Data is lost when the application stops
- **Memory usage**: All messages are kept in RAM
- **No search**: No advanced querying capabilities

## Usage Examples

### Basic Usage

```python
from tframex import InMemoryMemoryStore, Message

memory = InMemoryMemoryStore(max_messages=10)

# Add messages
await memory.add_message(Message(role="user", content="Hello"))
await memory.add_message(Message(role="assistant", content="Hi there!"))

# Get recent history
history = await memory.get_history(limit=5)
print(f"Found {len(history)} messages")

# Get specific roles
user_messages = await memory.get_history(roles=["user"])

# Clear all messages
await memory.clear()
```

### Agent Integration

```python
from tframex import TFrameXApp, InMemoryMemoryStore

app = TFrameXApp(
    default_memory_store_factory=lambda: InMemoryMemoryStore(max_messages=100)
)

@app.agent(name="Assistant")
async def assistant():
    pass

# Memory is automatically handled during conversations
async def main():
    async with app.run_context() as rt:
        # Each call automatically stores messages in memory
        result1 = await rt.call_agent("Assistant", "Remember this: my favorite color is blue")
        result2 = await rt.call_agent("Assistant", "What's my favorite color?")
```

## Custom Memory Stores

You can implement custom memory stores for persistence:

```python
import json
from typing import List, Optional

class FileMemoryStore(BaseMemoryStore):
    def __init__(self, file_path: str, max_messages: int = 100):
        self.file_path = file_path
        self.max_messages = max_messages
        self.messages: List[Message] = []
        self._load_from_file()
    
    def _load_from_file(self):
        try:
            with open(self.file_path, 'r') as f:
                data = json.load(f)
                self.messages = [Message(**msg) for msg in data]
        except FileNotFoundError:
            self.messages = []
    
    def _save_to_file(self):
        with open(self.file_path, 'w') as f:
            json.dump([msg.model_dump() for msg in self.messages], f)
    
    async def add_message(self, message: Message) -> None:
        self.messages.append(message)
        if len(self.messages) > self.max_messages:
            self.messages = self.messages[-self.max_messages:]
        self._save_to_file()
    
    async def get_history(
        self,
        limit: Optional[int] = None,
        offset: int = 0,
        roles: Optional[List[str]] = None
    ) -> List[Message]:
        filtered = self.messages
        
        if roles:
            filtered = [msg for msg in filtered if msg.role in roles]
        
        if offset:
            filtered = filtered[offset:]
        
        if limit:
            filtered = filtered[:limit]
        
        return filtered
    
    async def clear(self) -> None:
        self.messages = []
        self._save_to_file()

# Use custom memory store
app = TFrameXApp(
    default_memory_store_factory=lambda: FileMemoryStore("conversation.json")
)
```

## Enterprise Storage

For production deployments, consider using enterprise storage backends that provide persistent memory storage:

```python
# Enterprise storage provides persistent memory
from tframex.enterprise import EnterpriseApp

app = EnterpriseApp(
    enterprise_config={
        "storage": {
            "default": "postgresql",
            "backends": {
                "postgresql": {
                    "connection_string": "postgresql://user:pass@localhost/db"
                }
            }
        }
    }
)
```

## Best Practices

### Memory Management

```python
# Use appropriate memory limits
memory = InMemoryMemoryStore(max_messages=100)  # Good for chat apps

# For longer conversations, use higher limits
memory = InMemoryMemoryStore(max_messages=1000)  # Good for complex workflows

# For production, use persistent storage
from tframex.enterprise.storage.memory import MemoryStore
memory = MemoryStore(backend="postgresql")
```

### Performance Considerations

```python
# Limit history retrieval for better performance
recent_history = await memory.get_history(limit=50)

# Use role filtering to get specific message types
user_inputs = await memory.get_history(roles=["user"])
assistant_responses = await memory.get_history(roles=["assistant"])
```

### Error Handling

```python
try:
    await memory.add_message(message)
    history = await memory.get_history()
except Exception as e:
    logger.error(f"Memory operation failed: {e}")
    # Handle gracefully
```

## API Reference

### BaseMemoryStore

#### Methods

- `add_message(message: Message) -> None`: Add a message to storage
- `get_history(limit=None, offset=0, roles=None) -> List[Message]`: Retrieve messages
- `clear() -> None`: Remove all messages

### InMemoryMemoryStore

#### Constructor

```python
InMemoryMemoryStore(max_messages: int = 100)
```

#### Parameters

- `max_messages`: Maximum number of messages to store (default: 100)

#### Properties

- `max_messages`: Current message limit
- `current_count`: Number of stored messages

## Next Steps

- See [Enterprise Storage](../enterprise/storage) for persistent options
- Check [Agent Documentation](agents) for memory integration
- Review [Examples](../examples/) for complete implementations