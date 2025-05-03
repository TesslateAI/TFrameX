# example_usage.py

import asyncio
import os
import logging
import time

# Import Model and the specific System
from tframex.model import VLLMModel # NEW
from tframex.systems import FrontendAgentSystem # Import the new system

# --- Basic Configuration ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("ExampleUsage")

# --- VLLM Configuration ---
API_URL = "https://vllm.tesslate.com/v1"
API_KEY = "tesslateapi" # Replace with your actual key if needed
MODEL_NAME = "Qwen/Qwen3-30B-A3B-FP8"

# --- Custom Output Paths ---
ARTIFACTS_PATH = "my_build_process_files" # Custom directory for plan.md, etc.
WEBSITE_PATH = "my_coffee_shop_website"  # Custom directory for index.html, style.css etc.

# --- Main Execution Function ---
async def main():
    """Runs the FrontendAgentSystem example."""
    start_time_main = time.time()
    logger.info("--- Starting FrontendAgentSystem Example ---")

    # 1. Create the Model Instance
    logger.info("Creating VLLM Model instance...")
    vllm_model = VLLMModel(
        model_name=MODEL_NAME,
        api_url=API_URL,
        api_key=API_KEY,
        # Using default tokens/temp from model, system overrides where needed
    )

    # 2. Create the FrontendAgentSystem Instance
    logger.info("Creating FrontendAgentSystem instance with custom paths...")
    frontend_builder = FrontendAgentSystem(
        system_id="coffee_shop_builder_01",
        model=vllm_model,
        artifacts_dir=ARTIFACTS_PATH,        # Pass custom path
        website_output_dir=WEBSITE_PATH,   # Pass custom path
        max_tokens_plan=34000,              # Can override defaults if needed
        max_tokens_file_gen=34000,           # Set high limit for file gen
        temperature=0.5
    )

    # 3. Define the User Request
    # user_request = "a simple one-page website for a fictional bakery called 'The Rolling Pin', include sections for 'About Us', 'Menu', 'Contact'. Use basic HTML and CSS."
    user_request = "a modern multi-page website for a coffee shop called 'The Daily Grind'. Pages needed: Home, Menu, About, Contact. Use Tailwind CSS for styling and make it responsive. Include placeholders for images."

    logger.info(f"User Request: '{user_request}'")
    logger.info(f"Artifacts will be saved to: '{os.path.abspath(ARTIFACTS_PATH)}'")
    logger.info(f"Website files will be saved to: '{os.path.abspath(WEBSITE_PATH)}'")

    # 4. Run the System
    logger.info("Executing the FrontendAgentSystem run...")
    try:
        await frontend_builder.run(user_request=user_request)
        logger.info("FrontendAgentSystem run completed.")
    except Exception as e:
        logger.error(f"An error occurred during the system run: {e}", exc_info=True) # Log traceback

    # 5. Cleanup - Close the model client
    # This is done *after* all systems using the model are finished.
    logger.info("--- Closing VLLM Model Client ---")
    try:
        await vllm_model.close_client()
        logger.info("VLLM Model client closed successfully.")
    except Exception as e:
        logger.error(f"Error closing VLLM model client: {e}")

    end_time_main = time.time()
    logger.info(f"--- Example finished in {end_time_main - start_time_main:.2f} seconds ---")


# --- Standard Python Entry Point ---
if __name__ == "__main__":
    # Ensure the custom output directories exist before starting
    # (The class also does this, but doing it here provides early feedback)
    if not os.path.exists(ARTIFACTS_PATH):
        os.makedirs(ARTIFACTS_PATH)
        print(f"Created artifacts directory: {ARTIFACTS_PATH}")
    if not os.path.exists(WEBSITE_PATH):
        os.makedirs(WEBSITE_PATH)
        print(f"Created website output directory: {WEBSITE_PATH}")

    asyncio.run(main())