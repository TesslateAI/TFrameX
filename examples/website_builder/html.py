# software_builder.py

import asyncio
import os
import logging
import time
import re
from typing import List, Dict, Tuple, Optional

# Import required components from existing modules
from tframex.model import VLLMModel # NEW
from tframex.agents import BasicAgent # NEW
# We won't use MultiCallSystem directly for file gen due to prompt limitations,
# but the system concept is used via asyncio.gather

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("SoftwareBuilder")

# --- Configuration ---
# Ideally, load from config file or environment variables
API_URL = "https://vllm.tesslate.com/v1"
API_KEY = "tesslateapi" # Replace with your actual key if needed
MODEL_NAME = "Qwen/Qwen3-30B-A3B-FP8"
MAX_TOKENS_PLAN = 34000     # Tokens for planning stages
MAX_TOKENS_FILE_GEN = 34000 # Max tokens for generating a single file (leaving buffer for think tags etc.)
DEFAULT_TEMPERATURE = 0.5 # Slightly lower temp for more predictable code/planning
OUTPUT_WEBSITE_DIR = "generated_website" # Directory to save the generated website

# --- Helper Functions ---

def save_file(filepath: str, content: str, base_dir: str = OUTPUT_WEBSITE_DIR):
    """Saves content to a file, creating directories if needed."""
    # Ensure the path is relative to the base directory
    # Prevent absolute paths or path traversal (basic security)
    if os.path.isabs(filepath) or ".." in filepath:
        logger.error(f"Invalid filepath detected (absolute or traversal): {filepath}")
        return False
    
    full_path = os.path.join(base_dir, filepath)
    try:
        # Create directories if they don't exist
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(content)
        logger.info(f"Successfully saved file: {full_path}")
        return True
    except OSError as e:
        logger.error(f"Failed to save file {full_path}: {e}")
        return False
    except Exception as e:
        logger.error(f"An unexpected error occurred saving file {full_path}: {e}")
        return False

def extract_code(llm_output: str) -> Optional[str]:
    """Extracts the first code block (```...```) from LLM output."""
    # Regex to find markdown code blocks, capturing the content
    # It handles optional language identifiers (like ```html)
    match = re.search(r"```(?:[a-zA-Z0-9]*\n)?(.*?)```", llm_output, re.DOTALL | re.IGNORECASE)
    if match:
        code = match.group(1).strip()
        # Basic check if code seems plausible (not empty)
        if code:
            logger.debug(f"Extracted code block (length: {len(code)}).")
            return code
        else:
             logger.warning("Found code block delimiters but content inside was empty.")
             return None # Explicitly return None if block is empty
    else:
        logger.warning("No markdown code block found in the LLM output.")
        # Sometimes the LLM might forget the ```, attempt to return the whole thing if it looks like code
        if llm_output.strip().startswith('<') or llm_output.strip().startswith(('function', 'const', 'let', 'var', 'import', 'public class', '@', '.', '#')):
             logger.warning("No code block found, but output resembles code. Returning full output.")
             return llm_output.strip()
        return None

def parse_task_distribution(dist_output: str) -> Tuple[Optional[str], List[Dict[str, str]]]:
    """
    Parses the Task Distributor output to extract memory and file prompts.
    Expected format:
    <memory>...</memory>
    <prompt filename="file1.html" url="...">...</prompt>
    <prompt filename="style.css" url="...">...</prompt>
    """
    memory = None
    prompts = []

    # Extract memory
    memory_match = re.search(r"<memory>(.*?)</memory>", dist_output, re.DOTALL | re.IGNORECASE)
    if memory_match:
        memory = memory_match.group(1).strip()
        logger.info("Extracted memory block.")
    else:
        logger.warning("Could not find <memory> block in Task Distributor output.")

    # Extract prompts
    # Using re.finditer to find all prompt blocks
    prompt_pattern = re.compile(
        r'<prompt\s+filename="(?P<filename>[^"]+)"(?:\s+url="(?P<url>[^"]+)?"\s*)?>(?P<prompt_content>.*?)</prompt>',
        re.DOTALL | re.IGNORECASE
    )
    for match in prompt_pattern.finditer(dist_output):
        data = match.groupdict()
        filename = data['filename'].strip()
        prompt_content = data['prompt_content'].strip()
        url = data.get('url', '').strip() # Handle optional url

        if filename and prompt_content:
            prompts.append({
                "filename": filename,
                "url": url if url else filename, # Default url to filename if not provided
                "prompt": prompt_content
            })
            logger.debug(f"Extracted prompt for file: {filename}")
        else:
            logger.warning(f"Found prompt block but filename or content was empty: {match.group(0)}")


    if not prompts:
         logger.warning("Could not find any valid <prompt ...> blocks in Task Distributor output.")

    return memory, prompts

def strip_think_tags(text: str) -> str:
    """Removes content up to and including the first </think> tag if present."""
    think_end_tag = "</think>"
    tag_pos = text.find(think_end_tag)
    if tag_pos != -1:
        logger.debug("Found </think> tag, stripping preceding content.")
        return text[tag_pos + len(think_end_tag):].strip()
    else:
        # logger.debug("No </think> tag found, using full response.")
        return text # Return original text if tag not found

# --- Main Orchestration ---

async def build_software(user_request: str):
    """Orchestrates the software building process."""
    start_time_build = time.time()
    logger.info(f"Starting software build process for request: '{user_request}'")

    # 0. Initialize Model and Base Agent
    logger.info("Initializing VLLM Model and Basic Agent...")
    try:
        vllm_model = VLLMModel(
            model_name=MODEL_NAME,
            api_url=API_URL,
            api_key=API_KEY,
            # Use defaults, specific token limits will be passed per call
        )
        # Re-use a single BasicAgent instance for sequential planning/distribution steps
        orchestration_agent = BasicAgent(agent_id="orchestrator_001", model=vllm_model)
    except Exception as e:
        logger.error(f"Fatal Error: Failed to initialize VLLM Model or Basic Agent: {e}")
        return

    # === STEP 1: Planner Agent ===
    logger.info("\n--- Step 1: Planning ---")
    plan = None
    planner_prompt = f"""
You are an expert software architect and planner. Your goal is to create a comprehensive plan to build the software requested by the user.

User Request: "{user_request}"

Instructions:
1.  Analyze the user request thoroughly.
2.  Think through the project structure: Define a clear and logical directory and file structure. List all necessary files (HTML, CSS, JavaScript, images, etc.).
3.  Think through styling and UI/UX: Describe the desired look and feel, color palette, typography, and any key UI components. Consider responsiveness.
4.  Think through images and media: Identify the types of images or media needed and suggest placeholders or sources if applicable.
5.  Think through formatting and content: Outline the content required for each page or component.
6.  Think through frameworks and libraries: Recommend appropriate technologies (e.g., Tailwind CSS was mentioned in context, stick to basic HTML/CSS/JS if not specified, but plan for it if requested). If using libraries, specify how they should be included (CDN, local).
7.  Think through caveats and best practices: Mention any potential challenges, limitations, or important development practices (like accessibility, SEO basics for web).
8.  Output *only* the detailed plan in a clear, structured format (e.g., using markdown). Do not include any conversational text before or after the plan itself. Ensure the plan is detailed enough for another agent to break it down into specific file-generation tasks.
"""
    try:
        logger.info("Calling Planner Agent...")
        raw_plan_response = await orchestration_agent.run(planner_prompt, max_tokens=MAX_TOKENS_PLAN, temperature=DEFAULT_TEMPERATURE)
        plan = strip_think_tags(raw_plan_response) # Strip think tags *after* getting the full response
        if not plan or plan.startswith("ERROR:") :
             logger.error(f"Planner Agent failed or returned an error: {plan}")
             raise ValueError("Planner Agent failed.")
        logger.info("Planner Agent finished. Plan received (first 500 chars):\n" + plan[:500] + "...")
        # Save the plan for review
        save_file("plan.md", f"User Request:\n{user_request}\n\n---\n\nGenerated Plan:\n{plan}", base_dir="build_artifacts")

    except Exception as e:
        logger.error(f"Error during Planning step: {e}")
        await vllm_model.close_client()
        return

    # === STEP 2: Task Distribution Agent ===
    logger.info("\n--- Step 2: Task Distribution ---")
    memory = None
    file_prompts = []
    distributor_prompt = f"""
You are a task distribution agent. Your input is a software development plan. Your goal is to break down this plan into:
1.  A shared `<memory>` block containing essential context, design guidelines, framework choices, and overall architecture described in the plan that *all* subsequent file-generation agents need to know to ensure consistency. This should be lengthy. 
2.  Individual `<prompt>` blocks, one for *each file* identified in the plan's file structure. Each prompt block must specify the target `filename` and contain a highly detailed and specific prompt instructing another agent on *exactly* what code to generate for that single file, referencing the shared memory/plan as needed.
Any information the prompt that is coupled with another file, the entire integration must be properly and fully explained. Make the most solid pseudocode possible and talk about every single tiny detail in the prompt. 
Development Plan:
--- START PLAN ---
{plan}
--- END PLAN ---

Instructions:
1.  Carefully read the entire Development Plan.
2.  Extract the core principles, design language, chosen frameworks/libraries, color schemes, typography, file structure overview, and any global requirements into a concise `<memory>` block. This memory block should *not* contain specific file contents but rather the shared context.
3.  For *each* file mentioned in the plan's file structure (e.g., index.html, style.css, script.js, about.html, assets/logo.png):
    *   If it's a code file (HTML, CSS, JS, etc.): Create a `<prompt filename="path/to/file.ext">` block. Inside this block, write a very specific prompt detailing exactly what code needs to be in this file. Include details about structure, content (referencing the plan), functionality, required HTML elements, CSS classes (mentioning framework if used), JS functions, links to other files (using relative paths based on the plan's structure), and references to the shared `<memory>` context if necessary. Instruct the agent receiving this prompt to output *only* the raw code for the file, enclosed in appropriate markdown ``` code blocks.
    *   If it's a non-code asset (like an image placeholder path mentioned in the plan): You can optionally create a prompt block instructing to note this placeholder or skip creating a prompt block for it. Focus on generating code files.
4.  Ensure filenames and relative paths in the prompts are consistent with the file structure defined in the plan.
5.  Output *only* the `<memory>` block followed immediately by all the `<prompt>` blocks. Do not include any other conversational text, introductions, or summaries.

Example Output Structure:
<memory>
Shared context, design guidelines, framework info...
</memory>
<prompt filename="index.html" url="index.html">
Generate the complete HTML structure for the main landing page (index.html). Use semantic HTML5 tags. Include a header, navigation (linking to about.html), main content area, and footer based on the plan and shared memory design. Use Tailwind CSS classes defined in the memory block for styling. Content should be based on the 'Home Page Content' section of the plan. Output only the complete HTML code in a ```html ... ``` block.
</prompt>
<prompt filename="css/style.css" url="css/style.css">
Generate the CSS rules for the website based on the plan and memory. Define styles for base elements, utility classes (if not using a framework like Tailwind mentioned in memory), and specific component styles outlined in the plan. Reference the color palette and typography from memory. Output only the CSS code in a ```css ... ``` block.
</prompt>
<prompt filename="js/script.js" url="js/script.js">
Generate the JavaScript code for interactive elements mentioned in the plan, like a mobile menu toggle or an image carousel. Ensure code is clean and follows best practices mentioned in memory. Output only the JavaScript code in a ```javascript ... ``` block.
</prompt>
... (more prompt blocks for other files)
"""
    try:
        logger.info("Calling Task Distributor Agent...")
        raw_dist_response = await orchestration_agent.run(distributor_prompt, max_tokens=MAX_TOKENS_PLAN, temperature=DEFAULT_TEMPERATURE) # Plan can be long
        dist_output = strip_think_tags(raw_dist_response) # Strip think tags
        if not dist_output or dist_output.startswith("ERROR:") :
             logger.error(f"Task Distributor Agent failed or returned an error: {dist_output}")
             raise ValueError("Task Distributor Agent failed.")

        logger.info("Task Distributor Agent finished. Parsing output...")
        memory, file_prompts = parse_task_distribution(dist_output)

        if not memory or not file_prompts:
            logger.error("Failed to parse memory or file prompts from Task Distributor output. Check the output format.")
            # Save the raw output for debugging
            save_file("task_distribution_raw_output.txt", f"Distributor Prompt:\n{distributor_prompt}\n\n---\n\nRaw Response:\n{raw_dist_response}", base_dir="build_artifacts")
            raise ValueError("Failed to parse Task Distributor output.")

        logger.info(f"Successfully parsed memory and {len(file_prompts)} file prompts.")
        # Save parsed data for review
        parsed_prompts_log = f"<memory>\n{memory}\n</memory>\n\n" + "\n\n".join([f"<prompt filename=\"{p['filename']}\">\n{p['prompt']}\n</prompt>" for p in file_prompts])
        save_file("task_distribution_parsed.txt", parsed_prompts_log, base_dir="build_artifacts")

    except Exception as e:
        logger.error(f"Error during Task Distribution step: {e}")
        await vllm_model.close_client()
        return

    # === STEP 3: File Generation Agents (Parallel Execution) ===
    logger.info("\n--- Step 3: Generating Files in Parallel ---")
    if not file_prompts:
        logger.warning("No file prompts were generated. Skipping file generation step.")
    else:
        # Create a new agent instance for generation tasks if needed, or reuse
        # Let's create a separate one for clarity, though orchestration_agent could be reused
        generation_agent = BasicAgent(agent_id="generator_001", model=vllm_model)
        tasks = []
        file_mapping = {} # Keep track of which task corresponds to which file

        logger.info(f"Preparing {len(file_prompts)} file generation tasks...")
        for i, task_info in enumerate(file_prompts):
            filename = task_info["filename"]
            specific_prompt = task_info["prompt"]

            # Construct the final prompt for the generation agent
            generation_prompt = f"""
<memory>
{memory}
</memory>

<prompt filename="{filename}">
{specific_prompt}
</prompt>

Based *only* on the specific prompt for `{filename}` above and the shared `<memory>` context, generate the complete, raw code content for the file `{filename}`.
Output *only* the raw code content for the file, enclosed in the appropriate markdown code block (e.g., ```html ... ```, ```css ... ```, ```javascript ... ```).
Do not include any other text, explanations, introductions, or summaries outside the code block.
For tailwind, use this: <script src="https://cdn.jsdelivr.net/npm/@tailwindcss/browser@4"></script>
"""
            # Create the async task
            task = generation_agent.run(generation_prompt, max_tokens=MAX_TOKENS_FILE_GEN, temperature=DEFAULT_TEMPERATURE)
            tasks.append(task)
            file_mapping[i] = filename # Map task index to filename

            logger.debug(f"Created generation task for: {filename}")

        # Run tasks concurrently
        logger.info(f"Launching {len(tasks)} file generation tasks concurrently...")
        start_time_gen = time.time()
        # Use return_exceptions=True to handle potential errors in individual tasks
        results = await asyncio.gather(*tasks, return_exceptions=True)
        end_time_gen = time.time()
        logger.info(f"File generation tasks completed in {end_time_gen - start_time_gen:.2f} seconds.")

        # Process results
        logger.info("Processing generation results and saving files...")
        files_saved = 0
        files_failed = 0
        for i, result in enumerate(results):
            filename = file_mapping[i]
            logger.debug(f"Processing result for: {filename}")

            if isinstance(result, Exception):
                logger.error(f"Task for {filename} failed with exception: {result}")
                files_failed += 1
                # Optionally save the error to a file
                save_file(f"{filename}.error.txt", f"Task failed with exception:\n{result}", base_dir=OUTPUT_WEBSITE_DIR)
            elif isinstance(result, str) and result.startswith("ERROR:"):
                 logger.error(f"Task for {filename} returned an error: {result}")
                 files_failed += 1
                 save_file(f"{filename}.error.txt", f"Task returned error:\n{result}", base_dir=OUTPUT_WEBSITE_DIR)
            elif isinstance(result, str):
                # Strip think tags from the raw response before extracting code
                generation_output = strip_think_tags(result)
                # Extract code block
                code_content = extract_code(generation_output)
                if code_content:
                    if save_file(filename, code_content, base_dir=OUTPUT_WEBSITE_DIR):
                        files_saved += 1
                    else:
                        files_failed += 1
                else:
                    logger.error(f"Failed to extract code block for {filename}. Saving raw output.")
                    files_failed += 1
                    # Save the raw output (after stripping think tags) for debugging
                    save_file(f"{filename}.raw_output.txt", generation_output, base_dir=OUTPUT_WEBSITE_DIR)
            else:
                 logger.error(f"Task for {filename} returned unexpected result type: {type(result)}")
                 files_failed += 1
                 save_file(f"{filename}.error.txt", f"Task returned unexpected result type: {type(result)}\n{result}", base_dir=OUTPUT_WEBSITE_DIR)

        logger.info(f"File generation finished. Saved: {files_saved}, Failed/Skipped: {files_failed}")

    # === STEP 4: Cleanup ===
    logger.info("\n--- Step 4: Cleaning up ---")
    try:
        await vllm_model.close_client()
        logger.info("VLLM Model client closed.")
    except Exception as e:
        logger.error(f"Error closing VLLM model client: {e}")

    end_time_build = time.time()
    logger.info(f"--- Software build process completed in {end_time_build - start_time_build:.2f} seconds ---")
    logger.info(f"Generated website files should be in the '{OUTPUT_WEBSITE_DIR}' directory.")

# --- Main Execution Block ---
if __name__ == "__main__":
    print("Software Builder Initialized.")
    # Ensure the base output directory exists
    if not os.path.exists(OUTPUT_WEBSITE_DIR):
        os.makedirs(OUTPUT_WEBSITE_DIR)
        print(f"Created output directory: {OUTPUT_WEBSITE_DIR}")
    # Ensure artifact directory exists
    if not os.path.exists("build_artifacts"):
        os.makedirs("build_artifacts")
        print(f"Created build artifacts directory: build_artifacts")


    initial_request = input("Enter your software request (e.g., 'a website for a coffee shop frontend'): ")

    if not initial_request.strip():
        print("No request entered. Exiting.")
    else:
        # Run the main asynchronous function
        asyncio.run(build_software(initial_request))