# base.py

import logging
from abc import ABC, abstractmethod
from typing import AsyncGenerator, Dict, List

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class BaseModel(ABC):
    """Abstract base class for language models."""
    def __init__(self, model_id: str):
        self.model_id = model_id
        logger.info(f"Initializing base model structure for ID: {model_id}")

    @abstractmethod
    async def call_stream(self, messages: List[Dict[str, str]], **kwargs) -> AsyncGenerator[str, None]:
        """
        Calls the language model (now expecting chat format) and streams response chunks.
        Must be implemented by subclasses.

        Args:
            messages (List[Dict[str, str]]): A list of message dictionaries,
                                             e.g., [{"role": "user", "content": "Hello"}].
        Yields:
            str: Chunks of the generated text content.
        """
        raise NotImplementedError
        yield "" # Required for async generator typing

    @abstractmethod
    async def close_client(self):
        """Closes any underlying network clients."""
        raise NotImplementedError