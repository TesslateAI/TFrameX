#!/usr/bin/env python3
"""
TFrameX Discussion Pattern Example

Demonstrates collaborative agent discussions where multiple agents engage in 
iterative dialogue to reach consensus, explore different perspectives, or 
solve complex problems through multi-agent conversation.

This example shows:
- Multi-agent discussion facilitation
- Iterative consensus building
- Perspective synthesis and debate
- Discussion moderation and flow control
- Collaborative problem-solving
"""

import asyncio
import logging
from pathlib import Path
from typing import List, Optional

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

# ===== DISCUSSION PARTICIPANTS =====

@app.agent(
    name="DiscussionModerator",
    description="Facilitates discussions, guides conversation flow, and ensures productive dialogue",
    system_prompt="""
    You are a skilled discussion moderator. Your role is to:
    
    1. **Facilitate Discussion**: Guide the conversation to stay on topic and be productive
    2. **Encourage Participation**: Ensure all participants contribute meaningfully
    3. **Synthesize Views**: Identify common ground and key differences
    4. **Drive Consensus**: Help the group reach decisions or conclusions
    5. **Manage Flow**: Control the pace and structure of the discussion
    
    MODERATION STYLE:
    - Ask clarifying questions when needed
    - Summarize key points periodically
    - Identify when consensus is reached
    - Redirect when discussion goes off-track
    - Encourage respectful debate of ideas
    
    When moderating, be neutral but decisive in guiding the process.
    """
)
async def discussion_moderator():
    """Moderates and facilitates multi-agent discussions."""
    pass

@app.agent(
    name="OptimistAgent",
    description="Presents positive perspectives and identifies opportunities",
    system_prompt="""
    You are an optimistic team member who:
    
    - Focuses on opportunities and positive outcomes
    - Highlights potential benefits and advantages
    - Encourages creative and ambitious thinking
    - Builds on others' ideas constructively
    - Maintains enthusiasm and forward momentum
    
    Your perspective is valuable for:
    - Identifying growth opportunities
    - Encouraging innovation and risk-taking
    - Building team confidence
    - Finding silver linings in challenges
    - Inspiring ambitious goals
    
    Be genuinely optimistic but not naive. Base your optimism on realistic assessment.
    """
)
async def optimist_agent():
    """Provides optimistic perspectives and opportunity identification."""
    pass

@app.agent(
    name="RealistAgent", 
    description="Provides balanced, practical perspectives based on facts and experience",
    system_prompt="""
    You are a practical realist who:
    
    - Bases opinions on facts and evidence
    - Considers practical constraints and limitations
    - Evaluates both pros and cons objectively
    - Draws from experience and precedent
    - Focuses on feasible and actionable solutions
    
    Your perspective is valuable for:
    - Grounding discussions in reality
    - Identifying practical considerations
    - Evaluating resource requirements
    - Assessing implementation challenges
    - Ensuring feasible outcomes
    
    Be balanced and objective. Help the team make realistic decisions.
    """
)
async def realist_agent():
    """Provides realistic, fact-based perspectives."""
    pass

@app.agent(
    name="SkepticalAgent",
    description="Identifies risks, challenges, and potential problems",
    system_prompt="""
    You are a constructive skeptic who:
    
    - Identifies potential risks and pitfalls
    - Questions assumptions and challenges ideas
    - Highlights possible negative consequences
    - Ensures thorough risk assessment
    - Advocates for careful consideration
    
    Your perspective is valuable for:
    - Risk identification and mitigation
    - Preventing costly mistakes
    - Ensuring thorough analysis
    - Challenging groupthink
    - Improving decision quality
    
    Be constructively skeptical, not pessimistic. Your goal is to improve outcomes.
    """
)
async def skeptical_agent():
    """Provides skeptical analysis and risk identification."""
    pass

@app.agent(
    name="CreativeAgent",
    description="Generates innovative ideas and unconventional solutions",
    system_prompt="""
    You are a creative innovator who:
    
    - Generates novel ideas and approaches
    - Thinks outside conventional boundaries
    - Combines concepts in unique ways
    - Challenges traditional assumptions
    - Inspires breakthrough thinking
    
    Your perspective is valuable for:
    - Generating innovative solutions
    - Breaking through creative blocks
    - Finding unconventional approaches
    - Inspiring new possibilities
    - Challenging status quo thinking
    
    Be imaginative and bold. Help the team explore new possibilities.
    """
)
async def creative_agent():
    """Provides creative and innovative perspectives."""
    pass

@app.agent(
    name="ConsensusBuilder",
    description="Synthesizes different viewpoints and builds agreement",
    system_prompt="""
    You are a consensus builder who:
    
    - Identifies areas of agreement across perspectives
    - Finds compromises that address key concerns
    - Synthesizes different viewpoints into unified solutions
    - Builds bridges between opposing positions
    - Facilitates win-win outcomes
    
    Your perspective is valuable for:
    - Resolving conflicts and disagreements
    - Finding common ground
    - Creating unified action plans
    - Balancing competing interests
    - Building team alignment
    
    Focus on synthesis and integration. Help create solutions everyone can support.
    """
)
async def consensus_builder():
    """Builds consensus and synthesizes viewpoints."""
    pass

# ===== DISCUSSION FLOWS =====

async def facilitate_discussion(topic: str, rounds: int = 3) -> List[str]:
    """
    Facilitate a structured discussion on a given topic.
    
    Args:
        topic: The discussion topic
        rounds: Number of discussion rounds
        
    Returns:
        List of discussion outputs from each round
    """
    discussion_history = []
    
    async with app.run_context() as rt:
        print(f"🗣️ Starting discussion on: {topic}")
        print("=" * 60)
        
        # Initial input
        initial_message = Message(role="user", content=f"Let's discuss: {topic}")
        
        for round_num in range(1, rounds + 1):
            print(f"\n📝 Round {round_num}")
            print("-" * 40)
            
            # Moderator sets the stage
            if round_num == 1:
                moderator_prompt = f"Introduce the topic '{topic}' and invite initial perspectives from all participants."
            else:
                moderator_prompt = f"Moderate round {round_num} of our discussion on '{topic}'. Build on previous insights and guide toward consensus."
            
            moderator_input = Message(role="user", content=moderator_prompt)
            moderator_result = await rt.call_agent("DiscussionModerator", moderator_input)
            print(f"🎯 Moderator: {moderator_result.current_message.content}")
            
            # Each participant contributes
            participants = ["OptimistAgent", "RealistAgent", "SkepticalAgent", "CreativeAgent"]
            
            for participant in participants:
                participant_input = Message(role="user", content=f"Share your perspective on: {topic}")
                participant_result = await rt.call_agent(participant, participant_input)
                agent_name = participant.replace("Agent", "")
                print(f"💭 {agent_name}: {participant_result.current_message.content}")
            
            # Consensus builder synthesizes
            synthesis_prompt = f"Synthesize the perspectives shared in round {round_num} on '{topic}'."
            synthesis_input = Message(role="user", content=synthesis_prompt)
            synthesis_result = await rt.call_agent("ConsensusBuilder", synthesis_input)
            print(f"🤝 Synthesis: {synthesis_result.current_message.content}")
            
            discussion_history.append(synthesis_result.current_message.content)
    
    return discussion_history

# ===== DEMO FUNCTIONS =====

async def demo_business_strategy_discussion():
    """Demonstrate discussion pattern for business strategy decisions."""
    print("🏢 Business Strategy Discussion Demo")
    print("=" * 50)
    
    topic = "Should our company invest in AI automation for customer service?"
    
    await facilitate_discussion(topic, rounds=2)

async def demo_product_development_discussion():
    """Demonstrate discussion pattern for product development decisions."""
    print("\n🚀 Product Development Discussion Demo")
    print("=" * 50)
    
    topic = "How should we prioritize features for our mobile app's next major release?"
    
    await facilitate_discussion(topic, rounds=2)

async def demo_crisis_management_discussion():
    """Demonstrate discussion pattern for crisis management."""
    print("\n🚨 Crisis Management Discussion Demo")  
    print("=" * 50)
    
    topic = "Our main competitor just launched a similar product at half our price. How do we respond?"
    
    await facilitate_discussion(topic, rounds=3)

async def demo_individual_perspectives():
    """Show how different agents approach the same question."""
    print("\n🎭 Individual Perspective Analysis")
    print("=" * 50)
    
    question = "Should we expand our business to international markets next year?"
    
    agents = [
        ("OptimistAgent", "Optimist"), 
        ("RealistAgent", "Realist"),
        ("SkepticalAgent", "Skeptical"),
        ("CreativeAgent", "Creative")
    ]
    
    async with app.run_context() as rt:
        for agent_name, display_name in agents:
            input_msg = Message(role="user", content=question)
            result = await rt.call_agent(agent_name, input_msg)
            print(f"💭 {display_name}: {result.current_message.content}\n")

async def demo_consensus_building():
    """Demonstrate consensus building from diverse perspectives."""
    print("\n🤝 Consensus Building Demo")
    print("=" * 50)
    
    # Simulate a complex decision with multiple viewpoints
    perspectives = [
        "We should definitely expand internationally - huge growth opportunity!",
        "International expansion requires careful planning and significant resources.",
        "The risks are substantial - currency fluctuations, regulatory complexity, cultural barriers.",
        "What if we started with strategic partnerships instead of direct expansion?"
    ]
    
    async with app.run_context() as rt:
        print("📝 Given perspectives:")
        for i, perspective in enumerate(perspectives, 1):
            print(f"   {i}. {perspective}")
        
        consensus_prompt = f"""
        Build consensus from these diverse perspectives on international expansion:
        {chr(10).join(f'{i}. {p}' for i, p in enumerate(perspectives, 1))}
        
        Find common ground and create a unified recommendation.
        """
        
        input_msg = Message(role="user", content=consensus_prompt)
        result = await rt.call_agent("ConsensusBuilder", input_msg)
        print(f"\n🤝 Consensus: {result.current_message.content}")

async def demo_interactive_discussion():
    """Interactive discussion mode where user can participate."""
    print("\n💬 Interactive Discussion Mode")
    print("=" * 50)
    print("Join the discussion! You can ask questions or share opinions.")
    print("Type 'quit' to exit.\n")
    
    print("🎯 Current Topic: Future of Remote Work")
    
    async with app.run_context() as rt:
        # Set up the discussion
        moderator_input = Message(role="user", content="Introduce a discussion about the future of remote work.")
        moderator_result = await rt.call_agent("DiscussionModerator", moderator_input)
        print(f"🎯 Moderator: {moderator_result.current_message.content}\n")
        
        while True:
            user_input = input("You: ").strip()
            if user_input.lower() in ['quit', 'exit', 'q']:
                break
                
            if not user_input:
                continue
            
            try:
                # Get responses from different perspectives
                agents = [
                    ("OptimistAgent", "Optimist"),
                    ("RealistAgent", "Realist"), 
                    ("SkepticalAgent", "Skeptical")
                ]
                
                for agent_name, display_name in agents:
                    input_msg = Message(role="user", content=user_input)
                    result = await rt.call_agent(agent_name, input_msg)
                    print(f"💭 {display_name}: {result.current_message.content}")
                
                # Moderator provides synthesis
                mod_input = Message(role="user", content=f"Moderate this exchange about: {user_input}")
                mod_result = await rt.call_agent("DiscussionModerator", mod_input)
                print(f"🎯 Moderator: {mod_result.current_message.content}\n")
                
            except Exception as e:
                print(f"❌ Error: {e}\n")

# ===== MAIN DEMO =====

async def main():
    """Main demo function with user choices."""
    print("🗣️ TFrameX Discussion Pattern Example")
    print("=" * 50)
    print("This example demonstrates multi-agent discussions")
    print("where agents collaborate to explore topics,")
    print("debate perspectives, and reach consensus.\n")
    
    while True:
        print("Choose a demo:")
        print("1. 🏢 Business Strategy Discussion")
        print("2. 🚀 Product Development Discussion") 
        print("3. 🚨 Crisis Management Discussion")
        print("4. 🎭 Individual Perspective Analysis")
        print("5. 🤝 Consensus Building Demo")
        print("6. 💬 Interactive Discussion Mode")
        print("7. ❌ Exit")
        
        choice = input("\nEnter your choice (1-7): ").strip()
        
        if choice == "1":
            await demo_business_strategy_discussion()
        elif choice == "2":
            await demo_product_development_discussion()
        elif choice == "3":
            await demo_crisis_management_discussion()
        elif choice == "4":
            await demo_individual_perspectives()
        elif choice == "5":
            await demo_consensus_building()
        elif choice == "6":
            await demo_interactive_discussion()
        elif choice == "7":
            print("👋 Goodbye!")
            break
        else:
            print("❌ Invalid choice. Please try again.\n")

if __name__ == "__main__":
    asyncio.run(main())