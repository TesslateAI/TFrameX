import logging
from typing import Any, Dict, Optional, Union

from ..flows.flow_context import FlowContext
from ..models.primitives import Message
from ..util.engine import Engine
from .base_pattern import BasePattern # Adjusted for direct import from base_pattern

logger = logging.getLogger(__name__)


class RouterPattern(BasePattern):
    def __init__(
        self,
        pattern_name: str,
        router_agent_name: str,
        routes: Dict[str, Union[str, BasePattern]],
        default_route: Optional[Union[str, BasePattern]] = None,
    ):
        super().__init__(pattern_name)
        self.router_agent_name = router_agent_name
        self.routes = routes
        self.default_route = default_route

    async def execute(
        self,
        flow_ctx: FlowContext,
        engine: Engine,
        agent_call_kwargs: Optional[Dict[str, Any]] = None,
    ) -> FlowContext:
        logger.info(
            f"Executing RouterPattern '{self.pattern_name}'. Input: {str(flow_ctx.current_message.content)[:50]}..."
        )
        effective_agent_call_kwargs = agent_call_kwargs or {}
        try:
            router_response: Message = await engine.call_agent(
                self.router_agent_name,
                flow_ctx.current_message,
                **effective_agent_call_kwargs,
            )
            # The router_response itself isn't usually the main output of the pattern,
            # so we add it to history but don't update_current_message with it *yet*.
            # The actual output will be from the routed step.
            flow_ctx.history.append(router_response)
            route_key = (router_response.content or "").strip()
            logger.info(
                f"RouterPattern '{self.pattern_name}': Router agent '{self.router_agent_name}' decided route_key: '{route_key}'."
            )
        except Exception as e:
            logger.error(
                f"Error calling router agent '{self.router_agent_name}' in RouterPattern '{self.pattern_name}': {e}",
                exc_info=True,
            )
            error_msg = Message(
                role="assistant",
                content=f"Error in router agent '{self.router_agent_name}': {e}",
            )
            flow_ctx.update_current_message(error_msg)
            return flow_ctx

        target_step = self.routes.get(route_key)
        if target_step is None:
            logger.warning(
                f"RouterPattern '{self.pattern_name}': Route key '{route_key}' not found. Using default."
            )
            target_step = self.default_route

        if target_step is None:
            logger.error(
                f"RouterPattern '{self.pattern_name}': No route for key '{route_key}' and no default."
            )
            error_msg = Message(
                role="assistant", content=f"Routing error: No path for '{route_key}'. The router decided '{route_key}', but no corresponding action was defined, and no default action is set."
            )
            flow_ctx.update_current_message(error_msg)
            return flow_ctx

        target_name = (
            str(target_step) if isinstance(target_step, BasePattern) else target_step
        )
        logger.info(
            f"RouterPattern '{self.pattern_name}': Executing routed step '{target_name}'."
        )

        # The input to the routed step is the *original* input to the RouterPattern
        # (i.e., flow_ctx.current_message before the router_agent was called).
        # Or, if the design intends for the routed step to receive the router_agent's output,
        # then flow_ctx.update_current_message(router_response) should have happened.
        # Current design: routed step receives the same input as the router_agent.
        # If a different behavior is desired, this logic needs adjustment.
        # For now, let's assume the original flow_ctx.current_message is still the intended input for the target_step.

        if isinstance(target_step, str):  # Agent name
            try:
                # Using flow_ctx.current_message, which is the *original* input to the pattern before router agent.
                # If router_response should be input to target, need to update flow_ctx.current_message accordingly.
                # The prompt says "Router agent's output (e.g., "weather") is the route key", not the input to next step.
                # So, using flow_ctx.current_message (original pattern input) seems correct.
                output_message = await engine.call_agent(
                    target_step, flow_ctx.current_message, **effective_agent_call_kwargs
                )
                flow_ctx.update_current_message(output_message) # This is the final output of the pattern
            except Exception as e:
                logger.error(
                    f"Error in RouterPattern '{self.pattern_name}' calling routed agent '{target_step}': {e}",
                    exc_info=True,
                )
                error_msg = Message(
                    role="assistant",
                    content=f"Error executing routed agent '{target_step}': {e}",
                )
                flow_ctx.update_current_message(error_msg)
        elif isinstance(target_step, BasePattern):  # Nested pattern
            try:
                # Nested patterns operate on and return a FlowContext.
                # The input flow_ctx (containing original message) is passed.
                flow_ctx = await target_step.execute(
                    flow_ctx, engine, agent_call_kwargs=effective_agent_call_kwargs
                ) # The returned flow_ctx has its current_message updated by the nested pattern.
            except Exception as e:
                logger.error(
                    f"Error in RouterPattern '{self.pattern_name}' executing routed pattern '{target_step.pattern_name}': {e}",
                    exc_info=True,
                )
                error_msg = Message(
                    role="assistant",
                    content=f"Error executing routed pattern '{target_step.pattern_name}': {e}",
                )
                flow_ctx.update_current_message(error_msg)

        logger.info(f"RouterPattern '{self.pattern_name}' completed.")
        return flow_ctx

    async def reset_agents(self, engine: Engine) -> None:
        logger.debug(f"Resetting agents for RouterPattern '{self.pattern_name}'")
        await engine.reset_agent(self.router_agent_name)
        for route_target in self.routes.values():
            if isinstance(route_target, BasePattern):
                await route_target.reset_agents(engine)
            elif isinstance(route_target, str):
                await engine.reset_agent(route_target)
        if self.default_route:
            if isinstance(self.default_route, BasePattern):
                await self.default_route.reset_agents(engine)
            elif isinstance(self.default_route, str):
                await engine.reset_agent(self.default_route)