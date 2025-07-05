#!/usr/bin/env python3
"""
Comprehensive end-to-end streaming vs non-streaming comparison test
"""

import asyncio
import logging
import os
import time
import statistics
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# TFrameX imports
from tframex import TFrameXApp, Flow, Message, OpenAIChatLLM
from tframex import SequentialPattern, ParallelPattern, RouterPattern

# LLM Configuration
llm = OpenAIChatLLM(
    model_name=os.getenv("OPENAI_MODEL_NAME", "Llama-4-Maverick-17B-128E-Instruct-FP8"),
    api_base_url=os.getenv("OPENAI_API_BASE", "https://api.llama.com/compat/v1/"),
    api_key=os.getenv("OPENAI_API_KEY", " ")
)

class ComprehensiveStreamingTest:
    """Comprehensive test comparing streaming vs non-streaming performance and functionality."""
    
    def __init__(self):
        self.results = {}
        self.performance_metrics = {}
    
    async def test_basic_response_time(self, streaming: bool):
        """Test basic response time and quality."""
        mode = "streaming" if streaming else "non_streaming"
        logger.info(f"Testing basic response time - {mode}")
        
        app = TFrameXApp(default_llm=llm)
        
        @app.agent(
            name="ResponseTimeAgent",
            description="Agent for response time testing",
            system_prompt="You are a helpful assistant. Provide concise responses.",
            streaming=streaming
        )
        async def response_time_agent():
            pass
        
        times = []
        for i in range(3):  # Run 3 iterations
            start_time = time.time()
            
            async with app.run_context() as ctx:
                message = Message(role="user", content=f"Tell me a brief fact about science. Iteration {i+1}")
                response = await ctx.call_agent("ResponseTimeAgent", message)
                
            end_time = time.time()
            response_time = end_time - start_time
            times.append(response_time)
            
            # Quality check
            quality_score = 1 if response and len(response.content) > 10 else 0
            
        avg_time = statistics.mean(times)
        self.performance_metrics[f"basic_response_time_{mode}"] = {
            "avg_time": avg_time,
            "times": times,
            "quality": quality_score
        }
        
        logger.info(f"Basic response time {mode}: {avg_time:.2f}s avg")
        return avg_time, quality_score
    
    async def test_complex_workflow_performance(self, streaming: bool):
        """Test complex workflow with multiple agents."""
        mode = "streaming" if streaming else "non_streaming"
        logger.info(f"Testing complex workflow - {mode}")
        
        app = TFrameXApp(default_llm=llm)
        
        @app.agent(
            name="DataCollectorAgent",
            description="Collects data",
            system_prompt="You are a data collector. Create a brief data summary.",
            streaming=streaming
        )
        async def data_collector():
            pass
        
        @app.agent(
            name="DataProcessorAgent",
            description="Processes data",
            system_prompt="You are a data processor. Analyze the input data briefly.",
            streaming=streaming
        )
        async def data_processor():
            pass
        
        @app.agent(
            name="ReportGeneratorAgent",
            description="Generates reports",
            system_prompt="You are a report generator. Create a brief final report.",
            streaming=streaming
        )
        async def report_generator():
            pass
        
        # Create complex workflow
        flow = Flow(
            flow_name="ComplexWorkflow",
            description="Complex data processing workflow"
        )
        flow.add_step("DataCollectorAgent").add_step("DataProcessorAgent").add_step("ReportGeneratorAgent")
        app.register_flow(flow)
        
        start_time = time.time()
        
        async with app.run_context() as ctx:
            message = Message(role="user", content="Process sales data from Q3")
            result = await ctx.run_flow("ComplexWorkflow", message)
            
        end_time = time.time()
        workflow_time = end_time - start_time
        
        # Quality check
        quality_score = 1 if result and result.current_message and len(result.current_message.content) > 20 else 0
        
        self.performance_metrics[f"complex_workflow_{mode}"] = {
            "time": workflow_time,
            "quality": quality_score
        }
        
        logger.info(f"Complex workflow {mode}: {workflow_time:.2f}s")
        return workflow_time, quality_score
    
    async def test_parallel_processing_performance(self, streaming: bool):
        """Test parallel processing performance."""
        mode = "streaming" if streaming else "non_streaming"
        logger.info(f"Testing parallel processing - {mode}")
        
        app = TFrameXApp(default_llm=llm)
        
        @app.agent(
            name="TaskA",
            description="Task A processor",
            system_prompt="You are Task A processor. Handle Task A briefly.",
            streaming=streaming
        )
        async def task_a():
            pass
        
        @app.agent(
            name="TaskB",
            description="Task B processor",
            system_prompt="You are Task B processor. Handle Task B briefly.",
            streaming=streaming
        )
        async def task_b():
            pass
        
        @app.agent(
            name="TaskC",
            description="Task C processor",
            system_prompt="You are Task C processor. Handle Task C briefly.",
            streaming=streaming
        )
        async def task_c():
            pass
        
        @app.agent(
            name="ResultAggregator",
            description="Aggregates results",
            system_prompt="You are a result aggregator. Combine all results briefly.",
            streaming=streaming
        )
        async def result_aggregator():
            pass
        
        # Create parallel workflow
        flow = Flow(
            flow_name="ParallelWorkflow",
            description="Parallel processing workflow"
        )
        flow.add_step(
            ParallelPattern(
                pattern_name="ParallelTasks",
                tasks=["TaskA", "TaskB", "TaskC"]
            )
        )
        flow.add_step("ResultAggregator")
        app.register_flow(flow)
        
        start_time = time.time()
        
        async with app.run_context() as ctx:
            message = Message(role="user", content="Process multiple tasks simultaneously")
            result = await ctx.run_flow("ParallelWorkflow", message)
            
        end_time = time.time()
        parallel_time = end_time - start_time
        
        # Quality check
        quality_score = 1 if result and result.current_message and len(result.current_message.content) > 20 else 0
        
        self.performance_metrics[f"parallel_processing_{mode}"] = {
            "time": parallel_time,
            "quality": quality_score
        }
        
        logger.info(f"Parallel processing {mode}: {parallel_time:.2f}s")
        return parallel_time, quality_score
    
    async def test_router_pattern_performance(self, streaming: bool):
        """Test router pattern performance."""
        mode = "streaming" if streaming else "non_streaming"
        logger.info(f"Testing router pattern - {mode}")
        
        app = TFrameXApp(default_llm=llm)
        
        @app.agent(
            name="RouterAgent",
            description="Routes requests",
            system_prompt="Analyze the request and respond with exactly one of: 'finance', 'marketing', or 'general'",
            streaming=streaming
        )
        async def router_agent():
            pass
        
        @app.agent(
            name="FinanceAgent",
            description="Finance specialist",
            system_prompt="You are a finance specialist. Provide brief finance insights.",
            streaming=streaming
        )
        async def finance_agent():
            pass
        
        @app.agent(
            name="MarketingAgent",
            description="Marketing specialist",
            system_prompt="You are a marketing specialist. Provide brief marketing insights.",
            streaming=streaming
        )
        async def marketing_agent():
            pass
        
        @app.agent(
            name="GeneralAgent",
            description="General assistant",
            system_prompt="You are a general assistant. Provide brief general assistance.",
            streaming=streaming
        )
        async def general_agent():
            pass
        
        # Create router workflow
        flow = Flow(
            flow_name="RouterWorkflow",
            description="Router pattern workflow"
        )
        flow.add_step(
            RouterPattern(
                pattern_name="RequestRouter",
                router_agent_name="RouterAgent",
                routes={
                    "finance": "FinanceAgent",
                    "marketing": "MarketingAgent",
                    "general": "GeneralAgent"
                },
                default_route="GeneralAgent"
            )
        )
        app.register_flow(flow)
        
        start_time = time.time()
        
        async with app.run_context() as ctx:
            message = Message(role="user", content="Analyze our quarterly revenue trends")
            result = await ctx.run_flow("RouterWorkflow", message)
            
        end_time = time.time()
        router_time = end_time - start_time
        
        # Quality check
        quality_score = 1 if result and result.current_message and len(result.current_message.content) > 15 else 0
        
        self.performance_metrics[f"router_pattern_{mode}"] = {
            "time": router_time,
            "quality": quality_score
        }
        
        logger.info(f"Router pattern {mode}: {router_time:.2f}s")
        return router_time, quality_score
    
    async def test_tool_usage_performance(self, streaming: bool):
        """Test tool usage performance."""
        mode = "streaming" if streaming else "non_streaming"
        logger.info(f"Testing tool usage - {mode}")
        
        app = TFrameXApp(default_llm=llm)
        
        @app.tool(description="Calculate sum of two numbers")
        async def calculate_sum(a: float, b: float) -> float:
            await asyncio.sleep(0.1)  # Simulate processing time
            return a + b
        
        @app.tool(description="Get current timestamp")
        async def get_timestamp() -> str:
            import datetime
            return datetime.datetime.now().isoformat()
        
        @app.agent(
            name="ToolUsingAgent",
            description="Agent that uses tools",
            system_prompt="You are a helpful assistant with access to tools. Use them when appropriate.",
            tools=["calculate_sum", "get_timestamp"],
            streaming=streaming
        )
        async def tool_using_agent():
            pass
        
        start_time = time.time()
        
        async with app.run_context() as ctx:
            message = Message(role="user", content="Calculate 25 + 17 and tell me the current time")
            response = await ctx.call_agent("ToolUsingAgent", message)
            
        end_time = time.time()
        tool_time = end_time - start_time
        
        # Quality check - should mention both results
        quality_score = 1 if response and ("42" in response.content and "2025" in response.content) else 0
        
        self.performance_metrics[f"tool_usage_{mode}"] = {
            "time": tool_time,
            "quality": quality_score
        }
        
        logger.info(f"Tool usage {mode}: {tool_time:.2f}s")
        return tool_time, quality_score
    
    async def run_comprehensive_tests(self):
        """Run all comprehensive tests comparing streaming vs non-streaming."""
        logger.info("Starting comprehensive end-to-end tests...")
        
        test_methods = [
            self.test_basic_response_time,
            self.test_complex_workflow_performance,
            self.test_parallel_processing_performance,
            self.test_router_pattern_performance,
            self.test_tool_usage_performance
        ]
        
        results = {}
        
        for test_method in test_methods:
            test_name = test_method.__name__.replace("test_", "").replace("_performance", "")
            results[test_name] = {}
            
            # Test both streaming and non-streaming
            for streaming in [True, False]:
                mode = "streaming" if streaming else "non_streaming"
                try:
                    time_taken, quality = await test_method(streaming)
                    results[test_name][mode] = {
                        "time": time_taken,
                        "quality": quality,
                        "success": True
                    }
                except Exception as e:
                    logger.error(f"Test {test_name} {mode} failed: {e}")
                    results[test_name][mode] = {
                        "time": None,
                        "quality": 0,
                        "success": False,
                        "error": str(e)
                    }
        
        self.generate_comparison_report(results)
    
    def generate_comparison_report(self, results):
        """Generate comprehensive comparison report."""
        logger.info("\n" + "="*80)
        logger.info("COMPREHENSIVE STREAMING VS NON-STREAMING COMPARISON REPORT")
        logger.info("="*80)
        
        total_streaming_wins = 0
        total_non_streaming_wins = 0
        total_tests = 0
        
        for test_name, test_results in results.items():
            logger.info(f"\n📊 {test_name.replace('_', ' ').title()}")
            logger.info("-" * 50)
            
            streaming_result = test_results.get("streaming", {})
            non_streaming_result = test_results.get("non_streaming", {})
            
            # Performance comparison
            if streaming_result.get("success") and non_streaming_result.get("success"):
                streaming_time = streaming_result.get("time", 0)
                non_streaming_time = non_streaming_result.get("time", 0)
                
                logger.info(f"⏱️  Performance:")
                logger.info(f"   Streaming:     {streaming_time:.2f}s")
                logger.info(f"   Non-streaming: {non_streaming_time:.2f}s")
                
                if streaming_time < non_streaming_time:
                    logger.info(f"   🏆 Winner: Streaming (faster by {non_streaming_time - streaming_time:.2f}s)")
                    total_streaming_wins += 1
                elif non_streaming_time < streaming_time:
                    logger.info(f"   🏆 Winner: Non-streaming (faster by {streaming_time - non_streaming_time:.2f}s)")
                    total_non_streaming_wins += 1
                else:
                    logger.info(f"   🤝 Tie: Same performance")
                
                total_tests += 1
            
            # Quality comparison
            streaming_quality = streaming_result.get("quality", 0)
            non_streaming_quality = non_streaming_result.get("quality", 0)
            
            logger.info(f"✅ Quality:")
            logger.info(f"   Streaming:     {streaming_quality}")
            logger.info(f"   Non-streaming: {non_streaming_quality}")
            
            if streaming_quality > non_streaming_quality:
                logger.info(f"   🏆 Winner: Streaming (better quality)")
            elif non_streaming_quality > streaming_quality:
                logger.info(f"   🏆 Winner: Non-streaming (better quality)")
            else:
                logger.info(f"   🤝 Tie: Same quality")
            
            # Success status
            streaming_success = streaming_result.get("success", False)
            non_streaming_success = non_streaming_result.get("success", False)
            
            logger.info(f"🔄 Success:")
            logger.info(f"   Streaming:     {'✅' if streaming_success else '❌'}")
            logger.info(f"   Non-streaming: {'✅' if non_streaming_success else '❌'}")
        
        # Overall summary
        logger.info(f"\n🏁 OVERALL PERFORMANCE SUMMARY")
        logger.info("="*50)
        logger.info(f"Total performance tests: {total_tests}")
        logger.info(f"Streaming wins: {total_streaming_wins}")
        logger.info(f"Non-streaming wins: {total_non_streaming_wins}")
        logger.info(f"Ties: {total_tests - total_streaming_wins - total_non_streaming_wins}")
        
        if total_streaming_wins > total_non_streaming_wins:
            logger.info("🎉 OVERALL WINNER: STREAMING")
        elif total_non_streaming_wins > total_streaming_wins:
            logger.info("🎉 OVERALL WINNER: NON-STREAMING")
        else:
            logger.info("🤝 OVERALL RESULT: TIE")
        
        # Performance analysis
        streaming_times = []
        non_streaming_times = []
        
        for test_name, test_results in results.items():
            if test_results.get("streaming", {}).get("success"):
                streaming_times.append(test_results["streaming"]["time"])
            if test_results.get("non_streaming", {}).get("success"):
                non_streaming_times.append(test_results["non_streaming"]["time"])
        
        if streaming_times and non_streaming_times:
            avg_streaming_time = statistics.mean(streaming_times)
            avg_non_streaming_time = statistics.mean(non_streaming_times)
            
            logger.info(f"\n📈 AVERAGE PERFORMANCE METRICS")
            logger.info("="*50)
            logger.info(f"Average streaming time:     {avg_streaming_time:.2f}s")
            logger.info(f"Average non-streaming time: {avg_non_streaming_time:.2f}s")
            
            if avg_streaming_time < avg_non_streaming_time:
                improvement = ((avg_non_streaming_time - avg_streaming_time) / avg_non_streaming_time) * 100
                logger.info(f"🚀 Streaming is {improvement:.1f}% faster on average")
            elif avg_non_streaming_time < avg_streaming_time:
                degradation = ((avg_streaming_time - avg_non_streaming_time) / avg_non_streaming_time) * 100
                logger.info(f"📉 Streaming is {degradation:.1f}% slower on average")
            
            logger.info(f"\n✅ RELIABILITY")
            streaming_success_rate = sum(1 for r in results.values() if r.get("streaming", {}).get("success")) / len(results) * 100
            non_streaming_success_rate = sum(1 for r in results.values() if r.get("non_streaming", {}).get("success")) / len(results) * 100
            
            logger.info(f"Streaming success rate:     {streaming_success_rate:.1f}%")
            logger.info(f"Non-streaming success rate: {non_streaming_success_rate:.1f}%")
        
        logger.info("\n🎯 CONCLUSION")
        logger.info("="*50)
        if total_streaming_wins >= total_non_streaming_wins and streaming_success_rate >= 80:
            logger.info("✅ Streaming implementation is production-ready!")
            logger.info("   - Performance is competitive or better")
            logger.info("   - Reliability is maintained")
            logger.info("   - All major patterns work correctly")
        else:
            logger.info("⚠️  Streaming implementation needs attention:")
            if total_streaming_wins < total_non_streaming_wins:
                logger.info("   - Performance needs optimization")
            if streaming_success_rate < 80:
                logger.info("   - Reliability needs improvement")


async def main():
    """Main test runner."""
    test_suite = ComprehensiveStreamingTest()
    await test_suite.run_comprehensive_tests()


if __name__ == "__main__":
    asyncio.run(main())