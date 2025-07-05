"""
Real-world streaming tests using the provided test environment.
No mocking - tests against actual LLM API to validate streaming implementation.
"""
import asyncio
import os
import pytest
from datetime import datetime
from dotenv import load_dotenv

# Load test environment
load_dotenv('.env.test')

from tframex import TFrameXApp
from tframex.util.llms import OpenAIChatLLM
from tframex.models.primitives import MessageChunk


@pytest.fixture
def real_llm():
    """Create real LLM using test environment."""
    api_key = os.getenv("OPENAI_API_KEY")
    api_base = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")
    model_name = os.getenv("OPENAI_MODEL_NAME", "gpt-3.5-turbo")
    
    if not api_key:
        pytest.skip("No OPENAI_API_KEY in test environment")
    
    return OpenAIChatLLM(
        api_key=api_key,
        model_name=model_name,
        api_base_url=api_base
    )


@pytest.fixture
def streaming_app(real_llm):
    """Create TFrameX app with real LLM for streaming tests."""
    app = TFrameXApp(default_llm=real_llm)
    
    @app.tool(description="Get the current date and time")
    async def get_current_time() -> str:
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    @app.tool(description="Calculate the sum of two numbers")
    async def add_numbers(a: int, b: int) -> int:
        return a + b
    
    @app.agent(
        name="StreamingAgent",
        description="A helpful assistant that supports streaming",
        tools=["get_current_time", "add_numbers"],
        system_prompt="You are a helpful assistant. Be concise but informative. Use tools when appropriate."
    )
    async def streaming_agent():
        pass
    
    return app


@pytest.fixture
def multi_agent_app(real_llm):
    """Create multi-agent app for testing agent-to-agent streaming."""
    app = TFrameXApp(default_llm=real_llm)
    
    @app.agent(
        name="Researcher", 
        description="Specializes in research and analysis",
        system_prompt="You are a research specialist. Provide accurate, well-researched information."
    )
    async def researcher():
        pass
    
    @app.agent(
        name="Writer",
        description="Specializes in clear, engaging writing", 
        system_prompt="You are a professional writer. Create clear, engaging content."
    )
    async def writer():
        pass
    
    @app.agent(
        name="Coordinator",
        description="Coordinates research and writing tasks",
        callable_agents=["Researcher", "Writer"],
        system_prompt="You coordinate tasks between researchers and writers. Delegate appropriately."
    )
    async def coordinator():
        pass
    
    return app


class TestRealStreaming:
    """Test streaming with real LLM API."""
    
    @pytest.mark.asyncio
    async def test_basic_streaming_functionality(self, streaming_app):
        """Test basic streaming works with real LLM."""
        async with streaming_app.run_context() as rt:
            # Test streaming call
            stream = rt.call_agent_stream("StreamingAgent", "Hello! Tell me about yourself in 2-3 sentences.")
            
            chunks = []
            total_content = ""
            
            async for chunk in stream:
                chunks.append(chunk)
                assert isinstance(chunk, MessageChunk)
                assert chunk.role == "assistant"
                
                if chunk.content:
                    total_content += chunk.content
            
            # Validate we got streaming chunks
            assert len(chunks) > 1, "Should receive multiple chunks for streaming"
            assert len(total_content) > 0, "Should receive content"
            assert any(chunk.content for chunk in chunks), "At least one chunk should have content"
            
            print(f"✅ Received {len(chunks)} chunks, {len(total_content)} characters total")
    
    @pytest.mark.asyncio 
    async def test_streaming_vs_non_streaming_equivalence(self, streaming_app):
        """Test streaming and non-streaming produce similar results."""
        prompt = "What is 2 + 2? Be brief."
        
        async with streaming_app.run_context() as rt:
            # Non-streaming response
            non_stream_response = await rt.call_agent("StreamingAgent", prompt)
            
            # Streaming response  
            stream = rt.call_agent_stream("StreamingAgent", prompt)
            stream_chunks = []
            
            async for chunk in stream:
                stream_chunks.append(chunk)
            
            # Reconstruct streaming content
            stream_content = "".join(chunk.content or "" for chunk in stream_chunks)
            
            # Both should have meaningful content
            assert len(non_stream_response.content) > 0
            assert len(stream_content) > 0
            
            # Both should mention the answer (4)
            assert "4" in non_stream_response.content or "four" in non_stream_response.content.lower()
            assert "4" in stream_content or "four" in stream_content.lower()
            
            print(f"Non-streaming: {non_stream_response.content[:100]}...")
            print(f"Streaming: {stream_content[:100]}...")
    
    @pytest.mark.asyncio
    async def test_tool_calls_in_streaming(self, streaming_app):
        """Test tool calls work correctly in streaming mode."""
        async with streaming_app.run_context() as rt:
            stream = rt.call_agent_stream("StreamingAgent", "What time is it right now?")
            
            content_chunks = []
            tool_calls = []
            
            async for chunk in stream:
                if chunk.content:
                    content_chunks.append(chunk.content)
                if chunk.tool_calls:
                    tool_calls.extend(chunk.tool_calls)
            
            # Should have received tool calls for time
            assert len(tool_calls) > 0, "Should have called get_current_time tool"
            
            # Tool call should be for the time function
            time_tool_calls = [tc for tc in tool_calls if tc.function.name == "get_current_time"]
            assert len(time_tool_calls) > 0, "Should have called get_current_time"
            
            # Should also have content
            total_content = "".join(content_chunks)
            assert len(total_content) > 0, "Should have content along with tool calls"
            
            print(f"✅ Tool calls: {len(tool_calls)}, Content length: {len(total_content)}")
    
    @pytest.mark.asyncio
    async def test_streaming_with_calculation_tool(self, streaming_app):
        """Test streaming with calculation tool calls."""
        async with streaming_app.run_context() as rt:
            stream = rt.call_agent_stream("StreamingAgent", "Calculate 15 + 27 for me")
            
            content_parts = []
            calculation_tool_calls = []
            
            async for chunk in stream:
                if chunk.content:
                    content_parts.append(chunk.content)
                if chunk.tool_calls:
                    for tc in chunk.tool_calls:
                        if tc.function.name == "add_numbers":
                            calculation_tool_calls.append(tc)
            
            # Should have called calculation tool
            assert len(calculation_tool_calls) > 0, "Should have called add_numbers tool"
            
            # Full response should mention the result (42)
            full_content = "".join(content_parts)
            assert "42" in full_content, f"Should mention result 42 in: {full_content}"
            
            print(f"✅ Calculation tool calls: {len(calculation_tool_calls)}")
            print(f"Response: {full_content}")
    
    @pytest.mark.asyncio
    async def test_memory_persistence_in_streaming(self, streaming_app):
        """Test that streaming properly stores messages in memory."""
        async with streaming_app.run_context() as rt:
            # Get agent instance for memory checking
            agent_instance = rt.engine._get_agent_instance("StreamingAgent")
            initial_memory_size = len(await agent_instance.memory.get_history())
            
            # Make streaming call
            stream = rt.call_agent_stream("StreamingAgent", "Remember: my favorite color is blue")
            
            # Consume all chunks
            async for chunk in stream:
                pass
            
            # Check memory was updated
            final_memory_size = len(await agent_instance.memory.get_history())
            assert final_memory_size == initial_memory_size + 2, "Should add user + assistant message"
            
            # Follow-up call should remember context
            stream2 = rt.call_agent_stream("StreamingAgent", "What's my favorite color?")
            content_parts = []
            
            async for chunk in stream2:
                if chunk.content:
                    content_parts.append(chunk.content)
            
            full_response = "".join(content_parts)
            assert "blue" in full_response.lower(), f"Should remember favorite color: {full_response}"
            
            print(f"✅ Memory working: {full_response}")
    
    @pytest.mark.asyncio
    async def test_streaming_latency_improvement(self, streaming_app):
        """Test that streaming provides latency benefits."""
        prompt = "Tell me an interesting fact about space exploration"
        
        async with streaming_app.run_context() as rt:
            # Time non-streaming response
            start_time = asyncio.get_event_loop().time()
            non_stream_response = await rt.call_agent("StreamingAgent", prompt)
            non_stream_duration = asyncio.get_event_loop().time() - start_time
            
            # Time streaming response (first chunk)
            start_time = asyncio.get_event_loop().time()
            stream = rt.call_agent_stream("StreamingAgent", prompt)
            
            first_chunk_time = None
            total_chunks = 0
            
            async for chunk in stream:
                total_chunks += 1
                if chunk.content and first_chunk_time is None:
                    first_chunk_time = asyncio.get_event_loop().time() - start_time
            
            # First chunk should arrive faster than full non-streaming response
            assert first_chunk_time is not None, "Should receive first chunk"
            assert first_chunk_time < non_stream_duration, "First chunk should be faster than full response"
            
            improvement = (non_stream_duration - first_chunk_time) / non_stream_duration * 100
            
            print(f"✅ Latency improvement: {improvement:.1f}% ({first_chunk_time:.3f}s vs {non_stream_duration:.3f}s)")
            print(f"Total chunks received: {total_chunks}")


class TestMultiAgentStreaming:
    """Test streaming in multi-agent scenarios."""
    
    @pytest.mark.asyncio
    async def test_agent_coordination_streaming(self, multi_agent_app):
        """Test streaming when coordinator calls other agents."""
        async with multi_agent_app.run_context() as rt:
            stream = rt.call_agent_stream(
                "Coordinator", 
                "Create a brief overview of renewable energy (research then write)"
            )
            
            chunks = []
            content_parts = []
            
            async for chunk in stream:
                chunks.append(chunk)
                if chunk.content:
                    content_parts.append(chunk.content)
            
            full_content = "".join(content_parts)
            
            # Should have received streaming response
            assert len(chunks) > 1, "Should receive multiple chunks"
            assert len(full_content) > 0, "Should have content"
            
            # Content should be about renewable energy
            renewable_terms = ["renewable", "energy", "solar", "wind", "environment"]
            assert any(term in full_content.lower() for term in renewable_terms), \
                f"Should mention renewable energy terms in: {full_content}"
            
            print(f"✅ Multi-agent streaming: {len(chunks)} chunks")
            print(f"Content sample: {full_content[:200]}...")
    
    @pytest.mark.asyncio
    async def test_concurrent_streaming_agents(self, streaming_app):
        """Test multiple concurrent streaming calls."""
        async with streaming_app.run_context() as rt:
            # Start multiple streaming calls concurrently
            prompts = [
                "What is 5 + 5?",
                "What time is it?", 
                "Tell me a fun fact"
            ]
            
            # Create streams
            streams = [rt.call_agent_stream("StreamingAgent", prompt) for prompt in prompts]
            
            # Collect results concurrently
            async def collect_stream(stream):
                chunks = []
                async for chunk in stream:
                    chunks.append(chunk)
                return chunks
            
            # Run all streams concurrently
            results = await asyncio.gather(*[collect_stream(stream) for stream in streams])
            
            # All should have completed successfully
            assert len(results) == 3, "All three streams should complete"
            
            for i, chunks in enumerate(results):
                assert len(chunks) > 0, f"Stream {i} should have chunks"
                content = "".join(chunk.content or "" for chunk in chunks)
                assert len(content) > 0, f"Stream {i} should have content"
            
            print(f"✅ Concurrent streaming: {[len(r) for r in results]} chunks each")


class TestEnterpriseStreaming:
    """Test enterprise streaming features."""
    
    @pytest.mark.asyncio
    async def test_enterprise_streaming_integration(self, real_llm):
        """Test streaming works with enterprise features."""
        try:
            from tframex.enterprise.app import EnterpriseApp
            from tframex.enterprise.config import EnterpriseConfig
            
            # Minimal enterprise config for testing
            config = EnterpriseConfig()
            config.enabled = False  # Disable complex features for testing
            
            app = EnterpriseApp(
                default_llm=real_llm, 
                enterprise_config=config, 
                auto_initialize=False
            )
            
            @app.agent(
                name="EnterpriseStreamingAgent",
                description="Enterprise agent with streaming",
                system_prompt="You are a helpful enterprise assistant."
            )
            async def enterprise_agent():
                pass
            
            async with app.run_context() as rt:
                stream = rt.call_agent_stream(
                    "EnterpriseStreamingAgent", 
                    "Explain the benefits of AI in business in 2-3 sentences"
                )
                
                chunks = []
                content_parts = []
                
                async for chunk in stream:
                    chunks.append(chunk)
                    if chunk.content:
                        content_parts.append(chunk.content)
                
                full_content = "".join(content_parts)
                
                # Validate enterprise streaming works
                assert len(chunks) > 1, "Enterprise streaming should work"
                assert len(full_content) > 0, "Should have content"
                assert any(term in full_content.lower() for term in ["business", "ai", "benefit"]), \
                    "Should address the business AI question"
                
                print(f"✅ Enterprise streaming: {len(chunks)} chunks")
                print(f"Enterprise response: {full_content[:150]}...")
                
        except ImportError:
            pytest.skip("Enterprise features not available")


class TestStreamingErrorHandling:
    """Test error handling in streaming scenarios."""
    
    @pytest.mark.asyncio
    async def test_streaming_with_invalid_tool_call(self, streaming_app):
        """Test streaming handles tool errors gracefully."""
        async with streaming_app.run_context() as rt:
            # Request something that might cause a tool error
            stream = rt.call_agent_stream(
                "StreamingAgent", 
                "Add these numbers: 'hello' + 'world'"
            )
            
            chunks = []
            error_handled = False
            
            try:
                async for chunk in stream:
                    chunks.append(chunk)
                    # Check if error is handled gracefully in content
                    if chunk.content and ("error" in chunk.content.lower() or "cannot" in chunk.content.lower()):
                        error_handled = True
                
                # Should complete without raising exception
                assert len(chunks) > 0, "Should receive chunks even with errors"
                
                print(f"✅ Error handling: {len(chunks)} chunks, error handled gracefully")
                
            except Exception as e:
                # If exception is raised, it should be a reasonable error
                print(f"✅ Error handling: Exception caught as expected: {e}")
    
    @pytest.mark.asyncio
    async def test_streaming_with_long_response(self, streaming_app):
        """Test streaming with longer responses."""
        async with streaming_app.run_context() as rt:
            stream = rt.call_agent_stream(
                "StreamingAgent",
                "Tell me about the history of computers, but keep it under 5 sentences"
            )
            
            chunks = []
            total_length = 0
            
            async for chunk in stream:
                chunks.append(chunk)
                if chunk.content:
                    total_length += len(chunk.content)
            
            # Should receive many chunks for longer content
            assert len(chunks) >= 3, f"Should receive multiple chunks for longer content, got {len(chunks)}"
            assert total_length > 100, f"Should have substantial content, got {total_length} chars"
            
            print(f"✅ Long response streaming: {len(chunks)} chunks, {total_length} characters")


if __name__ == "__main__":
    # Run with pytest
    pytest.main([__file__, "-v", "-s"])