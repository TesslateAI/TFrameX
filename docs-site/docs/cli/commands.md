---
sidebar_position: 2
title: Command Reference
---

# TFrameX CLI Command Reference

Complete reference for all TFrameX CLI commands and options.

## Global Options

```bash
tframex [--help] [--version] <command> [options]
```

### Options
- `--help`, `-h` - Show help message and exit
- `--version`, `-v` - Show TFrameX version (if implemented)

## Commands

### `tframex basic`

Start an interactive AI session with a basic assistant.

```bash
tframex basic
```

#### Synopsis
Launches an interactive chat session with a pre-configured AI assistant. The session includes basic tools and automatic environment detection.

#### Options
No command-specific options. Configuration is via environment variables.

#### Environment Variables
- `OPENAI_API_KEY` - OpenAI API key
- `OPENAI_API_BASE` - API base URL (optional)
- `OPENAI_MODEL_NAME` - Model to use (optional, default: gpt-3.5-turbo)
- `LLAMA_API_KEY` - Alternative: Llama API key  
- `LLAMA_BASE_URL` - Llama API endpoint
- `LLAMA_MODEL` - Llama model name

#### Examples

**Basic usage:**
```bash
export OPENAI_API_KEY="sk-..."
tframex basic
```

**With Anthropic:**
```bash
export ANTHROPIC_API_KEY="sk-ant-..."
export OPENAI_API_BASE="https://api.anthropic.com/v1"
export OPENAI_MODEL_NAME="claude-3-sonnet-20240229"
tframex basic
```

**With local Ollama:**
```bash
export OPENAI_API_KEY="ollama"
export OPENAI_API_BASE="http://localhost:11434/v1"
export OPENAI_MODEL_NAME="llama3"
tframex basic
```

#### Interactive Commands
While in the session:
- `exit` or `quit` - End the session
- `switch` - Change agents (if multiple available)
- Regular text - Chat with the assistant

#### Exit Codes
- `0` - Successful session
- `1` - Error (configuration, API, etc.)

---

### `tframex setup`

Create a new TFrameX project with complete scaffolding.

```bash
tframex setup <project-name> [options]
```

#### Synopsis
Generates a complete project structure with configuration files, example code, and documentation.

#### Arguments
- `project-name` (required) - Name of the project directory to create

#### Options
- `--template <name>` - Project template to use (default: `basic`)
  - `basic` - Standard project structure

#### Generated Structure
```
project-name/
├── main.py              # Application entry point
├── config/
│   ├── __init__.py      # Package initialization
│   ├── agents.py        # Agent configurations
│   └── tools.py         # Tool definitions
├── data/                # Data storage directory
├── docs/                # Project documentation
├── requirements.txt     # Python dependencies
├── .env.example        # Environment template
├── .gitignore          # Git ignore rules
└── README.md           # Project documentation
```

#### Examples

**Create a new project:**
```bash
tframex setup my-assistant
cd my-assistant
```

**Overwrite existing directory:**
```bash
tframex setup existing-project
# Prompts: Directory 'existing-project' already exists. Overwrite? (y/N):
```

#### Generated Files

**main.py:**
```python
#!/usr/bin/env python3
"""
{project_name} - TFrameX Project
Generated with: tframex setup {project_name}
"""
import asyncio
from tframex import TFrameXApp
from config.agents import setup_agents
from config.tools import setup_tools

def create_app() -> TFrameXApp:
    app = TFrameXApp()
    setup_tools(app)
    setup_agents(app)
    return app

async def main():
    print(f"🚀 Starting {project_name}")
    app = create_app()
    async with app.run_context() as rt:
        await rt.interactive_chat()

if __name__ == "__main__":
    asyncio.run(main())
```

#### Exit Codes
- `0` - Project created successfully
- `1` - Error (permissions, user cancelled, etc.)

---

### `tframex serve`

Launch a web interface for TFrameX agents.

```bash
tframex serve [options]
```

#### Synopsis
Starts a Flask-based web server providing a browser interface for interacting with agents.

#### Options
- `--host <host>` - Host to bind to (default: `localhost`)
- `--port <port>` - Port to bind to (default: `8000`)

#### Requirements
```bash
pip install tframex[web]
# or
pip install flask>=3.0.0
```

#### Features
- Real-time chat interface
- Session management
- REST API endpoints
- Mobile-responsive design

#### API Endpoints

**GET /** - Main chat interface
```
Returns: HTML chat interface
```

**POST /chat** - Chat API endpoint
```json
Request:
{
  "message": "User message"
}

Response:
{
  "response": "AI response"
}
```

#### Examples

**Default server:**
```bash
tframex serve
# Serves at http://localhost:8000
```

**Custom port:**
```bash
tframex serve --port 3000
# Serves at http://localhost:3000
```

**Production deployment:**
```bash
tframex serve --host 0.0.0.0 --port 80
# Serves on all interfaces, port 80
```

**Behind a proxy:**
```bash
tframex serve --host 127.0.0.1 --port 8000
# Configure nginx/Apache to proxy to this
```

#### Web Interface

The web interface provides:

1. **Chat Area** - Message history display
2. **Input Field** - User message input
3. **Send Button** - Submit messages
4. **Status Indicator** - Shows when AI is thinking

#### Security Considerations

- Default binds to localhost only
- Use reverse proxy for production
- Implement authentication as needed
- Set rate limiting for public deployment

#### Exit Codes
- `0` - Server stopped gracefully
- `1` - Error (port in use, missing dependencies, etc.)

---

## Command Combinations

### Full Development Workflow

```bash
# 1. Test ideas
tframex basic

# 2. Create project
tframex setup ai-assistant
cd ai-assistant

# 3. Configure
cp .env.example .env
vim .env  # Add API keys

# 4. Install and run
pip install -r requirements.txt
python main.py

# 5. Web interface
pip install flask
tframex serve --port 3000
```

### Quick Demo

```bash
# Set API key and start
export OPENAI_API_KEY="sk-..."
tframex basic
```

### Production Setup

```bash
# Create and configure
tframex setup prod-app
cd prod-app
cp .env.example .env.production

# Install all dependencies
pip install -r requirements.txt
pip install tframex[web]

# Run with production settings
export $(cat .env.production | xargs)
tframex serve --host 0.0.0.0 --port 8080
```

## Error Messages

### Common Errors and Solutions

**No API key found:**
```
⚠️  No API key found in environment variables.
   Set OPENAI_API_KEY or LLAMA_API_KEY to use your LLM.
```
Solution: Export your API key before running.

**Flask not installed:**
```
❌ Flask is required for web server functionality.
   Install with: pip install flask
```
Solution: Install Flask or use `pip install tframex[web]`.

**Port already in use:**
```
❌ Error starting web server: [Errno 48] Address already in use
```
Solution: Use a different port with `--port`.

**Permission denied:**
```
❌ Error creating project: [Errno 13] Permission denied
```
Solution: Check directory permissions or use sudo (not recommended).

## Configuration Files

### Environment Variables (.env)

```bash
# LLM Configuration
OPENAI_API_KEY=sk-...
OPENAI_MODEL_NAME=gpt-3.5-turbo

# Alternative LLM
LLAMA_API_KEY=...
LLAMA_BASE_URL=https://api.llama.com/compat/v1/
LLAMA_MODEL=model-name

# Framework Settings
TFRAMEX_LOG_LEVEL=INFO
PROJECT_NAME="My Assistant"
ENVIRONMENT=development
```

### Project Configuration

Projects created with `tframex setup` include:

1. **requirements.txt** - Python dependencies
2. **.env.example** - Environment template
3. **.gitignore** - Version control setup
4. **README.md** - Project documentation

## Advanced Usage

### Custom Templates (Future)

```bash
# Future feature
tframex setup my-project --template enterprise
tframex setup my-project --template research
tframex setup my-project --template chatbot
```

### Configuration Overrides (Future)

```bash
# Future feature
tframex basic --config custom-config.yaml
tframex serve --ssl-cert cert.pem --ssl-key key.pem
```

## Debugging

### Enable Debug Logging

```bash
export TFRAMEX_LOG_LEVEL=DEBUG
tframex basic
```

### Verbose Output

```python
# In your code
from tframex.util.logging import setup_logging
import logging

setup_logging(level=logging.DEBUG)
```

### Check Installation

```bash
# Verify CLI installation
which tframex
tframex --help

# Check Python import
python -c "import tframex; print(tframex.__version__)"
```

## Platform-Specific Notes

### Windows

```powershell
# Set environment variable
$env:OPENAI_API_KEY = "sk-..."

# Run commands
tframex basic
```

### macOS/Linux

```bash
# Set environment variable
export OPENAI_API_KEY="sk-..."

# Or use .env file
source .env
```

### Docker

```dockerfile
FROM python:3.11-slim
RUN pip install tframex[web]
ENV OPENAI_API_KEY=""
CMD ["tframex", "serve", "--host", "0.0.0.0"]
```

## Next Steps

- Learn about [basic command](basic) in detail
- Understand [project setup](setup) options
- Explore [web serving](serve) features
- Read about [enterprise deployment](../enterprise/deployment)