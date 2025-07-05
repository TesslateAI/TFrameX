---
sidebar_position: 3
title: Agents
---

# Agents API Reference

Agents are the core autonomous entities in TFrameX that can use tools, maintain conversations, and work together to solve complex tasks. This reference covers all agent types and their APIs.

## Base Agent Class

All agents inherit from the base `Agent` class:

```python
from tframex.agents.base import Agent

class Agent:
    def __init__(
        self,
        name: str,
        description: str,
        tools: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Base agent class.
        
        Args:
            name: Unique identifier for the agent
            description: Human-readable description
            tools: List of tool names this agent can use
            metadata: Additional metadata
        """
```

### Common Properties

```python
# Agent properties
agent.name          # Unique identifier
agent.description   # Human-readable description
agent.tools        # List of available tool names
agent.metadata     # Custom metadata dictionary
```

## LLMAgent

The standard agent implementation powered by language models.

```python
from tframex.agents.llm_agent import LLMAgent
from tframex.util.llms import OpenAIChatLLM

class LLMAgent(Agent):
    def __init__(
        self,
        name: str,
        description: str,
        llm: BaseLLM,
        system_prompt: str = "",
        tools: Optional[List[str]] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        response_format: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        LLM-powered agent.
        
        Args:
            name: Unique agent identifier
            description: Agent description
            llm: Language model instance
            system_prompt: System instructions for the agent
            tools: List of tool names
            temperature: Sampling temperature (0-2)
            max_tokens: Maximum response length
            response_format: Output format ("text" or "json")
            metadata: Additional metadata
        """
```

### Basic Usage

```python
# Create an LLM agent
agent = LLMAgent(
    name="DataAnalyst",
    description="Analyzes data and creates insights",
    llm=OpenAIChatLLM(model_name="gpt-4"),
    system_prompt="""You are a data analyst expert.
    
    Your responsibilities:
    - Analyze data accurately
    - Provide clear insights
    - Create visualizations when helpful
    - Explain findings in simple terms
    """,
    tools=["read_csv", "analyze_stats", "create_chart"],
    temperature=0.3  # Lower temperature for analytical tasks
)

# Register with app
app.register_agent(agent)
```

### Advanced Configuration

```python
# JSON output format
structured_agent = LLMAgent(
    name="APIAgent",
    description="Returns structured data",
    llm=llm,
    response_format="json",
    system_prompt="""Return all responses as valid JSON:
    {
        "status": "success|error",
        "data": <response_data>,
        "metadata": {...}
    }
    """
)

# Token limits
concise_agent = LLMAgent(
    name="Summarizer",
    description="Creates concise summaries",
    llm=llm,
    max_tokens=150,
    system_prompt="Provide brief, concise summaries."
)

# Custom metadata
agent_with_meta = LLMAgent(
    name="SpecialAgent",
    description="Agent with custom metadata",
    llm=llm,
    metadata={
        "version": "1.0",
        "capabilities": ["research", "analysis"],
        "department": "R&D"
    }
)
```

## DelegatorAgent

Agents that can delegate tasks to other agents.

```python
from tframex.agents.delegator import DelegatorAgent

class DelegatorAgent(LLMAgent):
    def __init__(
        self,
        name: str,
        description: str,
        llm: BaseLLM,
        agents: List[str],
        system_prompt: str = "",
        delegation_strategy: str = "best_match",
        max_delegations: int = 5,
        **kwargs
    ):
        """
        Agent that delegates to other agents.
        
        Args:
            name: Unique identifier
            description: Agent description
            llm: Language model instance
            agents: List of agent names to delegate to
            system_prompt: System instructions
            delegation_strategy: How to choose delegates
            max_delegations: Maximum delegation depth
        """
```

### Delegation Strategies

```python
# Best match delegation (default)
supervisor = DelegatorAgent(
    name="Supervisor",
    description="Manages team of specialized agents",
    llm=llm,
    agents=["Researcher", "Writer", "Reviewer"],
    delegation_strategy="best_match",
    system_prompt="""You are a project supervisor.
    
    Delegate tasks to:
    - Researcher: For gathering information
    - Writer: For creating content
    - Reviewer: For quality checks
    """
)

# Round-robin delegation
load_balancer = DelegatorAgent(
    name="LoadBalancer",
    description="Distributes work evenly",
    llm=llm,
    agents=["Worker1", "Worker2", "Worker3"],
    delegation_strategy="round_robin"
)

# Capability-based delegation
smart_delegator = DelegatorAgent(
    name="SmartDelegator",
    description="Delegates based on capabilities",
    llm=llm,
    agents=["DataAgent", "WebAgent", "FileAgent"],
    delegation_strategy="capability_match",
    system_prompt="""Match tasks to agent capabilities:
    - DataAgent: Handles CSV, JSON, databases
    - WebAgent: Handles web searches, APIs
    - FileAgent: Handles file operations
    """
)
```

### Hierarchical Structures

```python
# Multi-level hierarchy
ceo = DelegatorAgent(
    name="CEO",
    description="Top-level executive",
    llm=llm,
    agents=["CTO", "CFO", "CMO"]
)

cto = DelegatorAgent(
    name="CTO",
    description="Technology executive",
    llm=llm,
    agents=["LeadDev", "LeadOps", "LeadQA"]
)

lead_dev = DelegatorAgent(
    name="LeadDev",
    description="Development team lead",
    llm=llm,
    agents=["BackendDev", "FrontendDev", "MobileDev"]
)

# Register all in hierarchy
for agent in [ceo, cto, lead_dev, ...]:
    app.register_agent(agent)
```

## Agent as Tool

Enable agents to call other agents as tools.

```python
# Create specialist agent
specialist = LLMAgent(
    name="SQLExpert",
    description="SQL query specialist",
    llm=llm,
    system_prompt="You are a SQL expert. Write optimal queries."
)

# Register as both agent and tool
app.register_agent(specialist)

# Another agent can now use it
analyst = LLMAgent(
    name="DataAnalyst",
    description="General data analyst",
    llm=llm,
    tools=["SQLExpert"],  # Can call the SQL expert
    system_prompt="""When you need complex SQL queries,
    use the SQLExpert tool for assistance."""
)
```

## Custom Agent Implementation

Create custom agent types by extending the base class:

```python
from tframex.agents.base import Agent

class RuleBasedAgent(Agent):
    """Custom agent using rule-based logic."""
    
    def __init__(self, name: str, description: str, rules: Dict[str, str]):
        super().__init__(name, description)
        self.rules = rules
    
    async def run(self, prompt: str, runtime: Runtime) -> str:
        """Execute based on rules."""
        for pattern, response in self.rules.items():
            if pattern.lower() in prompt.lower():
                return response
        return "No matching rule found."

# Use custom agent
rule_agent = RuleBasedAgent(
    name="RuleBot",
    description="Responds based on rules",
    rules={
        "hello": "Hi there! How can I help?",
        "weather": "I cannot check weather, but it's probably nice!",
        "help": "I can respond to: hello, weather, help"
    }
)

app.register_agent(rule_agent)
```

## Agent Communication

### Direct Communication

```python
# Agent-to-agent communication via runtime
async with app.run_context() as rt:
    # Agent calls another agent
    research = await rt.call_agent("Researcher", "Find info on AI")
    summary = await rt.call_agent("Summarizer", f"Summarize: {research}")
```

### Shared Context

```python
# Pass context between agents
async with app.run_context() as rt:
    # First agent produces data
    data = await rt.call_agent(
        "DataCollector", 
        "Collect sales data",
        context={"period": "Q4 2023"}
    )
    
    # Second agent uses the data
    analysis = await rt.call_agent(
        "Analyst",
        "Analyze the collected data",
        context={"data": data, "focus": "trends"}
    )
```

### Conversation Memory

```python
# Agents with conversation memory
chatbot = LLMAgent(
    name="ChatBot",
    description="Conversational agent with memory",
    llm=llm,
    system_prompt="""You are a helpful chatbot.
    Remember previous messages in our conversation."""
)

async with app.run_context() as rt:
    # Conversation maintains context
    await rt.call_agent("ChatBot", "My name is Alice")
    response = await rt.call_agent("ChatBot", "What's my name?")
    # Bot remembers: "Your name is Alice"
```

## Agent Patterns

### Specialist Pattern

```python
# Create specialized agents
agents = [
    LLMAgent(
        name="PythonExpert",
        description="Python programming specialist",
        llm=llm,
        system_prompt="You are a Python expert. Provide Pythonic solutions."
    ),
    LLMAgent(
        name="JavaScriptExpert",
        description="JavaScript programming specialist",
        llm=llm,
        system_prompt="You are a JavaScript expert. Provide modern JS solutions."
    ),
    LLMAgent(
        name="DatabaseExpert",
        description="Database design specialist",
        llm=llm,
        system_prompt="You are a database expert. Design efficient schemas."
    )
]

# Register all specialists
for agent in agents:
    app.register_agent(agent)

# Supervisor to coordinate
supervisor = DelegatorAgent(
    name="TechLead",
    description="Technical team lead",
    llm=llm,
    agents=["PythonExpert", "JavaScriptExpert", "DatabaseExpert"]
)
```

### Pipeline Pattern

```python
# Agents in a processing pipeline
agents = {
    "Validator": "Validate and clean input data",
    "Processor": "Process validated data",
    "Formatter": "Format processed results",
    "Reporter": "Generate final report"
}

for name, description in agents.items():
    agent = LLMAgent(
        name=name,
        description=description,
        llm=llm,
        system_prompt=f"You are responsible for: {description}"
    )
    app.register_agent(agent)

# Use in pipeline
async def data_pipeline(data):
    async with app.run_context() as rt:
        validated = await rt.call_agent("Validator", f"Validate: {data}")
        processed = await rt.call_agent("Processor", f"Process: {validated}")
        formatted = await rt.call_agent("Formatter", f"Format: {processed}")
        report = await rt.call_agent("Reporter", f"Report on: {formatted}")
        return report
```

### Consensus Pattern

```python
# Multiple agents reach consensus
reviewers = ["Reviewer1", "Reviewer2", "Reviewer3"]

for i, name in enumerate(reviewers):
    agent = LLMAgent(
        name=name,
        description=f"Code reviewer #{i+1}",
        llm=llm,
        system_prompt="Review code for quality, security, and best practices."
    )
    app.register_agent(agent)

async def code_review(code):
    async with app.run_context() as rt:
        # Gather all reviews
        reviews = []
        for reviewer in reviewers:
            review = await rt.call_agent(reviewer, f"Review this code:\n{code}")
            reviews.append(review)
        
        # Synthesize consensus
        consensus = await rt.call_agent(
            "LeadReviewer",
            f"Synthesize these reviews into a consensus:\n" + "\n".join(reviews)
        )
        return consensus
```

## Performance Optimization

### Agent Pooling

```python
# Create a pool of identical agents
worker_pool = []
for i in range(5):
    worker = LLMAgent(
        name=f"Worker{i}",
        description="General purpose worker",
        llm=llm,  # Shared LLM instance
        system_prompt="Process tasks efficiently."
    )
    worker_pool.append(worker)
    app.register_agent(worker)

# Load balancing across pool
async def process_tasks(tasks):
    async with app.run_context() as rt:
        # Distribute tasks across workers
        results = []
        for i, task in enumerate(tasks):
            worker_name = f"Worker{i % len(worker_pool)}"
            result = await rt.call_agent(worker_name, task)
            results.append(result)
        return results
```

### Caching Agent Responses

```python
from functools import lru_cache
import hashlib

class CachedAgent(LLMAgent):
    def __init__(self, *args, cache_size=100, **kwargs):
        super().__init__(*args, **kwargs)
        self._cache = {}
        self._cache_size = cache_size
    
    async def run(self, prompt: str, runtime: Runtime) -> str:
        # Create cache key
        cache_key = hashlib.md5(prompt.encode()).hexdigest()
        
        # Check cache
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        # Generate response
        response = await super().run(prompt, runtime)
        
        # Update cache
        if len(self._cache) >= self._cache_size:
            # Remove oldest entry
            self._cache.pop(next(iter(self._cache)))
        self._cache[cache_key] = response
        
        return response
```

## Error Handling

```python
from tframex.exceptions import AgentError, AgentTimeoutError

# Robust agent implementation
class RobustAgent(LLMAgent):
    async def run(self, prompt: str, runtime: Runtime) -> str:
        max_retries = 3
        retry_delay = 1.0
        
        for attempt in range(max_retries):
            try:
                response = await super().run(prompt, runtime)
                return response
            except AgentTimeoutError:
                if attempt < max_retries - 1:
                    await asyncio.sleep(retry_delay)
                    retry_delay *= 2
                else:
                    return "I'm taking too long to respond. Please try again."
            except AgentError as e:
                return f"I encountered an error: {str(e)}"
```

## Testing Agents

```python
import pytest
from tframex.testing import MockLLM, MockRuntime

@pytest.fixture
def mock_agent():
    return LLMAgent(
        name="TestAgent",
        description="Agent for testing",
        llm=MockLLM(responses=[
            "First response",
            "Second response"
        ]),
        system_prompt="Test prompt"
    )

async def test_agent_response(mock_agent):
    runtime = MockRuntime()
    
    # Test first response
    response1 = await mock_agent.run("Test 1", runtime)
    assert response1 == "First response"
    
    # Test second response
    response2 = await mock_agent.run("Test 2", runtime)
    assert response2 == "Second response"

async def test_agent_with_tools(mock_agent):
    # Add mock tool
    mock_agent.tools = ["test_tool"]
    
    # Verify tool usage
    runtime = MockRuntime(tools={"test_tool": lambda: "Tool result"})
    response = await mock_agent.run("Use test_tool", runtime)
    assert "Tool result" in response
```

## Best Practices

1. **Clear Responsibilities** - Give each agent a specific, well-defined role
2. **Descriptive Names** - Use clear, descriptive agent names
3. **Comprehensive Prompts** - Write detailed system prompts
4. **Tool Selection** - Only give agents tools they need
5. **Error Handling** - Implement robust error handling
6. **Testing** - Test agents in isolation and integration
7. **Documentation** - Document agent capabilities and limitations
8. **Monitoring** - Track agent performance and costs

## See Also

- [TFrameXApp](tframexapp) - Application management
- [Tools](tools) - Tool system for agents
- [Flows](flows) - Agent orchestration
- [Patterns](patterns) - Common agent patterns
- [Examples](../examples/multi-agent-systems) - Multi-agent examples