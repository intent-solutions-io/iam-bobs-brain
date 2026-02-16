# 138-PP-PLAN – ADK 1.18 Migration & App/Memory Alignment

**Phase:** Phase 12 - ADK 1.18 Migration & App/Memory Alignment
**Date:** 2025-11-21
**Status:** 📋 PLAN (Implementation Pending)
**Branch:** `feature/a2a-agentcards-foreman-worker`

---

## I. Executive Summary

**Objective:** Migrate all agent code to google-adk 1.18+ API, align App/memory patterns with actual API, and achieve 155/155 tests passing while maintaining R5 dual memory compliance.

**Scope:**
- Update `App` creation pattern to use Pydantic model with `name` and `root_agent`
- Preserve `Runner` pattern for backwards compatibility and local testing with dual memory
- Remove lazy-loading validation anti-pattern (env var checks at module import)
- Update all 11 agent files (bob, iam_adk, iam-senior-adk-devops-lead, iam_issue, iam_fix_plan, iam_fix_impl, iam_qa, iam_doc, iam_cleanup, iam_index, and tool files)
- Fix all 20 failing tests
- Pin google-adk to 1.18.x in requirements.txt

**Hard Constraints:**
- ✅ Maintain R5 dual memory requirement (Session + Memory Bank)
- ✅ Maintain lazy-loading pattern (no heavy work at module import)
- ✅ Maintain module-level `app` symbol for Agent Engine entrypoints (R2)
- ✅ Maintain backwards compatibility via `create_runner()` function
- ✅ Do NOT change R1-R8 Hard Mode rules compliance

---

## II. Background Context

### Prior Phases

**Phase 10B** (AAR 136):
- Fixed import path: `from google.adk.apps import App` ✅
- Fixed parameter rename: `project_id` → `project` ✅
- Discovered App constructor breaking changes ⚠️
- BLOCKED on App API migration

**Phase 11** (AAR 137):
- Systematically tested google-adk versions 1.5.0, 1.12.0, 1.14.0, 1.16.0, 1.17.0, 1.18.0
- **CRITICAL FINDING**: NO version supports `App(agent=..., app_name=..., session_service=..., memory_service=...)`
- Versions 1.5.0-1.12.0: No App class at all
- Versions 1.16.0+: Pydantic App with different API
- **Conclusion**: Code was never tested against actual google-adk, no compatible version exists
- BLOCKED - recommended proper 1.18+ migration

---

## III. API Analysis (google-adk 1.18.0)

### 1. App (google.adk.apps.App)

**Actual API:**
```python
App.__init__(self, /, **data: 'Any') -> 'None'
```

**Required Fields:**
- `name`: str (replaces `app_name`)
- `root_agent`: BaseAgent **instance** (replaces `agent` function reference)

**Optional Fields:**
- `plugins`: list[BasePlugin]
- `events_compaction_config`: Optional
- `context_cache_config`: Optional
- `resumability_config`: Optional

**❌ REMOVED:**
- `session_service` - NOT ACCEPTED
- `memory_service` - NOT ACCEPTED

**Key Change**: App uses Pydantic model with `**data` pattern. Session and memory services are NOT configured at App level.

---

### 2. Runner (google.adk.Runner)

**Actual API:**
```python
Runner.__init__(
    self, *,
    app: Optional[App] = None,
    app_name: Optional[str] = None,
    agent: Optional[BaseAgent] = None,
    plugins: Optional[List[BasePlugin]] = None,
    artifact_service: Optional[BaseArtifactService] = None,
    session_service: BaseSessionService,  # REQUIRED
    memory_service: Optional[BaseMemoryService] = None,
    credential_service: Optional[BaseCredentialService] = None
)
```

**✅ ACCEPTS**:
- `session_service` - **REQUIRED**
- `memory_service` - **Optional**

**Key Insight**: Runner is where dual memory services are configured for local/CI execution.

---

### 3. Memory Service Signatures (Unchanged from Phase 10B fixes)

**VertexAiSessionService:**
```python
VertexAiSessionService(
    project: Optional[str] = None,
    location: Optional[str] = None,
    agent_engine_id: Optional[str] = None,
    *,
    express_mode_api_key: Optional[str] = None
)
```

**VertexAiMemoryBankService:**
```python
VertexAiMemoryBankService(
    project: Optional[str] = None,
    location: Optional[str] = None,
    agent_engine_id: Optional[str] = None,
    *,
    express_mode_api_key: Optional[str] = None
)
```

**No changes needed** - Phase 10B fixes already correct.

---

## IV. Migration Design

### Design Principle: Dual-Pattern Approach

**For Agent Engine Deployment (R2):**
- Use `App` with `name` and `root_agent`
- Agent Engine runtime provides session/memory services automatically
- Entrypoint: `agents.{name}.agent.app`

**For Local/CI Testing:**
- Use `Runner` with explicit `session_service` and `memory_service`
- Satisfies R5 dual memory requirement
- Backwards compatible with existing test patterns

---

### Pattern 1: Agent Creation (create_agent)

**CURRENT (Broken)**:
```python
def create_agent() -> LlmAgent:
    # ❌ Validates env vars at call time (breaks lazy loading)
    if not PROJECT_ID:
        raise ValueError("PROJECT_ID environment variable is required")
    if not LOCATION:
        raise ValueError("LOCATION environment variable is required")
    if not AGENT_ENGINE_ID:
        raise ValueError("AGENT_ENGINE_ID environment variable is required")

    agent = LlmAgent(
        model="gemini-2.0-flash-exp",
        name="iam_adk",
        tools=IAM_ADK_TOOLS,
        instruction=instruction,
        after_agent_callback=auto_save_session_to_memory,
    )
    return agent
```

**NEW (Lazy-Loading Compliant)**:
```python
def create_agent() -> LlmAgent:
    """
    Create and configure the LlmAgent.

    Called by create_app() on first use (module-level app creation).
    Do NOT call this at module import time from external code.

    Note: Environment variable validation removed - ADK handles this on invocation.
    """
    # ✅ No validation - let ADK handle it on actual invocation
    # ✅ Cheap to call - just creates object, no GCP calls

    logger.info(
        f"Creating iam-adk LlmAgent for {APP_NAME}",
        extra={"spiffe_id": AGENT_SPIFFE_ID},
    )

    agent = LlmAgent(
        model="gemini-2.0-flash-exp",
        name="iam_adk",
        tools=IAM_ADK_TOOLS,
        instruction=instruction,
        after_agent_callback=auto_save_session_to_memory,
    )

    logger.info(
        "✅ iam-adk LlmAgent created successfully",
        extra={"spiffe_id": AGENT_SPIFFE_ID, "model": "gemini-2.0-flash-exp"},
    )

    return agent
```

**Key Changes**:
- ❌ REMOVE env var validation from `create_agent()`
- ✅ Let ADK handle validation on first invocation
- ✅ Keep logger.info calls (cheap, informative)
- ✅ Agent creation is now cheap - safe to call at module level

---

### Pattern 2: App Creation (create_app)

**CURRENT (Broken)**:
```python
def create_app() -> App:
    # Validate required env vars before app creation
    if not PROJECT_ID or not AGENT_ENGINE_ID:
        raise ValueError("PROJECT_ID and AGENT_ENGINE_ID are required for App creation")

    # R5: Create memory services (lazy, inside function)
    session_service = VertexAiSessionService(
        project=PROJECT_ID,
        location=LOCATION,
        agent_engine_id=AGENT_ENGINE_ID
    )

    memory_service = VertexAiMemoryBankService(
        project=PROJECT_ID,
        location=LOCATION,
        agent_engine_id=AGENT_ENGINE_ID
    )

    # ❌ OLD API - doesn't work in 1.18+
    app_instance = App(
        agent=create_agent,  # Function reference
        app_name=APP_NAME,
        session_service=session_service,
        memory_service=memory_service,
    )

    return app_instance
```

**NEW (1.18+ API)**:
```python
def create_app() -> App:
    """
    Create the App container for Agent Engine deployment.

    The App wraps the agent for Vertex AI Agent Engine. When deployed to
    Agent Engine, the runtime automatically provides session and memory services.

    For local testing with dual memory, use create_runner() instead.

    Enforces:
    - R2: App designed for Vertex AI Agent Engine deployment
    - R7: SPIFFE ID propagation in logs

    Returns:
        App: Configured app instance for Agent Engine

    Note:
        - Agent is created here (cheap - no validation, no GCP calls)
        - Session/memory services NOT configured (Agent Engine provides them)
        - For local testing with dual memory, use create_runner()
    """
    logger.info(
        "Creating App container for iam-adk",
        extra={"spiffe_id": AGENT_SPIFFE_ID}
    )

    # ✅ Call create_agent() to get instance (cheap operation)
    agent_instance = create_agent()

    # ✅ NEW API - Pydantic App with name and root_agent
    app_instance = App(
        name=APP_NAME,
        root_agent=agent_instance,
    )

    logger.info(
        "✅ App created successfully for iam-adk",
        extra={
            "spiffe_id": AGENT_SPIFFE_ID,
            "app_name": APP_NAME,
        }
    )

    return app_instance
```

**Key Changes**:
- ❌ REMOVE env var validation from `create_app()`
- ❌ REMOVE session_service creation
- ❌ REMOVE memory_service creation
- ✅ CALL `create_agent()` to get instance (not function reference)
- ✅ NEW: `App(name=APP_NAME, root_agent=agent_instance)`
- ✅ Document that Agent Engine provides memory services automatically

---

### Pattern 3: Runner Creation (create_runner) - Backwards Compatibility

**CURRENT (Partially Broken)**:
```python
def create_runner() -> Runner:
    logger.warning(
        "⚠️  create_runner() is deprecated. Use create_app() instead.",
        extra={"spiffe_id": AGENT_SPIFFE_ID}
    )

    # Validate required env vars
    if not PROJECT_ID or not AGENT_ENGINE_ID:
        raise ValueError("PROJECT_ID and AGENT_ENGINE_ID required")

    # R5: VertexAiSessionService (short-term conversation cache)
    session_service = VertexAiSessionService(
        project=PROJECT_ID, location=LOCATION, agent_engine_id=AGENT_ENGINE_ID
    )

    # R5: VertexAiMemoryBankService (long-term persistent memory)
    memory_service = VertexAiMemoryBankService(
        project=PROJECT_ID, location=LOCATION, agent_engine_id=AGENT_ENGINE_ID
    )

    # Get agent with after_agent_callback configured
    agent = create_agent()

    # ❌ OLD API
    runner = Runner(
        agent=agent,
        app_name=APP_NAME,
        session_service=session_service,
        memory_service=memory_service,
    )

    return runner
```

**NEW (1.18+ API)**:
```python
def create_runner() -> Runner:
    """
    Create Runner with dual memory wiring (Session + Memory Bank).

    DEPRECATED: Use create_app() for Agent Engine deployment.
    This function is kept for backwards compatibility with local testing and CI.

    Enforces:
    - R2: Runner designed for local testing (NOT Agent Engine deployment)
    - R5: Dual memory wiring (Session + Memory Bank)
    - R7: SPIFFE ID propagation in logs

    Returns:
        Runner: Configured runner with dual memory services

    Note:
        This runner is for LOCAL/CI testing only.
        For Agent Engine deployment, use create_app() which returns an App.
    """
    logger.warning(
        "⚠️  create_runner() is deprecated for Agent Engine deployment. "
        "Use create_app() for Agent Engine. create_runner() is for local/CI testing only.",
        extra={"spiffe_id": AGENT_SPIFFE_ID}
    )

    logger.info(
        f"Creating Runner with dual memory for iam-adk",
        extra={
            "spiffe_id": AGENT_SPIFFE_ID,
            "project_id": PROJECT_ID,
            "location": LOCATION,
            "agent_engine_id": AGENT_ENGINE_ID,
        },
    )

    # ✅ Validate env vars HERE (Runner requires them for memory services)
    if not PROJECT_ID or not AGENT_ENGINE_ID:
        raise ValueError("PROJECT_ID and AGENT_ENGINE_ID required for Runner with dual memory")

    # R5: VertexAiSessionService (short-term conversation cache)
    session_service = VertexAiSessionService(
        project=PROJECT_ID, location=LOCATION, agent_engine_id=AGENT_ENGINE_ID
    )
    logger.info("✅ Session service initialized", extra={"spiffe_id": AGENT_SPIFFE_ID})

    # R5: VertexAiMemoryBankService (long-term persistent memory)
    memory_service = VertexAiMemoryBankService(
        project=PROJECT_ID, location=LOCATION, agent_engine_id=AGENT_ENGINE_ID
    )
    logger.info(
        "✅ Memory Bank service initialized", extra={"spiffe_id": AGENT_SPIFFE_ID}
    )

    # Get agent with after_agent_callback configured
    agent = create_agent()

    # ✅ Runner API (still accepts session_service and memory_service)
    runner = Runner(
        agent=agent,
        app_name=APP_NAME,
        session_service=session_service,
        memory_service=memory_service,
    )

    logger.info(
        "✅ Runner created successfully with dual memory",
        extra={
            "spiffe_id": AGENT_SPIFFE_ID,
            "app_name": APP_NAME,
            "has_session_service": True,
            "has_memory_service": True,
        },
    )

    return runner
```

**Key Changes**:
- ✅ KEEP env var validation in `create_runner()` (needed for memory services)
- ✅ Runner API unchanged (still accepts session_service and memory_service)
- ✅ Update deprecation warning to clarify: "for local/CI testing only"
- ✅ Document R5 compliance via Runner for local testing

---

### Pattern 4: Module-Level Entrypoint

**CURRENT**:
```python
# Module-level App (lazy initialization)
# Agent Engine will access this on first request
app = create_app()
```

**NEW (Unchanged)**:
```python
# ✅ Module-level App (for Agent Engine entrypoint)
# Agent is created inside create_app() (cheap - no validation, no GCP calls)
# Agent Engine will access this on first request
app = create_app()

logger.info(
    "✅ App instance created for Agent Engine deployment (iam-adk)",
    extra={"spiffe_id": AGENT_SPIFFE_ID}
)
```

**Key Insight**: Module-level `app = create_app()` is STILL valid because:
- `create_agent()` is cheap (no validation, no GCP calls)
- `App()` constructor is cheap (Pydantic model creation)
- No heavy work happens at import time
- Lazy loading pattern preserved

---

## V. R5 Dual Memory Compliance Strategy

### How R5 is Satisfied in 1.18+

**R5 Requirement**:
> All agents MUST wire dual memory:
> - VertexAiSessionService (short-term conversation cache)
> - VertexAiMemoryBankService (long-term persistent memory)
> - after_agent_callback to save sessions to Memory Bank

**1. Agent Engine Deployment (via App)**:
- Agent Engine runtime automatically provides session and memory services
- Based on `agent_engine_id` configuration
- No explicit wiring needed in App
- `after_agent_callback` still configured in LlmAgent

**2. Local/CI Testing (via Runner)**:
- Explicit `session_service` and `memory_service` passed to Runner
- Full R5 compliance for local testing
- `after_agent_callback` still configured in LlmAgent

**3. Callback Function (Unchanged)**:
```python
def auto_save_session_to_memory(ctx):
    """
    After-agent callback to persist session to Memory Bank.

    This callback is invoked after each agent turn to save the conversation
    session to the Memory Bank for long-term persistence.

    Enforces R5: Dual memory wiring requirement.
    """
    try:
        if hasattr(ctx, "_invocation_context"):
            invocation_ctx = ctx._invocation_context
            memory_svc = invocation_ctx.memory_service
            session = invocation_ctx.session

            if memory_svc and session:
                memory_svc.add_session_to_memory(session)
                logger.info(
                    f"✅ Saved session {session.id} to Memory Bank",
                    extra={"spiffe_id": AGENT_SPIFFE_ID, "session_id": session.id},
                )
            else:
                logger.warning(
                    "Memory service or session not available in context",
                    extra={"spiffe_id": AGENT_SPIFFE_ID},
                )
        else:
            logger.warning(
                "Invocation context not available", extra={"spiffe_id": AGENT_SPIFFE_ID}
            )
    except Exception as e:
        logger.error(
            f"Failed to save session to Memory Bank: {e}",
            extra={"spiffe_id": AGENT_SPIFFE_ID},
            exc_info=True,
        )
        # Never block agent execution
```

**Callback remains unchanged** - works with both App (Agent Engine) and Runner (local) patterns.

---

## VI. Lazy Loading Pattern Verification

### 6767-LAZY Standard Compliance

**Standard Requirements**:
1. Module-level `app` symbol (not `agent`)
2. No heavy work at module import
3. No GCP API calls at import time
4. No env var validation at import time
5. Agent creation callable multiple times safely (idempotent)

**Migration Compliance**:

| Requirement | Current (Broken) | New (1.18+) | Compliant? |
|-------------|------------------|-------------|------------|
| Module-level `app` | ✅ `app = create_app()` | ✅ `app = create_app()` | ✅ YES |
| No heavy work at import | ❌ Validates env vars | ✅ No validation | ✅ YES |
| No GCP calls at import | ✅ No GCP calls | ✅ No GCP calls | ✅ YES |
| No env var validation at import | ❌ Validates in create_agent() | ✅ No validation | ✅ YES |
| Agent creation idempotent | ✅ Can call multiple times | ✅ Can call multiple times | ✅ YES |

**Conclusion**: Migration **improves** 6767-LAZY compliance by removing env var validation anti-pattern.

---

## VII. Implementation Steps

### Step 1: Update Core Pattern in bob Agent ✅

**File**: `agents/bob/agent.py`

**Changes**:
1. Remove env var validation from `create_agent()`
2. Update `create_app()` to new pattern:
   - Call `create_agent()` to get instance
   - Remove session/memory service creation
   - Use `App(name=APP_NAME, root_agent=agent_instance)`
3. Update `create_runner()` to clarify deprecation and R5 compliance
4. Update docstrings

**Estimated Lines Changed**: ~50 lines

---

### Step 2: Update iam_adk Agent ✅

**File**: `agents/iam_adk/agent.py`

**Same changes as bob** - update all three functions (create_agent, create_app, create_runner).

**Estimated Lines Changed**: ~50 lines

---

### Step 3: Update All Remaining IAM Agents ✅

**Files** (9 total):
- `agents/iam-senior-adk-devops-lead/agent.py`
- `agents/iam_issue/agent.py`
- `agents/iam_fix_plan/agent.py`
- `agents/iam_fix_impl/agent.py`
- `agents/iam_qa/agent.py`
- `agents/iam_doc/agent.py`
- `agents/iam_cleanup/agent.py`
- `agents/iam_index/agent.py`

**Changes**: Same pattern as bob/iam_adk

**Estimated Lines Changed**: ~450 lines (9 agents × 50 lines each)

---

### Step 4: Update Tool Files (if needed) ✅

**File**: `agents/iam_adk/tools/analysis_tools.py`

**Check**: Does this file create agents or runners directly?
- If YES: Apply same pattern
- If NO: No changes needed (already uses correct memory service parameters from Phase 10B)

**Estimated Lines Changed**: 0-20 lines (depends on findings)

---

### Step 5: Update Tests ✅

**Files**:
- `tests/unit/test_a2a_card.py` (6 failing tests)
- `tests/unit/test_iam_adk_lazy_loading.py` (14 failing tests)

**Changes**:
1. **test_a2a_card.py**: May need to update agent imports/usage if tests directly instantiate agents
2. **test_iam_adk_lazy_loading.py**:
   - Remove tests that validate env vars at import time (if they exist)
   - Update tests to match new create_app() pattern
   - Verify lazy loading still works (no heavy work at import)

**Estimated Lines Changed**: ~50 lines

---

### Step 6: Pin google-adk in requirements.txt ✅

**File**: `requirements.txt`

**Current**:
```
google-adk>=0.1.0
```

**New**:
```
google-adk>=1.18.0,<1.19.0
```

**Rationale**: Pin to 1.18.x series to avoid future breaking changes while allowing patch updates.

**Estimated Lines Changed**: 1 line

---

## VIII. Testing Strategy

### Test Execution Plan

**1. Unit Tests (Local)**:
```bash
source .venv/bin/activate
pytest tests/unit/ -v
```

**Expected Result**: 155/155 tests pass

**Key Test Categories**:
- ✅ AgentCard JSON validation (18 tests) - Should still pass
- ✅ Storage tests (36 tests) - Should still pass
- ✅ Slack sender tests - Should still pass
- ✅ A2A Card runtime tests (6 tests) - Should now pass (import errors fixed)
- ✅ IAM ADK lazy loading tests (14 tests) - Should now pass (API aligned)

---

**2. Import Smoke Test**:
```python
# Test cheap import (no env vars set)
python3 << 'EOF'
import agents.iam_adk.agent
import agents.bob.agent
print("✅ Imports successful without env vars")
EOF
```

**Expected Result**: No errors, no validation failures

---

**3. Agent Creation Test (With Env Vars)**:
```python
# Test agent creation with env vars
export PROJECT_ID=test-project
export LOCATION=us-central1
export AGENT_ENGINE_ID=test-engine
export AGENT_SPIFFE_ID=spiffe://test

python3 << 'EOF'
from agents.iam_adk.agent import create_agent, create_app
agent = create_agent()
print(f"✅ Agent created: {agent.name}")
app = create_app()
print(f"✅ App created: {app.name}")
EOF
```

**Expected Result**: Agent and App created successfully

---

**4. Runner Test (Dual Memory)**:
```python
# Test runner with dual memory
export PROJECT_ID=test-project
export LOCATION=us-central1
export AGENT_ENGINE_ID=test-engine
export AGENT_SPIFFE_ID=spiffe://test

python3 << 'EOF'
from agents.iam_adk.agent import create_runner
runner = create_runner()
print(f"✅ Runner created with dual memory")
print(f"   session_service: {runner.session_service is not None}")
print(f"   memory_service: {runner.memory_service is not None}")
EOF
```

**Expected Result**: Runner created with both services present

---

## IX. Rollback Plan

**If migration fails or tests don't pass**:

### Step 1: Revert Code Changes
```bash
# Revert all agent file changes
git checkout HEAD -- agents/bob/agent.py
git checkout HEAD -- agents/iam_adk/agent.py
# ... (all other agent files)

# Revert test changes
git checkout HEAD -- tests/unit/
```

### Step 2: Revert google-adk Version
```bash
source .venv/bin/activate
pip install google-adk==1.12.0
```

### Step 3: Re-run Tests
```bash
pytest tests/unit/ -v
```

**Expected State After Rollback**: Back to Phase 11 state (135 passed, 20 failed with known import errors)

---

## X. Success Criteria

**Phase 12 is complete when**:

1. ✅ All 11 agent files updated to 1.18+ API
2. ✅ All 155 unit tests pass
3. ✅ Lazy loading pattern verified (imports work without env vars)
4. ✅ R5 dual memory compliance maintained (via Runner for local/CI)
5. ✅ Module-level `app` symbol preserved (R2 Agent Engine entrypoint)
6. ✅ google-adk pinned to 1.18.x in requirements.txt
7. ✅ No regressions in existing functionality

---

## XI. Files to Modify

### Agent Files (11 total)
1. `agents/bob/agent.py`
2. `agents/iam_adk/agent.py`
3. `agents/iam-senior-adk-devops-lead/agent.py`
4. `agents/iam_issue/agent.py`
5. `agents/iam_fix_plan/agent.py`
6. `agents/iam_fix_impl/agent.py`
7. `agents/iam_qa/agent.py`
8. `agents/iam_doc/agent.py`
9. `agents/iam_cleanup/agent.py`
10. `agents/iam_index/agent.py`
11. `agents/iam_adk/tools/analysis_tools.py` (if needed)

### Test Files (2 test modules)
1. `tests/unit/test_a2a_card.py`
2. `tests/unit/test_iam_adk_lazy_loading.py`

### Dependency File (1 file)
1. `requirements.txt`

**Total Files**: 14 files

---

## XII. Risks & Mitigations

### Risk 1: Lazy Loading Breaks
**Risk**: Calling `create_agent()` at module level might violate lazy loading

**Mitigation**:
- `create_agent()` is cheap (no validation, no GCP calls)
- Verified via import smoke test without env vars
- Lazy loading pattern actually **improves** (removes validation anti-pattern)

---

### Risk 2: R5 Dual Memory Compliance Lost
**Risk**: App doesn't accept memory services - R5 violation?

**Mitigation**:
- Agent Engine provides memory services automatically
- Runner preserves explicit dual memory for local/CI
- Callback function unchanged (works with both patterns)
- R5 satisfied via different mechanisms (Agent Engine vs Runner)

---

### Risk 3: Tests Require Unexpected Changes
**Risk**: Tests may assume old API patterns deeply

**Mitigation**:
- Most tests (129/155) already pass (static validation)
- Only 20 tests failing (all import-related)
- Test changes should be minimal (update imports/usage)
- Rollback plan ready if tests won't pass

---

### Risk 4: Hidden Dependencies on Old API
**Risk**: Code outside agents/ may depend on old patterns

**Mitigation**:
- Full test suite will catch any external dependencies
- Most code uses agents via entrypoints (module-level `app`)
- Service code uses HTTP/gRPC (not direct agent imports)

---

## XIII. Post-Migration Verification

**After implementation, verify**:

### 1. Import Test (No Env Vars)
```bash
python3 -c "import agents.bob.agent; import agents.iam_adk.agent; print('✅ Imports OK')"
```

### 2. Full Test Suite
```bash
pytest tests/unit/ -v
# Expected: 155/155 passed
```

### 3. Inline Deploy Dry-Run
```bash
make deploy-inline-dry-run
# Expected: ✅ All validations passed
```

### 4. ARV Minimum Checks
```bash
make check-inline-deploy-ready
# Expected: Pass (or fail only on missing GCP env vars, not code issues)
```

---

## XIV. Next Steps After Migration

**Immediate**:
1. Run full test suite and verify 155/155 pass
2. Create AAR 139 documenting results
3. Commit with message: `feat(agents): migrate to google-adk 1.18+ API`

**Follow-Up** (Future Phases):
1. Phase 13 (if needed): First dev deployment to Agent Engine
2. Phase 14 (if needed): Verify R5 dual memory works in Agent Engine runtime
3. v0.11.0 planning: Decide next major features

---

## XV. References

**Prior AARs**:
- `000-docs/134-AA-REPT-phase-10-pr-merge-release-blocked-on-test-env.md` - Original test blocker
- `000-docs/135-AA-REPT-phase-10-unblocked-new-import-error-discovered.md` - Import errors
- `000-docs/136-AA-REPT-phase-10b-extensive-api-changes-discovered.md` - 1.18.0 API changes
- `000-docs/137-AA-REPT-phase-11-pre-upgrade-stabilization-blocked.md` - No compatible version found

**Standards**:
- `000-docs/000-DR-STND-adk-agent-engine-spec-and-hardmode-rules.md` - R1-R8 Hard Mode rules
- `000-docs/000-DR-STND-adk-lazy-loading-app-pattern.md` - Lazy loading pattern
- `000-docs/127-DR-STND-agent-engine-entrypoints.md` - Agent Engine entrypoints
- `000-docs/000-DR-STND-document-filing-system-standard-v4.md` - Filing system

---

**Prepared by:** Claude Code (Phase 12 PLAN)
**Date:** 2025-11-21
**Status:** Ready for Implementation
**Next:** Execute implementation steps and create AAR 139
