# Bob's Brain - Current State Baseline

**Document ID:** 248-DR-STND-bob-brain-baseline
**Date:** 2026-01-02
**Author:** Claude Code
**Status:** COMPLETE
**Beads Story:** bobs-brain-kpe.6
**Version:** v1.3.0

---

## 1. Executive Summary

Bob's Brain is a production-grade ADK agent department built on Google's Agent Development Kit (ADK) and Vertex AI Agent Engine. At v1.3.0, it consists of 10 agents operating in a strict three-tier architecture with A2A protocol communication.

**Current Capabilities:**
- Conversational AI assistant via Slack (Bob)
- Multi-agent workflow orchestration (Foreman)
- 8 specialist workers for SWE pipeline tasks
- Git-native task tracking (Beads)
- CI-enforced architectural rules (R1-R8)

**Missing for Full Orchestrator:**
- External workspace orchestration (Gastown patterns)
- Long-running autonomous loops (Ralph Wiggum patterns)
- Golden path packaging (Anthropic Skills)
- Budget/authorization mandates (AP2 patterns)

---

## 2. Architecture Overview

### 2.1 Three-Tier Hierarchy

```
┌─────────────────────────────────────────────────────────────┐
│ Tier 1: User Interface (Conversational)                    │
│                                                             │
│  User (via Slack)                                           │
│       ↓                                                     │
│  Bob - Conversational LLM Agent                             │
│  • Uses Gemini to respond naturally                         │
│  • Has ADK documentation search tools                       │
│  • Delegates complex work to foreman via A2A               │
└─────────────────────────────────────────────────────────────┘
                          ↓ A2A Protocol
┌─────────────────────────────────────────────────────────────┐
│ Tier 2: Orchestration Layer (Workflow Coordination)        │
│                                                             │
│  iam-senior-adk-devops-lead (Foreman)                       │
│  • Orchestrates workflow across specialists                 │
│  • NEVER executes specialist work itself                    │
│  • Delegation: single, sequential, parallel                 │
│  • Returns structured JSON to Bob                           │
└─────────────────────────────────────────────────────────────┘
                          ↓ A2A Protocol
┌─────────────────────────────────────────────────────────────┐
│ Tier 3: Execution Layer (Strict Function Workers)          │
│                                                             │
│  8 iam-* Specialists:                                       │
│  • iam-adk: ADK compliance checking                         │
│  • iam-issue: GitHub issue creation                         │
│  • iam-fix-plan: Fix planning                               │
│  • iam-fix-impl: Fix implementation                         │
│  • iam-qa: Testing and validation                           │
│  • iam-doc: Documentation                                   │
│  • iam-cleanup: Repository hygiene                          │
│  • iam-index: Knowledge indexing                            │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 Agent Inventory

| Agent | Role | Type | AgentCard |
|-------|------|------|-----------|
| **bob** | User interface | LlmAgent | ✅ |
| **iam-senior-adk-devops-lead** | Foreman/Orchestrator | LlmAgent | ✅ |
| **iam_adk** | ADK compliance | Specialist | ✅ |
| **iam_issue** | GitHub issues | Specialist | ✅ |
| **iam_fix_plan** | Fix planning | Specialist | ✅ |
| **iam_fix_impl** | Fix implementation | Specialist | ✅ |
| **iam_qa** | Testing/QA | Specialist | ✅ |
| **iam_doc** | Documentation | Specialist | ✅ |
| **iam_cleanup** | Repo hygiene | Specialist | ✅ |
| **iam_index** | Knowledge index | Specialist | ✅ |

**Total: 10 agents, all with AgentCards at `.well-known/agent-card.json`**

---

## 3. Hard Mode Rules (R1-R8)

CI-enforced architectural constraints:

| Rule | Name | Description | Status |
|------|------|-------------|--------|
| R1 | ADK-Only | No LangChain, CrewAI, custom frameworks | ✅ Enforced |
| R2 | Agent Engine | Vertex AI Agent Engine runtime | ✅ Deployed |
| R3 | Gateway Separation | Cloud Run proxies only | ✅ Enforced |
| R4 | CI-Only Deploys | GitHub Actions with WIF | ✅ Enforced |
| R5 | Dual Memory | VertexAiSessionService + VertexAiMemoryBankService | ✅ Implemented |
| R6 | Single Docs | All docs in `000-docs/` | ✅ Enforced |
| R7 | SPIFFE ID | Propagation in logs/headers | ✅ Implemented |
| R8 | Drift Detection | Runs first in CI | ✅ Enforced |

---

## 4. Key Implementation Patterns

### 4.1 Lazy Loading (6767-LAZY)

All agents use the lazy-loading pattern:

```python
def create_agent() -> LlmAgent:
    """Create agent at runtime, not import time."""
    return LlmAgent(
        name=APP_NAME,
        model="gemini-2.5-flash",
        tools=AGENT_TOOLS,
        after_agent_callback=auto_save_session_to_memory,
    )

def create_app() -> App:
    """Wrap agent in App for Agent Engine."""
    return App(create_agent())

# Module-level export
app = create_app()
```

### 4.2 Dual Memory Wiring (R5)

```python
def auto_save_session_to_memory(ctx):
    """After-agent callback to persist session to Memory Bank."""
    memory_svc = ctx._invocation_context.memory_service
    session = ctx._invocation_context.session
    memory_svc.add_session_to_memory(session)
```

### 4.3 A2A Protocol

Agents communicate via AgentCards with skill schemas:

```json
{
  "name": "iam-adk",
  "skills": [{
    "name": "adk_compliance_check",
    "input_schema": {
      "type": "object",
      "properties": {
        "target": {"type": "string"},
        "focus_rules": {"type": "array"}
      }
    },
    "output_schema": {
      "type": "object",
      "properties": {
        "compliance_status": {"type": "string"},
        "violations": {"type": "array"}
      }
    }
  }]
}
```

### 4.4 Shared Contracts

Pipeline contracts defined in `agents/shared_contracts/pipeline_contracts.py`:

```python
@dataclass
class PipelineRequest:
    repo_hint: str
    task_description: str
    pipeline_run_id: str
    env: Literal["dev", "staging", "prod"] = "dev"
    max_issues_to_fix: int = 2
```

---

## 5. Infrastructure Components

### 5.1 Directory Structure

```
bobs-brain/
├── agents/
│   ├── bob/                      # Tier 1: Conversational UI
│   ├── iam-senior-adk-devops-lead/  # Tier 2: Foreman
│   ├── iam_adk/                  # Tier 3: Specialists
│   ├── iam_issue/
│   ├── iam_fix_plan/
│   ├── iam_fix_impl/
│   ├── iam_qa/
│   ├── iam_doc/
│   ├── iam_cleanup/
│   ├── iam_index/
│   ├── a2a/                      # A2A dispatcher
│   ├── shared_contracts/         # Pipeline contracts
│   ├── shared_tools/             # Shared tool profiles
│   └── workflows/                # Workflow patterns
├── service/                      # Gateway services
│   └── slack-webhook/            # Slack gateway (Cloud Run)
├── infra/                        # Terraform infrastructure
├── tests/                        # Test suites
├── scripts/                      # CI/CD scripts
├── .beads/                       # Beads task tracking
├── 000-docs/                     # Documentation (240+ docs)
└── .github/workflows/            # GitHub Actions
```

### 5.2 Beads Integration

Git-native task tracking already integrated:

```bash
$ ls .beads/
beads.db          # SQLite primary store
issues.jsonl      # Exchange format
config.yaml       # Configuration
daemon.pid        # Background sync
```

### 5.3 CI/CD Pipeline

| Stage | Script | Purpose |
|-------|--------|---------|
| Drift Detection | `check_nodrift.sh` | R8 enforcement |
| Tests | `pytest` | Unit/integration tests |
| ARV | `check_arv_minimum.py` | Agent readiness |
| Deploy | Terraform + GHA | R4 compliant |

---

## 6. Current Capabilities

### 6.1 What Bob Can Do Today

**Conversational:**
- Natural language conversation via Slack
- ADK documentation search and retrieval
- Session memory (within conversation)
- Memory Bank persistence (across sessions)

**Orchestration:**
- Delegate tasks to foreman
- Single specialist invocation
- Sequential specialist chains
- Parallel specialist invocation (conceptual)

**SWE Pipeline:**
- ADK compliance auditing
- Issue detection and creation
- Fix planning
- Fix implementation
- QA verification
- Documentation generation
- Repository cleanup
- Knowledge indexing

### 6.2 What's Missing

| Gap | Description | Pattern Source |
|-----|-------------|----------------|
| **Work Persistence** | Work survives agent restarts | Beads hooks, Gastown |
| **Autonomous Loops** | Long-running iterative tasks | Ralph Wiggum |
| **Golden Path Packaging** | Reusable skill templates | Anthropic Skills |
| **Budget Authorization** | Pre-authorized operation limits | AP2 mandates |
| **Health Monitoring** | Detect stuck specialists | Gastown Witness |
| **Workflow Templates** | Reusable workflow formulas | Gastown Molecules |
| **Multi-Repo Coordination** | Portfolio-level orchestration | Gastown Convoys |

---

## 7. Integration Points for New Primitives

### 7.1 Beads Enhancement

**Current:** `.beads/` exists with basic CLI usage

**Enhancement Opportunities:**
- Epic/story/task hierarchy for portfolio audits
- `bd pin` for work assignment to specialists
- Chemistry metaphor (Proto/Mol/Wisp) for workflows
- `discovered-from` links for audit findings

### 7.2 Gastown Adaptation

**Mayor Role:** Bob already serves this function
**Polecat Role:** iam-* specialists as ephemeral workers
**New Needed:**
- Witness pattern for health monitoring
- Hook system for work persistence
- Molecule templates for workflows
- Convoy grouping for portfolio

### 7.3 Skills Integration

**Current:** AgentCards with skill schemas

**Enhancement Opportunities:**
- SKILL.md files exposing agents to Claude Code users
- Skill → A2A translation layer
- Golden path packaging for common workflows

### 7.4 Ralph Loop Pattern

**Current:** Single-shot specialist invocation

**Enhancement Opportunities:**
- Stop hook → `after_agent_callback` adaptation
- Completion promise in specialist output schemas
- Iterative fix loops (fix → test → fix)
- Portfolio audit loops

### 7.5 AP2 Mandate Pattern

**Current:** No authorization/budget tracking

**Enhancement Opportunities:**
- Intent Mandate for delegated tasks
- Budget tracking per operation
- Human approval gates for high-impact actions
- Audit trail in Memory Bank

---

## 8. Version History

| Version | Date | Key Changes |
|---------|------|-------------|
| v1.3.0 | 2025-12 | CI/CD automation, all agents deployed |
| v1.2.0 | 2025-12 | MCP security, testing standards |
| v1.1.0 | 2025-11 | Hard Mode rules, drift detection |
| v1.0.0 | 2025-10 | Initial release, Bob + Foreman |

---

## 9. Key Files Reference

### Architecture
- `CLAUDE.md` - Working guidance (this repo)
- `000-docs/000-DR-STND-adk-agent-engine-spec-and-hardmode-rules.md` - Hard Mode spec
- `000-docs/000-DR-STND-adk-lazy-loading-app-pattern.md` - Lazy loading pattern

### Agents
- `agents/bob/agent.py` - Conversational UI agent
- `agents/iam_senior_adk_devops_lead/agent.py` - Foreman agent
- `agents/shared_contracts/pipeline_contracts.py` - Pipeline contracts
- `agents/a2a/dispatcher.py` - A2A invocation

### Infrastructure
- `infra/terraform/` - Terraform modules
- `.github/workflows/` - CI/CD pipelines
- `scripts/ci/` - CI scripts

### Documentation
- `000-docs/` - All documentation (240+ files)
- `.beads/` - Task tracking

---

## 10. Summary

Bob's Brain at v1.3.0 is a production-ready ADK agent department with:

**Strengths:**
- ✅ Strict three-tier architecture
- ✅ 10 agents with A2A protocol
- ✅ CI-enforced Hard Mode rules
- ✅ Dual memory wiring
- ✅ Beads integration
- ✅ Comprehensive documentation

**Gaps (for full orchestrator role):**
- ❌ Work persistence (Beads hooks)
- ❌ Autonomous loops (Ralph pattern)
- ❌ Workflow templates (Gastown molecules)
- ❌ Budget authorization (AP2 mandates)
- ❌ Health monitoring (Gastown witness)
- ❌ Golden path skills (Anthropic Skills)

**Next Step:** Synthesis document mapping all 5 research items to specific Bob components.
