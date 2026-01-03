# Quality Gates Pattern

Iterative refinement with generator-critic loop until quality passes.

## Pattern Overview

```
┌─────────────────────────────────────────────────────────────┐
│                  LoopAgent (max_iterations=N)               │
│                                                             │
│  ┌───────────────────────────────────────────────────┐     │
│  │           Sequential Review Pair                   │     │
│  │                                                    │     │
│  │   Generator          Critic                        │     │
│  │   (produces)    →    (evaluates)                   │     │
│  │       │                  │                         │     │
│  │   output_key:       output_key:                    │     │
│  │   "output"          "verdict"                      │     │
│  │                          │                         │     │
│  │              ┌───────────┴───────────┐            │     │
│  │              │                       │            │     │
│  │         PASS: escalate         FAIL: retry        │     │
│  │              │                       │            │     │
│  └──────────────┼───────────────────────┼────────────┘     │
│                 │                       │                  │
│            exit loop              next iteration           │
└─────────────────┴───────────────────────┴──────────────────┘
```

## When to Use

- Output quality needs verification
- Iterative improvement is possible
- Clear PASS/FAIL criteria exist
- "Keep trying until good" workflows

## Implementation

```python
from google.adk.agents import LoopAgent, SequentialAgent, LlmAgent

# Step 1: Create generator
generator = LlmAgent(
    name="generator",
    instruction="Produce output based on {input}. If previous feedback exists, improve based on {verdict}.",
    output_key="generated_output",
)

# Step 2: Create critic with PASS/FAIL output
critic = LlmAgent(
    name="critic",
    instruction='Review {generated_output}. Output: {"status": "PASS|FAIL", "reason": "..."}',
    output_key="verdict",
    after_agent_callback=escalation_callback,  # Exits loop on PASS
)

# Step 3: Combine into review pair
review_pair = SequentialAgent(
    name="review_pair",
    sub_agents=[generator, critic],
)

# Step 4: Wrap in LoopAgent
loop = LoopAgent(
    name="quality_loop",
    sub_agents=[review_pair],
    max_iterations=3,  # ALWAYS set this!
)
```

## Key Requirements

1. **max_iterations**: ALWAYS set to prevent infinite loops
2. **Escalation callback**: Signal `ctx.actions.escalate = True` on PASS
3. **Unique output_keys**: Generator and critic need different keys
4. **Structured verdict**: Critic must output parseable PASS/FAIL

## Files

- `workflow.py` - Reusable workflow factory
- `example.py` - Runnable example

## References

- [Google Multi-Agent Patterns](https://developers.googleblog.com/en/developers-guide-to-multi-agent-patterns-in-adk/)
- [ADK LoopAgent](https://google.github.io/adk-docs/agents/multi-agents/)
