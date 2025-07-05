---
sidebar_position: 5
title: Patterns
---

# Patterns

Patterns are reusable workflow templates in TFrameX that solve common multi-agent coordination problems. They provide structured ways for agents to work together effectively.

## What are Patterns?

Patterns are:
- Pre-built coordination strategies for multiple agents
- Reusable components that can be embedded in flows
- Solutions to common agent interaction scenarios
- Building blocks for complex workflows

## Built-in Patterns

TFrameX includes four fundamental patterns:

### 1. Sequential Pattern

Executes agents one after another, passing output forward.

```python
from tframex.patterns import SequentialPattern

# Create a sequential workflow
pattern = SequentialPattern(
    name="research_process",
    agents=["topic_analyzer", "researcher", "summarizer"]
)

# Use in a flow
flow = Flow("ResearchFlow")
flow.add_pattern_step(pattern)
```

**Use Cases:**
- Data processing pipelines
- Step-by-step workflows
- Dependent operations
- Validation chains

**Example: Content Creation Pipeline**
```python
content_pattern = SequentialPattern(
    name="content_pipeline",
    agents=[
        "idea_generator",      # Generate content ideas
        "outline_creator",     # Create detailed outline
        "content_writer",      # Write the content
        "editor",             # Edit and refine
        "seo_optimizer"       # Optimize for search
    ]
)
```

### 2. Parallel Pattern

Executes multiple agents simultaneously, collecting all results.

```python
from tframex.patterns import ParallelPattern

# Create parallel execution
pattern = ParallelPattern(
    name="multi_analysis",
    agents=["financial_analyst", "technical_analyst", "market_analyst"]
)

# The output will contain results from all agents
# {
#     "financial_analyst": "Financial analysis results...",
#     "technical_analyst": "Technical analysis results...",
#     "market_analyst": "Market analysis results..."
# }
```

**Use Cases:**
- Multiple perspective analysis
- Parallel data processing
- Independent operations
- Performance optimization

**Example: Comprehensive Analysis**
```python
analysis_pattern = ParallelPattern(
    name="company_analysis",
    agents=[
        "financial_health_checker",
        "competitive_analyzer", 
        "market_position_assessor",
        "risk_evaluator",
        "growth_predictor"
    ]
)

# All analyses run simultaneously
flow = Flow("CompanyEvaluation")
flow.add_pattern_step(analysis_pattern)
flow.add_step("report_synthesizer")  # Combine all results
```

### 3. Router Pattern

Routes execution to different agents based on conditions.

```python
from tframex.patterns import RouterPattern

# Create conditional routing
pattern = RouterPattern(
    name="support_router",
    router_agent="ticket_classifier",  # Decides the route
    routes={
        "billing": "billing_specialist",
        "technical": "tech_support",
        "general": "general_support",
        "urgent": "senior_support"
    }
)
```

**Use Cases:**
- Conditional workflows
- Specialized handling
- Dynamic routing
- Classification-based processing

**Example: Document Processing**
```python
doc_router = RouterPattern(
    name="document_processor",
    router_agent="document_classifier",
    routes={
        "invoice": "invoice_processor",
        "contract": "contract_analyzer",
        "resume": "resume_parser",
        "report": "report_summarizer",
        "unknown": "manual_reviewer"
    }
)

# Router agent returns one of the route keys
# Only the corresponding agent is executed
```

### 4. Discussion Pattern

Facilitates multi-agent discussions with rounds of interaction.

```python
from tframex.patterns import DiscussionPattern

# Create a discussion
pattern = DiscussionPattern(
    name="design_review",
    agents=["architect", "developer", "designer", "tester"],
    num_rounds=3,
    moderator_agent="tech_lead"
)
```

**Use Cases:**
- Design reviews
- Brainstorming sessions
- Consensus building
- Collaborative problem solving

**Example: Product Feature Discussion**
```python
feature_discussion = DiscussionPattern(
    name="feature_planning",
    agents=[
        "product_manager",
        "lead_developer",
        "ux_designer",
        "qa_engineer",
        "customer_advocate"
    ],
    num_rounds=4,
    moderator_agent="product_owner"
)

# Each agent contributes in each round
# Moderator guides and summarizes
```

## Combining Patterns

### Nested Patterns

Patterns can be nested within each other:

```python
# Parallel analysis followed by discussion
flow = Flow("AnalysisAndReview")

# First: Parallel analysis
flow.add_pattern_step(
    ParallelPattern(
        name="gather_data",
        agents=["data_analyst", "market_researcher", "competitor_analyst"]
    )
)

# Then: Discussion of results
flow.add_pattern_step(
    DiscussionPattern(
        name="review_findings",
        agents=["strategist", "product_lead", "ceo"],
        num_rounds=2,
        moderator_agent="facilitator"
    )
)

# Finally: Decision
flow.add_step("decision_maker")
```

### Complex Workflows

```python
# Multi-stage pattern composition
flow = Flow("ComplexWorkflow")

# Stage 1: Classify request
flow.add_step("request_classifier")

# Stage 2: Route to appropriate team
flow.add_pattern_step(
    RouterPattern(
        name="team_router",
        router_agent="request_classifier",
        routes={
            "urgent": "emergency_team",
            "normal": "standard_process",
            "complex": "expert_team"
        }
    )
)

# Stage 3: Standard process (sequential)
standard_process = SequentialPattern(
    name="standard_process",
    agents=["validator", "processor", "reviewer"]
)

# Stage 4: Expert team (discussion)
expert_team = DiscussionPattern(
    name="expert_team",
    agents=["senior_analyst", "domain_expert", "architect"],
    num_rounds=3
)
```

## Custom Patterns

Create your own patterns by extending `BasePattern`:

```python
from tframex.patterns import BasePattern
from typing import List, Any

class VotingPattern(BasePattern):
    """
    Multiple agents vote on options, majority wins.
    """
    def __init__(
        self, 
        name: str, 
        agents: List[str], 
        options: List[str],
        deciding_agent: str = None
    ):
        super().__init__(name)
        self.agents = agents
        self.options = options
        self.deciding_agent = deciding_agent
    
    async def execute(self, context, input_data: str) -> Any:
        # Collect votes from all agents
        votes = {}
        for agent in self.agents:
            prompt = f"{input_data}\n\nOptions: {', '.join(self.options)}"
            response = await context.call_agent(agent, prompt)
            
            # Parse vote from response
            vote = self.extract_vote(response)
            votes[agent] = vote
        
        # Count votes
        vote_counts = {}
        for vote in votes.values():
            vote_counts[vote] = vote_counts.get(vote, 0) + 1
        
        # Determine winner
        winner = max(vote_counts, key=vote_counts.get)
        
        # Optional: Let deciding agent break ties
        if self.deciding_agent and self.has_tie(vote_counts):
            winner = await context.call_agent(
                self.deciding_agent,
                f"Break tie between: {self.get_tied_options(vote_counts)}"
            )
        
        return {
            "winner": winner,
            "votes": votes,
            "counts": vote_counts
        }
```

### Consensus Pattern

```python
class ConsensusPattern(BasePattern):
    """
    Agents work iteratively to reach consensus.
    """
    def __init__(
        self,
        name: str,
        agents: List[str],
        max_iterations: int = 5,
        consensus_threshold: float = 0.8
    ):
        super().__init__(name)
        self.agents = agents
        self.max_iterations = max_iterations
        self.consensus_threshold = consensus_threshold
    
    async def execute(self, context, input_data: str) -> Any:
        current_positions = {}
        
        for iteration in range(self.max_iterations):
            # Collect positions
            for agent in self.agents:
                # Include other agents' positions in prompt
                prompt = self.build_consensus_prompt(
                    input_data, 
                    current_positions, 
                    agent
                )
                position = await context.call_agent(agent, prompt)
                current_positions[agent] = position
            
            # Check for consensus
            if self.has_consensus(current_positions):
                return {
                    "consensus": True,
                    "iteration": iteration + 1,
                    "final_position": self.get_consensus_position(current_positions)
                }
        
        # No consensus reached
        return {
            "consensus": False,
            "iterations": self.max_iterations,
            "positions": current_positions
        }
```

## Pattern Best Practices

### 1. Choose the Right Pattern

```python
# Sequential for dependent steps
research_flow = SequentialPattern(
    name="research",
    agents=["gather_sources", "analyze_data", "write_report"]
)

# Parallel for independent operations
analysis_flow = ParallelPattern(
    name="analysis",
    agents=["financial_check", "legal_review", "risk_assessment"]
)

# Router for conditional logic
support_flow = RouterPattern(
    name="support",
    router_agent="classifier",
    routes={"bug": "dev_team", "feature": "product_team"}
)

# Discussion for collaboration
planning_flow = DiscussionPattern(
    name="planning",
    agents=["architect", "developer", "designer"],
    num_rounds=3
)
```

### 2. Pattern Configuration

```python
# Configure patterns for specific needs
pattern = DiscussionPattern(
    name="thorough_review",
    agents=["reviewer1", "reviewer2", "reviewer3"],
    num_rounds=5,  # More rounds for complex topics
    moderator_agent="lead_reviewer",
    # Can extend with custom parameters
    require_consensus=True,
    min_participation=0.8
)
```

### 3. Error Handling in Patterns

```python
class RobustPattern(BasePattern):
    async def execute(self, context, input_data):
        results = {}
        errors = {}
        
        for agent in self.agents:
            try:
                result = await context.call_agent(agent, input_data)
                results[agent] = result
            except Exception as e:
                errors[agent] = str(e)
                # Continue with other agents
        
        if errors:
            # Handle partial failure
            return {
                "status": "partial_success",
                "results": results,
                "errors": errors
            }
        
        return {"status": "success", "results": results}
```

## Pattern Composition Examples

### Customer Service Workflow

```python
def create_customer_service_flow():
    flow = Flow("CustomerService")
    
    # Initial classification
    flow.add_step("ticket_analyzer")
    
    # Route to appropriate handler
    flow.add_pattern_step(
        RouterPattern(
            name="ticket_router",
            router_agent="ticket_analyzer",
            routes={
                "refund": "refund_process",
                "technical": "tech_support_process",
                "complaint": "complaint_process",
                "general": "general_inquiry"
            }
        )
    )
    
    # Refund process (sequential)
    refund_process = SequentialPattern(
        name="refund_process",
        agents=["verify_purchase", "calculate_refund", "process_refund"]
    )
    
    # Tech support (discussion)
    tech_support = DiscussionPattern(
        name="tech_support_process",
        agents=["level1_support", "level2_support", "engineer"],
        num_rounds=2,
        moderator_agent="support_lead"
    )
    
    return flow
```

### Research and Development Pipeline

```python
def create_rd_pipeline():
    flow = Flow("RDPipeline")
    
    # Parallel research
    flow.add_pattern_step(
        ParallelPattern(
            name="research_phase",
            agents=[
                "literature_reviewer",
                "patent_searcher",
                "market_analyzer",
                "competitor_researcher"
            ]
        )
    )
    
    # Synthesis discussion
    flow.add_pattern_step(
        DiscussionPattern(
            name="synthesis",
            agents=["lead_researcher", "domain_expert", "strategist"],
            num_rounds=3,
            moderator_agent="research_director"
        )
    )
    
    # Development planning
    flow.add_pattern_step(
        SequentialPattern(
            name="planning",
            agents=[
                "technical_architect",
                "resource_planner",
                "timeline_estimator",
                "risk_assessor"
            ]
        )
    )
    
    return flow
```

## Testing Patterns

```python
import pytest

@pytest.mark.asyncio
async def test_sequential_pattern():
    app = TFrameXApp()
    # Setup test agents
    
    pattern = SequentialPattern(
        name="test_sequence",
        agents=["agent1", "agent2", "agent3"]
    )
    
    async with app.run_context() as rt:
        result = await pattern.execute(rt, "test input")
        
        # Verify sequential execution
        assert "agent3" in result  # Last agent's output

@pytest.mark.asyncio
async def test_parallel_pattern():
    pattern = ParallelPattern(
        name="test_parallel",
        agents=["fast_agent", "slow_agent"]
    )
    
    # Test that all agents run
    # Test timing to ensure parallel execution
```

## Next Steps

Now that you understand patterns:

1. Learn about [Memory](memory) for stateful patterns
2. Explore [MCP Integration](mcp-integration) for external services
3. Study [Flow Examples](../examples/pattern-examples) for real implementations
4. Check [API Reference](../api/patterns) for detailed documentation

## Visual Pattern Design

The execution flow of patterns is illustrated in our [Pattern Execution Flow diagram](/img/05-pattern-execution-flow.png), showing how different patterns coordinate agent interactions.