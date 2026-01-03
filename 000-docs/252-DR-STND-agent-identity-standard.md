# Agent Identity Standard

**Document ID:** 252-DR-STND-agent-identity-standard
**Status:** ACTIVE
**Created:** 2026-01-02
**Author:** Claude Code
**Phase:** D (Vision Alignment GA)

---

## 1. Purpose

This document defines the **canonical agent identity system** for Bob's Brain. It establishes:

- Canonical agent IDs for all agents
- Backwards-compatible alias mapping for one release
- SPIFFE ID generation patterns
- Directory naming conventions

---

## 2. Canonical Agent IDs

### 2.1 Naming Convention

| Tier | Pattern | Examples |
|------|---------|----------|
| Tier 1 (UI) | `bob` | `bob` |
| Tier 2 (Orchestrator) | `iam-orchestrator` | `iam-orchestrator` |
| Tier 3 (Specialists) | `iam-{function}` | `iam-compliance`, `iam-qa` |

**Rules:**
- Kebab-case only (no underscores)
- Tier 3 specialists use descriptive function names
- Short and memorable

### 2.2 Complete Agent Registry

| Canonical ID | Tier | Description | Old IDs (Deprecated) |
|--------------|------|-------------|---------------------|
| `bob` | 1 | Conversational UI | `bob_agent`, `bob-agent` |
| `iam-orchestrator` | 2 | Foreman/scheduler | `iam_senior_adk_devops_lead`, `iam-senior-adk-devops-lead`, `foreman` |
| `iam-compliance` | 3 | ADK/Vertex compliance | `iam_adk`, `iam-adk` |
| `iam-triage` | 3 | Issue decomposition | `iam_issue`, `iam-issue` |
| `iam-planner` | 3 | Fix planning | `iam_fix_plan`, `iam-fix-plan` |
| `iam-engineer` | 3 | Implementation | `iam_fix_impl`, `iam-fix-impl` |
| `iam-qa` | 3 | Testing/verification | `iam_qa` |
| `iam-docs` | 3 | Documentation | `iam_doc`, `iam-doc` |
| `iam-hygiene` | 3 | Cleanup/tech debt | `iam_cleanup`, `iam-cleanup` |
| `iam-index` | 3 | Knowledge indexing | `iam_index` |

---

## 3. Backwards Compatibility

### 3.1 Alias Resolution

Old IDs continue to work for **one release** via the alias system:

```python
from agents.shared_contracts import canonicalize

# Old ID → Canonical ID (with deprecation warning)
canonical_id = canonicalize("iam_adk")  # Returns "iam-compliance"

# Canonical ID → Itself (no warning)
canonical_id = canonicalize("iam-compliance")  # Returns "iam-compliance"
```

### 3.2 Deprecation Warnings

When using old IDs:
```
DeprecationWarning: Agent ID 'iam_adk' is deprecated.
Use canonical ID 'iam-compliance' instead.
Aliases will be removed in the next major version.
```

### 3.3 Migration Timeline

| Phase | Action |
|-------|--------|
| v2.0.0 | Old IDs work with warnings |
| v2.1.0 | Old IDs logged as errors |
| v3.0.0 | Old IDs removed |

---

## 4. Directory Mapping

During the transition, canonical IDs map to existing directories:

| Canonical ID | Directory |
|--------------|-----------|
| `bob` | `agents/bob/` |
| `iam-orchestrator` | `agents/iam_senior_adk_devops_lead/` |
| `iam-compliance` | `agents/iam_adk/` |
| `iam-triage` | `agents/iam_issue/` |
| `iam-planner` | `agents/iam_fix_plan/` |
| `iam-engineer` | `agents/iam_fix_impl/` |
| `iam-qa` | `agents/iam_qa/` |
| `iam-docs` | `agents/iam_doc/` |
| `iam-hygiene` | `agents/iam_cleanup/` |
| `iam-index` | `agents/iam_index/` |

**Future:** Directories will be renamed to match canonical IDs in a later phase.

---

## 5. SPIFFE ID Format

### 5.1 Template

```
spiffe://intent.solutions/agent/{canonical_id}/{env}/{region}/{version}
```

### 5.2 Examples

```
spiffe://intent.solutions/agent/bob/dev/us-central1/0.1.0
spiffe://intent.solutions/agent/iam-orchestrator/prod/us-central1/2.0.0
spiffe://intent.solutions/agent/iam-compliance/dev/us-central1/0.1.0
```

### 5.3 Generation

```python
from agents.shared_contracts import get_spiffe_id

spiffe = get_spiffe_id("iam-compliance", env="prod", region="us-central1", version="2.0.0")
# Returns: spiffe://intent.solutions/agent/iam-compliance/prod/us-central1/2.0.0
```

---

## 6. API Reference

### 6.1 Core Functions

```python
from agents.shared_contracts import (
    canonicalize,    # Resolve any ID to canonical
    is_canonical,    # Check if ID is canonical
    is_valid,        # Check if ID is valid (canonical or alias)
    get_definition,  # Get AgentDefinition for ID
    get_directory,   # Get directory name for ID
    get_spiffe_id,   # Generate SPIFFE ID
)
```

### 6.2 List Functions

```python
from agents.shared_contracts import (
    list_canonical_ids,  # All canonical IDs
    list_by_tier,        # IDs for specific tier
    list_specialists,    # All Tier 3 specialists
)

from agents.shared_contracts import AgentTier

specialists = list_specialists()
# ['iam-compliance', 'iam-triage', 'iam-planner', ...]

tier_1_agents = list_by_tier(AgentTier.TIER_1_UI)
# ['bob']
```

### 6.3 Data Exports

```python
from agents.shared_contracts import (
    CANONICAL_AGENTS,        # Dict[str, AgentDefinition]
    AGENT_ALIASES,           # Dict[str, str] (old -> canonical)
    CANONICAL_TO_DIRECTORY,  # Dict[str, str]
    DIRECTORY_TO_CANONICAL,  # Dict[str, str]
)
```

---

## 7. Integration Points

### 7.1 A2A Dispatcher

The dispatcher automatically resolves IDs:

```python
# Both work:
task = A2ATask(specialist="iam_adk", ...)      # Old ID (with warning)
task = A2ATask(specialist="iam-compliance", ...)  # Canonical (preferred)
```

### 7.2 Mandate Authorization

Mandates should use canonical IDs:

```json
{
  "mandate_id": "m-abc123",
  "authorized_specialists": [
    "iam-compliance",
    "iam-triage",
    "iam-planner"
  ]
}
```

### 7.3 AgentCards

AgentCards should use canonical IDs in the `name` field:

```json
{
  "name": "iam-compliance",
  "version": "2.0.0",
  "spiffe_id": "spiffe://intent.solutions/agent/iam-compliance/dev/us-central1/2.0.0"
}
```

---

## 8. Testing

### 8.1 Unit Tests

Located at: `tests/unit/test_agent_identity.py`

Run:
```bash
pytest tests/unit/test_agent_identity.py -v
```

### 8.2 Test Coverage

- Canonical ID registry completeness
- Alias mapping correctness
- Deprecation warning behavior
- SPIFFE ID generation
- Directory mapping

---

## 9. Related Documents

- `000-docs/251-AA-PLAN-bob-orchestrator-implementation.md` - Vision Alignment plan
- `000-docs/6767-DR-STND-agentcards-and-a2a-contracts.md` - AgentCard standard
- `000-docs/6767-DR-STND-adk-agent-engine-spec-and-hardmode-rules.md` - Hard Mode rules

---

## 10. Changelog

| Date | Version | Changes |
|------|---------|---------|
| 2026-01-02 | 1.0.0 | Initial release (Phase D) |
