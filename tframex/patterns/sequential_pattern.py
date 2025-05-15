import logging
from typing import Any, Dict, List, Optional, Union

from ..flows.flow_context import FlowContext
from ..models.primitives import Message
from ..util.engine import Engine
from .base_pattern import BasePattern # Adjusted for direct import from base_pattern

logger = logging.getLogger(__name__)


class SequentialPattern(BasePattern):
    def __init__(self, pattern_name: str, steps: List[Union[str, BasePattern]]):
        super().__init__(pattern_name)
        self.steps = steps

    async def execute(
        self,
        flow_ctx: FlowContext,
        engine: Engine,
        agent_call_kwargs: Optional[Dict[str, Any]] = None,
    ) -> FlowContext:
        logger.info(
            f"Executing SequentialPattern '{self.pattern_name}' with {len(self.steps)} steps. Input: {str(flow_ctx.current_message.content)[:50]}..."
        )
        effective_agent_call_kwargs = agent_call_kwargs or {}

        for i, step in enumerate(self.steps):
            step_name = str(step) if isinstance(step, BasePattern) else step
            logger.info(
                f"SequentialPattern '{self.pattern_name}' - Step {i + 1}/{len(self.steps)}: Executing '{step_name}'."
            )

            if isinstance(step, str):  # Agent name
                try:
                    output_message = await engine.call_agent(
                        step, flow_ctx.current_message, **effective_agent_call_kwargs
                    )
                    flow_ctx.update_current_message(output_message)
                except Exception as e:
                    logger.error(
                        f"Error in SequentialPattern '{self.pattern_name}' calling agent '{step}': {e}",
                        exc_info=True,
                    )
                    error_msg = Message(
                        role="assistant",
                        content=f"Error executing agent '{step}' in sequence '{self.pattern_name}': {e}",
                    )
                    flow_ctx.update_current_message(error_msg)
                    return flow_ctx
            elif isinstance(step, BasePattern):  # Nested pattern
                try:
                    flow_ctx = await step.execute(
                        flow_ctx, engine, agent_call_kwargs=effective_agent_call_kwargs
                    )
                except Exception as e:
                    logger.error(
                        f"Error in SequentialPattern '{self.pattern_name}' executing nested pattern '{step.pattern_name}': {e}",
                        exc_info=True,
                    )
                    error_msg = Message(
                        role="assistant",
                        content=f"Error executing nested pattern '{step.pattern_name}' in sequence '{self.pattern_name}': {e}",
                    )
                    flow_ctx.update_current_message(error_msg)
                    return flow_ctx
            else:
                logger.error(
                    f"SequentialPattern '{self.pattern_name}': Invalid step type: {type(step)}"
                )
                error_msg = Message(
                    role="assistant",
                    content=f"Invalid step type in sequence '{self.pattern_name}'.",
                )
                flow_ctx.update_current_message(error_msg)
                return flow_ctx
        logger.info(f"SequentialPattern '{self.pattern_name}' completed.")
        return flow_ctx

    async def reset_agents(self, engine: Engine) -> None:
        logger.debug(f"Resetting agents for SequentialPattern '{self.pattern_name}'")
        for step in self.steps:
            if isinstance(step, BasePattern):
                await step.reset_agents(engine)
            elif isinstance(step, str): # Agent name
                await engine.reset_agent(step)