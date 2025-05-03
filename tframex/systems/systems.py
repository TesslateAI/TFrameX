# systems.py
import asyncio
import logging
import os
import math
from tframex.model.model_logic import BaseModel # NEW
from tframex.agents.agents import BasicAgent # NEW
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

# --- Text Chunking Helper ---
# (No changes needed in chunk_text)
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
        if end >= len(text): # Ensure we don't miss the very end
             break # Last chunk captured
    if len(chunks) > 1 and chunks[-1] == chunks[-2][chunk_overlap:]:
         pass
    final_chunks = [c for c in chunks if c]
    logger.info(f"Chunked text into {len(final_chunks)} chunks (size={chunk_size}, overlap={chunk_overlap})")
    return final_chunks

# --- System Definitions ---

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

    # No changes needed in ChainOfAgents.run as it uses BasicAgent.run,
    # which relies on the modified _stream_and_aggregate
    async def run(self, initial_prompt: str, long_text: str, **kwargs) -> str:
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
        # --- MODIFICATION: Convert prompt string to messages list ---
        messages: List[Dict[str, str]] = [{"role": "user", "content": prompt}]
        try:
            with open(output_filename, 'w', encoding='utf-8') as f:
                 # --- MODIFICATION: Pass messages list to model ---
                async for chunk in self.model.call_stream(messages, **kwargs):
                    f.write(chunk)
                    full_response += chunk
                    f.flush() # Ensure data is written progressively
            # --- END MODIFICATION ---
            logger.info(f"System '{self.system_id}': Saved response to {output_filename}")
            return output_filename # Return filename on success
        except Exception as e:
            logger.error(f"System '{self.system_id}': Error saving to {output_filename}: {e}")
            try:
                 with open(output_filename, 'w', encoding='utf-8') as f:
                      f.write(f"ERROR processing/saving response: {e}\n\nPartial response if any:\n{full_response}")
            except Exception:
                 pass
            return f"ERROR: Failed to write to {output_filename}"

    # No changes needed in MultiCallSystem.run signature,
    # as the internal _call_and_save_task handles the format conversion
    async def run(self, prompt: str, num_calls: int, output_dir: str = "multi_call_outputs", base_filename: str = "output", **kwargs) -> Dict[str, str]:
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