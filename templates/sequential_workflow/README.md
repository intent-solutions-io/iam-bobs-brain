# Sequential Workflow Pattern

Execute agents in strict order with automatic state passing.

## Pattern Overview

```
┌─────────────────────────────────────────────────────────────┐
│                  SequentialAgent                            │
│                                                             │
│   Agent A          Agent B          Agent C                 │
│     ↓                ↓                ↓                     │
│   output_key:      output_key:      output_key:             │
│   "step_a"         "step_b"         "step_c"                │
│     │                │                │                     │
│     └────────────────┼────────────────┘                     │
│                      ↓                                      │
│              State flows via                                │
│              session.state                                  │
└─────────────────────────────────────────────────────────────┘
```

## When to Use

- Steps depend on previous step output
- Processing must occur in specific order
- Pipeline-style workflows (analyze → plan → execute)

## Implementation

```python
from google.adk.agents import SequentialAgent, LlmAgent

# Step 1: Create agents with unique output_keys
agent_a = LlmAgent(
    name="analyzer",
    instruction="Analyze the input and output findings.",
    output_key="analysis",  # Writes to state["analysis"]
)

agent_b = LlmAgent(
    name="planner",
    instruction="Based on {analysis}, create a plan.",  # Reads state["analysis"]
    output_key="plan",
)

agent_c = LlmAgent(
    name="executor",
    instruction="Execute based on {plan}.",  # Reads state["plan"]
    output_key="result",
)

# Step 2: Wrap in SequentialAgent
workflow = SequentialAgent(
    name="my_workflow",
    sub_agents=[agent_a, agent_b, agent_c],
)
```

## Key Requirements

1. **Unique output_keys**: Each agent must have a distinct `output_key`
2. **State references**: Use `{key}` in instructions to read from state
3. **Order matters**: Agents execute in list order

## Files

- `workflow.py` - Reusable workflow factory
- `example.py` - Runnable example

## References

- [Google Multi-Agent Patterns](https://developers.googleblog.com/en/developers-guide-to-multi-agent-patterns-in-adk/)
- [ADK SequentialAgent](https://google.github.io/adk-docs/agents/multi-agents/)
