import logging
from typing import Any, Dict, List, Optional, Tuple

from ..flows.flow_context import FlowContext
from ..models.primitives import Message
from ..util.engine import Engine
from .base_pattern import BasePattern # Adjusted for direct import from base_pattern

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
        # The initial message in flow_ctx is the topic of discussion.
        current_discussion_topic_msg = flow_ctx.current_message
        effective_agent_call_kwargs = agent_call_kwargs or {}

        for round_num in range(1, self.discussion_rounds + 1):
            logger.info(
                f"DiscussionPattern '{self.pattern_name}' - Round {round_num}/{self.discussion_rounds}"
            )
            round_messages: List[Tuple[str, Message]] = [] # (agent_name, message_object)

            for agent_name in self.participant_agent_names:
                logger.info(
                    f"DiscussionPattern '{self.pattern_name}' - Round {round_num}: Agent '{agent_name}' speaking on: {str(current_discussion_topic_msg.content)[:50]}..."
                )
                try:
                    # Each agent gets the current_discussion_topic_msg (which is the output of the previous agent or moderator)
                    agent_response: Message = await engine.call_agent(
                        agent_name,
                        current_discussion_topic_msg, # Input is the latest message in the discussion
                        **effective_agent_call_kwargs,
                    )
                    flow_ctx.history.append(agent_response)  # Record agent's turn in main flow history
                    round_messages.append((agent_name, agent_response))
                    current_discussion_topic_msg = (
                        agent_response  # Next agent responds to this
                    )

                    if (
                        self.stop_phrase
                        and self.stop_phrase in (agent_response.content or "").lower()
                    ):
                        logger.info(
                            f"DiscussionPattern '{self.pattern_name}': Agent '{agent_name}' said stop phrase. Ending."
                        )
                        flow_ctx.update_current_message(agent_response) # Final message of the pattern
                        return flow_ctx
                except Exception as e:
                    logger.error(
                        f"Error in DiscussionPattern '{self.pattern_name}' with agent '{agent_name}': {e}",
                        exc_info=True,
                    )
                    error_response = Message(
                        role="assistant", content=f"Agent {agent_name} error: {e}"
                    )
                    # Add error to main history and round messages
                    flow_ctx.history.append(error_response)
                    round_messages.append((agent_name, error_response))
                    current_discussion_topic_msg = error_response # Next agent sees this error message

            if not round_messages: # Should not happen if participants exist, but good check
                logger.warning(f"DiscussionPattern '{self.pattern_name}': Round {round_num} had no messages. Ending discussion.")
                break 

            # Moderator's turn, if configured and not the last round
            if self.moderator_agent_name and round_num < self.discussion_rounds:
                # Prepare input for the moderator: summary of the round
                # Use the original topic from flow_ctx.current_message (before this round started), or flow_ctx.history[0] for more robustness
                initial_topic_for_moderator = flow_ctx.history[0].content if flow_ctx.history else "the initial topic"

                mod_input_parts = [
                    f"Summary of Round {round_num} for discussion on '{str(initial_topic_for_moderator)[:50]}...':"
                ]
                for name, msg in round_messages: # msg is Message object
                    mod_input_parts.append(f"- {name}: {msg.content}")
                
                # Instruction for the moderator
                mod_input_parts.append("\nBased on the above, please moderate the discussion. You can summarize, ask follow-up questions, or guide the conversation.")
                
                mod_input_msg_content = "\n".join(mod_input_parts)
                mod_input_msg = Message(role="user", content=mod_input_msg_content)


                logger.info(
                    f"DiscussionPattern '{self.pattern_name}' - Round {round_num}: Calling moderator '{self.moderator_agent_name}'."
                )
                try:
                    moderator_response: Message = await engine.call_agent(
                        self.moderator_agent_name,
                        mod_input_msg,
                        **effective_agent_call_kwargs,
                    )
                    flow_ctx.history.append(moderator_response) # Record moderator's turn
                    current_discussion_topic_msg = moderator_response # Next round starts with moderator's output
                except Exception as e:
                    logger.error(
                        f"Error calling moderator agent '{self.moderator_agent_name}': {e}",
                        exc_info=True,
                    )
                    # If moderator fails, the next round continues based on the last participant's message
                    # or an error message.
                    current_discussion_topic_msg = Message(
                        role="assistant", content=f"Moderator error: {e}. Continuing based on previous messages."
                    )
                    flow_ctx.history.append(current_discussion_topic_msg)

            # If no moderator, or it's the last round and moderator already spoke,
            # current_discussion_topic_msg is already set to the last participant's response.

        # After all rounds, the current_discussion_topic_msg holds the final message of the discussion.
        flow_ctx.update_current_message(current_discussion_topic_msg)
        logger.info(
            f"DiscussionPattern '{self.pattern_name}' completed. Final message: {str(flow_ctx.current_message.content)[:50]}..."
        )
        return flow_ctx

    async def reset_agents(self, engine: Engine) -> None:
        logger.debug(f"Resetting agents for DiscussionPattern '{self.pattern_name}'")
        for agent_name in self.participant_agent_names:
            await engine.reset_agent(agent_name)
        if self.moderator_agent_name:
            await engine.reset_agent(self.moderator_agent_name)