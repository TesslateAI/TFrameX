# Multi-Agent VLLM Interaction Framework

[![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT) <!-- Adjust license if needed -->

## Overview

This project provides a flexible Python framework for interacting with VLLM (or other OpenAI-compatible) Large Language Model (LLM) endpoints. It features:

*   **Modular Design:** Separates concerns into Models, Agents (Primitives), and Systems.
*   **Streaming Support:** Handles LLM responses as streams to avoid timeouts with long generations and provide real-time output.
*   **Concurrency:** Supports making multiple simultaneous API calls efficiently using `asyncio`.
*   **Extensibility:** Designed to be easily extended with new models, agents, or complex interaction systems.
*   **Chat & Completions:** Supports the OpenAI Chat Completions API format (`/v1/chat/completions`), ensuring compatibility with features like system prompts and reasoning tags (e.g., `<think>`).
*   **Error Handling & Retries:** Includes basic retry mechanisms for common transient network errors.

## Features

*   Define specific LLM endpoint configurations (e.g., VLLMModel).
*   Create primitive agents with specific tasks (e.g., `BasicAgent`, `ContextAgent`).
*   Build complex systems orchestrating multiple agents or calls (e.g., `ChainOfAgents` for summarization, `MultiCallSystem` for parallel generation).
*   Stream responses directly to files or aggregate them.
*   Handle API errors and network issues gracefully.
*   Configure model parameters (temperature, max tokens) per call.

## Project Structure

```
.
├── model_logic.py        # Defines LLM model interaction classes (e.g., VLLMModel)
├── agent_logic.py        # Defines the BaseAgent class and shared agent utilities
├── agents.py             # Defines primitive Agent classes (e.g., BasicAgent, ContextAgent)
├── systems.py            # Defines complex Systems orchestrating agents/calls (e.g., ChainOfAgents, MultiCallSystem)
├── example.py            # Main script demonstrating usage of models, agents, and systems
├── requirements.txt      # Project dependencies
├── context.txt           # Sample input file for ContextAgent example
├── longtext.txt          # Sample input file for ChainOfAgents example
├── run_outputs/          # Default directory for example script outputs
│   ├── ex1_basic_agent_output.txt
│   ├── ex2_context_agent_output.txt
│   ├── ex3_chain_system_output.txt
│   └── ex4_multi_call_outputs/
│       ├── website_1.txt
│       └── ...
└── README.md             # This file
```

*   **`model_logic.py`**: Contains the `BaseModel` abstract class and concrete implementations like `VLLMModel`. Handles the direct API communication, streaming logic, and response parsing for a specific type of LLM endpoint. Configured for the `/v1/chat/completions` endpoint.
*   **`agent_logic.py`**: Contains the `BaseAgent` abstract class, defining the common interface for all agents (e.g., `run` method). Includes the `_stream_and_aggregate` helper to convert prompts to the chat message format and collect streamed responses.
*   **`agents.py`**: Implements simple, reusable "primitive" agents inheriting from `BaseAgent`.
    *   `BasicAgent`: Takes a prompt, calls the model, returns the full response.
    *   `ContextAgent`: Prepends a predefined context to the user's prompt before calling the model.
*   **`systems.py`**: Implements more complex workflows that might involve multiple steps, multiple agents, or specific orchestration logic.
    *   `ChainOfAgents`: Processes long text by chunking it and passing summaries sequentially between steps (using an internal `BasicAgent`).
    *   `MultiCallSystem`: Executes a specified number of *simultaneous* calls to the model with the same prompt, saving each response to a separate file.
*   **`example.py`**: Demonstrates how to instantiate models, agents, and systems, run them with sample data, and save the outputs. **This is the main entry point to run the examples.**
*   **`requirements.txt`**: Lists necessary Python packages.
*   **`.txt` Files**: Example input data files.
*   **`run_outputs/`**: Directory where `example.py` saves its output files by default.

## Setup & Installation

### 1. Prerequisites

*   Python 3.8 or higher.
*   Access to a VLLM or other OpenAI-compatible LLM endpoint URL and API key.

### 2. Clone or Download

Get the project files onto your local machine.

```bash
git clone <your-repository-url> # Or download and extract the ZIP
cd <project-directory>
```

### 3. Install Dependencies

Create a virtual environment (recommended) and install the required packages:

```bash
python -m venv venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate`
pip install -r requirements.txt
```

### 4. Configuration

The primary configuration happens within `example.py` (or potentially a separate config file/environment variables in a production setup).

**Crucial:** Edit `example.py` to set your specific LLM endpoint details:

```python
# example.py

# --- Configuration ---
API_URL = "https://your-vllm-or-openai-compatible-url/v1" # Replace with your actual endpoint URL
API_KEY = "your_actual_api_key" # !!! IMPORTANT: Replace with your key !!!
MODEL_NAME = "Qwen/Qwen3-30B-A3B-FP8" # Replace with the exact model identifier your endpoint expects

# Other default parameters (can be overridden per call)
MAX_TOKENS = 32000 # Adjust based on model limits and needs
TEMPERATURE = 0.7
```

**Security Warning:** For production or shared environments, **DO NOT** hardcode API keys directly in the script. Use environment variables or a secure configuration management system:

```python
# Example using environment variables (recommended)
import os
API_KEY = os.environ.get("VLLM_API_KEY", "default_key_if_not_set")
API_URL = os.environ.get("VLLM_API_URL", "default_url_if_not_set")
```

### 5. Create Input Files (Optional)

The `example.py` script expects `context.txt` and `longtext.txt`. If they don't exist, it will create basic placeholder files. You can create your own with more relevant content for testing:

*   **`context.txt`**: Text that the `ContextAgent` will prepend to its prompt.
*   **`longtext.txt`**: A longer piece of text for the `ChainOfAgents` system to process.

## Core Concepts

*   **Models (`model_logic.py`)**: Represent the connection to a specific LLM API endpoint. They handle the low-level details of formatting requests, making API calls, handling streaming responses, and parsing the results according to the endpoint's expected format (currently Chat Completions).
*   **Agents (`agent_logic.py`, `agents.py`)**: Represent individual actors or processing units. They inherit from `BaseAgent` and use a `Model` instance to perform their task. Primitives are designed for simple, reusable tasks. They receive input, format it appropriately (often using `_stream_and_aggregate` which converts prompts to the chat message format), interact with the model, and return a result.
*   **Systems (`systems.py`)**: Represent higher-level orchestrators. They manage complex workflows that might involve:
    *   Multiple steps.
    *   Using one or more Agents.
    *   Making multiple concurrent calls directly to the Model.
    *   Handling intermediate state or data transformations (like text chunking).
*   **Streaming**: LLM responses are received chunk-by-chunk as they are generated. This is crucial for:
    *   **Avoiding Timeouts:** Prevents intermediate proxies (like Cloudflare Tunnels) or the client itself from timing out while waiting for a potentially long generation.
    *   **Real-time Feedback:** Allows processing or displaying the response as it arrives.
    *   The `VLLMModel.call_stream` method returns an `AsyncGenerator` yielding text chunks.
*   **Concurrency (`asyncio`)**: Python's `asyncio` library is used extensively to handle multiple operations (like API calls) concurrently without blocking. This is vital for:
    *   **`MultiCallSystem`**: Makes many API calls simultaneously using `asyncio.gather`.
    *   **Efficiency**: Allows the program to do other work while waiting for network responses.
*   **Chat Completions API (`/v1/chat/completions`)**: The framework now uses this endpoint format. This means:
    *   Inputs are structured as a list of messages (e.g., `[{"role": "user", "content": "..."}]`).
    *   Responses often include richer structure, and reasoning/thought processes (like `<think>` tags) are typically part of the `delta.content` in the streamed chunks. The code is set up to capture this full content.

## Usage

1.  Ensure you have completed the **Setup & Installation** steps, including configuring your API key and URL in `example.py`.
2.  Navigate to the project directory in your terminal (and activate your virtual environment if you created one).
3.  Run the example script:

    ```bash
    python example.py
    ```

4.  **Output:**
    *   The script will print status messages and previews of the responses to the console.
    *   Detailed outputs will be saved to files within the `run_outputs/` directory (it will be created if it doesn't exist):
        *   `ex1_basic_agent_output.txt`: Output from the `BasicAgent`.
        *   `ex2_context_agent_output.txt`: Output from the `ContextAgent`.
        *   `ex3_chain_system_output.txt`: Final summarized output from the `ChainOfAgents` system.
        *   `run_outputs/ex4_multi_call_outputs/`: This sub-directory will contain multiple files (`website_1.txt`, `website_2.txt`, etc.), one for each concurrent call made by the `MultiCallSystem`.

## Code Documentation (Key Components)

*   **`model_logic.VLLMModel(model_name, api_url, api_key, ...)`**
    *   `__init__(...)`: Initializes the connection details and the `httpx.AsyncClient`. Points to the `/v1/chat/completions` endpoint.
    *   `call_stream(messages: List[Dict[str, str]], **kwargs) -> AsyncGenerator[str, None]`: Takes a list of chat messages, makes the streaming API call, handles retries, parses the chat stream delta chunks, and yields the `content` string chunks.
    *   `close_client()`: Closes the underlying HTTP client.
*   **`agent_logic.BaseAgent(agent_id, model)`**
    *   `_stream_and_aggregate(prompt: str, **kwargs) -> str`: Helper method that takes a simple prompt string, converts it to the `[{"role": "user", "content": prompt}]` format required by `call_stream`, calls the model's stream, and aggregates the resulting chunks into a single string.
*   **`agents.BasicAgent(agent_id, model)`**
    *   `run(prompt: str, **kwargs) -> str`: Takes a prompt string, uses `_stream_and_aggregate` to get the full response from the model, and returns it.
*   **`agents.ContextAgent(agent_id, model, context)`**
    *   `run(prompt: str, **kwargs) -> str`: Combines the stored `context` with the input `prompt`, then uses `_stream_and_aggregate` to get the full response, and returns it.
*   **`systems.ChainOfAgents(system_id, model, ...)`**
    *   `run(initial_prompt: str, long_text: str, **kwargs) -> str`: Chunks the `long_text`, iteratively calls its internal `processing_agent` (`BasicAgent`) to summarize chunks relative to the `initial_prompt`, and finally asks the agent to answer the `initial_prompt` based on the final summary.
*   **`systems.MultiCallSystem(system_id, model)`**
    *   `run(prompt: str, num_calls: int, output_dir: str, base_filename: str, **kwargs) -> Dict[str, str]`: Creates `num_calls` concurrent tasks. Each task calls the model via `_call_and_save_task` (which formats the prompt for the chat endpoint and streams the result directly to a unique file). Returns a dictionary mapping task IDs to output file paths or error messages.

## Troubleshooting

*   **`httpx.RemoteProtocolError: peer closed connection without sending complete message body (incomplete chunked read)` or similar Timeouts:**
    *   **Cause:** Often due to an intermediate proxy (like Cloudflare Tunnel with its ~100s inactivity timeout) closing the connection because the LLM took too long to send the *first* chunk or had too long a *pause between* chunks. Can also be caused by the VLLM server itself timing out or crashing.
    *   **VLLM Logs:** Check VLLM server logs. Look for errors (OOM), high load, or increasing `Waiting` requests and `Aborted request` messages – these indicate overload.
    *   **Solution 1: Reduce Concurrency:** Significantly lower `num_calls` in `example.py` when using `MultiCallSystem`. Find the stable limit for your setup.
    *   **Solution 2: Check Proxy/Tunnel:** Verify timeout settings in Cloudflare Tunnel or other proxies. Can they be increased?
    *   **Solution 3: Optimize VLLM:** Ensure the VLLM server is adequately resourced and configured.
*   **Missing `<think>` Tags or Initial Content:**
    *   **Cause:** Usually due to using the wrong API endpoint or parsing the response incorrectly. The code now uses `/v1/chat/completions` and parses `delta.content`, which *should* preserve these tags if the model includes them there.
    *   **Solution:** Ensure `model_logic.py` is correctly configured for the chat endpoint and your model actually outputs reasoning tags within the `content` field. Double-check the JSON structure of non-streaming responses from your endpoint using a tool like Insomnia or `curl`.
*   **Repetitive Output at the End of Files:**
    *   **Cause:** Typically the LLM itself getting stuck in a loop, often triggered by hitting `max_tokens`, unstable decoding under load, or specific sampling parameters.
    *   **Solution 1: Check `max_tokens`:** Is the limit being reached prematurely?
    *   **Solution 2: Adjust Sampling:** Slightly tweak `temperature` or `repetition_penalty` (if supported).
    *   **Solution 3: Reduce Load:** Lowering concurrency (`num_calls`) might improve model stability.
*   **Configuration Errors (401 Unauthorized, 404 Not Found):**
    *   **Cause:** Incorrect `API_KEY` or `API_URL`. Model name mismatch.
    *   **Solution:** Double-check the values in `example.py` (or your environment variables) against your VLLM endpoint details. Ensure the `MODEL_NAME` exactly matches what the server expects.
*   **Other `httpx` Errors (`ConnectError`, `ReadError`, etc.):**
    *   **Cause:** Network connectivity issues, server unavailability, DNS problems.
    *   **Solution:** The basic retry logic in `model_logic.py` helps. If persistent, check network connection, firewall rules, and server status.

## Customization & Extension

*   **Add New Models:** Create a new class in `model_logic.py` inheriting from `BaseModel` to support different LLM APIs (e.g., Anthropic, Cohere, a local Ollama instance).
*   **Add New Agents:** Create new classes in `agents.py` inheriting from `BaseAgent` for specialized tasks (e.g., a data extraction agent, a code generation agent).
*   **Add New Systems:** Create new classes in `systems.py` for more complex interactions (e.g., a debate system with multiple agents, a ReAct-style agent).
*   **Configuration Management:** Move configuration (API keys, URLs, model names, default parameters) out of `example.py` into environment variables, a `.env` file (using `python-dotenv`), or a dedicated YAML/JSON config file.
*   **Input/Output:** Modify how agents/systems receive input and handle output (e.g., read from/write to databases, interact via a web API).
*   **Enhanced Retries:** Implement more sophisticated retry logic using libraries like `tenacity`.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details (or adjust the badge/link if you choose a different license).