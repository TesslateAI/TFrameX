#!/usr/bin/env python3
"""
Test design patterns with streaming functionality
"""

import asyncio
import logging
import os
from dotenv import load_dotenv
from tframex import TFrameXApp, Flow, Message, OpenAIChatLLM
from tframex import SequentialPattern, ParallelPattern, RouterPattern, DiscussionPattern

# Load environment
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# LLM Configuration
llm = OpenAIChatLLM(
    model_name=os.getenv("OPENAI_MODEL_NAME", "Llama-4-Maverick-17B-128E-Instruct-FP8"),
    api_base_url=os.getenv("OPENAI_API_BASE", "https://api.llama.com/compat/v1/"),
    api_key=os.getenv("OPENAI_API_KEY", " ")
)

async def test_streaming_vs_non_streaming():
    """Test all design patterns with streaming on and off"""
    logger.info("Testing design patterns with streaming enabled and disabled...")
    
    test_results = []
    
    for streaming in [True, False]:
        mode = "STREAMING" if streaming else "NON-STREAMING"
        logger.info(f"\n{'='*50}")
        logger.info(f"Testing {mode} mode")
        logger.info(f"{'='*50}")
        
        # Test 1: Sequential Pattern - Observer-like behavior
        try:
            logger.info("1. Testing Sequential Pattern (Observer-like)")
            app = TFrameXApp(default_llm=llm)
            
            @app.agent(
                name="EventPublisher",
                description="Publishes events",
                system_prompt="You are an event publisher. Transform the input into an event notification.",
                streaming=streaming
            )
            async def event_publisher():
                pass
            
            @app.agent(
                name="EventSubscriber1",
                description="First event subscriber",
                system_prompt="You are subscriber 1. React to the event with 'Subscriber 1 received:'",
                streaming=streaming
            )
            async def event_subscriber1():
                pass
            
            @app.agent(
                name="EventSubscriber2", 
                description="Second event subscriber",
                system_prompt="You are subscriber 2. React to the event with 'Subscriber 2 processed:'",
                streaming=streaming
            )
            async def event_subscriber2():
                pass
            
            # Observer pattern via sequential flow
            flow = Flow(
                flow_name="ObserverPattern",
                description="Observer pattern implementation"
            )
            flow.add_step("EventPublisher").add_step("EventSubscriber1").add_step("EventSubscriber2")
            app.register_flow(flow)
            
            async with app.run_context() as ctx:
                message = Message(role="user", content="User clicked button")
                result = await ctx.run_flow("ObserverPattern", message)
                success = result and result.current_message
                test_results.append(f"Sequential/Observer {mode}: {'PASS' if success else 'FAIL'}")
                logger.info(f"Observer Pattern {mode}: {'PASS' if success else 'FAIL'}")
                
        except Exception as e:
            test_results.append(f"Sequential/Observer {mode}: FAIL - {str(e)}")
            logger.error(f"Observer Pattern {mode}: FAIL - {str(e)}")
        
        # Test 2: Strategy Pattern via Router
        try:
            logger.info("2. Testing Strategy Pattern (Router)")
            app = TFrameXApp(default_llm=llm)
            
            @app.agent(
                name="StrategySelector",
                description="Selects processing strategy",
                system_prompt="Analyze the request and respond with exactly one of: 'fast', 'detailed', or 'secure'",
                streaming=streaming
            )
            async def strategy_selector():
                pass
            
            @app.agent(
                name="FastStrategy",
                description="Fast processing strategy",
                system_prompt="Process quickly with minimal detail.",
                streaming=streaming
            )
            async def fast_strategy():
                pass
            
            @app.agent(
                name="DetailedStrategy",
                description="Detailed processing strategy", 
                system_prompt="Process with comprehensive analysis.",
                streaming=streaming
            )
            async def detailed_strategy():
                pass
            
            @app.agent(
                name="SecureStrategy",
                description="Secure processing strategy",
                system_prompt="Process with security focus.",
                streaming=streaming
            )
            async def secure_strategy():
                pass
            
            # Strategy pattern via router
            flow = Flow(
                flow_name="StrategyPattern",
                description="Strategy pattern implementation"
            )
            flow.add_step(
                RouterPattern(
                    pattern_name="StrategyRouter",
                    router_agent_name="StrategySelector",
                    routes={
                        "fast": "FastStrategy",
                        "detailed": "DetailedStrategy", 
                        "secure": "SecureStrategy"
                    },
                    default_route="FastStrategy"
                )
            )
            app.register_flow(flow)
            
            async with app.run_context() as ctx:
                message = Message(role="user", content="Process this data quickly")
                result = await ctx.run_flow("StrategyPattern", message)
                success = result and result.current_message
                test_results.append(f"Strategy/Router {mode}: {'PASS' if success else 'FAIL'}")
                logger.info(f"Strategy Pattern {mode}: {'PASS' if success else 'FAIL'}")
                
        except Exception as e:
            test_results.append(f"Strategy/Router {mode}: FAIL - {str(e)}")
            logger.error(f"Strategy Pattern {mode}: FAIL - {str(e)}")
        
        # Test 3: Chain of Responsibility Pattern
        try:
            logger.info("3. Testing Chain of Responsibility Pattern")
            app = TFrameXApp(default_llm=llm)
            
            @app.agent(
                name="Level1Handler",
                description="First level handler",
                system_prompt="Handle basic requests. If complex, pass to next level with 'ESCALATE:'",
                streaming=streaming
            )
            async def level1_handler():
                pass
            
            @app.agent(
                name="Level2Handler",
                description="Second level handler",
                system_prompt="Handle intermediate requests. If very complex, pass to next level with 'ESCALATE:'",
                streaming=streaming
            )
            async def level2_handler():
                pass
            
            @app.agent(
                name="Level3Handler",
                description="Final level handler",
                system_prompt="Handle all complex requests. This is the final handler.",
                streaming=streaming
            )
            async def level3_handler():
                pass
            
            # Chain of responsibility via sequential flow
            flow = Flow(
                flow_name="ChainOfResponsibilityPattern",
                description="Chain of responsibility pattern"
            )
            flow.add_step("Level1Handler").add_step("Level2Handler").add_step("Level3Handler")
            app.register_flow(flow)
            
            async with app.run_context() as ctx:
                message = Message(role="user", content="Complex system integration problem")
                result = await ctx.run_flow("ChainOfResponsibilityPattern", message)
                success = result and result.current_message
                test_results.append(f"Chain of Responsibility {mode}: {'PASS' if success else 'FAIL'}")
                logger.info(f"Chain of Responsibility {mode}: {'PASS' if success else 'FAIL'}")
                
        except Exception as e:
            test_results.append(f"Chain of Responsibility {mode}: FAIL - {str(e)}")
            logger.error(f"Chain of Responsibility {mode}: FAIL - {str(e)}")
        
        # Test 4: Command Pattern via Parallel Execution
        try:
            logger.info("4. Testing Command Pattern (Parallel)")
            app = TFrameXApp(default_llm=llm)
            
            @app.agent(
                name="SaveCommand",
                description="Save command executor",
                system_prompt="Execute save operation on the data.",
                streaming=streaming
            )
            async def save_command():
                pass
            
            @app.agent(
                name="ValidateCommand",
                description="Validate command executor",
                system_prompt="Execute validation operation on the data.",
                streaming=streaming
            )
            async def validate_command():
                pass
            
            @app.agent(
                name="LogCommand",
                description="Log command executor",
                system_prompt="Execute logging operation on the data.",
                streaming=streaming
            )
            async def log_command():
                pass
            
            @app.agent(
                name="CommandInvoker",
                description="Command invoker",
                system_prompt="Summarize the results of all executed commands.",
                streaming=streaming
            )
            async def command_invoker():
                pass
            
            # Command pattern via parallel execution
            flow = Flow(
                flow_name="CommandPattern",
                description="Command pattern implementation"
            )
            flow.add_step(
                ParallelPattern(
                    pattern_name="ExecuteCommands",
                    tasks=["SaveCommand", "ValidateCommand", "LogCommand"]
                )
            )
            flow.add_step("CommandInvoker")
            app.register_flow(flow)
            
            async with app.run_context() as ctx:
                message = Message(role="user", content="Process user data submission")
                result = await ctx.run_flow("CommandPattern", message)
                success = result and result.current_message
                test_results.append(f"Command/Parallel {mode}: {'PASS' if success else 'FAIL'}")
                logger.info(f"Command Pattern {mode}: {'PASS' if success else 'FAIL'}")
                
        except Exception as e:
            test_results.append(f"Command/Parallel {mode}: FAIL - {str(e)}")
            logger.error(f"Command Pattern {mode}: FAIL - {str(e)}")
        
        # Test 5: Mediator Pattern via Discussion
        try:
            logger.info("5. Testing Mediator Pattern (Discussion)")
            app = TFrameXApp(default_llm=llm)
            
            @app.agent(
                name="ComponentA",
                description="System component A",
                system_prompt="You are component A. Provide perspective A on the topic.",
                streaming=streaming
            )
            async def component_a():
                pass
            
            @app.agent(
                name="ComponentB",
                description="System component B",
                system_prompt="You are component B. Provide perspective B on the topic.",
                streaming=streaming
            )
            async def component_b():
                pass
            
            @app.agent(
                name="MediatorAgent",
                description="Mediator between components",
                system_prompt="You are the mediator. Coordinate between components and provide final decision.",
                streaming=streaming
            )
            async def mediator_agent():
                pass
            
            # Mediator pattern via discussion
            flow = Flow(
                flow_name="MediatorPattern",
                description="Mediator pattern implementation"
            )
            flow.add_step(
                DiscussionPattern(
                    pattern_name="ComponentDiscussion",
                    participant_agent_names=["ComponentA", "ComponentB"],
                    discussion_rounds=1,
                    moderator_agent_name="MediatorAgent"
                )
            )
            app.register_flow(flow)
            
            async with app.run_context() as ctx:
                message = Message(role="user", content="Coordinate system resource allocation")
                result = await ctx.run_flow("MediatorPattern", message)
                success = result and result.current_message
                test_results.append(f"Mediator/Discussion {mode}: {'PASS' if success else 'FAIL'}")
                logger.info(f"Mediator Pattern {mode}: {'PASS' if success else 'FAIL'}")
                
        except Exception as e:
            test_results.append(f"Mediator/Discussion {mode}: FAIL - {str(e)}")
            logger.error(f"Mediator Pattern {mode}: FAIL - {str(e)}")
    
    # Print summary
    logger.info(f"\n{'='*60}")
    logger.info("DESIGN PATTERNS STREAMING TEST SUMMARY")
    logger.info(f"{'='*60}")
    
    for result in test_results:
        logger.info(result)
    
    passed = len([r for r in test_results if 'PASS' in r])
    total = len(test_results)
    success_rate = (passed / total) * 100 if total > 0 else 0
    
    logger.info(f"\nOverall: {passed}/{total} tests passed ({success_rate:.1f}%)")
    
    if success_rate >= 80:
        logger.info("🎉 Design patterns work well with streaming!")
    else:
        logger.warning("⚠️ Some design patterns need attention with streaming")

if __name__ == "__main__":
    asyncio.run(test_streaming_vs_non_streaming())