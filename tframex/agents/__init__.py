# TAF/tframex/agents/__init__.py

# Import from the specific files within the 'agents' sub-package
from .agent_logic import BaseAgent
from .agents import BasicAgent, ContextAgent

# Optional: Define __all__
__all__ = ['BaseAgent', 'BasicAgent', 'ContextAgent']