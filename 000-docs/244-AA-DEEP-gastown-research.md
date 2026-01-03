# Gastown Research - Deep Dive Analysis

**Document ID:** 244-AA-DEEP-gastown-research
**Date:** 2026-01-02
**Author:** Claude Code
**Status:** COMPLETE
**Beads Story:** bobs-brain-kpe.2

---

## 1. What It Is (Executive Summary)

**Gas Town** is a multi-agent orchestration system for Claude Code that enables 20-30+ AI agents to work together on software projects. It provides persistent work tracking, agent communication via mail, and structured workflows through a "molecule" system. The key innovation is the **hook system**: each agent has a persistent work queue that survives crashes and restarts, enabling resilient async orchestration.

Core philosophy: "If your hook has work, RUN IT." Work packages (molecules) contain step dependencies that automatically resume from failure points.

---

## 2. Key Primitives to Implement/Integrate

### 2.1 Role Hierarchy

| Role | Scope | Responsibility | Bob Mapping |
|------|-------|----------------|-------------|
| **Overseer** | Human | Strategy, review, escalations | User (via Slack) |
| **Mayor** | Town-wide | Cross-project coordination, primary human interface | Bob (Tier 1) |
| **Deacon** | Town-wide | Daemon process, agent lifecycle, plugin execution | Background service |
| **Witness** | Per-rig | Monitor workers, detect stuck, handle lifecycle | Health check component |
| **Refinery** | Per-rig | Merge queue, code review, integration testing | CI/CD gates |
| **Polecat** | Per-task | Ephemeral worker, execute tasks, file discoveries | iam-* specialists (Tier 3) |
| **Crew** | Per-rig | Persistent human-managed workspace | Dev environment |

### 2.2 Directory Structure

```
Town (~/gt/)
├── mayor/                    # Town-wide coordinator
├── <rig-name>/               # Per-project workspace
│   ├── .beads/               # Issue tracking
│   ├── crew/
│   │   └── <name>/           # Persistent crew workspaces
│   ├── polecats/
│   │   └── <id>/             # Ephemeral worker clones
│   ├── refinery/             # Merge queue
│   └── witness/              # Lifecycle monitor
└── deacon/                   # Town daemon
```

### 2.3 Work Persistence: Hooks

**Each agent has a persistent hook** (work queue):
- Survives crashes and restarts
- Read on startup: "If your hook has work, RUN IT"
- No polling for tasks - work is already assigned

```bash
# Assign work to an agent
bd pin <id> --for <agent> --start

# Check what's on an agent's hook
bd hook --agent <agent>
```

### 2.4 Molecule System (Workflow Templates)

| Phase | Name | Storage | Purpose |
|-------|------|---------|---------|
| **Ice-9** | Formula | `.beads/formulas/` | Composable template with macros |
| **Solid** | Protomolecule | `.beads/` | Frozen, reusable template |
| **Liquid** | Molecule | `.beads/` | Active, persistent workflow |
| **Vapor** | Wisp | `.beads/` (marked) | Ephemeral, transient task |

**Lifecycle:**
1. **Cook**: Formula → Protomolecule (expand macros, flatten)
2. **Pour**: Protomolecule → Molecule (instantiate as persistent)
3. **Execute**: Worker processes steps, closing beads
4. **Recovery**: New worker resumes from last completed step

### 2.5 Formula Structure (TOML)

```toml
[[steps]]
id = "run-tests"
needs = ["update-deps"]
command = "pytest tests/"

[[steps]]
id = "build-binaries"
needs = ["run-tests"]
command = "go build ./..."
```

### 2.6 Convoy System

**Convoys** group related work for tracking and assignment:

```bash
gt convoy create "Auth Feature" issue-123 issue-456
gt sling issue-123 myproject    # Assign to polecat
gt convoy list                  # Dashboard view
```

Decouples work definition from agent assignment.

### 2.7 Communication: Mail

```bash
gt mail inbox                    # Check messages
gt mail send mayor/ -s "Subject" -m "Message"
gt mail send beads/dave -s "Handoff" -m "Context"
```

Mail enables:
- Human → Agent communication
- Agent → Agent handoffs
- Escalations to overseer

### 2.8 Lifecycle Management

**Witness responsibilities:**
- Detect stuck workers (no progress)
- Trigger recovery for crashed agents
- Escalate to Mayor for complex issues
- Garbage collect completed polecats

**Deacon responsibilities:**
- Manage agent processes
- Execute plugins
- Handle town-wide events

---

## 3. Minimum Interface Contract

### CLI Commands for Integration

```bash
# Town management
gt start                    # Launch daemon + Mayor
gt status                   # Town overview
gt doctor                   # Health diagnostics

# Work assignment
gt convoy create "Name" <beads...>
gt sling <bead> <rig>       # Assign to worker
bd pin <id> --for <agent>   # Direct hook assignment

# Agent operations
gt prime                    # Enter Mayor context
gt mail inbox               # Check messages
gt <role> attach            # Jump into session

# Lifecycle
gt spawn polecat <rig>      # Create worker
gt kill <agent>             # Terminate agent
```

### Agent Startup Protocol

```bash
# 1. Check hook
gt mol status               # What's on my hook?

# 2. Hook has work? RUN IT
# 3. Hook empty? Check mail
gt mail inbox

# 4. Mail has attached work? Self-pin it
gt mol attach-from-mail <mail-id>

# 5. Still nothing? Wait for assignment
```

### Session End Protocol

```bash
# 1. Check for uncommitted changes
git status

# 2. Push commits
git push

# 3. Sync beads
bd sync

# 4. Check inbox for pending messages
gt mail inbox

# 5. Hand off context (if needed)
gt handoff -s "Brief" -m "Details"
```

---

## 4. Risks / Failure Modes / Anti-Patterns

### 4.1 Stuck Workers

Workers can get stuck without external intervention.

**Mitigation:** Witness monitors health, triggers recovery.

### 4.2 Work Loss on Crash

Without hooks, work is lost when agent crashes.

**Mitigation:** Hook system persists work state in beads.

### 4.3 Coordination Overhead

Too many agents → communication overhead.

**Mitigation:**
- Mayor handles cross-project coordination
- Witness handles per-rig lifecycle
- Keep polecats focused on single tasks

### 4.4 Orphan Polecats

Ephemeral workers may not clean up properly.

**Mitigation:** Witness garbage collects completed polecats.

### 4.5 Mail Queue Overflow

High-traffic systems may overwhelm mail.

**Mitigation:** Priority-based mail routing, escalation paths.

---

## 5. What to Copy vs Adapt

### Option A: Extract Patterns (User-Selected)

Adapt Gastown concepts to work within Bob's existing A2A architecture:

| Gastown Concept | Bob Adaptation |
|-----------------|----------------|
| **Mayor** | Bob (Tier 1) already serves this role |
| **Polecat** | iam-* specialists as ephemeral workers |
| **Witness** | New health check component for specialists |
| **Hook** | Map to A2A task queue per specialist |
| **Molecule** | Workflow templates for foreman |
| **Mail** | Map to A2A messaging or Slack DMs |
| **Convoy** | Portfolio audit grouping |

**Advantages:**
- Works within existing A2A infrastructure
- No external Gastown dependency
- Simpler deployment

### Option B: Direct Integration (User-Selected for Exploration)

Make Bob a full Gastown Mayor with native dependencies:

| Component | Integration |
|-----------|-------------|
| **Town** | Create `~/gt/bobs-brain/` rig |
| **Mayor** | Bob runs as Mayor in Slack context |
| **Polecats** | iam-* specialists as worker polecats |
| **Witness** | Deploy witness for iam-* health |
| **Refinery** | Integrate with CI/CD gates |
| **Beads** | Already integrated |

**Advantages:**
- Full Gastown feature set
- Battle-tested orchestration
- Multi-repo coordination native

**Challenges:**
- External dependency (Go binary)
- Complexity in Vertex Agent Engine environment
- May conflict with A2A patterns

---

## 6. Integration Notes for Bob

### 6.1 Pattern Mapping

```
Gastown                    Bob's Brain
───────                    ───────────
Mayor                   →  Bob (conversational UI)
Witness                 →  Health check agent (new)
Polecat                 →  iam-* specialists
Hook                    →  A2A task assignment
Molecule                →  Foreman workflow
Convoy                  →  Portfolio audit scope
Mail                    →  A2A messages + Slack
```

### 6.2 Recommended Implementation

**Phase 1: Hook Pattern**
- Add hook-like work persistence to iam-* specialists
- Work survives agent restart via beads

**Phase 2: Witness Pattern**
- Create iam-health agent or add to foreman
- Monitor specialist health, detect stuck workers
- Trigger recovery or escalation

**Phase 3: Molecule/Workflow Templates**
- Create formulas for common workflows (audit, fix, QA)
- Foreman instantiates molecules for each request

**Phase 4: Convoy for Portfolio**
- Group portfolio repos into convoys
- Track progress across repos

### 6.3 R1-R8 Compliance

| Rule | Gastown Impact |
|------|----------------|
| R1 (ADK-only) | Gastown is external tooling - pattern extraction OK |
| R2 (Agent Engine) | Must adapt patterns to run in Agent Engine |
| R3 (Gateway separation) | Gastown doesn't conflict |
| R4 (CI-only deploys) | Gastown workflow templates OK |
| R8 (Drift detection) | Add checks for stuck workers |

### 6.4 Propulsion Principle for Bob

**"If your hook has work, RUN IT"**

Apply to Bob:
- On startup, check for pending A2A tasks
- Execute immediately, don't wait for new requests
- Persist work state in beads for recovery

---

## 7. Open Questions

1. **Should Bob become a full Gastown Mayor?**
   - Requires `gt` binary in Agent Engine environment
   - May conflict with A2A protocol

2. **How to implement Witness in Agent Engine?**
   - Separate agent or foreman responsibility?
   - Health check endpoints for specialists

3. **Molecule templates for IAM department?**
   - Define formulas for: audit, fix-plan, fix-impl, QA, doc
   - Where to store: `.beads/formulas/` in repo?

4. **Mail system integration?**
   - Use A2A for agent-to-agent?
   - Use Slack for agent-to-human?
   - Or implement gt mail in Agent Engine?

5. **Multi-repo coordination?**
   - Gastown native: Multiple rigs in town
   - Bob pattern: Portfolio orchestrator using convoys

---

## 8. References

- **Source Repository**: https://github.com/steveyegge/gastown
- **Beads Integration**: Already in Bob's Brain
- **gastown-viewer-intent**: `/home/jeremy/000-projects/gastown-viewer-intent/`

---

## 9. Key Takeaways for Bob Orchestrator

1. **Hook pattern is essential** - Work persistence survives crashes
2. **Witness pattern for health** - Monitor specialists, detect stuck
3. **Molecule pattern for workflows** - Reusable, recoverable templates
4. **Convoy pattern for grouping** - Track related work across agents
5. **Propulsion principle** - "If your hook has work, RUN IT"
6. **Two integration paths** - Extract patterns OR full integration

**User Decision:** Parallel exploration - document both approaches in synthesis.

**Next Step:** Research Anthropic Skills for golden path packaging.
