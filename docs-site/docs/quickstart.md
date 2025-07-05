---
sidebar_position: 3
title: Quickstart
---

# Quickstart Guide

Get up and running with TFrameX in 5 minutes! This guide will walk you through creating your first AI agent application.

## Prerequisites

- TFrameX installed (`pip install tframex`)
- An API key for an LLM service (OpenAI, Anthropic, etc.)

## Option 1: Using the CLI (Fastest)

### Step 1: Set Your API Key

```bash
export OPENAI_API_KEY="your-api-key-here"
```

### Step 2: Try Interactive Mode

```bash
tframex basic
```

This launches an interactive chat session with a basic AI assistant. Try asking:
- "What time is it?"
- "Can you help me with Python?"
- "What tools do you have available?"

Type `exit` to quit.

### Step 3: Create a Project

```bash
tframex setup my-first-agent
cd my-first-agent
```

### Step 4: Configure Environment

```bash
cp .env.example .env
# Edit .env and add your API key
nano .env  # or use your preferred editor
```

### Step 5: Run Your Project

```bash
pip install -r requirements.txt
python main.py
```

## Option 2: Manual Setup

### Step 1: Create a Simple Agent

Create a file called `simple_agent.py`:

```python
import asyncio
from tframex import TFrameXApp
from tframex.agents.llm_agent import LLMAgent
from tframex.util.llms import OpenAIChatLLM

# Create the app
app = TFrameXApp()

# Configure LLM
llm = OpenAIChatLLM(
    api_key="your-api-key-here",
    model_name="gpt-3.5-turbo"
)

# Create and register an agent using decorator
@app.agent(
    name="Assistant",
    description="A helpful AI assistant", 
    system_prompt="You are a helpful AI assistant. Be concise and friendly."
)
async def assistant():
    pass

# Run the app
async def main():
    async with app.run_context(llm_override=llm) as rt:
        # Single interaction
        response = await rt.call_agent("Assistant", "Hello! What can you do?")
        print(f"Assistant: {response.content}")
        
        # Interactive chat
        print("\nStarting interactive chat (type 'exit' to quit)...")
        await rt.interactive_chat()

if __name__ == "__main__":
    asyncio.run(main())
```

### Step 2: Run It

```bash
python simple_agent.py
```

## Adding Tools to Your Agent

Let's make your agent more capable by adding tools:

```python
import asyncio
from datetime import datetime
from tframex import TFrameXApp
from tframex.agents.llm_agent import LLMAgent
from tframex.util.llms import OpenAIChatLLM

app = TFrameXApp()

# Define tools
@app.tool(description="Get the current date and time")
async def get_current_time() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

@app.tool(description="Calculate the sum of two numbers")
async def add(a: int, b: int) -> int:
    return a + b

@app.tool(description="Get weather information (mock)")
async def get_weather(city: str) -> str:
    # In real app, this would call a weather API
    return f"The weather in {city} is sunny and 72°F"

# Create agent with tools using decorator
llm = OpenAIChatLLM(api_key="your-api-key")

@app.agent(
    name="SmartAssistant",
    description="An assistant with tools",
    tools=["get_current_time", "add", "get_weather"],
    system_prompt="""You are a helpful assistant with access to tools.
    
You can:
- Tell the current time
- Perform calculations
- Check the weather
    
Use your tools when appropriate to help the user."""
)
async def smart_assistant():
    pass

async def main():
    async with app.run_context(llm_override=llm) as rt:
        # Test the tools
        print("Testing agent with tools...\n")
        
        queries = [
            "What time is it?",
            "What's 234 + 567?",
            "What's the weather in San Francisco?"
        ]
        
        for query in queries:
            print(f"You: {query}")
            response = await rt.call_agent("SmartAssistant", query)
            print(f"Assistant: {response.content}\n")

if __name__ == "__main__":
    asyncio.run(main())
```

## Creating Multi-Agent Systems

Here's a simple multi-agent system where agents work together:

```python
from tframex import TFrameXApp
from tframex.agents.llm_agent import LLMAgent
from tframex.util.llms import OpenAIChatLLM
import asyncio

app = TFrameXApp()
llm = OpenAIChatLLM(api_key="your-api-key")

# Research Agent
@app.agent(
    name="Researcher",
    description="Specializes in research and information gathering",
    system_prompt="You are a research specialist. Provide detailed, accurate information."
)
async def researcher():
    pass

# Writer Agent
@app.agent(
    name="Writer",
    description="Specializes in clear, engaging writing",
    system_prompt="You are a professional writer. Create clear, engaging content."
)
async def writer():
    pass

# Coordinator Agent (can call other agents)
@app.agent(
    name="Coordinator",
    description="Coordinates research and writing tasks",
    callable_agents=["Researcher", "Writer"],
    system_prompt="""You coordinate research and writing tasks.
    
Available agents:
- Researcher: For gathering information
- Writer: For creating content

Delegate tasks appropriately and synthesize results."""
)
async def coordinator():
    pass

async def main():
    async with app.run_context(llm_override=llm) as rt:
        # Complex task requiring coordination
        task = "Create a brief article about the benefits of AI in healthcare"
        
        print(f"Task: {task}\n")
        result = await rt.call_agent("Coordinator", task)
        print(f"Result:\n{result.content}")

if __name__ == "__main__":
    asyncio.run(main())
```

## Web Interface

Launch a web interface for your agents:

```bash
# Install web support
pip install tframex[web]

# Start web server
tframex serve

# Open http://localhost:8000 in your browser
```

Or create a custom web app:

```python
from flask import Flask, render_template_string, request, jsonify
from tframex import TFrameXApp
from tframex.agents.llm_agent import LLMAgent
from tframex.util.llms import OpenAIChatLLM
import asyncio

# Create Flask app
flask_app = Flask(__name__)

# Create TFrameX app
tframex_app = TFrameXApp()
llm = OpenAIChatLLM(api_key="your-api-key")

@tframex_app.agent(
    name="WebAssistant",
    description="Web-based AI assistant",
    system_prompt="You are a helpful web assistant."
)
async def web_assistant():
    pass

@flask_app.route('/')
def index():
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <title>TFrameX Chat</title>
    </head>
    <body>
        <h1>Chat with AI Assistant</h1>
        <div id="chat"></div>
        <input type="text" id="input" placeholder="Type a message...">
        <button onclick="sendMessage()">Send</button>
        
        <script>
        async function sendMessage() {
            const input = document.getElementById('input');
            const message = input.value;
            input.value = '';
            
            const response = await fetch('/chat', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({message: message})
            });
            
            const data = await response.json();
            document.getElementById('chat').innerHTML += 
                `<p><b>You:</b> ${message}</p>
                 <p><b>AI:</b> ${data.response}</p>`;
        }
        </script>
    </body>
    </html>
    ''')

@flask_app.route('/chat', methods=['POST'])
def chat():
    message = request.json['message']
    
    async def get_response():
        async with tframex_app.run_context(llm_override=llm) as rt:
            result = await rt.call_agent("WebAssistant", message)
            return result.content
    
    response = asyncio.run(get_response())
    return jsonify({"response": response})

if __name__ == '__main__':
    flask_app.run(debug=True)
```

## Next Steps

Congratulations! You've created your first TFrameX agents. Here's what to explore next:

### 📚 Learn More
- [Building Custom Tools](guides/custom-tools) - Add capabilities to your agents
- [Multi-Agent Patterns](guides/multi-agent-systems) - Advanced collaboration patterns
- [Flow Orchestration](guides/flow-orchestration) - Complex workflows

### 🔧 Advanced Features
- [MCP Integration](guides/mcp-servers) - Connect to external services
- [Enterprise Features](enterprise/overview) - Production-ready capabilities
- [API Reference](api/overview) - Complete API documentation

### 💡 Examples
- [Basic Examples](examples/basic-examples) - Simple agent patterns
- [Integration Examples](examples/integration-examples) - Real-world integrations
- [Advanced Examples](examples/advanced-examples) - Complex systems

## Common Patterns

### Error Handling

```python
@app.tool(description="Safe division")
async def safe_divide(a: float, b: float) -> str:
    try:
        if b == 0:
            return "Error: Division by zero"
        return str(a / b)
    except Exception as e:
        return f"Error: {str(e)}"
```

### Environment Configuration

```python
import os
from dotenv import load_dotenv

load_dotenv()

llm = OpenAIChatLLM(
    api_key=os.getenv("OPENAI_API_KEY"),
    model_name=os.getenv("OPENAI_MODEL_NAME", "gpt-3.5-turbo"),
    api_base_url=os.getenv("OPENAI_API_BASE")
)
```

### Logging

```python
from tframex.util.logging import setup_logging
import logging

setup_logging(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.tool(description="Tool with logging")
async def logged_tool(param: str) -> str:
    logger.info(f"Tool called with param: {param}")
    result = f"Processed: {param}"
    logger.info(f"Tool returning: {result}")
    return result
```

## Getting Help

- 💬 [Discord Community](https://discord.gg/DkzMzwBTaw) - Get help from the community
- 📖 [Full Documentation](/) - Comprehensive guides and references
- 🐛 [GitHub Issues](https://github.com/TesslateAI/TFrameX/issues) - Report bugs or request features