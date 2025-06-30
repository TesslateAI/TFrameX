# Discussion Pattern - TFrameX Pattern Example

Demonstrates collaborative agent discussions where multiple agents engage in iterative dialogue to reach consensus, explore different perspectives, or solve complex problems through multi-agent conversation.

## 🎯 What You'll Learn

- **Multi-Agent Dialogue**: Facilitating conversations between multiple agents
- **Perspective Synthesis**: Combining different viewpoints into unified insights
- **Consensus Building**: Reaching agreement through structured discussion
- **Discussion Moderation**: Guiding productive multi-agent conversations
- **Collaborative Problem-Solving**: Leveraging diverse expertise through dialogue

## 📁 Project Structure

```
discussion-pattern/
├── README.md              # This guide
├── requirements.txt       # Dependencies
├── .env.example          # Environment template
├── main.py               # Main application
└── docs/
    └── discussion_flows.md # Advanced discussion patterns
```

## 🚀 Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your LLM settings

# Run the example
python main.py
```

## 🗣️ Discussion Pattern Architecture

```
                    Discussion Topic
                          │
                          ▼
                 DiscussionModerator
                    (Facilitator)
                          │
        ┌─────────────────┼─────────────────┐
        ▼                 ▼                 ▼
   OptimistAgent    RealistAgent    SkepticalAgent
   (Opportunities)   (Practical)     (Risks)
        │                 │                 │
        └─────────────────┼─────────────────┘
                          ▼
                  CreativeAgent
                   (Innovation)
                          │
                          ▼
                 ConsensusBuilder
                  (Synthesis)
                          │
                          ▼
                 Final Agreement
```

### **Collaborative Discussion Flow**
1. **Moderation**: DiscussionModerator sets agenda and guides process
2. **Multi-Perspective Input**: Various agents share diverse viewpoints
3. **Iterative Dialogue**: Multiple rounds of discussion and refinement
4. **Synthesis**: ConsensusBuilder integrates perspectives into unified outcomes

## 💻 Example Usage

### **Business Strategy Discussion**
```python
# Topic: "Should we invest in AI automation for customer service?"
#
# Round 1 - Initial Perspectives:
# → OptimistAgent: "Great opportunity for efficiency and 24/7 support!"
# → RealistAgent: "Need to consider implementation costs and training"
# → SkepticalAgent: "Risk of losing personal touch with customers"
# → CreativeAgent: "What about hybrid AI-human approach?"
#
# Round 2 - Synthesis:
# → ConsensusBuilder: "Phased implementation with human oversight..."
# → Final Decision: Balanced approach addressing all concerns
```

## 🎮 Demo Modes

### **1. Business Strategy Discussion**
Complete strategic decision-making discussion:
```bash
python main.py
# Select option 1
```

### **2. Product Development Discussion**
Feature prioritization through collaborative dialogue:
```bash
python main.py
# Select option 2
```

### **3. Crisis Management Discussion**
Multi-round crisis response planning:
```bash
python main.py
# Select option 3
```

### **4. Individual Perspective Analysis**
See how different agents approach the same question:
```bash
python main.py
# Select option 4
```

### **5. Consensus Building Demo**
Watch consensus emerge from diverse viewpoints:
```bash
python main.py
# Select option 5
```

### **6. Interactive Discussion Mode**
Join the discussion as a participant:
```bash
python main.py
# Select option 6
```

## 📊 Discussion Pattern Benefits

### **🎯 Comprehensive Analysis**
- Multiple expert perspectives
- Thorough exploration of options
- Reduced blind spots and bias
- More robust decision-making

### **🤝 Consensus Building**
- Structured path to agreement
- Address all stakeholder concerns
- Build buy-in and commitment
- Create win-win solutions

### **💡 Creative Problem-Solving**
- Diverse thinking approaches
- Cross-pollination of ideas
- Breakthrough insights
- Innovation through collaboration

### **⚖️ Balanced Outcomes**
- Consider multiple viewpoints
- Weigh pros and cons thoroughly
- Mitigate risks while pursuing opportunities
- Make well-rounded decisions

## 🏗️ Building Discussion Systems

### **1. Define Discussion Roles**
```python
@app.agent(
    name="ModeratorAgent",
    description="Facilitates productive discussion",
    system_prompt="Guide conversation, ensure participation, drive consensus..."
)
async def moderator_agent():
    pass

@app.agent(
    name="PerspectiveAgent",
    description="Represents specific viewpoint", 
    system_prompt="Focus on [specific perspective]: opportunities, risks, practicality..."
)
async def perspective_agent():
    pass
```

### **2. Create Discussion Flow**
```python
async def facilitate_discussion(topic: str, rounds: int = 3):
    async with app.run_context() as rt:
        for round_num in range(rounds):
            # Moderator guides
            moderator_result = await rt.call_agent("ModeratorAgent", topic)
            
            # Participants contribute
            for participant in participants:
                result = await rt.call_agent(participant, topic)
                
            # Synthesize round
            synthesis = await rt.call_agent("ConsensusBuilder", topic)
```

### **3. Manage Discussion Flow**
```python
class DiscussionManager:
    def __init__(self, participants: List[str]):
        self.participants = participants
        self.discussion_history = []
    
    async def run_discussion(self, topic: str) -> str:
        # Implement structured discussion logic
        pass
```

## 🎯 Use Cases

### **🏢 Strategic Planning**
- Business strategy decisions
- Investment evaluations
- Market entry planning
- Resource allocation

### **🚀 Product Development**
- Feature prioritization
- Design decisions
- Technology choices
- User experience planning

### **⚖️ Policy Making**
- Regulatory compliance
- Ethics considerations
- Risk management
- Stakeholder alignment

### **🔄 Process Improvement**
- Workflow optimization
- Quality enhancement
- Efficiency initiatives
- Change management

## 🔧 Advanced Discussion Patterns

### **Structured Debate Format**
```python
@app.agent(
    name="DebateModerator",
    system_prompt="""
    Moderate a structured debate:
    1. Opening statements from each side
    2. Argument exchange rounds
    3. Rebuttal opportunities  
    4. Closing arguments
    5. Final synthesis
    """
)
```

### **Devil's Advocate Pattern**
```python
@app.agent(
    name="DevilsAdvocate", 
    system_prompt="""
    Challenge the emerging consensus by:
    - Questioning assumptions
    - Identifying weaknesses
    - Proposing alternative views
    - Stress-testing decisions
    """
)
```

### **Socratic Method Discussion**
```python
@app.agent(
    name="SocraticModerator",
    system_prompt="""
    Guide discussion through questions:
    - Ask probing questions
    - Challenge assumptions
    - Draw out implications
    - Lead to insights through inquiry
    """
)
```

## 📈 Discussion Optimization

### **Participant Balance**
- Ensure diverse perspectives
- Avoid dominant voices
- Encourage equal participation
- Manage group dynamics

### **Flow Management**
- Set clear discussion structure
- Monitor progress toward goals
- Keep conversations focused
- Prevent endless loops

### **Quality Control**
- Ensure substantive contributions
- Prevent superficial responses
- Maintain professional dialogue
- Drive toward actionable outcomes

## 🔍 Discussion Evaluation

### **Consensus Quality Metrics**
```python
def evaluate_consensus(discussion_output: str) -> dict:
    return {
        "agreement_level": assess_agreement(discussion_output),
        "concern_coverage": check_concerns_addressed(discussion_output),
        "actionability": evaluate_actionable_outcomes(discussion_output),
        "stakeholder_satisfaction": rate_stakeholder_buy_in(discussion_output)
    }
```

### **Participation Analysis**
```python
def analyze_participation(discussion_log: List[dict]) -> dict:
    return {
        "contribution_balance": measure_equal_participation(discussion_log),
        "perspective_diversity": assess_viewpoint_variety(discussion_log),
        "quality_of_input": rate_contribution_substance(discussion_log)
    }
```

### **Decision Quality Assessment**
- Comprehensiveness of analysis
- Stakeholder concern integration
- Implementation feasibility
- Risk mitigation effectiveness

## 🚀 What's Next?

After mastering discussion patterns:

1. **Advanced Integration**: [Content Creation Pipeline](../../04-advanced-examples/content-creation-pipeline/)
2. **Real-World Applications**: [Legal Document Analysis](../../05-real-world-examples/legal-document-analysis/)
3. **Complex Workflows**: [DevOps Incident Response](../../05-real-world-examples/devops-incident-response/)
4. **Build Custom Discussions**: Create your own collaborative agent systems

## 💡 Best Practices

### **Design Principles**
- **Clear Roles**: Define distinct perspectives and responsibilities
- **Structured Process**: Use consistent discussion frameworks
- **Balanced Participation**: Ensure all voices are heard
- **Outcome Focus**: Drive toward actionable decisions

### **Implementation Tips**
- Start with 3-4 distinct perspectives
- Use a strong moderator to guide flow
- Build in synthesis and consensus steps
- Test with various topic complexities

### **Common Pitfalls**
- Avoid echo chambers (too similar perspectives)
- Don't let discussions become endless
- Ensure moderator remains neutral
- Plan for when consensus isn't reached

## 📚 Further Reading

- [TFrameX Discussion Patterns Guide](https://docs.tframex.com/patterns/discussion)
- [Multi-Agent Coordination](https://docs.tframex.com/coordination)
- [Consensus Building Strategies](https://docs.tframex.com/consensus)

## 📄 License

This example is provided under the MIT License.