---
sidebar_position: 4
title: Flows
---

# Flows

Flows are TFrameX's way of orchestrating complex, multi-step workflows. They enable you to chain agents, tools, and patterns together to solve sophisticated problems.

## What is a Flow?

A Flow is:
- A sequence of operations executed in order
- A container for agents, tools, and patterns
- A way to maintain context across multiple steps
- A reusable workflow definition

![Pattern Execution Flow](/img/05-pattern-execution-flow.png)

## Creating Flows

### Basic Flow

```python
from tframex.flows import Flow

# Create a flow
flow = Flow(
    name="ContentCreation",
    description="Create and publish content"
)

# Add steps
flow.add_step("research_agent")
flow.add_step("writer_agent")
flow.add_step("editor_agent")
flow.add_step("publisher_agent")

# Register with app
app.register_flow(flow)
```

### Flow with Patterns

```python
from tframex.patterns import ParallelPattern, RouterPattern

flow = Flow("AdvancedWorkflow")

# Sequential step
flow.add_step("input_processor")

# Parallel execution
flow.add_pattern_step(
    ParallelPattern(
        name="parallel_analysis",
        agents=["analyst_1", "analyst_2", "analyst_3"]
    )
)

# Conditional routing
flow.add_pattern_step(
    RouterPattern(
        name="content_router",
        router_agent="router",
        routes={
            "technical": "tech_writer",
            "marketing": "marketing_writer",
            "general": "general_writer"
        }
    )
)

# Final step
flow.add_step("quality_checker")
```

## Flow Execution

### Running a Flow

```python
async def run_content_pipeline():
    app = TFrameXApp()
    # ... register agents and flows ...
    
    async with app.run_context() as rt:
        result = await rt.run_flow(
            "ContentCreation",
            initial_input="Create an article about AI ethics"
        )
        print(result)
```

### Flow Context

Context is passed between steps:

```python
# Step 1 output becomes Step 2 input
flow = Flow("DataPipeline")
flow.add_step("data_collector")  # Returns collected data
flow.add_step("data_processor")  # Receives collected data
flow.add_step("data_analyzer")   # Receives processed data
```

## Advanced Flow Patterns

### Data Transformation Pipeline

```python
def create_etl_flow():
    flow = Flow(
        name="ETLPipeline",
        description="Extract, Transform, Load data"
    )
    
    # Extract from multiple sources in parallel
    flow.add_pattern_step(
        ParallelPattern(
            name="extract",
            agents=["db_extractor", "api_extractor", "file_extractor"]
        )
    )
    
    # Transform data
    flow.add_step("data_transformer")
    
    # Validate before loading
    flow.add_step("data_validator")
    
    # Load to destination
    flow.add_step("data_loader")
    
    return flow
```

### Document Processing Workflow

```python
def create_document_flow():
    flow = Flow("DocumentProcessor")
    
    # Parse document
    flow.add_step("document_parser")
    
    # Route based on document type
    flow.add_pattern_step(
        RouterPattern(
            name="doc_router",
            router_agent="type_classifier",
            routes={
                "invoice": "invoice_processor",
                "contract": "contract_analyzer",
                "report": "report_summarizer",
                "other": "general_processor"
            }
        )
    )
    
    # Common post-processing
    flow.add_step("metadata_extractor")
    flow.add_step("storage_agent")
    
    return flow
```

### Multi-Stage Approval Process

```python
def create_approval_flow():
    flow = Flow("ApprovalWorkflow")
    
    # Initial request
    flow.add_step("request_validator")
    
    # First level approval
    flow.add_step("manager_approval")
    
    # Conditional escalation
    flow.add_pattern_step(
        RouterPattern(
            name="escalation_router",
            router_agent="risk_assessor",
            routes={
                "low_risk": "auto_approver",
                "medium_risk": "director_approval",
                "high_risk": "executive_approval"
            }
        )
    )
    
    # Final processing
    flow.add_step("approval_processor")
    flow.add_step("notification_sender")
    
    return flow
```

## Flow Patterns

### Sequential Pattern in Flows

```python
from tframex.patterns import SequentialPattern

flow = Flow("SequentialWorkflow")

# Add a sequential pattern as a step
flow.add_pattern_step(
    SequentialPattern(
        name="research_phase",
        agents=["topic_analyzer", "researcher", "fact_checker"]
    )
)

flow.add_step("writer")
```

### Parallel Pattern in Flows

```python
from tframex.patterns import ParallelPattern

flow = Flow("ParallelAnalysis")

flow.add_step("data_preparer")

# Parallel analysis
flow.add_pattern_step(
    ParallelPattern(
        name="multi_analysis",
        agents=["statistical_analyst", "ml_analyst", "business_analyst"]
    )
)

flow.add_step("results_synthesizer")
```

### Discussion Pattern in Flows

```python
from tframex.patterns import DiscussionPattern

flow = Flow("DesignReview")

flow.add_step("proposal_creator")

# Multi-agent discussion
flow.add_pattern_step(
    DiscussionPattern(
        name="design_discussion",
        agents=["architect", "developer", "designer", "security_expert"],
        num_rounds=3,
        moderator_agent="tech_lead"
    )
)

flow.add_step("decision_maker")
```

### Nested Patterns

```python
# Complex nested workflow
flow = Flow("ComplexWorkflow")

# Parallel data collection
parallel_collect = ParallelPattern(
    name="collect_data",
    agents=["web_scraper", "api_fetcher", "db_querier"]
)

# Sequential processing of each result
sequential_process = SequentialPattern(
    name="process_each",
    agents=["cleaner", "transformer", "validator"]
)

# Main flow
flow.add_pattern_step(parallel_collect)
flow.add_pattern_step(sequential_process)
flow.add_step("aggregator")
```

## Error Handling in Flows

### Flow-Level Error Handling

```python
class RobustFlow(Flow):
    async def execute(self, context, initial_input):
        try:
            return await super().execute(context, initial_input)
        except Exception as e:
            # Log error
            logger.error(f"Flow {self.name} failed: {e}")
            
            # Attempt recovery
            if hasattr(self, 'recovery_agent'):
                return await context.call_agent(
                    self.recovery_agent,
                    f"Recover from error: {e}"
                )
            
            # Fallback response
            return f"Flow failed: {str(e)}"
```

### Step-Level Error Handling

```python
flow = Flow("FaultTolerantFlow")

# Add steps with error handlers
flow.add_step("risky_operation")
flow.add_step("error_handler", on_error=True)
flow.add_step("continue_processing")

# Alternative: Wrap in try-catch pattern
flow.add_pattern_step(
    RouterPattern(
        name="error_router",
        router_agent="error_detector",
        routes={
            "success": "next_step",
            "error": "error_recovery",
            "retry": "risky_operation"  # Loop back
        }
    )
)
```

## Flow Composition

### Reusable Sub-Flows

```python
# Define reusable flows
validation_flow = Flow("ValidationFlow")
validation_flow.add_step("format_checker")
validation_flow.add_step("content_validator")
validation_flow.add_step("security_scanner")

# Use in larger flows
main_flow = Flow("MainProcess")
main_flow.add_step("input_receiver")
main_flow.add_subflow(validation_flow)  # Include validation flow
main_flow.add_step("processor")
```

### Dynamic Flow Construction

```python
def create_dynamic_flow(steps: List[str], use_parallel: bool = False):
    flow = Flow("DynamicFlow")
    
    if use_parallel:
        flow.add_pattern_step(
            ParallelPattern(name="parallel_exec", agents=steps)
        )
    else:
        for step in steps:
            flow.add_step(step)
    
    return flow

# Create flow based on configuration
config = load_config()
flow = create_dynamic_flow(
    steps=config["agents"],
    use_parallel=config.get("parallel", False)
)
```

## Flow State Management

### Maintaining State Across Steps

```python
from tframex.flows import FlowContext

class StatefulFlow(Flow):
    async def execute(self, context: FlowContext, initial_input):
        # Initialize flow state
        context.state["processed_items"] = []
        context.state["errors"] = []
        
        # Execute steps
        result = await super().execute(context, initial_input)
        
        # Return final state
        return {
            "result": result,
            "stats": {
                "processed": len(context.state["processed_items"]),
                "errors": len(context.state["errors"])
            }
        }
```

### Checkpointing

```python
class CheckpointedFlow(Flow):
    async def execute_step(self, context, step, input_data):
        # Execute step
        result = await super().execute_step(context, step, input_data)
        
        # Save checkpoint
        await self.save_checkpoint(context, step, result)
        
        return result
    
    async def save_checkpoint(self, context, step, result):
        checkpoint = {
            "flow": self.name,
            "step": step.name,
            "result": result,
            "timestamp": datetime.now().isoformat()
        }
        await database.save_checkpoint(checkpoint)
```

## Flow Monitoring

### Execution Metrics

```python
import time
from dataclasses import dataclass

@dataclass
class FlowMetrics:
    start_time: float
    end_time: float
    steps_completed: int
    steps_failed: int
    total_duration: float

class MonitoredFlow(Flow):
    async def execute(self, context, initial_input):
        metrics = FlowMetrics(
            start_time=time.time(),
            end_time=0,
            steps_completed=0,
            steps_failed=0,
            total_duration=0
        )
        
        try:
            result = await super().execute(context, initial_input)
            metrics.steps_completed = len(self.steps)
        except Exception as e:
            metrics.steps_failed += 1
            raise
        finally:
            metrics.end_time = time.time()
            metrics.total_duration = metrics.end_time - metrics.start_time
            
            # Log metrics
            logger.info(f"Flow metrics: {metrics}")
            
            # Send to monitoring system
            await send_metrics(metrics)
        
        return result
```

## Best Practices

### 1. Keep Flows Focused
Each flow should have a single, clear purpose:

```python
# Good: Focused flows
invoice_flow = Flow("InvoiceProcessing")
payment_flow = Flow("PaymentProcessing")

# Avoid: Kitchen sink flow
everything_flow = Flow("DoEverything")
```

### 2. Use Meaningful Names
```python
# Good: Descriptive names
flow.add_step("validate_customer_data")
flow.add_step("calculate_risk_score")

# Avoid: Generic names
flow.add_step("step1")
flow.add_step("process")
```

### 3. Handle Edge Cases
```python
flow = Flow("RobustFlow")

# Add validation
flow.add_step("input_validator")

# Add error handling
flow.add_pattern_step(
    RouterPattern(
        name="validation_router",
        router_agent="validator",
        routes={
            "valid": "processor",
            "invalid": "error_handler",
            "needs_review": "manual_reviewer"
        }
    )
)
```

### 4. Document Flow Purpose
```python
flow = Flow(
    name="CustomerOnboarding",
    description="""
    Complete customer onboarding workflow:
    1. Validate customer information
    2. Perform KYC checks
    3. Create account
    4. Send welcome email
    5. Schedule follow-up
    
    Requires: customer data dictionary
    Returns: onboarding result with account details
    """
)
```

## Testing Flows

```python
import pytest

@pytest.mark.asyncio
async def test_content_flow():
    app = TFrameXApp()
    # Setup test agents
    setup_test_agents(app)
    
    # Register flow
    flow = create_content_flow()
    app.register_flow(flow)
    
    # Test execution
    async with app.run_context() as rt:
        result = await rt.run_flow(
            "ContentCreation",
            "Test article about testing"
        )
        
        assert result is not None
        assert "article" in result.lower()

@pytest.mark.asyncio
async def test_flow_error_handling():
    # Test that flow handles errors gracefully
    pass
```

## Flow Visualization

```python
def visualize_flow(flow: Flow) -> str:
    """Generate a visual representation of the flow."""
    lines = [f"Flow: {flow.name}"]
    lines.append("=" * 40)
    
    for i, step in enumerate(flow.steps):
        if hasattr(step, 'pattern_type'):
            lines.append(f"{i+1}. [{step.pattern_type}] {step.name}")
            if hasattr(step, 'agents'):
                for agent in step.agents:
                    lines.append(f"   - {agent}")
        else:
            lines.append(f"{i+1}. {step}")
    
    return "\n".join(lines)
```

## YAML Configuration

Define flows in YAML for easy modification:

```yaml
# flows.yaml
flows:
  - name: DocumentProcessing
    description: Process various document types
    steps:
      - type: agent
        name: document_parser
      
      - type: pattern
        pattern: router
        name: doc_router
        router_agent: classifier
        routes:
          invoice: invoice_processor
          contract: contract_processor
          
      - type: agent
        name: storage_agent
```

Load from YAML:

```python
import yaml

def load_flows_from_yaml(filename: str) -> List[Flow]:
    with open(filename) as f:
        config = yaml.safe_load(f)
    
    flows = []
    for flow_config in config['flows']:
        flow = Flow(
            name=flow_config['name'],
            description=flow_config.get('description', '')
        )
        
        for step in flow_config['steps']:
            if step['type'] == 'agent':
                flow.add_step(step['name'])
            elif step['type'] == 'pattern':
                # Create pattern based on config
                pattern = create_pattern_from_config(step)
                flow.add_pattern_step(pattern)
        
        flows.append(flow)
    
    return flows
```

## Next Steps

Now that you understand flows:

1. Explore [Patterns](patterns) for reusable workflow components
2. Learn about [Memory](memory) for stateful flows
3. Study [API Reference](../api/flows) for detailed documentation
4. Check [Examples](../examples/pattern-examples) for practical implementations

## Visual Flow Design

The [Configuration Lifecycle](/img/06-configuration-lifecycle.png) diagram shows how flows are configured and executed in TFrameX.