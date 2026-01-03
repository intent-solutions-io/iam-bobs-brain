# Bob Orchestrator Implementation Plan

**Document ID:** 251-AA-PLAN-bob-orchestrator-implementation
**Status:** PHASES A-C COMPLETE
**Created:** 2026-01-02
**Updated:** 2026-01-02
**Author:** Claude Code

---

## Executive Summary

This document outlines the phased implementation plan for enhancing Bob's Brain with orchestration primitives derived from Research Pass 1 (docs 243-250). The goal is to transform Bob from a conversational assistant into a full autonomous orchestrator capable of long-running tasks, budget-aware operations, and multi-session workflows.

**Key Insight:** We are NOT adding new agents. We are enhancing the existing 10-agent architecture with new capabilities.

---

## Architecture Overview

### Current Three-Tier Architecture (Unchanged)

```
┌─────────────────────────────────────────────────────────────┐
│ Tier 1: Bob (Conversational UI)                             │
│   - Friendly user interface via Slack                       │
│   - ADK documentation search                                │
│   - Delegates complex work to foreman                       │
└─────────────────────────────────────────────────────────────┘
                          ↓ A2A Protocol
┌─────────────────────────────────────────────────────────────┐
│ Tier 2: Foreman (iam-senior-adk-devops-lead)               │
│   - Workflow orchestration                                  │
│   - Delegation patterns (single, sequential, parallel)      │
│   - NEW: Loop patterns, budget tracking, checkpointing      │
└─────────────────────────────────────────────────────────────┘
                          ↓ A2A Protocol
┌─────────────────────────────────────────────────────────────┐
│ Tier 3: 8 iam-* Specialists (Function Workers)             │
│   - Strict input/output JSON schemas                        │
│   - Deterministic execution                                 │
│   - NEW: completion_promise in outputs                      │
└─────────────────────────────────────────────────────────────┘
```

### What's Being Added

| Component | Enhancement | Source |
|-----------|-------------|--------|
| Specialists | `completion_promise` field (COMPLETE/IN_PROGRESS/BLOCKED) | Ralph Wiggum |
| Foreman | Iterative loop pattern for re-invocation | Ralph Wiggum |
| Foreman | Budget & mandate tracking | AP2 Protocol |
| Foreman | Checkpointing & resume | Ralph Wiggum |
| Contracts | `Mandate`, `BudgetStatus` dataclasses | AP2 Protocol |
| Contracts | `TaskCheckpoint`, `ProgressStatus` dataclasses | Ralph Wiggum |
| A2A | Mandate validation before specialist calls | AP2 Protocol |

---

## Implementation Phases

### Phase A: Completion Promise & Loop Patterns
**Status:** ✅ COMPLETE (PR #43 merged)

**Objective:** Enable foreman to detect when specialists need re-invocation.

**Changes:**
1. Added `completion_promise` to all 8 specialist AgentCard output schemas
2. Added "Iterative Loop Pattern" section to foreman instruction
3. Updated iam-adk system prompt with completion awareness

**Files Modified:**
- `agents/iam_adk/.well-known/agent-card.json`
- `agents/iam_issue/.well-known/agent-card.json`
- `agents/iam_fix_plan/.well-known/agent-card.json`
- `agents/iam_fix_impl/.well-known/agent-card.json`
- `agents/iam_qa/.well-known/agent-card.json`
- `agents/iam_doc/.well-known/agent-card.json`
- `agents/iam_cleanup/.well-known/agent-card.json`
- `agents/iam_index/.well-known/agent-card.json`
- `agents/iam_adk/system-prompt.md`
- `agents/iam_senior_adk_devops_lead/agent.py`

---

### Phase B: Budget & Mandate Patterns
**Status:** ✅ COMPLETE (PR #45 merged)

**Objective:** Enable authorized, budget-limited operations.

**Changes:**
1. Added "Budget & Mandate Tracking" section to foreman instruction
2. Created `Mandate` dataclass with authorization logic
3. Created `BudgetStatus` dataclass for tracking
4. Added `mandate` field to `A2ATask`
5. Added `validate_mandate()` to A2A dispatcher

**Files Modified:**
- `agents/iam_senior_adk_devops_lead/agent.py`
- `agents/shared_contracts/pipeline_contracts.py`
- `agents/a2a/types.py`
- `agents/a2a/dispatcher.py`

**Mandate Structure:**
```json
{
  "mandate_id": "m-abc123",
  "intent": "Audit all iam-* agents for ADK compliance",
  "budget_limit": 10.0,
  "budget_unit": "USD",
  "max_iterations": 50,
  "authorized_specialists": ["iam-adk", "iam-qa"],
  "expires_at": "2024-01-15T23:59:59Z"
}
```

---

### Phase C: Checkpointing & Resume
**Status:** ✅ COMPLETE (PR #46 merged)

**Objective:** Enable long-running tasks to pause and resume.

**Changes:**
1. Added "Checkpointing & Resume" section to foreman instruction
2. Created `TaskCheckpoint` dataclass with state tracking
3. Created `ProgressStatus` dataclass for progress reporting
4. Added `CheckpointReason` enum
5. Added checkpoint/progress fields to `PipelineRequest` and `PipelineResult`

**Files Modified:**
- `agents/iam_senior_adk_devops_lead/agent.py`
- `agents/shared_contracts/pipeline_contracts.py`

**Checkpoint Structure:**
```json
{
  "checkpoint_id": "chk_abc123",
  "pipeline_run_id": "original_run_id",
  "state": {
    "current_step": 3,
    "total_steps": 8,
    "completed_specialists": ["iam-adk", "iam-issue"],
    "pending_specialists": ["iam-fix-plan", "iam-fix-impl"],
    "partial_results": {...}
  },
  "resumable": true,
  "reason": "budget_limit"
}
```

---

### Phase D: Gastown Workspace Patterns (PLANNED)
**Status:** 📋 PLANNED

**Objective:** Enable multi-workspace orchestration for portfolio-wide operations.

**Key Concepts from Gastown:**
- **Mayor**: Town-wide coordinator → Maps to Bob
- **Witness**: Per-project monitor → New component for each repo
- **Polecat**: Ephemeral workers → Maps to iam-* specialists
- **Molecules**: Workflow units → Maps to pipeline stages

**Proposed Changes:**
1. Add `WorkspaceContext` to track per-repo state
2. Add witness pattern for monitoring repo health
3. Extend portfolio contracts for multi-repo coordination
4. Add "propulsion principle" - if hook has work, run it

**Files to Modify:**
- `agents/shared_contracts/pipeline_contracts.py` (WorkspaceContext)
- `agents/iam_senior_adk_devops_lead/agent.py` (witness coordination)
- New: `agents/shared_contracts/workspace_contracts.py`

---

### Phase E: Skills Packaging (PLANNED)
**Status:** 📋 PLANNED

**Objective:** Package foreman patterns as reusable skills for other repos.

**Key Concepts from Anthropic Skills:**
- **SKILL.md format**: YAML frontmatter + markdown instructions
- **Activation triggers**: Pattern-based skill activation
- **Learning loops**: Capture successful patterns as new skills

**Proposed Changes:**
1. Create SKILL.md templates for foreman patterns
2. Package delegation patterns as installable skills
3. Add skill discovery to Bob's capabilities
4. Enable dynamic skill loading

**Files to Create:**
- `skills/delegation-patterns/SKILL.md`
- `skills/adk-compliance/SKILL.md`
- `skills/portfolio-audit/SKILL.md`

---

### Phase F: Integration Testing (PLANNED)
**Status:** 📋 PLANNED

**Objective:** Validate all new patterns work together end-to-end.

**Test Scenarios:**
1. Long-running audit with budget limit → checkpoint → resume
2. Multi-repo portfolio sweep with progress tracking
3. Mandate validation blocking unauthorized specialists
4. Loop pattern with multiple IN_PROGRESS iterations

---

## Beads Epic Tracking

| Epic ID | Phase | Description | Status |
|---------|-------|-------------|--------|
| iyv | A | completion_promise + loop patterns | ✅ Closed |
| 8jd | B | Budget & Mandate tracking | ✅ Closed |
| 4b4 | C | Checkpointing & Resume | ✅ Closed |
| TBD | D | Gastown Workspace patterns | 📋 Not started |
| TBD | E | Skills Packaging | 📋 Not started |
| TBD | F | Integration Testing | 📋 Not started |

---

## Pull Request Status

| PR | Phase | Title | Status |
|----|-------|-------|--------|
| #43 | A | completion_promise and loop pattern | ✅ Merged |
| #44 | - | Git workflow documentation | ✅ Merged |
| #45 | B | Budget & Mandate Patterns | ✅ Merged |
| #46 | C | Long-Running Task Patterns | ✅ Merged |

---

## Research Documents Referenced

| Doc | Title | Key Patterns Extracted |
|-----|-------|----------------------|
| 243 | Beads Research | Epic/story hierarchy, git-native tracking |
| 244 | Gastown Research | Mayor/Witness/Polecat, workspace management |
| 245 | Anthropic Skills Research | SKILL.md format, learning loops |
| 246 | Ralph Wiggum Research | Loop patterns, checkpointing, completion_promise |
| 247 | AP2 Research | Mandate structure, budget limits, authorization |
| 248 | Bob Brain Baseline | Current architecture snapshot |
| 249 | Primitives Synthesis | Unified vocabulary, design decisions |
| 250 | Research Pass 1 AAR | Lessons learned, ready-for-implementation |

---

## Success Criteria

### Phase A-C (COMPLETE)
- [x] All PRs merged to main
- [x] No regressions in existing tests
- [x] Foreman instruction includes loop patterns
- [x] Mandates properly validated in dispatcher
- [x] Checkpoint/progress dataclasses defined

### Phase D-F (Future)
- [ ] Multi-repo operations work with workspace context
- [ ] Skills can be packaged and installed
- [ ] End-to-end integration tests pass

---

## Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|------------|
| Breaking existing AgentCard contracts | High | Added fields are optional, backward compatible |
| Mandate validation too strict | Medium | Default to no restrictions when mandate absent |
| Checkpoint state grows too large | Medium | Limit partial_results size, compress |
| Phase B/C merge conflicts | Low | Independent changes, minimal overlap |

---

## Next Steps

1. **COMPLETE:** PRs #43, #44, #45, #46 all merged to main
2. **Next:** Create Phase D epic for Gastown Workspace patterns
3. **Medium-term:** Implement witness monitoring for repos
4. **Long-term:** Package as reusable skills for other departments

---

## Related Documents

- `243-AA-DEEP-beads-research.md` - Beads patterns
- `244-AA-DEEP-gastown-research.md` - Gastown architecture
- `245-AA-DEEP-anthropic-skills-research.md` - Skills format
- `246-AA-DEEP-ralph-wiggum-research.md` - Loop patterns
- `247-AA-DEEP-ap2-research.md` - Budget/mandate patterns
- `248-DR-STND-bob-brain-baseline.md` - Current state
- `249-AA-ANLY-bob-orchestrator-primitives-synthesis.md` - Unified design
- `250-AA-REPT-research-pass-1-aar.md` - Research summary
