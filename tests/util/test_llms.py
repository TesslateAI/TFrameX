
import pytest
import httpx
import json # Make sure json is imported
import asyncio # Make sure asyncio is imported
from unittest.mock import AsyncMock, MagicMock, patch

from tframex import OpenAIChatLLM, Message, MessageChunk, ToolCall, FunctionCall
import tframex.util.llms

@pytest.mark.asyncio
async def test_openai_chat_llm_init():
    llm = OpenAIChatLLM(model_name="test-model", api_base_url="http://localhost:1234/v1", api_key="test_key")
    assert llm.model_id == "test-model"
    assert llm.chat_completions_url == "http://localhost:1234/v1/chat/completions"

@pytest.mark.asyncio
async def test_openai_chat_llm_completion_success(mocker):
    llm = OpenAIChatLLM(model_name="test-model", api_base_url="http://localhost:1111/v1", api_key="fake")
    
    mock_response_json = {
        "id": "chatcmpl-123",
        "object": "chat.completion",
        "created": 1677652288,
        "model": "test-model",
        "choices": [{
            "index": 0,
            "message": {"role": "assistant", "content": "Hello there!"},
            "finish_reason": "stop"
        }]
    }
    
    # Mock the client's post method directly
    mock_async_client_instance = AsyncMock(spec=httpx.AsyncClient)
    mock_async_client_instance.post = AsyncMock(return_value=MagicMock(
        spec=httpx.Response,
        status_code=200,
        json=lambda: mock_response_json,
        raise_for_status=lambda: None 
    ))
    # Patch _get_client to return this specific mocked client instance
    mocker.patch.object(llm, '_get_client', AsyncMock(return_value=mock_async_client_instance))


    messages = [Message(role="user", content="Hi")]
    response_message = await llm.chat_completion(messages)

    assert isinstance(response_message, Message)
    assert response_message.role == "assistant"
    assert response_message.content == "Hello there!"
    mock_async_client_instance.post.assert_called_once()

@pytest.mark.asyncio
async def test_openai_chat_llm_completion_with_tools(mocker):
    llm = OpenAIChatLLM(model_name="test-model", api_base_url="http://localhost:1111/v1", api_key="fake")
    
    tool_call_data = {
        "id": "call_abc123",
        "type": "function",
        "function": {"name": "get_weather", "arguments": '{"location": "Paris"}'}
    }
    mock_response_json = {
        "id": "chatcmpl-124", "object": "chat.completion", "created": 1677652289, "model": "test-model",
        "choices": [{"index": 0, "message": {"role": "assistant", "content": None, "tool_calls": [tool_call_data]}, "finish_reason": "tool_calls"}]
    }
    
    mock_async_client_instance = AsyncMock(spec=httpx.AsyncClient)
    mock_async_client_instance.post = AsyncMock(return_value=MagicMock(
        spec=httpx.Response, status_code=200, json=lambda: mock_response_json, raise_for_status=lambda: None
    ))
    mocker.patch.object(llm, '_get_client', AsyncMock(return_value=mock_async_client_instance))

    messages = [Message(role="user", content="What's the weather in Paris?")]
    tools_def = [{"type": "function", "function": {"name": "get_weather", "description": "...", "parameters": {}}}]
    response_message = await llm.chat_completion(messages, tools=tools_def, tool_choice="auto")

    assert response_message.role == "assistant"
    assert response_message.content is None
    assert response_message.tool_calls is not None
    assert len(response_message.tool_calls) == 1
    tc = response_message.tool_calls[0]
    assert isinstance(tc, ToolCall)
    assert tc.id == "call_abc123"
    assert tc.function.name == "get_weather"
    assert tc.function.arguments == '{"location": "Paris"}'
    
    called_payload = mock_async_client_instance.post.call_args.kwargs['json']
    assert "tools" in called_payload and called_payload["tools"] == tools_def
    assert "tool_choice" in called_payload and called_payload["tool_choice"] == "auto"

@pytest.mark.asyncio
async def test_openai_chat_llm_stream_success(mocker):
    llm = OpenAIChatLLM(model_name="test-model", api_base_url="http://localhost:1111/v1", api_key="fake")

    async def mock_aiter_lines_gen():
        yield "data: {\"id\":\"1\",\"object\":\"chat.completion.chunk\",\"created\":1,\"model\":\"test-model\",\"choices\":[{\"index\":0,\"delta\":{\"role\":\"assistant\"},\"finish_reason\":null}]}\n\n"
        yield "data: {\"id\":\"1\",\"object\":\"chat.completion.chunk\",\"created\":1,\"model\":\"test-model\",\"choices\":[{\"index\":0,\"delta\":{\"content\":\"Hello\"},\"finish_reason\":null}]}\n\n"
        yield "data: {\"id\":\"1\",\"object\":\"chat.completion.chunk\",\"created\":1,\"model\":\"test-model\",\"choices\":[{\"index\":0,\"delta\":{\"content\":\" world\"},\"finish_reason\":null}]}\n\n"
        yield "data: {\"id\":\"1\",\"object\":\"chat.completion.chunk\",\"created\":1,\"model\":\"test-model\",\"choices\":[{\"index\":0,\"delta\":{},\"finish_reason\":\"stop\"}]}\n\n"
        yield "data: [DONE]\n\n"

    mock_httpx_response = MagicMock(spec=httpx.Response, status_code=200)
    mock_httpx_response.aiter_lines = mock_aiter_lines_gen # Assign the async generator function

    # Mock the client.stream() call to return an async context manager that yields the mock_httpx_response
    mock_stream_context_manager = AsyncMock() # This will be the return value of client.stream()
    mock_stream_context_manager.__aenter__.return_value = mock_httpx_response # What `async with ... as response` gets
    mock_stream_context_manager.__aexit__.return_value = None

    mock_async_client_instance = AsyncMock(spec=httpx.AsyncClient)
    mock_async_client_instance.stream = AsyncMock(return_value=mock_stream_context_manager) # client.stream returns the context manager
    mocker.patch.object(llm, '_get_client', AsyncMock(return_value=mock_async_client_instance))
    
    messages = [Message(role="user", content="Hi")]
    chunks = []
    # The await here is for the chat_completion coroutine itself, which then yields an async generator
    async_gen = await llm.chat_completion(messages, stream=True)
    async for chunk in async_gen:
        chunks.append(chunk)

    assert len(chunks) == 2 
    assert chunks[0].content == "Hello"
    assert chunks[1].content == " world"
    mock_async_client_instance.stream.assert_called_once()


@pytest.mark.asyncio
async def test_openai_chat_llm_http_error(mocker):
    llm = OpenAIChatLLM(model_name="test-model", api_base_url="http://localhost:1111/v1", api_key="fake")
    
    error_response_content = '{"error": {"message": "Test API error", "type": "invalid_request_error"}}'
    # This lambda needs access to 'json' module
    def error_json_loader():
        import json # Import json inside lambda if it's not in global scope of test file
        return json.loads(error_response_content)

    http_error = httpx.HTTPStatusError(
        "Test Error", 
        request=MagicMock(spec=httpx.Request), 
        response=MagicMock(spec=httpx.Response, status_code=400, text=error_response_content, json=error_json_loader)
    )
    
    mock_async_client_instance = AsyncMock(spec=httpx.AsyncClient)
    mock_async_client_instance.post = AsyncMock(side_effect=http_error)
    mocker.patch.object(llm, '_get_client', AsyncMock(return_value=mock_async_client_instance))

    messages = [Message(role="user", content="Hi")]
    response_message = await llm.chat_completion(messages, max_retries=0)

    assert response_message.role == "assistant"
    # Now that json is imported in lambda, the detailed message should be parsed
    assert "LLM API Error: 400 - Test API error" in response_message.content

@pytest.mark.asyncio
async def test_openai_chat_llm_retry_logic(mocker):
    llm = OpenAIChatLLM(model_name="test-model", api_base_url="http://localhost:1111/v1", api_key="fake")
    
    connect_error = httpx.ConnectError("Connection failed", request=MagicMock())
    
    mock_response_json = {"choices": [{"message": {"role": "assistant", "content": "Success after retry"}}]}
    successful_response = MagicMock(status_code=200, json=lambda: mock_response_json, raise_for_status=lambda: None)

    mock_async_client_instance = AsyncMock(spec=httpx.AsyncClient)
    mock_async_client_instance.post = AsyncMock(side_effect=[connect_error, successful_response])
    mocker.patch.object(llm, '_get_client', AsyncMock(return_value=mock_async_client_instance))
    
    # Patch asyncio.sleep within the tframex.util.llms module where it's called
    mocker.patch('tframex.util.llms.asyncio.sleep', AsyncMock())

    messages = [Message(role="user", content="Hi")]
    response_message = await llm.chat_completion(messages, max_retries=1)

    assert response_message.content == "Success after retry"
    assert mock_async_client_instance.post.call_count == 2
    # Access the mock through the patched path
    tframex.util.llms.asyncio.sleep.assert_called_once()

