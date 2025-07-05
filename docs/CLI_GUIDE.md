# TFrameX CLI Guide

The TFrameX CLI provides a comprehensive command-line interface for building, running, and managing AI agent applications. After installing TFrameX, the `tframex` command becomes available globally.

## Installation

```bash
pip install tframex
```

After installation, verify the CLI is working:

```bash
tframex --help
```

## Commands Overview

The TFrameX CLI provides three main commands:

- **`tframex basic`** - Start an interactive AI session
- **`tframex setup <project>`** - Create a new TFrameX project
- **`tframex serve`** - Launch a web interface

## Command Reference

### `tframex basic`

Starts an interactive session with a basic AI assistant using TFrameX's built-in chat system.

```bash
tframex basic
```

**Features:**
- Interactive chat loop with agent switching
- Basic time tool included
- Automatic environment variable detection
- Graceful demo mode if no API keys are configured
- Built-in commands: 'exit', 'quit', 'switch'

**Environment Variables:**
The command will look for LLM configuration in this order:
```bash
# OpenAI Configuration
OPENAI_API_KEY=your_openai_key
OPENAI_API_BASE=https://api.openai.com/v1  # Optional
OPENAI_MODEL_NAME=gpt-3.5-turbo             # Optional

# Alternative: Llama/Other OpenAI-compatible APIs
LLAMA_API_KEY=your_llama_key
LLAMA_BASE_URL=https://api.llama.com/compat/v1/
LLAMA_MODEL=Llama-4-Maverick-17B-128E-Instruct-FP8
```

**Demo Mode:**
If no API keys are found, the command runs in demo mode with helpful guidance on configuration.

### `tframex setup <project-name>`

Creates a complete TFrameX project with proper structure and templates.

```bash
tframex setup myproject
```

**Options:**
- `--template basic` - Use basic project template (default)

**Generated Project Structure:**
```
myproject/
├── main.py              # Main application entry point
├── config/
│   ├── __init__.py      # Package initialization
│   ├── agents.py        # Agent configurations
│   └── tools.py         # Tool configurations
├── data/                # Data files and storage
├── docs/                # Documentation
├── requirements.txt     # Python dependencies
├── .env.example        # Environment template
├── .gitignore          # Git ignore rules
└── README.md           # Project documentation
```

**Key Files Generated:**

**main.py:**
- Complete application entry point
- Async main function with interactive chat
- Modular configuration loading
- Ready to run out of the box

**config/agents.py:**
- LLM configuration from environment variables
- Sample agent with proper system prompt
- Extensible agent registration pattern
- Support for multiple LLM providers

**config/tools.py:**
- Dynamic tool creation examples
- Time tool implementation
- Comments showing how to add custom tools
- Proper tool registration patterns

**.env.example:**
- Complete environment variable template
- Multiple LLM provider configurations
- Project-specific settings
- Security and deployment notes

**requirements.txt:**
- TFrameX dependency
- Common additional packages
- Comments for easy extension

**README.md:**
- Complete setup instructions
- Usage examples
- Project structure explanation
- Development guidance

### `tframex serve`

Launches a web-based chat interface for TFrameX applications.

```bash
tframex serve [--host HOST] [--port PORT]
```

**Options:**
- `--host` - Host to bind to (default: localhost)
- `--port` - Port to bind to (default: 8000)

**Examples:**
```bash
# Default (localhost:8000)
tframex serve

# Custom port
tframex serve --port 3000

# Custom host and port
tframex serve --host 0.0.0.0 --port 8080
```

**Web Interface Features:**
- Real-time chat interface
- Agent interaction through HTTP
- Session management
- Responsive design
- Error handling and status indicators

**Requirements:**
The serve command requires Flask. Install with:
```bash
pip install tframex[web]
```

**API Endpoints:**
- `GET /` - Main chat interface
- `POST /chat` - Chat API endpoint

## Environment Configuration

### LLM Provider Setup

**OpenAI:**
```bash
export OPENAI_API_KEY="sk-..."
export OPENAI_MODEL_NAME="gpt-3.5-turbo"  # Optional
```

**Llama API:**
```bash
export LLAMA_API_KEY="LLM|..."
export LLAMA_BASE_URL="https://api.llama.com/compat/v1/"
export LLAMA_MODEL="Llama-4-Maverick-17B-128E-Instruct-FP8"
```

**Other OpenAI-Compatible APIs:**
```bash
export OPENAI_API_KEY="your_key"
export OPENAI_API_BASE="https://your-api-endpoint.com/v1"
export OPENAI_MODEL_NAME="your-model-name"
```

### Environment File Management

For projects created with `tframex setup`:

1. **Copy the template:**
   ```bash
   cd myproject
   cp .env.example .env
   ```

2. **Edit configuration:**
   ```bash
   nano .env  # or your preferred editor
   ```

3. **Add to .gitignore (already included):**
   ```gitignore
   .env
   .env.local
   ```

## Workflow Examples

### Quick Start Development

```bash
# 1. Create new project
tframex setup my-ai-app
cd my-ai-app

# 2. Setup environment
cp .env.example .env
# Edit .env with your API keys

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run interactive session
python main.py
```

### Testing and Prototyping

```bash
# Quick interactive session for testing
tframex basic

# Test web interface
tframex serve --port 3000
```

### Production Deployment

```bash
# Create production project
tframex setup production-app
cd production-app

# Setup production environment
cp .env.example .env.production
# Configure production API keys and settings

# Install with web dependencies
pip install -r requirements.txt
pip install tframex[web]

# Run web server
tframex serve --host 0.0.0.0 --port 8080
```

## Advanced Usage

### Custom Tool Development

In your project's `config/tools.py`:

```python
from tframex.util.tools import Tool, ToolParameters, ToolParameterProperty

def create_weather_tool():
    def get_weather(city: str) -> str:
        # Your weather API logic here
        return f"Weather in {city}: Sunny, 25°C"
    
    return Tool(
        name="get_weather",
        func=get_weather,
        description="Get current weather for a city",
        parameters_schema=ToolParameters(
            properties={
                "city": ToolParameterProperty(
                    type="string",
                    description="The city to get weather for"
                )
            },
            required=["city"]
        )
    )

def setup_tools(app):
    app.register_tool(create_weather_tool())
```

### Multi-Agent Configuration

In your project's `config/agents.py`:

```python
def setup_agents(app):
    # Configure LLM
    llm = OpenAIChatLLM(...)
    
    # Create specialized agents
    research_agent = LLMAgent(
        name="Researcher",
        description="Research specialist",
        llm=llm,
        system_prompt="You are a research specialist..."
    )
    
    writer_agent = LLMAgent(
        name="Writer",
        description="Content writer",
        llm=llm,
        system_prompt="You are a professional writer..."
    )
    
    # Register agents
    app.register_agent(research_agent)
    app.register_agent(writer_agent)
```

### MCP Integration

Add MCP servers to your project:

```python
# In main.py
from tframex.mcp import MCPManager

async def create_app():
    app = TFrameXApp()
    
    # Setup MCP servers
    mcp_config = {
        "aws-docs": {
            "command": "uvx",
            "args": ["awslabs.aws-documentation-mcp-server@latest"]
        }
    }
    
    mcp_manager = MCPManager(mcp_config)
    app.set_mcp_manager(mcp_manager)
    
    # Continue with agent/tool setup
    return app
```

## Troubleshooting

### Common Issues

**1. Command not found: `tframex`**
```bash
# Reinstall TFrameX
pip uninstall tframex
pip install tframex

# Check installation
which tframex
```

**2. Import errors in basic mode**
```bash
# Check TFrameX installation
python -c "import tframex; print(tframex.__version__)"

# Reinstall if needed
pip install --upgrade tframex
```

**3. API key not recognized**
```bash
# Check environment variables
echo $OPENAI_API_KEY
echo $LLAMA_API_KEY

# Set for current session
export OPENAI_API_KEY="your_key_here"
```

**4. Web server won't start**
```bash
# Install web dependencies
pip install flask
# OR
pip install tframex[web]

# Check port availability
netstat -an | grep :8000
```

**5. Project generation fails**
```bash
# Check permissions
ls -la .
mkdir test && rmdir test

# Check available space
df -h .
```

### Debug Mode

Enable debug logging for troubleshooting:

```bash
# Set log level
export TFRAMEX_LOG_LEVEL=DEBUG

# Run with debug output
tframex basic
```

### Getting Help

**CLI Help:**
```bash
tframex --help
tframex basic --help
tframex setup --help
tframex serve --help
```

**Documentation:**
- [TFrameX GitHub](https://github.com/TesslateAI/TFrameX)
- [API Reference](API_REFERENCE.md)
- [Architecture Guide](ARCHITECTURE.md)
- [Examples Directory](../examples/)

## Best Practices

### Project Organization

1. **Use the setup command** - Always start with `tframex setup` for consistent structure
2. **Environment files** - Keep API keys in `.env`, not in code
3. **Modular configuration** - Use separate files for agents and tools
4. **Documentation** - Update README.md with project-specific instructions

### Development Workflow

1. **Start with basic** - Use `tframex basic` for quick testing
2. **Iterate on tools** - Develop tools in `config/tools.py` first
3. **Agent specialization** - Create focused agents for specific tasks
4. **Web testing** - Use `tframex serve` for user interface testing

### Production Deployment

1. **Environment management** - Use separate `.env` files for different environments
2. **Dependency locking** - Pin specific versions in `requirements.txt`
3. **Error handling** - Implement proper error handling in custom tools
4. **Monitoring** - Add logging and metrics for production use

### Security

1. **API key management** - Never commit `.env` files
2. **Input validation** - Validate all tool parameters
3. **Rate limiting** - Implement rate limiting for web interfaces
4. **Access control** - Consider authentication for production web interfaces

## Next Steps

After mastering the CLI basics:

1. **Explore Examples** - Check out [integration examples](../examples/03-integration-examples/)
2. **Advanced Patterns** - Learn about [execution patterns](../examples/02-pattern-examples/)
3. **Enterprise Features** - Explore [enterprise capabilities](ENTERPRISE.md)
4. **MCP Integration** - Add external tools via [MCP servers](MCP_INTEGRATION.md)
5. **Custom Development** - Build specialized agents for your use case