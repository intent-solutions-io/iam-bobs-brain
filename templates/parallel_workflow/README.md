# Parallel Workflow Pattern

Execute independent agents concurrently with result aggregation.

## Pattern Overview

```
┌─────────────────────────────────────────────────────────────┐
│                  SequentialAgent                            │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              ParallelAgent (Fan-Out)                │   │
│  │                                                      │   │
│  │   Agent A       Agent B       Agent C               │   │
│  │     ↓             ↓             ↓                   │   │
│  │   "result_a"   "result_b"   "result_c"             │   │
│  │                                                      │   │
│  └──────────────────┬──────────────────────────────────┘   │
│                     ↓                                       │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              Aggregator (Fan-In)                    │   │
│  │                                                      │   │
│  │   Combines {result_a}, {result_b}, {result_c}       │   │
│  │   → "aggregated_result"                             │   │
│  │                                                      │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

## When to Use

- Tasks are independent (no cross-dependencies)
- Latency reduction is important
- Same input processed different ways

## Implementation

```python
from google.adk.agents import ParallelAgent, SequentialAgent, LlmAgent

# Step 1: Create parallel agents with unique output_keys
agent_a = LlmAgent(name="agent_a", output_key="result_a", ...)
agent_b = LlmAgent(name="agent_b", output_key="result_b", ...)
agent_c = LlmAgent(name="agent_c", output_key="result_c", ...)

# Step 2: Wrap in ParallelAgent (fan-out)
parallel = ParallelAgent(
    name="parallel_analysis",
    sub_agents=[agent_a, agent_b, agent_c],
)

# Step 3: Create aggregator (fan-in)
aggregator = LlmAgent(
    name="aggregator",
    instruction="Combine {result_a}, {result_b}, {result_c}",
    output_key="aggregated_result",
)

# Step 4: Combine into full workflow
workflow = SequentialAgent(
    name="parallel_workflow",
    sub_agents=[parallel, aggregator],
)
```

## Key Requirements

1. **Unique output_keys**: CRITICAL - prevents race conditions
2. **Independent agents**: No cross-dependencies in parallel phase
3. **Aggregator**: Combines results after parallel execution

## Files

- `workflow.py` - Reusable workflow factory
- `example.py` - Runnable example

## References

- [Google Multi-Agent Patterns](https://developers.googleblog.com/en/developers-guide-to-multi-agent-patterns-in-adk/)
- [ADK ParallelAgent](https://google.github.io/adk-docs/agents/multi-agents/)
