import asyncio
import logging
import re
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from ..agents.base import BaseAgent # Keep for type hinting if summary_agent is BaseAgent instance
from ..flows.flow_context import FlowContext
from ..models.primitives import Message
from ..util.engine import Engine
from .base_pattern import BasePattern # Adjusted for direct import from base_pattern

logger = logging.getLogger(__name__)


class ProcessingMode(Enum):
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"


class DelegatePattern(BasePattern):
    """
    A pattern where a delegator agent creates tasks, and delegatees process them.
    Tasks are extracted from the delegator's output using a user provided regex.
    Delegatees can be a single agent name (str) or a nested BasePattern instance.
    Tasks are processed sequentially or in parallel.
    Sequential processing can optionally maintain a chain of summaries if a summary_agent is provided.

    If no task_extraction_regex is provided, the delegator should format its response as a list
    of tasks, each wrapped in <task>...</task> tags.
    A shared_memory_extraction_regex can also be provided to extract a common context for all tasks.
    """

    def __init__(
        self,
        pattern_name: str,
        delegator_agent: str, # Name of the agent that generates tasks
        delegatee_agent: Union[str, BasePattern], # Name of agent or a pattern instance to process tasks
        processing_mode: ProcessingMode = ProcessingMode.SEQUENTIAL,
        summary_agent: Optional[str] = None, # Name of agent for summarizing in CoA mode
        chain_of_agents: bool = False, # Enable Chain of Agents style processing
        task_extraction_regex: str = r"<task>(.*?)</task>", # Regex to find individual tasks
        shared_memory_extraction_regex: Optional[str] = None, # Regex to find shared context
    ):
        super().__init__(pattern_name=pattern_name)

        if not isinstance(delegator_agent, str):
            raise TypeError("delegator_agent must be an agent name (str).")
        if not isinstance(delegatee_agent, (str, BasePattern)):
            raise TypeError("delegatee_agent must be an agent name (str) or a BasePattern instance.")

        if processing_mode == ProcessingMode.PARALLEL and chain_of_agents:
            raise ValueError(
                "chain_of_agents is not supported in PARALLEL processing mode."
            )

        if chain_of_agents and not summary_agent:
            raise ValueError("summary_agent (name) is required when chain_of_agents is True.")
        if summary_agent and not isinstance(summary_agent, str):
            raise TypeError("summary_agent must be an agent name (str).")


        self.delegator_agent = delegator_agent
        self.delegatee_agent = delegatee_agent
        self.processing_mode = processing_mode
        self.summary_agent = summary_agent
        self.chain_of_agents = chain_of_agents
        self.task_extraction_regex = task_extraction_regex
        self.shared_memory_extraction_regex = shared_memory_extraction_regex

    def _extract_content(self, text: str, regex: str) -> List[str]:
        if not isinstance(text, str):
            logger.warning(
                f"Input for regex extraction is not a string. Type: {type(text)}, Content: {text}"
            )
            return []
        # re.DOTALL allows '.' to match newline characters
        matches = re.findall(regex, text, re.DOTALL)
        return [match.strip() for match in matches]

    async def execute(
        self,
        flow_ctx: FlowContext,
        engine: Engine,
        agent_call_kwargs: Optional[Dict[str, Any]] = None,
    ) -> FlowContext:
        logger.info(
            f"Executing DelegatePattern '{self.pattern_name}'. Input: {str(flow_ctx.current_message.content)[:50]}..."
        )
        effective_agent_call_kwargs = agent_call_kwargs or {}

        # 1. Execute Delegator Agent to get tasks and potentially shared context
        try:
            delegator_output_message = await engine.call_agent(
                self.delegator_agent,
                flow_ctx.current_message, # Initial input to the pattern
                **effective_agent_call_kwargs,
            )
            flow_ctx.history.append(delegator_output_message) # Record delegator's output
        except Exception as e:
            logger.error(
                f"Error in DelegatePattern '{self.pattern_name}' calling delegator agent '{self.delegator_agent}': {e}",
                exc_info=True,
            )
            error_msg = Message(
                role="assistant",
                content=f"Error executing delegator agent '{self.delegator_agent}' in pattern '{self.pattern_name}': {e}",
            )
            flow_ctx.update_current_message(error_msg)
            return flow_ctx

        if not delegator_output_message.content or not isinstance(delegator_output_message.content, str):
            logger.warning(
                f"Delegator output content is empty or not a string for pattern '{self.pattern_name}'. Output: {delegator_output_message.content}"
            )
            error_msg = Message(
                role="assistant",
                content=f"Delegator agent '{self.delegator_agent}' in pattern '{self.pattern_name}' did not return usable string output for task extraction.",
            )
            flow_ctx.update_current_message(error_msg)
            return flow_ctx

        # 2. Extract Shared Memory (if regex provided)
        shared_context_str = ""
        if self.shared_memory_extraction_regex:
            shared_matches = self._extract_content(delegator_output_message.content, self.shared_memory_extraction_regex)
            if shared_matches:
                shared_context_str = "\n".join(shared_matches).strip() # Concatenate if multiple matches
                logger.info(
                    f"DelegatePattern '{self.pattern_name}': Extracted shared context: {shared_context_str[:100]}..."
                )
                # Store shared context in flow_ctx.shared_data for potential use by delegatees or later steps
                flow_ctx.shared_data[f"{self.pattern_name}_shared_context"] = shared_context_str


        # 3. Extract Tasks
        tasks_input_strings = self._extract_content(delegator_output_message.content, self.task_extraction_regex)
        if not tasks_input_strings:
            logger.info(
                f"DelegatePattern '{self.pattern_name}': No tasks extracted from delegator output. Delegator output was: {delegator_output_message.content[:200]}"
            )
            no_tasks_msg = Message(
                role="assistant",
                content=f"No tasks were extracted by pattern '{self.pattern_name}'. Delegator output: {delegator_output_message.content}",
            )
            flow_ctx.update_current_message(no_tasks_msg)
            return flow_ctx

        logger.info(
            f"DelegatePattern '{self.pattern_name}': Extracted {len(tasks_input_strings)} tasks."
        )

        task_results_contents: List[str] = []
        # original_message_role = flow_ctx.current_message.role # Role for task messages

        # 4. Process Tasks
        if self.processing_mode == ProcessingMode.SEQUENTIAL:
            current_summary_for_coa = "No previous task summary available." # Initial summary for CoA

            for i, task_str in enumerate(tasks_input_strings):
                logger.info(
                    f"DelegatePattern '{self.pattern_name}' (Sequential) - Task {i + 1}/{len(tasks_input_strings)}: Processing task."
                )
                
                # Construct input for the delegatee
                delegatee_input_content = task_str
                if shared_context_str:
                    delegatee_input_content = f"Shared Context:\n{shared_context_str}\n\nTask:\n{task_str}"
                
                if self.chain_of_agents:
                    # Prepend summary of previous task (and shared context if applicable)
                    if shared_context_str:
                         delegatee_input_content = f"Shared Context:\n{shared_context_str}\n\nSummary of previous work:\n{current_summary_for_coa}\n\nCurrent Task:\n{task_str}"
                    else:
                         delegatee_input_content = f"Summary of previous work:\n{current_summary_for_coa}\n\nCurrent Task:\n{task_str}"

                task_input_message = Message(role="user", content=delegatee_input_content)
                
                # Create a new FlowContext for this specific task if delegatee is a pattern,
                # to isolate its history and allow it to manage its own current_message.
                # However, we need to pass the correct shared_data.
                task_specific_flow_ctx = FlowContext(
                    initial_input=task_input_message,
                    shared_data=flow_ctx.shared_data.copy() # Pass a copy of the main flow's shared_data
                )

                try:
                    if isinstance(self.delegatee_agent, str): # Delegatee is an agent name
                        delegatee_output_message = await engine.call_agent(
                            self.delegatee_agent,
                            task_input_message, # Pass the constructed message
                            **effective_agent_call_kwargs,
                        )
                        task_result_content = str(delegatee_output_message.content)
                        task_specific_flow_ctx.update_current_message(delegatee_output_message) # For CoA summary
                    elif isinstance(self.delegatee_agent, BasePattern): # Delegatee is a nested pattern
                        # The nested pattern executes, potentially modifying task_specific_flow_ctx
                        processed_task_ctx = await self.delegatee_agent.execute(
                            task_specific_flow_ctx, # Pass the task-specific context
                            engine,
                            agent_call_kwargs=effective_agent_call_kwargs,
                        )
                        task_result_content = str(processed_task_ctx.current_message.content)
                        # Update task_specific_flow_ctx with the result from the pattern
                        task_specific_flow_ctx = processed_task_ctx 
                    else:
                        raise TypeError(f"Unsupported delegatee_agent type: {type(self.delegatee_agent)}")
                    
                    task_results_contents.append(task_result_content)
                    flow_ctx.history.extend(task_specific_flow_ctx.history[1:]) # Add task's history (skip initial) to main flow

                    if self.chain_of_agents and self.summary_agent:
                        # Summarize the output of this task for the next iteration's input
                        # The input to summary agent should be the result of the current task
                        summary_input_msg = Message(role="user", content=task_result_content)
                        summary_output_message = await engine.call_agent(
                            self.summary_agent,
                            summary_input_msg,
                            **effective_agent_call_kwargs
                        )
                        current_summary_for_coa = str(summary_output_message.content)
                        flow_ctx.history.append(summary_output_message) # Log summary agent's activity

                except Exception as e:
                    error_detail = f"Error processing task '{task_str[:50]}...' by delegatee '{str(self.delegatee_agent)}'"
                    logger.error(f"{error_detail}: {e}", exc_info=True)
                    task_results_contents.append(f"Error: {error_detail}: {e}")
                    # Update current_summary_for_coa to reflect error for CoA
                    if self.chain_of_agents:
                        current_summary_for_coa = f"Error encountered in previous task: {e}"


        elif self.processing_mode == ProcessingMode.PARALLEL:
            async def process_task_parallel(task_str_for_parallel: str, task_idx: int):
                logger.info(
                    f"DelegatePattern '{self.pattern_name}' (Parallel) - Task {task_idx + 1}/{len(tasks_input_strings)}: Processing."
                )
                parallel_delegatee_input_content = task_str_for_parallel
                if shared_context_str:
                    parallel_delegatee_input_content = f"Shared Context:\n{shared_context_str}\n\nTask:\n{task_str_for_parallel}"

                task_input_message = Message(role="user", content=parallel_delegatee_input_content)
                
                # Isolate context for parallel pattern execution
                parallel_task_flow_ctx = FlowContext(
                    initial_input=task_input_message,
                    shared_data=flow_ctx.shared_data.copy()
                )

                try:
                    if isinstance(self.delegatee_agent, str):
                        output_message = await engine.call_agent(
                            self.delegatee_agent, task_input_message, **effective_agent_call_kwargs
                        )
                        # For parallel, we usually just care about the content for aggregation
                        return str(output_message.content), parallel_task_flow_ctx.history[1:] 
                    elif isinstance(self.delegatee_agent, BasePattern):
                        processed_ctx = await self.delegatee_agent.execute(
                            parallel_task_flow_ctx, engine, agent_call_kwargs=effective_agent_call_kwargs
                        )
                        return str(processed_ctx.current_message.content), processed_ctx.history[1:]
                    else:
                        raise TypeError(f"Unsupported delegatee_agent type: {type(self.delegatee_agent)}")
                except Exception as e:
                    error_detail = f"Error processing task '{task_str_for_parallel[:50]}...' by delegatee '{str(self.delegatee_agent)}'"
                    logger.error(f"{error_detail}: {e}", exc_info=True)
                    return f"Error: {error_detail}: {e}", [] # Return error and empty history

            parallel_results_with_history = await asyncio.gather(
                *(process_task_parallel(task, i) for i, task in enumerate(tasks_input_strings))
            )
            
            for res_content, hist_messages in parallel_results_with_history:
                task_results_contents.append(res_content)
                flow_ctx.history.extend(hist_messages) # Add history from parallel tasks

        else: # Should not happen due to Enum
            logger.error(f"Invalid processing mode: {self.processing_mode}")
            # ... (handle error) ...
            pass


        # 5. Aggregate Results and finalize FlowContext
        # If CoA was used, the last current_summary_for_coa could be the final relevant output.
        # Otherwise, aggregate all task_results_contents.
        final_content_str: str
        if self.chain_of_agents and self.processing_mode == ProcessingMode.SEQUENTIAL and task_results_contents:
            # The last result in task_results_contents is the final output of the chain
            final_content_str = task_results_contents[-1]
        else:
            # General aggregation for parallel or non-CoA sequential
            final_content_str = "\n\n---\n\n".join(task_results_contents)
            final_content_str = f"Pattern '{self.pattern_name}' processed {len(tasks_input_strings)} tasks. Aggregated Results:\n{final_content_str}"
        
        final_output_message = Message(role="assistant", content=final_content_str)
        flow_ctx.update_current_message(final_output_message) # This is the final message of the DelegatePattern

        logger.info(
            f"DelegatePattern '{self.pattern_name}' completed. Output: {str(flow_ctx.current_message.content)[:100]}..."
        )
        return flow_ctx

    async def reset_agents(self, engine: Engine) -> None:
        logger.debug(f"Resetting agents for DelegatePattern '{self.pattern_name}'")
        await engine.reset_agent(self.delegator_agent)
        if isinstance(self.delegatee_agent, BasePattern):
            await self.delegatee_agent.reset_agents(engine)
        elif isinstance(self.delegatee_agent, str):
            await engine.reset_agent(self.delegatee_agent)
        
        if self.summary_agent: # summary_agent is a string (agent name)
            await engine.reset_agent(self.summary_agent)