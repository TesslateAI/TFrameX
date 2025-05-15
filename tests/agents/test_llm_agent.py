
import pytest
from unittest.mock import AsyncMock, MagicMock, call

from tframex import (
    LLMAgent,
    OpenAIChatLLM,
    Message,
    ToolCall,
    FunctionCall,
    Tool,
    ToolDefinition,
    ToolParameters,
    ToolParameterProperty,
    TFrameXApp, 
    Engine,
    TFrameXRuntimeContext 
)

@pytest.mark.asyncio
async def test_llm_agent_initialization(mock_openai_chat_llm, runtime_context):
    agent = LLMAgent(
        agent_id="test_agent_1_ctx123", # Make agent_id more specific if needed
        llm=mock_openai_chat_llm,
        engine=runtime_context.engine,
        system_prompt_template="You are a {role}.",
        strip_think_tags=True
    )
    assert agent.agent_id.startswith("test_agent_1") # Check prefix if full ID is dynamic
    assert agent.llm == mock_openai_chat_llm
    assert agent.strip_think_tags is True
    rendered_prompt = agent._render_system_prompt(role="tester")
    assert rendered_prompt.content == "You are a tester."

@pytest.mark.asyncio
async def test_llm_agent_run_simple_response(mock_openai_chat_llm, runtime_context):
    # Override the default return_value for this specific test
    mock_openai_chat_llm.chat_completion.return_value = Message(role="assistant", content="Hello from mock LLM for simple response")
    
    agent = LLMAgent("test_agent_run", mock_openai_chat_llm, runtime_context.engine)
    
    response = await agent.run("Hi there")
    
    assert response.role == "assistant"
    assert response.content == "Hello from mock LLM for simple response"
    mock_openai_chat_llm.chat_completion.assert_called_once()
    history = await agent.memory.get_history()
    assert len(history) == 2 
    assert history[0].content == "Hi there"
    assert history[1].content == "Hello from mock LLM for simple response"

@pytest.mark.asyncio
async def test_llm_agent_run_with_tool_call_and_execution(
    mock_llm_with_tool_call, 
    dummy_tool, # Use the dummy_tool fixture which also registers it
    runtime_context # Contains the app and engine
):
    # dummy_tool fixture ensures "test_tool" is registered in runtime_context._app

    # Expected final response after tool execution
    # The dummy_tool_func with args text="value", number=1 will return "Tool processed: value, 1"
    final_text_from_llm_after_tool = "OK, tool said: Tool processed: value, 1"
    final_response_msg = Message(role="assistant", content=final_text_from_llm_after_tool)
    
    # mock_llm_with_tool_call is already configured to return a tool call with:
    # arguments='{"text": "value", "number": 1}' for "test_tool"
    
    # Set up the side_effect for chat_completion on the mock_llm_with_tool_call
    # First call: returns the predefined tool call (from fixture setup)
    # Second call: returns the final_response_msg
    mock_llm_with_tool_call.chat_completion.side_effect = [
        # This is the first response, triggering the tool.
        # The fixture mock_llm_with_tool_call is already set to return this by default.
        # We can re-assert its default behavior or rely on it.
        # For clarity, let's redefine its first return if needed, or ensure fixture does it.
        # The fixture currently sets side_effect directly. So, the first element of our list here
        # will be its first response.
        Message(role="assistant", content=None, 
                tool_calls=[ToolCall(id="tool_call_123", type="function", 
                                     function=FunctionCall(name="test_tool", 
                                                           arguments='{"text": "value", "number": 1}'))]),
        final_response_msg 
    ]

    agent = LLMAgent(
        agent_id="tool_caller_agent_ctx123",
        llm=mock_llm_with_tool_call, 
        engine=runtime_context.engine,
        tools=[dummy_tool], # Pass the actual tool instance
        system_prompt_template="Use tools if needed."
    )

    user_message_content = "Use the test tool with text 'value' and number 1."
    response = await agent.run(user_message_content)

    assert response.role == "assistant"
    assert response.content == final_text_from_llm_after_tool # Check final textual response
    assert mock_llm_with_tool_call.chat_completion.call_count == 2
    
    # Check messages passed to LLM on second call (after tool result)
    second_call_args = mock_llm_with_tool_call.chat_completion.call_args_list[1]
    messages_to_llm2 = second_call_args.args[0]
    
    # The tool message content should be the output of dummy_tool_func
    expected_tool_result_content = "Tool processed: value, 1"
    assert any(
        msg.role == "tool" and 
        msg.tool_call_id == "tool_call_123" and 
        msg.name == "test_tool" and # Tool name should be in the tool message
        expected_tool_result_content in str(msg.content) # Check tool output
        for msg in messages_to_llm2
    ), f"Tool result message not found or incorrect in LLM history. Messages: {messages_to_llm2}"


@pytest.mark.asyncio
async def test_llm_agent_strip_think_tags(mock_openai_chat_llm, runtime_context):
    # Explicitly set the return value for this test case on the shared mock
    mock_openai_chat_llm.chat_completion.return_value = Message(role="assistant", content="<think>I am thinking.</think>This is the real response.")

    agent_strip = LLMAgent(
        "think_stripper_ctx123", 
        mock_openai_chat_llm, 
        runtime_context.engine, 
        strip_think_tags=True
    )
    response_strip = await agent_strip.run("Tell me something.")
    assert response_strip.content == "This is the real response."

    # Reset mock call count for the next agent using the same mock LLM instance
    mock_openai_chat_llm.chat_completion.reset_mock() 
    # Set a different return value for the agent that doesn't strip
    mock_openai_chat_llm.chat_completion.return_value = Message(role="assistant", content="<think>I am thinking again.</think>This is another real response.")
    
    agent_no_strip = LLMAgent(
        "no_think_strip_ctx123", 
        mock_openai_chat_llm, 
        runtime_context.engine, 
        strip_think_tags=False
    )
    response_no_strip = await agent_no_strip.run("Tell me something else.")
    assert response_no_strip.content == "<think>I am thinking again.</think>This is another real response."
    # Ensure chat_completion was called for the second agent
    mock_openai_chat_llm.chat_completion.assert_called_once() 

