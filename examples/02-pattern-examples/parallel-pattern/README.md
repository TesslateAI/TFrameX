# Parallel Pattern - TFrameX Pattern Example

Demonstrates concurrent agent execution where multiple agents work simultaneously on the same input, and their results are aggregated. Perfect for multi-perspective analysis, competitive solutions, and independent task execution.

## 🎯 What You'll Learn

- **Parallel Execution**: Multiple agents working simultaneously
- **Result Aggregation**: Combining outputs from parallel agents
- **Multi-Perspective Analysis**: Different viewpoints on the same problem
- **Performance Benefits**: Faster processing through concurrency
- **Synthesis Patterns**: Merging parallel results into unified insights

## 📁 Project Structure

```
parallel-pattern/
├── README.md              # This guide
├── requirements.txt       # Dependencies
├── .env.example          # Environment template
├── main.py               # Main application
└── docs/
    └── parallel_flows.md  # Parallel design patterns
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

## ⚡ Parallel Pattern Architecture

```
                    Input
                      │
        ┌─────────────┼─────────────┐
        ▼             ▼             ▼
   Agent 1       Agent 2       Agent 3
(Technical)    (Business)       (UX)
        │             │             │
        └─────────────┼─────────────┘
                      ▼
              Synthesis Agent
                      │
                      ▼
                Final Output
```

### **Multi-Perspective Analysis Pipeline**
1. **Parallel Analysis**: Technical, Business, UX, and Risk analysts work simultaneously
2. **Synthesis**: Results are combined into comprehensive insights
3. **Final Report**: Unified analysis with balanced perspectives

## 💻 Example Usage

### **Business Analysis Flow**
```python
# Input: "Implement AI-powered customer service chatbot"
#
# Parallel Analysis:
# ┌─ TechnicalAnalyst: Architecture, implementation, scalability
# ├─ BusinessAnalyst: ROI, market impact, competitive advantage  
# ├─ UXAnalyst: User experience, adoption, interface design
# └─ RiskAnalyst: Security, compliance, operational risks
#
# Synthesis:
# → Combines all perspectives
# → Identifies conflicts and synergies
# → Provides balanced recommendations
```

## 🎮 Demo Modes

### **1. Parallel Analysis Flow**
Complete multi-perspective analysis:
```bash
python main.py
# Select option 1
```

### **2. Individual Analyst Outputs**
See each analyst's perspective separately:
```bash
python main.py
# Select option 2
```

### **3. Interactive Chat**
Chat with the synthesis coordinator:
```bash
python main.py
# Select option 3
```

## 📊 Parallel Pattern Benefits

### **⚡ Performance**
- Faster processing through concurrency
- Multiple agents work simultaneously
- Reduced total execution time

### **🎯 Comprehensive Analysis**
- Multiple expert perspectives
- Reduced bias through diversity
- More thorough coverage

### **🔄 Independent Processing**
- Agents don't influence each other
- Pure, unbiased viewpoints
- Parallel problem-solving approaches

### **📈 Scalability**
- Easy to add more parallel agents
- Distribute workload effectively
- Handle complex multi-faceted problems

## 🏗️ Building Parallel Flows

### **1. Define Parallel Agents**
```python
@app.agent(
    name="AnalystA",
    description="Specialized perspective A",
    system_prompt="Focus on aspect A of the problem..."
)
async def analyst_a():
    pass

@app.agent(
    name="AnalystB", 
    description="Specialized perspective B",
    system_prompt="Focus on aspect B of the problem..."
)
async def analyst_b():
    pass
```

### **2. Create Parallel Pattern**
```python
from tframex import Flow, ParallelPattern

# Create flow with parallel pattern
analysis_flow = Flow(
    flow_name="ParallelAnalysisFlow",
    description="Multi-perspective parallel analysis"
)

# Add parallel pattern
analysis_flow.add_step(
    ParallelPattern(
        pattern_name="MultiAnalysis",
        tasks=["AnalystA", "AnalystB", "AnalystC"]
    )
)

# Optional: Add synthesis step
analysis_flow.add_step("SynthesisAgent")
```

### **3. Execute Parallel Flow**
```python
async with app.run_context() as rt:
    input_message = Message(role="user", content="Analyze this...")
    result = await rt.run_flow("ParallelAnalysisFlow", input_message)
    print(result.current_message.content)
```

## 🎯 Use Cases

### **📊 Business Analysis**
- Multi-stakeholder perspectives
- Risk and opportunity assessment
- Investment decision analysis
- Strategic planning

### **🔍 Research & Development**
- Competitive analysis
- Technology evaluation
- Market research
- Feasibility studies

### **🎨 Creative Projects**
- Design alternatives
- Creative brainstorming
- Multiple solution approaches
- Artistic perspectives

### **⚖️ Decision Making**
- Pro/con analysis
- Multiple expert opinions
- Consensus building
- Balanced evaluations

## 🔧 Advanced Patterns

### **Weighted Synthesis**
```python
@app.agent(
    name="WeightedSynthesizer",
    system_prompt="""
    Synthesize the parallel analyses, giving different weights based on:
    - Technical feasibility: 30%
    - Business value: 40% 
    - User experience: 20%
    - Risk factors: 10%
    """
)
async def weighted_synthesizer():
    pass
```

### **Competitive Approaches**
```python
# Multiple agents solving the same problem differently
parallel_flow.add_step(
    ParallelPattern(
        pattern_name="CompetitiveSolutions",
        tasks=["ApproachA", "ApproachB", "ApproachC"]
    )
)
```

### **Staged Parallel Processing**
```python
# Multiple rounds of parallel processing
flow.add_step(ParallelPattern(tasks=["Phase1A", "Phase1B"]))
flow.add_step(ParallelPattern(tasks=["Phase2A", "Phase2B"]))
flow.add_step("FinalSynthesis")
```

## 📈 Performance Considerations

### **Concurrency Benefits**
- True parallel execution
- Faster than sequential processing
- Better resource utilization

### **Resource Management**
- Monitor LLM API rate limits
- Balance parallel load
- Consider token usage across agents

### **Optimization Strategies**
- Group similar analysis types
- Use appropriate timeouts
- Implement result caching

## 🔍 Result Synthesis Patterns

### **Consensus Building**
```python
@app.agent(
    name="ConsensusBuilder",
    system_prompt="""
    Find common ground between the parallel analyses:
    1. Identify areas of agreement
    2. Highlight conflicting viewpoints
    3. Propose compromise solutions
    4. Build unified recommendations
    """
)
```

### **Conflict Resolution**
```python
@app.agent(
    name="ConflictResolver", 
    system_prompt="""
    When parallel analyses conflict:
    1. Identify the source of disagreement
    2. Evaluate the merits of each position
    3. Propose resolution strategies
    4. Make evidence-based recommendations
    """
)
```

### **Balanced Reporting**
```python
@app.agent(
    name="BalancedReporter",
    system_prompt="""
    Create a balanced report that:
    1. Presents all perspectives fairly
    2. Highlights trade-offs and considerations
    3. Provides clear recommendations
    4. Acknowledges uncertainties and limitations
    """
)
```

## 🚀 What's Next?

After mastering parallel patterns:

1. **Try Router Patterns**: [Router Pattern Example](../router-pattern/)
2. **Explore Discussion Patterns**: [Discussion Pattern Example](../discussion-pattern/)
3. **Advanced Applications**: [Content Creation Pipeline](../../04-advanced-examples/content-creation-pipeline/)
4. **Build Custom Flows**: Create your own parallel workflows

## 💡 Best Practices

### **Design Principles**
- **Independence**: Ensure parallel agents don't depend on each other
- **Diversity**: Use agents with genuinely different perspectives
- **Clarity**: Make synthesis clear and actionable
- **Balance**: Give appropriate weight to different viewpoints

### **Implementation Tips**
- Start with 2-3 parallel agents
- Test agents individually first
- Plan synthesis strategy carefully
- Monitor performance and resource usage

### **Common Pitfalls**
- Avoid redundant parallel agents
- Don't neglect the synthesis step
- Consider API rate limits
- Plan for partial failures

## 📚 Further Reading

- [TFrameX Parallel Patterns Guide](https://docs.tframex.com/patterns/parallel)
- [Performance Optimization](https://docs.tframex.com/performance)
- [Result Aggregation Strategies](https://docs.tframex.com/aggregation)

## 📄 License

This example is provided under the MIT License.