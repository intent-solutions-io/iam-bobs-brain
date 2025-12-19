# Quality Gates Pattern Standard

**Document ID:** 6767-DR-STND-quality-gates-pattern
**Type:** Standard (Cross-Repo Canonical)
**Status:** Active
**Created:** 2025-12-19
**Phase:** P3 - Quality Gates

---

## I. Overview

This standard defines how to implement Google's **Generator-Critic** and **Iterative Refinement** patterns using ADK's `LoopAgent` primitive in Bob's Brain and derived departments.

**Reference:** [Developer's Guide to Multi-Agent Patterns in ADK](https://developers.googleblog.com/en/developers-guide-to-multi-agent-patterns-in-adk/)

---

## II. Pattern Definition

### What Are Quality Gates?

A loop pattern where a generator produces output and a critic evaluates it, repeating until quality standards are met:

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

### When to Use

- Implementation → QA review cycles
- Code generation → validation loops
- Content generation → critique refinement
- Any workflow needing "keep trying until good"

### When NOT to Use

- Tasks without clear pass/fail criteria
- Tasks where retry won't improve results (data fetching)
- Infinite loops (always set `max_iterations`)

---

## III. Implementation Pattern

### Basic Structure

```python
from google.adk.agents import LoopAgent, SequentialAgent, LlmAgent

# Step 1: Create generator with output_key
generator = LlmAgent(
    name="generator",
    instruction="Produce implementation based on {plan}",
    output_key="generated_output",
)

# Step 2: Create critic that reads generator output
critic = LlmAgent(
    name="critic",
    instruction="""Review {generated_output} and output verdict.
    Output EXACTLY: {"status": "PASS|FAIL", "reason": "..."}""",
    output_key="qa_verdict",
)

# Step 3: Create sequential pair (generator → critic)
review_pair = SequentialAgent(
    name="review_pair",
    sub_agents=[generator, critic],
)

# Step 4: Wrap in LoopAgent
quality_loop = LoopAgent(
    name="quality_loop",
    sub_agents=[review_pair],
    max_iterations=3,  # Prevent infinite loops!
)
```

### Key Requirements

1. **max_iterations**: ALWAYS set this to prevent infinite loops
2. **escalate**: Critic should signal `ctx.actions.escalate = True` on PASS
3. **Unique output_keys**: Generator and critic need different keys
4. **Structured verdict**: Critic output should be parseable (PASS/FAIL)

---

## IV. Bob's Brain Implementation

### Fix Loop

The first `LoopAgent` implementation in Bob's Brain:

**Location:** `agents/workflows/fix_loop.py`

**Pipeline:**
```
┌─────────────────────────────────────────────────────────────┐
│                  fix_loop (LoopAgent)                       │
│                  max_iterations=3                           │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              fix_review (SequentialAgent)            │   │
│  │                                                      │   │
│  │  iam-fix-impl (generator)  →  iam-qa (critic)       │   │
│  │         ↓                          ↓                 │   │
│  │    fix_output                  qa_result             │   │
│  │                                    │                 │   │
│  │                      PASS: escalate / FAIL: retry    │   │
│  └────────────────────────────────────┼─────────────────┘   │
│                                       │                     │
└───────────────────────────────────────┴─────────────────────┘
```

**Usage:**
```python
from agents.workflows import create_fix_loop

loop = create_fix_loop(max_iterations=3)
# Execute via Runner or within parent agent
```

### State Flow

| Iteration | Step | Agent | Input State | Output Key |
|-----------|------|-------|-------------|------------|
| 1 | 1a | iam-fix-impl | (fix plan) | `fix_output` |
| 1 | 1b | iam-qa | `{fix_output}` | `qa_result` |
| (if FAIL) | | | | |
| 2 | 2a | iam-fix-impl | (fix plan + {qa_result}) | `fix_output` |
| 2 | 2b | iam-qa | `{fix_output}` | `qa_result` |
| (if PASS) | exit | | | |

### Specialist Agent Updates

Phase P3 added `output_key` to additional specialists:

| Agent | output_key | File |
|-------|------------|------|
| iam-fix-impl | `fix_output` | `agents/iam_fix_impl/agent.py` |
| iam-qa | `qa_result` | `agents/iam_qa/agent.py` |

---

## V. Escalation Mechanism

### How Loop Exit Works

The LoopAgent continues until:
1. **Escalation**: Critic signals `ctx.actions.escalate = True`
2. **Max iterations**: Loop hits `max_iterations` limit

### Escalation Callback

```python
def qa_escalation_callback(ctx):
    """After-agent callback to signal loop exit on PASS."""
    qa_result = ctx.state.get("qa_result", {})

    # Check for PASS status
    if isinstance(qa_result, dict):
        if qa_result.get("status") == "PASS":
            ctx.actions.escalate = True
            logger.info("✅ QA PASSED - signaling loop exit")
    elif isinstance(qa_result, str):
        if "PASS" in qa_result.upper():
            ctx.actions.escalate = True
```

### Critic Output Format

The critic MUST output a parseable verdict:

```json
{
  "status": "PASS",
  "reason": "All tests pass, 92% coverage, no blocking issues",
  "issues": []
}
```

or

```json
{
  "status": "FAIL",
  "reason": "Tests failing, coverage below 85%",
  "issues": [
    {"type": "test_failure", "file": "test_foo.py", "message": "..."},
    {"type": "coverage", "actual": 72, "required": 85}
  ]
}
```

---

## VI. Best Practices

### DO

```python
# ✅ Always set max_iterations
loop = LoopAgent(max_iterations=3)

# ✅ Clear PASS/FAIL criteria in critic instruction
instruction="Output EXACTLY: {\"status\": \"PASS|FAIL\", ...}"

# ✅ Generator uses critic feedback
instruction="Improve based on {qa_result} if present..."

# ✅ Unique output_keys
generator = LlmAgent(output_key="generated")
critic = LlmAgent(output_key="verdict")
```

### DON'T

```python
# ❌ No max_iterations (infinite loop risk!)
loop = LoopAgent(sub_agents=[...])  # MISSING max_iterations!

# ❌ Same output_key (state collision)
generator = LlmAgent(output_key="result")
critic = LlmAgent(output_key="result")  # COLLISION!

# ❌ Vague critic criteria
instruction="Review and say if it's good"  # Not parseable!

# ❌ Generator ignores critic feedback
instruction="Generate code"  # Doesn't improve on retry!
```

---

## VII. Testing

### Required Tests

```python
def test_loop_has_max_iterations():
    """Loop must have max_iterations set."""
    loop = create_fix_loop()
    assert loop.max_iterations is not None
    assert loop.max_iterations > 0

def test_escalation_callback_exits_on_pass():
    """Callback should set escalate=True on PASS."""
    callback = create_qa_escalation_callback()
    ctx = MockContext(state={"qa_result": {"status": "PASS"}})
    callback(ctx)
    assert ctx.actions.escalate is True

def test_escalation_callback_continues_on_fail():
    """Callback should NOT escalate on FAIL."""
    callback = create_qa_escalation_callback()
    ctx = MockContext(state={"qa_result": {"status": "FAIL"}})
    callback(ctx)
    assert ctx.actions.escalate is False

def test_generator_critic_output_keys_unique():
    """Generator and critic must have unique output_keys."""
    review = create_fix_review()
    keys = [a.output_key for a in review.sub_agents]
    assert len(keys) == len(set(keys))
```

### Test File

Tests are in: `tests/unit/test_fix_loop.py`

---

## VIII. Integration with Foreman

### Tool-Based Invocation

The foreman can invoke quality gate workflows via tools:

```python
# In foreman's tool profile
def run_fix_loop(fix_plan: dict, max_iterations: int = 3) -> dict:
    """Run the fix implementation loop with QA gates."""
    loop = create_fix_loop(max_iterations=max_iterations)
    # Execute and return results
    return {...}
```

### Workflow Decision Tree

```
Foreman receives fix request
    │
    ├─ Simple fix (low risk)?
    │   └─ Single iam-fix-impl call
    │
    └─ Complex fix (high risk)?
        └─ Use fix_loop (guaranteed QA)
            │
            ├─ Iteration 1: impl → QA
            │   └─ PASS? → Done
            │   └─ FAIL? → Continue
            │
            ├─ Iteration 2: impl → QA
            │   └─ PASS? → Done
            │   └─ FAIL? → Continue
            │
            └─ Iteration 3: impl → QA
                └─ PASS? → Done
                └─ FAIL? → Report max retries reached
```

---

## IX. Comparison with Other Patterns

| Aspect | Sequential (P1) | Parallel (P2) | Loop (P3) |
|--------|----------------|---------------|-----------|
| Use Case | Dependent steps | Independent tasks | Iterative refinement |
| Structure | A → B → C | A ∥ B ∥ C | (A → B) × N |
| Exit Condition | Completes all | All finish | PASS or max |
| Output Keys | Chain | Unique per agent | Unique + structured |
| Failure Mode | Stops at failure | Continues others | Retries up to N |

### Combined Patterns

Workflows can combine all three:

```python
# Full SWE workflow: parallel audit → sequential plan → loop fix
workflow = SequentialAgent(
    name="full_swe_workflow",
    sub_agents=[
        create_analysis_workflow(),     # P2: Parallel audit
        create_compliance_workflow(),   # P1: Sequential planning
        create_fix_loop(),              # P3: Loop implementation
    ],
)
```

---

## X. Compliance Checklist

Before using `LoopAgent` in Bob's Brain:

- [ ] `max_iterations` is set (prevent infinite loops)
- [ ] Critic has clear PASS/FAIL output format
- [ ] Escalation mechanism implemented
- [ ] Generator uses critic feedback on retry
- [ ] Unique `output_key` for each agent
- [ ] Tests verify escalation logic
- [ ] Documentation updated
- [ ] ARV checks pass

---

## XI. References

- **Google Guide:** [Multi-Agent Patterns in ADK](https://developers.googleblog.com/en/developers-guide-to-multi-agent-patterns-in-adk/)
- **ADK Docs:** [Multi-Agent Systems](https://google.github.io/adk-docs/agents/multi-agents/)
- **Gap Analysis:** `234-RA-AUDT-google-multi-agent-patterns-gap-analysis.md`
- **Rollout Plan:** `235-AA-PLAN-multi-agent-patterns-phased-rollout.md`
- **Sequential Pattern:** `6767-DR-STND-sequential-workflow-pattern.md`
- **Parallel Pattern:** `6767-DR-STND-parallel-execution-pattern.md`

---

**Document Status:** Active
**Last Updated:** 2025-12-19
**Next Review:** After Phase P4 (Human-in-the-Loop)
