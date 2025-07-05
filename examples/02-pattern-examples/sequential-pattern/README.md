# Sequential Pattern - TFrameX Pattern Example

Demonstrates step-by-step agent execution where each agent processes the output of the previous agent in sequence. Perfect for content creation pipelines, data processing workflows, and multi-stage analysis.

## 🎯 What You'll Learn

- **Sequential Workflows**: Step-by-step agent execution
- **Data Flow**: How information passes between agents
- **Flow Orchestration**: Using TFrameX Flow and patterns
- **Pipeline Design**: Creating effective processing pipelines
- **Content Creation**: Real-world content development workflow

## 📁 Project Structure

```
sequential-pattern/
├── README.md              # This guide
├── requirements.txt       # Dependencies
├── .env.example          # Environment template
├── main.py               # Main application
└── docs/
    └── sequential_flows.md # Flow design patterns
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

## 🔄 Sequential Pattern Architecture

```
Input → Agent 1 → Agent 2 → Agent 3 → Final Output
        ↓         ↓         ↓
     Step 1    Step 2    Step 3
    (Plan)    (Write)   (Edit)
```

### **Content Creation Pipeline**
1. **ContentPlanner**: Analyzes topic and creates structured plan
2. **ContentWriter**: Writes content based on the plan
3. **ContentEditor**: Reviews and improves the content

## 💻 Example Usage

### **Content Creation Flow**
```python
# Input: "Create a blog post about renewable energy for small businesses"
# 
# Step 1 - ContentPlanner:
# → Analyzes topic
# → Identifies target audience  
# → Creates content structure
# → Defines key points
#
# Step 2 - ContentWriter:
# → Takes the plan from Step 1
# → Writes engaging content
# → Follows the structure
# → Expands on key points
#
# Step 3 - ContentEditor:
# → Takes the content from Step 2
# → Reviews for grammar and style
# → Improves clarity and flow
# → Provides final polished version
```

## 🎮 Demo Modes

### **1. Content Creation Flow**
Complete automated content creation pipeline:
```bash
python main.py
# Select option 1
```

### **2. Step-by-Step Process**
See each individual step in the sequence:
```bash
python main.py
# Select option 2
```

### **3. Interactive Chat**
Chat with individual agents:
```bash
python main.py  
# Select option 3
```

## 📊 Sequential Pattern Benefits

### **🔗 Clear Data Flow**
- Each step builds on the previous
- Transparent progression
- Easy to debug and optimize

### **🎯 Specialized Agents** 
- Each agent has a focused role
- Expertise in specific tasks
- Reusable across different flows

### **📈 Quality Improvement**
- Iterative refinement
- Multiple passes for quality
- Structured improvement process

### **🔧 Maintainable Workflows**
- Easy to modify individual steps
- Add or remove agents as needed
- Clear separation of concerns

## 🏗️ Building Sequential Flows

### **1. Define Agent Roles**
```python
@app.agent(
    name="StepOneAgent",
    description="First step in the process",
    system_prompt="Your role in the sequential process..."
)
async def step_one_agent():
    pass
```

### **2. Create the Flow**
```python
# Create sequential flow
workflow = Flow(
    flow_name="MySequentialFlow",
    description="Step-by-step processing workflow"
)

# Add steps in order
workflow.add_step("StepOneAgent")
workflow.add_step("StepTwoAgent") 
workflow.add_step("StepThreeAgent")

# Register with app
app.register_flow(workflow)
```

### **3. Execute the Flow**
```python
async with app.run_context() as rt:
    initial_input = Message(role="user", content="Process this...")
    result = await rt.run_flow("MySequentialFlow", initial_input)
    print(result.current_message.content)
```

## 🎯 Use Cases

### **📝 Content Creation**
- Blog post writing
- Report generation
- Documentation creation
- Marketing copy development

### **📊 Data Processing**
- Data cleaning pipelines
- Analysis workflows
- Report generation
- Quality assurance processes

### **🔍 Analysis Workflows**
- Research processes
- Due diligence workflows
- Assessment procedures
- Evaluation pipelines

### **🎨 Creative Processes**
- Story development
- Design workflows
- Product development
- Creative reviews

## 🔧 Advanced Patterns

### **Conditional Steps**
```python
# Add conditional logic within agents
@app.agent(
    name="ConditionalAgent",
    system_prompt="If the content needs revision, suggest improvements. Otherwise, approve it."
)
async def conditional_agent():
    pass
```

### **Error Handling**
```python
# Agents can handle errors and provide feedback
@app.agent(
    name="RobustAgent", 
    system_prompt="If the previous step failed, provide alternative approach or error correction."
)
async def robust_agent():
    pass
```

### **Quality Gates**
```python
# Agents can act as quality checkpoints
@app.agent(
    name="QualityGate",
    system_prompt="Review the work and only pass it forward if it meets quality standards."
)
async def quality_gate():
    pass
```

## 📈 Performance Optimization

### **Agent Efficiency**
- Keep system prompts focused
- Use clear, specific instructions
- Minimize unnecessary processing

### **Flow Design**
- Optimize the number of steps
- Balance specialization vs overhead
- Consider parallel alternatives for independent tasks

### **Memory Management**
- Use appropriate history limits
- Clear unnecessary context
- Manage token usage efficiently

## 🔍 Debugging Sequential Flows

### **Step-by-Step Analysis**
```python
# Run each step individually to identify issues
step1_result = await rt.call_agent("Agent1", input_message)
step2_result = await rt.call_agent("Agent2", step1_result)
step3_result = await rt.call_agent("Agent3", step2_result)
```

### **Flow Context Inspection**
```python
# Examine flow context at each step
flow_context = await rt.run_flow("MyFlow", input_message)
print("History:", flow_context.history)
print("Shared Data:", flow_context.shared_data)
```

### **Logging and Monitoring**
- Enable detailed logging
- Monitor agent performance
- Track success/failure rates
- Measure processing times

## 🚀 What's Next?

After mastering sequential patterns:

1. **Try Parallel Patterns**: [Parallel Pattern Example](../parallel-pattern/)
2. **Explore Router Patterns**: [Router Pattern Example](../router-pattern/)
3. **Advanced Workflows**: [Code Review System](../../04-advanced-examples/code-review-system/)
4. **Build Custom Flows**: Create your own sequential workflows

## 💡 Best Practices

### **Design Principles**
- **Single Responsibility**: Each agent should have one clear purpose
- **Clear Interfaces**: Define what each agent expects and produces
- **Error Resilience**: Plan for failures and edge cases
- **Testability**: Make each step independently testable

### **Implementation Tips**
- Start with simple 2-3 step flows
- Test each agent individually first
- Use descriptive agent names and descriptions
- Document the flow purpose and expected outcomes

## 📚 Further Reading

- [TFrameX Flow Documentation](https://docs.tframex.com/flows)
- [Agent Design Patterns](https://docs.tframex.com/patterns)
- [Workflow Orchestration Guide](https://docs.tframex.com/orchestration)

## 📄 License

This example is provided under the MIT License.