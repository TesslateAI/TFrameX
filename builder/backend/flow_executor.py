import asyncio
import os
import logging
import time
import re
from typing import List, Dict, Tuple, Optional, Any
from dotenv import load_dotenv

# Load .env into environment variables
load_dotenv()

# Import tframex components
try:
    from tframex.model import VLLMModel
    from tframex.agents import BasicAgent, ContextAgent
    from tframex.systems import ChainOfAgents, MultiCallSystem
except ImportError as e:
    logging.error(f"Failed to import tframex components. Is it installed? Error: {e}")
    # Define dummy classes if import fails to prevent immediate crash
    class VLLMModel: pass
    class BasicAgent: pass
    class ContextAgent: pass
    class ChainOfAgents: pass
    class MultiCallSystem: pass

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("FlowExecutor")

# --- Configuration from Environment ---
API_URL = os.getenv("API_URL", "http://localhost:8000/v1") # Provide defaults
API_KEY = os.getenv("API_KEY", "your_api_key")
MODEL_NAME = os.getenv("MODEL_NAME", "default_model")
DEFAULT_MAX_TOKENS = int(os.getenv("MAX_TOKENS", 32000))
DEFAULT_TEMPERATURE = float(os.getenv("TEMPERATURE", 0.7))
MULTI_CALL_OUTPUT_DIR = os.getenv("MULTI_CALL_OUTPUT_DIR", "example_outputs/ex4_multi_call_outputs")
SOFTWARE_BUILDER_OUTPUT_DIR = os.getenv("SOFTWARE_BUILDER_OUTPUT_DIR", "generated_website")
SOFTWARE_BUILDER_ARTIFACTS_DIR = os.getenv("SOFTWARE_BUILDER_ARTIFACTS_DIR", "build_artifacts")

# --- Global Model Instance (Lazy Loaded) ---
# Avoid creating the model immediately on import
vllm_model_instance: Optional[VLLMModel] = None
model_lock = asyncio.Lock() # Ensure only one instance is created

async def get_model() -> VLLMModel:
    """Gets or creates the VLLMModel instance."""
    global vllm_model_instance
    async with model_lock:
        if vllm_model_instance is None:
            logger.info("Initializing VLLM Model instance...")
            try:
                vllm_model_instance = VLLMModel(
                    model_name=MODEL_NAME,
                    api_url=API_URL,
                    api_key=API_KEY,
                    default_max_tokens=DEFAULT_MAX_TOKENS,
                    default_temperature=DEFAULT_TEMPERATURE
                )
                # Test connection briefly - optional
                # await vllm_model_instance.generate("test connection")
                logger.info("VLLM Model instance created.")
            except Exception as e:
                logger.error(f"Fatal Error: Failed to initialize VLLM Model: {e}")
                raise RuntimeError(f"Could not initialize VLLM Model: {e}") # Raise to signal failure
        return vllm_model_instance

# --- Helper Functions (Adapted from Software Builder) ---

def save_artifact(filepath: str, content: str, base_dir: str):
    """Saves content to a file, creating directories if needed."""
    if os.path.isabs(filepath) or ".." in filepath:
        logger.error(f"Invalid filepath detected (absolute or traversal): {filepath}")
        return False
    
    # Ensure base_dir exists before joining
    os.makedirs(base_dir, exist_ok=True)
    full_path = os.path.join(base_dir, filepath)
    
    try:
        # Create intermediate directories for the file itself
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
    match = re.search(r"```(?:[a-zA-Z0-9]*\n)?(.*?)```", llm_output, re.DOTALL | re.IGNORECASE)
    if match:
        code = match.group(1).strip()
        return code if code else None
    # Attempt to return full output if it looks like code and no block found
    if llm_output.strip().startswith('<') or llm_output.strip().startswith(('function', 'const', 'let', 'var', 'import', 'public class', '@', '.', '#')):
         logger.warning("No code block ``` found, but output resembles code. Returning full output.")
         return llm_output.strip()
    logger.warning("No markdown code block found in the LLM output.")
    return None # Return None if no code block and doesn't resemble code

def parse_task_distribution(dist_output: str) -> Tuple[Optional[str], List[Dict[str, str]]]:
    memory = None
    prompts = []
    memory_match = re.search(r"<memory>(.*?)</memory>", dist_output, re.DOTALL | re.IGNORECASE)
    if memory_match:
        memory = memory_match.group(1).strip()
    prompt_pattern = re.compile(
        r'<prompt\s+filename="(?P<filename>[^"]+)"(?:\s+url="(?P<url>[^"]+)?"\s*)?>(?P<prompt_content>.*?)</prompt>',
        re.DOTALL | re.IGNORECASE
    )
    for match in prompt_pattern.finditer(dist_output):
        data = match.groupdict()
        filename = data['filename'].strip()
        prompt_content = data['prompt_content'].strip()
        url = data.get('url', '').strip()
        if filename and prompt_content:
            prompts.append({"filename": filename, "url": url if url else filename, "prompt": prompt_content})
    return memory, prompts

def strip_think_tags(text: str) -> str:
    think_end_tag = "</think>"
    tag_pos = text.find(think_end_tag)
    if tag_pos != -1:
        return text[tag_pos + len(think_end_tag):].strip()
    return text

# --- Execution Logic ---

async def execute_node(node_data: Dict[str, Any], run_id: str) -> Any:
    """Executes a single node based on its type and data."""
    node_type = node_data.get('type')
    node_id = node_data.get('id', 'unknown_node')
    data = node_data.get('data', {})
    start_time = time.time()
    logger.info(f"[{run_id}] Executing node '{node_id}' of type '{node_type}'")

    try:
        model = await get_model()
        # --- Handle Different Node Types ---
        if node_type == 'basicAgent':
            prompt = data.get('prompt', '')
            max_tokens = data.get('maxTokens') or None # Use None for default
            if not prompt: return f"Error: Prompt is missing for BasicAgent '{node_id}'"

            agent = BasicAgent(agent_id=f"{node_id}_{run_id}", model=model)
            response = await agent.run(prompt, max_tokens=max_tokens)
            return response

        elif node_type == 'contextAgent':
            prompt = data.get('prompt', '')
            context = data.get('context', '')
            max_tokens = data.get('maxTokens') or None
            if not prompt: return f"Error: Prompt is missing for ContextAgent '{node_id}'"
            # Allow empty context, use default if needed

            agent = ContextAgent(agent_id=f"{node_id}_{run_id}", model=model, context=context)
            response = await agent.run(prompt, max_tokens=max_tokens)
            return response

        elif node_type == 'chainOfAgents':
            initial_prompt = data.get('initialPrompt', '')
            long_text = data.get('longText', '')
            chunk_size = int(data.get('chunkSize', 2000)) # Provide defaults
            chunk_overlap = int(data.get('chunkOverlap', 200))
            max_tokens = data.get('maxTokens') or None

            if not initial_prompt: return f"Error: Initial Prompt is missing for ChainOfAgents '{node_id}'"
            if not long_text: return f"Error: Long Text is missing for ChainOfAgents '{node_id}'"

            system = ChainOfAgents(system_id=f"{node_id}_{run_id}", model=model, chunk_size=chunk_size, chunk_overlap=chunk_overlap)
            response = await system.run(initial_prompt=initial_prompt, long_text=long_text, max_tokens=max_tokens)
            return response

        elif node_type == 'multiCallSystem':
            prompt = data.get('prompt', '')
            num_calls = int(data.get('numCalls', 3)) # Default to small number
            output_dir = data.get('outputDir') or MULTI_CALL_OUTPUT_DIR
            base_filename = data.get('baseFilename', 'output')
            max_tokens = data.get('maxTokens') or 1000 # Default smaller for calls

            if not prompt: return f"Error: Prompt is missing for MultiCallSystem '{node_id}'"

            system = MultiCallSystem(system_id=f"{node_id}_{run_id}", model=model)
            # Ensure output dir exists
            os.makedirs(output_dir, exist_ok=True)
            results = await system.run(
                prompt=prompt,
                num_calls=num_calls,
                output_dir=output_dir,
                base_filename=base_filename,
                max_tokens=max_tokens
            )
            # Format results for display
            result_summary = f"MultiCallSystem completed. Results saved in '{output_dir}'.\nSummary:\n"
            for task_id, result_path_or_error in results.items():
                 result_summary += f"  - {task_id}: {result_path_or_error}\n"
            return result_summary

        elif node_type == 'softwareBuilder':
            user_request = data.get('userRequest', '')
            if not user_request: return f"Error: User Request is missing for SoftwareBuilder '{node_id}'"
            # Delegate to the dedicated software builder function
            log_output = await run_software_builder(user_request, run_id)
            return log_output

        else:
            logger.warning(f"[{run_id}] Unknown node type encountered: {node_type}")
            return f"Error: Unknown node type '{node_type}'"

    except Exception as e:
        logger.error(f"[{run_id}] Error executing node '{node_id}' ({node_type}): {e}", exc_info=True)
        return f"Error executing node '{node_id}': {e}"
    finally:
        end_time = time.time()
        logger.info(f"[{run_id}] Node '{node_id}' execution finished in {end_time - start_time:.2f} seconds.")


async def run_flow(nodes: List[Dict[str, Any]], edges: List[Dict[str, Any]]) -> str:
    """
    Executes the flow.
    Current Simple Implementation: Executes *each* runnable node independently.
    Ignores edges for data passing for now. Returns a combined log.
    """
    run_id = f"run_{int(time.time())}"
    logger.info(f"--- Starting Flow Execution ({run_id}) ---")
    output_log = [f"--- Flow Execution Start ({run_id}) ---"]
    execution_tasks = []
    start_time = time.time()

    # In this simple version, we just run all nodes provided.
    # A more complex version would determine execution order based on edges.
    if not nodes:
        return "No nodes found in the flow."

    for node in nodes:
        # We wrap execute_node to capture results along with node info
        async def task_wrapper(n):
            result = await execute_node(n, run_id)
            return {"id": n.get('id'), "type": n.get('type'), "result": result}
        
        execution_tasks.append(task_wrapper(node))

    # Run tasks (could be concurrent if desired, but run sequentially for now for simpler logging)
    # results = await asyncio.gather(*execution_tasks, return_exceptions=True)

    # Sequential execution for clearer logs in this version:
    results = []
    for node in nodes:
         # Only run nodes that seem like "end points" or stand-alone systems for now
         # This avoids running intermediate nodes without proper data passing.
         node_type = node.get('type')
         if node_type in ['basicAgent', 'contextAgent', 'chainOfAgents', 'multiCallSystem', 'softwareBuilder']:
             logger.info(f"[{run_id}] Adding node {node.get('id')} ({node_type}) to execution queue.")
             try:
                 result = await execute_node(node, run_id)
                 results.append({"id": node.get('id'), "type": node_type, "result": result})
             except Exception as e:
                 logger.error(f"[{run_id}] Top-level error during node {node.get('id')} execution: {e}")
                 results.append({"id": node.get('id'), "type": node_type, "result": f"Failed: {e}"})
         else:
             logger.info(f"[{run_id}] Skipping node {node.get('id')} ({node_type}) in simple execution mode.")


    # --- Compile Output ---
    output_log.append(f"\n--- Execution Results ({run_id}) ---")
    if not results:
         output_log.append("No executable nodes were run.")
    else:
        for result_info in results:
            if isinstance(result_info, dict):
                 node_id = result_info.get('id', 'N/A')
                 node_type = result_info.get('type', 'N/A')
                 result_content = result_info.get('result', 'No result captured.')
                 output_log.append(f"\n## Node: {node_id} ({node_type}) ##\n")
                 output_log.append(str(result_content)) # Ensure result is string
            else:
                 # Handle exceptions caught by gather if used
                 output_log.append(f"\n## Execution Error ##\n{result_info}")


    # --- Cleanup (Optional: Close model if needed, but better to keep alive for multiple runs) ---
    # global vllm_model_instance
    # if vllm_model_instance:
    #     try:
    #         # await vllm_model_instance.close_client() # Might close prematurely
    #         # vllm_model_instance = None
    #         logger.info(f"[{run_id}] VLLM Model client remains open for subsequent requests.")
    #     except Exception as e:
    #         logger.error(f"[{run_id}] Error during potential cleanup: {e}")

    end_time = time.time()
    output_log.append(f"\n--- Flow Execution End ({run_id}) ---")
    output_log.append(f"Total execution time: {end_time - start_time:.2f} seconds")
    logger.info(f"--- Flow Execution Finished ({run_id}) ---")

    return "\n".join(output_log)


# --- Software Builder Logic (Adapted) ---

async def run_software_builder(user_request: str, run_id: str) -> str:
    """Orchestrates the software building process and returns logs."""
    log_lines = [f"[{run_id}] Starting software build for request: '{user_request}'"]
    logger.info(log_lines[-1])
    start_time_build = time.time()

    # Ensure output directories exist
    os.makedirs(SOFTWARE_BUILDER_OUTPUT_DIR, exist_ok=True)
    os.makedirs(SOFTWARE_BUILDER_ARTIFACTS_DIR, exist_ok=True)

    model = await get_model()
    orchestration_agent = BasicAgent(agent_id=f"orchestrator_{run_id}", model=model)

    # === STEP 1: Planner Agent ===
    log_lines.append(f"\n[{run_id}] --- Step 1: Planning ---")
    logger.info(log_lines[-1])
    plan = None
    planner_prompt = f"""
You are an expert software architect and planner. Create a comprehensive plan for: "{user_request}"
Instructions: Define file structure, UI/UX, assets, content, frameworks (use basic HTML/CSS/JS if none specified), caveats. Output *only* the detailed plan in markdown.
""" # Simplified prompt for brevity
    try:
        log_lines.append(f"[{run_id}] Calling Planner Agent...")
        logger.info(log_lines[-1])
        raw_plan_response = await orchestration_agent.run(planner_prompt, max_tokens=4000, temperature=DEFAULT_TEMPERATURE) # Increased tokens for plan
        plan = strip_think_tags(raw_plan_response)
        if not plan or plan.startswith("ERROR:") :
             raise ValueError(f"Planner Agent failed: {plan}")
        log_lines.append(f"[{run_id}] Planner Agent finished. Plan (first 300 chars): {plan[:300]}...")
        logger.info(log_lines[-1])
        save_artifact("plan.md", f"User Request:\n{user_request}\n\n---\n\nGenerated Plan:\n{plan}", base_dir=SOFTWARE_BUILDER_ARTIFACTS_DIR)
        log_lines.append(f"[{run_id}] Plan saved to {SOFTWARE_BUILDER_ARTIFACTS_DIR}/plan.md")

    except Exception as e:
        error_msg = f"[{run_id}] Error during Planning step: {e}"
        logger.error(error_msg)
        log_lines.append(error_msg)
        # No model closing here, let the main loop handle it or keep it open
        return "\n".join(log_lines)

    # === STEP 2: Task Distribution Agent ===
    log_lines.append(f"\n[{run_id}] --- Step 2: Task Distribution ---")
    logger.info(log_lines[-1])
    memory = None
    file_prompts = []
    distributor_prompt = f"""
You are a task distribution agent. Input is a plan. Output a shared <memory> block and individual <prompt filename="..."> blocks for each file. Be extremely detailed in prompts.
Development Plan:
--- START PLAN ---
{plan}
--- END PLAN ---
Instructions: Extract shared context to <memory>. Create detailed <prompt filename="..."> for each code file (HTML, CSS, JS). Instruct the receiving agent to output ONLY raw code in ``` blocks. Reference memory. Use relative paths. Ensure filenames match the plan.
Example Output Structure:
<memory>...</memory>
<prompt filename="index.html" url="index.html">...</prompt>
<prompt filename="css/style.css" url="css/style.css">...</prompt>
""" # Simplified prompt
    try:
        log_lines.append(f"[{run_id}] Calling Task Distributor Agent...")
        logger.info(log_lines[-1])
        raw_dist_response = await orchestration_agent.run(distributor_prompt, max_tokens=6000, temperature=DEFAULT_TEMPERATURE) # Increased tokens
        dist_output = strip_think_tags(raw_dist_response)
        if not dist_output or dist_output.startswith("ERROR:") :
             raise ValueError(f"Task Distributor Agent failed: {dist_output}")

        log_lines.append(f"[{run_id}] Task Distributor Agent finished. Parsing output...")
        logger.info(log_lines[-1])
        memory, file_prompts = parse_task_distribution(dist_output)

        if not memory or not file_prompts:
            save_artifact("task_distribution_raw_output.txt", f"Raw Response:\n{raw_dist_response}", base_dir=SOFTWARE_BUILDER_ARTIFACTS_DIR)
            raise ValueError("Failed to parse memory or file prompts from Task Distributor output. Check format and saved raw output.")

        log_lines.append(f"[{run_id}] Successfully parsed memory and {len(file_prompts)} file prompts.")
        logger.info(log_lines[-1])
        parsed_prompts_log = f"<memory>\n{memory}\n</memory>\n\n" + "\n\n".join([f"<prompt filename=\"{p['filename']}\">\n{p['prompt']}\n</prompt>" for p in file_prompts])
        save_artifact("task_distribution_parsed.txt", parsed_prompts_log, base_dir=SOFTWARE_BUILDER_ARTIFACTS_DIR)
        log_lines.append(f"[{run_id}] Parsed tasks saved to {SOFTWARE_BUILDER_ARTIFACTS_DIR}/task_distribution_parsed.txt")


    except Exception as e:
        error_msg = f"[{run_id}] Error during Task Distribution step: {e}"
        logger.error(error_msg)
        log_lines.append(error_msg)
        return "\n".join(log_lines)

    # === STEP 3: File Generation Agents (Parallel Execution) ===
    log_lines.append(f"\n[{run_id}] --- Step 3: Generating Files ({len(file_prompts)} tasks) ---")
    logger.info(log_lines[-1])
    if not file_prompts:
        log_lines.append(f"[{run_id}] No file prompts were generated. Skipping file generation step.")
        logger.warning(log_lines[-1])

    else:
        generation_agent = BasicAgent(agent_id=f"generator_{run_id}", model=model)
        tasks = []
        file_mapping = {}

        for i, task_info in enumerate(file_prompts):
            filename = task_info["filename"]
            specific_prompt = task_info["prompt"]
            generation_prompt = f"""
<memory>
{memory}
</memory>
<prompt filename="{filename}">
{specific_prompt}
</prompt>
Based *only* on the specific prompt for `{filename}` and shared `<memory>`, generate the complete, raw code content for the file `{filename}`.
Output *only* the raw code content for the file, enclosed in the appropriate markdown code block (e.g., ```html ... ```).
Do not include any other text, explanations, or summaries outside the code block. Add Tailwind via CDN if requested: <script src="https://cdn.jsdelivr.net/npm/@tailwindcss/browser@4"></script>
"""
            # Use large token limit for file generation
            task = generation_agent.run(generation_prompt, max_tokens=DEFAULT_MAX_TOKENS - 1000, temperature=DEFAULT_TEMPERATURE) # Leave buffer
            tasks.append(task)
            file_mapping[i] = filename

        log_lines.append(f"[{run_id}] Launching file generation tasks...")
        logger.info(log_lines[-1])
        start_time_gen = time.time()
        results = await asyncio.gather(*tasks, return_exceptions=True)
        end_time_gen = time.time()
        log_lines.append(f"[{run_id}] File generation tasks completed in {end_time_gen - start_time_gen:.2f} seconds.")
        logger.info(log_lines[-1])

        # Process results
        files_saved = 0
        files_failed = 0
        for i, result in enumerate(results):
            filename = file_mapping[i]
            if isinstance(result, Exception):
                error_msg = f"Task for {filename} failed with exception: {result}"
                logger.error(f"[{run_id}] {error_msg}")
                log_lines.append(f"[{run_id}] ERROR: {error_msg}")
                files_failed += 1
                save_artifact(f"{filename}.error.txt", f"Task failed:\n{result}", base_dir=SOFTWARE_BUILDER_OUTPUT_DIR)
            elif isinstance(result, str) and result.startswith("ERROR:"):
                error_msg = f"Task for {filename} returned an error: {result}"
                logger.error(f"[{run_id}] {error_msg}")
                log_lines.append(f"[{run_id}] ERROR: {error_msg}")
                files_failed += 1
                save_artifact(f"{filename}.error.txt", f"Task returned error:\n{result}", base_dir=SOFTWARE_BUILDER_OUTPUT_DIR)
            elif isinstance(result, str):
                generation_output = strip_think_tags(result)
                code_content = extract_code(generation_output)
                if code_content:
                    if save_artifact(filename, code_content, base_dir=SOFTWARE_BUILDER_OUTPUT_DIR):
                        log_lines.append(f"[{run_id}] Saved: {filename}")
                        files_saved += 1
                    else:
                        log_lines.append(f"[{run_id}] FAILED SAVE: {filename}")
                        files_failed += 1
                else:
                    error_msg = f"Failed to extract code block for {filename}. Saving raw output."
                    logger.error(f"[{run_id}] {error_msg}")
                    log_lines.append(f"[{run_id}] WARNING: {error_msg}")
                    files_failed += 1
                    save_artifact(f"{filename}.raw_output.txt", generation_output, base_dir=SOFTWARE_BUILDER_OUTPUT_DIR)
            else:
                 error_msg = f"Task for {filename} returned unexpected result type: {type(result)}"
                 logger.error(f"[{run_id}] {error_msg}")
                 log_lines.append(f"[{run_id}] ERROR: {error_msg}")
                 files_failed += 1
                 save_artifact(f"{filename}.error.txt", f"Unexpected result:\n{result}", base_dir=SOFTWARE_BUILDER_OUTPUT_DIR)


        log_lines.append(f"[{run_id}] File generation finished. Saved: {files_saved}, Failed/Skipped: {files_failed}")
        logger.info(log_lines[-1])

    # === STEP 4: Cleanup === (Keep model open)
    log_lines.append(f"\n[{run_id}] --- Step 4: Build Complete ---")
    logger.info(log_lines[-1])
    end_time_build = time.time()
    log_lines.append(f"[{run_id}] Software build process completed in {end_time_build - start_time_build:.2f} seconds.")
    log_lines.append(f"[{run_id}] Generated files located in: '{os.path.abspath(SOFTWARE_BUILDER_OUTPUT_DIR)}'")
    log_lines.append(f"[{run_id}] Build artifacts (plan, etc.) located in: '{os.path.abspath(SOFTWARE_BUILDER_ARTIFACTS_DIR)}'")
    logger.info(f"--- Software Build Finished ({run_id}) ---")

    return "\n".join(log_lines)