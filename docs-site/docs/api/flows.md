---
sidebar_position: 5
title: Flows
---

# Flows API Reference

Flows enable complex multi-agent orchestration by defining how agents work together. This reference covers flow creation, execution, and advanced patterns.

## Base Flow Class

All flows inherit from the base `Flow` class:

```python
from tframex.flows.base import Flow, FlowResult

class Flow:
    def __init__(
        self,
        name: str,
        description: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Base flow class.
        
        Args:
            name: Unique flow identifier
            description: Human-readable description
            metadata: Additional metadata
        """
    
    async def run(
        self,
        runtime: Runtime,
        initial_input: Optional[Dict[str, Any]] = None
    ) -> FlowResult:
        """Execute the flow."""
        pass
```

### FlowResult

```python
class FlowResult:
    """Result of flow execution."""
    
    def __init__(
        self,
        final_output: Any,
        intermediate_results: List[Dict[str, Any]],
        metadata: Dict[str, Any]
    ):
        self.final_output = final_output
        self.intermediate_results = intermediate_results
        self.metadata = metadata
        self.execution_time = metadata.get("execution_time", 0)
        self.success = metadata.get("success", True)
```

## Sequential Flow

Execute agents in sequence, passing output from one to the next.

```python
from tframex.flows import SequentialFlow

flow = SequentialFlow(
    name="content_pipeline",
    description="Research and write content",
    steps=[
        ("Researcher", "Research the topic: {topic}"),
        ("Writer", "Write an article based on this research: {research_result}"),
        ("Editor", "Edit and improve this article: {article_draft}")
    ]
)

# Execute flow
async with app.run_context() as rt:
    result = await rt.run_flow(flow, topic="AI in healthcare")
    print(result.final_output)  # Edited article
```

### Advanced Sequential Flow

```python
# With error handling
flow = SequentialFlow(
    name="safe_pipeline",
    description="Pipeline with error handling",
    steps=[
        ("Validator", "Validate input: {data}"),
        ("Processor", "Process: {validated_data}"),
        ("Reporter", "Generate report: {processed_data}")
    ],
    on_error="continue",  # or "stop"
    error_handler=lambda e, step: f"Error at {step}: {e}"
)

# With conditional steps
flow = SequentialFlow(
    name="conditional_flow",
    steps=[
        ("Analyzer", "Analyze: {input}"),
        ("Router", "Determine path: {analysis}"),
        # Step executed conditionally based on router output
        ("SpecialistA", "Process type A: {data}", condition="type_a"),
        ("SpecialistB", "Process type B: {data}", condition="type_b")
    ]
)

# With step configuration
flow = SequentialFlow(
    name="configured_pipeline",
    steps=[
        {
            "agent": "Researcher",
            "prompt": "Research: {topic}",
            "timeout": 30,
            "retries": 3
        },
        {
            "agent": "Writer",
            "prompt": "Write: {research}",
            "min_length": 500,
            "max_length": 2000
        }
    ]
)
```

## Parallel Flow

Execute multiple agents concurrently.

```python
from tframex.flows import ParallelFlow

flow = ParallelFlow(
    name="multi_analysis",
    description="Analyze data from multiple perspectives",
    agents=[
        ("TechnicalAnalyst", "Analyze technical aspects: {data}"),
        ("BusinessAnalyst", "Analyze business impact: {data}"),
        ("RiskAnalyst", "Analyze risks: {data}")
    ],
    aggregation_method="combine"  # or "vote", "merge", "custom"
)

# Execute parallel flow
result = await rt.run_flow(flow, data=dataset)
# Result contains all three analyses
```

### Aggregation Methods

```python
# Voting aggregation
flow = ParallelFlow(
    name="consensus_flow",
    agents=[
        ("Expert1", "Evaluate: {proposal}"),
        ("Expert2", "Evaluate: {proposal}"),
        ("Expert3", "Evaluate: {proposal}")
    ],
    aggregation_method="vote",
    vote_threshold=0.6  # 60% agreement needed
)

# Custom aggregation
def custom_aggregator(results: List[str]) -> str:
    # Custom logic to combine results
    scores = []
    for result in results:
        score = extract_score(result)
        scores.append(score)
    
    return {
        "average_score": sum(scores) / len(scores),
        "individual_scores": scores,
        "consensus": max(set(scores), key=scores.count)
    }

flow = ParallelFlow(
    name="custom_aggregation",
    agents=[...],
    aggregation_method="custom",
    custom_aggregator=custom_aggregator
)
```

## Router Flow

Route to different agents based on conditions.

```python
from tframex.flows import RouterFlow

flow = RouterFlow(
    name="support_router",
    description="Route customer queries",
    router_agent="QueryClassifier",
    router_prompt="Classify this query and route appropriately: {query}",
    routes={
        "technical": "TechnicalSupport",
        "billing": "BillingSupport",
        "general": "GeneralSupport"
    },
    default_route="GeneralSupport"
)

# Execute router flow
result = await rt.run_flow(flow, query="My invoice is incorrect")
# Routes to BillingSupport
```

### Advanced Routing

```python
# Multi-criteria routing
flow = RouterFlow(
    name="advanced_router",
    router_agent="SmartRouter",
    router_prompt="""Analyze this request and determine:
    1. Category (technical/business/legal)
    2. Priority (high/medium/low)
    3. Complexity (simple/moderate/complex)
    
    Request: {request}""",
    routes={
        "technical_high_complex": "SeniorEngineer",
        "technical_high_simple": "JuniorEngineer",
        "business_high_*": "BusinessLead",
        "legal_*_*": "LegalTeam",
        "*_low_simple": "InternTeam"
    },
    route_extractor=lambda response: extract_route_key(response)
)

# Probability-based routing
flow = RouterFlow(
    name="probability_router",
    router_agent="ProbabilityRouter",
    routes={
        "path_a": ("AgentA", 0.7),  # 70% confidence threshold
        "path_b": ("AgentB", 0.8),  # 80% confidence threshold
        "path_c": ("AgentC", 0.6)   # 60% confidence threshold
    },
    use_probability=True
)
```

## Discussion Flow

Multiple agents discuss and reach consensus.

```python
from tframex.flows import DiscussionFlow

flow = DiscussionFlow(
    name="design_discussion",
    description="Discuss system design",
    participants=[
        "Architect",
        "Developer",
        "SecurityExpert",
        "QAEngineer"
    ],
    max_rounds=5,
    consensus_threshold=0.8,
    moderator="TechLead"
)

# Execute discussion
result = await rt.run_flow(
    flow,
    topic="Design a scalable microservices architecture"
)
print(result.final_output)  # Consensus design
```

### Discussion Configuration

```python
# Structured discussion
flow = DiscussionFlow(
    name="structured_debate",
    participants=["Proponent", "Opponent", "Neutral"],
    discussion_format="debate",
    rounds=[
        {"speaker": "Proponent", "time": 2},
        {"speaker": "Opponent", "time": 2},
        {"speaker": "Neutral", "time": 1},
        {"type": "open_discussion", "time": 3}
    ],
    summarizer="Moderator"
)

# Iterative refinement
flow = DiscussionFlow(
    name="document_review",
    participants=["Writer", "Editor", "FactChecker"],
    discussion_type="iterative",
    artifact_type="document",
    max_iterations=3,
    improvement_threshold=0.9
)
```

## Custom Flow Implementation

Create custom flows by extending the base class:

```python
from tframex.flows.base import Flow, FlowResult

class IterativeFlow(Flow):
    """Flow that iterates until a condition is met."""
    
    def __init__(
        self,
        name: str,
        description: str,
        agent: str,
        condition_checker: str,
        max_iterations: int = 10
    ):
        super().__init__(name, description)
        self.agent = agent
        self.condition_checker = condition_checker
        self.max_iterations = max_iterations
    
    async def run(
        self,
        runtime: Runtime,
        initial_input: Optional[Dict[str, Any]] = None
    ) -> FlowResult:
        current_input = initial_input
        intermediate_results = []
        
        for i in range(self.max_iterations):
            # Execute main agent
            result = await runtime.call_agent(
                self.agent,
                f"Process iteration {i+1}: {current_input}"
            )
            
            intermediate_results.append({
                "iteration": i + 1,
                "result": result
            })
            
            # Check condition
            condition_met = await runtime.call_agent(
                self.condition_checker,
                f"Is this result satisfactory? {result}"
            )
            
            if "yes" in condition_met.lower():
                break
            
            current_input = result
        
        return FlowResult(
            final_output=result,
            intermediate_results=intermediate_results,
            metadata={
                "iterations": i + 1,
                "success": True
            }
        )

# Use custom flow
flow = IterativeFlow(
    name="refinement_flow",
    description="Iteratively refine output",
    agent="Writer",
    condition_checker="QualityChecker",
    max_iterations=5
)
```

## Flow Composition

### Nested Flows

```python
# Sub-flow for research
research_flow = SequentialFlow(
    name="research_subflow",
    steps=[
        ("WebSearcher", "Search for: {topic}"),
        ("Summarizer", "Summarize findings: {search_results}")
    ]
)

# Sub-flow for writing
writing_flow = SequentialFlow(
    name="writing_subflow",
    steps=[
        ("OutlineWriter", "Create outline: {research}"),
        ("ContentWriter", "Write content: {outline}"),
        ("Editor", "Edit content: {draft}")
    ]
)

# Main flow composing sub-flows
main_flow = SequentialFlow(
    name="content_creation",
    steps=[
        (research_flow, "{topic}"),
        (writing_flow, "{research_output}")
    ]
)
```

### Dynamic Flow Generation

```python
class DynamicFlowBuilder:
    """Build flows based on runtime conditions."""
    
    @staticmethod
    def build_analysis_flow(data_type: str) -> Flow:
        if data_type == "financial":
            return SequentialFlow(
                name="financial_analysis",
                steps=[
                    ("FinancialValidator", "Validate: {data}"),
                    ("FinancialAnalyst", "Analyze: {validated_data}"),
                    ("RiskAssessor", "Assess risks: {analysis}")
                ]
            )
        elif data_type == "marketing":
            return ParallelFlow(
                name="marketing_analysis",
                agents=[
                    ("TrendAnalyst", "Analyze trends: {data}"),
                    ("CompetitorAnalyst", "Analyze competition: {data}"),
                    ("CustomerAnalyst", "Analyze customers: {data}")
                ]
            )
        else:
            return SequentialFlow(
                name="generic_analysis",
                steps=[("GeneralAnalyst", "Analyze: {data}")]
            )

# Use dynamic flow
data_type = detect_data_type(data)
flow = DynamicFlowBuilder.build_analysis_flow(data_type)
result = await rt.run_flow(flow, data=data)
```

## Flow Control

### Conditional Execution

```python
class ConditionalFlow(Flow):
    """Flow with conditional branching."""
    
    async def run(self, runtime: Runtime, initial_input: dict) -> FlowResult:
        # Initial assessment
        assessment = await runtime.call_agent(
            "Assessor",
            f"Assess this input: {initial_input}"
        )
        
        # Conditional branching
        if "urgent" in assessment:
            result = await runtime.call_agent(
                "UrgentHandler",
                f"Handle urgent case: {initial_input}"
            )
        elif "complex" in assessment:
            # Run complex flow
            complex_flow = ParallelFlow(
                name="complex_handler",
                agents=["Expert1", "Expert2", "Expert3"]
            )
            result = await runtime.run_flow(complex_flow, initial_input)
        else:
            result = await runtime.call_agent(
                "StandardHandler",
                f"Handle standard case: {initial_input}"
            )
        
        return FlowResult(
            final_output=result,
            intermediate_results=[{"assessment": assessment}],
            metadata={"path_taken": extract_path(assessment)}
        )
```

### Loop Control

```python
class LoopFlow(Flow):
    """Flow with loop control."""
    
    async def run(self, runtime: Runtime, initial_input: dict) -> FlowResult:
        results = []
        
        # For loop
        for item in initial_input.get("items", []):
            result = await runtime.call_agent(
                "ItemProcessor",
                f"Process: {item}"
            )
            results.append(result)
        
        # While loop with condition
        quality_score = 0
        attempts = 0
        while quality_score < 0.8 and attempts < 5:
            output = await runtime.call_agent(
                "Generator",
                "Generate high-quality output"
            )
            
            score_response = await runtime.call_agent(
                "QualityScorer",
                f"Score this output: {output}"
            )
            
            quality_score = extract_score(score_response)
            attempts += 1
        
        return FlowResult(
            final_output={"processed_items": results, "final_output": output},
            intermediate_results=results,
            metadata={"attempts": attempts, "final_score": quality_score}
        )
```

## Error Handling

### Flow-Level Error Handling

```python
flow = SequentialFlow(
    name="robust_flow",
    steps=[...],
    error_handling={
        "strategy": "retry",  # or "skip", "fallback", "fail"
        "max_retries": 3,
        "retry_delay": 2.0,
        "fallback_agent": "ErrorHandler",
        "log_errors": True
    }
)

# Custom error handler
async def custom_error_handler(error: Exception, context: dict) -> str:
    if isinstance(error, TimeoutError):
        return await runtime.call_agent(
            "TimeoutHandler",
            f"Handle timeout for: {context}"
        )
    else:
        return f"Error occurred: {error}"

flow = SequentialFlow(
    name="custom_error_flow",
    steps=[...],
    error_handler=custom_error_handler
)
```

### Recovery Strategies

```python
class RecoverableFlow(Flow):
    """Flow with recovery mechanisms."""
    
    async def run(self, runtime: Runtime, initial_input: dict) -> FlowResult:
        checkpoint = None
        
        try:
            # Step 1 with checkpoint
            result1 = await runtime.call_agent("Step1", "...")
            checkpoint = {"step": 1, "result": result1}
            
            # Step 2 with potential failure
            result2 = await runtime.call_agent("Step2", "...")
            checkpoint = {"step": 2, "result": result2}
            
            # Step 3
            result3 = await runtime.call_agent("Step3", "...")
            
            return FlowResult(
                final_output=result3,
                intermediate_results=[result1, result2, result3],
                metadata={"success": True}
            )
            
        except Exception as e:
            # Recover from checkpoint
            if checkpoint:
                recovery_result = await runtime.call_agent(
                    "RecoveryAgent",
                    f"Recover from: {checkpoint}"
                )
                return FlowResult(
                    final_output=recovery_result,
                    intermediate_results=[checkpoint],
                    metadata={"recovered": True, "error": str(e)}
                )
            else:
                raise
```

## Performance Optimization

### Caching Flow Results

```python
from functools import lru_cache
import hashlib

class CachedFlow(Flow):
    """Flow with result caching."""
    
    def __init__(self, base_flow: Flow, cache_ttl: int = 3600):
        super().__init__(
            name=f"cached_{base_flow.name}",
            description=f"Cached version of {base_flow.name}"
        )
        self.base_flow = base_flow
        self.cache_ttl = cache_ttl
        self._cache = {}
    
    async def run(self, runtime: Runtime, initial_input: dict) -> FlowResult:
        # Generate cache key
        cache_key = hashlib.md5(
            json.dumps(initial_input, sort_keys=True).encode()
        ).hexdigest()
        
        # Check cache
        if cache_key in self._cache:
            cached_result, timestamp = self._cache[cache_key]
            if time.time() - timestamp < self.cache_ttl:
                return cached_result
        
        # Execute flow
        result = await self.base_flow.run(runtime, initial_input)
        
        # Cache result
        self._cache[cache_key] = (result, time.time())
        
        return result
```

### Parallel Execution Optimization

```python
class OptimizedParallelFlow(ParallelFlow):
    """Parallel flow with resource optimization."""
    
    def __init__(self, *args, max_concurrent: int = 10, **kwargs):
        super().__init__(*args, **kwargs)
        self.semaphore = asyncio.Semaphore(max_concurrent)
    
    async def run(self, runtime: Runtime, initial_input: dict) -> FlowResult:
        async def run_with_limit(agent, prompt):
            async with self.semaphore:
                return await runtime.call_agent(agent, prompt)
        
        # Execute with concurrency limit
        tasks = [
            run_with_limit(agent, prompt.format(**initial_input))
            for agent, prompt in self.agents
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Handle results
        successful_results = [
            r for r in results if not isinstance(r, Exception)
        ]
        
        return FlowResult(
            final_output=self.aggregate(successful_results),
            intermediate_results=results,
            metadata={
                "successful": len(successful_results),
                "failed": len(results) - len(successful_results)
            }
        )
```

## Testing Flows

```python
import pytest
from tframex.testing import FlowTestHarness, MockAgent

@pytest.fixture
def test_flow():
    return SequentialFlow(
        name="test_flow",
        steps=[
            ("Agent1", "Process: {input}"),
            ("Agent2", "Enhance: {result1}"),
            ("Agent3", "Finalize: {result2}")
        ]
    )

async def test_flow_execution(test_flow):
    harness = FlowTestHarness()
    
    # Mock agents
    harness.add_mock_agent(MockAgent(
        name="Agent1",
        responses=["Processed data"]
    ))
    harness.add_mock_agent(MockAgent(
        name="Agent2",
        responses=["Enhanced data"]
    ))
    harness.add_mock_agent(MockAgent(
        name="Agent3",
        responses=["Final result"]
    ))
    
    # Execute flow
    result = await harness.run_flow(
        test_flow,
        initial_input={"input": "test data"}
    )
    
    # Verify results
    assert result.final_output == "Final result"
    assert len(result.intermediate_results) == 3
    assert result.success

async def test_flow_error_handling(test_flow):
    harness = FlowTestHarness()
    
    # Mock agent that fails
    harness.add_mock_agent(MockAgent(
        name="Agent1",
        should_fail=True,
        error_message="Simulated failure"
    ))
    
    # Test error handling
    with pytest.raises(FlowExecutionError):
        await harness.run_flow(test_flow, {"input": "test"})
```

## Best Practices

1. **Clear Flow Names** - Use descriptive, unique names
2. **Error Handling** - Always implement error handling
3. **Logging** - Add comprehensive logging
4. **Testing** - Test flows with various inputs
5. **Documentation** - Document flow purpose and requirements
6. **Modularity** - Build reusable sub-flows
7. **Performance** - Consider caching and parallelism
8. **Monitoring** - Track flow execution metrics
9. **Versioning** - Version flows for compatibility
10. **Simplicity** - Keep flows as simple as possible

## See Also

- [Patterns](patterns) - Pre-built flow patterns
- [Agents](agents) - Agents used in flows
- [Examples](../examples/flow-examples) - Flow implementation examples
- [Best Practices](../guides/flow-best-practices) - Flow design guidelines