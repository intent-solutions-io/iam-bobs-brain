# 237-AT-ARCH-apiregistry-cloud-tool-governance.md

**Document Type:** Architecture Design
**Status:** Implemented (Phase 1 + Phase 2)
**Created:** 2025-12-20
**Updated:** 2025-12-20
**Author:** Claude Code (Build Captain)

---

## Executive Summary

This document describes the integration of Google Cloud API Registry with Bob's Brain for **centralized tool governance**. The architecture separates MCP servers from agent code - agents discover tools at runtime via the registry, not at build time.

**Key Principle:** MCP server lives in same repo but deploys to different target (Cloud Run).

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    SAME REPO, DIFFERENT DEPLOY TARGETS                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  bobs-brain/                                                                │
│  ├── agents/        → Deploys to Agent Engine                              │
│  │   ├── bob/                                                              │
│  │   ├── iam_senior.../                                                    │
│  │   └── iam_*/                                                            │
│  │                                                                          │
│  ├── service/       → Deploys to Cloud Run (Slack gateway)                 │
│  │                                                                          │
│  └── mcp/           → Deploys to Cloud Run (bobs-mcp server)               │
│      ├── src/                                                               │
│      │   ├── server.py                                                      │
│      │   ├── auth/                                                          │
│      │   └── tools/                                                         │
│      └── Dockerfile                                                         │
│                                                                             │
│  Agents use: ApiRegistry.get_toolset() for runtime discovery               │
│                                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│                      CLOUD API REGISTRY (Console)                           │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Registered MCP Servers:                                              │   │
│  │                                                                      │   │
│  │  ┌──────────────────┐  ┌──────────────────┐                         │   │
│  │  │ google-bigquery  │  │ bobs-mcp         │                         │   │
│  │  │ (Google managed) │  │ (your Cloud Run) │                         │   │
│  │  └──────────────────┘  └──────────────────┘                         │   │
│  │                                                                      │   │
│  │  IAM Controls: Which agents can access which MCP servers            │   │
│  │  Audit Logs: All tool discovery and invocation events               │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Why This Separation Matters

### Traceability

| Concern | Without Registry | With Registry |
|---------|-----------------|---------------|
| "What tools can iam-adk access?" | Grep the code | Query the registry |
| "Who called create_issue at 3am?" | Parse Cloud Run logs | Registry audit log |
| "What changed in tool access?" | Git diff | Registry change history |
| "Is this agent authorized?" | Check code + IAM | Single IAM check |

**Two-layer audit trail:**
1. **Registry layer** - Tool discovery events (who requested what tools)
2. **MCP layer** - Tool execution events (what was actually called)

### Governance

| Concern | Without Registry | With Registry |
|---------|-----------------|---------------|
| Add new tool | Code change + deploy | Register + approve |
| Revoke tool access | Code change + deploy | Disable in registry (instant) |
| Emergency lockdown | Redeploy all agents | Toggle in console |
| Compliance audit | Reconstruct from git | Export from registry |

**Separation of duties:**
- **Security team** → Manages API Registry (approve/deny tools)
- **Infrastructure team** → Deploys MCP servers to Cloud Run
- **Agent team** → Uses `ApiRegistry.get_toolset()` (just consumes)

### Independent Lifecycles

```
MCP Server Update                    Agent Update
─────────────────                    ────────────
1. Fix bug in mcp-github             1. Update Bob's prompt
2. Push to mcp-github repo           2. Push to bobs-brain repo
3. Cloud Run redeploys               3. Agent Engine redeploys
4. Agents automatically get fix      4. No MCP server impact
   (no agent redeploy needed)
```

---

## What is Cloud API Registry?

Google's Cloud API Registry for Vertex AI Agent Builder provides:

- **Centralized tool governance** - Single registry for all agent tools
- **Dynamic MCP discovery** - Agents fetch approved tools at runtime
- **Admin-curated toolsets** - IT/admin controls which tools agents can access
- **Audit trail** - Track which agents use which tools
- **IAM integration** - Fine-grained access control

### The Runtime Flow

```
┌─────────┐     ┌──────────────┐     ┌─────────────┐     ┌──────────────┐
│  Agent  │────▶│ API Registry │────▶│   IAM Check │────▶│  MCP Server  │
│ (Bob)   │     │              │     │             │     │ (Cloud Run)  │
└─────────┘     └──────────────┘     └─────────────┘     └──────────────┘
     │                 │                    │                    │
     │  get_toolset()  │                    │                    │
     │────────────────▶│                    │                    │
     │                 │ Check permissions  │                    │
     │                 │───────────────────▶│                    │
     │                 │      ✅ Allowed    │                    │
     │                 │◀───────────────────│                    │
     │   Tool handles  │                    │                    │
     │◀────────────────│                    │                    │
     │                 │                    │                    │
     │  invoke tool    │                    │                    │
     │─────────────────┼────────────────────┼───────────────────▶│
     │                 │                    │                    │
     │  result         │                    │                    │
     │◀────────────────┼────────────────────┼────────────────────│
     │                 │                    │                    │
     ▼                 ▼                    ▼                    ▼
  Audit Log        Audit Log           Audit Log            Audit Log
```

---

## Agent-Side Implementation

The agent code is minimal - it only discovers tools, never defines them:

```python
# agents/shared_tools/api_registry.py

from typing import Optional, Any, List
import logging
import os

logger = logging.getLogger(__name__)

_registry_instance: Optional[Any] = None


def get_api_registry():
    """
    Get or initialize the Cloud API Registry client.

    Lazy singleton pattern (6767-LAZY compliant).
    """
    global _registry_instance

    if _registry_instance is not None:
        return _registry_instance

    project_id = os.getenv("PROJECT_ID")
    if not project_id:
        logger.warning("PROJECT_ID not set - ApiRegistry disabled")
        return None

    try:
        from google.adk.tools import ApiRegistry

        _registry_instance = ApiRegistry(
            project_id=project_id,
            header_provider=_get_header_provider()
        )
        logger.info(f"Initialized ApiRegistry for project: {project_id}")
        return _registry_instance

    except ImportError:
        logger.warning("ApiRegistry not available in this ADK version")
        return None
    except Exception as e:
        logger.error(f"Failed to initialize ApiRegistry: {e}")
        return None


def _get_header_provider():
    """Get header provider for auth context propagation (R7 compliance)."""
    try:
        from google.auth import default
        from google.auth.transport.requests import Request

        credentials, _ = default()

        def header_provider() -> dict:
            credentials.refresh(Request())
            return {"Authorization": f"Bearer {credentials.token}"}

        return header_provider
    except Exception:
        return None


def get_tools_for_agent(agent_name: str) -> List[Any]:
    """
    Fetch all approved tools for a specific agent from the registry.

    The registry knows which MCP servers this agent can access based on IAM.
    Agent code does NOT hardcode tool lists.

    Args:
        agent_name: The agent requesting tools (e.g., "iam-adk", "bob")

    Returns:
        List of tool handles from approved MCP servers
    """
    registry = get_api_registry()
    if registry is None:
        logger.warning(f"Registry unavailable for {agent_name} - no tools loaded")
        return []

    try:
        # Registry returns tools this agent is authorized to use
        # Based on IAM bindings, not hardcoded in agent code
        tools = registry.get_agent_tools(agent_name)
        logger.info(f"Loaded {len(tools)} tools for {agent_name} from registry")
        return tools
    except Exception as e:
        logger.error(f"Failed to get tools for {agent_name}: {e}")
        return []
```

### Agent Tool Profile (New Pattern)

```python
# agents/shared_tools/__init__.py

from .api_registry import get_tools_for_agent


def get_bob_tools() -> List[Any]:
    """
    Bob's tools - fetched from registry at runtime.

    NO HARDCODED TOOL DEFINITIONS.
    Registry + IAM determines what Bob can access.
    """
    return get_tools_for_agent("bob")


def get_iam_adk_tools() -> List[Any]:
    """iam-adk tools - fetched from registry."""
    return get_tools_for_agent("iam-adk")


def get_iam_issue_tools() -> List[Any]:
    """iam-issue tools - fetched from registry."""
    return get_tools_for_agent("iam-issue")

# ... etc for all agents
```

---

## MCP Server Infrastructure (Same Repo)

The MCP server lives in the same repo as agents, deployed to a different target:

### bobs-mcp Structure

```
bobs-brain/
├── agents/           # → Deploys to Agent Engine
├── service/          # → Deploys to Cloud Run (Slack gateway)
└── mcp/              # → Deploys to Cloud Run (bobs-mcp)
    ├── Dockerfile
    ├── requirements.txt
    ├── src/
    │   ├── server.py           # FastAPI MCP server
    │   ├── auth/
    │   │   └── validator.py    # R7 caller validation
    │   └── tools/
    │       ├── search_codebase.py
    │       ├── get_file.py
    │       ├── analyze_deps.py
    │       └── check_patterns.py
    └── tests/
        └── unit/
            └── test_tools.py
```

### MCP Server Terraform (in bobs-brain)

```hcl
# infra/terraform/cloud_run.tf

resource "google_cloud_run_service" "bobs_mcp" {
  count    = var.bobs_mcp_enabled ? 1 : 0
  name     = "${var.app_name}-mcp-${var.environment}"
  location = var.region
  project  = var.project_id

  template {
    spec {
      service_account_name = google_service_account.bobs_mcp[0].email
      containers {
        image = var.bobs_mcp_image
      }
    }
  }
}

# IAM: Only Agent Engine can invoke MCP server
resource "google_cloud_run_service_iam_member" "bobs_mcp_agents" {
  count   = var.bobs_mcp_enabled ? 1 : 0
  service = google_cloud_run_service.bobs_mcp[0].name
  role    = "roles/run.invoker"
  member  = "serviceAccount:${google_service_account.agent_engine.email}"
}
```

---

## MCP Servers

| Server | Purpose | Tools | Status |
|--------|---------|-------|--------|
| `bobs-mcp` | Repository operations | search_codebase, get_file, analyze_deps, check_patterns | ✅ Implemented |
| `bobs-mcp` (future) | GitHub integration | create_issue, create_pr, list_workflows | Planned |
| Google BigQuery | Data operations | execute_sql, list_datasets, get_schema | Use Google's |

**Note:** All tools will be added to the single `bobs-mcp` server rather than creating multiple MCP servers. This simplifies deployment and management.

---

## Hard Mode Compliance

| Rule | Status | Notes |
|------|--------|-------|
| R1: ADK-Only | ✅ | Uses `google.adk.tools.ApiRegistry` |
| R3: Gateway Separation | ✅ | MCP servers on Cloud Run, not in Agent Engine |
| R4: CI-Only Deployments | ✅ | MCP servers deploy via Terraform, agents deploy via CI |
| R5: Dual Memory | ✅ | No impact on memory wiring |
| R7: SPIFFE ID | ✅ | Header provider propagates auth context |
| R8: Drift Detection | ✅ | Registry is source of truth, not code |

**R4 Note:** Registry approval happens in Console, but MCP server deployment is Terraform. Future: registry-as-code.

---

## Implementation Phases

### Phase 1: Agent-Side Foundation ✅ COMPLETE
- [x] Create `agents/shared_tools/api_registry.py`
- [x] Add `get_api_registry()` singleton
- [x] Add `get_tools_for_agent()` function
- [x] Update tool profiles to use registry (hybrid: static + MCP)
- [x] Unit tests (mock registry) - `tests/unit/test_api_registry.py`
- [x] Fallback to empty tools if registry unavailable

### Phase 2: First MCP Server (bobs-mcp) ✅ COMPLETE
- [x] Create MCP server in `bobs-brain/mcp/` (same repo, different deploy target)
- [x] Implement MCP server with 4 tools:
  - `search_codebase` - Grep-based code search
  - `get_file` - File content retrieval with security
  - `analyze_deps` - Dependency analysis
  - `check_patterns` - Hard Mode rule validation
- [x] Terraform for Cloud Run deployment (`infra/terraform/cloud_run.tf`)
- [x] Service account + IAM (`infra/terraform/iam.tf`)
- [x] GitHub Actions workflow (`.github/workflows/deploy-mcp.yml`)
- [x] Unit tests for MCP tools (`mcp/tests/unit/`)
- [ ] Register in API Registry (manual - console)

### Phase 3: GitHub MCP Server
- [ ] Add GitHub tools to `mcp/src/tools/`
- [ ] Implement create_issue, create_pr tools
- [ ] Update registry IAM for iam-issue, iam-fix-impl

### Phase 4: Migration Complete
- [ ] Remove static tool definitions from agents/ (optional - hybrid works)
- [ ] All tools come from registry
- [ ] Add registry health check to ARV gates
- [ ] Document governance procedures

---

## Testing Strategy

### Unit Tests (in bobs-brain)

```python
# tests/unit/test_api_registry.py

def test_registry_unavailable_returns_empty():
    """Without registry, agents should get empty tools (not crash)."""
    with patch.dict(os.environ, {}, clear=True):
        tools = get_tools_for_agent("bob")
        assert tools == []

def test_registry_error_returns_empty():
    """On registry error, should degrade gracefully."""
    with patch("google.adk.tools.ApiRegistry", side_effect=Exception("boom")):
        tools = get_tools_for_agent("iam-adk")
        assert tools == []
```

### Integration Tests (per MCP server repo)

```python
# mcp-repo-ops/tests/test_server.py

def test_search_codebase_returns_results():
    """MCP server should return search results."""
    response = client.call_tool("search_codebase", {"query": "def agent"})
    assert response.results is not None
```

---

## References

- [Cloud API Registry](https://cloud.google.com/vertex-ai/docs/agent-builder/api-registry) (when public)
- [ADK Tools Documentation](https://google.github.io/adk-docs/tools/)
- [MCP Protocol Specification](https://spec.modelcontextprotocol.io/)
- Bob's Brain Hard Mode Rules: `000-docs/6767-DR-STND-adk-agent-engine-spec-and-hardmode-rules.md`

---

## Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2025-12-20 | ~~MCP servers in separate repos~~ | ~~Clean separation, independent lifecycles, different teams~~ |
| 2025-12-20 | **REVISED: MCP server in same repo** | Simpler management, shared CI/CD, single source of truth |
| 2025-12-20 | Registry-first tool discovery | Governance, traceability, audit compliance |
| 2025-12-20 | Hybrid tool loading | Static tools always available, MCP tools when registry configured |
| 2025-12-20 | Graceful degradation | Agents work (with static tools) if registry down |
| 2025-12-20 | Named "bobs-mcp" | Consistent with repo naming, clear ownership |
| 2025-12-20 | Feature flag pattern | `bobs_mcp_enabled` allows gradual rollout |
