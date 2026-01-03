# Human Approval Pattern

Risk-gated execution with human-in-the-loop approval.

## Pattern Overview

```
┌─────────────────────────────────────────────────────────────┐
│                   Approval Workflow                         │
│                                                             │
│   ┌─────────────┐                                          │
│   │    Risk     │                                          │
│   │  Assessor   │ ── Classifies action risk                │
│   └─────────────┘                                          │
│          │                                                  │
│          ▼                                                  │
│   ┌─────────────────────────────────────────────┐          │
│   │           Risk Level Check                   │          │
│   │                                              │          │
│   │   LOW/MEDIUM          HIGH/CRITICAL         │          │
│   │      │                     │                │          │
│   │      ▼                     ▼                │          │
│   │  Auto-approve      Request Human            │          │
│   │                    Approval                 │          │
│   │                         │                   │          │
│   │                    ┌────┴────┐              │          │
│   │                    │         │              │          │
│   │                Approved   Rejected          │          │
│   │                    │         │              │          │
│   └────────────────────┼─────────┼──────────────┘          │
│                        ▼         ▼                          │
│                    Execute     Abort                        │
└────────────────────────────────────────────────────────────┘
```

## When to Use

- Production deployments
- Destructive operations (delete, drop)
- Security-sensitive changes
- Infrastructure modifications
- Any action with significant blast radius

## Implementation

```python
from enum import Enum

class RiskLevel(Enum):
    LOW = "low"         # Auto-approve
    MEDIUM = "medium"   # Auto-approve + log
    HIGH = "high"       # Require approval
    CRITICAL = "critical"  # Require approval + escalation

def classify_risk(action: str, files: List[str]) -> RiskLevel:
    '''Classify action risk level.'''
    if any(kw in action.lower() for kw in ["delete", "destroy"]):
        return RiskLevel.CRITICAL
    if any(kw in action.lower() for kw in ["deploy", "migrate"]):
        return RiskLevel.HIGH
    if any("infra/" in f for f in files):
        return RiskLevel.HIGH
    return RiskLevel.LOW

def approval_gate_callback(ctx):
    '''Gate execution on approval.'''
    risk_level = ctx.state.get("risk_level")
    if risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
        # Block until human approves
        approval = request_approval(ctx.state)
        if not approval.approved:
            ctx.actions.abort = True
```

## Key Requirements

1. **Risk classification**: Clear rules for each risk level
2. **Approval timeout**: Don't wait forever (default 5 min)
3. **Audit trail**: Log all approval decisions
4. **Graceful handling**: Handle timeout and rejection

## Files

- `workflow.py` - Approval workflow factories
- `example.py` - Runnable example

## References

- [Google Multi-Agent Patterns](https://developers.googleblog.com/en/developers-guide-to-multi-agent-patterns-in-adk/)
- [Human-in-the-Loop](https://google.github.io/adk-docs/agents/multi-agents/)
