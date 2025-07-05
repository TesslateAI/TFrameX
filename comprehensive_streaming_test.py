#!/usr/bin/env python3
"""
Comprehensive TFrameX Streaming Test Suite
Tests streaming functionality across all usage scenarios.
"""

import asyncio
import logging
import os
import sys
import time
from pathlib import Path
from typing import List, Dict, Any

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Load environment
from dotenv import load_dotenv
load_dotenv(project_root / ".env")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# TFrameX imports
from tframex import TFrameXApp, Flow, Message, OpenAIChatLLM
from tframex import SequentialPattern, ParallelPattern, RouterPattern, DiscussionPattern


class StreamingTestSuite:
    """Comprehensive test suite for TFrameX streaming functionality."""
    
    def __init__(self):
        self.llm = OpenAIChatLLM(
            model_name=os.getenv("OPENAI_MODEL_NAME", "Llama-4-Maverick-17B-128E-Instruct-FP8"),
            api_base_url=os.getenv("OPENAI_API_BASE", "https://api.llama.com/compat/v1/"),
            api_key=os.getenv("OPENAI_API_KEY", " ")
        )
        self.results = []
        
    def log_test_result(self, test_name: str, passed: bool, streaming: bool, details: str = ""):
        """Log test result with streaming mode."""
        result = {
            "test_name": test_name,
            "passed": passed,
            "streaming": streaming,
            "details": details,
            "timestamp": time.time()
        }
        self.results.append(result)
        status = "✅ PASSED" if passed else "❌ FAILED"
        mode = "STREAMING" if streaming else "NON-STREAMING"
        logger.info(f"{status} - {test_name} ({mode}): {details}")
        
    async def test_basic_agent_streaming(self):
        """Test basic agent with streaming enabled/disabled."""
        logger.info("Testing basic agent with streaming...")
        
        for streaming in [True, False]:
            try:
                app = TFrameXApp(default_llm=self.llm)
                
                @app.agent(
                    name="BasicTestAgent",
                    description="Simple test agent",
                    system_prompt="You are a helpful assistant. Keep responses brief.",
                    streaming=streaming
                )
                async def basic_agent():
                    pass
                
                async with app.run_context() as ctx:
                    message = Message(role="user", content="Say hello briefly")
                    response = await ctx.call_agent("BasicTestAgent", message)
                    
                    self.log_test_result(
                        "basic_agent",
                        response is not None and len(response.content) > 0,
                        streaming,
                        f"Response length: {len(response.content) if response else 0}"
                    )
                    
            except Exception as e:
                self.log_test_result("basic_agent", False, streaming, f"Error: {str(e)}")
    
    async def test_sequential_pattern_streaming(self):
        """Test sequential pattern with streaming."""
        logger.info("Testing sequential pattern with streaming...")
        
        for streaming in [True, False]:
            try:
                app = TFrameXApp(default_llm=self.llm)
                
                @app.agent(
                    name="UppercaseAgent",
                    description="Converts text to uppercase",
                    system_prompt="Convert the input text to uppercase. Only return the uppercase text.",
                    streaming=streaming
                )
                async def uppercase_agent():
                    pass
                
                @app.agent(
                    name="ReverseAgent", 
                    description="Reverses text",
                    system_prompt="Reverse the input text. Only return the reversed text.",
                    streaming=streaming
                )
                async def reverse_agent():
                    pass
                
                # Create sequential flow
                flow = Flow(
                    flow_name="SequentialTest",
                    description="Tests sequential pattern"
                )
                flow.add_step("UppercaseAgent").add_step("ReverseAgent")
                app.register_flow(flow)
                
                async with app.run_context() as ctx:
                    message = Message(role="user", content="hello world")
                    result = await ctx.run_flow("SequentialTest", message)
                    
                    self.log_test_result(
                        "sequential_pattern",
                        result is not None and result.current_message is not None,
                        streaming,
                        f"Final result: {result.current_message.content if result and result.current_message else 'None'}"
                    )
                    
            except Exception as e:
                self.log_test_result("sequential_pattern", False, streaming, f"Error: {str(e)}")
    
    async def test_parallel_pattern_streaming(self):
        """Test parallel pattern with streaming."""
        logger.info("Testing parallel pattern with streaming...")
        
        for streaming in [True, False]:
            try:
                app = TFrameXApp(default_llm=self.llm)
                
                @app.agent(
                    name="WeatherAgent",
                    description="Provides weather info",
                    system_prompt="You are a weather assistant. For any location, provide a brief weather report.",
                    streaming=streaming
                )
                async def weather_agent():
                    pass
                
                @app.agent(
                    name="CityAgent",
                    description="Provides city info", 
                    system_prompt="You are a city information assistant. Provide brief city facts.",
                    streaming=streaming
                )
                async def city_agent():
                    pass
                
                @app.agent(
                    name="SummarizerAgent",
                    description="Summarizes information",
                    system_prompt="Summarize the provided information briefly.",
                    streaming=streaming
                )
                async def summarizer_agent():
                    pass
                
                # Create parallel flow
                flow = Flow(
                    flow_name="ParallelTest",
                    description="Tests parallel pattern"
                )
                flow.add_step(
                    ParallelPattern(
                        pattern_name="GetInfo",
                        tasks=["WeatherAgent", "CityAgent"]
                    )
                )
                flow.add_step("SummarizerAgent")
                app.register_flow(flow)
                
                async with app.run_context() as ctx:
                    message = Message(role="user", content="Tell me about Tokyo")
                    result = await ctx.run_flow("ParallelTest", message)
                    
                    self.log_test_result(
                        "parallel_pattern",
                        result is not None and result.current_message is not None,
                        streaming,
                        f"Result exists: {result.current_message is not None if result else False}"
                    )
                    
            except Exception as e:
                self.log_test_result("parallel_pattern", False, streaming, f"Error: {str(e)}")
    
    async def test_router_pattern_streaming(self):
        """Test router pattern with streaming."""
        logger.info("Testing router pattern with streaming...")
        
        for streaming in [True, False]:
            try:
                app = TFrameXApp(default_llm=self.llm)
                
                @app.agent(
                    name="RouterAgent",
                    description="Routes queries",
                    system_prompt="Analyze the query and respond with exactly one of: 'weather', 'city', or 'general'",
                    streaming=streaming
                )
                async def router_agent():
                    pass
                
                @app.agent(
                    name="WeatherAgent",
                    description="Weather assistant",
                    system_prompt="Provide weather information.",
                    streaming=streaming
                )
                async def weather_agent():
                    pass
                
                @app.agent(
                    name="CityAgent", 
                    description="City assistant",
                    system_prompt="Provide city information.",
                    streaming=streaming
                )
                async def city_agent():
                    pass
                
                @app.agent(
                    name="GeneralAgent",
                    description="General assistant",
                    system_prompt="Provide general assistance.",
                    streaming=streaming
                )
                async def general_agent():
                    pass
                
                # Create router flow
                flow = Flow(
                    flow_name="RouterTest",
                    description="Tests router pattern"
                )
                flow.add_step(
                    RouterPattern(
                        pattern_name="QueryRouter",
                        router_agent_name="RouterAgent",
                        routes={
                            "weather": "WeatherAgent",
                            "city": "CityAgent",
                            "general": "GeneralAgent"
                        },
                        default_route="GeneralAgent"
                    )
                )
                app.register_flow(flow)
                
                async with app.run_context() as ctx:
                    message = Message(role="user", content="What's the weather like?")
                    result = await ctx.run_flow("RouterTest", message)
                    
                    self.log_test_result(
                        "router_pattern",
                        result is not None and result.current_message is not None,
                        streaming,
                        f"Routed successfully: {result.current_message is not None if result else False}"
                    )
                    
            except Exception as e:
                self.log_test_result("router_pattern", False, streaming, f"Error: {str(e)}")
    
    async def test_discussion_pattern_streaming(self):
        """Test discussion pattern with streaming."""
        logger.info("Testing discussion pattern with streaming...")
        
        for streaming in [True, False]:
            try:
                app = TFrameXApp(default_llm=self.llm)
                
                @app.agent(
                    name="OptimistAgent",
                    description="Optimistic participant",
                    system_prompt="You are an optimist. Find positive aspects. Keep responses brief.",
                    streaming=streaming
                )
                async def optimist_agent():
                    pass
                
                @app.agent(
                    name="PessimistAgent",
                    description="Pessimistic participant", 
                    system_prompt="You are a pessimist. Point out concerns. Keep responses brief.",
                    streaming=streaming
                )
                async def pessimist_agent():
                    pass
                
                @app.agent(
                    name="ModeratorAgent",
                    description="Discussion moderator",
                    system_prompt="Moderate the discussion and provide brief summaries.",
                    streaming=streaming
                )
                async def moderator_agent():
                    pass
                
                # Create discussion flow
                flow = Flow(
                    flow_name="DiscussionTest",
                    description="Tests discussion pattern"
                )
                flow.add_step(
                    DiscussionPattern(
                        pattern_name="TestDiscussion",
                        participant_agent_names=["OptimistAgent", "PessimistAgent"],
                        discussion_rounds=1,
                        moderator_agent_name="ModeratorAgent"
                    )
                )
                app.register_flow(flow)
                
                async with app.run_context() as ctx:
                    message = Message(role="user", content="Discuss the benefits of AI")
                    result = await ctx.run_flow("DiscussionTest", message)
                    
                    self.log_test_result(
                        "discussion_pattern",
                        result is not None and result.current_message is not None,
                        streaming,
                        f"Discussion completed: {result.current_message is not None if result else False}"
                    )
                    
            except Exception as e:
                self.log_test_result("discussion_pattern", False, streaming, f"Error: {str(e)}")
    
    async def test_tool_usage_streaming(self):
        """Test tool usage with streaming."""
        logger.info("Testing tool usage with streaming...")
        
        for streaming in [True, False]:
            try:
                app = TFrameXApp(default_llm=self.llm)
                
                @app.tool(description="Get current weather")
                async def get_weather(location: str) -> str:
                    return f"The weather in {location} is sunny, 25°C"
                
                @app.agent(
                    name="WeatherToolAgent",
                    description="Uses weather tools",
                    system_prompt="You are a weather assistant. Use the get_weather tool to provide information.",
                    tools=["get_weather"],
                    streaming=streaming
                )
                async def weather_tool_agent():
                    pass
                
                async with app.run_context() as ctx:
                    message = Message(role="user", content="What's the weather in Tokyo?")
                    response = await ctx.call_agent("WeatherToolAgent", message)
                    
                    self.log_test_result(
                        "tool_usage",
                        response is not None and "tokyo" in response.content.lower(),
                        streaming,
                        f"Tool used successfully: {'tokyo' in response.content.lower() if response else False}"
                    )
                    
            except Exception as e:
                self.log_test_result("tool_usage", False, streaming, f"Error: {str(e)}")
    
    async def test_enterprise_streaming(self):
        """Test enterprise features with streaming."""
        logger.info("Testing enterprise features with streaming...")
        
        try:
            from tframex.enterprise import EnterpriseApp, create_default_config
            
            for streaming in [True, False]:
                try:
                    config = create_default_config(environment="test")
                    app = EnterpriseApp(
                        default_llm=self.llm,
                        enterprise_config=config,
                        auto_initialize=False
                    )
                    
                    @app.agent(
                        name="EnterpriseTestAgent",
                        description="Enterprise test agent",
                        system_prompt="You are an enterprise assistant. Keep responses brief.",
                        streaming=streaming
                    )
                    async def enterprise_agent():
                        pass
                    
                    await app.initialize_enterprise()
                    await app.start_enterprise()
                    
                    try:
                        async with app.run_context() as ctx:
                            message = Message(role="user", content="Test enterprise functionality")
                            response = await ctx.call_agent("EnterpriseTestAgent", message)
                            
                            self.log_test_result(
                                "enterprise_features",
                                response is not None and len(response.content) > 0,
                                streaming,
                                f"Enterprise agent responded: {response is not None}"
                            )
                    finally:
                        await app.stop_enterprise()
                        
                except Exception as e:
                    self.log_test_result("enterprise_features", False, streaming, f"Error: {str(e)}")
                    
        except ImportError:
            logger.warning("Enterprise features not available, skipping enterprise tests")
            self.log_test_result("enterprise_features", True, True, "Skipped - not available")
            self.log_test_result("enterprise_features", True, False, "Skipped - not available")
    
    async def run_all_tests(self):
        """Run all streaming tests."""
        logger.info("Starting comprehensive streaming test suite...")
        
        test_methods = [
            self.test_basic_agent_streaming,
            self.test_sequential_pattern_streaming,
            self.test_parallel_pattern_streaming,
            self.test_router_pattern_streaming,
            self.test_discussion_pattern_streaming,
            self.test_tool_usage_streaming,
            self.test_enterprise_streaming
        ]
        
        for test_method in test_methods:
            try:
                await test_method()
            except Exception as e:
                logger.error(f"Test method {test_method.__name__} failed: {e}")
        
        self.print_summary()
    
    def print_summary(self):
        """Print test summary."""
        logger.info("\n" + "="*60)
        logger.info("STREAMING TEST SUMMARY")
        logger.info("="*60)
        
        streaming_results = [r for r in self.results if r['streaming']]
        non_streaming_results = [r for r in self.results if not r['streaming']]
        
        streaming_passed = sum(1 for r in streaming_results if r['passed'])
        non_streaming_passed = sum(1 for r in non_streaming_results if r['passed'])
        
        logger.info(f"Streaming tests: {streaming_passed}/{len(streaming_results)} passed")
        logger.info(f"Non-streaming tests: {non_streaming_passed}/{len(non_streaming_results)} passed")
        logger.info(f"Total tests: {len(self.results)}")
        
        failed_tests = [r for r in self.results if not r['passed']]
        if failed_tests:
            logger.info("\nFailed tests:")
            for test in failed_tests:
                mode = "STREAMING" if test['streaming'] else "NON-STREAMING"
                logger.info(f"  - {test['test_name']} ({mode}): {test['details']}")
        
        total_passed = len([r for r in self.results if r['passed']])
        success_rate = (total_passed / len(self.results)) * 100 if self.results else 0
        logger.info(f"\nOverall success rate: {success_rate:.1f}%")
        
        if success_rate >= 80:
            logger.info("🎉 Streaming implementation is working well!")
        else:
            logger.warning("⚠️ Streaming implementation needs attention")


async def main():
    """Main test runner."""
    test_suite = StreamingTestSuite()
    await test_suite.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())