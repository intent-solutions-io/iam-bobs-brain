# 000-DR-STND – ADK Tools & Cloud Run Integration Pattern

**Version:** 0.1 (Draft)
**Scope:** bobs-brain / department adk iam / future intent-agent-model-* repos
**Purpose:** Define how "tools live in Cloud Run" while staying 100% compliant with google-adk 1.18+, Agent Engine, and 6767-LAZY.
**Status:** Draft - Ready for iteration
**Last Updated:** 2025-11-22

---

## 1. Mental Model

There are always **two layers:**

### 1. Tool object (ADK land)
- Lives in Python, inside `LlmAgent.tools`
- Type: `callable`, `BaseTool`, `FunctionTool`, `VertexAiSearchTool`, or `MCPToolset`
- Responsible for:
  - Validation of input/output schema
  - Making a call to a remote service (Cloud Run, Vertex AI Search, etc.)

### 2. Tool backend (Cloud Run / Vertex / MCP land)
- Actually does the work
- Examples:
  - Cloud Run service handling repo operations, indexing, fix planning
  - Vertex AI Search / Discovery Engine for org knowledge
  - MCP server speaking HTTP/JSON over a stable contract

**Translation:** "Tools live in Cloud Run" = the business logic lives in Cloud Run, ADK tools are typed clients.

---

## 2. Directory & Ownership

### ADK-side (clients):

```
agents/shared_tools/
├── vertex_search.py      # VertexAiSearchTool configs
├── cloud_run_tools.py    # HTTP clients talking to Cloud Run
└── mcp_tools.py          # MCPToolset wrappers if/when used
```

Agent-specific wiring:
- `agents/bob/agent.py`
- `agents/iam_adk/agent.py`
- etc.

### Cloud Run–side (services):

Separate repo OR clearly separated directory in same mono-repo:

```
services/
├── tools-repo-ops/
├── tools-issue-index/
└── tools-knowledge-sync/
```

Each service exposes a stable HTTP API with:
- `/healthz`
- Versioned routes like `/v1/summarize`, `/v1/index-repo`, `/v1/run-fix-plan`

---

## 3. ADK Tool Patterns

### 3.1 Vertex AI Search / Discovery Engine

**Where:** `agents/shared_tools/vertex_search.py`

**Pattern:**

```python
from google.adk.tools import VertexAiSearchTool
from typing import Optional

def get_org_knowledge_tool(env: Optional[str] = None) -> Optional[VertexAiSearchTool]:
    """
    Vertex AI Search / Discovery Engine tool for org knowledge.

    - Used for RAG-style lookups over docs, repos, runbooks.
    - Backed by a configured data store in Vertex.
    """
    # load env config / datastore id however you've standardized it
    datastore_id = "org-knowledge-datastore"  # from config/env

    return VertexAiSearchTool(
        data_store_id=datastore_id,
        # Optional: filter=..., max_results=...
    )
```

**Agent wiring (lazy, inside create_agent):**

```python
from google.adk.agents import LlmAgent

def create_agent() -> LlmAgent:
    from agents.shared_tools import ORG_KNOWLEDGE_TOOLS  # lazy import

    return LlmAgent(
        model="gemini-2.0-flash-exp",
        name="iam_adk",
        tools=ORG_KNOWLEDGE_TOOLS,
        instruction=instruction,
        after_agent_callback=auto_save_session_to_memory,
    )
```

**Rule:**
Vertex/Discovery tools are always declared via ADK-provided classes (`VertexAiSearchTool`, `DiscoveryEngineSearchTool`). No dicts.

---

### 3.2 Cloud Run–backed HTTP tools

**Where:** `agents/shared_tools/cloud_run_tools.py`

**Tool type:** `FunctionTool` wrapping a small, testable HTTP client function.

**Pattern:**

```python
import os
import requests
from google.adk.tools import FunctionTool

CLOUD_RUN_BASE_URL = os.getenv("TOOLS_REPO_OPS_BASE_URL")  # e.g. https://repo-ops-xxx.a.run.app

def _repo_summary_impl(repo_url: str) -> str:
    """
    Call Cloud Run service to summarize a repo.
    """
    resp = requests.post(
        f"{CLOUD_RUN_BASE_URL}/v1/repo-summary",
        json={"repo_url": repo_url},
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()
    return data["summary"]

def get_repo_summary_tool() -> FunctionTool:
    """
    ADK FunctionTool wrapping the Cloud Run /v1/repo-summary endpoint.
    """
    return FunctionTool(_repo_summary_impl)
```

**Agent wiring (lazy):**

```python
def create_agent() -> LlmAgent:
    from agents.shared_tools.cloud_run_tools import get_repo_summary_tool

    tools = [
        get_repo_summary_tool(),
        # ... other tools (VertexAiSearchTool, etc.)
    ]

    return LlmAgent(
        model="gemini-2.0-flash-exp",
        name="bob",
        tools=tools,
        instruction=instruction,
        after_agent_callback=auto_save_session_to_memory,
    )
```

**Rules:**
- Cloud Run base URLs come from env (`*_BASE_URL`), never hard-coded per environment
- The FunctionTool wrapper:
  - Has no GCP/HTTP calls at import time
  - Only calls the external service when invoked

---

### 3.3 MCP / A2A Tools (Future)

When you start doing real A2A + MCP, tools should look like:

```python
from google.adk.tools import MCPToolset

def get_git_mcp_toolset() -> MCPToolset:
    return MCPToolset(
        # config for MCP client that talks to a Cloud Run MCP server
    )
```

**Agent wiring:** same lazy pattern in `create_agent()`.

---

## 4. Lazy-Loading & Circular Import Rules

To stay compliant with 6767-LAZY and avoid the circular madness you just went through:

### 1. No tool imports at module level in `agents/*/agent.py`:
- ✅ **Allowed:** `from google.adk.agents import LlmAgent` at top
- ❌ **Not allowed:** `from agents.shared_tools import BOB_TOOLS` at top

### 2. Always import tool profiles inside `create_agent()`:

```python
def create_agent() -> LlmAgent:
    from agents.shared_tools import BOB_TOOLS
    ...
```

### 3. Tool creation may not:
- Call GCP or Cloud Run at import time
- Validate env vars at import time
- Do anything more expensive than small pure-Python operations

### 4. Env validation is runtime-only:
- If a URL or datastore ID is missing, fail when the tool is actually called, not when the module is imported

---

## 5. Agent Responsibilities vs Cloud Run Responsibilities

### Agent (ADK / Agent Engine side)

**Owns:**
- Prompt, instruction, and persona
- Which tools it's allowed to call
- The schema of those tool calls (arguments & return types)
- R5 dual memory wiring (Session + Memory Bank)

**Does not own:**
- Heavy logic in tools
- Long-running jobs
- State that should live in managed services (databases, queues)

### Cloud Run services

**Own:**
- Actual implementation of "repo index", "issue sync", "run fix plan", etc.
- Data storage & IO (Firestore, Postgres, GCS, etc.)
- Retry, idempotency, safety switches, audits

**Expose:**
- Clean, versioned APIs
- Auth (IAP, service account, etc.) where needed

---

## 6. Testing & ARV Expectations

For each Cloud Run–backed tool, ARV / CI should have:

### 1. Unit tests (Python-side):
- Mock HTTP responses for the FunctionTool implementation
- Verify ADK tool type is correct (callable or FunctionTool instance)

### 2. Integration tests (Cloud Run–side):
- Hit `/healthz` on the service
- Hit a test endpoint with a known fixture and check response

### 3. ARV gate:
Fails if:
- A tool list contains a dict instead of a proper ADK type
- Tool import at module level creates a circular import
- Tool construction does heavy work at import time

---

## 7. How to adopt this in bobs-brain now

Short version of what you've already done and what's next:

### ✅ Completed (Phase 13):
- **Vertex search tool:** Already converted to VertexAiSearchTool
- **Lazy imports:** Implemented in Phase 13 (no module-level tools in agents)
- **Tests:** Tool validation is now green; remaining red tests are A2A & lazy-loading expectations, not tool plumbing

### ⏳ Next Steps:
- **Cloud Run tools:**
  - Add `agents/shared_tools/cloud_run_tools.py` with FunctionTool wrappers
  - Replace any "internal" repo/issue logic in agents with calls to those tools as you build the services

---

## 8. Future Work

### When ready to implement Cloud Run tools:
1. **Draft `cloud_run_tools.py` skeleton** for first service (e.g., "issue indexer" or "repo ops")
2. **Design service APIs** with versioned endpoints, health checks, auth
3. **Wire FunctionTool wrappers** following the pattern in section 3.2
4. **Add integration tests** for Cloud Run services
5. **Update ARV checks** to validate Cloud Run tool contracts

### When ready for MCP/A2A:
1. **Design MCP server contracts** for external tool providers
2. **Implement MCPToolset wrappers** following pattern in section 3.3
3. **Add A2A protocol validation** for cross-agent tool calls

---

## 9. References

**Related Standards:**
- `000-DR-STND-adk-lazy-loading-app-pattern.md` - Lazy loading pattern
- `000-DR-STND-adk-agent-engine-spec-and-hardmode-rules.md` - Hard Mode rules (R1-R8)
- `000-DR-STND-agentcards-and-a2a-contracts.md` - AgentCard and A2A patterns

**Phase Documentation:**
- `141-AA-REPT-phase-13-tools-validation-and-refactor.md` - Tools refactor (dict → VertexAiSearchTool)

---

**Document Status:** Draft v0.1
**Next Review:** After first Cloud Run tool implementation
**Owner:** bobs-brain / department adk iam
