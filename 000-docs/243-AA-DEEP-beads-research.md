# Beads Research - Deep Dive Analysis

**Document ID:** 243-AA-DEEP-beads-research
**Date:** 2026-01-02
**Author:** Claude Code
**Status:** COMPLETE
**Beads Story:** bobs-brain-kpe.1

---

## 1. What It Is (Executive Summary)

**Beads** (`bd`) is a distributed, git-backed graph issue tracker designed specifically for AI agents. It replaces ad-hoc markdown plans with a **dependency-aware graph structure** that maintains context across long-running tasks. Issues are stored as JSONL files in a `.beads/` directory, making them versionable, branchable, and mergeable like regular code.

Key differentiator: "Persistent, structured memory for coding agents" - designed from the ground up for AI-supervised workflows, not human-first tooling adapted for AI.

---

## 2. Key Primitives to Implement/Integrate

### 2.1 Storage Model

| Component | Format | Location | Purpose |
|-----------|--------|----------|---------|
| **Primary Store** | SQLite | `.beads/beads.db` | Fast local queries, daemon-managed |
| **Exchange Format** | JSONL | `.beads/issues.jsonl` | Git-compatible, cross-clone sync |
| **Deletions Manifest** | JSONL | `.beads/deletions.jsonl` | Propagate deletes across clones |
| **Config** | TOML | `.beads/config.toml` | Per-repo settings |

### 2.2 Identifier System

**Hash-Based IDs** (prevents merge conflicts):
- Base: `bd-a1b2` (6-char hash from repo prefix)
- Hierarchical: `bd-a3f8.1` (epic.task), `bd-a3f8.1.1` (epic.task.subtask)
- Up to 3 levels of nesting supported
- Parent hash ensures unique namespace per agent

### 2.3 Issue Types

| Type | Use Case |
|------|----------|
| `bug` | Something broken that needs fixing |
| `feature` | New functionality |
| `task` | Work item (tests, docs, refactoring) |
| `epic` | Large feature with hierarchical children |
| `chore` | Maintenance (dependencies, tooling) |

### 2.4 Priority Levels

| Priority | Meaning |
|----------|---------|
| `0` | Critical (security, data loss, broken builds) |
| `1` | High (major features, important bugs) |
| `2` | Medium (default, nice-to-have) |
| `3` | Low (polish, optimization) |
| `4` | Backlog (future ideas) |

### 2.5 Dependency Types

**Blocking Dependencies:**
- `blocks` - Hard dependency (X blocks Y, only this affects ready queue)

**Structural Relationships:**
- `parent-child` - Epic/subtask relationship (automatic via hierarchical IDs)
- `discovered-from` - Track issues found during work (inherits `source_repo`)
- `related` - Soft relationship

**Graph Links:**
- `relates_to` - Bidirectional "see also"
- `duplicates` - Mark as duplicate
- `supersedes` - Version chains
- `replies_to` - Message threads (Gastown integration)

### 2.6 Chemistry Metaphor (Templates & Workflows)

| Phase | Storage | Synced | Use Case |
|-------|---------|--------|----------|
| **Proto** (solid) | Built-in | N/A | Reusable templates |
| **Mol** (liquid) | `.beads/` | Yes | Persistent work |
| **Wisp** (vapor) | `.beads-wisp/` | No | Ephemeral operations |

**Key Commands:**
- `bd pour <proto>` - Proto → persistent mol
- `bd wisp create <proto>` - Proto → ephemeral wisp
- `bd pin <id> --for <agent>` - Assign work to agent's hook

### 2.7 Daemon & Auto-Sync

- **Background daemon** per workspace for auto-sync
- **5-second debounce** for JSONL export
- **Event-driven mode** (v0.16+): <500ms latency, 60% less CPU
- Enable: `BEADS_DAEMON_MODE=events`

### 2.8 Memory Decay

Semantic summarization of closed tasks to conserve token context. Compressed issues preserve key context without full verbosity.

---

## 3. Minimum Interface Contract

### CLI Commands Bob Must Support

```bash
# Core CRUD
bd create "Title" --description="..." -t type -p priority --json
bd update <id> --status in_progress --json
bd close <id> --reason "Done" --json
bd show <id> --json
bd list --status open --priority 1 --json

# Dependency Management
bd dep add <child> <parent>
bd dep tree <id>
bd blocked  # Show blocked issues
bd ready    # Show unblocked issues

# Sync
bd sync     # Force export/commit/push

# Chemistry (for Gastown integration)
bd pour <proto> --var key=value
bd pin <id> --for <agent> --start
bd hook --agent <agent>
```

### JSON Output Schema (for A2A)

```json
{
  "id": "bd-a1b2",
  "title": "Issue title",
  "description": "Detailed context",
  "type": "task",
  "priority": 1,
  "status": "open",
  "created": "2026-01-02T20:00:00Z",
  "updated": "2026-01-02T20:00:00Z",
  "dependencies": {
    "blocks": [],
    "blocked_by": [],
    "discovered_from": "bd-parent",
    "children": ["bd-a1b2.1", "bd-a1b2.2"]
  },
  "labels": [],
  "source_repo": "bobs-brain"
}
```

---

## 4. Risks / Failure Modes / Anti-Patterns

### 4.1 Dependency Direction Confusion

**COGNITIVE TRAP**: Temporal language inverts dependencies!

```bash
# WRONG - temporal thinking
"Phase 1 comes before Phase 2" → bd dep add phase1 phase2

# RIGHT - requirement thinking
"Phase 2 NEEDS Phase 1" → bd dep add phase2 phase1
```

**Mitigation**: Always use requirement language ("X needs Y"), verify with `bd blocked`.

### 4.2 Missing Descriptions

Issues without descriptions lack context for future work. Always include:
- **Why** the issue exists
- **What** needs to be done
- **How** you discovered it

### 4.3 Daemon Mode Conflicts

Some commands require `--no-daemon` flag when daemon is running (e.g., `bd pour`).

### 4.4 Merge Conflicts

Hierarchical IDs prevent conflicts, but JSONL can have conflicts during concurrent edits. The git merge driver handles this, but ensure `bd hooks install` has been run.

### 4.5 Orphan Handling

When parent issues are deleted, children become orphans. Configure handling:
- `allow` (default) - Import orphans anyway
- `resurrect` - Recreate deleted parents as tombstones
- `skip` - Skip orphaned children
- `strict` - Fail import

---

## 5. What to Copy vs Adapt

### Copy Verbatim (Bob Already Has `.beads/`)

- **CLI integration**: Bob can invoke `bd` commands directly
- **JSONL storage**: Already in place, just use it
- **Hierarchical IDs**: Work naturally with existing setup
- **Sync mechanism**: `bd sync` already functional

### Adapt for Bob's A2A Architecture

| Beads Concept | Bob Adaptation |
|---------------|----------------|
| `bd pin --for <agent>` | Map to A2A task assignment |
| Chemistry metaphor | Use for workflow templates in foreman |
| `discovered-from` | Link audit findings to parent issues |
| Memory decay | Integrate with Memory Bank summarization |

### New Patterns to Implement

1. **Epic → Story → Task Hierarchy**
   - Use for portfolio audits: `audit-portfolio.1` (repo1), `.2` (repo2)
   - Map to foreman → specialist delegation

2. **Proto Templates for Workflows**
   - Create protos for common workflows (audit, fix, QA)
   - Pour into mols when work is assigned

3. **Hook System for Work Assignment**
   - Map `bd hook` to A2A skill invocation
   - Persist work state across agent restarts

---

## 6. Integration Notes for Bob

### 6.1 Existing Integration

Bob's Brain already has:
- `.beads/` directory with `beads.db` and `issues.jsonl`
- `bd` CLI available
- Git sync configured

### 6.2 Recommended Enhancements

**Foreman Integration:**
```python
# When foreman receives a task, create beads issue
bd create "Audit repo X" --description="..." -t task -p 1 --json

# Assign to specialist
bd update <id> --status in_progress --json

# On completion
bd close <id> --reason "Audit complete, 3 violations found" --json
```

**Specialist Integration:**
```python
# Specialists create discovered-from issues
bd create "Found R1 violation" \
  --description="Using LangChain in agents/bob/agent.py" \
  --deps discovered-from:<parent-audit> -t bug -p 1 --json
```

**Portfolio Audit Pattern:**
```bash
# Epic for portfolio
bd create "Portfolio Audit 2026-01-02" -t epic -p 1

# Child per repo (auto-numbered)
bd create "Audit repo-1" --parent <epic-id>
bd create "Audit repo-2" --parent <epic-id>
```

### 6.3 R1-R8 Compliance

| Rule | Beads Impact |
|------|--------------|
| R1 (ADK-only) | Beads is external tooling, OK to use via CLI |
| R4 (CI-only deploys) | Beads changes should sync via git, not manual |
| R6 (single docs folder) | Beads issues are data, not docs - OK |
| R8 (drift detection) | Add check for orphan beads issues |

---

## 7. Open Questions

1. **Should Bob invoke `bd` directly or through a wrapper tool?**
   - Direct CLI is simpler but less controlled
   - Wrapper could add A2A-specific metadata

2. **How to handle beads across multiple repos in portfolio audit?**
   - Each repo has own `.beads/` - need coordination strategy
   - Consider central coordination via Gastown mayor pattern

3. **Memory decay integration with Vertex Memory Bank?**
   - Both handle context compression
   - Potential overlap or synergy

4. **Proto templates for IAM department workflows?**
   - Create protos for: audit, fix-plan, fix-impl, QA, doc
   - How to version and distribute?

5. **MCP server integration?**
   - Beads has `beads-mcp` for non-CLI environments
   - Could expose beads operations as MCP tools for Bob

---

## 8. References

- **Source Repository**: https://github.com/steveyegge/beads
- **Local Clone**: `/home/jeremy/000-projects/beads/`
- **CLAUDE.md**: Comprehensive agent instructions
- **CLI Reference**: `docs/CLI_REFERENCE.md`
- **MCP Integration**: `integrations/beads-mcp/`

---

## 9. Key Takeaways for Bob Orchestrator

1. **Beads is already in Bob's Brain** - Just need to leverage it better
2. **Hierarchical IDs map to foreman → specialist** - Natural fit
3. **Chemistry metaphor enables workflow templates** - Proto → Mol for reusable patterns
4. **Hook system enables work persistence** - Survives agent restarts
5. **Memory decay complements Memory Bank** - Both handle context compression
6. **Dependency graph enables proper sequencing** - Use for SWE pipeline ordering

**Next Step**: Research Gastown to understand how beads integrates with multi-agent orchestration.
