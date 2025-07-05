---
sidebar_position: 4
title: tframex setup
---

# tframex setup

The `tframex setup` command creates a complete TFrameX project with proper structure, configuration files, and working examples. It's the recommended way to start building production-ready AI applications.

## Overview

```bash
tframex setup <project-name> [options]
```

This command:
- Creates a complete project structure
- Generates configuration templates
- Provides working agent examples
- Sets up environment management
- Includes documentation

## Quick Start

```bash
# Create a new project
tframex setup my-assistant

# Navigate to project
cd my-assistant

# Configure environment
cp .env.example .env
# Edit .env with your API keys

# Install and run
pip install -r requirements.txt
python main.py
```

## Generated Structure

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

## File Details

### main.py

The entry point for your application:

```python
#!/usr/bin/env python3
"""
{project_name} - TFrameX Project

Generated with: tframex setup {project_name}
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


async def main():
    """Main application entry point."""
    print(f"🚀 Starting {project_name}")
    print("=" * 50)
    
    app = create_app()
    
    # Run interactive session
    async with app.run_context() as rt:
        await rt.interactive_chat()


if __name__ == "__main__":
    asyncio.run(main())
```

### config/agents.py

Agent configuration module:

```python
"""
Agent configurations for this TFrameX project.
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

### config/tools.py

Tool configuration module:

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

### .env.example

Environment configuration template:

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
PROJECT_NAME="{project_name}"
ENVIRONMENT=development

# Add other environment variables here
```

### requirements.txt

Project dependencies:

```
# TFrameX project requirements
tframex>=1.1.0
python-dotenv>=1.0.0

# Add additional dependencies here
# For example:
# requests>=2.31.0
# pandas>=2.0.0
```

### .gitignore

Version control configuration:

```gitignore
# Environment files
.env
.env.local

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
.venv/
venv/
ENV/

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Data files (adjust as needed)
data/*.db
data/*.sqlite
data/*.log

# Documentation builds
docs/_build/
```

### README.md

Project documentation (automatically generated):

```markdown
# {project_name}

A TFrameX project for building AI agents and workflows.

## Setup

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

3. **Run the application:**
   ```bash
   python main.py
   ```

[... more documentation ...]
```

## Customization Options

### Templates (Future Feature)

```bash
# Basic template (default)
tframex setup my-project

# Future templates
tframex setup my-project --template enterprise
tframex setup my-project --template research
tframex setup my-project --template chatbot
```

### Project Name Validation

Valid project names:
- Letters, numbers, hyphens, underscores
- No spaces (converted to hyphens)
- No special characters

```bash
# Valid
tframex setup my-ai-assistant
tframex setup research_bot_v2
tframex setup MyProject

# Invalid (but handled)
tframex setup "My Project"  # Becomes: My-Project
```

## Common Workflows

### Basic Project Setup

```bash
# 1. Create project
tframex setup customer-support-bot

# 2. Enter directory
cd customer-support-bot

# 3. Set up environment
cp .env.example .env
nano .env  # Add your API keys

# 4. Install dependencies
pip install -r requirements.txt

# 5. Run
python main.py
```

### Adding Custom Tools

Edit `config/tools.py`:

```python
def setup_tools(app):
    # ... existing tools ...
    
    # Add web search tool
    async def web_search(query: str) -> str:
        """Search the web for information."""
        # Implementation here
        return f"Search results for: {query}"
    
    search_tool = Tool(
        name="web_search",
        func=web_search,
        description="Search the web"
    )
    app.register_tool(search_tool)
```

### Adding Multiple Agents

Edit `config/agents.py`:

```python
def setup_agents(app):
    # ... existing setup ...
    
    # Research agent
    researcher = LLMAgent(
        name="Researcher",
        description="Specializes in research",
        llm=llm,
        tools=["web_search"],
        system_prompt="You are a research specialist..."
    )
    
    # Writer agent
    writer = LLMAgent(
        name="Writer",
        description="Creates content",
        llm=llm,
        system_prompt="You are a professional writer..."
    )
    
    # Register all agents
    app.register_agent(assistant)
    app.register_agent(researcher)
    app.register_agent(writer)
```

### Environment Management

```bash
# Development
cp .env.example .env.development

# Staging
cp .env.example .env.staging

# Production
cp .env.example .env.production

# Load specific environment
export $(cat .env.production | xargs)
python main.py
```

## Best Practices

### 1. Project Organization

```
my-project/
├── config/           # All configuration
├── agents/           # Complex agent definitions
├── tools/            # Tool implementations
├── flows/            # Workflow definitions
├── utils/            # Helper functions
├── tests/            # Unit tests
└── data/             # Data storage
```

### 2. Configuration Management

```python
# config/settings.py
import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    # LLM settings
    API_KEY = os.getenv("OPENAI_API_KEY")
    MODEL_NAME = os.getenv("OPENAI_MODEL_NAME", "gpt-3.5-turbo")
    
    # Project settings
    PROJECT_NAME = os.getenv("PROJECT_NAME")
    ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
    
    # Feature flags
    ENABLE_LOGGING = os.getenv("ENABLE_LOGGING", "true").lower() == "true"
    
settings = Settings()
```

### 3. Modular Agents

```python
# agents/research_agent.py
from tframex.agents.llm_agent import LLMAgent

def create_research_agent(llm):
    return LLMAgent(
        name="Researcher",
        description="Research specialist",
        llm=llm,
        tools=["web_search", "save_notes"],
        system_prompt="""..."""
    )

# config/agents.py
from agents.research_agent import create_research_agent

def setup_agents(app):
    llm = create_llm()
    app.register_agent(create_research_agent(llm))
```

### 4. Tool Libraries

```python
# tools/web_tools.py
from tframex.util.tools import Tool

def create_web_tools():
    tools = []
    
    # Web search
    async def search(query: str) -> str:
        # Implementation
        pass
    
    tools.append(Tool(
        name="web_search",
        func=search,
        description="Search the web"
    ))
    
    # URL fetch
    async def fetch_url(url: str) -> str:
        # Implementation
        pass
    
    tools.append(Tool(
        name="fetch_url",
        func=fetch_url,
        description="Fetch URL content"
    ))
    
    return tools

# config/tools.py
from tools.web_tools import create_web_tools

def setup_tools(app):
    for tool in create_web_tools():
        app.register_tool(tool)
```

## Troubleshooting

### Directory Already Exists

```bash
$ tframex setup my-project
Directory 'my-project' already exists. Overwrite? (y/N): n
❌ Setup cancelled.
```

**Solution:** Choose a different name or confirm overwrite.

### Permission Errors

```bash
❌ Error creating project: [Errno 13] Permission denied: 'my-project'
```

**Solution:** Check directory permissions or use a different location.

### Invalid Project Names

```bash
$ tframex setup "My Project!"
# Automatically sanitized to: My-Project
```

**Solution:** Use valid characters or let the tool sanitize.

## Migration and Upgrades

### From Basic to Full Project

```bash
# After using tframex basic
tframex setup advanced-version

# Copy learnings
# - Agent prompts that worked well
# - Tool ideas
# - Workflow patterns
```

### Version Upgrades

```bash
# Update TFrameX
pip install --upgrade tframex

# Check for new template features
tframex setup test-new-version
# Compare with existing project
```

### Project Templates

Save your configured project as a template:

```bash
# Create template
cp -r my-configured-project ~/.tframex-templates/my-template

# Future use (manual for now)
cp -r ~/.tframex-templates/my-template new-project
```

## Integration with IDEs

### VS Code

`.vscode/settings.json`:
```json
{
  "python.linting.enabled": true,
  "python.linting.pylintEnabled": true,
  "python.formatting.provider": "black",
  "files.exclude": {
    "**/__pycache__": true,
    "**/*.pyc": true
  }
}
```

### PyCharm

- Mark `config` as Sources Root
- Configure interpreter with virtual environment
- Set up run configuration for `main.py`

## Next Steps

After creating your project:

1. **Customize Agents** - Modify `config/agents.py`
2. **Add Tools** - Extend `config/tools.py`
3. **Create Flows** - Build workflows
4. **Add Tests** - Ensure reliability
5. **Deploy** - Use `tframex serve` or custom deployment

## Related Commands

- [`tframex basic`](basic) - Quick testing without project
- [`tframex serve`](serve) - Web interface for your project
- [CLI Overview](overview) - General CLI documentation