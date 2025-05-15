import asyncio
import logging
import re
from curses import init_color
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from ..agents.base import BaseAgent
from ..flows.flow_context import FlowContext
from ..models.primitives import Message
from ..util.engine import Engine
from .base_pattern import BasePattern

logger = logging.getLogger(__name__)


class ProcessingMode(Enum):
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"


class DelegatePattern(BasePattern):
    """
    A pattern where a delegator agent creates tasks, and delegatees process them.
    Tasks are extracted from the delegator's output using a user provided regex.
    Delegatees are the same kind of agent but processed sequentially or in parallel.
    Sequential processing can optionally maintain a chain of summaries, as seen in chain of agents (CoA).

    If no regex is provided, delegator should format response as a list of tasks with <task> tags.
    """

    def __init__(
        self,
        pattern_name: str,
        delegator_agent: str,
        delegatee_agent: Union[str, BasePattern],
        processing_mode: ProcessingMode = ProcessingMode.SEQUENTIAL,
        summary_agent: Optional[BaseAgent] = None,
        chain_of_agents: bool = False,
        task_extraction_regex: str = r"<task>(.*?)</task>",
        shared_memory_extraction_regex: Optional[str] = None,
    ):
        super().__init__(pattern_name=pattern_name)  # type: ignore

        if processing_mode == ProcessingMode.PARALLEL and chain_of_agents:
            raise ValueError(
                "chain_of_agents is not supported in parallel processing mode."
            )

        if chain_of_agents and not summary_agent:
            raise ValueError("summary_agent is required when chain_of_agents is True.")

        self.summary_agent = summary_agent
        self.delegator_agent = delegator_agent
        self.delegatee_agent = delegatee_agent
        self.processing_mode = processing_mode
        self.chain_of_agents = chain_of_agents
        self.task_extraction_regex = task_extraction_regex
        self.shared_memory_extraction_regex = shared_memory_extraction_regex

    def extract_tasks(self, text: str) -> List[str]:
        if not isinstance(text, str):
            logger.warning(
                f"Delegator output is not a string, cannot extract tasks. Output type: {type(text)}, Output: {text}"
            )
            return []

        # re.DOTALL allows '.' to match newline characters
        tasks = re.findall(self.task_extraction_regex, text, re.DOTALL)
        return [task.strip() for task in tasks]

    async def execute(
        self,
        flow_ctx: FlowContext,
        engine: Engine,
        agent_call_kwargs: Optional[Dict[str, Any]] = None,
    ) -> FlowContext:
        """
        Executes the delegate pattern.
        1. The delegator agent generates tasks based on the initial_input.
        2. Tasks are extracted from the delegator's output.
        3. Each task is processed by the delegatee agent.
        4. Results from processing each task are collected and returned.
        """
        logger.info(
            f"Executing DelegatePattern '{self.pattern_name}'. Input: {str(flow_ctx.current_message.content)[:50]}..."
        )
        effective_agent_call_kwargs = agent_call_kwargs or {}

        # 1. Execute Delegator Agent
        try:
            delegator_output_message = await engine.call_agent(
                self.delegator_agent,
                flow_ctx.current_message,
                **effective_agent_call_kwargs,
            )

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

        if not isinstance(delegator_output_message.content, str):
            logger.warning(
                f"Delegator output content is not a string for pattern '{self.pattern_name}', cannot extract tasks. Output type: {type(delegator_output_message.content)}"
            )
            error_msg = Message(
                role="assistant",
                content=f"Delegator agent '{self.delegator_agent}' in pattern '{self.pattern_name}' did not return a string output for task extraction.",
            )
            flow_ctx.update_current_message(error_msg)
            return flow_ctx

        # 2. Extract Shared Memory (if regex provided)
        shared_memory_str = ""
        if self.shared_memory_extraction_regex:
            shared_memory_matches = re.findall(
                self.shared_memory_extraction_regex,
                delegator_output_message.content,
                re.DOTALL,
            )
            if shared_memory_matches:
                shared_memory_str = "\n".join(
                    [match.strip() for match in shared_memory_matches]
                ).strip()
                logger.info(
                    f"DelegatePattern '{self.pattern_name}': Extracted shared memory: {shared_memory_str[:100]}..."
                )

        # 3. Extract Tasks
        tasks = self.extract_tasks(delegator_output_message.content)
        if not tasks:
            logger.info(
                f"DelegatePattern '{self.pattern_name}': No tasks extracted from delegator output. Delegator output was: {delegator_output_message.content[:100]}"
            )
            # Update flow_ctx to indicate no tasks were processed.
            # Return a message indicating no tasks, or the delegator's output directly.
            no_tasks_msg = Message(
                role="assistant",
                content=f"No tasks were extracted by pattern '{self.pattern_name}'. Delegator output: {delegator_output_message.content}",
            )
            flow_ctx.update_current_message(no_tasks_msg)
            return flow_ctx

        logger.info(
            f"DelegatePattern '{self.pattern_name}': Extracted {len(tasks)} tasks."
        )

        task_results_content = []
        original_message_role = (
            flow_ctx.current_message.role if flow_ctx.current_message else "user"
        )

        # 4. Process Tasks
        if self.processing_mode == ProcessingMode.SEQUENTIAL:
            previous_task_summary = "N/A"

            for i, task_input_str in enumerate(tasks):

                if isinstance(self.delegatee_agent, str):
                    await engine.reset_agent(self.delegatee_agent)
                elif isinstance(self.delegatee_agent, BasePattern):
                    await self.delegatee_agent.reset_agents(engine)

                if self.summary_agent:
                    await engine.reset_agent(self.summary_agent)

                logger.info(
                    f"DelegatePattern '{self.pattern_name}' (Sequential) - Task {i + 1}/{len(tasks)}: Processing task."
                )
                current_task_input_content = task_input_str

                # Prepend shared memory if available
                if shared_memory_str:
                    current_task_input_content = f"Shared Context:\\n{shared_memory_str}\\n\\nTask:\\n{current_task_input_content}"

                if self.chain_of_agents and previous_task_summary != "N/A":
                    # If shared memory is also present, it's already prepended.
                    # The structure will be: Shared Context -> Previous Summary -> Current Task
                    current_task_input_content = f"Previous task(s) summary: {previous_task_summary}\\n\\nCurrent task: {task_input_str}"
                    if (
                        shared_memory_str
                    ):  # Re-evaluate to ensure correct order if both shared_memory and chain_of_agents
                        current_task_input_content = f"Shared Context:\\n{shared_memory_str}\\n\\nPrevious task(s) summary: {previous_task_summary}\\n\\nCurrent task: {task_input_str}"

                task_message = Message(
                    role=original_message_role, content=current_task_input_content
                )

                try:
                    # Update flow_ctx's current message for the delegatee
                    flow_ctx.update_current_message(task_message)

                    if isinstance(
                        self.delegatee_agent, str
                    ):  # Delegatee is an agent name
                        output_message = await engine.call_agent(
                            self.delegatee_agent,
                            flow_ctx.current_message,
                            **effective_agent_call_kwargs,
                        )
                        flow_ctx.update_current_message(output_message)

                    elif isinstance(
                        self.delegatee_agent, BasePattern
                    ):  # Delegatee is a nested pattern
                        # The nested pattern executes using the main flow_ctx, modifying it.
                        flow_ctx = await self.delegatee_agent.execute(
                            flow_ctx,
                            engine,
                            agent_call_kwargs=effective_agent_call_kwargs,
                        )
                        # flow_ctx.current_message is now the result of the nested pattern
                    else:
                        # This case should ideally be prevented by __init__ validation
                        raise TypeError(
                            f"Unsupported delegatee_agent type: {type(self.delegatee_agent)} in pattern '{self.pattern_name}'"
                        )

                    # Append the result of the task to the list of task results
                    task_results_content.append(str(flow_ctx.current_message.content))

                    # Get all messages from flow_ctx
                    all_messages = flow_ctx.get_all_messages()

                    # Filter for only tool and assistant messages
                    filtered_messages = [
                        msg for msg in all_messages if msg.role in ["tool", "assistant"]
                    ]

                    # Combine filtered messages into a single string
                    combined_messages = "\n".join(
                        str(msg.content) for msg in filtered_messages
                    )

                    if self.chain_of_agents:
                        summary_message = await engine.call_agent(
                            self.summary_agent,
                            combined_messages,
                            **effective_agent_call_kwargs,
                        )
                        previous_task_summary = str(summary_message.content)

                except Exception as e:
                    error_detail = f"Error processing task '{task_input_str[:50]}...' by delegatee '{str(self.delegatee_agent)}' in pattern '{self.pattern_name}'"
                    logger.error(
                        f"DelegatePattern '{self.pattern_name}' (Sequential): {error_detail}: {e}",
                        exc_info=True,
                    )
                    # Append error to results and continue with next task
                    task_results_content.append(f"Error: {error_detail}: {e}")
                    # Update current_message to reflect this task's error for consistency if needed,
                    # though final aggregation will show all results.
                    flow_ctx.update_current_message(
                        Message(
                            role="assistant",
                            content=f"Error processing one of the sequential tasks: {e}",
                        )
                    )

        elif self.processing_mode == ProcessingMode.PARALLEL:
            # TODO: Needs to be tested

            async def process_task_parallel(task_input_str: str, task_index: int):
                logger.info(
                    f"DelegatePattern '{self.pattern_name}' (Parallel) - Task {task_index + 1}/{len(tasks)}: Processing task."
                )
                task_input_for_parallel = task_input_str
                # Prepend shared memory if available
                if shared_memory_str:
                    task_input_for_parallel = f"Shared Context:\\n{shared_memory_str}\\n\\nTask:\\n{task_input_for_parallel}"

                task_message = Message(
                    role=original_message_role, content=task_input_for_parallel
                )

                try:
                    if isinstance(self.delegatee_agent, str):  # Agent name
                        output_message = await engine.call_agent(
                            self.delegatee_agent,
                            task_message,
                            **effective_agent_call_kwargs,
                        )
                        return str(output_message.content)

                    elif isinstance(
                        self.delegatee_agent, BasePattern
                    ):  # Nested pattern
                        # Each parallel execution of a nested pattern needs its own FlowContext copy
                        # to avoid race conditions or unintended shared state modifications.
                        parallel_task_flow_ctx = FlowContext(
                            current_message=task_message,
                            history=list(
                                flow_ctx.history
                            ),  # Create a new list (shallow copy of history messages)
                            shared_data=flow_ctx.shared_data.copy(),  # Shallow copy of shared_data dict
                        )
                        processed_task_flow_ctx = await self.delegatee_agent.execute(
                            parallel_task_flow_ctx,
                            engine,
                            agent_call_kwargs=effective_agent_call_kwargs,
                        )
                        return str(processed_task_flow_ctx.current_message.content)
                    else:
                        # This case should ideally be prevented by __init__ validation
                        raise TypeError(
                            f"Unsupported delegatee_agent type: {type(self.delegatee_agent)} in pattern '{self.pattern_name}'"
                        )
                except Exception as e:
                    error_detail = f"Error processing task '{task_input_str[:50]}...' by delegatee '{str(self.delegatee_agent)}' in pattern '{self.pattern_name}'"
                    logger.error(
                        f"DelegatePattern '{self.pattern_name}' (Parallel): {error_detail}: {e}",
                        exc_info=True,
                    )
                    return (
                        f"Error: {error_detail}: {e}"  # Return error as string result
                    )

            parallel_execution_results = await asyncio.gather(
                *(process_task_parallel(task, i) for i, task in enumerate(tasks))
            )
            task_results_content.extend(parallel_execution_results)

        else:
            logger.error(
                f"DelegatePattern '{self.pattern_name}': Invalid processing mode: {self.processing_mode}"
            )
            error_msg = Message(
                role="assistant",
                content=f"Invalid processing mode '{self.processing_mode}' in pattern '{self.pattern_name}'.",
            )
            flow_ctx.update_current_message(error_msg)
            return flow_ctx

        # 4. Aggregate Results
        final_aggregated_content = "\n\n---\n\n".join(
            task_results_content
        )  # Use a clear separator
        final_output_message = Message(
            role="assistant",
            content=f"Pattern '{self.pattern_name}' processed {len(tasks)} tasks. Results:\n{final_aggregated_content}",
        )
        flow_ctx.update_current_message(final_output_message)

        logger.info(
            f"DelegatePattern '{self.pattern_name}' completed. Output: {str(flow_ctx.current_message.content)[:100]}..."
        )
        return flow_ctx

    async def reset_agents(self, engine: Engine) -> None:
        if self.summary_agent:
            await engine.reset_agent(self.summary_agent)

        await engine.reset_agent(self.delegator_agent)

        if isinstance(self.delegatee_agent, str):
            await engine.reset_agent(self.delegatee_agent)
        elif isinstance(self.delegatee_agent, BasePattern):
            await self.delegatee_agent.reset_agents(engine)
