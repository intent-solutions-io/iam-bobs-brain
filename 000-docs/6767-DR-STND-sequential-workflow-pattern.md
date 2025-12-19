# Sequential Workflow Pattern Standard

**Document ID:** 6767-DR-STND-sequential-workflow-pattern
**Type:** Standard (Cross-Repo Canonical)
**Status:** Active
**Created:** 2025-12-19
**Phase:** P1 - Sequential Workflow Foundation

---

## I. Overview

This standard defines how to implement Google's **Sequential Pipeline Pattern** using ADK's `SequentialAgent` primitive in Bob's Brain and derived departments.

**Reference:** [Developer's Guide to Multi-Agent Patterns in ADK](https://developers.googleblog.com/en/developers-guide-to-multi-agent-patterns-in-adk/)

---

## II. Pattern Definition

### What Is Sequential Pipeline?

A linear assembly-line pattern where agents execute in order, passing state between steps:

```
Agent A → Agent B → Agent C
   ↓         ↓         ↓
output_key  reads A   reads B
   ↓         ↓         ↓
state["a"] state["b"] state["c"]
```

### When to Use

- Tasks with clear dependencies (output of one feeds another)
- Multi-step workflows (audit → issue → plan → fix → test)
- Pipelines where order matters
- Data transformation chains

### When NOT to Use

- Independent tasks (use `ParallelAgent`)
- Tasks requiring iteration (use `LoopAgent`)
- Single-step operations (use direct agent call)

---

## III. Implementation Pattern

### Basic Structure

```python
from google.adk.agents import LlmAgent, SequentialAgent

# Step 1: Create agents with output_key
agent_a = LlmAgent(
    name="step_a",
    instruction="Analyze input and produce findings.",
    output_key="findings",  # Writes to session.state["findings"]
)

agent_b = LlmAgent(
    name="step_b",
    instruction="Process {findings} and create specifications.",
    output_key="specs",  # Reads {findings}, writes to state["specs"]
)

agent_c = LlmAgent(
    name="step_c",
    instruction="Generate plans from {specs}.",
    output_key="plans",  # Reads {specs}, writes to state["plans"]
)

# Step 2: Create SequentialAgent
workflow = SequentialAgent(
    name="my_workflow",
    sub_agents=[agent_a, agent_b, agent_c],
)
```

### Key Requirements

1. **Unique `output_key`**: Each agent MUST have a unique `output_key`
2. **State References**: Use `{key}` in instructions to read from state
3. **Order Matters**: Sub-agents execute in list order
4. **No Cycles**: Sequential workflows are one-way (use `LoopAgent` for cycles)

---

## IV. Bob's Brain Implementation

### Compliance Workflow

The first SequentialAgent implementation in Bob's Brain:

**Location:** `agents/workflows/compliance_workflow.py`

**Pipeline:**
```
iam-adk (analysis) → iam-issue (specs) → iam-fix-plan (plans)
      ↓                    ↓                    ↓
 adk_findings          issue_specs          fix_plans
```

**Usage:**
```python
from agents.workflows import create_compliance_workflow

workflow = create_compliance_workflow()
# Execute via Runner or within parent agent
```

### State Flow

| Step | Agent | Input State | Output Key |
|------|-------|-------------|------------|
| 1 | workflow_analysis | (task input) | `adk_findings` |
| 2 | workflow_issue | `{adk_findings}` | `issue_specs` |
| 3 | workflow_planning | `{issue_specs}` | `fix_plans` |

### Specialist Agent Updates

Phase P1 added `output_key` to specialist agents:

| Agent | output_key | File |
|-------|------------|------|
| iam-adk | `adk_findings` | `agents/iam_adk/agent.py` |
| iam-issue | `issue_specs` | `agents/iam_issue/agent.py` |
| iam-fix-plan | `fix_plans` | `agents/iam_fix_plan/agent.py` |

---

## V. Best Practices

### DO

```python
# ✅ Unique, descriptive output_keys
output_key="compliance_findings"  # Clear what it contains

# ✅ Reference state in instruction
instruction="Analyze {compliance_findings} and create issues."

# ✅ Clear pipeline naming
workflow = SequentialAgent(
    name="compliance_workflow",  # Describes the workflow
    sub_agents=[...],
)
```

### DON'T

```python
# ❌ Duplicate output_keys (race condition!)
agent_a = LlmAgent(output_key="result")
agent_b = LlmAgent(output_key="result")  # COLLISION!

# ❌ Missing state reference
instruction="Create issues."  # Doesn't read from previous step!

# ❌ Vague naming
workflow = SequentialAgent(name="workflow1")  # Unclear purpose
```

---

## VI. Testing

### Required Tests

```python
def test_workflow_has_unique_output_keys():
    """Each agent must have unique output_key."""
    workflow = create_compliance_workflow()
    keys = [a.output_key for a in workflow.sub_agents]
    assert len(keys) == len(set(keys))

def test_agents_reference_previous_state():
    """Agents should reference previous agent's output."""
    workflow = create_compliance_workflow()
    # Agent 2 should reference Agent 1's output
    assert "{adk_findings}" in workflow.sub_agents[1].instruction

def test_workflow_is_sequential_agent():
    """Workflow must be SequentialAgent type."""
    from google.adk.agents import SequentialAgent
    workflow = create_compliance_workflow()
    assert isinstance(workflow, SequentialAgent)
```

### Test File

Tests are in: `tests/unit/test_sequential_workflow.py`

---

## VII. Integration with Foreman

### Tool-Based Invocation

The foreman can invoke workflows via tools:

```python
# In foreman's tool profile
def run_compliance_workflow(repo_path: str, rules: list[str]) -> dict:
    """Run the full compliance analysis workflow."""
    workflow = create_compliance_workflow()
    # Execute and return results
    return {...}
```

### Direct Agent Invocation

For more control, foreman can manage workflow execution directly:

```python
from agents.workflows import create_compliance_workflow
from google.adk import Runner

workflow = create_compliance_workflow()
runner = Runner(agent=workflow, ...)
result = await runner.run(...)
```

---

## VIII. Future Patterns

### Phase P2: Parallel Fan-Out

```python
from google.adk.agents import ParallelAgent, SequentialAgent

parallel = ParallelAgent(
    sub_agents=[agent_a, agent_b, agent_c],  # Concurrent
)
aggregator = LlmAgent(
    instruction="Combine {result_a}, {result_b}, {result_c}",
)
workflow = SequentialAgent(
    sub_agents=[parallel, aggregator],  # Fan-out then gather
)
```

### Phase P3: Quality Gates (LoopAgent)

```python
from google.adk.agents import LoopAgent

quality_loop = LoopAgent(
    sub_agents=[generator, critic],
    max_iterations=3,
)
```

---

## IX. Compliance Checklist

Before using SequentialAgent in Bob's Brain:

- [ ] Each sub-agent has unique `output_key`
- [ ] Instructions reference state variables `{key}`
- [ ] Workflow has descriptive name
- [ ] Tests verify state flow
- [ ] Documentation updated
- [ ] ARV checks pass

---

## X. References

- **Google Guide:** [Multi-Agent Patterns in ADK](https://developers.googleblog.com/en/developers-guide-to-multi-agent-patterns-in-adk/)
- **ADK Docs:** [Multi-Agent Systems](https://google.github.io/adk-docs/agents/multi-agents/)
- **Gap Analysis:** `234-RA-AUDT-google-multi-agent-patterns-gap-analysis.md`
- **Rollout Plan:** `235-AA-PLAN-multi-agent-patterns-phased-rollout.md`

---

**Document Status:** Active
**Last Updated:** 2025-12-19
**Next Review:** After Phase P2 (Parallel Execution)
