# Router Pattern - TFrameX Pattern Example

Demonstrates intelligent request routing where incoming requests are dynamically routed to specialized agents based on content analysis. Perfect for handling diverse inputs that require different types of expertise.

## 🎯 What You'll Learn

- **Intelligent Routing**: Dynamic agent selection based on content
- **Content Classification**: Analyzing requests to determine expertise needed
- **Specialist Agents**: Domain-specific expert agents
- **Fallback Handling**: Graceful handling of unclassified requests
- **Scalable Architecture**: Easy addition of new routing rules and agents

## 📁 Project Structure

```
router-pattern/
├── README.md              # This guide
├── requirements.txt       # Dependencies
├── .env.example          # Environment template
├── main.py               # Main application
└── docs/
    └── routing_strategies.md # Advanced routing patterns
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

## 🔀 Router Pattern Architecture

```
                    Input Request
                         │
                         ▼
                  RequestRouter
                   (Analyzer)
                         │
        ┌────────────────┼────────────────┐
        ▼                ▼                ▼
   TechnicalAgent   CreativeAgent    BusinessAgent
   (Programming)    (Writing)        (Strategy)
        │                │                │
        └────────────────┼────────────────┘
                         ▼
                    Final Response
```

### **Intelligent Routing System**
1. **Content Analysis**: RequestRouter analyzes incoming requests
2. **Dynamic Routing**: Routes to appropriate specialist agent
3. **Expert Response**: Specialist provides domain-specific expertise
4. **Fallback Support**: GeneralAgent handles unclassified requests

## 💻 Example Usage

### **Request Routing Flow**
```python
# Input: "How do I optimize my database queries?"
#
# Step 1 - RequestRouter:
# → Analyzes: "database queries" + "optimize"
# → Classification: Technical/Programming
# → Routes to: TechnicalAgent
#
# Step 2 - TechnicalAgent:
# → Provides: Database optimization techniques
# → Includes: Code examples and best practices
# → Returns: Expert technical advice
```

## 🎮 Demo Modes

### **1. Router Flow Demo**
Automated routing with multiple example requests:
```bash
python main.py
# Select option 1
```

### **2. Individual Routing Analysis**
See routing decisions for various request types:
```bash
python main.py
# Select option 2
```

### **3. Interactive Chat**
Chat with automatic intelligent routing:
```bash
python main.py
# Select option 3
```

## 📊 Router Pattern Benefits

### **🎯 Intelligent Distribution**
- Automatic expert selection
- Content-based routing decisions
- Optimal agent utilization
- Reduced response time

### **🔧 Scalable Expertise**
- Easy addition of new specialists
- Domain-specific knowledge
- Specialized system prompts
- Expert-level responses

### **🛡️ Robust Handling**
- Fallback for unclassified requests
- Error recovery mechanisms
- Graceful degradation
- Comprehensive coverage

### **📈 Performance Optimization**
- Direct routing to experts
- Reduced processing overhead
- Efficient resource utilization
- Faster response times

## 🏗️ Building Router Systems

### **1. Define Specialist Agents**
```python
@app.agent(
    name="SpecialistAgent",
    description="Expert in specific domain",
    system_prompt="You are an expert in [domain]. Focus on..."
)
async def specialist_agent():
    pass
```

### **2. Create Router Logic**
```python
@app.agent(
    name="RequestRouter",
    system_prompt="""
    Analyze requests and route to specialists:
    - Technical questions → TechnicalAgent
    - Creative tasks → CreativeAgent
    - Business strategy → BusinessAgent
    - Fallback → GeneralAgent
    """
)
async def request_router():
    pass
```

### **3. Implement Routing Flow**
```python
async def route_and_process(request: str):
    async with app.run_context() as rt:
        # Get routing decision
        router_input = Message(role="user", content=request)
        router_result = await rt.call_agent("RequestRouter", router_input)
        selected_agent = router_result.current_message.content.strip()
        
        # Call selected specialist
        response = await rt.call_agent(selected_agent, router_input)
        return response.current_message.content
```

## 🎯 Use Cases

### **📞 Customer Support**
- Route inquiries to appropriate departments
- Technical, billing, sales specialists
- Escalation path management
- Automated triage systems

### **📝 Content Management**
- Route content by type and complexity
- Writing, editing, technical documentation
- Multi-language content routing
- Quality-specific handling

### **🔍 Research & Analysis**
- Route questions to domain experts
- Technical, business, market research
- Specialized analysis requirements
- Expert opinion aggregation

### **🏢 Enterprise Applications**
- Department-specific routing
- Expertise-based distribution
- Workflow optimization
- Resource allocation

## 🔧 Advanced Routing Patterns

### **Multi-Level Routing**
```python
@app.agent(
    name="Level1Router",
    system_prompt="Route to department: Tech, Business, Creative, or General"
)

@app.agent(
    name="TechRouter", 
    system_prompt="Route technical requests: Backend, Frontend, DevOps, or Database"
)
```

### **Confidence-Based Routing**
```python
@app.agent(
    name="ConfidenceRouter",
    system_prompt="""
    Route based on confidence:
    - High confidence (90%+): Direct to specialist
    - Medium confidence (70-90%): Route with fallback
    - Low confidence (<70%): Route to GeneralAgent
    """
)
```

### **Priority-Based Routing**
```python
@app.agent(
    name="PriorityRouter",
    system_prompt="""
    Route based on urgency and importance:
    - Critical: Route to senior specialists
    - High: Route to regular specialists  
    - Normal: Route to appropriate agent
    - Low: Queue for batch processing
    """
)
```

## 📈 Routing Optimization

### **Classification Accuracy**
- Train router on diverse examples
- Use clear routing criteria
- Implement feedback loops
- Monitor routing decisions

### **Performance Tuning**
- Optimize routing agent prompts
- Cache routing decisions
- Parallel routing evaluation
- Fast specialist selection

### **Specialist Management**
- Balance specialist workloads
- Monitor agent performance
- Dynamic specialist scaling
- Expert availability tracking

## 🔍 Debugging Router Systems

### **Routing Analysis**
```python
# Track routing decisions
routing_log = []

async def debug_routing(request: str):
    router_result = await rt.call_agent("RequestRouter", request)
    selected_agent = router_result.current_message.content
    
    routing_log.append({
        "request": request,
        "selected_agent": selected_agent,
        "timestamp": datetime.now()
    })
```

### **Routing Statistics**
```python
# Analyze routing patterns
def analyze_routing_stats():
    agent_usage = {}
    for entry in routing_log:
        agent = entry["selected_agent"]
        agent_usage[agent] = agent_usage.get(agent, 0) + 1
    
    print("Agent Usage Statistics:")
    for agent, count in agent_usage.items():
        print(f"  {agent}: {count} requests")
```

### **Routing Validation**
- Test with diverse request types
- Validate specialist responses
- Check routing consistency
- Monitor misclassification rates

## 🚀 What's Next?

After mastering router patterns:

1. **Try Discussion Patterns**: [Discussion Pattern Example](../discussion-pattern/)
2. **Advanced Routing**: [Smart Home Orchestration](../../04-advanced-examples/smart-home-orchestration/)
3. **Multi-Agent Systems**: [DevOps Incident Response](../../05-real-world-examples/devops-incident-response/)
4. **Build Custom Routers**: Create your own intelligent routing systems

## 💡 Best Practices

### **Design Principles**
- **Clear Categories**: Define distinct specialist domains
- **Fallback Strategy**: Always provide fallback options
- **Routing Transparency**: Make routing decisions visible
- **Expert Quality**: Ensure specialists are truly expert-level

### **Implementation Tips**
- Start with 3-5 specialist categories
- Use clear, unambiguous routing criteria
- Test routing accuracy extensively
- Monitor and adjust routing rules

### **Common Pitfalls**
- Avoid overlapping specialist domains
- Don't over-complicate routing logic
- Ensure fallback agent is robust
- Monitor for routing bias

## 📚 Further Reading

- [TFrameX Routing Patterns Guide](https://docs.tframex.com/patterns/routing)
- [Agent Specialization](https://docs.tframex.com/agents/specialization)
- [Dynamic Flow Control](https://docs.tframex.com/flows/dynamic)

## 📄 License

This example is provided under the MIT License.