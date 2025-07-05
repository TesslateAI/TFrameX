---
sidebar_position: 6
title: Patterns
---

# Patterns API Reference

Patterns are reusable multi-agent orchestration templates that implement common collaboration strategies. TFrameX provides four built-in patterns that can be customized and nested for complex workflows.

## Pattern Overview

All patterns inherit from the `BasePattern` class and implement the `execute` method:

```python
from tframex import (
    SequentialPattern,
    ParallelPattern, 
    RouterPattern,
    DiscussionPattern
)
```

## Sequential Pattern

Execute agents or nested patterns in a defined sequence, passing data from one to the next.

```python
from tframex import SequentialPattern

# Basic sequential pattern
pattern = SequentialPattern(
    pattern_name="document_pipeline",
    steps=[
        "ResearchAgent",      # Agent name (string)
        "WriterAgent",
        "EditorAgent"
    ]
)

# With nested patterns
inner_pattern = ParallelPattern(
    pattern_name="parallel_analysis",
    tasks=["Analyst1", "Analyst2", "Analyst3"]
)

pattern = SequentialPattern(
    pattern_name="complex_pipeline",
    steps=[
        "DataCollector",
        inner_pattern,        # Nested pattern
        "Synthesizer"
    ]
)
```

### SequentialPattern Constructor

```python
SequentialPattern(
    pattern_name: str,
    steps: List[Union[str, BasePattern]]
)
```

**Parameters:**
- `pattern_name`: Unique identifier for the pattern
- `steps`: List of agent names (strings) or nested pattern instances

### Execution Flow

1. Each step receives the output from the previous step
2. The initial input goes to the first step
3. The final output comes from the last step
4. Execution stops if `STOP_FLOW` is set in `shared_data`

## Parallel Pattern

Execute multiple agents or patterns concurrently and aggregate their results.

```python
from tframex import ParallelPattern

# Basic parallel pattern
pattern = ParallelPattern(
    pattern_name="multi_perspective_analysis",
    tasks=[
        "TechnicalAnalyst",
        "BusinessAnalyst",
        "LegalAnalyst",
        "RiskAnalyst"
    ]
)

# With nested patterns
pattern = ParallelPattern(
    pattern_name="parallel_nested",
    tasks=[
        "QuickAnalyzer",
        SequentialPattern(
            pattern_name="deep_analysis",
            steps=["Researcher", "Analyst"]
        )
    ]
)
```

### ParallelPattern Constructor

```python
ParallelPattern(
    pattern_name: str,
    tasks: List[Union[str, BasePattern]]
)
```

**Parameters:**
- `pattern_name`: Unique identifier for the pattern
- `tasks`: List of agent names (strings) or nested pattern instances to run in parallel

### Aggregation

The default aggregation creates a summary containing:
- Combined content from all task outputs
- Individual task results indexed by task name
- Execution metadata

## Router Pattern

Route execution to different agents or patterns based on a router agent's decision.

```python
from tframex import RouterPattern

# Basic routing
pattern = RouterPattern(
    pattern_name="support_router",
    router_agent_name="RequestClassifier",
    routes={
        "technical": "TechnicalSupport",
        "billing": "BillingSupport", 
        "account": "AccountSupport",
        "general": "GeneralSupport"
    },
    default_route="GeneralSupport"
)

# With nested pattern routes
technical_flow = SequentialPattern(
    pattern_name="tech_flow",
    steps=["DiagnosticAgent", "SolutionAgent"]
)

pattern = RouterPattern(
    pattern_name="advanced_router",
    router_agent_name="IssueClassifier",
    routes={
        "hardware": "HardwareExpert",
        "software": technical_flow,  # Route to pattern
        "network": "NetworkExpert"
    },
    default_route="GeneralSupport"
)
```

### RouterPattern Constructor

```python
RouterPattern(
    pattern_name: str,
    router_agent_name: str,
    routes: Dict[str, Union[str, BasePattern]],
    default_route: Optional[Union[str, BasePattern]] = None
)
```

**Parameters:**
- `pattern_name`: Unique identifier for the pattern
- `router_agent_name`: Name of the agent that decides the route
- `routes`: Dictionary mapping route keys to agent names or patterns
- `default_route`: Fallback agent/pattern if no route matches

### Router Agent Requirements

The router agent should return one of the route keys. For example:

```python
@app.agent(
    name="RequestClassifier",
    system_prompt="""Classify the user request into one of these categories:
    - technical: Technical issues and bugs
    - billing: Payment and subscription issues
    - account: Login and account management
    - general: Everything else
    
    Respond with ONLY the category name."""
)
```

## Discussion Pattern

Facilitate multi-round discussions between agents with optional moderation.

```python
from tframex import DiscussionPattern

# Basic discussion
pattern = DiscussionPattern(
    pattern_name="design_review",
    participant_agent_names=[
        "Architect",
        "Developer",
        "Designer", 
        "ProductManager"
    ],
    discussion_rounds=3
)

# With moderator
pattern = DiscussionPattern(
    pattern_name="moderated_debate",
    participant_agent_names=["Proponent", "Opponent"],
    moderator_agent_name="Moderator",
    discussion_rounds=5,
    stop_phrase="DISCUSSION_COMPLETE"
)
```

### DiscussionPattern Constructor

```python
DiscussionPattern(
    pattern_name: str,
    participant_agent_names: List[str],
    discussion_rounds: int = 1,
    moderator_agent_name: Optional[str] = None,
    stop_phrase: Optional[str] = None
)
```

**Parameters:**
- `pattern_name`: Unique identifier for the pattern
- `participant_agent_names`: List of agent names to participate
- `discussion_rounds`: Number of discussion rounds
- `moderator_agent_name`: Optional moderator agent
- `stop_phrase`: Optional phrase to end discussion early

### Discussion Flow

1. Each round, all participants respond to the current discussion state
2. If a moderator is specified, they summarize after each round
3. Discussion continues for the specified rounds or until stop phrase
4. Final output includes the complete discussion history

## Using Patterns in Flows

Patterns are typically used as steps within a Flow:

```python
from tframex import Flow, SequentialPattern, ParallelPattern

# Create patterns
analysis_pattern = ParallelPattern(
    pattern_name="analyze",
    tasks=["Analyst1", "Analyst2", "Analyst3"]
)

process_pattern = SequentialPattern(
    pattern_name="process",
    steps=["Processor", "Validator", "Finalizer"]
)

# Create flow with patterns
flow = Flow(
    flow_name="analyze_and_process",
    description="Analyze data then process results"
)
flow.add_step(analysis_pattern)
flow.add_step(process_pattern)

# Register and run
app.register_flow(flow)

async with app.run_context() as rt:
    result = await rt.run_flow(
        "analyze_and_process",
        initial_message
    )
```

## Nested Patterns

Patterns can be nested to create complex hierarchical workflows:

```python
# Create inner patterns
team_a = ParallelPattern(
    pattern_name="team_a_work",
    tasks=["A1", "A2", "A3"]
)

team_b = ParallelPattern(
    pattern_name="team_b_work", 
    tasks=["B1", "B2", "B3"]
)

review = DiscussionPattern(
    pattern_name="review_meeting",
    participant_agent_names=["TeamALead", "TeamBLead", "Manager"],
    discussion_rounds=2
)

# Create outer sequential pattern
project = SequentialPattern(
    pattern_name="project_flow",
    steps=[
        "ProjectPlanner",
        ParallelPattern(
            pattern_name="team_work",
            tasks=[team_a, team_b]
        ),
        "IntegrationAgent",
        review,
        "DeploymentAgent"
    ]
)
```

## Pattern Execution Context

Patterns receive and pass `FlowContext` objects containing:

```python
class FlowContext:
    initial_input: Message      # Original input message
    current_message: Message    # Current message in flow
    history: List[Message]      # All messages in execution
    shared_data: Dict[str, Any] # Shared data between steps
```

### Accessing Pattern Results

When patterns are used in parallel, results are indexed by pattern name:

```python
parallel_pattern = ParallelPattern(
    pattern_name="parallel_work",
    tasks=[
        SequentialPattern(pattern_name="flow_1", steps=["A", "B"]),
        SequentialPattern(pattern_name="flow_2", steps=["C", "D"])
    ]
)

# Results will include:
# {
#   "aggregated_content": "Combined summary...",
#   "task_results": {
#     "flow_1": "Result from flow_1",
#     "flow_2": "Result from flow_2"
#   }
# }
```

## Error Handling

Patterns handle errors by default, but you can implement custom handling:

```python
try:
    flow_context = await rt.run_flow("my_flow", message)
except Exception as e:
    # Handle pattern execution errors
    logger.error(f"Pattern failed: {e}")
```

## Pattern Guidelines

### Do's
- Keep patterns focused on a single collaboration strategy
- Use meaningful pattern and agent names
- Nest patterns for complex workflows
- Test patterns with various inputs
- Consider using `shared_data` for pattern coordination

### Don'ts
- Don't create overly complex single patterns
- Don't use patterns for simple single-agent tasks
- Don't create circular dependencies between patterns
- Don't ignore error handling

## Custom Patterns

You can create custom patterns by extending `BasePattern`:

```python
from tframex.patterns.patterns import BasePattern

class VotingPattern(BasePattern):
    """Custom pattern for voting scenarios."""
    
    def __init__(self, pattern_name: str, voters: List[str], threshold: float = 0.5):
        super().__init__(pattern_name)
        self.voters = voters
        self.threshold = threshold
    
    async def execute(
        self,
        flow_context: FlowContext,
        engine: Any,
        agent_call_kwargs: Optional[Dict[str, Any]] = None
    ) -> FlowContext:
        votes = []
        
        # Collect votes
        for voter in self.voters:
            response = await engine.call_agent(
                voter,
                flow_context.current_message,
                **(agent_call_kwargs or {})
            )
            votes.append(response)
        
        # Count positive votes
        positive = sum(1 for v in votes if "yes" in v.content.lower())
        passed = positive / len(votes) >= self.threshold
        
        # Update flow context
        result = Message(
            role="assistant",
            content=f"Vote {'passed' if passed else 'failed'}: {positive}/{len(votes)}"
        )
        flow_context.update_current_message(result)
        
        return flow_context
```

## Performance Considerations

1. **Parallel Execution**: ParallelPattern uses `asyncio.gather()` for true concurrent execution
2. **Memory Usage**: Large discussion patterns can accumulate significant history
3. **Nesting Depth**: Deeply nested patterns may impact performance
4. **Agent Reuse**: Agents are instantiated per execution context

## Examples

See the pattern examples in the repository:
- `/examples/02-pattern-examples/sequential-pattern/`
- `/examples/02-pattern-examples/parallel-pattern/`
- `/examples/02-pattern-examples/router-pattern/`
- `/examples/02-pattern-examples/discussion-pattern/`

## See Also

- [Flows](flows) - Flow orchestration system
- [Agents](agents) - Agent creation and configuration
- [Concepts: Patterns](../concepts/patterns) - Conceptual overview of patterns