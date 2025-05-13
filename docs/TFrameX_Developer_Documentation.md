# TFrameX Developer Documentation

## Table of Contents
1. [Introduction](#introduction)
2. [Core Concepts](#core-concepts)
3. [Getting Started](#getting-started)
4. [Architecture Overview](#architecture-overview)
5. [Components](#components)
   - [App](#app)
   - [Agents](#agents)
   - [Flows](#flows)
   - [Patterns](#patterns)
   - [Tools](#tools)
   - [LLM Integration](#llm-integration)
   - [Memory Management](#memory-management)
6. [Creating Agentic Flows](#creating-agentic-flows)
7. [Extending TFrameX](#extending-tframex)
8. [Example Applications](#example-applications)

## Introduction

TFrameX is a framework for building complex, multi-agent AI systems. It enables developers to create sophisticated agentic flows by composing LLM-powered agents with different interaction patterns. The framework provides a structured approach to organizing communication between AI components, making it easier to build applications that leverage multiple AI agents working together.

## Core Concepts

- **Agents**: Individual AI entities with specific roles and capabilities
- **Flows**: Sequences of interactions between agents 
- **Patterns**: Reusable structures for organizing agent interactions
- **Tools**: Functions that agents can use to interact with external systems
- **Messages**: The basic unit of communication

## Getting Started

### Installation

```python
# You can install TFrameX from pip
pip install tframex  # Hypothetical, based on the repository structure
```

### Basic Example

```python
import asyncio
from dotenv import load_dotenv
from tframex import (
    TFrameXApp, 
    OpenAIChatLLM, 
    Message, 
    SequentialPattern,
    Flow
)

# Load environment variables
load_dotenv()

# Initialize LLM
llm = OpenAIChatLLM(
    model_name="gpt-3.5-turbo",
    api_key="your_api_key"  # Or from environment: os.getenv("OPENAI_API_KEY")
)

# Create application
app = TFrameXApp(default_llm=llm)

# Define agents
@app.agent(
    name="Summarizer",
    description="Summarizes text",
    system_prompt="Summarize the following text concisely."
)
async def summarizer_agent_placeholder():
    pass

@app.agent(
    name="Critic",
    description="Critiques summaries",
    system_prompt="Review the summary and provide constructive feedback."
)
async def critic_agent_placeholder():
    pass

# Create a flow using sequential pattern
summary_flow = Flow(
    "SummaryReviewFlow",
    SequentialPattern(
        "SummarizeAndCritique",
        steps=["Summarizer", "Critic"]
    )
)

# Register flow
app.register_flow(summary_flow)

# Run the flow
async def main():
    async with app.run_context() as ctx:
        input_message = Message(role="user", content="The quick brown fox jumps over the lazy dog.")
        result = await ctx.run_flow("SummaryReviewFlow", input_message)
        print(result.current_message.content)

if __name__ == "__main__":
    asyncio.run(main())
```

## Architecture Overview

TFrameX follows a modular architecture centered around the core `TFrameXApp` class, which manages agent registrations, tools, and flows. The framework uses asyncio for asynchronous operation and provides several key components:

- **TFrameXApp**: The main application container
- **TFrameXRuntimeContext**: The runtime environment for executing flows
- **Flow**: Defines a sequence of agent interactions
- **FlowContext**: Maintains state during flow execution
- **BaseAgent/LLMAgent/ToolAgent**: Agent implementations
- **Patterns**: Flow organization structures

## Components

### App

The `TFrameXApp` class is the central container for your application:

```python
from tframex import TFrameXApp, OpenAIChatLLM

llm = OpenAIChatLLM(model_name="gpt-3.5-turbo", api_key="your-api-key")
app = TFrameXApp(default_llm=llm)
```

Key features:
- Register agents and tools
- Create and manage flows
- Provides runtime context

### Agents

Agents are the core AI entities in TFrameX:

#### Types of Agents
- **BaseAgent**: Abstract base class for all agents
- **LLMAgent**: Default agent powered by an LLM
- **ToolAgent**: Agent that can use registered tools

#### Creating Agents

```python
@app.agent(
    name="WeatherAgent",
    description="Provides weather information",
    system_prompt="You are a weather assistant. Answer questions about weather only.",
    tools=["get_weather"],  # Optional tools this agent can use
    llm=special_llm  # Optional override for specific LLM
)
async def weather_agent_placeholder():
    pass
```

### Flows

Flows define sequences of actions using agents and patterns:

```python
from tframex import Flow, SequentialPattern

# Create a flow with a sequential pattern
my_flow = Flow(
    "MyProcessingFlow",
    SequentialPattern(
        "ProcessSequence",
        steps=["AgentA", "AgentB", "AgentC"]
    )
)

# Register the flow
app.register_flow(my_flow)

# Run the flow
async with app.run_context() as ctx:
    result = await ctx.run_flow(
        "MyProcessingFlow", 
        initial_input=Message(role="user", content="Process this information")
    )
```

### Patterns

Patterns are reusable structures for organizing agent interactions:

#### Available Patterns
- **SequentialPattern**: Executes agents in sequence, piping output to input
- **ParallelPattern**: Runs multiple agents concurrently with the same input
- **RouterPattern**: Dynamically selects which agent to run based on input
- **DiscussionPattern**: Creates multi-agent discussions with turns and moderators
- **DelegatePattern**: Allows a supervisor agent to assign other agents tasks

#### Example: Sequential Pattern

```python
from tframex import SequentialPattern

sequence = SequentialPattern(
    "ProcessingSequence",
    steps=["Analyzer", "Enhancer", "Formatter"]
)
```

#### Example: Router Pattern

```python
from tframex import RouterPattern

router = RouterPattern(
    "QueryRouter",
    router_agent="RouterAgent",
    routes={
        "weather": "WeatherAgent",
        "news": "NewsAgent",
        "general": "GeneralAgent"
    },
    default_route="GeneralAgent"
)
```

### Tools

Tools are functions that agents can call to perform actions:

```python
@app.tool(
    name="get_weather", 
    description="Gets current weather for a location",
    parameters_schema={
        "properties": {
            "location": {"type": "string", "description": "City name"},
            "unit": {"type": "string", "description": "Temperature unit (celsius/fahrenheit)"}
        },
        "required": ["location"]
    }
)
async def get_weather(location: str, unit: str = "celsius") -> str:
    # Implementation to fetch weather
    return f"The weather in {location} is sunny, 25°{unit[0].upper()}"
```

### LLM Integration

TFrameX supports different LLM providers through a common interface:

```python
from tframex import OpenAIChatLLM

# Default LLM for general use
default_llm = OpenAIChatLLM(
    model_name="gpt-3.5-turbo",
    api_key="your-api-key"
)

# Special LLM for specific tasks
special_llm = OpenAIChatLLM(
    model_name="gpt-4",
    api_key="your-api-key"
)

# Use in app
app = TFrameXApp(default_llm=default_llm)

# Or override for specific agents
@app.agent(
    name="ComplexReasoningAgent",
    description="Handles complex reasoning tasks",
    system_prompt="You solve complex problems with detailed reasoning.",
    llm=special_llm  # This agent uses the more powerful model
)
async def complex_reasoning_placeholder():
    pass
```

### Memory Management

TFrameX includes memory management for storing conversation history:

```python
from tframex import InMemoryMemoryStore, TFrameXApp

# Use default in-memory store
app = TFrameXApp(default_memory_store_factory=InMemoryMemoryStore)

# Or create custom memory stores by extending BaseMemoryStore
from tframex import BaseMemoryStore

class CustomMemoryStore(BaseMemoryStore):
    # Implement required methods
    async def add_message(self, message, conversation_id=None):
        pass
    
    async def get_messages(self, conversation_id=None):
        pass
```

## Creating Agentic Flows

### Basic Flow Creation

1. Define agents with specific capabilities
2. Create patterns to organize agent interactions
3. Compose a flow using the patterns
4. Register the flow with the application
5. Run the flow with initial input

### Flow with Template Variables

```python
# Create a flow with template variables
greeting_flow = Flow(
    "GreetingFlow",
    SequentialPattern(
        "GreetAndRespond",
        steps=["GreetingAgent"]
    )
)

# Register the flow
app.register_flow(greeting_flow)

# Run with template variables
async with app.run_context() as ctx:
    result = await ctx.run_flow(
        "GreetingFlow",
        initial_input=Message(role="user", content="Hello there"),
        flow_template_vars={
            "user_name": "Alice",
            "user_query": "How to use TFrameX"
        }
    )
```

### Using Shared Data

```python
# Run flow with shared data across steps
async with app.run_context() as ctx:
    result = await ctx.run_flow(
        "AnalysisFlow",
        initial_input=Message(role="user", content="Analyze this data"),
        initial_shared_data={
            "source_document": "Important research paper",
            "analysis_level": "detailed"
        }
    )
```

## Extending TFrameX

### Creating Custom Agents

Extend `BaseAgent` to create custom agent types:

```python
from tframex.agents.base import BaseAgent
from tframex.models.primitives import Message

class MyCustomAgent(BaseAgent):
    async def process(self, input_message: Message, **kwargs) -> Message:
        # Custom processing logic
        return Message(
            role="assistant",
            content=f"Processed: {input_message.content}"
        )

# Register with custom class
@app.agent(
    name="CustomAgent",
    description="My specialized agent",
    agent_class=MyCustomAgent
)
async def custom_agent_placeholder():
    pass
```

### Creating Custom Patterns

Extend `BasePattern` to create custom interaction patterns:

```python
from tframex.patterns.base_pattern import BasePattern
from tframex.flows.flow_context import FlowContext
from tframex.util.engine import Engine

class MyCustomPattern(BasePattern):
    def __init__(self, pattern_name: str, custom_config):
        super().__init__(pattern_name)
        self.custom_config = custom_config
        
    async def execute(
        self,
        flow_ctx: FlowContext,
        engine: Engine,
        agent_call_kwargs=None
    ) -> FlowContext:
        # Implementation of custom pattern execution
        # ...
        return flow_ctx
```

### Creating Custom LLM Wrappers

Extend `BaseLLMWrapper` to integrate with other LLM providers:

```python
from tframex.util.llms import BaseLLMWrapper
from tframex.models.primitives import Message

class MyCustomLLM(BaseLLMWrapper):
    # Implement required methods
    async def generate_response(self, messages, **kwargs):
        # Custom LLM integration
        pass
        
    async def generate_response_stream(self, messages, **kwargs):
        # Custom streaming implementation
        pass
```

## Example Applications

TFrameX can be used to build various agentic applications:

### Multi-Agent Discussion System

```python
from tframex import (
    TFrameXApp, 
    DiscussionPattern, 
    Flow, 
    Message, 
    OpenAIChatLLM
)

app = TFrameXApp(default_llm=OpenAIChatLLM(...))

# Define discussant agents
@app.agent(name="OptimistAgent", system_prompt="You are optimistic about everything.")
async def optimist_placeholder():
    pass

@app.agent(name="PessimistAgent", system_prompt="You see problems in everything.")
async def pessimist_placeholder():
    pass

@app.agent(name="ModeratorAgent", system_prompt="Summarize and moderate discussions.")
async def moderator_placeholder():
    pass

# Create discussion pattern
discussion = DiscussionPattern(
    "ProblemDiscussion",
    participants=["OptimistAgent", "PessimistAgent"],
    moderator="ModeratorAgent",
    rounds=2
)

# Create and register flow
discussion_flow = Flow("DiscussionFlow", discussion)
app.register_flow(discussion_flow)

# Run discussion
async with app.run_context() as ctx:
    result = await ctx.run_flow(
        "DiscussionFlow", 
        Message(role="user", content="Discuss the impact of AI on society")
    )
```

### Dynamic Task Router

```python
from tframex import TFrameXApp, RouterPattern, Flow, Message

app = TFrameXApp(...)

# Define router and handler agents
@app.agent(name="RouterAgent", system_prompt="Classify the query type.")
async def router_placeholder():
    pass

@app.agent(name="WeatherAgent", tools=["get_weather"])
async def weather_placeholder():
    pass

@app.agent(name="NewsAgent", tools=["fetch_news"])
async def news_placeholder():
    pass

# Create router pattern
router = RouterPattern(
    "QueryRouter",
    router_agent="RouterAgent",
    routes={
        "weather": "WeatherAgent",
        "news": "NewsAgent",
        "general": "GeneralAssistantAgent"
    }
)

# Create and register flow
router_flow = Flow("RoutingFlow", router)
app.register_flow(router_flow)
```

### Supervisor with Delegate Pattern

```python
from tframex import TFrameXApp, Flow, Message

app = TFrameXApp(...)

# Define specialist agents
@app.agent(name="ResearchAgent", system_prompt="You research topics in depth.")
async def research_placeholder():
    pass

@app.agent(name="WritingAgent", system_prompt="You write high-quality content.")
async def writing_placeholder():
    pass

# Define supervisor agent that can call other agents
@app.agent(
    name="SupervisorAgent",
    system_prompt="Delegate tasks to specialist agents as needed.",
    callable_agents=["ResearchAgent", "WritingAgent"]
)
async def supervisor_placeholder():
    pass

# Create a flow with the supervisor
supervisor_flow = Flow("SupervisedTaskFlow", "SupervisorAgent")
app.register_flow(supervisor_flow)
```

---

This documentation provides an overview of the TFrameX framework and its capabilities. For more detailed examples, see the examples directory in the repository. 