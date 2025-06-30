# TFrameX Examples

Welcome to the TFrameX examples collection! This directory contains comprehensive examples demonstrating various aspects of the TFrameX framework, from basic agent creation to complex multi-agent workflows.

## 📚 Example Categories

### **🚀 01. Basic Examples**
Perfect for getting started with TFrameX fundamentals.

| Example | Description | Difficulty | Key Concepts |
|---------|-------------|------------|--------------|
| [Hello World](./01-basic-examples/hello-world/) | Your first TFrameX agent | Beginner | Agent creation, basic execution |
| [Simple Agent](./01-basic-examples/simple-agent/) | Agent with tools and memory | Beginner | Tools, memory, system prompts |
| [Tool Integration](./01-basic-examples/tool-integration/) | Working with external APIs | Intermediate | Tool creation, async operations |

### **🔄 02. Pattern Examples**
Learn TFrameX's powerful orchestration patterns.

| Example | Description | Difficulty | Key Concepts |
|---------|-------------|------------|--------------|
| [Sequential Pattern](./02-pattern-examples/sequential-pattern/) | Step-by-step agent execution | Beginner | Sequential flows, data passing |
| [Parallel Pattern](./02-pattern-examples/parallel-pattern/) | Concurrent agent execution | Intermediate | Parallel processing, result aggregation |
| [Router Pattern](./02-pattern-examples/router-pattern/) | Dynamic agent routing | Intermediate | Conditional logic, intelligent routing |
| [Discussion Pattern](./02-pattern-examples/discussion-pattern/) | Multi-agent collaboration | Advanced | Agent debates, consensus building |

### **🔌 03. Integration Examples**
Explore TFrameX's integration capabilities.

| Example | Description | Difficulty | Key Concepts |
|---------|-------------|------------|--------------|
| [MCP Integration](./03-integration-examples/mcp-integration/) | Model Context Protocol servers | Intermediate | MCP servers, external tools |
| [Blender Integration](./03-integration-examples/blender-integration/) | 3D modeling with AI | Advanced | Creative workflows, complex tools |
| [Web Chatbot](./03-integration-examples/web-chatbot/) | Flask-based web interface | Intermediate | Web frameworks, real-time chat |

### **🏗️ 04. Advanced Examples**
Production-ready applications demonstrating complex workflows.

| Example | Description | Difficulty | Key Concepts |
|---------|-------------|------------|--------------|
| [Code Review System](./04-advanced-examples/code-review-system/) | AI-powered code analysis | Advanced | Multi-agent analysis, security scanning |
| [Content Creation Pipeline](./04-advanced-examples/content-creation-pipeline/) | Multi-modal content generation | Advanced | Creative workflows, asset coordination |
| [Smart Home Orchestration](./04-advanced-examples/smart-home-orchestration/) | IoT device coordination | Advanced | Real-time monitoring, automation |
| [Financial Trading Platform](./04-advanced-examples/financial-trading-platform/) | Market analysis and research | Expert | Data analysis, risk assessment |

### **🌟 05. Real-World Examples**
Enterprise-grade applications for specific industries.

| Example | Description | Difficulty | Key Concepts |
|---------|-------------|------------|--------------|
| [Medical Diagnosis Support](./05-real-world-examples/medical-diagnosis-support/) | Healthcare AI assistant | Expert | Multi-modal analysis, safety protocols |
| [DevOps Incident Response](./05-real-world-examples/devops-incident-response/) | Automated incident management | Expert | Monitoring, alerting, coordination |
| [Legal Document Analysis](./05-real-world-examples/legal-document-analysis/) | Contract and compliance review | Expert | Document processing, risk analysis |
| [Game AI Director](./05-real-world-examples/game-ai-director/) | Dynamic game content generation | Expert | Real-time adaptation, player analytics |

## 🏃 Quick Start

### Prerequisites
- Python 3.8+
- TFrameX installed (`pip install tframex`)
- LLM API access (OpenAI, local model, etc.)

### Running an Example
1. Navigate to any example directory
2. Install dependencies: `pip install -r requirements.txt`
3. Copy environment template: `cp .env.example .env`
4. Configure your LLM settings in `.env`
5. Run the example: `python main.py`

## 📖 Learning Path

### **For Beginners:**
1. Start with [Hello World](./01-basic-examples/hello-world/)
2. Progress through [Basic Examples](./01-basic-examples/)
3. Try [Sequential Pattern](./02-pattern-examples/sequential-pattern/)

### **For Intermediate Users:**
1. Explore all [Pattern Examples](./02-pattern-examples/)
2. Try [MCP Integration](./03-integration-examples/mcp-integration/)
3. Build your own variation

### **For Advanced Users:**
1. Study [Advanced Examples](./04-advanced-examples/)
2. Implement [Real-World Examples](./05-real-world-examples/)
3. Contribute your own examples!

## 🛠️ Example Structure

Each example follows a standardized structure:

```
example-name/
├── README.md                   # Comprehensive guide
├── requirements.txt            # Python dependencies
├── .env.example               # Environment template
├── main.py                    # Primary application
├── config/
│   ├── agents.py             # Agent definitions
│   ├── tools.py              # Tool definitions
│   └── flows.py              # Flow definitions
├── data/                     # Sample data files
├── docs/
│   ├── setup.md              # Setup instructions
│   ├── usage.md              # Usage examples
│   └── troubleshooting.md    # Common issues
└── assets/                   # Screenshots, diagrams
```

## 🔧 Configuration

### Environment Variables
All examples use these standard environment variables:

```env
# LLM Configuration
OPENAI_API_KEY=your_api_key_here
OPENAI_API_BASE=https://api.openai.com/v1
OPENAI_MODEL_NAME=gpt-3.5-turbo

# Example-specific variables
# (See individual .env.example files)
```

### Local Development
For local development with Ollama:

```env
OPENAI_API_BASE=http://localhost:11434/v1
OPENAI_API_KEY=ollama
OPENAI_MODEL_NAME=llama3
```

## 📊 Difficulty Levels

- **🟢 Beginner**: Basic TFrameX concepts, single agents
- **🟡 Intermediate**: Multiple agents, basic patterns, external tools
- **🟠 Advanced**: Complex workflows, real-time processing, integrations
- **🔴 Expert**: Production systems, safety-critical applications, optimization

## 🤝 Contributing

Found a bug? Want to add an example? Contributions are welcome!

1. Fork the repository
2. Create your example following the standard structure
3. Add comprehensive documentation
4. Test thoroughly
5. Submit a pull request

### Example Contribution Guidelines
- Follow the standardized folder structure
- Include comprehensive README with setup instructions
- Add requirements.txt with exact versions
- Include .env.example with all required variables
- Test on multiple platforms when possible
- Add appropriate difficulty level

## 📞 Support

- **Documentation**: [TFrameX Docs](https://tframex.tesslate.com/)
- **Discord**: [Join our Discord](https://discord.gg/DkzMzwBTaw)
- **Issues**: [GitHub Issues](https://github.com/TesslateAI/TFrameX/issues)

## 📄 License

All examples are provided under the MIT License. See the main repository LICENSE file for details.

---

**Happy building with TFrameX! 🚀**