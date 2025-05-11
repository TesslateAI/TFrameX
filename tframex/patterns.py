import asyncio
import logging
from abc import ABC, abstractmethod
from typing import List, Union, Dict, Any, Tuple, Optional

from .primitives import Message, ToolCall
from .flow_context import FlowContext
if False: # TYPE_CHECKING:
    from .app import TFrameXRuntimeContext

logger = logging.getLogger(__name__)

class BasePattern(ABC):
    def __init__(self, pattern_name: str):
        self.pattern_name = pattern_name
        logger.debug(f"Pattern '{self.pattern_name}' initialized.")

    @abstractmethod
    async def execute(self, flow_ctx: FlowContext, app_runtime: 'TFrameXRuntimeContext',
                      agent_call_kwargs: Optional[Dict[str, Any]] = None) -> FlowContext: # NEW agent_call_kwargs
        pass

    def __str__(self):
        return f"{self.__class__.__name__}(name='{self.pattern_name}')"


class SequentialPattern(BasePattern):
    def __init__(self, pattern_name: str, steps: List[Union[str, BasePattern]]):
        super().__init__(pattern_name)
        self.steps = steps

    async def execute(self, flow_ctx: FlowContext, app_runtime: 'TFrameXRuntimeContext',
                      agent_call_kwargs: Optional[Dict[str, Any]] = None) -> FlowContext: # NEW
        logger.info(f"Executing SequentialPattern '{self.pattern_name}' with {len(self.steps)} steps. Input: {str(flow_ctx.current_message.content)[:50]}...")
        effective_agent_call_kwargs = agent_call_kwargs or {}

        for i, step in enumerate(self.steps):
            step_name = str(step) if isinstance(step, BasePattern) else step
            logger.info(f"SequentialPattern '{self.pattern_name}' - Step {i+1}/{len(self.steps)}: Executing '{step_name}'.")
            
            if isinstance(step, str): # Agent name
                try:
                    output_message = await app_runtime.call_agent(step, flow_ctx.current_message, **effective_agent_call_kwargs)
                    flow_ctx.update_current_message(output_message)
                except Exception as e: # ... error handling ...
                    logger.error(f"Error in SequentialPattern '{self.pattern_name}' calling agent '{step}': {e}", exc_info=True)
                    error_msg = Message(role="assistant", content=f"Error executing agent '{step}' in sequence '{self.pattern_name}': {e}")
                    flow_ctx.update_current_message(error_msg)
                    return flow_ctx
            elif isinstance(step, BasePattern): # Nested pattern
                try:
                    flow_ctx = await step.execute(flow_ctx, app_runtime, agent_call_kwargs=effective_agent_call_kwargs) # Pass kwargs
                except Exception as e: # ... error handling ...
                    logger.error(f"Error in SequentialPattern '{self.pattern_name}' executing nested pattern '{step.pattern_name}': {e}", exc_info=True)
                    error_msg = Message(role="assistant", content=f"Error executing nested pattern '{step.pattern_name}' in sequence '{self.pattern_name}': {e}")
                    flow_ctx.update_current_message(error_msg)
                    return flow_ctx
            else: # ... error handling ...
                logger.error(f"SequentialPattern '{self.pattern_name}': Invalid step type: {type(step)}")
                error_msg = Message(role="assistant", content=f"Invalid step type in sequence '{self.pattern_name}'.")
                flow_ctx.update_current_message(error_msg)
                return flow_ctx
        logger.info(f"SequentialPattern '{self.pattern_name}' completed.")
        return flow_ctx


class ParallelPattern(BasePattern):
    def __init__(self, pattern_name: str, tasks: List[Union[str, BasePattern]]):
        super().__init__(pattern_name)
        self.tasks = tasks

    async def execute(self, flow_ctx: FlowContext, app_runtime: 'TFrameXRuntimeContext',
                      agent_call_kwargs: Optional[Dict[str, Any]] = None) -> FlowContext: # NEW
        logger.info(f"Executing ParallelPattern '{self.pattern_name}' with {len(self.tasks)} tasks. Input: {str(flow_ctx.current_message.content)[:50]}...")
        initial_input_msg = flow_ctx.current_message
        effective_agent_call_kwargs = agent_call_kwargs or {}
        coroutines = []
        task_identifiers = []

        for task_item in self.tasks:
            task_name = str(task_item) if isinstance(task_item, BasePattern) else task_item
            task_identifiers.append(task_name)

            if isinstance(task_item, str): # Agent name
                coroutines.append(app_runtime.call_agent(task_item, initial_input_msg, **effective_agent_call_kwargs))
            elif isinstance(task_item, BasePattern):
                branch_flow_ctx = FlowContext(initial_input=initial_input_msg, shared_data=flow_ctx.shared_data.copy())
                coroutines.append(task_item.execute(branch_flow_ctx, app_runtime, agent_call_kwargs=effective_agent_call_kwargs)) # Pass kwargs
            else: # ... error handling ...
                async def error_coro(): return Message(role="assistant", content=f"Invalid task type in parallel pattern '{self.pattern_name}'.")
                coroutines.append(error_coro())
        
        results = await asyncio.gather(*coroutines, return_exceptions=True)
        # ... (rest of result aggregation logic - no changes needed here for agent_call_kwargs) ...
        aggregated_content_parts = []
        result_artifacts = [] 

        for i, res_item in enumerate(results):
            task_id = task_identifiers[i]
            if isinstance(res_item, Exception):
                logger.error(f"ParallelPattern '{self.pattern_name}' - Task '{task_id}' failed: {res_item}", exc_info=False)
                aggregated_content_parts.append(f"Task '{task_id}' failed: {str(res_item)}")
                result_artifacts.append({"name": f"Result_for_{task_id.replace(' ', '_')}", "parts": [{"type": "text", "text": f"Error: {str(res_item)}"}]})
            elif isinstance(res_item, FlowContext): 
                logger.info(f"ParallelPattern '{self.pattern_name}' - Task '{task_id}' (pattern) completed. Output: {str(res_item.current_message.content)[:50]}...")
                aggregated_content_parts.append(f"Task '{task_id}' (pattern) completed. Result: {str(res_item.current_message.content)[:100]}...")
                result_artifacts.append({"name": f"Result_for_{task_id.replace(' ', '_')}", "parts": [{"type": "data", "data": res_item.current_message.model_dump(exclude_none=True)}]})
            elif isinstance(res_item, Message): 
                logger.info(f"ParallelPattern '{self.pattern_name}' - Task '{task_id}' (agent) completed. Output: {str(res_item.content)[:50]}...")
                aggregated_content_parts.append(f"Task '{task_id}' (agent) completed. Result: {str(res_item.content)[:100]}...")
                result_artifacts.append({"name": f"Result_for_{task_id.replace(' ', '_')}", "parts": [{"type": "data", "data": res_item.model_dump(exclude_none=True)}]})
            else: 
                logger.warning(f"ParallelPattern '{self.pattern_name}' - Task '{task_id}' returned unexpected type: {type(res_item)}")
                aggregated_content_parts.append(f"Task '{task_id}' returned unexpected data.")
                result_artifacts.append({"name": f"Result_for_{task_id.replace(' ', '_')}", "parts": [{"type": "text", "text": "Unexpected result type."}]})

        summary_content = (f"Parallel execution of '{self.pattern_name}' completed with {len(self.tasks)} tasks.\n" + "\n".join(aggregated_content_parts))
        final_output_message = Message(role="assistant", content=summary_content)
        flow_ctx.shared_data[f"{self.pattern_name}_results"] = result_artifacts
        flow_ctx.update_current_message(final_output_message)
        
        logger.info(f"ParallelPattern '{self.pattern_name}' completed.")
        return flow_ctx


class RouterPattern(BasePattern):
    def __init__(self, pattern_name: str, router_agent_name: str,
                 routes: Dict[str, Union[str, BasePattern]],
                 default_route: Optional[Union[str, BasePattern]] = None):
        super().__init__(pattern_name)
        self.router_agent_name = router_agent_name
        self.routes = routes
        self.default_route = default_route

    async def execute(self, flow_ctx: FlowContext, app_runtime: 'TFrameXRuntimeContext',
                      agent_call_kwargs: Optional[Dict[str, Any]] = None) -> FlowContext: # NEW
        logger.info(f"Executing RouterPattern '{self.pattern_name}'. Input: {str(flow_ctx.current_message.content)[:50]}...")
        effective_agent_call_kwargs = agent_call_kwargs or {}
        try:
            router_response: Message = await app_runtime.call_agent(self.router_agent_name, flow_ctx.current_message, **effective_agent_call_kwargs)
            flow_ctx.history.append(router_response)
            route_key = (router_response.content or "").strip()
            logger.info(f"RouterPattern '{self.pattern_name}': Router agent '{self.router_agent_name}' decided route_key: '{route_key}'.")
        except Exception as e: # ... error handling ...
            logger.error(f"Error calling router agent '{self.router_agent_name}' in RouterPattern '{self.pattern_name}': {e}", exc_info=True)
            error_msg = Message(role="assistant", content=f"Error in router agent '{self.router_agent_name}': {e}")
            flow_ctx.update_current_message(error_msg)
            return flow_ctx

        target_step = self.routes.get(route_key)
        if target_step is None:
            logger.warning(f"RouterPattern '{self.pattern_name}': Route key '{route_key}' not found. Using default.")
            target_step = self.default_route
        if target_step is None: # ... error handling ...
            logger.error(f"RouterPattern '{self.pattern_name}': No route for key '{route_key}' and no default.")
            error_msg = Message(role="assistant", content=f"Routing error: No path for '{route_key}'.")
            flow_ctx.update_current_message(error_msg)
            return flow_ctx
        
        target_name = str(target_step) if isinstance(target_step, BasePattern) else target_step
        logger.info(f"RouterPattern '{self.pattern_name}': Executing routed step '{target_name}'.")

        if isinstance(target_step, str): # Agent name
            try:
                output_message = await app_runtime.call_agent(target_step, flow_ctx.current_message, **effective_agent_call_kwargs)
                flow_ctx.update_current_message(output_message)
            except Exception as e: # ... error handling ...
                logger.error(f"Error in RouterPattern '{self.pattern_name}' calling routed agent '{target_step}': {e}", exc_info=True)
                error_msg = Message(role="assistant", content=f"Error executing routed agent '{target_step}': {e}")
                flow_ctx.update_current_message(error_msg)
        elif isinstance(target_step, BasePattern): # Nested pattern
            try:
                flow_ctx = await target_step.execute(flow_ctx, app_runtime, agent_call_kwargs=effective_agent_call_kwargs) # Pass kwargs
            except Exception as e: # ... error handling ...
                logger.error(f"Error in RouterPattern '{self.pattern_name}' executing routed pattern '{target_step.pattern_name}': {e}", exc_info=True)
                error_msg = Message(role="assistant", content=f"Error executing routed pattern '{target_step.pattern_name}': {e}")
                flow_ctx.update_current_message(error_msg)
        
        logger.info(f"RouterPattern '{self.pattern_name}' completed.")
        return flow_ctx


class DiscussionPattern(BasePattern):
    def __init__(self, pattern_name: str,
                 participant_agent_names: List[str],
                 discussion_rounds: int = 1,
                 moderator_agent_name: Optional[str] = None,
                 stop_phrase: Optional[str] = None):
        super().__init__(pattern_name)
        if not participant_agent_names: raise ValueError("DiscussionPattern needs participants.")
        self.participant_agent_names = participant_agent_names
        self.discussion_rounds = discussion_rounds
        self.moderator_agent_name = moderator_agent_name
        self.stop_phrase = stop_phrase.lower() if stop_phrase else None

    async def execute(self, flow_ctx: FlowContext, app_runtime: 'TFrameXRuntimeContext',
                      agent_call_kwargs: Optional[Dict[str, Any]] = None) -> FlowContext: # NEW
        logger.info(f"Executing DiscussionPattern '{self.pattern_name}' for {self.discussion_rounds} rounds. Topic: {str(flow_ctx.current_message.content)[:50]}...")
        current_discussion_topic_msg = flow_ctx.current_message
        effective_agent_call_kwargs = agent_call_kwargs or {}

        for round_num in range(1, self.discussion_rounds + 1):
            logger.info(f"DiscussionPattern '{self.pattern_name}' - Round {round_num}/{self.discussion_rounds}")
            round_messages: List[Tuple[str, Message]] = []

            for agent_name in self.participant_agent_names:
                logger.info(f"DiscussionPattern '{self.pattern_name}' - Round {round_num}: Agent '{agent_name}' speaking on: {str(current_discussion_topic_msg.content)[:50]}...")
                try:
                    # Each agent gets the current_discussion_topic_msg as input
                    # Pass effective_agent_call_kwargs which might contain global template_vars
                    agent_response: Message = await app_runtime.call_agent(agent_name, current_discussion_topic_msg, **effective_agent_call_kwargs)
                    flow_ctx.history.append(agent_response) # Record turn
                    round_messages.append((agent_name, agent_response))
                    current_discussion_topic_msg = agent_response # Next agent responds to this

                    if self.stop_phrase and self.stop_phrase in (agent_response.content or "").lower():
                        logger.info(f"DiscussionPattern '{self.pattern_name}': Agent '{agent_name}' said stop phrase. Ending.")
                        flow_ctx.update_current_message(agent_response)
                        return flow_ctx
                except Exception as e: # ... error handling ...
                    logger.error(f"Error in DiscussionPattern '{self.pattern_name}' with agent '{agent_name}': {e}", exc_info=True)
                    error_response = Message(role="assistant", content=f"Agent {agent_name} error: {e}")
                    round_messages.append((agent_name, error_response))
                    current_discussion_topic_msg = error_response

            if not round_messages: break # End if round is empty

            if self.moderator_agent_name and round_num < self.discussion_rounds:
                mod_input_parts = [f"Summary of Round {round_num} for discussion on '{str(flow_ctx.current_message.content)[:50]}...':"]
                for name, msg in round_messages: mod_input_parts.append(f"- {name}: {msg.content}")
                mod_input_msg = Message(role="user", content="\n".join(mod_input_parts) + "\n\nPlease moderate.")
                
                logger.info(f"DiscussionPattern '{self.pattern_name}' - Round {round_num}: Calling moderator '{self.moderator_agent_name}'.")
                try:
                    moderator_response: Message = await app_runtime.call_agent(self.moderator_agent_name, mod_input_msg, **effective_agent_call_kwargs)
                    flow_ctx.history.append(moderator_response)
                    current_discussion_topic_msg = moderator_response
                except Exception as e: # ... error handling ...
                    logger.error(f"Error calling moderator agent '{self.moderator_agent_name}': {e}", exc_info=True)
                    current_discussion_topic_msg = Message(role="assistant", content=f"Moderator error: {e}. Continuing.")
            elif round_messages:
                current_discussion_topic_msg = round_messages[-1][1]

        flow_ctx.update_current_message(current_discussion_topic_msg)
        logger.info(f"DiscussionPattern '{self.pattern_name}' completed. Final message: {str(flow_ctx.current_message.content)[:50]}...")
        return flow_ctx