# Simple Agent - TFrameX Basic Example

A step up from Hello World, this example demonstrates agents with tools, memory, and more sophisticated interactions.

## 🎯 What You'll Learn

- Creating agents with custom tools
- Memory management and conversation history
- Tool integration and execution
- Template variables in system prompts
- Agent configuration options

## 📁 Project Structure

```
simple-agent/
├── README.md              # This guide
├── requirements.txt       # Dependencies
├── .env.example          # Environment template
├── main.py               # Main application
├── config/
│   ├── agents.py         # Agent definitions
│   └── tools.py          # Tool definitions
├── data/
│   └── sample_data.json  # Sample data for tools
└── docs/
    ├── setup.md          # Setup instructions
    └── usage.md          # Usage examples
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

## 🔧 Features Demonstrated

### **Tools Integration**
- Math calculations
- File operations
- Data processing
- API simulations

### **Memory Management**
- Conversation history
- Context retention
- Memory limits

### **Agent Configuration**
- Custom system prompts
- Template variables
- Tool assignments

## 💻 Code Examples

### **Agent with Tools**
```python
@app.agent(
    name="CalculatorAgent",
    tools=["calculate", "save_result"],
    system_prompt="You are a calculator assistant. Use tools to perform calculations and save results."
)
async def calculator_agent():
    pass
```

### **Tool Definition**
```python
@app.tool(description="Performs mathematical calculations")
async def calculate(expression: str) -> str:
    try:
        result = eval(expression)  # Note: Use safely in production
        return f"Result: {result}"
    except Exception as e:
        return f"Error: {str(e)}"
```

## 🎮 Interactive Features

- Calculator agent for math operations
- File manager for data operations
- Personal assistant with memory
- Multi-turn conversations

## 📚 Key Concepts

- **Tool Registration**: Using `@app.tool` decorator
- **Agent-Tool Binding**: Assigning tools to specific agents
- **Memory Persistence**: Maintaining conversation context
- **Error Handling**: Graceful tool failure management

## 🔍 What's Next?

- Explore [Tool Integration](../tool-integration/) for advanced tool usage
- Try [Sequential Pattern](../../02-pattern-examples/sequential-pattern/) for multi-agent workflows