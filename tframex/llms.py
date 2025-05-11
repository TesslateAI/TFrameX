import httpx
import json
import asyncio
import logging
from abc import ABC, abstractmethod
from typing import AsyncGenerator, Union, List, Dict, Any, Literal, overload, Optional

from tframex.primitives import Message, MessageChunk, ToolCall, FunctionCall

logger = logging.getLogger(__name__)

class BaseLLMWrapper(ABC):
    def __init__(self, model_id: str, api_key: Optional[str] = None, 
                 api_base_url: Optional[str] = None, client_kwargs: Optional[Dict[str, Any]] = None):
        self.model_id = model_id
        self.api_key = api_key
        self.api_base_url = api_base_url.rstrip('/') if api_base_url else None
        self.client_kwargs = client_kwargs or {}
        self._client: Optional[httpx.AsyncClient] = None
        logger.info(f"BaseLLMWrapper initialized for model_id: {model_id}")

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            headers = {}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"
            headers["Content-Type"] = "application/json"
            
            timeout_config = self.client_kwargs.pop("timeout", None)
            if timeout_config is None:
                timeouts = httpx.Timeout(300.0, connect=60.0) # Default: 5 min total, 1 min connect
            elif isinstance(timeout_config, (int, float)):
                timeouts = httpx.Timeout(timeout_config)
            else: # Assumes httpx.Timeout object
                timeouts = timeout_config

            self._client = httpx.AsyncClient(headers=headers, timeout=timeouts, **self.client_kwargs)
        return self._client
    
    @overload
    async def chat_completion(
        self, messages: List[Message], stream: Literal[True], **kwargs: Any
    ) -> AsyncGenerator[MessageChunk, None]: ...
    
    @overload
    async def chat_completion(
        self, messages: List[Message], stream: Literal[False] = False, **kwargs: Any
    ) -> Message: ...

    @abstractmethod
    async def chat_completion(
        self, messages: List[Message], stream: bool = False, **kwargs: Any
    ) -> Union[Message, AsyncGenerator[MessageChunk, None]]:
        pass

    async def close(self):
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            logger.info(f"LLM client for {self.model_id} closed.")

class OpenAIChatLLM(BaseLLMWrapper):
    def __init__(self, model_name: str, api_base_url: str, api_key: Optional[str] = None,
                 default_max_tokens: int = 4096, default_temperature: float = 0.7, **kwargs: Any):
        super().__init__(model_id=model_name, api_key=api_key, api_base_url=api_base_url, client_kwargs=kwargs)
        self.chat_completions_url = f"{self.api_base_url}/v1/chat/completions"
        self.default_max_tokens = default_max_tokens
        self.default_temperature = default_temperature

    async def chat_completion(
        self, messages: List[Message], stream: bool = False, max_retries: int = 2, **kwargs: Any
    ) -> Union[Message, AsyncGenerator[MessageChunk, None]]:
        client = await self._get_client()
        payload: Dict[str, Any] = {
            "model": self.model_id,
            "messages": [msg.model_dump(exclude_none=True) for msg in messages],
            "stream": stream,
            "max_tokens": kwargs.get('max_tokens', self.default_max_tokens),
            "temperature": kwargs.get('temperature', self.default_temperature),
        }
        
        # Handle tools if provided
        if "tools" in kwargs and kwargs["tools"]:
            payload["tools"] = kwargs["tools"] # Expects List[ToolDefinition.model_dump()]
            if "tool_choice" in kwargs:
                payload["tool_choice"] = kwargs["tool_choice"]
        
        # Remove our custom/internal kwargs before sending to OpenAI
        internal_kwargs = ['max_retries']
        for ikw in internal_kwargs:
            kwargs.pop(ikw, None)
        payload.update(kwargs)


        last_exception = None
        for attempt in range(max_retries + 1):
            try:
                logger.debug(f"OpenAIChatLLM: Attempt {attempt+1} to {self.chat_completions_url}. Stream: {stream}. Model: {self.model_id}")
                if stream:
                    return self._stream_response(client, self.chat_completions_url, payload) # type: ignore
                else:
                    response = await client.post(self.chat_completions_url, json=payload)
                    response.raise_for_status()
                    response_data = response.json()
                    choice = response_data.get("choices", [{}])[0]
                    msg_data = choice.get("message", {})
                    return Message(**msg_data)

            except httpx.HTTPStatusError as e:
                logger.error(f"HTTP Error from LLM API ({self.model_id}): {e.response.status_code} - {e.response.text}", exc_info=False) # Reduce noise
                err_content = f"LLM API Error: {e.response.status_code}"
                try: err_detail = e.response.json().get("error",{}).get("message",""); err_content += f" - {err_detail}" if err_detail else ""
                except: pass
                if stream: 
                    async def err_gen(): 
                        yield MessageChunk(role="assistant", content=err_content)
                        return 
                    return err_gen() # type: ignore
                return Message(role="assistant", content=err_content)
            except (httpx.ReadError, httpx.ConnectError, httpx.PoolTimeout, httpx.RemoteProtocolError) as e:
                last_exception = e
                logger.warning(f"LLM Call Attempt {attempt+1} for {self.model_id} failed with {type(e).__name__}: {e}. Retrying...")
                if attempt < max_retries: await asyncio.sleep(1 * (2 ** attempt))
            except Exception as e:
                logger.error(f"Unexpected error during LLM call ({self.model_id}): {e}", exc_info=True)
                err_content = f"Unexpected error: {e}"
                if stream: 
                    async def err_gen(): 
                        yield MessageChunk(role="assistant", content=err_content)
                        return
                    return err_gen() # type: ignore
                return Message(role="assistant", content=err_content)

        err_msg = f"LLM call ({self.model_id}) failed after {max_retries + 1} attempts. Last error: {last_exception}"
        logger.error(err_msg)
        if stream: 
            async def err_gen(): 
                yield MessageChunk(role="assistant", content=err_msg)
                return
            return err_gen() # type: ignore
        return Message(role="assistant", content=err_msg)

    async def _stream_response(self, client: httpx.AsyncClient, url: str, payload: Dict[str, Any]) -> AsyncGenerator[MessageChunk, None]:
        async with client.stream("POST", url, json=payload) as response:
            if response.status_code != 200:
                error_content_bytes = await response.aread()
                error_content = error_content_bytes.decode(errors='replace')
                logger.error(f"LLM API Stream Error ({self.model_id}): Status {response.status_code}, Response: {error_content}")
                yield MessageChunk(role="assistant", content=f"LLM API Stream Error: {response.status_code} - {error_content}")
                return

            # Tool call accumulation logic (OpenAI specific streaming format for tools)
            current_tool_calls: List[Dict[str, Any]] = []

            async for line in response.aiter_lines():
                if line.startswith("data:"):
                    data_content = line[len("data:") :].strip()
                    if data_content == "[DONE]":
                        break
                    try:
                        chunk_data = json.loads(data_content)
                        delta = chunk_data.get("choices", [{}])[0].get("delta", {})
                        
                        role_chunk = delta.get("role") # Will be "assistant" on first useful chunk
                        content_chunk = delta.get("content")
                        tool_calls_chunk = delta.get("tool_calls")

                        # Yield content immediately if present
                        if content_chunk:
                            yield MessageChunk(role="assistant", content=content_chunk)
                        
                        if tool_calls_chunk:
                            for tc_delta in tool_calls_chunk:
                                index = tc_delta.get("index", 0)
                                
                                # Ensure current_tool_calls list is long enough
                                while index >= len(current_tool_calls):
                                    current_tool_calls.append({}) # Initialize with empty dict

                                if "id" in tc_delta:
                                    current_tool_calls[index]["id"] = tc_delta["id"]
                                current_tool_calls[index]["type"] = "function" # OpenAI specific
                                
                                if "function" in tc_delta:
                                    current_tool_calls[index].setdefault("function", {})
                                    if "name" in tc_delta["function"]:
                                        current_tool_calls[index]["function"]["name"] = tc_delta["function"]["name"]
                                    if "arguments" in tc_delta["function"]:
                                        current_tool_calls[index]["function"].setdefault("arguments", "")
                                        current_tool_calls[index]["function"]["arguments"] += tc_delta["function"]["arguments"]
                        
                        finish_reason = chunk_data.get("choices", [{}])[0].get("finish_reason")
                        if finish_reason == "tool_calls" or (finish_reason and not tool_calls_chunk and current_tool_calls): # End of stream and we have tool calls
                            parsed_tool_calls_list = []
                            for tc_data in current_tool_calls:
                                if tc_data.get("id") and tc_data.get("function", {}).get("name"):
                                    parsed_tool_calls_list.append(
                                        ToolCall(
                                            id=tc_data["id"],
                                            function=FunctionCall(
                                                name=tc_data["function"]["name"],
                                                arguments=tc_data["function"].get("arguments", "{}") # Default to empty JSON obj string
                                            )
                                        )
                                    )
                            if parsed_tool_calls_list:
                                yield MessageChunk(role="assistant", content=None, tool_calls=parsed_tool_calls_list)
                            current_tool_calls = [] # Reset for potential future chunks (though unlikely with OpenAI)
                            
                    except json.JSONDecodeError:
                        logger.warning(f"Could not decode stream chunk for {self.model_id}: {data_content}")

            # If stream ended and there are still unyielded tool calls (e.g. no explicit finish_reason="tool_calls")
            if current_tool_calls:
                parsed_tool_calls_list = []
                for tc_data in current_tool_calls:
                     if tc_data.get("id") and tc_data.get("function", {}).get("name"):
                        parsed_tool_calls_list.append(
                            ToolCall(id=tc_data["id"], function=FunctionCall(name=tc_data["function"]["name"], arguments=tc_data["function"].get("arguments", "{}")))
                        )
                if parsed_tool_calls_list:
                    yield MessageChunk(role="assistant", content=None, tool_calls=parsed_tool_calls_list)