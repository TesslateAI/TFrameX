import logging
from typing import Any, Dict, List, Optional, Tuple, Union

from ..flows.flow_context import FlowContext
from ..models.primitives import Message
from ..util.engine import Engine
from .base_pattern import BasePattern

logger = logging.getLogger(__name__)


class DiscussionPattern(BasePattern):
    def __init__(
        self,
        pattern_name: str,
        participant_agent_names: List[str],
        discussion_rounds: int = 1,
        moderator_agent_name: Optional[str] = None,
        stop_phrase: Optional[str] = None,
    ):
        super().__init__(pattern_name)
        if not participant_agent_names:
            raise ValueError("DiscussionPattern needs participants.")
        self.participant_agent_names = participant_agent_names
        self.discussion_rounds = discussion_rounds
        self.moderator_agent_name = moderator_agent_name
        self.stop_phrase = stop_phrase.lower() if stop_phrase else None

    async def execute(
        self,
        flow_ctx: FlowContext,
        engine: Engine,
        agent_call_kwargs: Optional[Dict[str, Any]] = None,
    ) -> FlowContext:
        logger.info(
            f"Executing DiscussionPattern '{self.pattern_name}' for {self.discussion_rounds} rounds. Topic: {str(flow_ctx.current_message.content)[:50]}..."
        )
        current_discussion_topic_msg = flow_ctx.current_message
        effective_agent_call_kwargs = agent_call_kwargs or {}

        for round_num in range(1, self.discussion_rounds + 1):
            logger.info(
                f"DiscussionPattern '{self.pattern_name}' - Round {round_num}/{self.discussion_rounds}"
            )
            round_messages: List[Tuple[str, Message]] = []

            for agent_name in self.participant_agent_names:
                logger.info(
                    f"DiscussionPattern '{self.pattern_name}' - Round {round_num}: Agent '{agent_name}' speaking on: {str(current_discussion_topic_msg.content)[:50]}..."
                )
                try:
                    agent_response: Message = await engine.call_agent(
                        agent_name,
                        current_discussion_topic_msg,
                        **effective_agent_call_kwargs,
                    )
                    flow_ctx.history.append(agent_response)
                    round_messages.append((agent_name, agent_response))
                    current_discussion_topic_msg = agent_response

                    if (
                        self.stop_phrase
                        and self.stop_phrase in (agent_response.content or "").lower()
                    ):
                        logger.info(
                            f"DiscussionPattern '{self.pattern_name}': Agent '{agent_name}' said stop phrase. Ending."
                        )
                        flow_ctx.update_current_message(agent_response)
                        return flow_ctx
                except Exception as e:
                    logger.error(
                        f"Error in DiscussionPattern '{self.pattern_name}' with agent '{agent_name}': {e}",
                        exc_info=True,
                    )
                    error_response = Message(
                        role="assistant", content=f"Agent {agent_name} error: {e}"
                    )
                    round_messages.append((agent_name, error_response))
                    current_discussion_topic_msg = error_response

            if not round_messages:
                break

            if self.moderator_agent_name and round_num < self.discussion_rounds:
                mod_input_parts = [
                    f"Summary of Round {round_num} for discussion on '{str(flow_ctx.current_message.content)[:50]}...':"
                ]
                for name, msg in round_messages:
                    mod_input_parts.append(f"- {name}: {msg.content}")
                mod_input_msg = Message(
                    role="user",
                    content="\n".join(mod_input_parts) + "\n\nPlease moderate.",
                )

                logger.info(
                    f"DiscussionPattern '{self.pattern_name}' - Round {round_num}: Calling moderator '{self.moderator_agent_name}'."
                )
                try:
                    moderator_response: Message = await engine.call_agent(
                        self.moderator_agent_name,
                        mod_input_msg,
                        **effective_agent_call_kwargs,
                    )
                    flow_ctx.history.append(moderator_response)
                    current_discussion_topic_msg = moderator_response
                except Exception as e:
                    logger.error(
                        f"Error calling moderator agent '{self.moderator_agent_name}': {e}",
                        exc_info=True,
                    )
                    current_discussion_topic_msg = Message(
                        role="assistant", content=f"Moderator error: {e}. Continuing."
                    )
            elif round_messages:
                current_discussion_topic_msg = round_messages[-1][1]

        flow_ctx.update_current_message(current_discussion_topic_msg)
        logger.info(
            f"DiscussionPattern '{self.pattern_name}' completed. Final message: {str(flow_ctx.current_message.content)[:50]}..."
        )
        return flow_ctx
