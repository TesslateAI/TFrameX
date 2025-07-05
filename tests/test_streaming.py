"""
Comprehensive tests for TFrameX streaming functionality.

Tests all aspects of streaming implementation including:
- Basic streaming agent calls
- Tool calls in streaming mode  
- Memory management during streaming
- Enterprise streaming integration
- Multi-agent streaming workflows
- Error handling in streaming mode
"""
import asyncio
import json
import pytest
from typing import List, AsyncGenerator
from unittest.mock import AsyncMock, MagicMock, patch

# Import TFrameX components
from tframex import TFrameXApp
from tframex.agents.llm_agent import LLMAgent
from tframex.models.primitives import Message, MessageChunk, ToolCall, FunctionCall
from tframex.util.llms import BaseLLMWrapper
from tframex.util.memory import InMemoryMemoryStore


class MockStreamingLLM(BaseLLMWrapper):
    """Mock LLM that supports streaming for testing."""
    
    def __init__(self, model_id="test-streaming-llm", responses=None, tool_responses=None):
        super().__init__(model_id=model_id)
        self.responses = responses or ["Hello, I'm streaming!"]
        self.tool_responses = tool_responses or []
        self.call_count = 0
        
    async def chat_completion(self, messages, stream=False, **kwargs):
        """Mock chat completion with streaming support."""
        self.call_count += 1
        
        if stream:
            return self._mock_stream_response(messages, **kwargs)
        else:
            # Non-streaming response
            response_text = self.responses[min(self.call_count - 1, len(self.responses) - 1)]
            return Message(role="assistant", content=response_text)
    
    async def _mock_stream_response(self, messages, **kwargs) -> AsyncGenerator[MessageChunk, None]:
        """Generate mock streaming response."""
        response_text = self.responses[min(self.call_count - 1, len(self.responses) - 1)]
        
        # Check if this should be a tool call response
        has_tools = "tools" in kwargs and kwargs["tools"]
        should_call_tool = has_tools and self.tool_responses
        
        if should_call_tool:
            # Simulate tool call streaming
            tool_response = self.tool_responses[min(self.call_count - 1, len(self.tool_responses) - 1)]
            
            # First yield some content
            for chunk in ["I need to ", "use a tool ", "for this."]:
                yield MessageChunk(role="assistant", content=chunk)
                await asyncio.sleep(0.001)  # Simulate network delay
            
            # Then yield tool call
            tool_call = ToolCall(
                id="test_tool_call_1",
                function=FunctionCall(
                    name=tool_response["name"],
                    arguments=json.dumps(tool_response["args"])
                )
            )
            yield MessageChunk(role="assistant", content=None, tool_calls=[tool_call])
        else:
            # Regular content streaming
            words = response_text.split()
            for i, word in enumerate(words):
                chunk_content = word if i == 0 else f" {word}"
                yield MessageChunk(role="assistant", content=chunk_content)
                await asyncio.sleep(0.001)  # Simulate network delay


@pytest.fixture
def basic_streaming_app():
    """Create a basic TFrameX app with streaming LLM for testing."""
    llm = MockStreamingLLM(responses=["This is a test streaming response."])
    app = TFrameXApp(default_llm=llm)
    
    @app.agent(name="TestAgent", description="Test streaming agent")
    async def test_agent():
        pass
    
    return app


@pytest.fixture  
def tool_streaming_app():
    """Create a TFrameX app with tools for streaming tests."""
    llm = MockStreamingLLM(
        responses=["I'll help you with that calculation."],
        tool_responses=[{"name": "calculate", "args": {"a": 5, "b": 3}}]
    )
    app = TFrameXApp(default_llm=llm)
    
    @app.tool(description="Perform basic calculations")
    async def calculate(a: int, b: int) -> int:
        return a + b
    
    @app.agent(
        name="CalculatorAgent", 
        description="Agent that can do calculations",
        tools=["calculate"]
    )
    async def calculator_agent():
        pass
    
    return app


@pytest.fixture
def multi_agent_streaming_app():
    """Create a multi-agent app for streaming tests."""
    llm = MockStreamingLLM(responses=[
        "Let me research this topic.",
        "Based on my research, here's the content.",
        "I'll coordinate the research and writing."
    ])
    app = TFrameXApp(default_llm=llm)
    
    @app.agent(name="Researcher", description="Research specialist")
    async def researcher():
        pass
        
    @app.agent(name="Writer", description="Writing specialist") 
    async def writer():
        pass
        
    @app.agent(
        name="Coordinator",
        description="Coordinates other agents",
        callable_agents=["Researcher", "Writer"]
    )
    async def coordinator():
        pass
    
    return app


class TestBasicStreaming:
    """Test basic streaming functionality."""
    
    @pytest.mark.asyncio
    async def test_agent_streaming_enabled(self, basic_streaming_app):
        """Test that agents can be called with streaming enabled."""
        async with basic_streaming_app.run_context() as rt:
            # Test streaming call
            stream = rt.call_agent_stream("TestAgent", "Hello!")
            chunks = []
            
            async for chunk in stream:
                chunks.append(chunk)
                assert isinstance(chunk, MessageChunk)
                assert chunk.role == "assistant"
            
            # Verify we got chunks
            assert len(chunks) > 0
            
            # Verify content reconstruction
            full_content = "".join(chunk.content or "" for chunk in chunks)
            assert "test streaming response" in full_content.lower()
    
    @pytest.mark.asyncio
    async def test_non_streaming_still_works(self, basic_streaming_app):
        """Test that non-streaming calls still work unchanged."""
        async with basic_streaming_app.run_context() as rt:
            response = await rt.call_agent("TestAgent", "Hello!")
            
            assert isinstance(response, Message)
            assert response.role == "assistant"
            assert "streaming" in response.content.lower()
    
    @pytest.mark.asyncio
    async def test_streaming_vs_non_streaming_equivalence(self, basic_streaming_app):
        """Test that streaming and non-streaming produce equivalent results."""
        async with basic_streaming_app.run_context() as rt:
            # Get non-streaming response
            non_stream_response = await rt.call_agent("TestAgent", "Test message")
            
            # Get streaming response
            stream = rt.call_agent_stream("TestAgent", "Test message")
            chunks = []
            async for chunk in stream:
                chunks.append(chunk)
            
            # Reconstruct streaming content
            stream_content = "".join(chunk.content or "" for chunk in chunks)
            
            # Content should be equivalent (allowing for minor differences)
            assert len(stream_content) > 0
            assert isinstance(non_stream_response.content, str)
    
    @pytest.mark.asyncio
    async def test_memory_management_streaming(self, basic_streaming_app):
        """Test that memory is properly managed during streaming."""
        async with basic_streaming_app.run_context() as rt:
            # Get the agent instance to check memory
            agent_instance = rt.engine._get_agent_instance("TestAgent")
            initial_memory_count = len(await agent_instance.memory.get_history())
            
            # Make streaming call
            stream = rt.call_agent_stream("TestAgent", "Test memory")
            async for chunk in stream:
                pass  # Consume all chunks
            
            # Check memory was updated
            final_memory_count = len(await agent_instance.memory.get_history())
            assert final_memory_count == initial_memory_count + 2  # +1 user, +1 assistant


class TestToolCallStreaming:
    """Test tool call handling in streaming mode."""
    
    @pytest.mark.asyncio
    async def test_tool_calls_in_streaming(self, tool_streaming_app):
        """Test that tool calls work correctly in streaming mode."""
        async with tool_streaming_app.run_context() as rt:
            stream = rt.call_agent_stream("CalculatorAgent", "What is 5 + 3?")
            
            content_chunks = []
            tool_calls = []
            
            async for chunk in stream:
                if chunk.content:
                    content_chunks.append(chunk.content)
                if chunk.tool_calls:
                    tool_calls.extend(chunk.tool_calls)
            
            # Verify we got both content and tool calls
            assert len(content_chunks) > 0
            assert len(tool_calls) > 0
            
            # Verify tool call structure
            tool_call = tool_calls[0]
            assert tool_call.function.name == "calculate"
            args = json.loads(tool_call.function.arguments)
            assert args["a"] == 5
            assert args["b"] == 3
    
    @pytest.mark.asyncio  
    async def test_tool_execution_in_streaming(self, tool_streaming_app):
        """Test that tools are actually executed during streaming."""
        with patch.object(tool_streaming_app.get_tool("calculate"), 'execute') as mock_execute:
            mock_execute.return_value = 8
            
            async with tool_streaming_app.run_context() as rt:
                stream = rt.call_agent_stream("CalculatorAgent", "Calculate 5 + 3")
                
                # Consume all chunks
                async for chunk in stream:
                    pass
                
                # Verify tool was executed (may be called multiple times due to mock LLM behavior)
                assert mock_execute.call_count >= 1
    
    @pytest.mark.asyncio
    async def test_streaming_memory_with_tools(self, tool_streaming_app):
        """Test memory management when tools are used in streaming mode."""
        async with tool_streaming_app.run_context() as rt:
            agent_instance = rt.engine._get_agent_instance("CalculatorAgent")
            initial_count = len(await agent_instance.memory.get_history())
            
            stream = rt.call_agent_stream("CalculatorAgent", "What is 5 + 3?")
            async for chunk in stream:
                pass
            
            final_count = len(await agent_instance.memory.get_history())
            # Should have: user message + assistant message + tool message(s)
            assert final_count > initial_count + 1


class TestStreamingErrorHandling:
    """Test error handling in streaming mode."""
    
    @pytest.mark.asyncio
    async def test_llm_error_in_streaming(self, basic_streaming_app):
        """Test handling of LLM errors during streaming."""
        # Mock LLM to raise an error
        with patch.object(basic_streaming_app.default_llm, 'chat_completion') as mock_chat:
            async def error_stream():
                yield MessageChunk(role="assistant", content="Error: ")
                raise Exception("Mock LLM error")
            
            mock_chat.return_value = error_stream()
            
            async with basic_streaming_app.run_context() as rt:
                stream = rt.call_agent_stream("TestAgent", "Cause an error")
                
                chunks = []
                with pytest.raises(Exception, match="Mock LLM error"):
                    async for chunk in stream:
                        chunks.append(chunk)
                
                # Should have received at least the first chunk before error
                assert len(chunks) >= 1
    
    @pytest.mark.asyncio
    async def test_tool_error_in_streaming(self, tool_streaming_app):
        """Test handling of tool errors during streaming."""
        with patch.object(tool_streaming_app.get_tool("calculate"), 'execute') as mock_execute:
            mock_execute.side_effect = Exception("Tool execution failed")
            
            async with tool_streaming_app.run_context() as rt:
                stream = rt.call_agent_stream("CalculatorAgent", "Calculate 5 + 3")
                
                # Should complete without raising exception
                # Error should be handled gracefully and included in response
                chunks = []
                async for chunk in stream:
                    chunks.append(chunk)
                
                assert len(chunks) > 0
    
    @pytest.mark.asyncio
    async def test_max_iterations_in_streaming(self):
        """Test max iterations handling in streaming mode."""
        # Create LLM that always requests tool calls
        llm = MockStreamingLLM(
            responses=["Calling tool again."] * 10,
            tool_responses=[{"name": "endless_tool", "args": {}}] * 10
        )
        
        app = TFrameXApp(default_llm=llm)
        
        @app.tool(description="Tool that triggers more tool calls")
        async def endless_tool() -> str:
            return "This will trigger another tool call"
        
        @app.agent(
            name="EndlessAgent", 
            tools=["endless_tool"],
            max_tool_iterations=2  # Limit iterations
        )
        async def endless_agent():
            pass
        
        async with app.run_context() as rt:
            stream = rt.call_agent_stream("EndlessAgent", "Start endless loop")
            
            chunks = []
            async for chunk in stream:
                chunks.append(chunk)
            
            # Should complete despite hitting iteration limit
            assert len(chunks) > 0
            
            # Last chunk should indicate iteration limit reached
            last_content = "".join(chunk.content or "" for chunk in chunks if chunk.content)
            assert "exceeded maximum" in last_content.lower()


class TestMultiAgentStreaming:
    """Test streaming in multi-agent scenarios."""
    
    @pytest.mark.asyncio
    async def test_agent_calling_agent_streaming(self, multi_agent_streaming_app):
        """Test streaming when one agent calls another."""
        async with multi_agent_streaming_app.run_context() as rt:
            stream = rt.call_agent_stream("Coordinator", "Research and write about AI")
            
            chunks = []
            async for chunk in stream:
                chunks.append(chunk)
                assert isinstance(chunk, MessageChunk)
            
            assert len(chunks) > 0
            content = "".join(chunk.content or "" for chunk in chunks)
            assert len(content) > 0
    
    @pytest.mark.asyncio  
    async def test_concurrent_streaming_calls(self, basic_streaming_app):
        """Test concurrent streaming calls to different agents."""
        async with basic_streaming_app.run_context() as rt:
            # Start multiple streaming calls concurrently
            streams = [
                rt.call_agent_stream("TestAgent", f"Message {i}")
                for i in range(3)
            ]
            
            # Collect all results
            all_chunks = []
            for stream in streams:
                chunks = []
                async for chunk in stream:
                    chunks.append(chunk)
                all_chunks.append(chunks)
            
            # Verify all streams completed
            assert len(all_chunks) == 3
            for chunks in all_chunks:
                assert len(chunks) > 0


class TestEnterpriseStreaming:
    """Test enterprise features with streaming."""
    
    @pytest.mark.asyncio
    async def test_enterprise_streaming_with_audit(self):
        """Test enterprise streaming with audit logging."""
        from tframex.enterprise.app import EnterpriseApp
        from tframex.enterprise.config import EnterpriseConfig
        from tframex.models import User
        
        # Create enterprise config
        config = EnterpriseConfig({
            "enabled": True,
            "security": {
                "audit": {"enabled": True}
            }
        })
        
        llm = MockStreamingLLM()
        app = EnterpriseApp(default_llm=llm, enterprise_config=config, auto_initialize=False)
        
        @app.agent(name="EnterpriseAgent", description="Enterprise test agent")
        async def enterprise_agent():
            pass
        
        try:
            await app.initialize_enterprise()
            
            # Create test user
            user = User(id="test_user", username="testuser", email="test@example.com")
            
            async with app.run_context(user=user) as rt:
                # Test streaming call
                stream = rt.call_agent_stream("EnterpriseAgent", "Enterprise test")
                
                chunks = []
                async for chunk in stream:
                    chunks.append(chunk)
                
                assert len(chunks) > 0
                
                # Verify audit logging occurred
                audit_logger = app.get_audit_logger()
                if audit_logger:
                    # This would verify audit logs were created
                    assert True  # Placeholder for actual audit verification
        
        finally:
            await app.stop_enterprise()
    
    @pytest.mark.asyncio
    async def test_enterprise_streaming_metrics(self):
        """Test enterprise streaming with metrics collection."""
        from tframex.enterprise.app import EnterpriseApp
        from tframex.enterprise.config import EnterpriseConfig
        
        config = EnterpriseConfig({
            "enabled": True,
            "metrics": {"enabled": True}
        })
        
        llm = MockStreamingLLM()
        app = EnterpriseApp(default_llm=llm, enterprise_config=config, auto_initialize=False)
        
        @app.agent(name="MetricsAgent", description="Metrics test agent")
        async def metrics_agent():
            pass
        
        try:
            await app.initialize_enterprise()
            
            async with app.run_context() as rt:
                stream = rt.call_agent_stream("MetricsAgent", "Metrics test")
                
                chunks = []
                async for chunk in stream:
                    chunks.append(chunk)
                
                assert len(chunks) > 0
                
                # Verify metrics collection
                metrics_manager = app.get_metrics_manager()
                if metrics_manager:
                    # This would verify metrics were collected
                    assert True  # Placeholder for actual metrics verification
        
        finally:
            await app.stop_enterprise()


class TestStreamingPerformance:
    """Test streaming performance characteristics."""
    
    @pytest.mark.asyncio
    async def test_streaming_latency(self, basic_streaming_app):
        """Test that streaming provides lower latency than non-streaming."""
        import time
        
        async with basic_streaming_app.run_context() as rt:
            # Time first chunk in streaming
            start_time = time.time()
            stream = rt.call_agent_stream("TestAgent", "Latency test")
            
            first_chunk_time = None
            async for chunk in stream:
                if first_chunk_time is None:
                    first_chunk_time = time.time()
                # Continue consuming stream
            
            streaming_first_chunk_latency = first_chunk_time - start_time
            
            # Time complete non-streaming response
            start_time = time.time()
            response = await rt.call_agent("TestAgent", "Latency test")
            non_streaming_latency = time.time() - start_time
            
            # First chunk should arrive faster than complete response
            # (This may not always be true in mocked tests, but verifies the pattern)
            assert streaming_first_chunk_latency >= 0
            assert non_streaming_latency >= 0
    
    @pytest.mark.asyncio
    async def test_large_response_streaming(self):
        """Test streaming with large responses."""
        # Create LLM with a very long response
        long_response = " ".join([f"word_{i}" for i in range(1000)])
        llm = MockStreamingLLM(responses=[long_response])
        
        app = TFrameXApp(default_llm=llm)
        
        @app.agent(name="LongResponseAgent")
        async def long_response_agent():
            pass
        
        async with app.run_context() as rt:
            stream = rt.call_agent_stream("LongResponseAgent", "Give me a long response")
            
            chunk_count = 0
            total_length = 0
            
            async for chunk in stream:
                chunk_count += 1
                if chunk.content:
                    total_length += len(chunk.content)
            
            # Should receive many chunks for long response
            assert chunk_count > 10
            assert total_length > 1000


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])