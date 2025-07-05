---
sidebar_position: 2
title: Installation
---

# Installation

This guide covers all the ways to install and set up TFrameX for your projects.

## Requirements

- Python 3.8 or higher
- pip (Python package manager)
- An LLM API key (OpenAI, Anthropic, or compatible service)

## Quick Install

The fastest way to get started with TFrameX:

```bash
# Install TFrameX
pip install tframex

# Verify installation
tframex --help
```

## Installation Methods

### 1. Basic Installation (Recommended)

For most users, the standard pip installation is sufficient:

```bash
pip install tframex
```

This installs TFrameX with all core dependencies including:
- `httpx` - HTTP client for API calls
- `pydantic` - Data validation and models
- `PyYAML` - YAML configuration support
- `openai` - OpenAI API client
- `aiohttp` - Async HTTP support
- `mcp` - Model Context Protocol support

### 2. Installation with Web Support

If you plan to use the `tframex serve` command for web interfaces:

```bash
pip install tframex[web]
```

This additionally installs:
- `Flask` - Web framework for the serve command

### 3. Installation with All Extras

To install TFrameX with all optional dependencies:

```bash
pip install tframex[web,examples]
```

### 4. Development Installation

If you're contributing to TFrameX or need the latest development version:

```bash
# Clone the repository
git clone https://github.com/TesslateAI/TFrameX.git
cd TFrameX

# Create a virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode
pip install -e .

# Install development dependencies
pip install -e ".[dev]"
```

### 5. Using UV (Fast Alternative)

[UV](https://github.com/astral-sh/uv) is a fast Python package installer:

```bash
# Install UV first
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create virtual environment and install TFrameX
uv venv
source .venv/bin/activate
uv pip install tframex
```

## Environment Configuration

After installation, configure your environment variables for LLM access.

### OpenAI Configuration

```bash
export OPENAI_API_KEY="sk-..."
export OPENAI_MODEL_NAME="gpt-3.5-turbo"  # Optional, defaults to gpt-3.5-turbo
```

### Anthropic Configuration

```bash
export ANTHROPIC_API_KEY="sk-ant-..."
export OPENAI_API_BASE="https://api.anthropic.com/v1"
export OPENAI_MODEL_NAME="claude-3-sonnet-20240229"
```

### Local LLM Configuration (Ollama)

```bash
export OPENAI_API_KEY="ollama"  # Dummy key for local
export OPENAI_API_BASE="http://localhost:11434/v1"
export OPENAI_MODEL_NAME="llama3"
```

### Other OpenAI-Compatible APIs

```bash
export OPENAI_API_KEY="your-api-key"
export OPENAI_API_BASE="https://your-api-endpoint.com/v1"
export OPENAI_MODEL_NAME="your-model-name"
```

## Verify Installation

### 1. Check CLI Installation

```bash
tframex --help
```

You should see:
```
usage: tframex [-h] {basic,setup,serve} ...

TFrameX CLI - Framework for building agentic systems
...
```

### 2. Test Basic Functionality

```bash
# Set your API key
export OPENAI_API_KEY="your-key"

# Start interactive session
tframex basic
```

### 3. Create a Test Project

```bash
tframex setup test-project
cd test-project
cp .env.example .env
# Edit .env with your API keys
python main.py
```

### 4. Python Import Test

```python
python -c "import tframex; print(f'TFrameX version: {tframex.__version__}')"
```

## Docker Installation

For containerized deployments:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install TFrameX
RUN pip install tframex[web]

# Copy your application
COPY . .

# Set environment variables
ENV OPENAI_API_KEY=""

# Run your app
CMD ["python", "main.py"]
```

Build and run:
```bash
docker build -t my-tframex-app .
docker run -e OPENAI_API_KEY="your-key" my-tframex-app
```

## Virtual Environment Best Practices

We strongly recommend using virtual environments:

### Using venv (Built-in)

```bash
# Create virtual environment
python -m venv tframex-env

# Activate it
source tframex-env/bin/activate  # Linux/Mac
tframex-env\Scripts\activate     # Windows

# Install TFrameX
pip install tframex

# Deactivate when done
deactivate
```

### Using conda

```bash
# Create conda environment
conda create -n tframex python=3.11

# Activate it
conda activate tframex

# Install TFrameX
pip install tframex
```

## Troubleshooting Installation

### Common Issues

#### 1. Command not found: tframex

The CLI script isn't in your PATH. Try:
```bash
# Find where it was installed
pip show -f tframex | grep tframex

# Add to PATH or use full path
python -m tframex.cli --help
```

#### 2. Import errors

Ensure all dependencies are installed:
```bash
pip install --upgrade tframex
pip install -r requirements.txt  # If using from source
```

#### 3. SSL Certificate errors

For corporate environments:
```bash
pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org tframex
```

#### 4. Permission errors

Use user installation:
```bash
pip install --user tframex
```

Or use a virtual environment (recommended).

## Next Steps

✅ Installation complete! Now you can:

1. 📖 Follow the [Quickstart Guide](quickstart)
2. 🚀 Create your first project with `tframex setup my-project`
3. 🧪 Try the interactive mode with `tframex basic`
4. 📚 Explore [Core Concepts](concepts/overview)

## Getting Help

If you encounter issues:

1. Check our [Troubleshooting Guide](reference/troubleshooting)
2. Search [GitHub Issues](https://github.com/TesslateAI/TFrameX/issues)
3. Join our [Discord Community](https://discord.gg/DkzMzwBTaw)
4. Contact support@tesslate.com