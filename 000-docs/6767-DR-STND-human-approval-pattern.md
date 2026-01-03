# Human-in-the-Loop Approval Pattern Standard

**Document ID:** 6767-DR-STND-human-approval-pattern
**Type:** Standard (Cross-Repo Canonical)
**Status:** Active
**Created:** 2025-12-19
**Phase:** P4 - Human-in-the-Loop

---

## I. Overview

This standard defines how to implement Google's **Human-in-the-Loop** pattern in Bob's Brain and derived departments. This pattern ensures that high-risk actions require human approval before execution.

**Reference:** [Developer's Guide to Multi-Agent Patterns in ADK](https://developers.googleblog.com/en/developers-guide-to-multi-agent-patterns-in-adk/)

---

## II. Pattern Definition

### What is Human-in-the-Loop?

A safety pattern where agents pause execution and request human approval before performing high-risk actions:

```
┌─────────────────────────────────────────────────────────────┐
│                   Approval Workflow                         │
│                                                             │
│  ┌─────────────┐     ┌─────────────┐     ┌─────────────┐   │
│  │    Risk     │     │  Approval   │     │    Fix      │   │
│  │  Assessor   │ ──► │    Gate     │ ──► │    Loop     │   │
│  │             │     │             │     │  (Phase 3)  │   │
│  └─────────────┘     └─────────────┘     └─────────────┘   │
│         │                   │                   │          │
│    Classifies          LOW/MED:            Executes        │
│    risk level          Auto-approve        with QA         │
│                             │                              │
│                        HIGH/CRIT:                          │
│                        Wait for                            │
│                        human approval                      │
│                             │                              │
│                     ┌───────┴───────┐                      │
│                     │               │                      │
│                  Approved       Rejected                   │
│                     │               │                      │
│                 Continue          Abort                    │
└─────────────────────┴───────────────┴──────────────────────┘
```

### When to Use

- Production deployments
- Database migrations
- Infrastructure changes (Terraform)
- Security-sensitive operations
- Destructive actions (delete, destroy)
- Any action with significant blast radius

### When NOT to Use

- Documentation updates (LOW risk)
- Test additions (LOW risk)
- Code refactoring (MEDIUM risk, auto-approved)
- Local development changes
- CI/CD pipeline runs (automated)

---

## III. Risk Classification

### Risk Levels

| Level | Description | Approval | Examples |
|-------|-------------|----------|----------|
| **LOW** | Safe, reversible, minimal impact | Auto-approve | Docs, tests, linting |
| **MEDIUM** | Limited scope, recoverable | Auto-approve + log | Refactoring, bug fixes |
| **HIGH** | Significant scope, requires review | Human approval | Deployments, migrations |
| **CRITICAL** | Production impact, security sensitive | Human approval + escalation | Data deletion, auth changes |

### Classification Rules

```python
# File-based classification
if any(f in ["infra/", "terraform/"] for f in files):
    return RiskLevel.HIGH
if any(f in ["service/", ".github/workflows/"] for f in files):
    return RiskLevel.HIGH
if any(f in ["agents/", "config/"] for f in files):
    return RiskLevel.MEDIUM
# Default: LOW

# Action-based classification
critical_keywords = ["delete", "destroy", "drop", "production"]
high_keywords = ["deploy", "release", "migrate", "security"]
medium_keywords = ["refactor", "update", "fix"]
```

---

## IV. Implementation

### Contract Definitions

**Location:** `agents/iam_contracts.py`

```python
from enum import Enum

class RiskLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

    @classmethod
    def requires_approval(cls, level: "RiskLevel") -> bool:
        return level in [cls.HIGH, cls.CRITICAL]


class ApprovalStatus(Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    TIMEOUT = "timeout"
    AUTO_APPROVED = "auto_approved"


@dataclass
class ApprovalRequest:
    request_id: str
    action: str
    description: str
    risk_level: RiskLevel
    context: Dict[str, Any]
    requested_by: str  # SPIFFE ID
    requested_at: datetime
    timeout_seconds: int = 300
    files_affected: List[str]
    estimated_impact: str


@dataclass
class ApprovalResponse:
    request_id: str
    status: ApprovalStatus
    approved: bool
    reason: str
    approved_by: Optional[str]
    approved_at: Optional[datetime]
    conditions: List[str]  # Conditional approval
```

### Approval Tool

**Location:** `agents/tools/approval_tool.py`

```python
def classify_risk_level(
    action: str,
    files_affected: List[str],
    context: Dict[str, Any],
) -> RiskLevel:
    """Classify risk based on action and files."""
    # Critical indicators
    if any(kw in action.lower() for kw in ["delete", "destroy", "production"]):
        return RiskLevel.CRITICAL

    # High indicators
    if any(kw in action.lower() for kw in ["deploy", "migrate", "security"]):
        return RiskLevel.HIGH
    if any("infra/" in f or "terraform/" in f for f in files_affected):
        return RiskLevel.HIGH

    # Medium indicators
    if any(kw in action.lower() for kw in ["refactor", "update", "fix"]):
        return RiskLevel.MEDIUM

    return RiskLevel.LOW


async def request_approval(request: ApprovalRequest) -> ApprovalResponse:
    """Request human approval for high-risk action."""
    if not RiskLevel.requires_approval(request.risk_level):
        return ApprovalResponse(
            request_id=request.request_id,
            status=ApprovalStatus.AUTO_APPROVED,
            approved=True,
            reason=f"Auto-approved ({request.risk_level.value} risk)",
            approved_by="system",
        )

    # Queue for human approval
    await send_slack_notification(request)

    # Wait for response
    try:
        return await asyncio.wait_for(
            poll_for_approval(request.request_id),
            timeout=request.timeout_seconds,
        )
    except asyncio.TimeoutError:
        return ApprovalResponse(
            request_id=request.request_id,
            status=ApprovalStatus.TIMEOUT,
            approved=False,
            reason="Approval timeout",
        )
```

### Approval Workflow

**Location:** `agents/workflows/approval_workflow.py`

```python
from google.adk.agents import LlmAgent, SequentialAgent

def create_risk_assessor() -> LlmAgent:
    """Create risk assessment agent."""
    return LlmAgent(
        name="risk_assessor",
        instruction="""Analyze fix plan and classify risk.
        Output: {"risk_level": "LOW|MEDIUM|HIGH|CRITICAL", "reason": "..."}
        """,
        output_key="risk_assessment",
    )


def create_approval_gate_callback(spiffe_id: str):
    """Create approval gate callback."""
    def callback(ctx):
        risk_assessment = ctx.state.get("risk_assessment", {})
        risk_level = RiskLevel.from_string(risk_assessment.get("risk_level"))

        if not requires_approval(risk_level):
            ctx.state["approval_result"] = {"status": "auto_approved"}
            return

        # Queue for human approval
        request = create_approval_request(...)
        ctx.state["pending_approval"] = request.to_dict()
        ctx.state["approval_result"] = {"status": "pending"}

    return callback


def create_approval_workflow(max_fix_iterations: int = 3) -> SequentialAgent:
    """Create full approval workflow."""
    risk_assessor = create_risk_assessor()
    risk_assessor.after_agent_callback = create_approval_gate_callback()

    fix_loop = create_fix_loop(max_iterations=max_fix_iterations)

    return SequentialAgent(
        name="approval_workflow",
        sub_agents=[risk_assessor, fix_loop],
    )
```

---

## V. State Flow

| Step | Agent | Input State | Output Key |
|------|-------|-------------|------------|
| 1 | risk_assessor | fix_plan | risk_assessment |
| 2 | approval_gate | risk_assessment | approval_result |
| (if approved) | | | |
| 3 | iam-fix-impl | fix_plan | fix_output |
| 4 | iam-qa | fix_output | qa_result |
| (loop if FAIL) | | | |

---

## VI. Slack Integration

### Approval Message Format

```
┌─────────────────────────────────────────────────────────────┐
│ 🔐 APPROVAL REQUIRED                                        │
│                                                             │
│ Action: Deploy to production                                │
│ Risk Level: 🔴 HIGH                                         │
│                                                             │
│ Files Affected:                                             │
│ • infra/terraform/main.tf                                   │
│ • service/main.py                                           │
│                                                             │
│ Requested by: iam-fix-impl                                  │
│ Timeout: 5 minutes                                          │
│                                                             │
│ [✅ Approve]  [❌ Reject]                                   │
└─────────────────────────────────────────────────────────────┘
```

### Webhook Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/approval/callback` | POST | Receive Slack button callbacks |
| `/approval/status` | GET | Check approval status |
| `/approval/pending` | GET | List pending approvals |

---

## VII. Best Practices

### DO

```python
# ✅ Always classify risk before execution
risk_level = classify_risk_level(action, files, context)

# ✅ Set reasonable timeout
request = ApprovalRequest(timeout_seconds=300)

# ✅ Include context for approver
request = ApprovalRequest(
    context={"fix_plan": plan, "qa_result": result},
    estimated_impact="Production service restart",
)

# ✅ Log all approval decisions
logger.info(f"Approval {response.status}: {response.reason}")

# ✅ Handle timeout gracefully
if response.status == ApprovalStatus.TIMEOUT:
    return {"error": "Approval timeout - action not executed"}
```

### DON'T

```python
# ❌ Skip risk classification
# Always classify to avoid accidental approvals

# ❌ Infinite timeout
request = ApprovalRequest(timeout_seconds=0)  # BAD!

# ❌ Missing context
request = ApprovalRequest(context={})  # Approver needs info!

# ❌ Ignore rejection
if response.status == ApprovalStatus.REJECTED:
    execute_anyway()  # NEVER do this!
```

---

## VIII. Testing

### Required Tests

```python
def test_low_risk_auto_approves():
    """LOW risk should auto-approve."""
    assert not requires_approval(RiskLevel.LOW)

def test_high_risk_requires_approval():
    """HIGH risk should require approval."""
    assert requires_approval(RiskLevel.HIGH)

def test_classify_risk_deployment():
    """Deployments should be HIGH risk."""
    level = classify_risk_level("Deploy to production", [], {})
    assert level == RiskLevel.HIGH

def test_approval_timeout():
    """Timeout should reject."""
    # Mock slow approval
    response = await request_approval(request)
    assert response.status == ApprovalStatus.TIMEOUT
    assert response.approved is False

def test_callback_auto_approves_low():
    """Callback should auto-approve LOW risk."""
    callback = create_approval_gate_callback()
    ctx = MockContext(state={"risk_assessment": {"risk_level": "LOW"}})
    callback(ctx)
    assert ctx.state["approval_result"]["status"] == "auto_approved"
```

### Test File

Tests are in: `tests/unit/test_approval_workflow.py`

---

## IX. Integration with Other Patterns

### Combined with Quality Gates (Phase P3)

```python
# Approval workflow wraps fix loop
workflow = SequentialAgent(
    name="approval_workflow",
    sub_agents=[
        risk_assessor,  # Phase P4: Classify risk
        fix_loop,       # Phase P3: LoopAgent with QA
    ],
)
```

### Full SWE Pipeline

```python
# Complete pipeline: P2 → P4 → P3
workflow = SequentialAgent(
    name="full_swe_workflow",
    sub_agents=[
        create_analysis_workflow(),   # P2: Parallel analysis
        create_approval_workflow(),   # P4: Approval + P3 fix loop
    ],
)
```

### Foreman Decision Tree

```
Foreman receives fix request
    │
    ├─ Low risk (docs, tests)?
    │   └─ Direct fix_loop (no approval)
    │
    ├─ Medium risk (refactoring)?
    │   └─ fix_loop with logging
    │
    └─ High/Critical risk?
        └─ approval_workflow (blocks until approved)
            │
            ├─ Approved → fix_loop → QA
            │
            └─ Rejected → Report to Bob
```

---

## X. Compliance Checklist

Before using Human-in-the-Loop in Bob's Brain:

- [ ] Risk classification logic implemented
- [ ] Approval contracts defined (ApprovalRequest, ApprovalResponse)
- [ ] Approval tool available (`request_human_approval`)
- [ ] Slack integration configured (or alternative notification)
- [ ] Timeout handling implemented
- [ ] Rejection handling implemented
- [ ] Audit logging enabled
- [ ] Tests verify approval flow
- [ ] Documentation updated
- [ ] ARV checks pass

---

## XI. Security Considerations

### Authentication

- Verify approver identity via Slack OAuth
- Log SPIFFE ID of requesting agent
- Maintain audit trail of all approvals

### Authorization

- Only designated approvers can approve HIGH/CRITICAL
- Rate limit approval requests
- Alert on unusual approval patterns

### Audit Trail

Store in Firestore:
- Request ID
- Requester SPIFFE ID
- Risk level
- Files affected
- Approver identity
- Decision (approve/reject)
- Timestamp
- Conditions (if any)

---

## XII. References

- **Google Guide:** [Multi-Agent Patterns in ADK](https://developers.googleblog.com/en/developers-guide-to-multi-agent-patterns-in-adk/)
- **ADK Docs:** [Multi-Agent Systems](https://google.github.io/adk-docs/agents/multi-agents/)
- **Gap Analysis:** `234-RA-AUDT-google-multi-agent-patterns-gap-analysis.md`
- **Rollout Plan:** `235-AA-PLAN-multi-agent-patterns-phased-rollout.md`
- **Sequential Pattern:** `6767-DR-STND-sequential-workflow-pattern.md`
- **Parallel Pattern:** `6767-DR-STND-parallel-execution-pattern.md`
- **Quality Gates Pattern:** `6767-DR-STND-quality-gates-pattern.md`

---

**Document Status:** Active
**Last Updated:** 2025-12-19
**Next Review:** After Phase P5 (Agent Starter Pack Contribution)
