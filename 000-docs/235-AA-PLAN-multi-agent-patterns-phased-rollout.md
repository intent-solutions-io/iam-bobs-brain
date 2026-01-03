# Multi-Agent Patterns Phased Rollout Plan

**Document ID:** 235-AA-PLAN-multi-agent-patterns-phased-rollout
**Type:** After-Action - Plan
**Status:** DRAFT - Awaiting Review
**Created:** 2025-12-19
**Author:** Claude Code (Build Captain)
**Depends On:** 234-RA-AUDT-google-multi-agent-patterns-gap-analysis.md

---

## I. Executive Summary

This plan implements Google's 8 multi-agent patterns in Bob's Brain through 5 phases over ~4 sprints. Each phase has clear gates, organized commits, and sub-agent assignments.

**Strategic Value:**
- Align with official Google ADK patterns
- Create reusable templates for Agent Starter Pack contribution
- Improve department efficiency (parallel execution, iterative refinement)
- Strengthen position as ADK reference implementation

---

## II. Phase Overview

| Phase | Name | Patterns | Priority | Sub-Agents |
|-------|------|----------|----------|------------|
| **P1** | Sequential Workflow | Sequential Pipeline | HIGH | adk-skeleton-coder |
| **P2** | Parallel Execution | Parallel Fan-Out | HIGH | adk-skeleton-coder |
| **P3** | Quality Gates | Generator-Critic, Iterative Refinement | MEDIUM | adk-a2a-wiring-engineer |
| **P4** | Human Approval | Human-in-the-Loop | LOW | frontend-developer |
| **P5** | ASP Contribution | Export to Agent Starter Pack | STRATEGIC | docs-architect |

---

## III. Phase 1: Sequential Workflow Foundation

### Objective
Replace manual A2A orchestration with native `SequentialAgent` for the core compliance workflow.

### Scope
- Create `SequentialAgent` wrapper for: `iam-adk → iam-issue → iam-fix-plan`
- Implement `output_key` state passing
- Maintain backwards compatibility with A2A

### Sub-Agent Assignment

| Task | Sub-Agent | Rationale |
|------|-----------|-----------|
| Design workflow agent structure | `adk-skeleton-coder` | ADK agent scaffolding expert |
| Update foreman to use workflow | `adk-skeleton-coder` | Agent wiring |
| Validate A2A compatibility | `adk-pattern-auditor` | Pattern compliance |
| Update tests | `test-automator` | Test coverage |

### Commits (Organized)

```
Phase 1: Sequential Workflow Foundation
├── feat(agents): add SequentialAgent wrapper for compliance workflow
│   └── agents/workflows/compliance_workflow.py
│   └── Creates SequentialAgent with iam-adk, iam-issue, iam-fix-plan
│
├── feat(agents): add output_key to iam-adk specialist
│   └── agents/iam_adk/agent.py
│   └── output_key="adk_findings" for state passing
│
├── feat(agents): add output_key to iam-issue specialist
│   └── agents/iam_issue/agent.py
│   └── output_key="issue_specs", instruction uses {adk_findings}
│
├── feat(agents): add output_key to iam-fix-plan specialist
│   └── agents/iam_fix_plan/agent.py
│   └── output_key="fix_plans", instruction uses {issue_specs}
│
├── refactor(agents): update foreman to use compliance_workflow
│   └── agents/iam_senior_adk_devops_lead/agent.py
│   └── Import and invoke SequentialAgent
│
├── test(agents): add tests for sequential workflow
│   └── tests/unit/test_sequential_workflow.py
│   └── Verify state passing, error propagation
│
├── docs(000-docs): add sequential workflow pattern doc
│   └── 000-docs/6767-DR-STND-sequential-workflow-pattern.md
│   └── Document pattern for Agent Starter Pack
│
└── chore(agents): update shared_contracts for workflow types
    └── agents/shared_contracts.py
    └── Add WorkflowResult, WorkflowStep types
```

### Implementation Details

**File: `agents/workflows/compliance_workflow.py`**
```python
"""Compliance Workflow - Sequential Pipeline Pattern.

Implements Google's Sequential Pipeline pattern using SequentialAgent.
Reference: https://developers.googleblog.com/en/developers-guide-to-multi-agent-patterns-in-adk/
"""

from google.adk.agents import SequentialAgent
from agents.iam_adk.agent import create_agent as create_iam_adk
from agents.iam_issue.agent import create_agent as create_iam_issue
from agents.iam_fix_plan.agent import create_agent as create_iam_fix_plan


def create_compliance_workflow() -> SequentialAgent:
    """Create the compliance analysis workflow.

    Pipeline: iam-adk → iam-issue → iam-fix-plan
    State flow: findings → issue_specs → fix_plans
    """
    return SequentialAgent(
        name="compliance_workflow",
        sub_agents=[
            create_iam_adk(),        # output_key="adk_findings"
            create_iam_issue(),      # output_key="issue_specs"
            create_iam_fix_plan(),   # output_key="fix_plans"
        ],
    )
```

### Gate Criteria
- [ ] SequentialAgent executes all 3 specialists in order
- [ ] State passes via `session.state` (verified in tests)
- [ ] Foreman can invoke workflow as single call
- [ ] A2A contracts still work (backwards compat)
- [ ] ARV checks pass
- [ ] Docs updated

### Branch
```
feature/phase-p1-sequential-workflow
```

---

## IV. Phase 2: Parallel Execution

### Objective
Add `ParallelAgent` for independent analysis tasks to reduce end-to-end latency.

### Scope
- Create `ParallelAgent` for: `iam-adk`, `iam-cleanup`, `iam-index`
- Implement unique `output_key` per agent
- Add result aggregation step

### Sub-Agent Assignment

| Task | Sub-Agent | Rationale |
|------|-----------|-----------|
| Design parallel workflow | `adk-skeleton-coder` | ADK agent scaffolding |
| Implement aggregator agent | `adk-skeleton-coder` | Result synthesis |
| Validate no race conditions | `adk-pattern-auditor` | Pattern compliance |
| Performance benchmarking | `performance-engineer` | Latency measurement |

### Commits (Organized)

```
Phase 2: Parallel Execution
├── feat(agents): add ParallelAgent for analysis phase
│   └── agents/workflows/parallel_analysis.py
│   └── Concurrent: iam-adk, iam-cleanup, iam-index
│
├── feat(agents): add output_key to iam-cleanup specialist
│   └── agents/iam_cleanup/agent.py
│   └── output_key="cleanup_findings"
│
├── feat(agents): add output_key to iam-index specialist
│   └── agents/iam_index/agent.py
│   └── output_key="index_status"
│
├── feat(agents): add aggregator agent for parallel results
│   └── agents/workflows/result_aggregator.py
│   └── Combines {adk_findings}, {cleanup_findings}, {index_status}
│
├── feat(agents): create combined analysis workflow
│   └── agents/workflows/analysis_workflow.py
│   └── SequentialAgent([parallel_analysis, aggregator])
│
├── test(agents): add tests for parallel execution
│   └── tests/unit/test_parallel_workflow.py
│   └── Verify concurrent execution, unique output_keys
│
├── perf(agents): add latency benchmarks
│   └── tests/benchmarks/test_parallel_latency.py
│   └── Compare sequential vs parallel execution
│
└── docs(000-docs): add parallel workflow pattern doc
    └── 000-docs/6767-DR-STND-parallel-workflow-pattern.md
```

### Implementation Details

**File: `agents/workflows/parallel_analysis.py`**
```python
"""Parallel Analysis - Fan-Out/Gather Pattern.

Implements Google's Parallel Fan-Out pattern using ParallelAgent.
"""

from google.adk.agents import ParallelAgent, SequentialAgent, LlmAgent
from agents.iam_adk.agent import create_agent as create_iam_adk
from agents.iam_cleanup.agent import create_agent as create_iam_cleanup
from agents.iam_index.agent import create_agent as create_iam_index


def create_parallel_analysis() -> ParallelAgent:
    """Create parallel analysis agents.

    Concurrent execution of independent analysis tasks.
    Each agent writes to unique output_key to prevent race conditions.
    """
    return ParallelAgent(
        name="parallel_analysis",
        sub_agents=[
            create_iam_adk(),      # output_key="adk_findings"
            create_iam_cleanup(),  # output_key="cleanup_findings"
            create_iam_index(),    # output_key="index_status"
        ],
    )


def create_result_aggregator() -> LlmAgent:
    """Create aggregator that combines parallel results."""
    return LlmAgent(
        name="result_aggregator",
        model="gemini-2.0-flash-exp",
        instruction="""Aggregate analysis results from parallel agents.

Inputs available in state:
- {adk_findings}: ADK compliance analysis
- {cleanup_findings}: Repository hygiene findings
- {index_status}: Knowledge index status

Output a unified analysis report with:
1. Critical issues (from any source)
2. Medium issues (grouped by source)
3. Recommendations (prioritized)
""",
        output_key="aggregated_analysis",
    )


def create_analysis_workflow() -> SequentialAgent:
    """Create complete analysis workflow with parallel fan-out and gather."""
    return SequentialAgent(
        name="analysis_workflow",
        sub_agents=[
            create_parallel_analysis(),  # Fan-out
            create_result_aggregator(),  # Gather
        ],
    )
```

### Gate Criteria
- [ ] ParallelAgent executes 3 specialists concurrently
- [ ] Unique output_keys prevent race conditions
- [ ] Aggregator successfully combines results
- [ ] Latency reduced by >20% vs sequential
- [ ] ARV checks pass
- [ ] Docs updated

### Branch
```
feature/phase-p2-parallel-execution
```

---

## V. Phase 3: Quality Gates (Generator-Critic + LoopAgent)

### Objective
Implement iterative refinement for the fix workflow using Generator-Critic pattern and LoopAgent.

### Scope
- Wire `iam-fix-impl` (generator) + `iam-qa` (critic) as loop
- Add `LoopAgent` with `max_iterations=3`
- Implement `escalate=True` for early exit on PASS

### Sub-Agent Assignment

| Task | Sub-Agent | Rationale |
|------|-----------|-----------|
| Design loop workflow | `adk-a2a-wiring-engineer` | A2A + workflow expert |
| Update iam-qa for PASS/FAIL output | `adk-skeleton-coder` | Agent modification |
| Add escalation logic | `adk-skeleton-coder` | LoopAgent control |
| Integration testing | `test-automator` | Loop validation |

### Commits (Organized)

```
Phase 3: Quality Gates
├── feat(agents): update iam-qa for PASS/FAIL output format
│   └── agents/iam_qa/agent.py
│   └── Output: {"status": "PASS|FAIL", "reason": "...", "issues": [...]}
│
├── feat(agents): add escalation callback to iam-qa
│   └── agents/iam_qa/agent.py
│   └── after_agent_callback signals escalate=True on PASS
│
├── feat(agents): create fix-review SequentialAgent
│   └── agents/workflows/fix_review.py
│   └── SequentialAgent([iam_fix_impl, iam_qa])
│
├── feat(agents): create LoopAgent for fix iteration
│   └── agents/workflows/fix_loop.py
│   └── LoopAgent(sub_agents=[fix_review], max_iterations=3)
│
├── feat(agents): add output_key to iam-fix-impl
│   └── agents/iam_fix_impl/agent.py
│   └── output_key="fix_output"
│
├── feat(agents): update iam-qa to use {fix_output}
│   └── agents/iam_qa/agent.py
│   └── instruction references {fix_output}
│
├── test(agents): add tests for fix loop
│   └── tests/unit/test_fix_loop.py
│   └── Verify retry on FAIL, exit on PASS, max_iterations
│
├── test(agents): add integration test for full fix workflow
│   └── tests/integration/test_fix_workflow_e2e.py
│   └── End-to-end fix → QA → (retry?) → success
│
└── docs(000-docs): add quality gates pattern doc
    └── 000-docs/6767-DR-STND-quality-gates-pattern.md
```

### Implementation Details

**File: `agents/workflows/fix_loop.py`**
```python
"""Fix Loop - Generator-Critic + Iterative Refinement Patterns.

Implements Google's Generator-Critic and Iterative Refinement patterns.
"""

from google.adk.agents import LoopAgent, SequentialAgent
from agents.iam_fix_impl.agent import create_agent as create_iam_fix_impl
from agents.iam_qa.agent import create_agent as create_iam_qa


def create_fix_review() -> SequentialAgent:
    """Create generator-critic pair.

    Generator: iam-fix-impl produces fix
    Critic: iam-qa reviews and outputs PASS/FAIL
    """
    return SequentialAgent(
        name="fix_review",
        sub_agents=[
            create_iam_fix_impl(),  # output_key="fix_output"
            create_iam_qa(),        # output_key="qa_result", may escalate
        ],
    )


def create_fix_loop() -> LoopAgent:
    """Create iterative refinement loop.

    Loops until:
    - iam-qa signals PASS (escalate=True), or
    - max_iterations reached (fail with context)
    """
    return LoopAgent(
        name="fix_loop",
        sub_agents=[create_fix_review()],
        max_iterations=3,
    )
```

**File: `agents/iam_qa/agent.py` (modification)**
```python
def qa_escalation_callback(ctx):
    """After-agent callback to signal escalation on PASS.

    When QA passes, signal early exit from LoopAgent.
    """
    qa_result = ctx.state.get("qa_result", {})
    if qa_result.get("status") == "PASS":
        ctx.actions.escalate = True
        logger.info("QA PASSED - signaling loop exit")
```

### Gate Criteria
- [ ] LoopAgent retries on FAIL up to 3 times
- [ ] Loop exits early on PASS (escalate=True)
- [ ] Fix quality improves across iterations
- [ ] Max iterations prevents infinite loops
- [ ] ARV checks pass
- [ ] Docs updated

### Branch
```
feature/phase-p3-quality-gates
```

---

## VI. Phase 4: Human-in-the-Loop

### Objective
Add Slack-based approval workflow for high-risk actions before execution.

### Scope
- Create approval tool for `iam-fix-impl` deploys
- Add Slack confirmation workflow
- Implement risk-level classification

### Sub-Agent Assignment

| Task | Sub-Agent | Rationale |
|------|-----------|-----------|
| Design approval workflow | `adk-a2a-wiring-engineer` | Workflow design |
| Implement Slack approval tool | `frontend-developer` | Slack integration |
| Add risk classification | `adk-skeleton-coder` | Agent logic |
| Security review | `security-auditor` | Approval security |

### Commits (Organized)

```
Phase 4: Human-in-the-Loop
├── feat(agents): add risk level classification to fix specs
│   └── agents/shared_contracts.py
│   └── RiskLevel enum: LOW, MEDIUM, HIGH, CRITICAL
│
├── feat(agents): add approval tool for high-risk actions
│   └── agents/tools/approval_tool.py
│   └── request_slack_approval(), check_approval_status()
│
├── feat(service): add approval webhook endpoint
│   └── service/slack_webhook/approval.py
│   └── POST /approve, POST /reject endpoints
│
├── feat(agents): integrate approval tool with iam-fix-impl
│   └── agents/iam_fix_impl/agent.py
│   └── Call approval_tool for HIGH/CRITICAL risk
│
├── feat(infra): add approval state storage (Firestore)
│   └── infra/terraform/modules/approval_store/
│   └── Pending approvals, approval history
│
├── test(agents): add tests for approval workflow
│   └── tests/unit/test_approval_workflow.py
│   └── Verify blocking, approval, rejection
│
├── test(integration): add e2e approval test
│   └── tests/integration/test_approval_e2e.py
│   └── Slack → Approve → Execute flow
│
└── docs(000-docs): add human-in-the-loop pattern doc
    └── 000-docs/6767-DR-STND-human-approval-pattern.md
```

### Implementation Details

**File: `agents/tools/approval_tool.py`**
```python
"""Human-in-the-Loop Approval Tool.

Implements Google's Human-in-the-Loop pattern for high-risk actions.
"""

import asyncio
from typing import Optional
from agents.shared_contracts import RiskLevel, ApprovalStatus

APPROVAL_TIMEOUT_SECONDS = 300  # 5 minutes


async def request_slack_approval(
    action: str,
    risk_level: RiskLevel,
    context: dict,
) -> ApprovalStatus:
    """Request human approval via Slack.

    Args:
        action: Description of action requiring approval
        risk_level: Risk classification (HIGH/CRITICAL triggers approval)
        context: Additional context for approver

    Returns:
        ApprovalStatus with approved flag and optional reason
    """
    if risk_level not in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
        return ApprovalStatus(approved=True, reason="Auto-approved (low risk)")

    # Send Slack message with approve/reject buttons
    approval_id = await send_approval_request(action, context)

    # Wait for response (with timeout)
    try:
        result = await asyncio.wait_for(
            poll_approval_status(approval_id),
            timeout=APPROVAL_TIMEOUT_SECONDS,
        )
        return result
    except asyncio.TimeoutError:
        return ApprovalStatus(
            approved=False,
            reason="Approval timeout - no response within 5 minutes",
        )
```

### Gate Criteria
- [ ] HIGH/CRITICAL actions trigger Slack approval
- [ ] LOW/MEDIUM actions auto-proceed
- [ ] Timeout after 5 minutes (configurable)
- [ ] Approval history stored in Firestore
- [ ] ARV checks pass
- [ ] Docs updated

### Branch
```
feature/phase-p4-human-approval
```

---

## VII. Phase 5: Agent Starter Pack Contribution

### Objective
Export Bob's Brain patterns as reusable templates for Agent Starter Pack contribution.

### Scope
- Package workflow patterns as standalone templates
- Create documentation for each pattern
- Submit PR to Agent Starter Pack

### Sub-Agent Assignment

| Task | Sub-Agent | Rationale |
|------|-----------|-----------|
| Create pattern templates | `docs-architect` | Documentation expert |
| Package for ASP | `deployment-engineer` | Packaging |
| Write contribution docs | `tutorial-engineer` | Tutorial creation |
| Review PR readiness | `code-reviewer` | Quality check |

### Commits (Organized)

```
Phase 5: Agent Starter Pack Contribution
├── feat(templates): extract sequential workflow template
│   └── templates/sequential_workflow/
│   └── Standalone template with README
│
├── feat(templates): extract parallel workflow template
│   └── templates/parallel_workflow/
│   └── Standalone template with README
│
├── feat(templates): extract quality gates template
│   └── templates/quality_gates/
│   └── Generator-Critic + LoopAgent template
│
├── feat(templates): extract foreman-worker template
│   └── templates/foreman_worker/
│   └── Hierarchical decomposition template
│
├── docs(templates): add pattern comparison guide
│   └── templates/PATTERNS.md
│   └── When to use each pattern
│
├── docs(templates): add contribution README
│   └── templates/CONTRIBUTING.md
│   └── How to use templates in new projects
│
└── chore(asp): prepare Agent Starter Pack PR
    └── External PR to GoogleCloudPlatform/agent-starter-pack
    └── Add bobs-brain templates to community section
```

### Contribution Structure for ASP

```
agent-starter-pack/
└── community/
    └── bobs-brain-patterns/
        ├── README.md                    # Overview
        ├── PATTERNS.md                  # Pattern comparison
        ├── sequential_workflow/
        │   ├── README.md
        │   ├── workflow.py
        │   └── example.py
        ├── parallel_workflow/
        │   ├── README.md
        │   ├── workflow.py
        │   └── example.py
        ├── quality_gates/
        │   ├── README.md
        │   ├── loop_workflow.py
        │   └── example.py
        └── foreman_worker/
            ├── README.md
            ├── foreman.py
            ├── worker.py
            └── example.py
```

### Gate Criteria
- [ ] All templates work standalone
- [ ] Each template has complete README
- [ ] Examples are runnable
- [ ] PR submitted to Agent Starter Pack
- [ ] PR approved and merged

### Branch
```
feature/phase-p5-asp-contribution
```

---

## VIII. Timeline and Dependencies

```
Week 1-2: Phase 1 (Sequential Workflow)
    └── Foundation for all other patterns

Week 2-3: Phase 2 (Parallel Execution)
    └── Depends on: Phase 1 (output_key pattern)

Week 3-4: Phase 3 (Quality Gates)
    └── Depends on: Phase 1 (SequentialAgent)
    └── Depends on: Phase 2 (output_key mastery)

Week 5: Phase 4 (Human Approval)
    └── Depends on: Phase 3 (risk classification)
    └── Can run in parallel with Phase 5

Week 5-6: Phase 5 (ASP Contribution)
    └── Depends on: Phases 1-3 complete
    └── Can start extraction while Phase 4 runs
```

### Dependency Graph

```
Phase 1 (Sequential)
    │
    ├───────────────────┐
    ▼                   ▼
Phase 2 (Parallel)   Phase 3 (Quality)
    │                   │
    └───────┬───────────┘
            ▼
    Phase 4 (Human) ◄──┐
            │          │
            ▼          │
    Phase 5 (ASP) ─────┘
```

---

## IX. Sub-Agent Assignment Summary

| Phase | Primary Sub-Agent | Supporting Sub-Agents |
|-------|-------------------|----------------------|
| P1: Sequential | `adk-skeleton-coder` | `adk-pattern-auditor`, `test-automator` |
| P2: Parallel | `adk-skeleton-coder` | `adk-pattern-auditor`, `performance-engineer` |
| P3: Quality | `adk-a2a-wiring-engineer` | `adk-skeleton-coder`, `test-automator` |
| P4: Human | `frontend-developer` | `adk-a2a-wiring-engineer`, `security-auditor` |
| P5: ASP | `docs-architect` | `tutorial-engineer`, `code-reviewer` |

---

## X. Risk Mitigation

| Risk | Mitigation | Owner |
|------|------------|-------|
| Breaking A2A compatibility | Maintain backwards compat, feature flag new patterns | Build Captain |
| LoopAgent infinite loops | Always set max_iterations, add timeout | adk-skeleton-coder |
| Parallel race conditions | Unique output_keys, state isolation | adk-pattern-auditor |
| Approval workflow abuse | Rate limiting, audit logging | security-auditor |
| Scope creep | Strict phase gates, no cross-phase work | Build Captain |

---

## XI. Success Metrics

### Per-Phase Metrics

| Phase | Key Metric | Target |
|-------|-----------|--------|
| P1 | State passing works | 100% test pass |
| P2 | Latency reduction | >20% improvement |
| P3 | Fix success rate | >80% on first loop |
| P4 | Approval workflow | <5min median response |
| P5 | ASP PR merged | 1 PR accepted |

### Overall Metrics

| Metric | Current | Target |
|--------|---------|--------|
| Google patterns implemented | 3/8 | 7/8 |
| Native ADK workflow usage | 0% | 80% |
| Agent Starter Pack contributions | 1 | 2+ |

---

## XII. Review Checklist

Before starting implementation, confirm:

- [ ] **Audit reviewed**: 234-RA-AUDT gap analysis approved
- [ ] **Phase 1 scope clear**: Sequential workflow boundaries defined
- [ ] **Sub-agents available**: Tooling for adk-skeleton-coder ready
- [ ] **Test strategy defined**: How to validate each phase
- [ ] **Rollback plan**: How to revert if issues arise
- [ ] **ASP coordination**: Timing with Agent Starter Pack team

---

## XIII. Approval

**Plan Status:** DRAFT - Awaiting Review

**Requested Actions:**
1. Review gap analysis (234-RA-AUDT)
2. Approve/modify phase scope
3. Confirm sub-agent assignments
4. Approve branch naming convention
5. Confirm ASP contribution timeline

**Next Steps After Approval:**
1. Create `feature/phase-p1-sequential-workflow` branch
2. Invoke `adk-skeleton-coder` for Phase 1 scaffolding
3. Begin implementation per commit plan

---

**Document Status:** Draft
**Awaiting:** User Review
**Created:** 2025-12-19
