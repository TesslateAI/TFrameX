# multicall_system.py
import asyncio
import logging
import os
from tframex.model import BaseModel
from typing import List, Dict

logger = logging.getLogger(__name__)
# --- MultiCallSystem ---
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