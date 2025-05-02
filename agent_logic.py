# agent_logic.py
import logging
from abc import ABC, abstractmethod
from model_logic import BaseModel # Import the base model
# --- MODIFICATION: Added List, Dict for type hint ---
from typing import Any, List, Dict
# --- END MODIFICATION ---

logger = logging.getLogger(__name__)

class BaseAgent(ABC):
    """Abstract base class for all agents."""
    def __init__(self, agent_id: str, model: BaseModel):
        """
        Initializes the BaseAgent.

        Args:
            agent_id (str): A unique identifier for the agent instance.
            model (BaseModel): The language model instance the agent will use.
        """
        self.agent_id = agent_id
        self.model = model
        logger.info(f"Agent '{self.agent_id}' initialized using model '{self.model.model_id}'")

    @abstractmethod
    async def run(self, *args, **kwargs) -> Any:
        """
        The main execution method for the agent.
        Must be implemented by subclasses.
        Returns:
            Any: The result of the agent's operation.
        """
        raise NotImplementedError

    async def _stream_and_aggregate(self, prompt: str, **kwargs) -> str:
        """
        Helper to call model's stream (using chat format) and collect the full response.
        """
        # --- MODIFICATION: Convert prompt string to messages list ---
        messages: List[Dict[str, str]] = [{"role": "user", "content": prompt}]
        full_response = ""
        # --- MODIFICATION: Pass messages list to model ---
        async for chunk in self.model.call_stream(messages, **kwargs):
            full_response += chunk
        return full_response
        # --- END MODIFICATION ---

# Potentially add shared utility functions here in the future
# e.g., parse_xml_tags, format_common_prompts etc.