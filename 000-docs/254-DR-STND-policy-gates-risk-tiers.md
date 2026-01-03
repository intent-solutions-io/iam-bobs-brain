# Policy Gates and Risk Tiers Standard

**Document ID:** 254-DR-STND-policy-gates-risk-tiers
**Status:** ACTIVE
**Created:** 2026-01-02
**Author:** Claude Code
**Phase:** E (Enterprise Controls)

---

## 1. Purpose

This document defines the **policy gate system** for Bob's Brain. Policy gates are preflight checks that run before specialist invocation to ensure operations meet their risk tier requirements.

Key principles:
- **Default-deny for high-risk**: R3/R4 operations blocked without explicit approval
- **Fail-fast**: Gate checks run before any work begins
- **Transparent**: All gate decisions are logged and auditable

---

## 2. Risk Tier Definitions

| Tier | Name | Description | Requirements |
|------|------|-------------|--------------|
| **R0** | Read-Only | No side effects | None (default) |
| **R1** | Local | Local changes, reversible | Mandate optional |
| **R2** | External | External writes (GitHub, APIs) | Mandate required |
| **R3** | Infrastructure | Infrastructure changes | Mandate + human approval |
| **R4** | Financial | Payment/financial operations | Mandate + 2-person approval |

### 2.1 Risk Tier Descriptions

```python
from agents.shared_contracts import RISK_TIER_DESCRIPTIONS

# {
#     RiskTier.R0: "Read-only operations with no side effects",
#     RiskTier.R1: "Local changes that are reversible",
#     RiskTier.R2: "External writes (GitHub issues, PRs, comments)",
#     RiskTier.R3: "Infrastructure changes (requires human approval)",
#     RiskTier.R4: "Payment/financial operations (requires 2-person approval)",
# }
```

---

## 3. Gate Types

### 3.1 Mandate Required Gate

Checks if a mandate is required for the operation's risk tier.

| Risk Tier | Mandate Required |
|-----------|------------------|
| R0, R1 | No |
| R2, R3, R4 | Yes |

```python
from agents.shared_contracts import PolicyGate, Mandate

# R0/R1: No mandate needed
result = PolicyGate.check_mandate_required("R0", None)
assert result.allowed is True

# R2+: Mandate required
result = PolicyGate.check_mandate_required("R2", None)
assert result.allowed is False
assert result.blocking_requirement == "mandate"
```

### 3.2 Approval Required Gate

Checks if human approval is required and granted.

| Risk Tier | Approval Required |
|-----------|-------------------|
| R0, R1, R2 | No |
| R3 | Single human approval |
| R4 | Two-person approval |

```python
mandate = Mandate(
    mandate_id="m-001",
    intent="deploy",
    risk_tier="R3",
    approval_state="pending"
)

result = PolicyGate.check_approval_required("R3", mandate)
assert result.allowed is False
assert result.blocking_requirement == "approval"

# After approval
mandate.approve("admin@company.com")
result = PolicyGate.check_approval_required("R3", mandate)
assert result.allowed is True
```

### 3.3 Tool Allowed Gate

Checks if a tool is permitted by the mandate's allowlist.

```python
mandate = Mandate(
    mandate_id="m-001",
    intent="read files",
    tool_allowlist=["search_code", "read_file"]
)

result = PolicyGate.check_tool_allowed("read_file", mandate)
assert result.allowed is True

result = PolicyGate.check_tool_allowed("delete_file", mandate)
assert result.allowed is False
```

### 3.4 Specialist Authorized Gate

Checks if a specialist can be invoked under the mandate.

```python
mandate = Mandate(
    mandate_id="m-001",
    intent="compliance check",
    authorized_specialists=["iam-compliance"]
)

result = PolicyGate.check_specialist_authorized("iam-compliance", mandate)
assert result.allowed is True

result = PolicyGate.check_specialist_authorized("iam-engineer", mandate)
assert result.allowed is False
```

---

## 4. GateResult Structure

Every gate check returns a `GateResult`:

```python
@dataclass
class GateResult:
    allowed: bool           # Whether the gate passed
    reason: str             # Human-readable explanation
    risk_tier: str          # Risk tier being checked
    gate_name: str          # Name of the gate
    blocking_requirement: Optional[str] = None  # What's blocking
```

### 4.1 Boolean Context

GateResult can be used in boolean context:

```python
result = PolicyGate.check_mandate_required("R0", None)
if result:  # True if allowed
    proceed()
```

---

## 5. Preflight Check

The `preflight_check` function runs all gates at once:

```python
from agents.shared_contracts import preflight_check, PolicyGate

results = preflight_check(
    specialist_name="iam-compliance",
    risk_tier="R2",
    mandate=mandate,
    tools_to_use=["search_code", "analyze"]
)

if PolicyGate.is_all_gates_passed(results):
    # Safe to proceed
    invoke_specialist()
else:
    # Some gates blocked
    blocking = PolicyGate.get_blocking_gates(results)
    for gate in blocking:
        print(f"Blocked by {gate.gate_name}: {gate.reason}")
```

---

## 6. Integration with Dispatcher

The A2A dispatcher runs policy gates before specialist invocation:

```python
# agents/a2a/dispatcher.py

def validate_mandate(task: A2ATask) -> None:
    """Validate mandate with policy gate checks."""
    # Parse mandate from task
    mandate = parse_mandate(task.mandate)
    risk_tier = mandate.risk_tier if mandate else "R0"

    # Run preflight checks
    gate_results = PolicyGate.preflight_check(
        specialist_name=task.specialist,
        risk_tier=risk_tier,
        mandate=mandate
    )

    # Check for blocking gates
    blocking = PolicyGate.get_blocking_gates(gate_results)
    if blocking:
        blocks = [f"{g.gate_name}: {g.reason}" for g in blocking]
        raise A2AError(
            f"Policy gate check failed: {'; '.join(blocks)}",
            specialist=task.specialist
        )
```

---

## 7. Decision Matrix

| Operation | Risk Tier | Mandate | Approval | Allowed? |
|-----------|-----------|---------|----------|----------|
| Read files | R0 | No | No | Yes |
| Edit local files | R1 | Optional | No | Yes |
| Create GitHub issue | R2 | Required | No | If mandate |
| Deploy to prod | R3 | Required | Required | If approved |
| Process payment | R4 | Required | 2-person | If 2 approvals |

---

## 8. Error Messages

When gates block, they provide clear messages:

```
# Missing mandate for R2
"R2+ operations require a mandate. Risk tier: R2"

# Pending approval for R3
"Operation pending human approval"

# Denied operation
"Operation was denied by approver"

# Tool not allowed
"Tool 'delete_file' not in allowlist: ['search_code', 'read_file']"

# Specialist not authorized
"Specialist 'iam-engineer' not in authorized list"
```

---

## 9. Logging

All gate checks are logged for audit:

```python
logger.debug(
    f"Policy gates passed for {task.specialist} (risk_tier={risk_tier})",
    extra={"specialist": task.specialist, "risk_tier": risk_tier}
)
```

---

## 10. Testing

### 10.1 Unit Tests

Located at: `tests/unit/test_enterprise_controls.py`

Run:
```bash
pytest tests/unit/test_enterprise_controls.py::TestPolicyGate* -v
```

### 10.2 Test Coverage

- RiskTier enum completeness
- GateResult boolean behavior
- Mandate required checks (R0-R4)
- Approval required checks
- Tool allowlist enforcement
- Preflight integration

---

## 11. Related Documents

- `000-docs/252-DR-STND-agent-identity-standard.md` - Agent ID standard
- `000-docs/253-DR-STND-mandates-budgets-approvals.md` - Mandate enterprise fields
- `000-docs/255-DR-STND-evidence-bundles-and-audit-export.md` - Audit trails
- `000-docs/251-AA-PLAN-bob-orchestrator-implementation.md` - Vision Alignment plan

---

## 12. Changelog

| Date | Version | Changes |
|------|---------|---------|
| 2026-01-02 | 1.0.0 | Initial release (Phase E) |
