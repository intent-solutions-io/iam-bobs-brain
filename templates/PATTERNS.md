# Pattern Selection Guide

Choose the right pattern for your multi-agent workflow.

## Quick Reference

| Pattern | Use When | ADK Primitive | Latency |
|---------|----------|---------------|---------|
| Sequential | Steps depend on each other | `SequentialAgent` | Sum of all |
| Parallel | Independent concurrent tasks | `ParallelAgent` | Max of any |
| Quality Gates | Iterative improvement needed | `LoopAgent` | 1-N iterations |
| Foreman-Worker | Complex task delegation | `LlmAgent` + tools | Varies |
| Human Approval | High-risk gating needed | Callbacks | +human time |

## Decision Tree

```
Start
  │
  ├─ Are tasks dependent on each other?
  │   │
  │   ├─ Yes → Do you need iteration until success?
  │   │         │
  │   │         ├─ Yes → QUALITY GATES (LoopAgent)
  │   │         │
  │   │         └─ No  → SEQUENTIAL (SequentialAgent)
  │   │
  │   └─ No  → PARALLEL (ParallelAgent)
  │
  ├─ Do you need task delegation to specialists?
  │   │
  │   └─ Yes → FOREMAN-WORKER (LlmAgent + delegation)
  │
  └─ Do high-risk actions need approval?
      │
      └─ Yes → HUMAN APPROVAL (Callbacks)
```

## Pattern Combinations

### Sequential + Parallel
Parallel analysis, then sequential processing:
```
ParallelAgent([analyzer1, analyzer2])
    ↓
SequentialAgent([planner, executor])
```

### Parallel + Quality Gates
Parallel generation, then QA loop:
```
ParallelAgent([generator1, generator2])
    ↓
LoopAgent([combiner, critic])
```

### All Four Patterns
Full SWE workflow:
```
ParallelAgent([adk_check, cleanup_check, index_check])  # Parallel analysis
    ↓
SequentialAgent([issue_creator, planner])               # Sequential planning
    ↓
LoopAgent([implementer, qa])                            # Quality gates
    ↓
ApprovalGate → Deployer                                 # Human approval
```

## Pattern Comparison

### Sequential vs Parallel

| Aspect | Sequential | Parallel |
|--------|-----------|----------|
| Execution | One at a time | Concurrent |
| Dependencies | Allowed | Not allowed |
| Latency | Sum of agents | Max of agents |
| State | Chained via output_key | Unique per agent |
| Use case | Pipelines | Fan-out/gather |

### Quality Gates vs Sequential

| Aspect | Quality Gates | Sequential |
|--------|--------------|------------|
| Iteration | Yes (up to N) | No |
| Exit condition | PASS or max | All complete |
| Feedback | Critic → Generator | None |
| Use case | Refinement | Processing |

### Foreman-Worker vs All Others

| Aspect | Foreman-Worker | Others |
|--------|---------------|--------|
| Structure | Hierarchical | Flat |
| Control | Foreman decides | Predefined |
| Flexibility | High | Fixed |
| Complexity | Higher | Lower |
| Use case | Complex delegation | Simple workflows |

## Anti-Patterns

### Don't Do

```python
# ❌ Same output_key in parallel (race condition!)
ParallelAgent([
    agent1(output_key="result"),
    agent2(output_key="result"),  # COLLISION!
])

# ❌ LoopAgent without max_iterations (infinite loop!)
LoopAgent(sub_agents=[...])  # Missing max_iterations!

# ❌ Foreman executing worker tasks
foreman_instruction = "You analyze code..."  # BAD: foreman should delegate!

# ❌ Human approval without timeout
await wait_for_approval()  # MISSING timeout!
```

### Do Instead

```python
# ✅ Unique output_keys
ParallelAgent([
    agent1(output_key="result_a"),
    agent2(output_key="result_b"),
])

# ✅ Always set max_iterations
LoopAgent(sub_agents=[...], max_iterations=3)

# ✅ Foreman delegates
foreman_instruction = "Delegate analysis to analyzer worker..."

# ✅ Approval with timeout
await asyncio.wait_for(approval, timeout=300)
```

## References

- [Google Multi-Agent Patterns](https://developers.googleblog.com/en/developers-guide-to-multi-agent-patterns-in-adk/)
- [ADK Multi-Agent Documentation](https://google.github.io/adk-docs/agents/multi-agents/)
