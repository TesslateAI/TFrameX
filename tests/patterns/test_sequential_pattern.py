
import pytest
from unittest.mock import AsyncMock, MagicMock, call

from tframex import (
    SequentialPattern,
    Message,
    FlowContext,
    TFrameXApp, 
    Engine,
    TFrameXRuntimeContext
)

@pytest.mark.asyncio
async def test_sequential_pattern_with_mock_agents(runtime_context):
    engine = runtime_context.engine
    
    mock_agent1_response = Message(role="assistant", content="Output from Agent1")
    mock_agent2_response = Message(role="assistant", content="Output from Agent2 based on Agent1")

    async def mock_call_agent_side_effect(agent_name, input_message, **kwargs):
        if agent_name == "Agent1":
            assert input_message.content == "Initial input"
            return mock_agent1_response
        elif agent_name == "Agent2":
            assert input_message.content == "Output from Agent1"
            return mock_agent2_response
        raise ValueError(f"Unexpected agent called: {agent_name}")

    engine.call_agent = AsyncMock(side_effect=mock_call_agent_side_effect)
    engine.reset_agent = AsyncMock()

    pattern = SequentialPattern(pattern_name="TestSequence", steps=["Agent1", "Agent2"])
    
    initial_message = Message(role="user", content="Initial input")
    flow_ctx = FlowContext(initial_input=initial_message)
    
    final_flow_ctx = await pattern.execute(flow_ctx, engine)
    
    assert final_flow_ctx.current_message.content == "Output from Agent2 based on Agent1"
    assert engine.call_agent.call_count == 2
    
    calls = engine.call_agent.call_args_list
    assert calls[0][0][0] == "Agent1" 
    assert calls[0][0][1].content == "Initial input" 
    
    assert calls[1][0][0] == "Agent2"
    assert calls[1][0][1].content == "Output from Agent1"

    await pattern.reset_agents(engine)
    assert engine.reset_agent.call_count == 2
    engine.reset_agent.assert_any_call("Agent1")
    engine.reset_agent.assert_any_call("Agent2")


@pytest.mark.asyncio
async def test_sequential_pattern_with_nested_pattern(runtime_context):
    engine = runtime_context.engine
    
    mock_agentA_response = Message(role="assistant", content="Output A")
    mock_agentB_response = Message(role="assistant", content="Output B")
    mock_agentC_response = Message(role="assistant", content="Output C from AgentC based on B")

    async def mock_call_agent_side_effect(agent_name, input_message, **kwargs):
        if agent_name == "AgentA": 
            assert input_message.content == "Start main sequence"
            return mock_agentA_response
        if agent_name == "AgentB": 
            assert input_message.content == "Output A" # Input from AgentA
            return mock_agentB_response
        if agent_name == "AgentC":
            assert input_message.content == "Output B" # Input from AgentB
            return mock_agentC_response
        raise ValueError(f"Unexpected agent: {agent_name}")

    engine.call_agent = AsyncMock(side_effect=mock_call_agent_side_effect)
    engine.reset_agent = AsyncMock()

    nested_sequential = SequentialPattern(pattern_name="NestedSeq", steps=["AgentB", "AgentC"])
    main_sequential = SequentialPattern(pattern_name="MainSeq", steps=["AgentA", nested_sequential])

    initial_message = Message(role="user", content="Start main sequence")
    flow_ctx = FlowContext(initial_input=initial_message)

    final_flow_ctx = await main_sequential.execute(flow_ctx, engine)

    assert final_flow_ctx.current_message.content == "Output C from AgentC based on B"
    assert engine.call_agent.call_count == 3 

    await main_sequential.reset_agents(engine)
    assert engine.reset_agent.call_count == 3 
    engine.reset_agent.assert_any_call("AgentA")
    engine.reset_agent.assert_any_call("AgentB")
    engine.reset_agent.assert_any_call("AgentC")


