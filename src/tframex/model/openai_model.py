import logging
from typing import AsyncGenerator, Dict, List

from openai import AsyncOpenAI
from .base import BaseModel

logger = logging.getLogger(__name__)


class OpenAIModel(BaseModel):
    """
    Represents a connection to OpenAI's official hosted models using the OpenAI SDK.
    Designed to be used with any OpenAI-compatible chat model (e.g., gpt-3.5-turbo, gpt-4).
    """
    def __init__(self,
                 model_name: str,
                 api_key: str,
                 default_max_tokens: int = 1024,
                 default_temperature: float = 0.7):
        """
        Initializes the OpenAIModel with credentials and default generation parameters.

        Args:
            model_name (str): The model ID to use (e.g., "gpt-4").
            api_key (str): Your OpenAI API key.
            default_max_tokens (int): Default max tokens to generate if not overridden.
            default_temperature (float): Default temperature for sampling.
        """
        super().__init__(model_id=f"openai_{model_name}")  # Call BaseModel constructor and set model_id
        self.client = AsyncOpenAI(api_key=api_key)         # Initialize OpenAI async client with API key
        self.model_name = model_name                       # Store the model name (e.g., "gpt-4")
        self.default_max_tokens = default_max_tokens       # Set default max_tokens if not overridden
        self.default_temperature = default_temperature     # Set default temperature if not overridden
        logger.info(f"OpenAIModel '{self.model_id}' initialized.")  # Log successful model setup


    async def call_stream(self, messages: List[Dict[str, str]], **kwargs) -> AsyncGenerator[str, None]:
        """
        Calls OpenAI's chat completions API with the given message history and streams the response.

        Args:
            messages (List[Dict[str, str]]): The conversation history/prompt.
            **kwargs: Optional overrides like 'max_tokens', 'temperature'.

        Yields:
            str: Chunks of the generated text content.
        """
        try:
            # Send the request to OpenAI with streaming enabled
            response = await self.client.chat.completions.create(
                model=self.model_name,                                           # Model name (e.g., "gpt-4")
                messages=messages,                                               # Chat history in OpenAI format
                max_tokens=kwargs.get("max_tokens", self.default_max_tokens),    # Use passed or default token limit
                temperature=kwargs.get("temperature", self.default_temperature), # Use passed or default temperature
                stream=True,                                                     # Enable streaming response
                **{k: v for k, v in kwargs.items() if k not in ["max_tokens", "temperature"]}  # Pass other kwargs
            )

            # Iterate through streamed response chunks
            async for chunk in response:
                if chunk.choices:                             # Ensure choices exist in the chunk
                    delta = chunk.choices[0].delta            # Get the delta object (partial update)
                    if delta.content is not None:             # Yield content if present
                        yield delta.content

        except Exception as e:
            # Log and yield error string if anything goes wrong
            logger.error(f"[{self.model_id}] OpenAI call failed: {e}", exc_info=True)
            yield f"ERROR: {str(e)}"


    async def close_client(self):
        """
        Placeholder for SDK compatibility with BaseModel. No-op for OpenAI client.
        """
        logger.info(f"[{self.model_id}] OpenAI client closed (noop).")
