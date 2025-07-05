---
sidebar_position: 4
title: Your First Agent
---

# Building Your First Agent

This tutorial will guide you through building a complete AI agent from scratch, teaching you the core concepts of TFrameX along the way.

## What We'll Build

We'll create a **Personal Research Assistant** that can:
- Answer questions using web search
- Summarize information
- Save important findings to files
- Maintain conversation context

## Step 1: Project Setup

### Create the Project

```bash
# Use the CLI to scaffold a project
tframex setup research-assistant
cd research-assistant

# Set up environment
cp .env.example .env
# Edit .env with your API key
```

### Install Dependencies

```bash
pip install -r requirements.txt
pip install aiohttp  # For web search functionality
```

## Step 2: Create the Web Search Tool

First, let's create a tool that can search the web. Edit `config/tools.py`:

```python
"""
Tool configurations for Research Assistant
"""
from tframex.util.tools import Tool, ToolParameters, ToolParameterProperty
import aiohttp
import json

async def web_search(query: str, max_results: int = 5) -> str:
    """
    Search the web for information.
    In production, you'd use a real search API like Google Custom Search or Bing.
    """
    # For demo purposes, we'll simulate search results
    # In real implementation, call actual search API
    mock_results = [
        {
            "title": f"Result for: {query}",
            "snippet": f"This is a relevant result about {query}. It contains useful information.",
            "url": f"https://example.com/{query.replace(' ', '-')}"
        }
    ]
    
    return json.dumps(mock_results, indent=2)

async def save_to_file(filename: str, content: str) -> str:
    """Save content to a file in the data directory."""
    import os
    from pathlib import Path
    
    # Ensure data directory exists
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)
    
    # Sanitize filename
    safe_filename = "".join(c for c in filename if c.isalnum() or c in (' ', '-', '_')).rstrip()
    filepath = data_dir / f"{safe_filename}.txt"
    
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return f"Successfully saved to {filepath}"
    except Exception as e:
        return f"Error saving file: {str(e)}"

async def read_from_file(filename: str) -> str:
    """Read content from a file in the data directory."""
    from pathlib import Path
    
    data_dir = Path("data")
    filepath = data_dir / f"{filename}.txt"
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        return content
    except FileNotFoundError:
        return f"File not found: {filepath}"
    except Exception as e:
        return f"Error reading file: {str(e)}"

def setup_tools(app):
    """Setup and register tools with the app."""
    
    # Web search tool
    search_tool = Tool(
        name="web_search",
        func=web_search,
        description="Search the web for information",
        parameters_schema=ToolParameters(
            properties={
                "query": ToolParameterProperty(
                    type="string",
                    description="The search query"
                ),
                "max_results": ToolParameterProperty(
                    type="integer",
                    description="Maximum number of results to return",
                    default=5
                )
            },
            required=["query"]
        )
    )
    
    # File save tool
    save_tool = Tool(
        name="save_to_file",
        func=save_to_file,
        description="Save content to a file",
        parameters_schema=ToolParameters(
            properties={
                "filename": ToolParameterProperty(
                    type="string",
                    description="Name of the file (without extension)"
                ),
                "content": ToolParameterProperty(
                    type="string",
                    description="Content to save"
                )
            },
            required=["filename", "content"]
        )
    )
    
    # File read tool
    read_tool = Tool(
        name="read_from_file",
        func=read_from_file,
        description="Read content from a file",
        parameters_schema=ToolParameters(
            properties={
                "filename": ToolParameterProperty(
                    type="string",
                    description="Name of the file to read (without extension)"
                )
            },
            required=["filename"]
        )
    )
    
    # Register all tools
    app.register_tool(search_tool)
    app.register_tool(save_tool)
    app.register_tool(read_tool)
    
    # Keep the default time tool
    from datetime import datetime
    
    def get_current_time() -> str:
        """Get the current date and time."""
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    time_tool = Tool(
        name="get_current_time",
        func=get_current_time,
        description="Get the current date and time",
        parameters_schema=ToolParameters(properties={}, required=None)
    )
    app.register_tool(time_tool)
```

## Step 3: Configure the Research Assistant Agent

Now let's create our research assistant agent. Edit `config/agents.py`:

```python
"""
Agent configurations for Research Assistant
"""
import os
from tframex.agents.llm_agent import LLMAgent
from tframex.util.llms import OpenAIChatLLM

def setup_agents(app):
    """Setup and register agents with the app."""
    
    # Configure LLM
    api_key = os.getenv("OPENAI_API_KEY") or os.getenv("LLAMA_API_KEY")
    if not api_key:
        raise ValueError("Please set OPENAI_API_KEY or LLAMA_API_KEY environment variable")
    
    base_url = os.getenv("OPENAI_API_BASE") or os.getenv("LLAMA_BASE_URL")
    model_name = os.getenv("OPENAI_MODEL_NAME") or os.getenv("LLAMA_MODEL") or "gpt-3.5-turbo"
    
    llm = OpenAIChatLLM(
        model_name=model_name,
        api_key=api_key,
        api_base_url=base_url,
        parse_text_tool_calls=True
    )
    
    # Create Research Assistant
    research_assistant = LLMAgent(
        name="ResearchAssistant",
        description="A personal research assistant that can search the web and manage information",
        llm=llm,
        tools=["web_search", "save_to_file", "read_from_file", "get_current_time"],
        system_prompt="""You are a helpful research assistant with the ability to search the web and manage information.

Your capabilities:
1. **Web Search**: Use web_search to find information on any topic
2. **Save Information**: Use save_to_file to store important findings
3. **Read Files**: Use read_from_file to recall previously saved information
4. **Time Awareness**: Use get_current_time to know the current date and time

Guidelines:
- When asked to research a topic, always start with a web search
- Summarize findings clearly and concisely
- Offer to save important information for future reference
- When saving files, use descriptive filenames
- If asked about previous research, check saved files first
- Provide sources when sharing information
- Be thorough but concise in your responses

Remember: You're helping users conduct research efficiently and effectively."""
    )
    
    # Register the agent
    app.register_agent(research_assistant)
```

## Step 4: Enhance the Main Application

Update `main.py` to showcase the capabilities:

```python
#!/usr/bin/env python3
"""
Research Assistant - TFrameX Project
"""
import asyncio
import os
from pathlib import Path

from tframex import TFrameXApp
from config.agents import setup_agents
from config.tools import setup_tools


def create_app() -> TFrameXApp:
    """Create and configure the TFrameX application."""
    app = TFrameXApp()
    
    # Setup tools and agents
    setup_tools(app)
    setup_agents(app)
    
    return app


async def demo_research_capabilities(rt):
    """Demonstrate the research assistant's capabilities."""
    print("🔬 Research Assistant Demo")
    print("=" * 50)
    
    demos = [
        ("Research", "Research the benefits of meditation and save a summary"),
        ("Recall", "What information do we have saved about meditation?"),
        ("Time-aware", "What's the current date and time?"),
        ("Complex", "Research Python async programming best practices and create a guide")
    ]
    
    for demo_name, query in demos:
        print(f"\n📌 Demo: {demo_name}")
        print(f"Query: {query}")
        print("-" * 30)
        
        response = await rt.call_agent("ResearchAssistant", query)
        print(f"Response: {response}")
        
        input("\nPress Enter to continue...")


async def main():
    """Main application entry point."""
    print(f"🚀 Starting Research Assistant")
    print("=" * 50)
    
    app = create_app()
    
    # Check if we should run demo or interactive mode
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--demo":
        async with app.run_context() as rt:
            await demo_research_capabilities(rt)
    else:
        print("\n💬 Interactive Mode")
        print("You can ask me to:")
        print("- Research any topic")
        print("- Save important information")
        print("- Recall previously saved information")
        print("- Get the current time")
        print("\nType 'exit' or 'quit' to end the session.\n")
        
        # Run interactive session
        async with app.run_context() as rt:
            await rt.interactive_chat(default_agent_name="ResearchAssistant")


if __name__ == "__main__":
    asyncio.run(main())
```

## Step 5: Testing Your Agent

### Run the Demo

```bash
python main.py --demo
```

This will showcase the agent's capabilities with predefined queries.

### Interactive Mode

```bash
python main.py
```

Try these interactions:

```
You: Research the history of artificial intelligence
You: Save a timeline of major AI milestones
You: What files do we have saved?
You: Read the file about AI milestones
```

## Step 6: Extending Your Agent

### Add a Summarization Specialist

Create a multi-agent system by adding a summarization specialist:

```python
# In config/agents.py, add:

summarizer = LLMAgent(
    name="Summarizer",
    description="Specializes in creating concise summaries",
    llm=llm,
    system_prompt="""You are an expert at summarization.
    
Your job is to:
- Create concise, accurate summaries
- Highlight key points
- Maintain important context
- Use bullet points for clarity"""
)

# Update the research assistant to use the summarizer
research_assistant = LLMAgent(
    name="ResearchAssistant",
    description="A personal research assistant with a summarization specialist",
    llm=llm,
    tools=["web_search", "save_to_file", "read_from_file", "get_current_time"],
    callable_agents=["Summarizer"],  # Can now call the summarizer
    system_prompt="""You are a helpful research assistant with access to a summarization specialist.

Your capabilities:
1. **Web Search**: Use web_search to find information
2. **Summarization**: Call the Summarizer agent for concise summaries
3. **File Management**: Save and read files
4. **Time Awareness**: Get current time

When researching complex topics, use the Summarizer agent to create clear, concise summaries."""
)

app.register_agent(summarizer)
app.register_agent(research_assistant)
```

### Add Real Web Search

Replace the mock search with a real API:

```python
# Using DuckDuckGo (no API key required)
import aiohttp
from urllib.parse import quote

async def web_search(query: str, max_results: int = 5) -> str:
    """Search the web using DuckDuckGo instant answers API."""
    encoded_query = quote(query)
    url = f"https://api.duckduckgo.com/?q={encoded_query}&format=json"
    
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            data = await response.json()
            
    results = []
    
    # Abstract text
    if data.get('AbstractText'):
        results.append({
            "title": data.get('Heading', 'Summary'),
            "snippet": data['AbstractText'],
            "url": data.get('AbstractURL', '')
        })
    
    # Related topics
    for topic in data.get('RelatedTopics', [])[:max_results-1]:
        if isinstance(topic, dict) and 'Text' in topic:
            results.append({
                "title": topic.get('FirstURL', '').split('/')[-1].replace('_', ' '),
                "snippet": topic['Text'],
                "url": topic.get('FirstURL', '')
            })
    
    return json.dumps(results, indent=2) if results else "No results found"
```

## Best Practices

### 1. Tool Design
- Keep tools focused on a single responsibility
- Always handle errors gracefully
- Return structured data when possible
- Include helpful error messages

### 2. Agent Prompts
- Be specific about the agent's role
- List capabilities clearly
- Provide guidelines for tool usage
- Include examples when helpful

### 3. Error Handling
```python
@app.tool(description="Safe web request")
async def safe_web_request(url: str) -> str:
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=10) as response:
                if response.status == 200:
                    return await response.text()
                else:
                    return f"Error: HTTP {response.status}"
    except asyncio.TimeoutError:
        return "Error: Request timed out"
    except Exception as e:
        return f"Error: {str(e)}"
```

### 4. Testing
Create a test file `test_agent.py`:

```python
import asyncio
from main import create_app

async def test_research_assistant():
    app = create_app()
    
    test_queries = [
        "What is the weather like?",  # Should handle gracefully
        "Search for Python tutorials",
        "Save a note about testing",
        "Read the note about testing"
    ]
    
    async with app.run_context() as rt:
        for query in test_queries:
            print(f"\nTest: {query}")
            response = await rt.call_agent("ResearchAssistant", query)
            print(f"Response: {response[:200]}...")
            assert response, "Agent should always return a response"

if __name__ == "__main__":
    asyncio.run(test_research_assistant())
```

## What You've Learned

Congratulations! You've built a complete AI research assistant. You've learned how to:

✅ Create and configure agents with specific roles  
✅ Build custom tools with proper error handling  
✅ Design effective system prompts  
✅ Create multi-agent systems  
✅ Handle file I/O safely  
✅ Structure a TFrameX project  

## Next Steps

1. **Add More Tools**: Integrate with real APIs (news, weather, databases)
2. **Create Specialized Agents**: Add agents for specific domains
3. **Build Workflows**: Use [Flow Orchestration](guides/flow-orchestration) for complex tasks
4. **Add MCP Servers**: Connect to [external services](guides/mcp-servers)
5. **Deploy to Production**: Explore [enterprise features](enterprise/overview)

## Complete Code

The full code for this tutorial is available in the TFrameX examples:
- [GitHub Repository](https://github.com/TesslateAI/TFrameX/tree/main/examples)

## Getting Help

- 💬 [Discord Community](https://discord.gg/DkzMzwBTaw)
- 📖 [API Reference](../api/overview)
- 🐛 [GitHub Issues](https://github.com/TesslateAI/TFrameX/issues)