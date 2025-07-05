#!/usr/bin/env python3
"""
TFrameX CLI Tool

Provides command-line interface for TFrameX framework operations.
"""
import asyncio
import argparse
import sys
import os
import shutil
from pathlib import Path
from typing import Optional

from tframex import TFrameXApp
from tframex.agents.llm_agent import LLMAgent
from tframex.util.llms import OpenAIChatLLM
from tframex.util.tools import Tool, ToolParameters


def create_basic_app() -> TFrameXApp:
    """Create a basic TFrameX app with a simple assistant agent."""
    app = TFrameXApp()
    
    # Create a basic LLM configuration
    try:
        # Try to use environment variables first
        api_key = os.getenv("OPENAI_API_KEY") or os.getenv("LLAMA_API_KEY")
        if not api_key:
            print("⚠️  No API key found in environment variables.")
            print("   Set OPENAI_API_KEY or LLAMA_API_KEY to use your LLM.")
            print("   For now, using demo mode with placeholder responses.")
            api_key = "demo-key"
        
        base_url = os.getenv("OPENAI_API_BASE") or os.getenv("LLAMA_BASE_URL")
        model_name = os.getenv("OPENAI_MODEL_NAME") or os.getenv("LLAMA_MODEL") or "gpt-3.5-turbo"
        
        if api_key == "demo-key":
            # Demo mode with mock responses
            llm = None
        else:
            llm = OpenAIChatLLM(
                model_name=model_name,
                api_key=api_key,
                api_base_url=base_url,
                parse_text_tool_calls=True
            )
    except Exception as e:
        print(f"⚠️  Error setting up LLM: {e}")
        print("   Running in demo mode.")
        llm = None
    
    # Create a basic assistant agent
    assistant = LLMAgent(
        name="BasicAssistant",
        description="A helpful AI assistant with basic tools",
        llm=llm,
        system_prompt="""You are a helpful AI assistant created with TFrameX.
        
You have access to basic tools and can help with:
- General questions and conversations
- Time-related queries
- Basic problem solving

If you don't have access to external tools or APIs, you can still provide helpful responses based on your training."""
    )
    
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
    
    # Register the agent
    app.register_agent(assistant)
    
    return app


async def run_basic_session():
    """Run a basic interactive TFrameX session."""
    print("🚀 Starting TFrameX Basic Interactive Session")
    print("=" * 50)
    print()
    print("Welcome to TFrameX! This is a basic interactive session.")
    print("Type 'exit' or 'quit' to end the session.")
    print()
    
    app = create_basic_app()
    
    try:
        async with app.run_context() as rt:
            await rt.interactive_chat(default_agent_name="BasicAssistant")
    except KeyboardInterrupt:
        print("\n👋 Session ended by user.")
    except Exception as e:
        print(f"❌ Error during session: {e}")
        return 1
    
    print("\n👋 Thanks for using TFrameX!")
    return 0


def create_project_structure(project_path: Path, project_name: str, template: str = "basic"):
    """Create a new TFrameX project with the specified template."""
    
    # Create main directory
    project_path.mkdir(parents=True, exist_ok=True)
    
    # Create subdirectories
    (project_path / "config").mkdir(exist_ok=True)
    (project_path / "data").mkdir(exist_ok=True)
    (project_path / "docs").mkdir(exist_ok=True)
    
    # Create main.py
    main_py_content = f'''#!/usr/bin/env python3
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
    print(f"🚀 Starting {{project_name}}")
    print("=" * 50)
    
    app = create_app()
    
    # Run interactive session
    async with app.run_context() as rt:
        await rt.interactive_chat()


if __name__ == "__main__":
    asyncio.run(main())
'''
    
    # Create config/agents.py
    agents_py_content = '''"""
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
'''
    
    # Create config/tools.py
    tools_py_content = '''"""
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
'''
    
    # Create requirements.txt
    requirements_content = '''# TFrameX project requirements
tframex>=0.1.3
python-dotenv>=1.0.0

# Add additional dependencies here
# For example:
# requests>=2.31.0
# pandas>=2.0.0
'''
    
    # Create .env.example
    env_example_content = '''# Environment configuration for your TFrameX project
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
'''
    
    # Create README.md
    readme_content = f'''# {project_name}

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
{project_name}/
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

Generated with TFrameX CLI: `tframex setup {project_name}`
'''
    
    # Write files
    (project_path / "main.py").write_text(main_py_content)
    (project_path / "config" / "__init__.py").write_text("")
    (project_path / "config" / "agents.py").write_text(agents_py_content)
    (project_path / "config" / "tools.py").write_text(tools_py_content)
    (project_path / "requirements.txt").write_text(requirements_content)
    (project_path / ".env.example").write_text(env_example_content)
    (project_path / "README.md").write_text(readme_content)
    
    # Create .gitignore
    gitignore_content = '''# Environment files
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
'''
    (project_path / ".gitignore").write_text(gitignore_content)


def setup_project(project_name: str, template: str = "basic"):
    """Setup a new TFrameX project."""
    project_path = Path.cwd() / project_name
    
    if project_path.exists():
        response = input(f"Directory '{project_name}' already exists. Overwrite? (y/N): ")
        if response.lower() != 'y':
            print("❌ Setup cancelled.")
            return 1
        shutil.rmtree(project_path)
    
    print(f"🚀 Creating TFrameX project: {project_name}")
    print(f"📁 Location: {project_path}")
    print()
    
    try:
        create_project_structure(project_path, project_name, template)
        
        print("✅ Project created successfully!")
        print()
        print("📋 Next steps:")
        print(f"   1. cd {project_name}")
        print("   2. pip install -r requirements.txt")
        print("   3. cp .env.example .env")
        print("   4. Edit .env with your API keys")
        print("   5. python main.py")
        print()
        print("🎯 Your project is ready to go!")
        
        return 0
        
    except Exception as e:
        print(f"❌ Error creating project: {e}")
        return 1


async def serve_webapp(host: str = "localhost", port: int = 8000):
    """Start a web server for TFrameX."""
    try:
        from flask import Flask, render_template_string, request, jsonify
    except ImportError:
        print("❌ Flask is required for web server functionality.")
        print("   Install with: pip install flask")
        return 1
    
    print(f"🌐 Starting TFrameX Web Server on http://{host}:{port}")
    print("=" * 50)
    
    app_flask = Flask(__name__)
    tframex_app = create_basic_app()
    
    # HTML template for the web interface
    template = '''
<!DOCTYPE html>
<html>
<head>
    <title>TFrameX Web Interface</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
        .container { max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .header { text-align: center; margin-bottom: 30px; }
        .chat-box { border: 1px solid #ddd; height: 400px; overflow-y: auto; padding: 15px; margin-bottom: 15px; background: #fafafa; border-radius: 5px; }
        .input-area { display: flex; gap: 10px; }
        .input-area input { flex: 1; padding: 10px; border: 1px solid #ddd; border-radius: 5px; }
        .input-area button { padding: 10px 20px; background: #007bff; color: white; border: none; border-radius: 5px; cursor: pointer; }
        .input-area button:hover { background: #0056b3; }
        .message { margin: 10px 0; padding: 10px; border-radius: 5px; }
        .user-message { background: #e3f2fd; text-align: right; }
        .bot-message { background: #f1f8e9; }
        .status { margin: 10px 0; font-style: italic; color: #666; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 TFrameX Web Interface</h1>
            <p>Interactive AI Assistant powered by TFrameX</p>
        </div>
        
        <div id="chat-box" class="chat-box">
            <div class="message bot-message">
                <strong>Assistant:</strong> Hello! I'm your TFrameX AI assistant. How can I help you today?
            </div>
        </div>
        
        <div class="input-area">
            <input type="text" id="user-input" placeholder="Type your message here..." onkeypress="handleKeyPress(event)">
            <button onclick="sendMessage()">Send</button>
        </div>
        
        <div class="status" id="status"></div>
    </div>

    <script>
        function handleKeyPress(event) {
            if (event.key === 'Enter') {
                sendMessage();
            }
        }
        
        function sendMessage() {
            const input = document.getElementById('user-input');
            const message = input.value.trim();
            if (!message) return;
            
            // Add user message to chat
            addMessage('user', message);
            input.value = '';
            
            // Show thinking status
            document.getElementById('status').textContent = 'Assistant is thinking...';
            
            // Send to backend
            fetch('/chat', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({message: message})
            })
            .then(response => response.json())
            .then(data => {
                document.getElementById('status').textContent = '';
                addMessage('bot', data.response);
            })
            .catch(error => {
                document.getElementById('status').textContent = '';
                addMessage('bot', 'Sorry, I encountered an error. Please try again.');
                console.error('Error:', error);
            });
        }
        
        function addMessage(sender, text) {
            const chatBox = document.getElementById('chat-box');
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${sender}-message`;
            messageDiv.innerHTML = `<strong>${sender === 'user' ? 'You' : 'Assistant'}:</strong> ${text}`;
            chatBox.appendChild(messageDiv);
            chatBox.scrollTop = chatBox.scrollHeight;
        }
    </script>
</body>
</html>
    '''
    
    @app_flask.route('/')
    def index():
        return render_template_string(template)
    
    @app_flask.route('/chat', methods=['POST'])
    async def chat():
        try:
            data = request.get_json()
            message = data.get('message', '')
            
            # Use TFrameX to process the message
            async with tframex_app.run_context() as rt:
                response = await rt.call_agent("BasicAssistant", message)
                return jsonify({"response": response})
                
        except Exception as e:
            return jsonify({"response": f"Error: {str(e)}"})
    
    try:
        app_flask.run(host=host, port=port, debug=False)
        return 0
    except Exception as e:
        print(f"❌ Error starting web server: {e}")
        return 1


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="TFrameX CLI - Framework for building agentic systems",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  tframex basic              Start an interactive session
  tframex setup myproject    Create a new TFrameX project
  tframex serve             Start a web server interface
  tframex serve --port 3000  Start web server on port 3000
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Basic command
    basic_parser = subparsers.add_parser('basic', help='Start an interactive TFrameX session')
    
    # Setup command
    setup_parser = subparsers.add_parser('setup', help='Create a new TFrameX project')
    setup_parser.add_argument('project_name', help='Name of the project to create')
    setup_parser.add_argument('--template', default='basic', choices=['basic'], 
                             help='Project template to use')
    
    # Serve command
    serve_parser = subparsers.add_parser('serve', help='Start a web server interface')
    serve_parser.add_argument('--host', default='localhost', help='Host to bind to')
    serve_parser.add_argument('--port', type=int, default=8000, help='Port to bind to')
    
    # Parse arguments
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    # Execute commands
    try:
        if args.command == 'basic':
            return asyncio.run(run_basic_session())
        
        elif args.command == 'setup':
            return setup_project(args.project_name, args.template)
        
        elif args.command == 'serve':
            return asyncio.run(serve_webapp(args.host, args.port))
    
    except KeyboardInterrupt:
        print("\n👋 Operation cancelled by user.")
        return 1
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())