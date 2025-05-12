import asyncio
import logging
import os
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv

from tframex import (
    DiscussionPattern,
    Flow,
    InMemoryMemoryStore,
    Message,
    OpenAIChatLLM,
    ParallelPattern,
    RouterPattern,
    SequentialPattern,
    TFrameXApp,
    TFrameXRuntimeContext,
)

# --- Environment and Logging Setup ---
load_dotenv()
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - [%(funcName)s] - %(message)s",
)
logging.getLogger("tframex").setLevel(logging.INFO)
# For more detailed logs:
logging.getLogger("tframex.agents.llm_agent").setLevel(logging.DEBUG)
# logging.getLogger("tframex.agents.base").setLevel(logging.DEBUG)
# logging.getLogger("tframex.app").setLevel(logging.DEBUG)

# --- LLM Configurations ---
# Default LLM (e.g., a local, faster model for general tasks)
default_llm_config = OpenAIChatLLM(
    model_name=os.getenv("OPENAI_MODEL_NAME", "gpt-3.5-turbo"),  # Your default model
    api_base_url=os.getenv("OPENAI_API_BASE", "http://localhost:11434"),
    api_key=os.getenv("OPENAI_API_KEY", "ollama"),
)

if not default_llm_config.api_base_url:
    print("Error: OPENAI_API_BASE not set for default LLM.")
    exit(1)

# --- Initialize TFrameX Application ---
app = TFrameXApp(default_llm=default_llm_config)


@app.tool(description="Writes file to file system.")
async def write_file(file_path: str, content: str):
    with open(file_path, "w") as f:
        f.write(content)
