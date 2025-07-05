# test-project

A TFrameX project for building AI agents and workflows.

## Setup

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys and configuration
   ```

3. **Run the application:**
   ```bash
   python main.py
   ```

## Project Structure

```
test-project/
├── main.py              # Main application entry point
├── config/
│   ├── agents.py        # Agent configurations
│   └── tools.py         # Tool configurations
├── data/                # Data files and storage
├── docs/                # Documentation
├── requirements.txt     # Python dependencies
├── .env.example        # Environment template
└── README.md           # This file
```

## Adding Agents

Edit `config/agents.py` to add new agents:

```python
new_agent = LLMAgent(
    name="NewAgent",
    description="Description of what this agent does",
    llm=llm,
    system_prompt="Agent instructions..."
)
app.register_agent(new_agent)
```

## Adding Tools

Edit `config/tools.py` to add new tools:

```python
def create_custom_tool():
    # Implement your tool logic
    pass

app.register_tool(create_custom_tool())
```

## Usage

Once running, you can:
- Chat with your agents interactively
- Type 'switch' to change between agents
- Type 'exit' or 'quit' to end the session

## Next Steps

- Customize agents in `config/agents.py`
- Add new tools in `config/tools.py`
- Explore TFrameX documentation for advanced features
- Consider adding MCP servers for external integrations

Generated with TFrameX CLI: `tframex setup test-project`
