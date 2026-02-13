# 127-DR-STND-agent-engine-entrypoints

**Status**: Canonical Standard (INLINE1 Phase)
**Author**: Build Captain
**Created**: 2025-11-21
**Last Updated**: 2025-11-21

---

## Purpose

This document defines the **canonical ADK/Agent Engine entrypoints** for all agents in the bobs-brain repository. These entrypoints are used by inline source deployment (6775 standard) to deploy agents to Vertex AI Agent Engine.

---

## Canonical Entrypoints

### Bob (Global Orchestrator)

**Module**: `agents.bob.agent`
**Object**: `app`
**Pattern**: Lazy-loading App (6774 standard)

**Location in Code**:
```python
# agents/bob/agent.py:405
app = create_app()
```

**What It Does**:
- Creates `App` instance with lazy agent initialization
- Wires dual memory services (R5): VertexAiSessionService + VertexAiMemoryBankService
- Propagates SPIFFE ID in logs (R7)
- Ready for Agent Engine deployment

**Inline Source Configuration** (from `agents/agent_engine/deploy_inline_source.py`):
```python
"bob": {
    "entrypoint_module": "agents.bob.agent",
    "entrypoint_object": "app",
    "class_methods": ["query", "orchestrate"],
    "display_name": "Bob (Global Orchestrator)",
}
```

---

### IAM Senior ADK DevOps Lead (Foreman)

**Module**: `agents.iam_senior_adk_devops_lead.agent`
**Object**: `app`
**Pattern**: Lazy-loading App (6774 standard)

**Inline Source Configuration**:
```python
"iam-senior-adk-devops-lead": {
    "entrypoint_module": "agents.iam_senior_adk_devops_lead.agent",
    "entrypoint_object": "app",
    "class_methods": ["orchestrate_workflow", "validate_specialist_output"],
    "display_name": "IAM Senior ADK DevOps Lead (Foreman)",
}
```

---

### IAM-ADK (Specialist)

**Module**: `agents.iam_adk.agent`
**Object**: `app`
**Pattern**: Lazy-loading App (6774 standard)

**Inline Source Configuration**:
```python
"iam-adk": {
    "entrypoint_module": "agents.iam_adk.agent",
    "entrypoint_object": "app",
    "class_methods": ["check_adk_compliance", "validate_agentcard"],
    "display_name": "IAM ADK (Specialist)",
}
```

---

## Lazy-Loading App Pattern (6774)

All agents follow this pattern:

```python
# agents/{agent_name}/agent.py

def create_agent() -> LlmAgent:
    """Lazy agent creation - validates env vars here, not at import."""
    # Validation
    if not PROJECT_ID:
        raise ValueError("PROJECT_ID required")

    # Create agent
    agent = LlmAgent(
        model="gemini-2.0-flash-exp",
        name="agent_name",
        tools=TOOLS,
        instruction=INSTRUCTION,
        after_agent_callback=auto_save_session_to_memory,  # R5
    )
    return agent


def create_app() -> App:
    """Create App container for Agent Engine."""
    # Create memory services (R5)
    session_service = VertexAiSessionService(
        project_id=PROJECT_ID,
        location=LOCATION,
        agent_engine_id=AGENT_ENGINE_ID
    )

    memory_service = VertexAiMemoryBankService(
        project=PROJECT_ID,
        location=LOCATION,
        agent_engine_id=AGENT_ENGINE_ID
    )

    # Create App with lazy agent creation
    app_instance = App(
        agent=create_agent,  # Function reference, not called yet
        app_name=APP_NAME,
        session_service=session_service,
        memory_service=memory_service,
    )

    return app_instance


# Module-level App (Agent Engine entrypoint)
app = create_app()
```

**Key Points**:
- ✅ Module-level `app`, not `agent`
- ✅ `create_agent` passed as function reference to `App()`
- ✅ Validation happens in `create_agent()`, not at import time
- ✅ Dual memory wiring in `create_app()`

**See**: `000-docs/000-DR-STND-adk-lazy-loading-app-pattern.md` for complete pattern spec

---

## Legacy Files (Ignore for Inline Source)

### `agents/bob/agent_engine_app.py`

**Status**: LEGACY - Do NOT use for inline source deployment

**Why It Exists**:
- Originally created for `adk deploy agent_engine` CLI command (old deployment method)
- Uses deprecated `create_runner()` pattern
- Not compatible with inline source deployment

**What It Does**:
```python
# agents/bob/agent_engine_app.py
from .agent import create_runner

# DEPRECATED: Uses Runner pattern instead of App
app = create_runner()
```

**Why NOT to Use**:
- Inline source deployment requires `App` pattern, not `Runner`
- `create_runner()` is marked deprecated in `agents/bob/agent.py:323`
- Canonical entrypoint is `agents.bob.agent.app`, not `agents.bob.agent_engine_app.app`

**Action Required**: None - leave as-is for backwards compatibility with old deploy scripts

---

## How Inline Source Deployment Uses Entrypoints

When you run inline source deployment (6775 standard):

```bash
python -m agents.agent_engine.deploy_inline_source \
  --project bobs-brain-dev \
  --location us-central1 \
  --agent-name bob \
  --env dev
```

**What Happens**:

1. **Script reads config** from `AGENT_CONFIGS` dict (line 60-80 of deploy_inline_source.py)
2. **Packages source** from `source_packages = ["agents"]`
3. **Tells Agent Engine**:
   - Import module: `agents.bob.agent`
   - Access object: `app`
   - Available methods: `["query", "orchestrate"]`
4. **Agent Engine imports** `agents.bob.agent` and accesses `app` object
5. **Agent Engine invokes** `app.run()` or `app.run_live()` for each request

**Key Insight**: Agent Engine never calls `create_agent()` or `create_app()` directly. It only imports the module and accesses the `app` variable.

---

## Validation Checklist

Before deploying an agent via inline source:

- [ ] Agent has `agents/{name}/agent.py` file
- [ ] File contains `create_agent()` function (lazy validation)
- [ ] File contains `create_app()` function (wires dual memory)
- [ ] File has module-level `app = create_app()` statement
- [ ] `app` is an `App` instance (not `Runner`, not `LlmAgent`)
- [ ] Agent config exists in `deploy_inline_source.py` AGENT_CONFIGS dict
- [ ] `entrypoint_module` points to correct module path
- [ ] `entrypoint_object` is `"app"` (lowercase)
- [ ] `class_methods` list matches agent's available methods

---

## Troubleshooting

### "Module not found" error during deployment

**Problem**: Agent Engine can't import `agents.{name}.agent`

**Fix**:
1. Verify module path is correct in AGENT_CONFIGS
2. Ensure `agents/` is in `source_packages` list
3. Check that `agents/{name}/__init__.py` exists

### "Object 'app' not found" error

**Problem**: Agent Engine imported module but can't find `app` variable

**Fix**:
1. Verify `agent.py` has module-level `app = create_app()` statement
2. Ensure `entrypoint_object` is `"app"` (not `"agent"`, not `"root_agent"`)
3. Check that `app` is not inside `if __name__ == "__main__"` block

### "App is not an App instance" error

**Problem**: Agent Engine found `app` but it's wrong type

**Fix**:
1. Ensure `app = create_app()` returns `App` instance, not `Runner` or `LlmAgent`
2. Check imports: `from google.adk import App` (not `Runner`)
3. Verify not using legacy `create_runner()` pattern

---

## Related Standards

- **000-DR-STND-adk-lazy-loading-app-pattern.md** - Lazy-loading App pattern spec
- **000-DR-STND-inline-source-deployment-for-vertex-agent-engine.md** - Inline source deployment standard
- **000-DR-STND-adk-agent-engine-spec-and-hardmode-rules.md** - Hard Mode rules (R1-R8)

---

**Maintained by**: Build Captain
**Last Review**: 2025-11-21
**Next Review**: When ADK introduces breaking changes to App/Agent Engine integration
