# TFrameX CLI Reference

Complete command-line interface reference for TFrameX framework.

## Overview

The TFrameX CLI provides three main commands for building and running AI agent applications:

```bash
tframex basic        # Interactive AI session
tframex setup        # Project scaffolding
tframex serve        # Web interface
```

## Global Options

```bash
tframex --help       # Show help and exit
tframex --version    # Show version and exit (if implemented)
```

## Command Reference

### `tframex basic`

Start an interactive AI session with a basic assistant.

#### Syntax
```bash
tframex basic
```

#### Description
Launches an interactive chat session using TFrameX's built-in `interactive_chat()` system. The session includes:
- A basic AI assistant with time tool
- Agent switching capabilities ('switch' command)
- Graceful exit ('exit', 'quit' commands)
- Environment-based LLM configuration
- Demo mode if no API credentials are found

#### Environment Variables
The command automatically detects LLM configuration from environment variables in this priority order:

**OpenAI Configuration:**
```bash
OPENAI_API_KEY=sk-proj-...              # Required
OPENAI_API_BASE=https://api.openai.com/v1  # Optional, defaults to OpenAI
OPENAI_MODEL_NAME=gpt-3.5-turbo            # Optional, defaults to gpt-3.5-turbo
```

**Llama API Configuration:**
```bash
LLAMA_API_KEY=LLM|...                    # Required
LLAMA_BASE_URL=https://api.llama.com/compat/v1/  # Optional
LLAMA_MODEL=Llama-4-Maverick-17B-128E-Instruct-FP8  # Optional
```

**Generic OpenAI-Compatible API:**
```bash
OPENAI_API_KEY=your_api_key             # Required
OPENAI_API_BASE=https://your-api.com/v1 # Required for non-OpenAI APIs
OPENAI_MODEL_NAME=your_model_name       # Optional
```

#### Example Usage
```bash
# Set up your API key
export OPENAI_API_KEY="sk-proj-..."

# Start interactive session
tframex basic

# In the session:
You: What time is it?
BasicAssistant: [get_current_time()] The current time is 2024-01-15 14:30:22.

You: switch
Available agents: BasicAssistant
Enter the name of the agent you want to switch to: BasicAssistant

You: exit
👋 Thanks for using TFrameX!
```

#### Demo Mode
If no API keys are found, the command runs in demo mode:
```bash
tframex basic
⚠️  No API key found in environment variables.
   Set OPENAI_API_KEY or LLAMA_API_KEY to use your LLM.
   For now, using demo mode with placeholder responses.
```

#### Exit Codes
- `0` - Success
- `1` - Error (API issues, configuration problems, etc.)

---

### `tframex setup <project-name>`

Create a new TFrameX project with complete scaffolding.

#### Syntax
```bash
tframex setup <project-name> [--template <template>]
```

#### Arguments
- `project-name` (required) - Name of the project directory to create

#### Options
- `--template <template>` - Project template to use (default: `basic`)
  - `basic` - Standard TFrameX project structure

#### Description
Creates a complete TFrameX project with:
- Organized directory structure
- Ready-to-run main application
- Configuration modules for agents and tools
- Environment templates
- Documentation and setup instructions
- Git configuration

#### Generated Structure
```
project-name/
├── main.py              # Application entry point
├── config/
│   ├── __init__.py      # Python package marker
│   ├── agents.py        # Agent configuration module
│   └── tools.py         # Tool configuration module
├── data/                # Data storage directory
├── docs/                # Project documentation
├── requirements.txt     # Python dependencies
├── .env.example        # Environment configuration template
├── .gitignore          # Git ignore rules
└── README.md           # Project documentation
```

#### Key Generated Files

**main.py** - Complete application entry point:
```python
#!/usr/bin/env python3
"""
project-name - TFrameX Project

Generated with: tframex setup project-name
"""
import asyncio
from tframex import TFrameXApp
from config.agents import setup_agents
from config.tools import setup_tools

def create_app() -> TFrameXApp:
    """Create and configure the TFrameX application."""
    app = TFrameXApp()
    setup_tools(app)
    setup_agents(app)
    return app

async def main():
    """Main application entry point."""
    print(f"🚀 Starting project-name")
    print("=" * 50)
    
    app = create_app()
    
    # Run interactive session
    async with app.run_context() as rt:
        await rt.interactive_chat()

if __name__ == "__main__":
    asyncio.run(main())
```

**config/agents.py** - Agent configuration module:
```python
"""
Agent configurations for this TFrameX project.
"""
import os
from tframex.agents.llm_agent import LLMAgent
from tframex.util.llms import OpenAIChatLLM

def setup_agents(app):
    """Setup and register agents with the app."""
    
    # Configure LLM from environment
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
    
    # Create main assistant agent
    assistant = LLMAgent(
        name="Assistant",
        description="A helpful AI assistant",
        llm=llm,
        system_prompt="""You are a helpful AI assistant with access to various tools.
        
You can help with:
- General questions and conversations
- Using available tools to solve problems
- Providing information and assistance

Always be helpful, accurate, and engaging."""
    )
    
    # Register agents
    app.register_agent(assistant)
    
    # Add more agents here as needed
```

**config/tools.py** - Tool configuration module:
```python
"""
Tool configurations for this TFrameX project.
"""
from tframex.util.tools import Tool, ToolParameters

def setup_tools(app):
    """Setup and register tools with the app."""
    
    # Register basic tools
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
    
    # Add more tools here as needed
    # Example:
    # def custom_function(param1: str, param2: int = 10) -> str:
    #     return f"Custom result: {param1} with {param2}"
    # 
    # custom_tool = Tool(
    #     name="custom_tool",
    #     func=custom_function,
    #     description="A custom tool example"
    # )
    # app.register_tool(custom_tool)
```

**.env.example** - Environment configuration template:
```bash
# Environment configuration for your TFrameX project
# Copy this file to .env and fill in your actual values

# LLM Configuration (choose one)
# For OpenAI:
OPENAI_API_KEY=your_openai_api_key_here
# OPENAI_API_BASE=https://api.openai.com/v1
# OPENAI_MODEL_NAME=gpt-3.5-turbo

# For Llama or other OpenAI-compatible APIs:
# LLAMA_API_KEY=your_llama_api_key_here
# LLAMA_BASE_URL=https://api.llama.com/compat/v1/
# LLAMA_MODEL=Llama-4-Maverick-17B-128E-Instruct-FP8

# Project Configuration
PROJECT_NAME="project-name"
ENVIRONMENT=development

# Add other environment variables here
```

#### Example Usage
```bash
# Create a new project
tframex setup my-ai-app
cd my-ai-app

# Setup environment
cp .env.example .env
# Edit .env with your API keys

# Install dependencies
pip install -r requirements.txt

# Run the application
python main.py
```

#### Overwrite Behavior
If the target directory already exists, the command will prompt for confirmation:
```bash
tframex setup existing-project
Directory 'existing-project' already exists. Overwrite? (y/N): n
❌ Setup cancelled.
```

#### Exit Codes
- `0` - Success
- `1` - Error (permission issues, user cancelled, etc.)

---

### `tframex serve`

Launch a web interface for TFrameX applications.

#### Syntax
```bash
tframex serve [--host <host>] [--port <port>]
```

#### Options
- `--host <host>` - Host to bind to (default: `localhost`)
- `--port <port>` - Port to bind to (default: `8000`)

#### Description
Starts a Flask-based web server that provides a browser-based chat interface for interacting with TFrameX agents. The server creates a basic TFrameX application with the same configuration as `tframex basic`.

#### Requirements
The serve command requires Flask. Install with:
```bash
pip install tframex[web]
```

Or manually:
```bash
pip install flask>=3.0.0
```

#### Web Interface Features
- **Real-time Chat**: Interactive chat interface with message history
- **Agent Integration**: Backend powered by TFrameX BasicAssistant
- **Responsive Design**: Works on desktop and mobile browsers
- **Error Handling**: Graceful error display and recovery
- **Session Management**: Maintains conversation context

#### HTTP Endpoints
- `GET /` - Main chat interface (HTML page)
- `POST /chat` - Chat API endpoint (JSON)

#### API Usage
**POST /chat**
```json
Request:
{
  "message": "What time is it?"
}

Response:
{
  "response": "The current time is 2024-01-15 14:30:22."
}
```

#### Example Usage
```bash
# Default server (localhost:8000)
tframex serve

# Custom port
tframex serve --port 3000

# Bind to all interfaces
tframex serve --host 0.0.0.0 --port 8080

# Access in browser
open http://localhost:8000
```

#### Production Deployment
```bash
# Production configuration
export OPENAI_API_KEY="sk-proj-..."

# Start production server
tframex serve --host 0.0.0.0 --port 80
```

#### Environment Variables
Uses the same environment variable detection as `tframex basic`:
- `OPENAI_API_KEY`, `OPENAI_API_BASE`, `OPENAI_MODEL_NAME`
- `LLAMA_API_KEY`, `LLAMA_BASE_URL`, `LLAMA_MODEL`

#### Security Considerations
- **API Keys**: Ensure environment variables are secure
- **Host Binding**: Use `localhost` for development, configure firewall for production
- **HTTPS**: Consider reverse proxy (nginx, Apache) for production TLS
- **Rate Limiting**: Implement rate limiting for production use

#### Exit Codes
- `0` - Success (server stopped gracefully)
- `1` - Error (port in use, missing dependencies, etc.)

## Environment Variable Reference

### LLM Configuration

#### OpenAI
```bash
OPENAI_API_KEY=sk-proj-...              # Your OpenAI API key
OPENAI_API_BASE=https://api.openai.com/v1  # API base URL (optional)
OPENAI_MODEL_NAME=gpt-3.5-turbo            # Model name (optional)
```

#### Llama API
```bash
LLAMA_API_KEY=LLM|...                   # Your Llama API key
LLAMA_BASE_URL=https://api.llama.com/compat/v1/  # API base URL
LLAMA_MODEL=Llama-4-Maverick-17B-128E-Instruct-FP8  # Model name
```

#### Custom OpenAI-Compatible
```bash
OPENAI_API_KEY=your_api_key             # API key
OPENAI_API_BASE=https://your-api.com/v1 # Custom API base URL
OPENAI_MODEL_NAME=your_model_name       # Model identifier
```

#### Local Development (Ollama)
```bash
OPENAI_API_KEY=ollama                   # Dummy key for Ollama
OPENAI_API_BASE=http://localhost:11434/v1  # Ollama API endpoint
OPENAI_MODEL_NAME=llama3                # Local model name
```

### Framework Configuration
```bash
TFRAMEX_LOG_LEVEL=INFO                  # Logging level (DEBUG, INFO, WARNING, ERROR)
MCP_LOG_LEVEL=INFO                      # MCP-specific logging level
TFRAMEX_ALLOW_NO_DEFAULT_LLM=false      # Allow apps without default LLM
```

### Project-Specific
```bash
PROJECT_NAME="My AI Project"            # Project display name
ENVIRONMENT=development                 # Environment (development, staging, production)
```

## Exit Codes

All TFrameX CLI commands use standard exit codes:
- `0` - Success
- `1` - General error (configuration, API, user cancellation)
- `2` - Usage error (invalid arguments, missing required parameters)

## Error Handling

### Common Error Scenarios

#### Missing Dependencies
```bash
❌ Flask is required for web server functionality.
   Install with: pip install flask
```

#### API Key Issues
```bash
⚠️  No API key found in environment variables.
   Set OPENAI_API_KEY or LLAMA_API_KEY to use your LLM.
```

#### Port Already in Use
```bash
❌ Error starting web server: [Errno 48] Address already in use
```

#### Permission Errors
```bash
❌ Error creating project: [Errno 13] Permission denied: 'project-name'
```

### Debugging

#### Enable Debug Logging
```bash
export TFRAMEX_LOG_LEVEL=DEBUG
tframex basic
```

#### Verify Installation
```bash
# Check CLI installation
which tframex
tframex --help

# Check TFrameX import
python -c "import tframex; print(tframex.__version__)"

# Check environment
echo $OPENAI_API_KEY
env | grep -E "(OPENAI|LLAMA)"
```

## Best Practices

### Development Workflow
1. **Start with basic**: Use `tframex basic` for quick testing and prototyping
2. **Use setup for projects**: Always use `tframex setup` for structured development
3. **Environment management**: Keep API keys in `.env` files, never in code
4. **Version control**: Add `.env` to `.gitignore`, use `.env.example` for templates

### Production Deployment
1. **Security**: Use environment variables or secret management for API keys
2. **Monitoring**: Implement logging and error tracking
3. **Performance**: Use connection pooling and caching where appropriate
4. **Scalability**: Consider load balancing for `tframex serve` deployments

### Project Organization
1. **Modular configuration**: Keep agents and tools in separate modules
2. **Documentation**: Update README.md with project-specific instructions
3. **Dependencies**: Pin versions in requirements.txt for reproducibility
4. **Testing**: Add unit tests for custom tools and agents

## Integration Examples

### CI/CD Pipeline
```yaml
# GitHub Actions example
- name: Test TFrameX Project
  run: |
    pip install -r requirements.txt
    export OPENAI_API_KEY="${{ secrets.OPENAI_API_KEY }}"
    python -m pytest tests/
```

### Docker Deployment
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
ENV OPENAI_API_KEY=""
EXPOSE 8000
CMD ["tframex", "serve", "--host", "0.0.0.0"]
```

### Kubernetes Deployment
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: tframex-app
spec:
  replicas: 3
  selector:
    matchLabels:
      app: tframex-app
  template:
    metadata:
      labels:
        app: tframex-app
    spec:
      containers:
      - name: tframex
        image: my-tframex-app:latest
        ports:
        - containerPort: 8000
        env:
        - name: OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: api-keys
              key: openai-key
        command: ["tframex", "serve", "--host", "0.0.0.0"]
```

This reference provides complete documentation for all TFrameX CLI commands, options, and usage patterns.