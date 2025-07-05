---
sidebar_position: 2
title: Agents
---

# Agents

Agents are the core intelligent actors in TFrameX. They process inputs, make decisions, execute tools, and collaborate with other agents to accomplish complex tasks.

## What is an Agent?

An agent in TFrameX is an autonomous entity that:
- Receives and processes natural language inputs
- Uses an LLM to reason about tasks
- Executes tools to interact with external systems
- Maintains conversation context
- Can delegate to other agents

## Types of Agents

### LLMAgent

The most common agent type, powered by a language model:

```python
from tframex.agents.llm_agent import LLMAgent
from tframex.util.llms import OpenAIChatLLM

agent = LLMAgent(
    name="Assistant",
    description="A helpful AI assistant",
    llm=OpenAIChatLLM(),
    system_prompt="You are a helpful assistant. Be concise and friendly.",
    tools=["calculator", "web_search"],
    callable_agents=["Specialist"],
    max_tool_iterations=10
)
```

**Key Features:**
- Full LLM reasoning capabilities
- Tool execution
- Agent delegation
- Memory management
- Configurable behavior

### ToolAgent

A lightweight agent that directly executes a tool without LLM reasoning:

```python
from tframex.agents.tool_agent import ToolAgent

# Wrap a tool as an agent
tool_agent = ToolAgent(
    name="Calculator",
    tool_name="calculate",
    description="Direct calculation agent"
)
```

**Use Cases:**
- Performance-critical operations
- Deterministic workflows
- Tool exposure in multi-agent systems

### Custom Agents

Extend `BaseAgent` for specialized behavior:

```python
from tframex.agents.base import BaseAgent
from tframex.models.primitives import Message

class CustomAgent(BaseAgent):
    async def run(self, input_message: Message, **kwargs) -> Message:
        # Custom processing logic
        result = await self.process_custom_logic(input_message)
        return Message(role="assistant", content=result)
    
    async def process_custom_logic(self, message: Message) -> str:
        # Your implementation
        return "Custom response"
```

## Agent Configuration

### Basic Configuration

```python
agent = LLMAgent(
    name="ResearchAssistant",  # Unique identifier
    description="Specializes in research and analysis",  # Used by other agents
    llm=llm_instance,  # Language model to use
    system_prompt="You are a research specialist..."  # Defines behavior
)
```

### Advanced Configuration

```python
agent = LLMAgent(
    name="AdvancedAssistant",
    description="Feature-rich assistant",
    llm=custom_llm,
    
    # Tool configuration
    tools=["web_search", "calculator", "file_reader"],
    
    # Agent delegation
    callable_agents=["Researcher", "Writer", "Analyst"],
    
    # Memory configuration
    memory_store=CustomMemoryStore(max_messages=100),
    
    # Behavior configuration
    system_prompt="Complex prompt with {custom_var}",
    additional_prompt_variables={"custom_var": "dynamic value"},
    strip_think_tags=True,  # Remove <think> tags from output
    max_tool_iterations=15,  # Maximum tool calls per interaction
    
    # MCP integration
    mcp_tools_from_servers=["server1", "server2"]
)
```

## System Prompts

System prompts define agent behavior and capabilities:

### Effective System Prompt Structure

```python
system_prompt = """You are a [ROLE] specializing in [DOMAIN].

Your capabilities:
1. [CAPABILITY 1]: Description
2. [CAPABILITY 2]: Description
3. [CAPABILITY 3]: Description

Available tools:
- tool_name: What it does
- tool_name: What it does

Guidelines:
- [GUIDELINE 1]
- [GUIDELINE 2]
- [GUIDELINE 3]

Examples:
User: [Example query]
You: [Example response using tools]

Remember: [KEY REMINDERS]"""
```

### Real Example

```python
system_prompt = """You are a Financial Analyst specializing in investment research.

Your capabilities:
1. **Market Analysis**: Analyze market trends and provide insights
2. **Risk Assessment**: Evaluate investment risks and opportunities
3. **Report Generation**: Create comprehensive investment reports

Available tools:
- get_stock_data: Retrieve real-time stock information
- calculate_metrics: Compute financial metrics (P/E, ROI, etc.)
- generate_chart: Create visualization of financial data
- save_report: Save analysis reports to file

Guidelines:
- Always cite data sources
- Provide balanced analysis (pros and cons)
- Use appropriate financial terminology
- Quantify risks when possible

When asked about an investment:
1. Gather current market data
2. Calculate relevant metrics
3. Assess risks and opportunities
4. Provide a clear recommendation

Remember: Past performance doesn't guarantee future results. Always include appropriate disclaimers."""
```

## Tool Integration

Agents can use tools to extend their capabilities:

```python
# Define tools
@app.tool(description="Search financial news")
async def search_news(query: str, days_back: int = 7) -> str:
    # Implementation
    return news_results

@app.tool(description="Get stock quote")
async def get_quote(symbol: str) -> dict:
    # Implementation
    return {"symbol": symbol, "price": 150.25, "change": 2.5}

# Agent uses tools
analyst = LLMAgent(
    name="FinancialAnalyst",
    tools=["search_news", "get_quote"],
    system_prompt="You analyze financial markets using available tools."
)
```

## Agent Collaboration

### Agent-as-Tool Pattern

Agents can call other agents, creating hierarchical structures:

```python
# Specialist agents
researcher = LLMAgent(
    name="Researcher",
    description="Gathers and analyzes information",
    tools=["web_search", "database_query"]
)

writer = LLMAgent(
    name="Writer",
    description="Creates well-structured content",
    tools=["grammar_check", "format_document"]
)

# Coordinator agent
coordinator = LLMAgent(
    name="Coordinator",
    description="Manages research and writing projects",
    callable_agents=["Researcher", "Writer"],
    system_prompt="""You coordinate research and writing projects.
    
    Workflow:
    1. Use Researcher agent to gather information
    2. Use Writer agent to create content
    3. Review and refine the output
    
    Available agents:
    {available_agents_descriptions}"""
)
```

### Communication Patterns

```python
# Direct delegation
async def process_task(rt, task):
    # Coordinator delegates to specialists
    research = await rt.call_agent("Researcher", f"Research: {task}")
    content = await rt.call_agent("Writer", f"Write about: {research}")
    return content

# Iterative refinement
async def iterative_work(rt, task):
    draft = await rt.call_agent("Writer", task)
    feedback = await rt.call_agent("Editor", f"Review: {draft}")
    final = await rt.call_agent("Writer", f"Revise based on: {feedback}")
    return final
```

## Memory Management

Agents maintain conversation context through memory stores:

```python
from tframex.util.memory import InMemoryMemoryStore

# Bounded memory
agent = LLMAgent(
    name="Assistant",
    memory_store=InMemoryMemoryStore(max_messages=50),
    llm=llm
)

# Custom memory implementation
class PersistentMemoryStore(BaseMemoryStore):
    async def add_message(self, message: Message):
        # Save to database
        await self.db.save_message(message)
    
    async def get_history(self, limit=None):
        # Retrieve from database
        return await self.db.get_messages(limit=limit)

agent = LLMAgent(
    name="PersistentAssistant",
    memory_store=PersistentMemoryStore(),
    llm=llm
)
```

## Error Handling

Robust agents handle errors gracefully:

```python
class RobustAgent(BaseAgent):
    async def run(self, input_message: Message, **kwargs) -> Message:
        try:
            # Normal processing
            result = await self.process(input_message)
            return Message(role="assistant", content=result)
            
        except ToolExecutionError as e:
            # Handle tool failures
            fallback = await self.fallback_strategy(e)
            return Message(role="assistant", content=fallback)
            
        except Exception as e:
            # General error handling
            logger.error(f"Agent error: {e}")
            return Message(
                role="assistant", 
                content="I encountered an error. Please try again."
            )
```

## Performance Optimization

### 1. Tool Iteration Limits

```python
agent = LLMAgent(
    name="EfficientAgent",
    max_tool_iterations=5,  # Prevent infinite loops
    llm=llm
)
```

### 2. Streaming Responses

```python
async def stream_agent_response(rt, agent_name, query):
    async for chunk in rt.stream_agent(agent_name, query):
        print(chunk.content, end='', flush=True)
```

### 3. Parallel Agent Execution

```python
async def parallel_analysis(rt, data):
    tasks = [
        rt.call_agent("Analyst1", data),
        rt.call_agent("Analyst2", data),
        rt.call_agent("Analyst3", data)
    ]
    results = await asyncio.gather(*tasks)
    return results
```

## Best Practices

### 1. Single Responsibility
Each agent should have a clear, focused purpose:

```python
# Good: Focused agents
email_writer = LLMAgent(name="EmailWriter", ...)
code_reviewer = LLMAgent(name="CodeReviewer", ...)

# Avoid: Jack-of-all-trades
super_agent = LLMAgent(name="DoEverything", ...)
```

### 2. Clear Descriptions
Help other agents understand capabilities:

```python
agent = LLMAgent(
    name="DataAnalyst",
    description="Analyzes datasets, creates visualizations, and provides statistical insights",
    # NOT: "Does data stuff"
)
```

### 3. Comprehensive System Prompts
Include all necessary context:

```python
system_prompt = """You are a Customer Service Representative.

Guidelines:
- Always be polite and professional
- Acknowledge customer concerns
- Provide specific solutions
- Escalate when appropriate

You have access to:
- Customer database (use lookup_customer tool)
- Order system (use check_order tool)
- Refund system (use process_refund tool)

Never:
- Share customer personal information
- Make promises beyond policy
- Express frustration"""
```

### 4. Appropriate Tool Selection
Give agents only the tools they need:

```python
# Financial analyst doesn't need social media tools
analyst = LLMAgent(
    name="FinancialAnalyst",
    tools=["get_financials", "calculate_ratios"],  # Relevant tools only
)
```

## Testing Agents

Create comprehensive tests for your agents:

```python
import pytest
from tframex import TFrameXApp

@pytest.fixture
async def app():
    app = TFrameXApp()
    # Configure app with test agents
    return app

async def test_agent_response(app):
    async with app.run_context() as rt:
        response = await rt.call_agent(
            "Assistant",
            "What is 2 + 2?"
        )
        assert "4" in response
        
async def test_agent_tool_usage(app):
    async with app.run_context() as rt:
        response = await rt.call_agent(
            "Calculator",
            "Calculate 15% of 200"
        )
        assert "30" in response

async def test_agent_error_handling(app):
    async with app.run_context() as rt:
        response = await rt.call_agent(
            "Assistant",
            "Invalid tool request"
        )
        assert "error" not in response.lower()
```

## Advanced Patterns

### Dynamic Agent Creation

```python
def create_specialist_agent(domain: str, tools: list[str]) -> LLMAgent:
    return LLMAgent(
        name=f"{domain}Specialist",
        description=f"Expert in {domain}",
        tools=tools,
        system_prompt=f"You are a {domain} specialist. {get_domain_prompt(domain)}"
    )

# Create agents dynamically
domains = ["Finance", "Healthcare", "Technology"]
for domain in domains:
    agent = create_specialist_agent(domain, get_domain_tools(domain))
    app.register_agent(agent)
```

### Agent Middleware

```python
class LoggingAgent(LLMAgent):
    async def run(self, input_message: Message, **kwargs) -> Message:
        # Log input
        logger.info(f"Agent {self.name} received: {input_message.content}")
        
        # Process normally
        response = await super().run(input_message, **kwargs)
        
        # Log output
        logger.info(f"Agent {self.name} responded: {response.content}")
        
        return response
```

## Next Steps

Now that you understand agents:

1. Learn about [Tools](tools) to extend agent capabilities
2. Explore [Flows](flows) for multi-agent workflows
3. Study [Patterns](patterns) for common agent arrangements
4. Check [API Reference](../api/agents) for detailed documentation

## Examples

For practical agent implementations, see:
- [Basic Examples](../examples/basic-examples#simple-agent)
- [Multi-Agent Systems](../examples/pattern-examples#multi-agent)
- [Advanced Agents](../examples/advanced-examples#smart-agents)