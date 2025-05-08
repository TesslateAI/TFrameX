# model_logic.py
import httpx
import json
import asyncio
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

class VLLMModel(BaseModel):
    """
    Represents a connection to a VLLM OpenAI-compatible endpoint.
    MODIFIED TO USE CHAT COMPLETIONS ENDPOINT AND FORMAT.
    """
    def __init__(self,
                 model_name: str,
                 api_url: str,
                 api_key: str,
                 default_max_tokens: int = 1024,
                 default_temperature: float = 0.7):
        super().__init__(model_id=f"vllm_{model_name.replace('/', '_')}")
        self.model_name = model_name
        base_url = api_url.replace('/v1', '').rstrip('/')
        self.chat_completions_url = f"{base_url}/v1/chat/completions"
        self.api_key = api_key
        self.default_max_tokens = default_max_tokens
        self.default_temperature = default_temperature
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        timeouts = httpx.Timeout(None, connect=100.0)
        self._client = httpx.AsyncClient(headers=self.headers, timeout=timeouts)
        logger.info(f"VLLMModel '{self.model_id}' initialized for CHAT endpoint {self.chat_completions_url}")

    async def call_stream(self, messages: List[Dict[str, str]], max_retries: int = 2, **kwargs) -> AsyncGenerator[str, None]:
        """
        Calls the VLLM CHAT completions endpoint with messages and streams the response.
        Includes basic retry logic for specific network errors.

        Args:
            messages (List[Dict[str, str]]): The conversation history/prompt.
            max_retries (int): Maximum number of retries on specific errors.
            **kwargs: Override default parameters like 'max_tokens', 'temperature'.

        Yields:
            str: Chunks of the generated text content, including tags like <think>.
        """
        payload = {
            "model": self.model_name,
            "messages": messages,
            "max_tokens": kwargs.get('max_tokens', self.default_max_tokens),
            "temperature": kwargs.get('temperature', self.default_temperature),
            "stream": True,
            **{k: v for k, v in kwargs.items() if k not in ['max_tokens', 'temperature', 'max_retries']}
        }

        last_exception = None
        for attempt in range(max_retries + 1):
            try:
                logger.debug(f"[{self.model_id}] Attempt {attempt+1}/{max_retries+1}: Sending request to {self.chat_completions_url}")
                async with self._client.stream("POST", self.chat_completions_url, json=payload) as response:
                    if response.status_code == 429: # Specific handling for rate limits
                         retry_after = int(response.headers.get("Retry-After", "5")) # Default to 5s
                         logger.warning(f"[{self.model_id}] Rate limit hit (429). Retrying after {retry_after} seconds.")
                         await asyncio.sleep(retry_after)
                         last_exception = httpx.HTTPStatusError("Rate limit hit", request=response.request, response=response)
                         continue # Go to next attempt

                    if response.status_code != 200:
                        error_content = await response.aread()
                        error_msg = f"API Error: Status {response.status_code}, Response: {error_content.decode()}"
                        logger.error(f"[{self.model_id}] {error_msg}")
                        yield f"ERROR: {error_msg}" # Yield non-retryable API errors
                        return # Stop processing this request

                    # --- Stream Processing ---
                    async for line in response.aiter_lines():
                        line = line.strip()
                        if line.startswith("data:"):
                            data_content = line[len("data:"):].strip()
                            if data_content == "[DONE]":
                                logger.debug(f"[{self.model_id}] DONE signal received.")
                                return # Successful completion of the stream

                            try:
                                json_data = json.loads(data_content)
                                text_chunk = "" # Initialize empty
                                if 'choices' in json_data and len(json_data['choices']) > 0:
                                    choice = json_data['choices'][0]
                                    if 'delta' in choice and 'content' in choice['delta']:
                                         # Check if content is not None before assigning
                                         content = choice['delta']['content']
                                         if content is not None:
                                             text_chunk = content

                                # Yield chunk even if empty/whitespace
                                yield text_chunk

                            except json.JSONDecodeError:
                                logger.warning(f"[{self.model_id}] Could not decode JSON chunk: {data_content}")
                            except Exception as e:
                                logger.warning(f"[{self.model_id}] Error processing chunk data {data_content}: {e}")

                    logger.debug(f"[{self.model_id}] Stream finished without explicit [DONE] after loop.")
                    return # Successfully finished processing stream

            except httpx.ReadError as e:
                 last_exception = e
                 logger.warning(f"[{self.model_id}] Attempt {attempt+1} failed with ReadError: {e}. Retrying...")
                 await asyncio.sleep(2 ** attempt)
            except httpx.ConnectError as e:
                 last_exception = e
                 logger.warning(f"[{self.model_id}] Attempt {attempt+1} failed with ConnectError: {e}. Retrying...")
                 await asyncio.sleep(2 ** attempt)
            except httpx.PoolTimeout as e:
                 last_exception = e
                 logger.warning(f"[{self.model_id}] Attempt {attempt+1} failed with PoolTimeout: {e}. Retrying...")
                 await asyncio.sleep(2 ** attempt)
            except httpx.RemoteProtocolError as e:
                 last_exception = e
                 logger.warning(f"[{self.model_id}] Attempt {attempt+1} failed with RemoteProtocolError: {e}. Retrying...")
                 await asyncio.sleep(2 ** attempt)
            except Exception as e:
                 logger.error(f"[{self.model_id}] An unexpected error occurred during streaming attempt {attempt+1}: {e}", exc_info=True)
                 yield f"ERROR: Unexpected error - {e}"
                 return

        logger.error(f"[{self.model_id}] All {max_retries + 1} attempts failed. Last error: {last_exception}")
        yield f"ERROR: Request failed after multiple retries - {last_exception}"


    async def close_client(self):
        """Closes the underlying HTTP client."""
        await self._client.aclose()
        logger.info(f"[{self.model_id}] VLLM HTTP client closed.")