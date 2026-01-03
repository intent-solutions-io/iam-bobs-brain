# 257-DR-STND-mission-spec-v1.md

**Mission Spec v1 Standard**

Status: ACTIVE
Version: 1.0
Created: 2026-01-03
Phase: Phase F (Vision Alignment)

---

## 1. Overview

Mission Spec v1 is a **declarative workflow-as-code format** for defining multi-agent workflows in the bobs-brain orchestration system. It enables:

- **Declarative Workflows**: Define what should happen, not how
- **Deterministic Compilation**: Same input always produces same execution plan
- **Dry-Run Previews**: Validate and preview workflows before execution
- **Enterprise Controls**: Integrated mandates, budgets, and risk tiers
- **Evidence Bundles**: Audit trails for every run

---

## 2. Mission Spec Schema

### 2.1 Top-Level Structure

```yaml
mission_id: "unique-mission-identifier"
title: "Human-readable title"
intent: "What this mission accomplishes"
version: "1"

scope:
  repos:
    - path: "."  # Repository scope

workflow:
  - step: "step-name"
    agent: "agent-id"
    inputs: {}
    outputs: []

mandate:
  budget_limit: 5.0
  risk_tier: "R1"

evidence:
  bundle_required: true
```

### 2.2 Required Fields

| Field | Type | Description |
|-------|------|-------------|
| `mission_id` | string | Unique identifier (kebab-case) |
| `title` | string | Human-readable title |
| `intent` | string | What the mission accomplishes |

### 2.3 Optional Fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `version` | string | "1" | Mission spec version |
| `scope` | MissionScope | empty | Repository scope |
| `workflow` | list | empty | Workflow steps |
| `mandate` | MissionMandate | defaults | Authorization config |
| `evidence` | EvidenceConfig | defaults | Evidence bundle config |

---

## 3. Workflow Elements

### 3.1 Workflow Step

Basic agent invocation:

```yaml
workflow:
  - step: "analyze"
    agent: "iam-compliance"
    inputs:
      targets: ["agents/*/agent.py"]
      focus_rules: ["R1", "R2"]
    outputs:
      - name: "compliance_report"
        description: "ADK compliance analysis"
    depends_on: []
    condition: null
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `step` | string | Yes | Step identifier |
| `agent` | string | Yes | Agent canonical ID |
| `inputs` | dict | No | Input parameters |
| `outputs` | list | No | Output definitions |
| `depends_on` | list | No | Step dependencies |
| `condition` | string | No | Execution condition |

### 3.2 Loop Step

Iterative workflows with gates:

```yaml
workflow:
  - loop:
      name: "fix-loop"
      until: "all issues resolved"
      max_iterations: 10
      gates:
        - type: "test_pass"
          command: "pytest tests/"
      steps:
        - step: "plan"
          agent: "iam-planner"
        - step: "implement"
          agent: "iam-engineer"
          depends_on: ["plan"]
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | Yes | Loop identifier |
| `until` | string | No | Semantic termination condition |
| `max_iterations` | int | No | Hard limit (default: 10) |
| `gates` | list | No | Gate checks per iteration |
| `steps` | list | Yes | Steps within the loop |

### 3.3 Gate Types

| Type | Description | Required Fields |
|------|-------------|-----------------|
| `test_pass` | Run command, pass if exit 0 | `command` |
| `approval` | Require human approval | `approvers` |
| `custom` | Custom condition expression | `condition` |

---

## 4. Scope Configuration

### 4.1 Repository Scope

```yaml
scope:
  repos:
    - path: "."              # Current repository
    - path: "../other-repo"  # Relative path
      ref: "main"            # Git ref
      worktree: "/tmp/wt"    # Worktree path
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `path` | string | Yes | Repository path |
| `ref` | string | No | Git ref (branch, tag, commit) |
| `worktree` | string | No | Git worktree path |

---

## 5. Mandate Configuration

### 5.1 Authorization Settings

```yaml
mandate:
  budget_limit: 5.0
  budget_unit: "USD"
  max_iterations: 50
  authorized_specialists:
    - "iam-compliance"
    - "iam-triage"
  risk_tier: "R2"
  data_classification: "internal"
```

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `budget_limit` | float | 0.0 | Maximum budget |
| `budget_unit` | string | "USD" | Budget currency/unit |
| `max_iterations` | int | 100 | Max specialist calls |
| `authorized_specialists` | list | [] | Allowed agents (empty=all) |
| `risk_tier` | string | "R0" | Risk tier (R0-R4) |
| `data_classification` | string | "internal" | Data sensitivity |

### 5.2 Risk Tiers

| Tier | Description | Gate Requirements |
|------|-------------|-------------------|
| R0 | Read-only, no side effects | None (default) |
| R1 | Local changes, reversible | Mandate optional |
| R2 | External writes (GitHub, etc.) | Mandate + budget |
| R3 | Infrastructure changes | Mandate + approval |
| R4 | Payment/financial | Mandate + 2-person approval |

---

## 6. Evidence Configuration

```yaml
evidence:
  bundle_required: true
  include:
    - "compliance_report"
    - "test_results"
  export_to_gcs: true
  gcs_bucket: "evidence-bucket"
```

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `bundle_required` | bool | true | Create evidence bundle |
| `include` | list | [] | Outputs to include |
| `export_to_gcs` | bool | false | Export to GCS |
| `gcs_bucket` | string | null | GCS bucket name |

---

## 7. CLI Commands

### 7.1 Validate

Check mission file for errors:

```bash
python -m agents.mission_spec.runner validate missions/my-mission.yaml
```

### 7.2 Compile

Generate execution plan:

```bash
python -m agents.mission_spec.runner compile missions/my-mission.yaml -o plan.json
```

### 7.3 Dry-Run

Preview execution without running:

```bash
python -m agents.mission_spec.runner dry-run missions/my-mission.yaml
```

### 7.4 Run

Execute the mission:

```bash
python -m agents.mission_spec.runner run missions/my-mission.yaml
```

---

## 8. Compilation Process

### 8.1 Compiler Steps

1. **Validate** - Check mission schema and constraints
2. **Expand Workflow** - Flatten loops into tasks
3. **Topological Sort** - Order tasks by dependencies
4. **Generate IDs** - Create deterministic task IDs
5. **Create Plan** - Build ExecutionPlan with mandate
6. **Create Request** - Generate PipelineRequest

### 8.2 Determinism Guarantees

The compiler produces deterministic output:

- Same mission → same content hash
- Same seed → same task IDs
- Sorted outputs for reproducibility

```python
# Same seed produces same plan
result1 = compile_mission(mission, seed="fixed-seed")
result2 = compile_mission(mission, seed="fixed-seed")
assert result1.plan.content_hash == result2.plan.content_hash
```

---

## 9. Output Artifacts

### 9.1 ExecutionPlan

```json
{
  "plan_id": "plan-abc12345",
  "mission_id": "audit-adk-compliance",
  "mission_title": "Audit ADK Compliance",
  "created_at": "2026-01-03T00:00:00Z",
  "content_hash": "sha256:...",
  "tasks": [
    {
      "task_id": "task-12345678",
      "step_name": "analyze",
      "agent": "iam-compliance",
      "inputs": {},
      "depends_on": []
    }
  ],
  "execution_order": ["task-12345678"],
  "mandate": {
    "budget_limit": 5.0,
    "risk_tier": "R2"
  }
}
```

### 9.2 PipelineRequest

The compiler also generates a PipelineRequest ready for dispatcher execution:

```python
PipelineRequest(
    repo_hint=".",
    task_description="Ensure all agents follow Hard Mode rules",
    pipeline_run_id="mission-audit-adk-compliance",
    mandate=Mandate(...)
)
```

---

## 10. Variable Interpolation

Reference outputs from previous steps:

```yaml
workflow:
  - step: "analyze"
    agent: "iam-compliance"
    outputs:
      - name: "report"

  - step: "triage"
    agent: "iam-triage"
    depends_on: ["analyze"]
    inputs:
      report: "${analyze.report}"
```

Syntax: `${step_name.output_name}`

---

## 11. Sample Missions

### 11.1 Single-Repo Audit

See: `missions/sample-single-repo.mission.yaml`

Basic compliance audit of the current repository.

### 11.2 Fix Loop

See: `missions/sample-fix-loop.mission.yaml`

Iterative fix loop with test gates.

---

## 12. Integration with Beads

Mission Spec compiles to Beads-compatible task graphs:

1. Each workflow step becomes a Beads task
2. Dependencies map to Beads task relationships
3. Loops expand to iteration-indexed tasks
4. Gates map to Beads checkpoints

---

## 13. Related Documentation

- **6767-DR-STND-adk-agent-engine-spec-and-hardmode-rules.md** - Hard Mode rules
- **253-DR-STND-mandates-budgets-approvals.md** - Mandate system
- **254-DR-STND-policy-gates-risk-tiers.md** - Policy gates
- **255-DR-STND-evidence-bundles-and-audit-export.md** - Evidence bundles

---

## 14. Changelog

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-01-03 | Initial release (Phase F) |
