# agents.py
import logging
from tframex.agents.agent_logic import BaseAgent # NEW
from tframex.model.model_logic import BaseModel # NEWBaseModel

logger = logging.getLogger(__name__)

class BasicAgent(BaseAgent):
    """
    A simple agent that takes a prompt, calls the LLM, and returns the full response.
    """
    def __init__(self, agent_id: str, model: BaseModel):
        super().__init__(agent_id, model)

    async def run(self, prompt: str, **kwargs) -> str:
        """
        Sends the prompt to the LLM and returns the aggregated streamed response.

        Args:
            prompt (str): The input prompt.
            **kwargs: Additional parameters for the model call (e.g., max_tokens).

        Returns:
            str: The complete response from the LLM.
        """
        logger.info(f"Agent '{self.agent_id}' running with prompt: '{prompt[:50]}...'")
        full_response = await self._stream_and_aggregate(prompt, **kwargs)
        logger.info(f"Agent '{self.agent_id}' finished.")
        return full_response

class ContextAgent(BaseAgent):
    """
    An agent that combines a given context with the prompt before calling the LLM.
    """
    def __init__(self, agent_id: str, model: BaseModel, context: str):
        """
        Initializes the ContextAgent.

        Args:
            agent_id (str): Unique identifier for the agent.
            model (BaseModel): The language model instance.
            context (str): The predefined context to use.
        """
        super().__init__(agent_id, model)
        self.context = context
        logger.info(f"Agent '{self.agent_id}' initialized with context: '{self.context[:100]}...'")

    async def run(self, prompt: str, **kwargs) -> str:
        """
        Combines context and prompt, sends to LLM, and returns the full response.

        Args:
            prompt (str): The input prompt.
            **kwargs: Additional parameters for the model call (e.g., max_tokens).

        Returns:
            str: The complete response from the LLM.
        """
        combined_prompt = f"Context:\n{self.context}\n\n---\n\nPrompt:\n{prompt}"
        logger.info(f"Agent '{self.agent_id}' running with combined prompt.")
        logger.debug(f"Agent '{self.agent_id}' combined prompt: {combined_prompt}") # Log full prompt if needed
        full_response = await self._stream_and_aggregate(combined_prompt, **kwargs)
        logger.info(f"Agent '{self.agent_id}' finished.")
        return full_response