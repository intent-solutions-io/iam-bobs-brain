# Mandates, Budgets, and Approvals Standard

**Document ID:** 253-DR-STND-mandates-budgets-approvals
**Status:** ACTIVE
**Created:** 2026-01-02
**Author:** Claude Code
**Phase:** E (Enterprise Controls)

---

## 1. Purpose

This document defines the **enterprise control extensions** to the Mandate system for Bob's Brain. It establishes:

- Risk tier classification (R0-R4)
- Tool allowlists for operation restrictions
- Data classification levels
- Approval workflows for high-risk operations

---

## 2. Mandate Enterprise Fields

### 2.1 Risk Tier

Controls the level of authorization required for operations.

| Tier | Description | Requirements |
|------|-------------|--------------|
| R0 | Read-only, no side effects | None (default) |
| R1 | Local changes, reversible | Mandate optional |
| R2 | External writes (GitHub, etc.) | Mandate + budget |
| R3 | Infrastructure changes | Mandate + human approval |
| R4 | Payment/financial | Mandate + 2-person approval |

**Default:** `R0` (no restrictions)

```python
from agents.shared_contracts import Mandate

# R0: No restrictions
mandate = Mandate(mandate_id="m-001", intent="read files", risk_tier="R0")

# R3: Requires approval
mandate = Mandate(
    mandate_id="m-002",
    intent="deploy infrastructure",
    risk_tier="R3",
    approval_state="pending"
)
```

### 2.2 Tool Allowlist

Restricts which tools can be used during execution.

- **Empty list** = all tools allowed
- **Non-empty list** = only listed tools allowed

```python
mandate = Mandate(
    mandate_id="m-001",
    intent="code review",
    tool_allowlist=["search_code", "read_file", "analyze_code"]
)

# Check if tool is allowed
if mandate.can_use_tool("delete_file"):
    print("Allowed")
else:
    print("Blocked")  # This will print
```

### 2.3 Data Classification

Indicates sensitivity level of data being processed.

| Level | Description |
|-------|-------------|
| `public` | No restrictions on visibility |
| `internal` | Organization-internal only (default) |
| `confidential` | Limited access, business-sensitive |
| `restricted` | Highest sensitivity, regulatory requirements |

```python
mandate = Mandate(
    mandate_id="m-001",
    intent="process customer data",
    data_classification="confidential"
)
```

### 2.4 Approval Fields

For R3/R4 operations requiring human approval:

| Field | Type | Description |
|-------|------|-------------|
| `approval_state` | Literal | "pending", "approved", "denied", "auto" |
| `approver_id` | Optional[str] | ID of approving user |
| `approval_timestamp` | Optional[datetime] | When approval was granted |

---

## 3. Approval Workflow

### 3.1 State Machine

```
                    ┌─────────┐
                    │  auto   │ (R0-R2: no approval needed)
                    └─────────┘

     ┌─────────┐    ┌─────────┐    ┌──────────┐
     │ pending │───>│ approved│───>│ execution│
     └─────────┘    └─────────┘    └──────────┘
          │
          └────────>┌─────────┐
                    │ denied  │
                    └─────────┘
```

### 3.2 Usage

```python
from agents.shared_contracts import Mandate

# Create mandate for R3 operation
mandate = Mandate(
    mandate_id="m-deploy-001",
    intent="deploy to production",
    risk_tier="R3",
    approval_state="pending"
)

# Check approval status
if mandate.requires_approval():
    print("Human approval required")

if mandate.is_pending_approval():
    print("Waiting for approval")

# Approve the mandate
mandate.approve("admin@example.com")
print(f"Approved by: {mandate.approver_id}")
print(f"Approved at: {mandate.approval_timestamp}")

# Now can proceed
if mandate.is_approved():
    execute_deployment()
```

---

## 4. Mandate Methods

### 4.1 Approval Methods

```python
# Check if approval is required (R3/R4)
requires_approval() -> bool

# Check if approved (or doesn't need approval)
is_approved() -> bool

# Check if pending approval
is_pending_approval() -> bool

# Check if denied
is_denied() -> bool

# Approve the mandate
approve(approver_id: str) -> None

# Deny the mandate
deny(approver_id: str) -> None
```

### 4.2 Tool Allowlist Methods

```python
# Check if tool is allowed
can_use_tool(tool_name: str) -> bool
```

### 4.3 Specialist Invocation

Updated `can_invoke_specialist()` now includes approval checks:

```python
def can_invoke_specialist(self, specialist_name: str) -> bool:
    """Check if specialist is authorized and all constraints satisfied."""
    if self.is_expired():
        return False
    if self.is_budget_exhausted():
        return False
    if self.is_iterations_exhausted():
        return False
    if self.authorized_specialists and specialist_name not in self.authorized_specialists:
        return False
    # Enterprise control: check approval for R3/R4
    if self.requires_approval() and not self.is_approved():
        return False
    return True
```

---

## 5. Integration with A2A Dispatcher

The dispatcher validates mandates before specialist invocation:

```python
# In agents/a2a/dispatcher.py
def validate_mandate(task: A2ATask) -> None:
    """Validate mandate including enterprise controls."""
    # ... parse mandate from task ...

    # Run policy gate preflight checks
    gate_results = PolicyGate.preflight_check(
        specialist_name=task.specialist,
        risk_tier=mandate.risk_tier,
        mandate=mandate
    )

    # Check for blocking gates
    if not PolicyGate.is_all_gates_passed(gate_results):
        blocking = PolicyGate.get_blocking_gates(gate_results)
        raise A2AError(f"Policy gate check failed: {blocking}")
```

---

## 6. Example Use Cases

### 6.1 Code Review (R0)

```python
mandate = Mandate(
    mandate_id="m-review-001",
    intent="review code changes",
    risk_tier="R0",  # Read-only
    tool_allowlist=["search_code", "read_file", "analyze_code"]
)
```

### 6.2 GitHub Issue Creation (R2)

```python
mandate = Mandate(
    mandate_id="m-issue-001",
    intent="create GitHub issues",
    risk_tier="R2",  # External writes
    budget_limit=1.0,
    authorized_specialists=["iam-triage"]
)
```

### 6.3 Infrastructure Deployment (R3)

```python
mandate = Mandate(
    mandate_id="m-deploy-001",
    intent="deploy to production",
    risk_tier="R3",  # Requires approval
    approval_state="pending",
    authorized_specialists=["iam-engineer"]
)

# Admin approves
mandate.approve("devops-admin@company.com")

# Now deployment can proceed
if mandate.is_approved():
    deploy()
```

---

## 7. Testing

### 7.1 Unit Tests

Located at: `tests/unit/test_enterprise_controls.py`

Run:
```bash
pytest tests/unit/test_enterprise_controls.py -v
```

### 7.2 Test Coverage

- Enterprise field defaults
- Risk tier requires_approval logic
- Approval workflow (approve/deny)
- Tool allowlist enforcement
- can_invoke_specialist with approval checks

---

## 8. Related Documents

- `000-docs/252-DR-STND-agent-identity-standard.md` - Agent ID standard
- `000-docs/254-DR-STND-policy-gates-risk-tiers.md` - Policy gate enforcement
- `000-docs/255-DR-STND-evidence-bundles-and-audit-export.md` - Audit trails
- `000-docs/251-AA-PLAN-bob-orchestrator-implementation.md` - Vision Alignment plan

---

## 9. Changelog

| Date | Version | Changes |
|------|---------|---------|
| 2026-01-02 | 1.0.0 | Initial release (Phase E) |
