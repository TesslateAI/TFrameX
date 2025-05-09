import pytest
import json
from tframex.model import ModelWrapper

# --- Helpers ---

class DummyResponse:
    def __init__(self, status_code, lines=None, headers=None, error_content=b""):
        self.status_code = status_code
        self._lines = lines or []
        self.headers = headers or {}
        self._error_content = error_content
        self.request = None

    async def __aenter__(self): return self
    async def __aexit__(self, *args): pass
    async def aread(self): return self._error_content
    def aiter_lines(self):
        async def gen():
            for line in self._lines:
                yield line
        return gen()


class DummyClient:
    def __init__(self, response): self._response = response
    def stream(self, *args, **kwargs): return self._response


# --- Tests ---

@pytest.mark.asyncio
async def test_call_stream_success_with_wrapper():
    lines = [
        'data:' + json.dumps({"choices": [{"delta": {"content": "hello"}}]}),
        'data:[DONE]'
    ]
    dummy_response = DummyResponse(status_code=200, lines=lines)
    
    # Wrap a VLLMModel via the wrapper
    wrapper = ModelWrapper(
        provider="vllm",
        model_name="test-model",
        api_url="API_URL",
        api_key="API_KEY"
    )
    wrapper.model._client = DummyClient(dummy_response)

    chunks = [chunk async for chunk in wrapper.call_stream([{"role": "user", "content": "ping"}])]
    assert chunks == ["hello"]


@pytest.mark.asyncio
async def test_call_stream_api_error_with_wrapper():
    dummy_response = DummyResponse(status_code=500, error_content=b"something went wrong")

    wrapper = ModelWrapper(
        provider="vllm",
        model_name="test-model",
        api_url="API_URL",
        api_key="API_KEY"
    )
    wrapper.model._client = DummyClient(dummy_response)

    chunks = [chunk async for chunk in wrapper.call_stream([{"role": "user", "content": "ping"}])]
    assert len(chunks) == 1
    assert "ERROR" in chunks[0]
    assert "500" in chunks[0]
    assert "something went wrong" in chunks[0]


@pytest.mark.asyncio
async def test_close_client_with_wrapper():
    wrapper = ModelWrapper(
        provider="vllm",
        model_name="test-model",
        api_url="API_URL",
        api_key="API_KEY"
    )

    closed = {"done": False}
    class DummyCloseClient:
        async def aclose(self): closed["done"] = True

    wrapper.model._client = DummyCloseClient()
    await wrapper.close_client()
    assert closed["done"] is True
