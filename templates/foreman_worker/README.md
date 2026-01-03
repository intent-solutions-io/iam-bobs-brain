# Foreman-Worker Pattern

Hierarchical task decomposition with specialized workers.

## Pattern Overview

```
┌─────────────────────────────────────────────────────────────┐
│                      Foreman Agent                          │
│                  (Orchestration Layer)                      │
│                                                             │
│   • Receives high-level requests                            │
│   • Decomposes into specialist tasks                        │
│   • Routes to appropriate workers                           │
│   • Aggregates results                                      │
│                                                             │
│               ┌───────────┬───────────┐                     │
│               ↓           ↓           ↓                     │
│         ┌─────────┐ ┌─────────┐ ┌─────────┐                │
│         │ Worker  │ │ Worker  │ │ Worker  │                │
│         │    A    │ │    B    │ │    C    │                │
│         └─────────┘ └─────────┘ └─────────┘                │
│                                                             │
│   Workers are strict function agents:                       │
│   • Deterministic execution                                 │
│   • Clear input/output schemas                              │
│   • Domain-specific tools                                   │
└─────────────────────────────────────────────────────────────┘
```

## When to Use

- Complex tasks requiring multiple domains
- Specialists with distinct capabilities
- Need for task delegation and coordination
- Hierarchical team structures

## Implementation

```python
from google.adk.agents import LlmAgent

# Step 1: Create specialized workers
worker_a = LlmAgent(
    name="analyzer",
    instruction="You analyze code. Input: {task}. Output structured analysis.",
    tools=[analysis_tool],
    output_key="analysis_result",
)

worker_b = LlmAgent(
    name="planner",
    instruction="You create plans. Input: {task}. Output structured plan.",
    tools=[planning_tool],
    output_key="plan_result",
)

# Step 2: Create foreman with delegation tools
foreman = LlmAgent(
    name="foreman",
    instruction='''You orchestrate workers. Available:
    - analyzer: Code analysis
    - planner: Plan creation
    
    Delegate tasks appropriately.''',
    tools=[delegate_to_worker],
)
```

## Key Requirements

1. **Clear worker roles**: Each worker has specific capability
2. **Foreman doesn't execute**: Only delegates and aggregates
3. **Structured delegation**: Clear task inputs and expected outputs
4. **Worker tools**: Each worker has domain-specific tools

## Files

- `workflow.py` - Foreman and worker factories
- `example.py` - Runnable example

## References

- [Google Multi-Agent Patterns](https://developers.googleblog.com/en/developers-guide-to-multi-agent-patterns-in-adk/)
- [Hierarchical Decomposition](https://google.github.io/adk-docs/agents/multi-agents/)
