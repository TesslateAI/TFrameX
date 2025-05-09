import pytest
import os
from tframex.model import ModelWrapper
from dotenv import load_dotenv

load_dotenv()

@pytest.mark.asyncio
async def test_vllm_model_real_response():
    api_key = os.getenv("API_KEY")
    api_url = os.getenv("API_URL")
    model_name = os.getenv("MODEL_NAME")

    assert api_key and api_url and model_name, "API_URL, API_KEY, and MODEL_NAME must be set."

    model = ModelWrapper(
        provider="vllm",
        model_name=model_name,
        api_url=api_url,
        api_key=api_key
    )

    messages = [{"role": "user", "content": "Say hello in Spanish"}]
    response = [chunk async for chunk in model.call_stream(messages)]

    full_response = "".join(response).lower()
    print("API_URL =", os.getenv("API_URL"))
    assert "hola" in full_response
    await model.close_client()
