# systems.py
import asyncio
import logging
import os
import math
import re # Added
import time # Added
from tframex.model import BaseModel
from tframex.agents import BasicAgent # Using BasicAgent for summarization/final answer
# --- MODIFICATION: Added more specific types ---
from typing import List, Dict, Any, Tuple, Optional
# --- END MODIFICATION ---


logger = logging.getLogger(__name__)

# --- Text Chunking Helper (Existing) ---
def chunk_text(text: str, chunk_size: int, chunk_overlap: int = 50) -> List[str]:
    """Splits text into overlapping chunks."""
    if chunk_overlap >= chunk_size:
        raise ValueError("Overlap must be smaller than chunk size")
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start += chunk_size - chunk_overlap
        if end >= len(text):
             break
    if len(chunks) > 1 and chunks[-1] == chunks[-2][chunk_overlap:]:
         pass
    final_chunks = [c for c in chunks if c]
    logger.info(f"Chunked text into {len(final_chunks)} chunks (size={chunk_size}, overlap={chunk_overlap})")
    return final_chunks

# --- ChainOfAgents (Existing - No Changes Needed) ---
class ChainOfAgents:
    """
    A system that processes long text by summarizing chunks sequentially.
    """
    def __init__(self, system_id: str, model: BaseModel, chunk_size: int = 1000, chunk_overlap: int = 100):
        self.system_id = system_id
        self.model = model
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.processing_agent = BasicAgent(agent_id=f"{system_id}_processor", model=model)
        logger.info(f"System '{self.system_id}' initialized (Chain of Agents).")

    async def run(self, initial_prompt: str, long_text: str, **kwargs) -> str:
        """Processes the long text based on the initial prompt using a chain of summaries."""
        logger.info(f"System '{self.system_id}' starting run for prompt: '{initial_prompt[:50]}...'")
        chunks = chunk_text(long_text, self.chunk_size, self.chunk_overlap)
        if not chunks:
            logger.warning(f"System '{self.system_id}': No text chunks generated from input.")
            return "Error: Input text was empty or too short to chunk."

        current_summary = ""
        num_chunks = len(chunks)

        for i, chunk in enumerate(chunks):
            chunk_prompt = (
                f"Overall Goal: {initial_prompt}\n\n"
                f"Previous Summary (if any):\n{current_summary}\n\n"
                f"---\n\n"
                f"Current Text Chunk ({i+1}/{num_chunks}):\n{chunk}\n\n"
                f"---\n\n"
                f"Task: Summarize the 'Current Text Chunk' focusing on information relevant to the 'Overall Goal'. "
                f"Integrate relevant details from the 'Previous Summary' if applicable, but keep the summary concise. "
                f"Output *only* the refined summary."
            )
            logger.info(f"System '{self.system_id}': Processing chunk {i+1}/{num_chunks}...")
            current_summary = await self.processing_agent.run(chunk_prompt, **kwargs)
            logger.debug(f"System '{self.system_id}': Intermediate summary after chunk {i+1}: '{current_summary[:100]}...'")

        final_prompt = (
            f"Context (summary derived from the full text):\n{current_summary}\n\n"
            f"---\n\n"
            f"Prompt:\n{initial_prompt}\n\n"
            f"---\n\n"
            f"Task: Using the provided context (summary), answer the prompt accurately and completely."
        )
        logger.info(f"System '{self.system_id}': Generating final answer...")
        final_answer = await self.processing_agent.run(final_prompt, **kwargs)

        logger.info(f"System '{self.system_id}' finished run.")
        return final_answer

# --- MultiCallSystem (Existing - No Changes Needed) ---
class MultiCallSystem:
    """
    A system that makes multiple simultaneous calls to the LLM with the same prompt.
    """
    def __init__(self, system_id: str, model: BaseModel):
        self.system_id = system_id
        self.model = model
        logger.info(f"System '{self.system_id}' initialized (Multi Call).")

    async def _call_and_save_task(self, prompt: str, output_filename: str, **kwargs) -> str:
        """Internal task to call LLM stream (using chat format) and save to a file."""
        full_response = ""
        messages: List[Dict[str, str]] = [{"role": "user", "content": prompt}]
        try:
            with open(output_filename, 'w', encoding='utf-8') as f:
                async for chunk in self.model.call_stream(messages, **kwargs):
                    f.write(chunk)
                    full_response += chunk
                    f.flush()
            logger.info(f"System '{self.system_id}': Saved response to {output_filename}")
            return output_filename
        except Exception as e:
            logger.error(f"System '{self.system_id}': Error saving to {output_filename}: {e}")
            try:
                 with open(output_filename, 'w', encoding='utf-8') as f:
                      f.write(f"ERROR processing/saving response: {e}\n\nPartial response if any:\n{full_response}")
            except Exception:
                 pass
            return f"ERROR: Failed to write to {output_filename}"

    async def run(self, prompt: str, num_calls: int, output_dir: str = "multi_call_outputs", base_filename: str = "output", **kwargs) -> Dict[str, str]:
        """Makes `num_calls` simultaneous requests to the model with the given prompt."""
        logger.info(f"System '{self.system_id}' starting run for {num_calls} simultaneous calls.")
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            logger.info(f"Created output directory: {output_dir}")

        tasks = []
        output_files = {}

        for i in range(1, num_calls + 1):
            output_filename = os.path.join(output_dir, f"{base_filename}_{i}.txt")
            task_id = f"call_{i}"
            task = self._call_and_save_task(prompt, output_filename, **kwargs)
            tasks.append(task)
            output_files[task_id] = output_filename

        logger.info(f"System '{self.system_id}': Launching {num_calls} concurrent tasks...")
        results = await asyncio.gather(*tasks, return_exceptions=True)

        final_results = {}
        success_count = 0
        error_count = 0
        for i, result in enumerate(results):
            task_id = f"call_{i+1}"
            original_filename = output_files[task_id]
            if isinstance(result, Exception):
                logger.error(f"System '{self.system_id}': Task {task_id} raised an exception: {result}")
                final_results[task_id] = f"ERROR: Task Exception - {result}"
                error_count += 1
                try:
                    with open(original_filename, 'w', encoding='utf-8') as f:
                         f.write(f"ERROR: Task Exception - {result}")
                except Exception:
                    pass
            elif isinstance(result, str) and result.startswith("ERROR:"):
                 logger.error(f"System '{self.system_id}': Task {task_id} failed: {result}")
                 final_results[task_id] = result
                 error_count += 1
            else:
                 final_results[task_id] = result
                 success_count +=1

        logger.info(f"System '{self.system_id}' finished run. Success: {success_count}, Errors: {error_count}")
        return final_results

# --- NEW: FrontendAgentSystem Class ---
class FrontendAgentSystem:
    """
    A system that orchestrates the generation of a multi-page frontend website
    based on a user request, using planning, task distribution, and parallel
    file generation agents.
    """
    def __init__(self,
                 system_id: str,
                 model: BaseModel,
                 artifacts_dir: str = "build_artifacts",
                 website_output_dir: str = "generated_website",
                 max_tokens_plan: int = 4096,
                 max_tokens_file_gen: int = 34000,
                 temperature: float = 0.5):
        """
        Initializes the FrontendAgentSystem.

        Args:
            system_id (str): Identifier for this system instance.
            model (BaseModel): The language model instance to use.
            artifacts_dir (str): Directory to save intermediate build artifacts (plan, etc.).
            website_output_dir (str): Directory to save the final generated website files.
            max_tokens_plan (int): Max tokens for planning/distribution LLM calls.
            max_tokens_file_gen (int): Max tokens for file generation LLM calls.
            temperature (float): Default temperature for LLM calls.
        """
        self.system_id = system_id
        self.model = model
        self.artifacts_dir = artifacts_dir
        self.website_output_dir = website_output_dir
        self.max_tokens_plan = max_tokens_plan
        self.max_tokens_file_gen = max_tokens_file_gen
        self.temperature = temperature
        self._logger = logging.getLogger(f"FrontendAgentSystem.{system_id}") # Specific logger instance

        # Ensure output directories exist
        os.makedirs(self.artifacts_dir, exist_ok=True)
        os.makedirs(self.website_output_dir, exist_ok=True)
        self._logger.info(f"Initialized. Artifacts Dir: '{self.artifacts_dir}', Website Output Dir: '{self.website_output_dir}'")

    # --- Helper Methods as Private Class Methods ---

    def _save_file(self, filename: str, content: str, is_artifact: bool = False) -> bool:
        """Saves content to a file in the appropriate directory (artifact or website)."""
        base_dir = self.artifacts_dir if is_artifact else self.website_output_dir
        # Basic security check
        if os.path.isabs(filename) or ".." in filename:
            self._logger.error(f"Invalid filepath detected (absolute or traversal): {filename}")
            return False

        full_path = os.path.join(base_dir, filename)
        try:
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(content)
            self._logger.info(f"Successfully saved file: {full_path}")
            return True
        except OSError as e:
            self._logger.error(f"Failed to save file {full_path}: {e}")
            return False
        except Exception as e:
            self._logger.error(f"An unexpected error occurred saving file {full_path}: {e}")
            return False

    def _extract_code(self, llm_output: str) -> Optional[str]:
        """Extracts the first code block (```...```) from LLM output."""
        match = re.search(r"```(?:[a-zA-Z0-9]*\n)?(.*?)```", llm_output, re.DOTALL | re.IGNORECASE)
        if match:
            code = match.group(1).strip()
            if code:
                self._logger.debug(f"Extracted code block (length: {len(code)}).")
                return code
            else:
                self._logger.warning("Found code block delimiters but content inside was empty.")
                return None
        else:
            self._logger.warning("No markdown code block found in the LLM output.")
            if llm_output.strip().startswith('<') or llm_output.strip().startswith(('function', 'const', 'let', 'var', 'import', 'public class', '@', '.', '#')):
                 self._logger.warning("No code block found, but output resembles code. Returning full output.")
                 return llm_output.strip()
            return None

    def _parse_task_distribution(self, dist_output: str) -> Tuple[Optional[str], List[Dict[str, str]]]:
        """Parses the Task Distributor output to extract memory and file prompts."""
        memory = None
        prompts = []
        memory_match = re.search(r"<memory>(.*?)</memory>", dist_output, re.DOTALL | re.IGNORECASE)
        if memory_match:
            memory = memory_match.group(1).strip()
            self._logger.info("Extracted memory block.")
        else:
            self._logger.warning("Could not find <memory> block in Task Distributor output.")

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
                prompts.append({
                    "filename": filename,
                    "url": url if url else filename,
                    "prompt": prompt_content
                })
                self._logger.debug(f"Extracted prompt for file: {filename}")
            else:
                self._logger.warning(f"Found prompt block but filename or content was empty: {match.group(0)}")

        if not prompts:
             self._logger.warning("Could not find any valid <prompt ...> blocks in Task Distributor output.")
        return memory, prompts

    def _strip_think_tags(self, text: str) -> str:
        """Removes content up to and including the first </think> tag if present."""
        think_end_tag = "</think>"
        tag_pos = text.find(think_end_tag)
        if tag_pos != -1:
            self._logger.debug("Found </think> tag, stripping preceding content.")
            return text[tag_pos + len(think_end_tag):].strip()
        else:
            return text

    # --- Main Run Method ---
    async def run(self, user_request: str):
        """
        Orchestrates the frontend generation process for the given user request.
        """
        start_time_build = time.time()
        self._logger.info(f"--- Starting Frontend Build Process for Request: '{user_request}' ---")

        # Create agent instances needed for this run
        # Using separate IDs for clarity within this system run
        orchestration_agent = BasicAgent(agent_id=f"{self.system_id}_orchestrator", model=self.model)
        generation_agent = BasicAgent(agent_id=f"{self.system_id}_generator", model=self.model)

        # === STEP 1: Planner Agent ===
        self._logger.info("--- Step 1: Planning ---")
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
            self._logger.info("Calling Planner Agent...")
            raw_plan_response = await orchestration_agent.run(planner_prompt, max_tokens=self.max_tokens_plan, temperature=self.temperature)
            plan = self._strip_think_tags(raw_plan_response) # Strip think tags
            if not plan or plan.startswith("ERROR:") :
                 self._logger.error(f"Planner Agent failed or returned an error: {plan}")
                 raise ValueError("Planner Agent failed.")
            self._logger.info("Planner Agent finished. Plan received (first 500 chars):\n" + plan[:500] + "...")
            # Save the plan artifact
            self._save_file("plan.md", f"User Request:\n{user_request}\n\n---\n\nGenerated Plan:\n{plan}", is_artifact=True)

        except Exception as e:
            self._logger.error(f"Error during Planning step: {e}")
            # Note: We don't close the client here, caller is responsible
            return # Stop the process

        # === STEP 2: Task Distribution Agent ===
        self._logger.info("--- Step 2: Task Distribution ---")
        memory = None
        file_prompts = []
        distributor_prompt = f"""
You are a task distribution agent. Your input is a software development plan. Your goal is to break down this plan into:
1.  A shared `<memory>` block containing essential context, design guidelines, framework choices, and overall architecture described in the plan that *all* subsequent file-generation agents need to know to ensure consistency.
2.  Individual `<prompt>` blocks, one for *each file* identified in the plan's file structure. Each prompt block must specify the target `filename` and contain a highly detailed and specific prompt instructing another agent on *exactly* what code to generate for that single file, referencing the shared memory/plan as needed.

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
"""
        try:
            self._logger.info("Calling Task Distributor Agent...")
            raw_dist_response = await orchestration_agent.run(distributor_prompt, max_tokens=self.max_tokens_plan, temperature=self.temperature)
            dist_output = self._strip_think_tags(raw_dist_response) # Strip think tags
            if not dist_output or dist_output.startswith("ERROR:") :
                 self._logger.error(f"Task Distributor Agent failed or returned an error: {dist_output}")
                 raise ValueError("Task Distributor Agent failed.")

            self._logger.info("Task Distributor Agent finished. Parsing output...")
            memory, file_prompts = self._parse_task_distribution(dist_output)

            if not memory or not file_prompts:
                self._logger.error("Failed to parse memory or file prompts from Task Distributor output. Check the output format.")
                self._save_file("task_distribution_raw_output.txt", f"Distributor Prompt:\n{distributor_prompt}\n\n---\n\nRaw Response:\n{raw_dist_response}", is_artifact=True)
                raise ValueError("Failed to parse Task Distributor output.")

            self._logger.info(f"Successfully parsed memory and {len(file_prompts)} file prompts.")
            # Save parsed data artifact
            parsed_prompts_log = f"<memory>\n{memory}\n</memory>\n\n" + "\n\n".join([f"<prompt filename=\"{p['filename']}\">\n{p['prompt']}\n</prompt>" for p in file_prompts])
            self._save_file("task_distribution_parsed.txt", parsed_prompts_log, is_artifact=True)

        except Exception as e:
            self._logger.error(f"Error during Task Distribution step: {e}")
            return # Stop the process

        # === STEP 3: File Generation Agents (Parallel Execution) ===
        self._logger.info("--- Step 3: Generating Files in Parallel ---")
        if not file_prompts:
            self._logger.warning("No file prompts were generated. Skipping file generation step.")
        else:
            tasks = []
            file_mapping = {}

            self._logger.info(f"Preparing {len(file_prompts)} file generation tasks...")
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

Based *only* on the specific prompt for `{filename}` above and the shared `<memory>` context, generate the complete, raw code content for the file `{filename}`.
Output *only* the raw code content for the file, enclosed in the appropriate markdown code block (e.g., ```html ... ```, ```css ... ```, ```javascript ... ```).
Do not include any other text, explanations, introductions, or summaries outside the code block.
"""
                task = generation_agent.run(generation_prompt, max_tokens=self.max_tokens_file_gen, temperature=self.temperature)
                tasks.append(task)
                file_mapping[i] = filename
                self._logger.debug(f"Created generation task for: {filename}")

            self._logger.info(f"Launching {len(tasks)} file generation tasks concurrently...")
            start_time_gen = time.time()
            results = await asyncio.gather(*tasks, return_exceptions=True)
            end_time_gen = time.time()
            self._logger.info(f"File generation tasks completed in {end_time_gen - start_time_gen:.2f} seconds.")

            self._logger.info("Processing generation results and saving files...")
            files_saved = 0
            files_failed = 0
            for i, result in enumerate(results):
                filename = file_mapping[i]
                self._logger.debug(f"Processing result for: {filename}")

                if isinstance(result, Exception):
                    self._logger.error(f"Task for {filename} failed with exception: {result}")
                    files_failed += 1
                    self._save_file(f"{filename}.error.txt", f"Task failed with exception:\n{result}", is_artifact=False) # Save error in website dir
                elif isinstance(result, str) and result.startswith("ERROR:"):
                     self._logger.error(f"Task for {filename} returned an error: {result}")
                     files_failed += 1
                     self._save_file(f"{filename}.error.txt", f"Task returned error:\n{result}", is_artifact=False)
                elif isinstance(result, str):
                    generation_output = self._strip_think_tags(result) # Strip think tags
                    code_content = self._extract_code(generation_output)
                    if code_content:
                        if self._save_file(filename, code_content, is_artifact=False): # Save to website dir
                            files_saved += 1
                        else:
                            files_failed += 1
                    else:
                        self._logger.error(f"Failed to extract code block for {filename}. Saving raw output.")
                        files_failed += 1
                        self._save_file(f"{filename}.raw_output.txt", generation_output, is_artifact=False) # Save raw output to website dir
                else:
                     self._logger.error(f"Task for {filename} returned unexpected result type: {type(result)}")
                     files_failed += 1
                     self._save_file(f"{filename}.error.txt", f"Task returned unexpected result type: {type(result)}\n{result}", is_artifact=False)

            self._logger.info(f"File generation finished. Saved: {files_saved}, Failed/Skipped: {files_failed}")

        end_time_build = time.time()
        self._logger.info(f"--- Frontend build process finished in {end_time_build - start_time_build:.2f} seconds ---")
        self._logger.info(f"Generated website files should be in '{self.website_output_dir}'")
        self._logger.info(f"Build artifacts (plan, etc.) are in '{self.artifacts_dir}'")