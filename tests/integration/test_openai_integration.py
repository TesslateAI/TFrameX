import pytest
import os
from tframex.model import ModelWrapper
from dotenv import load_dotenv

# Load variables from .env file
load_dotenv()

@pytest.mark.asyncio
async def test_openai_model_real_response(capfd):
    api_key = os.getenv("OPENAI_API_KEY")
    model_name = os.getenv("OPENAI_MODEL_NAME", "gpt-3.5-turbo")

    assert api_key, "OPENAI_API_KEY must be set in .env to run this test."

    model = ModelWrapper(
        provider="openai",
        model_name=model_name,
        api_key=api_key
    )

    messages = [{"role": "user", "content": "What is the capital of France?"}]
    response = [chunk async for chunk in model.call_stream(messages)]

    full_response = "".join(response)
    print("RESPONSE:", full_response, flush=True)

    await model.close_client()

    # Capture and display output
    out, _ = capfd.readouterr()
    assert "Paris" in full_response, f"Expected 'Paris' in response. Got:\n{out}"
