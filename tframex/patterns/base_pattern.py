import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from ..flows.flow_context import FlowContext
from ..util.engine import Engine

logger = logging.getLogger(__name__)


class BasePattern(ABC):
    def __init__(self, pattern_name: str):
        self.pattern_name = pattern_name
        logger.debug(f"Pattern '{self.pattern_name}' initialized.")

    @abstractmethod
    async def execute(
        self,
        flow_ctx: FlowContext,
        engine: Engine,
        agent_call_kwargs: Optional[Dict[str, Any]] = None,
    ) -> FlowContext:
        pass

    @abstractmethod
    async def reset_agents(self, engine: Engine) -> None:
        """
        Resets the memory of all agents managed by this pattern.
        This should be called if the pattern instance is reused and needs a fresh start
        for its agents' memories.
        """
        pass

    def __str__(self):
        return f"{self.__class__.__name__}(name='{self.pattern_name}')"
