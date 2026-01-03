# Bob Orchestrator Primitives - Synthesis

**Document ID:** 249-AA-ANLY-bob-orchestrator-primitives-synthesis
**Date:** 2026-01-02
**Author:** Claude Code
**Status:** COMPLETE
**Beads Story:** bobs-brain-kpe.7
**Related:** 243-247 (research docs), 248 (baseline)

---

## 1. Executive Summary

This synthesis maps 5 external systems (Beads, Gastown, Anthropic Skills, Ralph Wiggum, AP2) to Bob's Brain architecture, producing a unified vocabulary and concrete design decisions for implementing Bob-as-Orchestrator.

**Key Insight:** All 5 systems address different planes of orchestration:

| System | Plane | Bob Integration |
|--------|-------|-----------------|
| **Beads** | Work Graph | Task tracking, dependency management |
| **Gastown** | Workspace Orchestration | Agent lifecycle, health monitoring |
| **Skills** | Learning/Packaging | Golden path templates, Claude Code exposure |
| **Ralph** | Execution Loops | Autonomous iteration, self-improvement |
| **AP2** | Authorization/Budget | Mandate patterns, spending limits |

---

## 2. Unified Vocabulary

### Cross-System Concept Mapping

| Concept | Beads | Gastown | Skills | Ralph | AP2 | **Bob Unified** |
|---------|-------|---------|--------|-------|-----|-----------------|
| Task unit | Issue | Molecule | Skill invocation | Prompt | Mandate | **WorkUnit** |
| Dependency | blocks/blocked_by | step.needs | N/A | N/A | N/A | **depends_on** |
| Assignment | bd pin | gt sling | Skill tool | /ralph-loop | Intent signed | **assign()** |
| Completion | bd close | step complete | Exit | Completion promise | Cart approved | **complete()** |
| Failure | status=blocked | stuck worker | N/A | Max iterations | Mandate expired | **fail()** |
| Persistence | .beads/issues.jsonl | Hook work queue | N/A | File state | Mandate store | **WorkStore** |
| Template | Proto | Formula | SKILL.md | Prompt pattern | Mandate schema | **WorkflowTemplate** |
| Grouping | Epic/Story | Convoy | Skill suite | N/A | Multi-cart | **WorkPackage** |
| Health check | bd ready | Witness | N/A | Iteration count | TTL check | **HealthCheck** |
| Approval | N/A | Mail | N/A | N/A | User signature | **ApprovalGate** |

### Bob's Unified Orchestrator Vocabulary

```python
# Core Work Unit
WorkUnit:
    id: str                   # bd-style hierarchical ID
    title: str
    description: str
    type: Literal["epic", "story", "task"]
    status: Literal["open", "in_progress", "blocked", "complete"]
    depends_on: List[str]     # Blocking dependencies
    assigned_to: str          # Agent/specialist
    completion_promise: str   # Ralph-style exit signal
    budget_limit: float       # AP2-style constraint
    expiry: datetime          # TTL from mandate
    iteration: int            # Current loop iteration
    max_iterations: int       # Safety limit

# Workflow Template
WorkflowTemplate:
    id: str
    name: str                 # Proto name (Beads) or Skill name
    steps: List[Step]         # Molecule steps with needs[]
    completion_criteria: str  # When to exit
    budget_limit: float       # Total budget for workflow

# Work Package (Portfolio grouping)
WorkPackage:
    id: str
    name: str                 # Convoy name
    work_units: List[str]     # WorkUnit IDs
    total_budget: float
    human_approval_required: bool
```

---

## 3. Component Mapping

### 3.1 Bob (Tier 1) ← Gastown Mayor + AP2 User

| Current | Enhancement | Source |
|---------|-------------|--------|
| Conversational UI | + Mandate creation | AP2 Intent Mandate |
| ADK doc search | + Skill invocation | Anthropic Skills |
| Session memory | + Work package tracking | Gastown Convoy |
| Slack gateway | + Approval flow | AP2 Cart Mandate |

**Bob becomes:**
- Primary human interface (Mayor)
- Mandate creator (AP2)
- Work package coordinator (Convoy)
- Approval collector (Cart signing)

### 3.2 Foreman (Tier 2) ← Gastown Propulsion + Ralph Loop

| Current | Enhancement | Source |
|---------|-------------|--------|
| Single delegation | + Iterative loops | Ralph Wiggum |
| Sequential chains | + Step dependencies | Gastown Molecule |
| Parallel invocation | + Budget tracking | AP2 Budget |
| Structured JSON | + Completion detection | Ralph Promise |

**Foreman becomes:**
- Molecule executor (Gastown)
- Loop controller (Ralph)
- Budget tracker (AP2)
- Work state persister (Beads)

### 3.3 Specialists (Tier 3) ← Beads + Ralph Self-Reference

| Current | Enhancement | Source |
|---------|-------------|--------|
| Strict JSON I/O | + Completion promise in output | Ralph |
| Single invocation | + Iteration awareness | Ralph |
| Tool execution | + Previous attempt reading | Ralph self-reference |
| No state | + Work unit tracking | Beads |

**Specialists become:**
- Function workers with completion signals
- Self-improving via previous attempt context
- Beads-aware (create discovered-from issues)

### 3.4 New Components Needed

| Component | Role | Source Pattern |
|-----------|------|----------------|
| **WorkStore** | Persist work state | Beads + Gastown Hook |
| **HealthMonitor** | Detect stuck agents | Gastown Witness |
| **BudgetTracker** | Track spending | AP2 |
| **ApprovalGate** | Human approval flow | AP2 Cart Mandate |
| **LoopController** | Manage iterative execution | Ralph Stop Hook |
| **TemplateEngine** | Instantiate workflows | Gastown Pour + Skills |

---

## 4. Golden Path Execution Loop

The unified execution flow combining all 5 systems:

```
┌─────────────────────────────────────────────────────────────┐
│ 1. MANDATE CREATION (AP2 + Gastown)                         │
│                                                             │
│  User → Bob: "Audit all repos, fix violations. Budget $50" │
│                                                             │
│  Bob creates:                                               │
│  - Intent Mandate (budget, scope, expiry)                   │
│  - Work Package (convoy of repos)                           │
│  - Epic in Beads (bd create ... -t epic)                    │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ 2. WORKFLOW INSTANTIATION (Gastown + Skills)                │
│                                                             │
│  Foreman:                                                   │
│  - Pours workflow template → molecule                       │
│  - Creates child stories in Beads (per repo)                │
│  - Assigns work via bd pin                                  │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ 3. ITERATIVE EXECUTION (Ralph + Beads)                      │
│                                                             │
│  Loop for each step:                                        │
│    - Check hook: "If work exists, RUN IT" (Gastown)         │
│    - Invoke specialist                                      │
│    - Check completion promise (Ralph)                       │
│    - If not complete:                                       │
│      - Read previous attempt (Ralph self-reference)         │
│      - Increment iteration                                  │
│      - Re-invoke with feedback                              │
│    - If complete:                                           │
│      - Close beads story                                    │
│      - Move to next step                                    │
│    - Track budget (AP2)                                     │
│    - Check health (Gastown Witness)                         │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ 4. APPROVAL GATES (AP2)                                     │
│                                                             │
│  If action > threshold:                                     │
│  - Create Cart Mandate (specific changes)                   │
│  - Send to Slack for approval                               │
│  - Wait for user signature                                  │
│  - Proceed or abort                                         │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ 5. COMPLETION & LEARNING (Beads + Skills)                   │
│                                                             │
│  On success:                                                │
│  - Close epic (bd close)                                    │
│  - Generate AAR (iam-doc)                                   │
│  - Package as skill (if reusable pattern)                   │
│  - Update Memory Bank                                       │
│                                                             │
│  On failure:                                                │
│  - Escalate to human (Gastown mail)                         │
│  - Record failure in beads                                  │
│  - Preserve context for retry                               │
└─────────────────────────────────────────────────────────────┘
```

---

## 5. Top 10 Design Decisions

### Decision 1: Beads as Primary Work Store

**Choice:** Use existing `.beads/` for all work tracking
**Rationale:** Already integrated, git-native, hierarchical IDs
**Implementation:** Enhance with epic/story/task patterns

### Decision 2: Hook Pattern via `after_agent_callback`

**Choice:** Implement Gastown hook in Python callback, not shell
**Rationale:** Runs in Agent Engine, maintains session context
**Implementation:** Check work queue in callback, re-invoke if needed

### Decision 3: Completion Promise in Output Schema

**Choice:** Add `completion_promise` field to all specialist outputs
**Rationale:** Enables Ralph-style loop detection
**Implementation:** Update AgentCard schemas, foreman checks field

### Decision 4: Intent Mandate for All Authorized Operations

**Choice:** Extend AP2 pattern to non-payment authorization
**Rationale:** Unified authorization model
**Implementation:** `OperationMandate` schema, tracked in session

### Decision 5: Budget Tracking in Memory Bank

**Choice:** Use Memory Bank for persistent budget state
**Rationale:** Survives session boundaries, auditable
**Implementation:** `BudgetEntry` schema, real-time updates

### Decision 6: Human Approval via Slack

**Choice:** Slack message approval = user signature
**Rationale:** Already have Slack integration
**Implementation:** `ApprovalRequest` → Slack → `ApprovalResponse`

### Decision 7: Molecules as Workflow Templates

**Choice:** TOML-based workflow definitions (Gastown formula style)
**Rationale:** Declarative, versionable, portable
**Implementation:** `.beads/formulas/` directory

### Decision 8: Witness as Foreman Responsibility

**Choice:** Foreman monitors specialist health (no separate agent)
**Rationale:** Simpler architecture, foreman already tracks state
**Implementation:** Health check in orchestration loop

### Decision 9: Skills for Claude Code Exposure

**Choice:** Generate SKILL.md from AgentCards
**Rationale:** Users invoke Bob via Claude Code skills
**Implementation:** Skill → A2A translation in gateway

### Decision 10: Memory Bank for Loop State

**Choice:** Use Memory Bank instead of file-based state
**Rationale:** Works in Agent Engine, already wired
**Implementation:** `LoopState` schema with iteration tracking

---

## 6. Implementation Phases

### Phase A: Work Persistence (Beads + Hook)

**Goal:** Work survives agent restarts

| Task | Source | Effort |
|------|--------|--------|
| Epic/story patterns in Beads | Beads | Low |
| `bd pin` for specialist assignment | Beads | Low |
| Check hook on foreman startup | Gastown | Medium |
| Persist work state to Beads | Gastown | Medium |

**Exit Criteria:** Interrupted work resumes automatically

### Phase B: Iterative Loops (Ralph)

**Goal:** Long-running tasks with self-improvement

| Task | Source | Effort |
|------|--------|--------|
| Completion promise in schemas | Ralph | Low |
| Loop detection in foreman | Ralph | Medium |
| Previous attempt context | Ralph | Medium |
| Max iteration limits | Ralph | Low |

**Exit Criteria:** Fix-until-pass workflow functional

### Phase C: Authorization (AP2)

**Goal:** Budget-aware, approval-gated operations

| Task | Source | Effort |
|------|--------|--------|
| Intent Mandate schema | AP2 | Low |
| Budget tracking | AP2 | Medium |
| Approval gate in Slack | AP2 | Medium |
| Audit trail in Memory Bank | AP2 | Medium |

**Exit Criteria:** Operations respect budget, high-impact needs approval

### Phase D: Workflow Templates (Gastown + Skills)

**Goal:** Reusable workflow patterns

| Task | Source | Effort |
|------|--------|--------|
| Formula/Proto in `.beads/formulas/` | Gastown | Medium |
| Pour workflow → molecule | Gastown | Medium |
| SKILL.md generation | Skills | Medium |
| Claude Code integration | Skills | High |

**Exit Criteria:** Common workflows are templates, exposed as skills

### Phase E: Health Monitoring (Gastown)

**Goal:** Detect and recover stuck agents

| Task | Source | Effort |
|------|--------|--------|
| Stuck detection in foreman | Gastown | Medium |
| Escalation to Slack | Gastown | Low |
| Recovery/retry logic | Gastown | Medium |
| Health metrics | Gastown | Low |

**Exit Criteria:** Stuck specialists detected and escalated

---

## 7. Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Agent Engine session limits | High | High | Checkpoint and resume pattern |
| Cost explosion from loops | Medium | High | Budget hard limits, max iterations |
| Beads sync conflicts | Low | Medium | Use daemon mode, git merge driver |
| Skill selection confusion | Medium | Low | Clear descriptions, trigger phrases |
| Human approval delays | High | Medium | Timeout with default action |

---

## 8. Ready-for-Combined-Plan Checklist

- [x] **Gastown primitives mapped** to Bob's A2A model
- [x] **Ralph loops adapted** for `after_agent_callback`
- [x] **Skills patterns identified** for AgentCard compatibility
- [x] **AP2 mandates applied** to non-payment authorization
- [x] **Beads enhancements specified** for epic/story support
- [x] **Unified vocabulary defined** across all 5 systems
- [x] **Component boundaries clear** (Bob, Foreman, Specialists, New)
- [x] **Implementation phases ordered** by dependency
- [x] **Design decisions documented** with rationale

---

## 9. Next Steps

1. **Create Combined Implementation Plan** - Phase-by-phase with stories
2. **Prototype Phase A** - Work persistence with Beads hooks
3. **Validate with User** - Confirm design decisions
4. **RFC for Team** - Share synthesis for feedback

---

## 10. References

### Research Documents
- 243-AA-DEEP-beads-research.md
- 244-AA-DEEP-gastown-research.md
- 245-AA-DEEP-anthropic-skills-research.md
- 246-AA-DEEP-ralph-wiggum-research.md
- 247-AA-DEEP-ap2-research.md

### Baseline
- 248-DR-STND-bob-brain-baseline.md

### External Sources
- https://github.com/steveyegge/beads
- https://github.com/steveyegge/gastown
- https://github.com/anthropics/skills
- https://github.com/anthropics/claude-plugins-official/tree/main/plugins/ralph-wiggum
- https://ap2-protocol.org/
