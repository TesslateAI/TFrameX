# tframex/patterns/__init__.py
from .base_pattern import BasePattern
from .delegate_pattern import DelegatePattern, ProcessingMode # Add DelegatePattern and Enum
from .discussion_pattern import DiscussionPattern
from .parallel_pattern import ParallelPattern
from .router_pattern import RouterPattern
from .sequential_pattern import SequentialPattern

__all__ = [
    "BasePattern",
    "SequentialPattern",
    "ParallelPattern",
    "RouterPattern",
    "DiscussionPattern",
    "DelegatePattern", # Export DelegatePattern
    "ProcessingMode",  # Export ProcessingMode Enum
]