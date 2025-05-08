# chain_of_agents.py
import logging
from tframex.model import BaseModel
from tframex.agents import BasicAgent # Using BasicAgent for summarization/final answer
from typing import List

logger = logging.getLogger(__name__)

# --- Text Chunking Helper ---
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

# --- ChainOfAgents ---
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