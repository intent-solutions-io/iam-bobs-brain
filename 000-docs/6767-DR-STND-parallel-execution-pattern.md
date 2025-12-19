# Parallel Execution Pattern Standard

**Document ID:** 6767-DR-STND-parallel-execution-pattern
**Type:** Standard (Cross-Repo Canonical)
**Status:** Active
**Created:** 2025-12-19
**Phase:** P2 - Parallel Execution

---

## I. Overview

This standard defines how to implement Google's **Parallel Fan-Out** pattern using ADK's `ParallelAgent` primitive in Bob's Brain and derived departments.

**Reference:** [Developer's Guide to Multi-Agent Patterns in ADK](https://developers.googleblog.com/en/developers-guide-to-multi-agent-patterns-in-adk/)

---

## II. Pattern Definition

### What Is Parallel Fan-Out?

A concurrent execution pattern where multiple agents run simultaneously, then results are gathered:

```
                    ┌─────────────┐
                    │ Fan-Out     │
                    └─────┬───────┘
            ┌─────────────┼─────────────┐
            ▼             ▼             ▼
      ┌─────────┐   ┌─────────┐   ┌─────────┐
      │ Agent A │   │ Agent B │   │ Agent C │
      │         │   │         │   │         │
      │output:  │   │output:  │   │output:  │
      │state[a] │   │state[b] │   │state[c] │
      └────┬────┘   └────┬────┘   └────┬────┘
           └─────────────┼─────────────┘
                         ▼
                    ┌─────────┐
                    │ Fan-In  │
                    │Aggregate│
                    └─────────┘
```

### When to Use

- Independent analysis tasks (no dependencies between agents)
- Latency-sensitive operations (3 sequential agents → 1 parallel call)
- Multi-domain audits (ADK, cleanup, index all at once)
- Redundant analysis (multiple models analyzing same input)

### When NOT to Use

- Tasks with dependencies (use `SequentialAgent`)
- Tasks requiring coordination mid-flight (use orchestrator)
- Tasks where failure of one affects others (use conditional logic)

---

## III. Implementation Pattern

### Basic Structure

```python
from google.adk.agents import ParallelAgent, SequentialAgent, LlmAgent

# Step 1: Create agents with unique output_keys
agent_a = LlmAgent(
    name="analyzer_a",
    instruction="Analyze for pattern A",
    output_key="findings_a",  # MUST be unique!
)

agent_b = LlmAgent(
    name="analyzer_b",
    instruction="Analyze for pattern B",
    output_key="findings_b",  # MUST be unique!
)

agent_c = LlmAgent(
    name="analyzer_c",
    instruction="Analyze for pattern C",
    output_key="findings_c",  # MUST be unique!
)

# Step 2: Create ParallelAgent
parallel = ParallelAgent(
    name="parallel_analysis",
    sub_agents=[agent_a, agent_b, agent_c],
)

# Step 3: Create aggregator that reads all outputs
aggregator = LlmAgent(
    name="result_aggregator",
    instruction="Combine {findings_a}, {findings_b}, {findings_c} into report.",
    output_key="aggregated_report",
)

# Step 4: Wrap in SequentialAgent (fan-out, then gather)
workflow = SequentialAgent(
    name="analysis_workflow",
    sub_agents=[parallel, aggregator],
)
```

### Key Requirements

1. **Unique `output_key`**: Each parallel agent MUST have unique `output_key` (race condition prevention)
2. **No Dependencies**: Parallel agents MUST NOT depend on each other's output
3. **Aggregator Pattern**: Use aggregator agent to combine results
4. **State References**: Aggregator uses `{key}` to read from state

---

## IV. Bob's Brain Implementation

### Analysis Workflow

The first `ParallelAgent` implementation in Bob's Brain:

**Location:** `agents/workflows/analysis_workflow.py`

**Pipeline:**
```
┌─────────────────────────────────────────┐
│           parallel_analysis             │
│                                         │
│  iam-adk     iam-cleanup    iam-index   │
│     ↓            ↓             ↓        │
│adk_findings cleanup_finds index_status  │
└─────────────────┬───────────────────────┘
                  ↓
         result_aggregator
                  ↓
         aggregated_analysis
```

**Usage:**
```python
from agents.workflows import create_analysis_workflow

workflow = create_analysis_workflow()
# Execute via Runner or within parent agent
```

### State Flow

| Step | Agent(s) | Input State | Output Key |
|------|----------|-------------|------------|
| 1a | iam-adk | (task input) | `adk_findings` |
| 1b | iam-cleanup | (task input) | `cleanup_findings` |
| 1c | iam-index | (task input) | `index_status` |
| 2 | result_aggregator | `{adk_findings}`, `{cleanup_findings}`, `{index_status}` | `aggregated_analysis` |

### Specialist Agent Updates

Phase P2 added `output_key` to additional specialists:

| Agent | output_key | File |
|-------|------------|------|
| iam-cleanup | `cleanup_findings` | `agents/iam_cleanup/agent.py` |
| iam-index | `index_status` | `agents/iam_index/agent.py` |

---

## V. Best Practices

### DO

```python
# ✅ Unique, descriptive output_keys
output_key="adk_compliance_findings"  # Clear what it contains

# ✅ Aggregator references all parallel outputs
instruction="Combine {adk_findings}, {cleanup_findings}, {index_status}..."

# ✅ Use SequentialAgent to wrap parallel + aggregator
workflow = SequentialAgent(
    sub_agents=[parallel_analysis, aggregator],
)

# ✅ Independent tasks only
# Each agent should work without knowledge of others
```

### DON'T

```python
# ❌ Duplicate output_keys (RACE CONDITION!)
agent_a = LlmAgent(output_key="result")
agent_b = LlmAgent(output_key="result")  # COLLISION!

# ❌ Dependent tasks in parallel
# If agent_b needs agent_a's output, use SequentialAgent instead

# ❌ Missing aggregator
# Parallel results need to be combined somehow

# ❌ Vague output_keys
output_key="data"  # Unclear what this contains
```

---

## VI. Testing

### Required Tests

```python
def test_parallel_agent_has_unique_output_keys():
    """Each parallel agent must have unique output_key."""
    parallel = create_parallel_analysis()
    keys = [a.output_key for a in parallel.sub_agents]
    assert len(keys) == len(set(keys))

def test_aggregator_references_all_outputs():
    """Aggregator should reference all parallel outputs."""
    aggregator = create_result_aggregator()
    assert "{adk_findings}" in aggregator.instruction
    assert "{cleanup_findings}" in aggregator.instruction
    assert "{index_status}" in aggregator.instruction

def test_workflow_structure():
    """Workflow should be Sequential(Parallel, Aggregator)."""
    from google.adk.agents import ParallelAgent, SequentialAgent
    workflow = create_analysis_workflow()
    assert isinstance(workflow, SequentialAgent)
    assert isinstance(workflow.sub_agents[0], ParallelAgent)
```

### Test File

Tests are in: `tests/unit/test_parallel_workflow.py`

---

## VII. Integration with Foreman

### Tool-Based Invocation

The foreman can invoke parallel workflows via tools:

```python
# In foreman's tool profile
def run_analysis_workflow(
    repo_path: str,
    include_adk: bool = True,
    include_cleanup: bool = True,
    include_index: bool = True,
) -> dict:
    """Run the parallel analysis workflow."""
    workflow = create_analysis_workflow()
    # Execute and return results
    return {...}
```

### Latency Improvement

Parallel execution provides significant latency reduction:

| Pattern | Agents | Latency |
|---------|--------|---------|
| Sequential | A → B → C | 3× single agent |
| Parallel | A ∥ B ∥ C | ~1× single agent |

**Expected improvement:** ~67% latency reduction for 3-agent analysis.

---

## VIII. Comparison with Sequential Pattern

| Aspect | Sequential (Phase P1) | Parallel (Phase P2) |
|--------|----------------------|---------------------|
| Use Case | Dependent tasks | Independent tasks |
| Latency | Sum of all agents | Max of any agent |
| State Flow | A → B → C (chain) | A ∥ B ∥ C → gather |
| Output Keys | Can overlap | Must be unique |
| Failure Mode | Stops at failure | Continues others |

### Combined Pattern

Workflows can combine both:

```python
# Phase 1 + Phase 2 combined
workflow = SequentialAgent(
    name="combined_workflow",
    sub_agents=[
        create_parallel_analysis(),  # P2: Concurrent audit
        create_compliance_workflow(),  # P1: Sequential remediation
    ],
)
```

---

## IX. Future Patterns

### Phase P3: Quality Gates (LoopAgent)

```python
from google.adk.agents import LoopAgent

quality_loop = LoopAgent(
    sub_agents=[generator, critic],
    max_iterations=3,
)
```

### Phase P4: Human-in-the-Loop

```python
# Approval gates before execution
workflow = SequentialAgent(
    sub_agents=[
        analyzer,
        human_approval_gate,  # Pauses for approval
        executor,
    ],
)
```

---

## X. Compliance Checklist

Before using `ParallelAgent` in Bob's Brain:

- [ ] Each sub-agent has unique `output_key`
- [ ] Sub-agents are truly independent (no dependencies)
- [ ] Aggregator references all parallel outputs `{key}`
- [ ] Workflow has descriptive name
- [ ] Tests verify output_key uniqueness
- [ ] Tests verify aggregator state references
- [ ] Documentation updated
- [ ] ARV checks pass

---

## XI. References

- **Google Guide:** [Multi-Agent Patterns in ADK](https://developers.googleblog.com/en/developers-guide-to-multi-agent-patterns-in-adk/)
- **ADK Docs:** [Multi-Agent Systems](https://google.github.io/adk-docs/agents/multi-agents/)
- **Gap Analysis:** `234-RA-AUDT-google-multi-agent-patterns-gap-analysis.md`
- **Rollout Plan:** `235-AA-PLAN-multi-agent-patterns-phased-rollout.md`
- **Sequential Pattern:** `6767-DR-STND-sequential-workflow-pattern.md`

---

**Document Status:** Active
**Last Updated:** 2025-12-19
**Next Review:** After Phase P3 (Quality Gates)
