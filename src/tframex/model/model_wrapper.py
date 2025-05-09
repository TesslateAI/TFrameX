from .base import BaseModel
from .vllm_model import VLLMModel
from .openai_model import OpenAIModel 

class ModelWrapper(BaseModel):
    def __init__(self, provider: str, **kwargs):
        if provider == "vllm":
            self.model = VLLMModel(**kwargs)
        elif provider == "openai": 
            self.model = OpenAIModel(**kwargs)
        else:
            raise ValueError(f"Unsupported provider: {provider}")

        super().__init__(model_id=self.model.model_id)

    async def call_stream(self, messages, **kwargs):
        async for chunk in self.model.call_stream(messages, **kwargs):
            yield chunk

    async def close_client(self):
        await self.model.close_client()
