from tframex.model import ModelWrapper
import pytest

# --- Dummy OpenAI-style client + stream ---

class DummyOpenAIChunk:
    def __init__(self, content):
        self.choices = [type("Choice", (), {"delta": type("Delta", (), {"content": content})()})]

class DummyOpenAIStream:
    def __init__(self, chunks): self._chunks = chunks
    def __aiter__(self):
        async def gen():
            for c in self._chunks:
                yield DummyOpenAIChunk(c)
        return gen()


class DummyOpenAIClient:
    def __init__(self, stream):
        self.chat = type("Chat", (), {})()
        self.chat.completions = type("Completions", (), {})()

        async def create(*_args, **_kwargs):
            return stream

        self.chat.completions.create = create


@pytest.mark.asyncio
async def test_model_wrapper_openai_stream():
    # Prepare dummy OpenAI-like streamed chunks
    dummy_stream = DummyOpenAIStream(["hello", " world"])

    wrapper = ModelWrapper(
        provider="openai",
        model_name="gpt-3.5-turbo",
        api_key="dummy-key"
    )

    # Inject dummy OpenAI client
    wrapper.model.client = DummyOpenAIClient(dummy_stream)

    chunks = [chunk async for chunk in wrapper.call_stream([{"role": "user", "content": "hi"}])]
    assert "".join(chunks) == "hello world"
