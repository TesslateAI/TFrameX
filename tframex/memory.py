import logging
from abc import ABC, abstractmethod
from typing import List, Optional
from tframex.primitives import Message

logger = logging.getLogger(__name__)

class BaseMemoryStore(ABC):
    @abstractmethod
    async def add_message(self, message: Message) -> None: ...
    
    @abstractmethod
    async def get_history(self, limit: Optional[int] = None, 
                          offset: int = 0, 
                          roles: Optional[List[str]] = None) -> List[Message]: ...
    
    @abstractmethod
    async def clear(self) -> None: ...

class InMemoryMemoryStore(BaseMemoryStore):
    def __init__(self, max_history_size: Optional[int] = None):
        self._history: List[Message] = []
        self.max_history_size = max_history_size
        logger.debug(f"InMemoryMemoryStore initialized. Max size: {max_history_size}")

    async def add_message(self, message: Message) -> None:
        self._history.append(message)
        if self.max_history_size is not None and len(self._history) > self.max_history_size:
            self._history.pop(0) # Keep it a rolling window
        logger.debug(f"Added message to InMemoryMemoryStore: Role={message.role}, Content='{str(message.content)[:50]}...', ToolCalls={bool(message.tool_calls)}")

    async def get_history(self, limit: Optional[int] = None, 
                          offset: int = 0, 
                          roles: Optional[List[str]] = None) -> List[Message]:
        
        filtered_history = self._history
        if roles:
            filtered_history = [msg for msg in self._history if msg.role in roles]

        start_index = offset
        end_index = len(filtered_history)
        if limit is not None:
            # If limit is used, it usually means "last N messages"
            # So offset should count from the end if limit is present
            # For simplicity now, offset from start, then limit
            end_index = min(start_index + limit, len(filtered_history))
        
        return list(filtered_history[start_index:end_index])

    async def clear(self) -> None:
        self._history = []
        logger.info("InMemoryMemoryStore cleared.")