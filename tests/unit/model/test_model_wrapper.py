import pytest
from tframex.model import ModelWrapper

# --- Dummy Setup ---

class DummyResponse:
    def __init__(self, lines=None, status_code=200):
        self._lines = lines or []
        self.status_code = status_code
        self.headers = {}
        self.request = None

    async def __aenter__(self): return self
    async def __aexit__(self, *args): pass
    async def aread(self): return b"Internal error"
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
async def test_model_wrapper_stream_success():
    # Simulated streaming chunks from a VLLM-like model
    lines = [
        'data:{"choices":[{"delta":{"content":"streamed"}}]}',
        'data:{"choices":[{"delta":{"content":" output"}}]}',
        'data:[DONE]'
    ]
    dummy = DummyResponse(lines=lines)

    wrapper = ModelWrapper(
        provider="vllm",
        model_name="test",
        api_url="http://localhost",
        api_key="dummy"
    )
    wrapper.model._client = DummyClient(dummy)

    chunks = [chunk async for chunk in wrapper.call_stream([{"role": "user", "content": "Say something"}])]
    assert "".join(chunks).strip() == "streamed output"


@pytest.mark.asyncio
async def test_model_wrapper_stream_failure():
    # Simulate an API error (500)
    dummy = DummyResponse(status_code=500)

    wrapper = ModelWrapper(
        provider="vllm",
        model_name="test",
        api_url="http://localhost",
        api_key="dummy"
    )
    wrapper.model._client = DummyClient(dummy)

    chunks = [chunk async for chunk in wrapper.call_stream([{"role": "user", "content": "test"}])]
    assert any("ERROR" in chunk for chunk in chunks)


@pytest.mark.asyncio
async def test_model_wrapper_close_client():
    called = {"closed": False}

    class DummyCloseClient:
        async def aclose(self): called["closed"] = True

    wrapper = ModelWrapper(
        provider="vllm",
        model_name="test",
        api_url="http://localhost",
        api_key="dummy"
    )
    wrapper.model._client = DummyCloseClient()

    await wrapper.close_client()
    assert called["closed"] is True
