# Hello World - TFrameX Basic Example

Welcome to your first TFrameX example! This demonstrates the most basic usage of TFrameX with a simple agent that greets users.

## 🎯 What You'll Learn

- How to create a TFrameX application
- How to define a simple agent
- How to run agents and get responses
- Basic TFrameX concepts and structure

## 📁 Project Structure

```
hello-world/
├── README.md              # This guide
├── requirements.txt       # Python dependencies
├── .env.example          # Environment template
├── main.py               # Main application
├── config/
│   └── agents.py         # Agent definitions
└── docs/
    ├── setup.md          # Setup instructions
    └── usage.md          # Usage examples
```

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Environment
```bash
cp .env.example .env
# Edit .env with your LLM settings
```

### 3. Run the Example
```bash
python main.py
```

## 🔧 Configuration

### Environment Variables (.env)
```env
# Required: LLM Configuration
OPENAI_API_KEY=your_api_key_here
OPENAI_API_BASE=https://api.openai.com/v1
OPENAI_MODEL_NAME=gpt-3.5-turbo

# Optional: Application Settings
APP_NAME=Hello World TFrameX
LOG_LEVEL=INFO
```

### For Local Models (Ollama)
```env
OPENAI_API_BASE=http://localhost:11434/v1
OPENAI_API_KEY=ollama
OPENAI_MODEL_NAME=llama3
```

## 📖 Code Walkthrough

### 1. Application Setup
```python
from tframex import TFrameXApp, OpenAIChatLLM, Message

# Create LLM instance
llm = OpenAIChatLLM(
    model_name=os.getenv("OPENAI_MODEL_NAME", "gpt-3.5-turbo"),
    api_base_url=os.getenv("OPENAI_API_BASE"),
    api_key=os.getenv("OPENAI_API_KEY")
)

# Initialize TFrameX app
app = TFrameXApp(default_llm=llm)
```

### 2. Agent Definition
```python
@app.agent(
    name="GreeterAgent",
    description="A friendly greeting agent",
    system_prompt="You are a friendly greeter. Greet the user warmly and ask how you can help them today."
)
async def greeter_agent():
    pass  # Logic handled by TFrameX LLMAgent
```

### 3. Agent Execution
```python
async with app.run_context() as rt:
    response = await rt.call_agent(
        "GreeterAgent",
        Message(role="user", content="Hello!")
    )
    print(f"Agent: {response.content}")
```

## 🎮 Interactive Mode

The example includes an interactive mode where you can chat with the agent:

```python
async with app.run_context() as rt:
    await rt.interactive_chat(default_agent_name="GreeterAgent")
```

## 📚 Key Concepts

### **TFrameXApp**
- Central application instance
- Manages agents, tools, and configuration
- Provides runtime contexts

### **Agents**
- Autonomous entities powered by LLMs
- Defined using decorators (`@app.agent`)
- Can have custom system prompts and behaviors

### **Runtime Context**
- Execution environment for agents
- Manages LLM connections and cleanup
- Used with `async with app.run_context()`

### **Messages**
- Standard communication format
- Contains role (user/assistant/tool) and content
- Used for all agent interactions

## 🔍 What's Next?

After running this example, try:

1. **Modify the system prompt** to change the agent's personality
2. **Add template variables** to the system prompt
3. **Experiment with different LLM models**
4. **Move to the next example**: [Simple Agent](../simple-agent/)

## 🐛 Troubleshooting

### Common Issues

**Error: "No module named 'tframex'"**
```bash
pip install tframex
```

**Error: "OpenAI API key not found"**
- Check your `.env` file has `OPENAI_API_KEY` set
- Ensure the `.env` file is in the same directory as `main.py`

**Error: "Connection failed"**
- Verify your `OPENAI_API_BASE` URL is correct
- For local models, ensure the server is running

### Getting Help

- **Documentation**: [TFrameX Docs](https://tframex.tesslate.com/)
- **Discord**: [Join our Discord](https://discord.gg/DkzMzwBTaw)
- **Issues**: [GitHub Issues](https://github.com/TesslateAI/TFrameX/issues)

## 📄 License

This example is provided under the MIT License.