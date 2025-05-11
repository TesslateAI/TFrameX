from typing import Any, Dict, Optional
from .primitives import Message

class FlowContext:
    """
    Holds the current state and data being processed within a single execution of a Flow.
    """
    def __init__(self, initial_input: Message, shared_data: Optional[Dict[str, Any]] = None):
        self.current_message: Message = initial_input
        self.history: list[Message] = [initial_input] # History of messages within this flow execution
        self.shared_data: Dict[str, Any] = shared_data or {} # For patterns/steps to share data

    def update_current_message(self, message: Message):
        self.current_message = message
        self.history.append(message)

    def __str__(self):
        return (f"FlowContext(current_message='{str(self.current_message.content)[:50]}...', "
                f"history_len={len(self.history)}, shared_data_keys={list(self.shared_data.keys())})")