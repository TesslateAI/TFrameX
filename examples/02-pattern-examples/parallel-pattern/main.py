#!/usr/bin/env python3
"""
TFrameX Parallel Pattern Example

Demonstrates concurrent agent execution where multiple agents
work simultaneously and their results are aggregated.

Use cases:
- Multi-perspective analysis
- Concurrent data processing
- Independent task execution
- Competitive solutions

Author: TFrameX Team
License: MIT
"""

import asyncio
import logging
import os
from dotenv import load_dotenv

from tframex import TFrameXApp, OpenAIChatLLM, Message, Flow, ParallelPattern

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("parallel-pattern")


def create_app() -> TFrameXApp:
    """Create and configure the TFrameX application."""
    
    api_key = os.getenv("OPENAI_API_KEY")
    api_base = os.getenv("OPENAI_API_BASE") 
    model_name = os.getenv("OPENAI_MODEL_NAME", "gpt-3.5-turbo")
    
    if not api_key or not api_base:
        raise ValueError("Missing required environment configuration")
    
    llm = OpenAIChatLLM(
        model_name=model_name,
        api_base_url=api_base,
        api_key=api_key
    )
    
    app = TFrameXApp(default_llm=llm)
    
    # Define specialized agents for parallel analysis
    @app.agent(
        name="TechnicalAnalyst",
        description="Analyzes technical aspects and implementation details",
        system_prompt=(
            "You are a Technical Analyst. Focus on:\n"
            "- Technical feasibility and requirements\n"
            "- Implementation challenges and solutions\n"
            "- Technology stack recommendations\n"
            "- Performance and scalability considerations\n"
            "Provide detailed technical insights."
        )
    )
    async def technical_analyst():
        pass
    
    @app.agent(
        name="BusinessAnalyst", 
        description="Analyzes business value and market impact",
        system_prompt=(
            "You are a Business Analyst. Focus on:\n"
            "- Business value and ROI\n"
            "- Market opportunities and risks\n"
            "- Competitive advantages\n"
            "- Cost-benefit analysis\n"
            "Provide strategic business insights."
        )
    )
    async def business_analyst():
        pass
    
    @app.agent(
        name="UserExperienceAnalyst",
        description="Analyzes user experience and design aspects",
        system_prompt=(
            "You are a UX Analyst. Focus on:\n"
            "- User needs and pain points\n"
            "- Usability and accessibility\n"
            "- User journey and interface design\n"
            "- User adoption and engagement\n"
            "Provide user-centered insights."
        )
    )
    async def ux_analyst():
        pass
    
    @app.agent(
        name="RiskAnalyst",
        description="Analyzes risks and compliance requirements",
        system_prompt=(
            "You are a Risk Analyst. Focus on:\n"
            "- Security risks and vulnerabilities\n"
            "- Compliance and regulatory requirements\n"
            "- Operational risks\n"
            "- Risk mitigation strategies\n"
            "Provide comprehensive risk assessment."
        )
    )
    async def risk_analyst():
        pass
    
    @app.agent(
        name="AnalysisSynthesizer",
        description="Synthesizes multiple analysis perspectives into unified insights",
        system_prompt=(
            "You are an Analysis Synthesizer. Your role is to:\n"
            "1. Review all the parallel analysis results\n"
            "2. Identify common themes and conflicts\n"
            "3. Synthesize insights into a comprehensive overview\n"
            "4. Provide balanced recommendations\n"
            "5. Highlight key decisions and trade-offs\n"
            "Create a unified, actionable summary."
        )
    )
    async def analysis_synthesizer():
        pass
    
    # Create parallel analysis flow
    analysis_flow = Flow(
        flow_name="ParallelAnalysisFlow",
        description="Multi-perspective parallel analysis with synthesis"
    )
    
    # Parallel pattern for concurrent analysis
    analysis_flow.add_step(
        ParallelPattern(
            pattern_name="MultiPerspectiveAnalysis",
            tasks=["TechnicalAnalyst", "BusinessAnalyst", "UserExperienceAnalyst", "RiskAnalyst"]
        )
    )
    
    # Synthesis step
    analysis_flow.add_step("AnalysisSynthesizer")
    
    app.register_flow(analysis_flow)
    
    return app


async def demo_parallel_analysis(app: TFrameXApp):
    """Demonstrate parallel multi-perspective analysis."""
    
    logger.info("=== Parallel Analysis Demo ===")
    
    async with app.run_context() as rt:
        project = Message(
            role="user",
            content=(
                "Analyze the proposal to implement an AI-powered customer service chatbot "
                "for a mid-size e-commerce company. The chatbot would handle 80% of customer "
                "inquiries, integrate with existing systems, and provide 24/7 support."
            )
        )
        
        flow_result = await rt.run_flow("ParallelAnalysisFlow", project)
        
        print("\n" + "="*60)
        print("SYNTHESIZED ANALYSIS RESULTS:")
        print("="*60)
        print(flow_result.current_message.content)
        print("="*60)


async def demo_individual_analysts(app: TFrameXApp):
    """Show individual analyst results before synthesis."""
    
    logger.info("=== Individual Analyst Demo ===")
    
    async with app.run_context() as rt:
        topic = (
            "Implementing a remote work policy for a traditional office-based company "
            "with 500 employees across multiple locations."
        )
        
        analysts = [
            ("TechnicalAnalyst", "🔧 Technical Analysis"),
            ("BusinessAnalyst", "💼 Business Analysis"), 
            ("UserExperienceAnalyst", "👥 UX Analysis"),
            ("RiskAnalyst", "⚠️ Risk Analysis")
        ]
        
        for agent_name, title in analysts:
            print(f"\n{title}")
            print("-" * 50)
            result = await rt.call_agent(agent_name, Message(role="user", content=topic))
            print(result.content)


async def main():
    """Main application entry point."""
    
    try:
        app = create_app()
        
        print("\nTFrameX Parallel Pattern Example")
        print("=================================")
        print("1. Run parallel analysis flow")
        print("2. Show individual analyst outputs")
        print("3. Interactive chat with synthesizer")
        
        choice = input("\nEnter your choice (1-3): ").strip()
        
        if choice == "1":
            await demo_parallel_analysis(app)
        elif choice == "2":
            await demo_individual_analysts(app)
        elif choice == "3":
            async with app.run_context() as rt:
                await rt.interactive_chat(default_agent_name="AnalysisSynthesizer")
        else:
            print("Running parallel analysis flow...")
            await demo_parallel_analysis(app)
            
    except Exception as e:
        logger.error(f"Application error: {e}")
        raise


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Parallel Pattern example terminated by user")
    except Exception as e:
        logger.error(f"Unhandled error: {e}")
        exit(1)