---
sidebar_position: 1
title: Introduction
---

# Welcome to TFrameX v1.1.0

**TFrameX** is a production-ready Python framework for building sophisticated multi-agent LLM applications. Move beyond simple prompt-response interactions and construct complex, dynamic workflows where intelligent agents collaborate, use tools, and adapt to intricate tasks.

## 🎉 What's New in v1.1.0

- **Enhanced MCP Integration**: Improved stability and performance for Model Context Protocol servers
- **Comprehensive CLI Tooling**: New `tframex` command for instant project setup and deployment
- **Enterprise Features**: Complete suite for production deployments including authentication, RBAC, metrics, and audit logging
- **Improved Documentation**: You're reading it! Complete Docusaurus-based documentation site

## Why TFrameX?

### 🧠 Intelligent Agents, Simplified
Define specialized agents with unique system prompts, tools, and even dedicated LLM models. Create hierarchical agent structures where supervisors delegate to specialists.

### 🛠️ Seamless Tool Integration
Equip your agents with custom tools using a simple decorator. Let them interact with APIs, databases, or any Python function.

### 🌊 Powerful Flow Orchestration
Design complex workflows by chaining agents and predefined patterns using an intuitive Flow API. Supports sequential, parallel, routing, and discussion patterns.

### 🧩 Composable & Modular
Build reusable components (agents, tools, flows) that can be combined to create increasingly complex applications.

### 🚀 Agent-as-Tool Paradigm
Enable agents to call other agents as tools, creating hierarchical and supervised agent structures.

### ⚡ CLI for Rapid Development
Get started instantly with `tframex basic`, scaffold projects with `tframex setup`, and deploy web interfaces with `tframex serve`.

## Architecture Overview

TFrameX is built on a clean, extensible architecture:

![TFrameX Architecture Overview](/img/01-overall-framework-architecture.png)

The framework consists of several key components:

- **TFrameXApp**: Central registry and configuration hub
- **Agents**: Intelligent actors that can reason, use tools, and collaborate
- **Tools**: Functions that agents can invoke to interact with external systems
- **Flows**: Orchestration layer for complex multi-agent workflows
- **MCP Integration**: Connect to external services via Model Context Protocol
- **Enterprise Layer**: Production-ready features for scalability and compliance

## Quick Example

Here's a simple example to get you started:

```python
from tframex import TFrameXApp
from tframex.agents.llm_agent import LLMAgent
from tframex.util.llms import OpenAIChatLLM
import asyncio

# Create the app
app = TFrameXApp()

# Define a tool
@app.tool(description="Calculate the sum of two numbers")
async def add(a: int, b: int) -> int:
    return a + b

# Create an agent
calculator = LLMAgent(
    name="CalculatorAgent",
    description="A helpful math assistant",
    llm=OpenAIChatLLM(),
    system_prompt="You are a helpful math assistant. Use the add tool when needed."
)

# Register agent with tools
app.register_agent(calculator, tools=["add"])

# Run the agent
async def main():
    async with app.run_context() as rt:
        result = await rt.call_agent("CalculatorAgent", "What is 25 + 17?")
        print(result)

asyncio.run(main())
```

## Use Cases

TFrameX is perfect for:

- **Customer Service Automation**: Multi-tier support systems with escalation workflows
- **Content Creation Pipelines**: Research, writing, editing, and publishing workflows
- **Data Analysis Systems**: Collaborative analysis with specialized analyst agents
- **DevOps Automation**: Infrastructure management with approval workflows
- **Financial Analysis**: Trading systems with risk management and compliance
- **Healthcare Applications**: Diagnostic support with specialist consultation patterns

## Getting Help

- 📚 Continue to [Installation](installation) to get started
- 💬 Join our [Discord Community](https://discord.gg/DkzMzwBTaw)
- 🐛 Report issues on [GitHub](https://github.com/TesslateAI/TFrameX/issues)
- 📧 Contact us at support@tesslate.com

## License

TFrameX is open source software licensed under the [MIT License](https://github.com/TesslateAI/TFrameX/blob/main/LICENSE).