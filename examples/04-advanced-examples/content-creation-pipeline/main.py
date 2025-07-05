#!/usr/bin/env python3
"""
TFrameX Content Creation Pipeline - Advanced Example

Demonstrates a sophisticated content creation workflow that combines multiple 
TFrameX patterns to create high-quality content from ideation to publication. 
This example showcases sequential flows, parallel analysis, routing, and 
collaborative review processes.

Pipeline Features:
- Multi-stage content development
- Parallel research and analysis
- Intelligent content routing by type
- Collaborative review and editing
- SEO optimization and formatting
- Quality assurance and publication readiness
"""

import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from dotenv import load_dotenv
from tframex import TFrameX, Message, Flow
from tframex.llms import OpenAILLM
from tframex.memory import InMemoryMemoryStore

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize TFrameX app
app = TFrameX(
    default_llm=OpenAILLM(),
    default_memory_store_factory=InMemoryMemoryStore
)

# ===== CONTENT STRATEGY AGENTS =====

@app.agent(
    name="ContentStrategist",
    description="Develops content strategy, target audience analysis, and content planning",
    system_prompt="""
    You are a senior content strategist responsible for:
    
    1. **Audience Analysis**: Define target demographics, pain points, and content preferences
    2. **Content Planning**: Structure content for maximum engagement and value
    3. **Strategic Positioning**: Align content with business objectives and brand voice
    4. **Competitive Analysis**: Position content effectively in the market landscape
    5. **Success Metrics**: Define KPIs and success criteria for content
    
    DELIVERABLES:
    - Target audience profile
    - Content structure and outline  
    - Key messaging and positioning
    - Success metrics and goals
    - Brand voice and tone guidelines
    
    Focus on strategic thinking and data-driven insights.
    """
)
async def content_strategist():
    """Develops content strategy and planning."""
    pass

@app.agent(
    name="TopicResearcher", 
    description="Conducts comprehensive topic research and fact-checking",
    system_prompt="""
    You are a thorough researcher specializing in:
    
    1. **Topic Investigation**: Deep dive into subject matter and current trends
    2. **Fact Verification**: Ensure accuracy and credibility of information
    3. **Source Collection**: Gather authoritative and diverse sources
    4. **Data Analysis**: Extract insights from research findings
    5. **Context Building**: Provide comprehensive background information
    
    RESEARCH APPROACH:
    - Use multiple authoritative sources
    - Verify claims and statistics
    - Identify current trends and developments
    - Gather supporting evidence and examples
    - Note any controversial or debated aspects
    
    Provide well-researched, factual, and comprehensive information.
    """
)
async def topic_researcher():
    """Conducts comprehensive topic research."""
    pass

@app.agent(
    name="ContentRouter",
    description="Routes content to appropriate specialist writers based on content type and complexity",
    system_prompt="""
    You are a content routing specialist. Analyze the content request and route to the appropriate writer:
    
    ROUTING RULES:
    - Technical/educational content → "TechnicalWriter"
    - Marketing/promotional content → "MarketingWriter" 
    - Creative/storytelling content → "CreativeWriter"
    - News/informational content → "NewsWriter"
    - Business/professional content → "BusinessWriter"
    
    Consider factors:
    - Content complexity and technical depth
    - Target audience sophistication
    - Purpose (educate, persuade, entertain, inform)
    - Tone and style requirements
    
    Respond with ONLY the writer name that should handle this content.
    """
)
async def content_router():
    """Routes content to appropriate specialist writers."""
    pass

# ===== SPECIALIST WRITERS =====

@app.agent(
    name="TechnicalWriter",
    description="Creates clear, accurate technical and educational content",
    system_prompt="""
    You are an expert technical writer specializing in:
    
    - Complex technical concepts made accessible
    - Educational and instructional content
    - How-to guides and tutorials
    - Product documentation and specifications
    - Scientific and research-based writing
    
    WRITING STYLE:
    - Clear, precise, and well-structured
    - Use examples and analogies for complex concepts
    - Include step-by-step instructions when appropriate
    - Maintain accuracy while ensuring readability
    - Use appropriate technical terminology with explanations
    
    Create content that educates and empowers readers.
    """
)
async def technical_writer():
    """Creates technical and educational content."""
    pass

@app.agent(
    name="MarketingWriter",
    description="Creates persuasive marketing and promotional content",
    system_prompt="""
    You are a skilled marketing writer focused on:
    
    - Compelling value propositions
    - Persuasive copy that drives action
    - Brand messaging and positioning
    - Customer-focused benefits
    - Conversion-optimized content
    
    WRITING STYLE:
    - Benefit-driven and customer-focused
    - Persuasive but authentic
    - Clear calls-to-action
    - Emotional connection with audience
    - Features translated into benefits
    
    Create content that engages prospects and drives conversions.
    """
)
async def marketing_writer():
    """Creates marketing and promotional content."""
    pass

@app.agent(
    name="CreativeWriter",
    description="Creates engaging creative and storytelling content",
    system_prompt="""
    You are a creative writer specializing in:
    
    - Storytelling and narrative content
    - Creative and engaging prose
    - Brand storytelling and case studies
    - Entertainment and lifestyle content
    - Unique voice and personality
    
    WRITING STYLE:
    - Engaging and memorable
    - Strong narrative structure
    - Vivid imagery and descriptions
    - Emotional resonance
    - Unique voice and creativity
    
    Create content that captivates and inspires readers.
    """
)
async def creative_writer():
    """Creates creative and storytelling content."""
    pass

@app.agent(
    name="NewsWriter",
    description="Creates timely, factual news and informational content",
    system_prompt="""
    You are a news writer focused on:
    
    - Timely and relevant information
    - Fact-based objective reporting
    - Current events and industry news
    - Interview and quote integration
    - Newsworthy angle development
    
    WRITING STYLE:
    - Clear, concise, and objective
    - Lead with most important information
    - Use quotes and attributions
    - Maintain journalistic integrity
    - Focus on who, what, when, where, why
    
    Create content that informs and updates readers.
    """
)
async def news_writer():
    """Creates news and informational content."""
    pass

@app.agent(
    name="BusinessWriter",
    description="Creates professional business and thought leadership content",
    system_prompt="""
    You are a business writer specializing in:
    
    - Thought leadership and insights
    - Business strategy and analysis
    - Professional industry content
    - Executive communications
    - B2B focused messaging
    
    WRITING STYLE:
    - Professional and authoritative
    - Data-driven and analytical
    - Strategic insights and implications
    - Executive-level perspective
    - Industry expertise demonstration
    
    Create content that establishes authority and professional credibility.
    """
)
async def business_writer():
    """Creates business and professional content."""
    pass

# ===== CONTENT OPTIMIZATION AGENTS =====

@app.agent(
    name="SEOOptimizer",
    description="Optimizes content for search engines while maintaining readability",
    system_prompt="""
    You are an SEO optimization specialist focused on:
    
    1. **Keyword Integration**: Natural keyword placement and semantic SEO
    2. **Content Structure**: Headers, meta descriptions, and SEO-friendly formatting
    3. **Readability**: Maintain quality while optimizing for search
    4. **Technical SEO**: URL structure, internal linking opportunities
    5. **Featured Snippets**: Structure content for SERP features
    
    OPTIMIZATION APPROACH:
    - Integrate keywords naturally
    - Create compelling meta descriptions
    - Use proper header hierarchy (H1, H2, H3)
    - Optimize for user intent and search queries
    - Suggest internal and external linking opportunities
    
    Balance SEO optimization with user experience and content quality.
    """
)
async def seo_optimizer():
    """Optimizes content for search engines."""
    pass

@app.agent(
    name="ContentEditor",
    description="Reviews and improves content for clarity, flow, and quality", 
    system_prompt="""
    You are a professional content editor specializing in:
    
    1. **Structural Editing**: Overall organization, flow, and logical progression
    2. **Copy Editing**: Grammar, style, clarity, and consistency
    3. **Fact Checking**: Verify claims, statistics, and references
    4. **Tone Alignment**: Ensure voice matches brand and audience
    5. **Quality Assurance**: Final polish and publication readiness
    
    EDITING APPROACH:
    - Improve clarity and readability
    - Enhance logical flow and structure
    - Correct grammar and style issues
    - Ensure consistency in tone and voice
    - Verify factual accuracy
    
    Focus on elevating content quality while preserving the author's intent.
    """
)
async def content_editor():
    """Reviews and improves content quality."""
    pass

@app.agent(
    name="QualityAssurance",
    description="Performs final quality check and publication readiness assessment",
    system_prompt="""
    You are a quality assurance specialist responsible for:
    
    1. **Final Review**: Comprehensive quality assessment
    2. **Brand Compliance**: Ensure alignment with brand guidelines
    3. **Publication Readiness**: Confirm content meets all requirements
    4. **Error Detection**: Final check for any remaining issues
    5. **Approval Decision**: Determine if content is ready for publication
    
    QUALITY CRITERIA:
    - Accuracy and factual correctness
    - Brand voice and tone consistency
    - Technical and grammatical perfection
    - Audience appropriateness
    - Objective achievement
    
    Provide final approval or specific recommendations for improvement.
    """
)
async def quality_assurance():
    """Performs final quality assurance check."""
    pass

# ===== CONTENT CREATION FLOWS =====

# Create the main content creation pipeline
content_pipeline = Flow(
    flow_name="ContentCreationPipeline",
    description="Comprehensive content creation from strategy to publication"
)

# Sequential pipeline stages
content_pipeline.add_step("ContentStrategist")  # Strategy and planning
content_pipeline.add_step("TopicResearcher")   # Research and fact-checking
content_pipeline.add_step("ContentRouter")     # Route to appropriate writer
# Note: Dynamic writer selection happens in execution logic
content_pipeline.add_step("SEOOptimizer")      # SEO optimization
content_pipeline.add_step("ContentEditor")     # Editorial review
content_pipeline.add_step("QualityAssurance")  # Final QA

app.register_flow(content_pipeline)

# ===== PIPELINE EXECUTION FUNCTIONS =====

async def execute_content_pipeline(content_brief: str, content_type: str = "auto") -> Dict:
    """
    Execute the complete content creation pipeline.
    
    Args:
        content_brief: Description of the content to create
        content_type: Type hint for content routing (optional)
        
    Returns:
        Dictionary containing all pipeline outputs
    """
    pipeline_results = {}
    
    async with app.run_context() as rt:
        print(f"🚀 Starting Content Creation Pipeline")
        print(f"📝 Brief: {content_brief}")
        print("=" * 60)
        
        # Stage 1: Strategy Development
        print("\n📊 Stage 1: Content Strategy Development")
        strategy_input = Message(role="user", content=f"Develop a content strategy for: {content_brief}")
        strategy_result = await rt.call_agent("ContentStrategist", strategy_input)
        pipeline_results["strategy"] = strategy_result.current_message.content
        print(f"✅ Strategy: {strategy_result.current_message.content[:100]}...")
        
        # Stage 2: Research
        print("\n🔍 Stage 2: Topic Research")
        research_input = Message(role="user", content=f"Research this topic comprehensively: {content_brief}")
        research_result = await rt.call_agent("TopicResearcher", research_input)
        pipeline_results["research"] = research_result.current_message.content
        print(f"✅ Research: {research_result.current_message.content[:100]}...")
        
        # Stage 3: Content Routing
        print("\n🎯 Stage 3: Content Routing")
        if content_type == "auto":
            routing_input = Message(role="user", content=f"Route this content request: {content_brief}")
            routing_result = await rt.call_agent("ContentRouter", routing_input)
            selected_writer = routing_result.current_message.content.strip()
        else:
            selected_writer = f"{content_type.title()}Writer"
        
        pipeline_results["selected_writer"] = selected_writer
        print(f"✅ Routed to: {selected_writer}")
        
        # Stage 4: Content Writing
        print(f"\n✍️  Stage 4: Content Writing ({selected_writer})")
        writing_context = f"""
        Content Brief: {content_brief}
        Strategy: {pipeline_results['strategy']}
        Research: {pipeline_results['research']}
        
        Create the content based on this information.
        """
        writing_input = Message(role="user", content=writing_context)
        writing_result = await rt.call_agent(selected_writer, writing_input)
        pipeline_results["content"] = writing_result.current_message.content
        print(f"✅ Content: {writing_result.current_message.content[:100]}...")
        
        # Stage 5: SEO Optimization
        print("\n🔎 Stage 5: SEO Optimization")
        seo_input = Message(role="user", content=f"Optimize this content for SEO: {pipeline_results['content']}")
        seo_result = await rt.call_agent("SEOOptimizer", seo_input)
        pipeline_results["seo_optimized"] = seo_result.current_message.content
        print(f"✅ SEO Optimized: {seo_result.current_message.content[:100]}...")
        
        # Stage 6: Editorial Review
        print("\n📝 Stage 6: Editorial Review")
        editing_input = Message(role="user", content=f"Edit and improve this content: {pipeline_results['seo_optimized']}")
        editing_result = await rt.call_agent("ContentEditor", editing_input)
        pipeline_results["edited_content"] = editing_result.current_message.content
        print(f"✅ Edited: {editing_result.current_message.content[:100]}...")
        
        # Stage 7: Quality Assurance
        print("\n🔍 Stage 7: Quality Assurance")
        qa_input = Message(role="user", content=f"Perform final quality check: {pipeline_results['edited_content']}")
        qa_result = await rt.call_agent("QualityAssurance", qa_input)
        pipeline_results["qa_assessment"] = qa_result.current_message.content
        print(f"✅ QA Assessment: {qa_result.current_message.content[:100]}...")
        
        # Pipeline completion
        pipeline_results["pipeline_completed"] = datetime.now().isoformat()
        print(f"\n🎉 Content Pipeline Completed Successfully!")
        
    return pipeline_results

async def parallel_content_analysis(content_brief: str) -> Dict:
    """
    Demonstrate parallel analysis for content planning.
    
    Args:
        content_brief: Content description for analysis
        
    Returns:
        Dictionary with parallel analysis results
    """
    print(f"⚡ Parallel Content Analysis")
    print(f"📝 Brief: {content_brief}")
    print("=" * 50)
    
    analysis_results = {}
    
    async with app.run_context() as rt:
        # Parallel analysis by different specialists
        analysis_tasks = [
            ("ContentStrategist", "strategy_analysis"),
            ("TopicResearcher", "research_analysis"), 
            ("SEOOptimizer", "seo_analysis"),
            ("ContentEditor", "editorial_analysis")
        ]
        
        # Execute analyses in parallel
        tasks = []
        for agent_name, result_key in analysis_tasks:
            input_msg = Message(role="user", content=f"Analyze this content request: {content_brief}")
            task = rt.call_agent(agent_name, input_msg)
            tasks.append((task, result_key))
        
        # Collect results
        for task, result_key in tasks:
            result = await task
            analysis_results[result_key] = result.current_message.content
            agent_name = result_key.replace("_analysis", "").title()
            print(f"✅ {agent_name}: {result.current_message.content[:80]}...")
    
    return analysis_results

# ===== DEMO FUNCTIONS =====

async def demo_full_pipeline():
    """Demonstrate the complete content creation pipeline."""
    print("🏭 Full Content Creation Pipeline Demo")
    print("=" * 50)
    
    content_brief = "Create a comprehensive guide about implementing remote work policies for small businesses, including best practices, tools, and management strategies"
    
    results = await execute_content_pipeline(content_brief)
    
    print("\n📋 Pipeline Summary:")
    print("-" * 30)
    for stage, content in results.items():
        if stage != "pipeline_completed":
            print(f"📌 {stage.title()}: {len(content)} characters")

async def demo_content_types():
    """Demonstrate routing to different content types."""
    print("\n🎭 Content Type Routing Demo")
    print("=" * 50)
    
    content_requests = [
        ("How to optimize database performance for web applications", "technical"),
        ("Launch announcement for our new AI-powered analytics platform", "marketing"),
        ("The inspiring story of how our startup overcame early challenges", "creative"),
        ("Industry report: Q4 trends in cybersecurity investments", "business")
    ]
    
    async with app.run_context() as rt:
        for brief, expected_type in content_requests:
            print(f"\n📝 Request: {brief[:50]}...")
            
            # Get routing decision
            routing_input = Message(role="user", content=brief)
            routing_result = await rt.call_agent("ContentRouter", routing_input)
            selected_writer = routing_result.current_message.content.strip()
            
            print(f"   ➡️  Routed to: {selected_writer}")
            print(f"   ✅ Expected: {expected_type.title()}Writer")

async def demo_parallel_analysis():
    """Demonstrate parallel content analysis."""
    print("\n⚡ Parallel Analysis Demo")
    print("=" * 50)
    
    content_brief = "Create content about the future of artificial intelligence in healthcare"
    
    results = await parallel_content_analysis(content_brief)
    
    print(f"\n📊 Analysis Summary:")
    print("-" * 30)
    for analysis_type, content in results.items():
        print(f"📌 {analysis_type.replace('_', ' ').title()}: {len(content)} characters")

async def demo_quality_stages():
    """Demonstrate the quality improvement stages."""
    print("\n🔧 Quality Improvement Stages Demo")
    print("=" * 50)
    
    # Start with basic content
    initial_content = """
    AI is good for businesses. It help with many thing like customer service and data.
    Company should use AI because its the future. AI save time and money.
    """
    
    async with app.run_context() as rt:
        print("📝 Initial Content:")
        print(initial_content)
        
        # SEO Optimization
        print(f"\n🔎 SEO Optimization:")
        seo_input = Message(role="user", content=f"Optimize this content for SEO: {initial_content}")
        seo_result = await rt.call_agent("SEOOptimizer", seo_input)
        seo_content = seo_result.current_message.content
        print(seo_content[:200] + "...")
        
        # Editorial Review
        print(f"\n📝 Editorial Review:")
        edit_input = Message(role="user", content=f"Edit and improve this content: {seo_content}")
        edit_result = await rt.call_agent("ContentEditor", edit_input)
        edited_content = edit_result.current_message.content
        print(edited_content[:200] + "...")
        
        # Quality Assurance
        print(f"\n🔍 Quality Assessment:")
        qa_input = Message(role="user", content=f"Assess quality and publication readiness: {edited_content}")
        qa_result = await rt.call_agent("QualityAssurance", qa_input)
        print(qa_result.current_message.content[:200] + "...")

async def demo_interactive_pipeline():
    """Interactive content creation pipeline."""
    print("\n💬 Interactive Content Pipeline")
    print("=" * 50)
    print("Describe the content you'd like to create:")
    print("(e.g., 'blog post about sustainable business practices')")
    
    user_brief = input("\nContent Brief: ").strip()
    if not user_brief:
        user_brief = "blog post about the benefits of remote work for productivity"
        print(f"Using default: {user_brief}")
    
    print("\nSelect content type (or 'auto' for automatic routing):")
    print("1. Technical  2. Marketing  3. Creative  4. News  5. Business  6. Auto")
    
    type_choice = input("Choice (1-6): ").strip()
    type_map = {
        "1": "technical", "2": "marketing", "3": "creative",
        "4": "news", "5": "business", "6": "auto"
    }
    content_type = type_map.get(type_choice, "auto")
    
    print(f"\n🚀 Creating content: '{user_brief}' (Type: {content_type})")
    
    results = await execute_content_pipeline(user_brief, content_type)
    
    print(f"\n📄 Final Content Preview:")
    print("-" * 40)
    final_content = results.get("edited_content", results.get("content", ""))
    print(final_content[:500] + "..." if len(final_content) > 500 else final_content)

# ===== MAIN DEMO =====

async def main():
    """Main demo function with user choices."""
    print("🏭 TFrameX Content Creation Pipeline")
    print("=" * 50)
    print("This advanced example demonstrates a complete content")
    print("creation workflow from strategy to publication,")
    print("showcasing multiple TFrameX patterns working together.\n")
    
    while True:
        print("Choose a demo:")
        print("1. 🏭 Full Content Creation Pipeline")
        print("2. 🎭 Content Type Routing Demo")
        print("3. ⚡ Parallel Analysis Demo")
        print("4. 🔧 Quality Improvement Stages")
        print("5. 💬 Interactive Content Pipeline")
        print("6. ❌ Exit")
        
        choice = input("\nEnter your choice (1-6): ").strip()
        
        if choice == "1":
            await demo_full_pipeline()
        elif choice == "2":
            await demo_content_types()
        elif choice == "3":
            await demo_parallel_analysis()
        elif choice == "4":
            await demo_quality_stages()
        elif choice == "5":
            await demo_interactive_pipeline()
        elif choice == "6":
            print("👋 Goodbye!")
            break
        else:
            print("❌ Invalid choice. Please try again.\n")

if __name__ == "__main__":
    asyncio.run(main())