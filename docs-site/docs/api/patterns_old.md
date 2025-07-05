---
sidebar_position: 6
title: Patterns
---

# Patterns API Reference

Patterns are pre-built, reusable flow templates that implement common multi-agent orchestration strategies. TFrameX provides several built-in patterns that can be customized for your specific use cases.

## Pattern Overview

All patterns inherit from the base Flow class and provide specialized orchestration logic:

```python
from tframex.patterns import (
    SequentialPattern,
    ParallelPattern,
    RouterPattern,
    DiscussionPattern,
    HierarchicalPattern,
    PipelinePattern,
    ConsensusPattern,
    MapReducePattern
)
```

## Sequential Pattern

Execute agents in a defined sequence with data flowing from one to the next.

```python
from tframex.patterns import SequentialPattern

# Basic sequential pattern
pattern = SequentialPattern(
    name="document_pipeline",
    agents=[
        ("Researcher", "Research topic: {topic}"),
        ("Writer", "Write based on research: {research}"),
        ("Editor", "Edit the document: {draft}"),
        ("Publisher", "Prepare for publication: {edited_doc}")
    ]
)

# Execute pattern
result = await runtime.run_pattern(pattern, topic="AI Ethics")
```

### Advanced Sequential Options

```python
# With step conditions
pattern = SequentialPattern(
    name="conditional_pipeline",
    agents=[
        ("Analyzer", "Analyze input: {data}"),
        ("ProcessorA", "Process type A: {analysis}", when="type=='A'"),
        ("ProcessorB", "Process type B: {analysis}", when="type=='B'"),
        ("Finalizer", "Finalize results: {processed}")
    ],
    skip_on_condition_fail=True
)

# With transformation functions
def transform_research(research_output):
    """Transform research into writer-friendly format."""
    return {
        "key_points": extract_key_points(research_output),
        "sources": extract_sources(research_output),
        "outline": generate_outline(research_output)
    }

pattern = SequentialPattern(
    name="transform_pipeline",
    agents=[
        ("Researcher", "Research: {topic}"),
        ("Writer", "Write article: {transformed_research}")
    ],
    transformations={
        "research": transform_research
    }
)

# With parallel sub-steps
pattern = SequentialPattern(
    name="mixed_pipeline",
    agents=[
        ("Planner", "Create plan: {goal}"),
        # Parallel execution within sequence
        [
            ("TaskA", "Execute task A: {plan}"),
            ("TaskB", "Execute task B: {plan}"),
            ("TaskC", "Execute task C: {plan}")
        ],
        ("Integrator", "Integrate results: {task_results}")
    ]
)
```

## Parallel Pattern

Execute multiple agents concurrently and aggregate their results.

```python
from tframex.patterns import ParallelPattern

# Basic parallel pattern
pattern = ParallelPattern(
    name="multi_perspective_analysis",
    agents=[
        ("TechnicalAnalyst", "Technical analysis: {data}"),
        ("BusinessAnalyst", "Business analysis: {data}"),
        ("LegalAnalyst", "Legal analysis: {data}"),
        ("RiskAnalyst", "Risk analysis: {data}")
    ],
    aggregation="merge"  # combine all results
)

result = await runtime.run_pattern(pattern, data=company_data)
```

### Aggregation Strategies

```python
# Voting aggregation
pattern = ParallelPattern(
    name="decision_making",
    agents=[
        ("Expert1", "Should we proceed? {proposal}"),
        ("Expert2", "Should we proceed? {proposal}"),
        ("Expert3", "Should we proceed? {proposal}")
    ],
    aggregation="vote",
    vote_threshold=0.66  # 2/3 majority needed
)

# Weighted aggregation
pattern = ParallelPattern(
    name="weighted_analysis",
    agents=[
        ("SeniorAnalyst", "Analyze: {data}", weight=0.5),
        ("MidAnalyst", "Analyze: {data}", weight=0.3),
        ("JuniorAnalyst", "Analyze: {data}", weight=0.2)
    ],
    aggregation="weighted"
)

# Custom aggregation function
def synthesize_analyses(results: List[Dict]) -> Dict:
    """Custom synthesis of multiple analyses."""
    return {
        "technical_score": results[0].get("score", 0),
        "business_score": results[1].get("score", 0),
        "combined_risk": calculate_combined_risk(results),
        "recommendation": generate_recommendation(results)
    }

pattern = ParallelPattern(
    name="custom_synthesis",
    agents=[...],
    aggregation="custom",
    custom_aggregator=synthesize_analyses
)

# Competitive aggregation (best result wins)
pattern = ParallelPattern(
    name="competitive_solving",
    agents=[
        ("Solver1", "Solve problem: {problem}"),
        ("Solver2", "Solve problem: {problem}"),
        ("Solver3", "Solve problem: {problem}")
    ],
    aggregation="best",
    scoring_function=lambda x: x.get("confidence", 0)
)
```

## Router Pattern

Route requests to appropriate agents based on conditions.

```python
from tframex.patterns import RouterPattern

# Basic routing
pattern = RouterPattern(
    name="support_router",
    classifier="RequestClassifier",
    routes={
        "technical": "TechnicalSupport",
        "billing": "BillingSupport",
        "account": "AccountSupport",
        "general": "GeneralSupport"
    },
    default_route="GeneralSupport"
)

result = await runtime.run_pattern(
    pattern,
    request="I can't log into my account"
)
# Routes to AccountSupport
```

### Advanced Routing

```python
# Multi-level routing
pattern = RouterPattern(
    name="hierarchical_router",
    classifier="PrimaryClassifier",
    routes={
        "technical": RouterPattern(
            name="technical_subrouter",
            classifier="TechnicalClassifier",
            routes={
                "hardware": "HardwareExpert",
                "software": "SoftwareExpert",
                "network": "NetworkExpert"
            }
        ),
        "business": RouterPattern(
            name="business_subrouter",
            classifier="BusinessClassifier",
            routes={
                "sales": "SalesTeam",
                "marketing": "MarketingTeam",
                "strategy": "StrategyTeam"
            }
        )
    }
)

# Conditional routing with metadata
pattern = RouterPattern(
    name="priority_router",
    classifier="PriorityClassifier",
    classification_prompt="""Classify this request:
    Priority: (high/medium/low)
    Category: (technical/business/support)
    Complexity: (simple/moderate/complex)
    
    Request: {request}""",
    routes={
        "high_technical_complex": "SeniorEngineer",
        "high_technical_*": "Engineer",
        "high_*_*": "SeniorStaff",
        "*_*_simple": "JuniorStaff",
        "*_*_*": "GeneralStaff"
    },
    route_extractor=lambda x: f"{x['priority']}_{x['category']}_{x['complexity']}"
)

# Load-balanced routing
pattern = RouterPattern(
    name="load_balancer",
    classifier="LoadBalancer",
    routes={
        "worker": ["Worker1", "Worker2", "Worker3"]  # Round-robin
    },
    load_balance=True
)
```

## Discussion Pattern

Facilitate multi-agent discussions to reach consensus.

```python
from tframex.patterns import DiscussionPattern

# Basic discussion
pattern = DiscussionPattern(
    name="design_review",
    participants=[
        "Architect",
        "Developer", 
        "Designer",
        "ProductManager"
    ],
    moderator="TechLead",
    max_rounds=5,
    consensus_threshold=0.8
)

result = await runtime.run_pattern(
    pattern,
    topic="Should we migrate to microservices?"
)
```

### Discussion Formats

```python
# Structured debate
pattern = DiscussionPattern(
    name="structured_debate",
    participants=["Proponent", "Opponent"],
    moderator="Moderator",
    format="debate",
    rounds=[
        {"speaker": "Proponent", "duration": 2},
        {"speaker": "Opponent", "duration": 2},
        {"speaker": "Proponent", "duration": 1},
        {"speaker": "Opponent", "duration": 1},
        {"type": "open_floor", "duration": 3}
    ]
)

# Iterative refinement
pattern = DiscussionPattern(
    name="document_refinement",
    participants=["Writer", "Editor", "Reviewer"],
    format="iterative",
    artifact_type="document",
    max_iterations=3,
    improvement_metric=lambda old, new: calculate_quality_score(new) > calculate_quality_score(old)
)

# Brainstorming session
pattern = DiscussionPattern(
    name="brainstorming",
    participants=["Creative1", "Creative2", "Creative3"],
    format="brainstorm",
    phases=[
        ("divergent", 10),  # Generate ideas for 10 turns
        ("convergent", 5)   # Refine and select for 5 turns
    ],
    idea_synthesis="AI_Synthesizer"
)

# Council decision
pattern = DiscussionPattern(
    name="council_decision",
    participants=[
        ("Elder1", "senior", 2.0),  # Role, seniority, vote weight
        ("Elder2", "senior", 2.0),
        ("Member1", "regular", 1.0),
        ("Member2", "regular", 1.0),
        ("Advisor", "advisory", 0.5)
    ],
    format="council",
    decision_method="weighted_vote"
)
```

## Hierarchical Pattern

Implement supervisor-worker hierarchies.

```python
from tframex.patterns import HierarchicalPattern

# Basic hierarchy
pattern = HierarchicalPattern(
    name="company_hierarchy",
    structure={
        "CEO": {
            "CTO": ["TechLead", "Architect"],
            "CFO": ["Controller", "Treasurer"],
            "CMO": ["BrandManager", "GrowthManager"]
        }
    },
    delegation_strategy="capability_based"
)

# Execute with task
result = await runtime.run_pattern(
    pattern,
    task="Develop a new product strategy",
    start_level="CEO"
)
```

### Advanced Hierarchies

```python
# Multi-level with specialized routing
pattern = HierarchicalPattern(
    name="support_hierarchy",
    structure={
        "SupportDirector": {
            "L3Manager": {
                "SeniorL3": ["NetworkExpert", "SystemExpert"],
                "JuniorL3": ["GeneralistL3"]
            },
            "L2Manager": {
                "L2Lead": ["L2Tech1", "L2Tech2", "L2Tech3"]
            },
            "L1Manager": {
                "L1Supervisor": ["L1Agent1", "L1Agent2", "L1Agent3", "L1Agent4"]
            }
        }
    },
    escalation_rules={
        "complexity": {
            "high": "L3Manager",
            "medium": "L2Manager", 
            "low": "L1Manager"
        },
        "priority": {
            "critical": "SupportDirector",
            "high": "L3Manager",
            "normal": "L2Manager"
        }
    }
)

# Department-based hierarchy
pattern = HierarchicalPattern(
    name="department_hierarchy",
    structure={
        "President": {
            "Engineering": {
                "Backend": ["API_Team", "Database_Team"],
                "Frontend": ["Web_Team", "Mobile_Team"],
                "QA": ["AutomationQA", "ManualQA"]
            },
            "Product": {
                "ProductManagement": ["PM1", "PM2"],
                "ProductDesign": ["UX_Team", "UI_Team"]
            },
            "Operations": {
                "Infrastructure": ["Cloud_Team", "Security_Team"],
                "Support": ["CustomerSuccess", "TechnicalSupport"]
            }
        }
    },
    communication_style="chain_of_command"  # or "direct", "matrix"
)
```

## Pipeline Pattern

Process data through a series of transformation stages.

```python
from tframex.patterns import PipelinePattern

# Data processing pipeline
pattern = PipelinePattern(
    name="data_pipeline",
    stages=[
        ("Extractor", "Extract data from: {source}"),
        ("Validator", "Validate: {extracted_data}"),
        ("Transformer", "Transform: {validated_data}"),
        ("Enricher", "Enrich: {transformed_data}"),
        ("Loader", "Load to destination: {enriched_data}")
    ],
    error_handling="skip"  # or "abort", "retry"
)
```

### Advanced Pipelines

```python
# Conditional pipeline stages
pattern = PipelinePattern(
    name="conditional_pipeline",
    stages=[
        ("Ingester", "Ingest: {input}"),
        {
            "condition": "data_type == 'structured'",
            "true": ("StructuredProcessor", "Process structured: {data}"),
            "false": ("UnstructuredProcessor", "Process unstructured: {data}")
        },
        ("Quality", "Check quality: {processed}"),
        {
            "condition": "quality_score < 0.8",
            "true": [
                ("Enhancer", "Enhance: {data}"),
                ("ReChecker", "Re-check: {enhanced}")
            ]
        },
        ("Finalizer", "Finalize: {data}")
    ]
)

# Pipeline with parallel stages
pattern = PipelinePattern(
    name="parallel_pipeline",
    stages=[
        ("Reader", "Read: {file}"),
        # Parallel processing
        [
            ("Analyzer1", "Analyze aspect 1: {content}"),
            ("Analyzer2", "Analyze aspect 2: {content}"),
            ("Analyzer3", "Analyze aspect 3: {content}")
        ],
        ("Synthesizer", "Synthesize analyses: {analyses}"),
        ("Reporter", "Generate report: {synthesis}")
    ],
    stream_processing=True  # Process items as they complete
)

# Pipeline with caching
pattern = PipelinePattern(
    name="cached_pipeline",
    stages=[
        ("Fetcher", "Fetch: {url}", cache_ttl=3600),
        ("Parser", "Parse: {content}", cache_ttl=1800),
        ("Analyzer", "Analyze: {parsed}", cache_ttl=900),
        ("Formatter", "Format: {analysis}")  # No cache
    ],
    cache_backend="redis"
)
```

## Consensus Pattern

Achieve agreement among multiple agents.

```python
from tframex.patterns import ConsensusPattern

# Basic consensus
pattern = ConsensusPattern(
    name="investment_decision",
    agents=[
        "InvestmentAnalyst1",
        "InvestmentAnalyst2", 
        "InvestmentAnalyst3",
        "RiskAnalyst",
        "MarketAnalyst"
    ],
    consensus_method="majority",
    min_agreement=0.6  # 60% must agree
)
```

### Consensus Methods

```python
# Weighted consensus
pattern = ConsensusPattern(
    name="expert_consensus",
    agents=[
        ("SeniorExpert", 0.4),
        ("Expert1", 0.2),
        ("Expert2", 0.2),
        ("JuniorExpert", 0.1),
        ("ExternalAdvisor", 0.1)
    ],
    consensus_method="weighted",
    threshold=0.7
)

# Iterative consensus (Delphi method)
pattern = ConsensusPattern(
    name="delphi_consensus",
    agents=["Expert1", "Expert2", "Expert3", "Expert4"],
    consensus_method="delphi",
    max_rounds=3,
    anonymize_responses=True,
    convergence_threshold=0.85
)

# Ranked choice consensus
pattern = ConsensusPattern(
    name="ranked_choice",
    agents=["Voter1", "Voter2", "Voter3", "Voter4", "Voter5"],
    consensus_method="ranked_choice",
    options=["Option A", "Option B", "Option C", "Option D"],
    elimination_rounds=True
)

# Byzantine consensus (fault-tolerant)
pattern = ConsensusPattern(
    name="byzantine_consensus",
    agents=["Node1", "Node2", "Node3", "Node4", "Node5", "Node6", "Node7"],
    consensus_method="byzantine",
    fault_tolerance=2,  # Tolerate up to 2 faulty agents
    verification_rounds=3
)
```

## MapReduce Pattern

Distribute work across agents and aggregate results.

```python
from tframex.patterns import MapReducePattern

# Basic map-reduce
pattern = MapReducePattern(
    name="document_analysis",
    mapper="DocumentAnalyzer",
    reducer="AnalysisAggregator",
    num_workers=5,
    chunk_size=10
)

# Process large dataset
result = await runtime.run_pattern(
    pattern,
    data=large_document_list
)
```

### Advanced MapReduce

```python
# Custom partitioning
def partition_by_type(data):
    """Partition data by document type."""
    partitions = {}
    for item in data:
        doc_type = item.get("type", "unknown")
        if doc_type not in partitions:
            partitions[doc_type] = []
        partitions[doc_type].append(item)
    return partitions

pattern = MapReducePattern(
    name="typed_analysis",
    mappers={
        "pdf": "PDFAnalyzer",
        "doc": "DocAnalyzer",
        "txt": "TextAnalyzer",
        "unknown": "GeneralAnalyzer"
    },
    reducer="TypedAggregator",
    partitioner=partition_by_type
)

# Multi-stage map-reduce
pattern = MapReducePattern(
    name="multi_stage",
    stages=[
        {
            "name": "initial_processing",
            "mapper": "InitialProcessor",
            "reducer": "InitialAggregator",
            "num_workers": 10
        },
        {
            "name": "deep_analysis", 
            "mapper": "DeepAnalyzer",
            "reducer": "DeepAggregator",
            "num_workers": 5
        },
        {
            "name": "final_synthesis",
            "mapper": "Synthesizer",
            "reducer": "FinalAggregator",
            "num_workers": 3
        }
    ]
)

# Stream processing map-reduce
pattern = MapReducePattern(
    name="stream_processing",
    mapper="StreamProcessor",
    reducer="StreamAggregator",
    streaming=True,
    window_size=100,  # Process in windows of 100 items
    emit_partial=True  # Emit partial results
)
```

## Custom Pattern Creation

Create your own patterns by extending the base classes:

```python
from tframex.patterns.base import Pattern

class RetryPattern(Pattern):
    """Pattern that retries failed operations with different agents."""
    
    def __init__(
        self,
        name: str,
        agents: List[str],
        max_attempts: int = 3,
        backoff_factor: float = 2.0
    ):
        super().__init__(name)
        self.agents = agents
        self.max_attempts = max_attempts
        self.backoff_factor = backoff_factor
    
    async def execute(self, runtime: Runtime, task: str) -> Dict:
        last_error = None
        wait_time = 1.0
        
        for attempt in range(self.max_attempts):
            for agent in self.agents:
                try:
                    result = await runtime.call_agent(agent, task)
                    return {
                        "success": True,
                        "result": result,
                        "attempts": attempt + 1,
                        "agent": agent
                    }
                except Exception as e:
                    last_error = e
                    logger.warning(f"Agent {agent} failed: {e}")
            
            if attempt < self.max_attempts - 1:
                await asyncio.sleep(wait_time)
                wait_time *= self.backoff_factor
        
        return {
            "success": False,
            "error": str(last_error),
            "attempts": self.max_attempts
        }

# Use custom pattern
pattern = RetryPattern(
    name="resilient_execution",
    agents=["PrimaryAgent", "BackupAgent", "EmergencyAgent"],
    max_attempts=3
)
```

## Pattern Composition

Combine patterns for complex workflows:

```python
# Nested patterns
analysis_pattern = ParallelPattern(
    name="analysis",
    agents=["Analyst1", "Analyst2", "Analyst3"]
)

decision_pattern = ConsensusPattern(
    name="decision",
    agents=["Decider1", "Decider2", "Decider3"]
)

main_pattern = SequentialPattern(
    name="analyze_and_decide",
    stages=[
        ("DataCollector", "Collect data: {request}"),
        (analysis_pattern, "{collected_data}"),
        (decision_pattern, "{analysis_results}"),
        ("Executor", "Execute decision: {consensus}")
    ]
)

# Dynamic pattern selection
class AdaptivePattern(Pattern):
    """Pattern that selects sub-patterns based on context."""
    
    async def execute(self, runtime: Runtime, context: Dict) -> Dict:
        # Analyze context
        analysis = await runtime.call_agent(
            "ContextAnalyzer",
            f"Analyze context: {context}"
        )
        
        # Select appropriate pattern
        if "urgent" in analysis:
            pattern = ParallelPattern(
                name="urgent_response",
                agents=["FastAgent1", "FastAgent2"]
            )
        elif "complex" in analysis:
            pattern = HierarchicalPattern(
                name="complex_handling",
                structure={...}
            )
        else:
            pattern = SequentialPattern(
                name="standard_flow",
                agents=[...]
            )
        
        # Execute selected pattern
        return await runtime.run_pattern(pattern, context)
```

## Performance Considerations

### Pattern Caching

```python
from functools import lru_cache

class CachedPattern(Pattern):
    """Pattern with result caching."""
    
    @lru_cache(maxsize=100)
    async def execute_cached(self, runtime: Runtime, task_hash: str) -> Dict:
        # Execute expensive pattern
        return await self.base_pattern.execute(runtime, task_hash)
    
    async def execute(self, runtime: Runtime, task: Dict) -> Dict:
        # Create hash of task
        task_hash = hashlib.md5(
            json.dumps(task, sort_keys=True).encode()
        ).hexdigest()
        
        return await self.execute_cached(runtime, task_hash)
```

### Resource Management

```python
class ResourceAwarePattern(Pattern):
    """Pattern that manages resource usage."""
    
    def __init__(self, *args, max_memory_mb: int = 1000, **kwargs):
        super().__init__(*args, **kwargs)
        self.max_memory = max_memory_mb * 1024 * 1024
    
    async def execute(self, runtime: Runtime, task: Dict) -> Dict:
        # Monitor memory usage
        import psutil
        process = psutil.Process()
        
        if process.memory_info().rss > self.max_memory:
            # Trigger garbage collection
            import gc
            gc.collect()
            
            # If still over limit, use memory-efficient approach
            if process.memory_info().rss > self.max_memory:
                return await self.execute_low_memory(runtime, task)
        
        return await self.execute_normal(runtime, task)
```

## Testing Patterns

```python
import pytest
from tframex.testing import PatternTestKit

@pytest.fixture
def test_pattern():
    return SequentialPattern(
        name="test_pattern",
        agents=[
            ("Agent1", "Step 1: {input}"),
            ("Agent2", "Step 2: {step1_result}")
        ]
    )

async def test_pattern_execution(test_pattern):
    kit = PatternTestKit()
    
    # Mock agents
    kit.mock_agent("Agent1", response="Result 1")
    kit.mock_agent("Agent2", response="Result 2")
    
    # Execute pattern
    result = await kit.run_pattern(
        test_pattern,
        input="Test input"
    )
    
    # Verify execution
    assert result["final_output"] == "Result 2"
    assert kit.agent_called("Agent1", times=1)
    assert kit.agent_called("Agent2", times=1)

async def test_pattern_error_handling(test_pattern):
    kit = PatternTestKit()
    
    # Mock failing agent
    kit.mock_agent("Agent1", should_fail=True)
    
    # Test error handling
    with pytest.raises(PatternExecutionError):
        await kit.run_pattern(test_pattern, input="Test")
```

## Best Practices

1. **Choose the Right Pattern** - Select patterns that match your use case
2. **Keep It Simple** - Don't over-engineer; use the simplest pattern that works
3. **Error Handling** - Always implement proper error handling
4. **Testing** - Test patterns with various inputs and edge cases
5. **Documentation** - Document pattern configuration and usage
6. **Performance** - Consider caching and resource usage
7. **Modularity** - Build reusable pattern components
8. **Monitoring** - Add logging and metrics to patterns
9. **Flexibility** - Design patterns to be configurable
10. **Composition** - Combine simple patterns for complex workflows

## See Also

- [Flows](flows) - Base flow system
- [Agents](agents) - Agents used in patterns
- [Examples](../examples/pattern-examples) - Pattern implementation examples
- [Best Practices](../guides/pattern-best-practices) - Pattern design guidelines