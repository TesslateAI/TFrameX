---
sidebar_position: 3
title: tframex basic
---

# tframex basic

The `tframex basic` command provides an instant interactive AI session with a pre-configured assistant. It's the fastest way to experience TFrameX's capabilities.

## Overview

```bash
tframex basic
```

This command:
- Starts an interactive chat session
- Provides a basic AI assistant with tools
- Auto-detects LLM configuration
- Offers demo mode without API keys

## Features

### 🤖 Pre-configured Assistant

The basic assistant comes with:
- General conversation abilities
- Time-awareness tool
- Helpful, concise responses
- Context memory management

### 🔧 Built-in Tools

**get_current_time** - Returns the current date and time
```
You: What time is it?
Assistant: [get_current_time()] The current time is 2024-01-15 14:30:45.
```

### 🔄 Interactive Commands

- `exit` or `quit` - End the session
- `switch` - Change agents (when multiple available)
- Regular text - Chat with the assistant

### 🎯 Auto-Detection

Automatically detects configuration from environment:
1. Checks for OpenAI credentials
2. Checks for Llama/compatible API credentials  
3. Falls back to demo mode if none found

## Configuration

### OpenAI

```bash
export OPENAI_API_KEY="sk-proj-..."
export OPENAI_MODEL_NAME="gpt-3.5-turbo"  # Optional
tframex basic
```

### Anthropic Claude

```bash
export ANTHROPIC_API_KEY="sk-ant-..."
export OPENAI_API_BASE="https://api.anthropic.com/v1"
export OPENAI_MODEL_NAME="claude-3-sonnet-20240229"
tframex basic
```

### Llama API

```bash
export LLAMA_API_KEY="LLM|..."
export LLAMA_BASE_URL="https://api.llama.com/compat/v1/"
export LLAMA_MODEL="Llama-4-Maverick-17B"
tframex basic
```

### Local Models (Ollama)

```bash
# Start Ollama first
ollama serve

# Configure TFrameX
export OPENAI_API_KEY="ollama"
export OPENAI_API_BASE="http://localhost:11434/v1"
export OPENAI_MODEL_NAME="llama3"
tframex basic
```

### Other Compatible APIs

```bash
export OPENAI_API_KEY="your-api-key"
export OPENAI_API_BASE="https://your-api.com/v1"
export OPENAI_MODEL_NAME="your-model"
tframex basic
```

## Usage Examples

### Basic Interaction

```bash
$ tframex basic

🚀 Starting TFrameX Basic Interactive Session
==================================================

Welcome to TFrameX! This is a basic interactive session.
Type 'exit' or 'quit' to end the session.

You: Hello! Who are you?
BasicAssistant: I'm BasicAssistant, an AI assistant created with TFrameX. I'm here to help with general questions, conversations, and I can tell you the current time. How can I assist you today?

You: Can you help me understand Python decorators?
BasicAssistant: Python decorators are a way to modify or enhance functions without changing their code. They use the @ syntax and wrap functions with additional functionality.

Here's a simple example:

```python
def timer_decorator(func):
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        print(f"{func.__name__} took {time.time() - start:.2f} seconds")
        return result
    return wrapper

@timer_decorator
def slow_function():
    time.sleep(1)
    return "Done"

slow_function()  # Prints: slow_function took 1.00 seconds
```

Decorators are commonly used for logging, timing, authentication, and caching.

You: What's the current date and time?
BasicAssistant: [get_current_time()] The current date and time is 2024-01-15 14:45:22.

You: exit
👋 Thanks for using TFrameX!
```

### Demo Mode

When no API keys are configured:

```bash
$ tframex basic

⚠️  No API key found in environment variables.
   Set OPENAI_API_KEY or LLAMA_API_KEY to use your LLM.
   For now, using demo mode with placeholder responses.

🚀 Starting TFrameX Basic Interactive Session
==================================================

You: Hello
BasicAssistant: [Demo Mode] This is a placeholder response. Please configure an API key to use real AI capabilities.
```

## Implementation Details

### Assistant Configuration

The basic assistant is created with:

```python
assistant = LLMAgent(
    name="BasicAssistant",
    description="A helpful AI assistant with basic tools",
    llm=llm,  # Auto-configured from environment
    system_prompt="""You are a helpful AI assistant created with TFrameX.
        
You have access to basic tools and can help with:
- General questions and conversations
- Time-related queries
- Basic problem solving

If you don't have access to external tools or APIs, you can still provide helpful responses based on your training."""
)
```

### Tool Registration

```python
def get_current_time() -> str:
    """Get the current date and time."""
    from datetime import datetime
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

time_tool = Tool(
    name="get_current_time",
    func=get_current_time,
    description="Get the current date and time",
    parameters_schema=ToolParameters(properties={}, required=None)
)
app.register_tool(time_tool)
```

## Advanced Usage

### Using with Scripts

You can pipe input to the basic session:

```bash
echo "What is the capital of France?" | tframex basic
```

### Custom Environment

Create a `.env` file for consistent configuration:

```bash
# .env
OPENAI_API_KEY=sk-proj-...
OPENAI_MODEL_NAME=gpt-4
TFRAMEX_LOG_LEVEL=INFO
```

Then:
```bash
source .env && tframex basic
```

### Debug Mode

Enable detailed logging:

```bash
export TFRAMEX_LOG_LEVEL=DEBUG
tframex basic
```

## Troubleshooting

### No Response from AI

**Issue:** Assistant doesn't respond or errors occur
**Solution:** Check API key and network connection
```bash
# Verify API key is set
echo $OPENAI_API_KEY

# Test API connection
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"
```

### Tool Execution Errors

**Issue:** Tools fail to execute
**Solution:** Check debug logs
```bash
export TFRAMEX_LOG_LEVEL=DEBUG
tframex basic
```

### Memory Issues

**Issue:** Long conversations become slow
**Solution:** Exit and restart session, or implement memory limits in custom agents

### Demo Mode Activation

**Issue:** Always runs in demo mode despite API key
**Solution:** Ensure environment variables are properly exported
```bash
# Wrong (doesn't export)
OPENAI_API_KEY=sk-...

# Correct (exports to child processes)
export OPENAI_API_KEY=sk-...
```

## Comparison with Full Project

| Feature | `tframex basic` | Full Project |
|---------|----------------|--------------|
| Setup Time | Instant | Few minutes |
| Customization | Limited | Full control |
| Tools | Basic only | Unlimited |
| Agents | Single | Multiple |
| Configuration | Environment | Files + Code |
| Use Case | Testing/Demo | Production |

## Best Practices

### 1. Quick Testing
Use `tframex basic` for:
- Testing API connectivity
- Trying different models
- Quick interactions
- Learning TFrameX

### 2. Environment Management
```bash
# Create aliases for different configs
alias tframex-gpt4="OPENAI_MODEL_NAME=gpt-4 tframex basic"
alias tframex-claude="OPENAI_API_BASE=https://api.anthropic.com/v1 tframex basic"
```

### 3. Session Management
- Keep sessions focused on specific topics
- Exit and restart for context reset
- Use for prototyping before building full agents

## Migration to Full Project

When ready to move beyond basic:

```bash
# 1. Create project from your learnings
tframex setup my-advanced-assistant

# 2. Copy useful patterns
cd my-advanced-assistant
# Edit config/agents.py with your improvements

# 3. Add custom tools
# Edit config/tools.py

# 4. Run enhanced version
python main.py
```

## Limitations

- Single agent only
- Limited tool selection
- No persistent storage
- No custom configurations
- No multi-agent workflows

For advanced features, create a full project with `tframex setup`.

## Next Steps

- Try different LLM providers
- Explore [project creation](setup) for customization
- Learn about [web interfaces](serve)
- Study [agent development](../concepts/agents)