---
sidebar_position: 1
title: CLI Overview
---

# TFrameX CLI Overview

The TFrameX CLI provides powerful command-line tools for building, testing, and deploying AI agent applications. With simple commands, you can start interactive sessions, create projects, and launch web interfaces.

## Installation

The CLI is automatically installed when you install TFrameX:

```bash
pip install tframex
```

Verify installation:
```bash
tframex --help
```

## Available Commands

The TFrameX CLI provides three main commands:

### 🚀 `tframex basic`
Start an interactive AI session with a pre-configured assistant.

```bash
tframex basic
```

**Features:**
- Instant AI interaction
- Built-in time tool
- Environment auto-detection
- Demo mode without API keys

### 📁 `tframex setup`
Create a complete TFrameX project with proper structure.

```bash
tframex setup my-project
```

**Creates:**
- Project scaffold
- Agent configurations
- Tool templates
- Environment setup
- Documentation

### 🌐 `tframex serve`
Launch a web interface for your agents.

```bash
tframex serve [--host HOST] [--port PORT]
```

**Provides:**
- Browser-based chat
- Real-time interaction
- Session management
- REST API endpoints

## Quick Start

### 1. Set Your API Key

```bash
# For OpenAI
export OPENAI_API_KEY="sk-..."

# For Anthropic/Claude
export ANTHROPIC_API_KEY="sk-ant-..."

# For local models (Ollama)
export OPENAI_API_KEY="ollama"
export OPENAI_API_BASE="http://localhost:11434/v1"
```

### 2. Try Interactive Mode

```bash
tframex basic
```

```
🚀 Starting TFrameX Basic Interactive Session
==================================================

Welcome to TFrameX! This is a basic interactive session.
Type 'exit' or 'quit' to end the session.

You: Hello! What can you do?
BasicAssistant: I'm a helpful AI assistant with access to basic tools. I can help with general questions, tell you the current time, and assist with problem-solving. How can I help you today?

You: What time is it?
BasicAssistant: [get_current_time()] The current time is 2024-01-15 14:30:45.

You: exit
👋 Thanks for using TFrameX!
```

### 3. Create a Project

```bash
tframex setup my-ai-assistant
cd my-ai-assistant
```

This creates:
```
my-ai-assistant/
├── main.py              # Entry point
├── config/
│   ├── agents.py        # Agent definitions
│   └── tools.py         # Tool configurations
├── data/                # Data storage
├── docs/                # Documentation
├── requirements.txt     # Dependencies
├── .env.example        # Environment template
├── .gitignore          # Git configuration
└── README.md           # Project guide
```

### 4. Configure and Run

```bash
# Set up environment
cp .env.example .env
# Edit .env with your API keys

# Install dependencies
pip install -r requirements.txt

# Run your project
python main.py
```

## Environment Variables

The CLI automatically detects configuration from environment variables:

### OpenAI Configuration
```bash
OPENAI_API_KEY=sk-proj-...
OPENAI_API_BASE=https://api.openai.com/v1  # Optional
OPENAI_MODEL_NAME=gpt-3.5-turbo           # Optional
```

### Anthropic Configuration
```bash
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_BASE=https://api.anthropic.com/v1
OPENAI_MODEL_NAME=claude-3-sonnet-20240229
```

### Llama/Compatible APIs
```bash
LLAMA_API_KEY=your-key
LLAMA_BASE_URL=https://api.llama.com/compat/v1/
LLAMA_MODEL=model-name
```

### Framework Settings
```bash
TFRAMEX_LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR
```

## CLI Architecture

The CLI is built on top of TFrameX's core components:

```python
# Simplified CLI structure
tframex/cli.py
├── create_basic_app()      # Basic app configuration
├── run_basic_session()     # Interactive mode
├── setup_project()         # Project scaffolding
├── serve_webapp()          # Web server
└── main()                  # Entry point
```

## Common Workflows

### Development Workflow

```bash
# 1. Quick prototype
tframex basic

# 2. Create project when ready
tframex setup my-project
cd my-project

# 3. Develop and test
python main.py

# 4. Web interface
tframex serve
```

### Production Deployment

```bash
# 1. Create production project
tframex setup prod-app

# 2. Configure for production
export OPENAI_API_KEY="${PROD_API_KEY}"

# 3. Install with web support
pip install tframex[web]

# 4. Run web server
tframex serve --host 0.0.0.0 --port 8080
```

## Features

### Auto-Detection
The CLI automatically detects:
- Available API keys
- LLM provider type
- Model configurations
- Environment settings

### Demo Mode
If no API keys are found, the CLI runs in demo mode:
```
⚠️  No API key found in environment variables.
   Set OPENAI_API_KEY or LLAMA_API_KEY to use your LLM.
   For now, using demo mode with placeholder responses.
```

### Project Templates
Generated projects include:
- Working agent examples
- Tool templates with documentation
- Environment configuration
- Git setup
- Comprehensive README

### Web Interface
The built-in web server provides:
- Clean chat interface
- Real-time responses
- Mobile-friendly design
- REST API for integration

## Best Practices

### 1. Start Simple
Use `tframex basic` to test ideas before creating a full project.

### 2. Use Environment Files
Keep API keys in `.env` files, never in code:
```bash
# .env
OPENAI_API_KEY=sk-...
PROJECT_NAME="My Assistant"
```

### 3. Modular Design
Organize agents and tools in separate configuration files:
- `config/agents.py` - Agent definitions
- `config/tools.py` - Tool implementations

### 4. Version Control
The generated `.gitignore` excludes sensitive files:
```gitignore
.env
.env.local
__pycache__/
*.pyc
```

## Troubleshooting

### Command Not Found
```bash
# Reinstall TFrameX
pip uninstall tframex
pip install tframex

# Check PATH
which tframex
```

### API Key Issues
```bash
# Check environment
echo $OPENAI_API_KEY

# Set for session
export OPENAI_API_KEY="your-key"
```

### Port Already in Use
```bash
# Use different port
tframex serve --port 3000

# Check what's using port
lsof -i :8000  # Mac/Linux
netstat -ano | findstr :8000  # Windows
```

## Next Steps

- Explore individual commands: [basic](basic), [setup](setup), [serve](serve)
- Read the [command reference](commands) for detailed options
- Check out [examples](../examples/overview) for inspiration
- Learn about [enterprise features](../enterprise/overview)

## Getting Help

- 💬 [Discord Community](https://discord.gg/DkzMzwBTaw)
- 📖 [Full Documentation](/)
- 🐛 [GitHub Issues](https://github.com/TesslateAI/TFrameX/issues)