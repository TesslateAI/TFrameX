# example.py
import asyncio
import os
import logging
import time
from dotenv import load_dotenv

# Load .env into environment
load_dotenv()

# Import Model, Agents, and Systems
from model_logic import VLLMModel
from agents import BasicAgent, ContextAgent
from systems import ChainOfAgents, MultiCallSystem

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Configuration ---
API_URL = os.getenv("API_URL")
API_KEY = os.getenv("API_KEY")
MODEL_NAME = os.getenv("MODEL_NAME")
MAX_TOKENS = int(os.getenv("MAX_TOKENS", 32000))
TEMPERATURE = float(os.getenv("TEMPERATURE", 0.7))

# --- File Paths ---
CONTEXT_FILE = "context.txt"
LONG_TEXT_FILE = "longtext.txt"
OUTPUT_DIR = "example_outputs"

# --- Helper Function ---
def save_output(filename: str, content: str, directory: str = OUTPUT_DIR):
    """Saves content to a file in the specified directory."""
    if not os.path.exists(directory):
        os.makedirs(directory)
    filepath = os.path.join(directory, filename)
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        logger.info(f"Output saved to {filepath}")
    except Exception as e:
        logger.error(f"Failed to save output to {filepath}: {e}")


# --- Main Execution ---
async def main():
    """Runs the demonstration examples."""
    start_time = time.time()
    logger.info("--- Starting Examples ---")

    # 0. Create the Model Instance
    logger.info("Creating VLLM Model instance...")
    vllm_model = VLLMModel(
        model_name=MODEL_NAME,
        api_url=API_URL,
        api_key=API_KEY,
        default_max_tokens=MAX_TOKENS,
        default_temperature=TEMPERATURE
    )

    # --- Example 1: Basic Agent ---
    logger.info("\n--- Example 1: Basic Agent ---")
    basic_agent = BasicAgent(agent_id="basic_001", model=vllm_model)
    basic_prompt = "Explain the difference between synchronous and asynchronous programming using a simple analogy."
    basic_output_file = "ex1_basic_agent_output.txt"
    print(f"Running BasicAgent with prompt: '{basic_prompt}'")

    basic_response = await basic_agent.run(basic_prompt, max_tokens=300) # Override default tokens

    print(f"BasicAgent Response:\n{basic_response[:200]}...") # Print preview
    save_output(basic_output_file, f"Prompt:\n{basic_prompt}\n\nResponse:\n{basic_response}")


    # --- Example 2: Context Agent ---
    logger.info("\n--- Example 2: Context Agent ---")
    context_content = ""
    try:
        with open(CONTEXT_FILE, 'r', encoding='utf-8') as f:
            context_content = f.read()
        logger.info(f"Loaded context from {CONTEXT_FILE}")
    except FileNotFoundError:
        logger.warning(f"{CONTEXT_FILE} not found. Using default context.")
        context_content = "The user is interested in Python programming best practices."
        save_output(CONTEXT_FILE, context_content, directory=".") # Create dummy file

    context_agent = ContextAgent(agent_id="context_001", model=vllm_model, context=context_content)
    context_prompt = "What are 3 key recommendations for writing clean code?"
    context_output_file = "ex2_context_agent_output.txt"
    print(f"Running ContextAgent with prompt: '{context_prompt}'")

    context_response = await context_agent.run(context_prompt)

    print(f"ContextAgent Response:\n{context_response[:200]}...")
    save_output(context_output_file, f"Context:\n{context_content}\n\nPrompt:\n{context_prompt}\n\nResponse:\n{context_response}")

    # --- Example 3: Chain of Agents System ---
    logger.info("\n--- Example 3: Chain of Agents System ---")
    long_text_content = ""
    try:
        with open(LONG_TEXT_FILE, 'r', encoding='utf-8') as f:
            long_text_content = f.read()
        logger.info(f"Loaded long text from {LONG_TEXT_FILE}")
    except FileNotFoundError:
        logger.warning(f"{LONG_TEXT_FILE} not found. Using default long text.")
        long_text_content = ("Python is dynamically typed, which offers flexibility but can lead to runtime errors if not carefully managed. "
                             "Static analysis tools like MyPy help mitigate this by adding optional type hints and checking them before runtime. "
                             "Another key aspect is its extensive standard library, covering areas from web protocols to GUI development. "
                             "The Global Interpreter Lock (GIL) in CPython means that only one thread executes Python bytecode at a time in a single process, which can limit CPU-bound parallelism but simplifies memory management. "
                             "Asynchronous programming with asyncio provides concurrency for I/O-bound tasks without needing multiple threads.")
        save_output(LONG_TEXT_FILE, long_text_content, directory=".") # Create dummy file

    chain_system = ChainOfAgents(system_id="chain_summarizer_01", model=vllm_model, chunk_size=200, chunk_overlap=50)
    chain_prompt = "Based on the provided text, explain the implications of Python's dynamic typing and the GIL."
    chain_output_file = "ex3_chain_system_output.txt"
    print(f"Running ChainOfAgents system with prompt: '{chain_prompt}'")

    # Reduce max_tokens for intermediate summaries if needed via kwargs
    chain_response = await chain_system.run(initial_prompt=chain_prompt, long_text=long_text_content, max_tokens=400) # kwargs passed down

    print(f"ChainOfAgents Response:\n{chain_response[:200]}...")
    save_output(chain_output_file, f"Initial Prompt:\n{chain_prompt}\n\nLong Text Input (preview):\n{long_text_content[:300]}...\n\nFinal Response:\n{chain_response}")


    # --- Example 4: Multi Call System ---
    logger.info("\n--- Example 4: Multi Call System ---")
    multi_call_system = MultiCallSystem(system_id="multi_haiku_01", model=vllm_model)
    multi_call_prompt = "Make the best looking website for a html css js tailwind coffee shop landing page."
    num_calls = 15 # Use a smaller number for testing, change to 120 if needed
    # num_calls = 120
    multi_call_output_dir = os.path.join(OUTPUT_DIR, "ex4_multi_call_outputs")
    print(f"Running MultiCallSystem for {num_calls} calls with prompt: '{multi_call_prompt}'")

    multi_results = await multi_call_system.run(
        prompt=multi_call_prompt,
        num_calls=num_calls,
        output_dir=multi_call_output_dir,
        base_filename="website",
        max_tokens=35000 # Keep haikus short
    )

    print(f"MultiCallSystem finished. Results saved in '{multi_call_output_dir}'.")
    print("Result Summary (File path or Error):")
    for task_id, result_path_or_error in multi_results.items():
        print(f"  {task_id}: {result_path_or_error}")


    # --- Cleanup ---
    logger.info("\n--- Closing Model Client ---")
    await vllm_model.close_client()

    end_time = time.time()
    logger.info(f"--- All examples finished in {end_time - start_time:.2f} seconds ---")


if __name__ == "__main__":
    # Create dummy files if they don't exist for the first run
    if not os.path.exists(CONTEXT_FILE):
        save_output(CONTEXT_FILE, "Default context: Focus on AI safety and alignment.", directory=".")
    if not os.path.exists(LONG_TEXT_FILE):
         save_output(LONG_TEXT_FILE, "This is placeholder text. Replace it with a much longer document to properly test the ChainOfAgents system. It should discuss various topics to allow for meaningful summarization and chunking.", directory=".")

    asyncio.run(main())