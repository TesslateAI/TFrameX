
import pytest
import pytest_asyncio
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from tframex import (
    TFrameXApp,
    OpenAIChatLLM,
    InMemoryMemoryStore,
    Message,
    Tool,
    ToolDefinition,
    ToolParameters,
    ToolParameterProperty,
    FunctionCall,
    ToolCall,
)

# --- Mock LLM Fixture ---
@pytest.fixture
def mock_openai_chat_llm():
    llm = MagicMock(spec=OpenAIChatLLM)
    llm.model_id = "mock-gpt-3.5-turbo"
    llm.api_base_url = "mock_url"
    llm.api_key = "mock_key"

    # Set a default return_value. Tests can override this.
    llm.chat_completion = AsyncMock(return_value=Message(role="assistant", content="Default mock LLM response."))
    
    llm._get_client = AsyncMock(return_value=AsyncMock())
    llm.close = AsyncMock()
    return llm

@pytest.fixture
def mock_llm_with_tool_call():
    llm = MagicMock(spec=OpenAIChatLLM)
    llm.model_id = "mock-tool-caller-llm"
    llm.api_base_url = "mock_url"
    llm.api_key = "mock_key"

    async def chat_completion_with_tool(messages, stream=False, **kwargs):
        # Corrected arguments for dummy_tool_func
        tool_call = ToolCall(
            id="tool_call_123",
            type="function",
            function=FunctionCall(name="test_tool", arguments='{"text": "value", "number": 1}'), # Corrected args
        )
        return Message(role="assistant", content=None, tool_calls=[tool_call])

    llm.chat_completion = AsyncMock(side_effect=chat_completion_with_tool)
    llm._get_client = AsyncMock(return_value=AsyncMock())
    llm.close = AsyncMock()
    return llm


# --- TFrameXApp Fixture ---
@pytest.fixture
def tframex_app(mock_openai_chat_llm):
    app = TFrameXApp(default_llm=mock_openai_chat_llm)
    return app

@pytest.fixture
def tframex_app_no_default_llm():
    with patch.dict('os.environ', {'TFRAMEX_ALLOW_NO_DEFAULT_LLM': 'True'}):
        app = TFrameXApp(default_llm=None)
    return app


# --- Dummy Tool Fixture ---
@pytest.fixture
def dummy_tool_func():
    async def _dummy_tool_func(text: str, number: int = 0): # Matches arguments in mock_llm_with_tool_call
        return f"Tool processed: {text}, {number}"
    return _dummy_tool_func

@pytest.fixture
def dummy_tool(dummy_tool_func, tframex_app):
    tool_name = "test_tool" # Ensure this name matches what mock_llm_with_tool_call uses
    description = "A dummy tool for testing."
    
    params_schema = ToolParameters(
        properties={
            "text": ToolParameterProperty(type="string", description="Text to process"),
            "number": ToolParameterProperty(type="integer", description="A number", enum=[0, 1, 2]) # Added enum for variety
        },
        required=["text"] # number has a default
    )
    
    tool = Tool(
        name=tool_name,
        func=dummy_tool_func,
        description=description,
        parameters_schema=params_schema
    )
    tframex_app._tools[tool_name] = tool
    return tool

# --- Dummy Agent Registration Fixture ---
@pytest_asyncio.fixture
async def register_dummy_agents(tframex_app, dummy_tool): # dummy_tool ensures tool is registered
    @tframex_app.agent(name="EchoAgent", system_prompt="Echo: {user_input}")
    async def echo_agent_placeholder(): pass
    
    # ToolUserAgent uses "test_tool", which is registered by dummy_tool fixture
    @tframex_app.agent(name="ToolUserAgent", tools=["test_tool"], system_prompt="Use test_tool")
    async def tool_user_agent_placeholder(): pass

    return tframex_app

# --- Runtime Context Fixture ---
@pytest_asyncio.fixture
async def runtime_context(tframex_app):
    async with tframex_app.run_context() as rt_ctx:
        yield rt_ctx

