# TFrameX Agents Framework

[![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT) <!-- Adjust license if needed -->

## Overview

This project provides a flexible Python framework for interacting with VLLM (or other OpenAI-compatible) Large Language Model (LLM) endpoints. It features:

*   **Modular Design:** Separates concerns into Models, Agents (Primitives), and Systems within a standard Python package structure.
*   **Simplified Imports:** Core classes are easily accessible directly from their respective modules (e.g., `from tframex.model import VLLMModel`).
*   **Streaming Support:** Handles LLM responses as streams to avoid timeouts with long generations and provide real-time output.
*   **Concurrency:** Supports making multiple simultaneous API calls efficiently using `asyncio`.
*   **Extensibility:** Designed to be easily extended with new models, agents, or complex interaction systems.
*   **Chat & Completions:** Supports the OpenAI Chat Completions API format (`/v1/chat/completions`), ensuring compatibility with features like system prompts and reasoning tags (e.g., `<think>`).
*   **Error Handling & Retries:** Includes basic retry mechanisms for common transient network errors.

## Features

*   Define specific LLM endpoint configurations (e.g., `VLLMModel`).
*   Create primitive agents with specific tasks (e.g., `BasicAgent`, `ContextAgent`).
*   Build complex systems orchestrating multiple agents or calls (e.g., `ChainOfAgents` for summarization, `MultiCallSystem` for parallel generation).
*   Stream responses directly to files or aggregate them.
*   Handle API errors and network issues gracefully.
*   Configure model parameters (temperature, max tokens) per call.

## Project Structure

```
.
├── src/
│   └── tframex/                   # Core library package
│       ├── __init__.py           # Makes 'tframex' importable
│       ├── agents/
│       │   ├── __init__.py       # Exposes agent classes (e.g., BasicAgent)
│       │   ├── agent_logic.py    # BaseAgent and shared logic
│       │   └── agents.py         # Concrete agent implementations
│       ├── model/
│       │   ├── __init__.py       # Exposes model classes (e.g., VLLMModel)
│       │   └── model_logic.py    # BaseModel, VLLMModel implementation
│       └── systems/
│           ├── __init__.py       # Exposes system classes (e.g., ChainOfAgents, MultiCallSystem)
│           ├── chain_of_agents.py    # Sequential summarization system
│           └── multi_call_system.py  # Parallel sampling/generation system
│
├── examples/                  # Example usage scripts (separate from the library)
│   ├── website_builder/
│   │   └── html.py
│   ├── context.txt           # Sample input file
│   ├── example.py            # Main example script
│   └── longtext.txt          # Sample input file
│
├── .env copy                 # Example environment file template
├── .gitignore
├── README.md                 # This file
├── requirements.txt          # Core library dependencies
└── pyproject.toml            # Build system and package configuration
```

*   **`tframex/`**: The main directory containing the library source code.
*   **`tframex/model/`**: Contains `BaseModel` and implementations like `VLLMModel`. Handles API communication, streaming, and response parsing (configured for `/v1/chat/completions`).
*   **`tframex/agents/`**: Contains `BaseAgent` and implementations like `BasicAgent`, `ContextAgent`. Represents individual processing units.
*   **`tframex/systems/`**: Contains orchestrators like `ChainOfAgents` and `MultiCallSystem` for complex workflows.
*   **`__init__.py` files**: These files make the directories Python packages and are used to expose the main classes for easier imports (e.g., allowing `from tframex.model import VLLMModel` instead of `from tframex.model.model_logic import VLLMModel`).
*   **`examples/`**: Contains scripts demonstrating library usage. These scripts import the `tframex` package.
*   **`pyproject.toml`**: Defines how to build and install the `tframex` package using standard Python tools like `pip`.
*   **`requirements.txt`**: Lists core dependencies needed by the `tframex` library itself. Dependencies needed *only* for examples (like `python-dotenv`) should ideally be installed separately by the user running the examples.

## Setup & Installation

### 1. Prerequisites

*   Python 3.8 or higher.
*   Access to a VLLM or other OpenAI-compatible LLM endpoint URL and API key.
*   `pip` and `setuptools` (usually included with Python).

### 2. Clone or Download

Get the project files onto your local machine.

```bash
git clone <your-repository-url> # Or download and extract the ZIP
cd TFrameX # Navigate into the project root directory (containing pyproject.toml)
```

### 3. Install Dependencies & Library

Create a virtual environment (recommended) and install the library. Installing in editable mode (`-e`) is useful during development, as changes to the library code are immediately reflected without reinstalling.

```bash
# Create and activate a virtual environment (optional but recommended)
python -m venv venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate`

# Install the tframex library and its core dependencies
pip install -e .  # Installs in editable mode from the current directory

# OR, for a standard installation:
# pip install .

# If running examples that use .env files, you might also need:
# pip install python-dotenv
```

### 4. Configuration (for Examples)

The example scripts (`examples/example.py`, `examples/website_builder/html.py`) typically read configuration from environment variables (using `python-dotenv` and a `.env` file) or have placeholders.

**Crucial:** To run the examples, ensure your API credentials and endpoint details are accessible. You can:
    *   Create a `.env` file in the `TAF/` root directory by copying `.env copy` and filling in your details.
    *   Set environment variables directly in your shell.
    *   Modify the example scripts to hardcode values (not recommended for API keys).

Example `.env` file content:
```dotenv
API_URL="https://your-vllm-or-openai-compatible-url/v1"
API_KEY="your_actual_api_key"
MODEL_NAME="Qwen/Qwen3-30B-A3B-FP8" # Or your target model
MAX_TOKENS=32000
TEMPERATURE=0.7
```

**Security Warning:** **DO NOT** commit your actual API keys to version control. Use environment variables or secure configuration management for production or shared environments.

### 5. Create Input Files (Optional)

The `examples/example.py` script uses `examples/context.txt` and `examples/longtext.txt`. If they don't exist, basic placeholders might be used or created by the script. You can create your own with relevant content:

*   **`examples/context.txt`**: Text for the `ContextAgent`.
*   **`examples/longtext.txt`**: Longer text for the `ChainOfAgents`.

## Core Concepts

*   **Models (`tframex.model`)**: Represent the connection to an LLM API endpoint. Handle request formatting, API calls, streaming, and response parsing (using Chat Completions format). Access like: `from tframex.model import VLLMModel`.
*   **Agents (`tframex.agents`)**: Represent individual actors using a Model. Inherit from `BaseAgent`. Access like: `from tframex.agents import BasicAgent`.
*   **Systems (`tframex.systems`)**: Higher-level orchestrators managing complex workflows, potentially using multiple Agents or direct Model calls. Access like: `from tframex.systems import ChainOfAgents`.
*   **Streaming**: LLM responses are processed chunk-by-chunk via `AsyncGenerator`s to handle long responses and provide real-time data.
*   **Concurrency (`asyncio`)**: Used for efficient handling of multiple network operations (like in `MultiCallSystem`).
*   **Chat Completions API (`/v1/chat/completions`)**: The framework standardizes on this input/output format for compatibility with modern LLMs and features like reasoning tags.

## Usage

1.  Ensure you have completed the **Setup & Installation** steps, including installing the library (`pip install -e .` or `pip install .`) and configuring API access for the examples.
2.  Navigate to the project root directory (`TAF/`) in your terminal (and activate your virtual environment).
3.  Run an example script:

    ```bash
    # Run the main example suite
    python examples/example.py

    # Run the website builder example
    python examples/website_builder/html.py
    ```

4.  **Output:**
    *   Status messages and response previews will appear in the console.
    *   Detailed outputs are typically saved to files (e.g., within `examples/example_outputs/` or `examples/website_builder/generated_website/`, depending on the script).

## Code Documentation (Key Components & Imports)

*   **`tframex.model.VLLMModel(model_name, api_url, api_key, ...)`**
    *   Initializes connection to a VLLM/OpenAI-compatible chat endpoint.
    *   `call_stream(messages: List[Dict[str, str]], **kwargs) -> AsyncGenerator[str, None]`: Makes the streaming API call, yields content chunks.
    *   `close_client()`: Closes the HTTP client.
*   **`tframex.agents.BaseAgent(agent_id, model)`**
    *   Abstract base class for all agents.
    *   Provides `_stream_and_aggregate` helper.
*   **`tframex.agents.BasicAgent(agent_id, model)`**
    *   `run(prompt: str, **kwargs) -> str`: Simple agent; takes prompt, returns aggregated model response.
*   **`tframex.agents.ContextAgent(agent_id, model, context)`**
    *   `run(prompt: str, **kwargs) -> str`: Prepends context to the prompt before calling the model.
*   **`tframex.systems.ChainOfAgents(system_id, model, ...)`**
    *   `run(initial_prompt: str, long_text: str, **kwargs) -> str`: Processes long text via chunking and sequential summarization using an internal agent.
*   **`tframex.systems.MultiCallSystem(system_id, model)`**
    *   `run(prompt: str, num_calls: int, ..., **kwargs) -> Dict[str, str]`: Makes multiple concurrent model calls with the same prompt, saving results.

**Example Import Style:**

```python
from tframex.model import VLLMModel
from tframex.agents import BasicAgent, ContextAgent
from tframex.systems import ChainOfAgents, MultiCallSystem

# Initialize the model
model = VLLMModel(model_name="...", api_url="...", api_key="...")

# Initialize agents/systems
agent = BasicAgent(agent_id="my_agent", model=model)
# ... rest of your code
```

## Troubleshooting

*   **`httpx.RemoteProtocolError: peer closed connection without sending complete message body (incomplete chunked read)` or similar Timeouts:**
    *   **Cause:** Often proxy timeouts (e.g., Cloudflare Tunnel ~100s), VLLM server overload/timeouts.
    *   **VLLM Logs:** Check VLLM logs for errors (OOM), high load, `Waiting` requests, `Aborted request`.
    *   **Solution 1: Reduce Concurrency:** Lower `num_calls` in `MultiCallSystem` examples.
    *   **Solution 2: Check Proxy/Tunnel:** Verify/increase timeouts if possible.
    *   **Solution 3: Optimize/Scale VLLM:** Ensure adequate server resources.
*   **Missing `<think>` Tags or Initial Content:**
    *   **Cause:** Using wrong API endpoint format or incorrect response parsing. The library uses `/v1/chat/completions` and parses `delta.content`.
    *   **Solution:** Ensure your model endpoint is compatible and outputs reasoning tags within the standard chat completion structure.
*   **Repetitive Output:**
    *   **Cause:** LLM looping, often due to `max_tokens`, unstable decoding, or specific sampling parameters.
    *   **Solution:** Check `max_tokens`, adjust `temperature`/`repetition_penalty`, reduce concurrency/load.
*   **Configuration Errors (401 Unauthorized, 404 Not Found):**
    *   **Cause:** Incorrect `API_KEY`, `API_URL`, or `MODEL_NAME`.
    *   **Solution:** Double-check configuration values against your endpoint details.
*   **Import Errors (`ModuleNotFoundError: No module named 'tframex'`):**
    *   **Cause:** The library hasn't been installed in the current Python environment.
    *   **Solution:** Ensure you have run `pip install .` or `pip install -e .` in the project root directory (`TAF/`) within your activated virtual environment.
*   **Other `httpx` Errors (`ConnectError`, `ReadError`):**
    *   **Cause:** Network issues, server down.
    *   **Solution:** Basic retry logic helps. Check network, firewall, server status.

## Customization & Extension

*   **Add New Models:** Create a new class in `tframex/model/` inheriting from `BaseModel`, implement `call_stream`, and expose it in `tframex/model/__init__.py`.
*   **Add New Agents:** Create new classes in `tframex/agents/` inheriting from `BaseAgent` and expose them in `tframex/agents/__init__.py`.
*   **Add New Systems:** Create new classes in `tframex/systems/` and expose them in `tframex/systems/__init__.py`.
*   **Configuration Management:** Use a more robust system like environment variables or dedicated config files instead of hardcoding in examples.
*   **Input/Output:** Adapt agents/systems to interact with databases, web APIs, etc.
*   **Enhanced Retries:** Use libraries like `tenacity` for more sophisticated retry strategies.

## License

This project is licensed under the MIT License.