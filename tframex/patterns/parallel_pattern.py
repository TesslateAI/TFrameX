import asyncio
import logging
from typing import Any, Dict, List, Optional, Union

from ..flows.flow_context import FlowContext
from ..models.primitives import Message
from ..util.engine import Engine
from .base_pattern import BasePattern

logger = logging.getLogger(__name__)


class ParallelPattern(BasePattern):
    def __init__(self, pattern_name: str, tasks: List[Union[str, BasePattern]]):
        super().__init__(pattern_name)
        self.tasks = tasks

    async def execute(
        self,
        flow_ctx: FlowContext,
        engine: Engine,
        agent_call_kwargs: Optional[Dict[str, Any]] = None,
    ) -> FlowContext:
        logger.info(
            f"Executing ParallelPattern '{self.pattern_name}' with {len(self.tasks)} tasks. Input: {str(flow_ctx.current_message.content)[:50]}..."
        )
        initial_input_msg = flow_ctx.current_message
        effective_agent_call_kwargs = agent_call_kwargs or {}
        coroutines = []
        task_identifiers = []

        for task_item in self.tasks:
            task_name = (
                str(task_item) if isinstance(task_item, BasePattern) else task_item
            )
            task_identifiers.append(task_name)

            if isinstance(task_item, str):  # Agent name
                coroutines.append(
                    engine.call_agent(
                        task_item, initial_input_msg, **effective_agent_call_kwargs
                    )
                )
            elif isinstance(task_item, BasePattern):
                branch_flow_ctx = FlowContext(
                    initial_input=initial_input_msg,
                    shared_data=flow_ctx.shared_data.copy(),
                )
                coroutines.append(
                    task_item.execute(
                        branch_flow_ctx,
                        engine,
                        agent_call_kwargs=effective_agent_call_kwargs,
                    )
                )
            else:

                async def error_coro():
                    return Message(
                        role="assistant",
                        content=f"Invalid task type in parallel pattern '{self.pattern_name}'.",
                    )

                coroutines.append(error_coro())

        results = await asyncio.gather(*coroutines, return_exceptions=True)
        aggregated_content_parts = []
        result_artifacts = []

        for i, res_item in enumerate(results):
            task_id = task_identifiers[i]
            if isinstance(res_item, Exception):
                logger.error(
                    f"ParallelPattern '{self.pattern_name}' - Task '{task_id}' failed: {res_item}",
                    exc_info=False,
                )
                aggregated_content_parts.append(
                    f"Task '{task_id}' failed: {str(res_item)}"
                )
                result_artifacts.append(
                    {
                        "name": f"Result_for_{task_id.replace(' ', '_')}",
                        "parts": [{"type": "text", "text": f"Error: {str(res_item)}"}],
                    }
                )
            elif isinstance(res_item, FlowContext):
                logger.info(
                    f"ParallelPattern '{self.pattern_name}' - Task '{task_id}' (pattern) completed. Output: {str(res_item.current_message.content)[:50]}..."
                )
                aggregated_content_parts.append(
                    f"Task '{task_id}' (pattern) completed. Result: {str(res_item.current_message.content)[:100]}..."
                )
                result_artifacts.append(
                    {
                        "name": f"Result_for_{task_id.replace(' ', '_')}",
                        "parts": [
                            {
                                "type": "data",
                                "data": res_item.current_message.model_dump(
                                    exclude_none=True
                                ),
                            }
                        ],
                    }
                )
            elif isinstance(res_item, Message):
                logger.info(
                    f"ParallelPattern '{self.pattern_name}' - Task '{task_id}' (agent) completed. Output: {str(res_item.content)[:50]}..."
                )
                aggregated_content_parts.append(
                    f"Task '{task_id}' (agent) completed. Result: {str(res_item.content)[:100]}..."
                )
                result_artifacts.append(
                    {
                        "name": f"Result_for_{task_id.replace(' ', '_')}",
                        "parts": [
                            {
                                "type": "data",
                                "data": res_item.model_dump(exclude_none=True),
                            }
                        ],
                    }
                )
            else:
                logger.warning(
                    f"ParallelPattern '{self.pattern_name}' - Task '{task_id}' returned unexpected type: {type(res_item)}"
                )
                aggregated_content_parts.append(
                    f"Task '{task_id}' returned unexpected data."
                )
                result_artifacts.append(
                    {
                        "name": f"Result_for_{task_id.replace(' ', '_')}",
                        "parts": [{"type": "text", "text": "Unexpected result type."}],
                    }
                )

        summary_content = (
            f"Parallel execution of '{self.pattern_name}' completed with {len(self.tasks)} tasks.\n"
            + "\n".join(aggregated_content_parts)
        )
        final_output_message = Message(role="assistant", content=summary_content)
        flow_ctx.shared_data[f"{self.pattern_name}_results"] = result_artifacts
        flow_ctx.update_current_message(final_output_message)

        logger.info(f"ParallelPattern '{self.pattern_name}' completed.")
        return flow_ctx
