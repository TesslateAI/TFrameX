#!/usr/bin/env python3
"""
Enhanced TFrameX Enterprise Example

This example demonstrates the complete enterprise feature set including:
- Enhanced workflow tracing with distributed spans
- Real-time analytics dashboard
- Comprehensive security with RBAC
- Cost tracking and optimization
- Performance monitoring
- Audit logging
- Multi-agent workflow orchestration
"""

import asyncio
import os
from pathlib import Path

# Load environment
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env.test")

from tframex.enterprise import (
    create_enhanced_enterprise_app, 
    create_default_config,
    User
)
from tframex.util.llms import OpenAIChatLLM


async def main():
    """Main example function demonstrating enterprise features."""
    
    print("🚀 TFrameX Enhanced Enterprise Features Demo")
    print("=" * 60)
    
    # 1. Create enterprise configuration
    print("\n📋 Setting up enterprise configuration...")
    config = create_default_config(environment="demo")
    
    # 2. Create LLM
    llm = OpenAIChatLLM(
        model_name=os.getenv("OPENAI_MODEL_NAME", "gpt-3.5-turbo"),
        api_key=os.getenv("OPENAI_API_KEY"),
        api_base_url=os.getenv("OPENAI_API_BASE")
    )
    
    # 3. Create enhanced enterprise app
    print("🏢 Creating enhanced enterprise application...")
    app = create_enhanced_enterprise_app(
        default_llm=llm,
        enterprise_config=config
    )
    
    # 4. Define enterprise agents
    @app.agent(
        name="DataAnalyst",
        description="Analyzes data and provides insights",
        system_prompt="You are a data analyst. Analyze the provided data and give actionable insights. Be concise but thorough."
    )
    async def data_analyst(): pass
    
    @app.agent(
        name="ReportGenerator", 
        description="Generates comprehensive reports",
        system_prompt="You are a report generator. Create well-structured reports based on analysis results. Use clear headings and bullet points."
    )
    async def report_generator(): pass
    
    @app.agent(
        name="QualityAssurance",
        description="Reviews and validates outputs for quality",
        system_prompt="You are a quality assurance specialist. Review the provided content for accuracy, completeness, and clarity. Provide feedback and suggestions."
    )
    async def quality_assurance(): pass
    
    # 5. Create a multi-agent workflow with tracing
    @app.flow(
        name="DataProcessingPipeline",
        description="Complete data processing pipeline with analysis, reporting, and QA"
    )
    async def data_processing_pipeline():
        # This will be automatically traced as a workflow
        pass
    
    # 6. Start enterprise services
    print("⚡ Starting enterprise services...")
    async with app:
        print("✅ Enterprise services started")
        
        # 7. Create a demo user for security context
        demo_user = User(
            username="demo_analyst",
            email="analyst@company.com"
        )
        
        # 8. Execute workflows with full enterprise features
        print("\n🔬 Executing enterprise workflows...")
        
        async with app.run_context(user=demo_user) as ctx:
            print("📊 Running data processing pipeline...")
            
            # Step 1: Data Analysis
            data_input = "Sales data: Q1: $100k, Q2: $150k, Q3: $200k, Q4: $180k. Customer satisfaction: 85%"
            
            analysis_result = await ctx.call_agent(
                "DataAnalyst",
                data_input
            )
            print(f"   📈 Analysis: {analysis_result.content[:100]}...")
            
            # Step 2: Report Generation
            report_result = await ctx.call_agent(
                "ReportGenerator",
                f"Create a report based on this analysis: {analysis_result.content}"
            )
            print(f"   📋 Report: {report_result.content[:100]}...")
            
            # Step 3: Quality Assurance
            qa_result = await ctx.call_agent(
                "QualityAssurance",
                f"Review this report: {report_result.content}"
            )
            print(f"   ✅ QA Review: {qa_result.content[:100]}...")
        
        # 9. Demonstrate enterprise analytics
        print("\n📊 Retrieving enterprise analytics...")
        
        # Real-time analytics
        real_time = await app.get_real_time_analytics()
        print(f"   🔄 Real-time metrics:")
        if "real_time" in real_time:
            rt_data = real_time["real_time"]
            print(f"      • Success rate: {rt_data.get('success_rate', 0):.1f}%")
            print(f"      • Avg response time: {rt_data.get('avg_response_time_ms', 0):.1f}ms")
            print(f"      • Total requests: {rt_data.get('total_requests', 0)}")
        
        # Agent analytics
        agent_analytics = await app.get_agent_analytics()
        if "agents" in agent_analytics:
            print(f"   🤖 Agent performance:")
            for agent_name, stats in agent_analytics["agents"].items():
                print(f"      • {agent_name}: {stats.get('success_rate', 0):.1f}% success, {stats.get('total_calls', 0)} calls")
        
        # Cost analytics
        cost_analytics = await app.get_cost_analytics("24h")
        if "total_cost_usd" in cost_analytics:
            print(f"   💰 Cost analysis:")
            print(f"      • Total cost: ${cost_analytics['total_cost_usd']:.4f}")
            print(f"      • Daily average: ${cost_analytics.get('cost_trends', {}).get('daily_average', 0):.4f}")
        
        # Workflow traces
        traces = await app.search_workflow_traces(limit=5)
        if traces:
            print(f"   🔍 Recent workflow traces: {len(traces)} found")
            for trace in traces[:2]:  # Show first 2
                print(f"      • {trace['workflow_name']}: {trace['status']} ({trace.get('spans', []) and len(trace['spans'])} spans)")
        
        # 10. Export analytics
        print("\n📤 Exporting analytics data...")
        export_data = await app.export_analytics(format="json", time_range="24h")
        if "export_info" in export_data:
            print(f"   ✅ Export completed: {export_data['export_info']['timestamp']}")
            print(f"   📊 Included: {len(export_data)} data sections")
        
        # 11. Health check
        health = await app.health_check()
        print(f"\n🏥 System health: {'✅ Healthy' if health.get('healthy') else '❌ Unhealthy'}")
        if health.get('components'):
            print("   Component status:")
            for component, status in health['components'].items():
                status_icon = "✅" if status.get('healthy') else "❌"
                print(f"      • {component}: {status_icon}")
    
    print("\n🎉 Enhanced enterprise demo completed successfully!")
    print("\n📚 Features demonstrated:")
    print("   ✅ Enhanced enterprise application")
    print("   ✅ Automatic workflow tracing")
    print("   ✅ Real-time analytics dashboard")
    print("   ✅ Agent performance monitoring")
    print("   ✅ Cost tracking and analysis")
    print("   ✅ Security context with user management")
    print("   ✅ Comprehensive audit logging")
    print("   ✅ Multi-agent workflow orchestration")
    print("   ✅ Data export capabilities")
    print("   ✅ Health monitoring")


if __name__ == "__main__":
    asyncio.run(main())