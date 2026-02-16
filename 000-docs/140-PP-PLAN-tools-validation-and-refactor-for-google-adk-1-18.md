# PLAN: Phase 13 - Tools Validation & Refactor for google-adk 1.18+

**Status**: 🚧 IN PROGRESS
**Date**: 2025-11-21
**Phase**: Phase 13 - Tools Validation & Refactor
**Related Documents**:
- Prior AAR: `139-AA-REPT-phase-12-adk-1-18-migration-and-app-memory-alignment.md`
- Hard Mode Spec: `000-DR-STND-adk-agent-engine-spec-and-hardmode-rules.md`

---

## I. Executive Summary

### Problem

After Phase 12's successful App migration to google-adk 1.18+, **18 tests are failing** with Pydantic validation errors on `LlmAgent.tools`. All failures trace to a single root cause: **dict-based tool configurations** in `agents/shared_tools/vertex_search.py` that don't match google-adk 1.18's stricter tool validation.

**Error Pattern**:
```python
pydantic_core._pydantic_core.ValidationError: 3 validation errors for LlmAgent
tools.4.callable
  Input should be callable [type=callable_type, input_value={'type': 'vertex_search',...}]
tools.4.is-instance[BaseTool]
  Input should be an instance of BaseTool [type=is_instance_of, input_value={'type': 'vertex_search',...}]
tools.4.is-instance[BaseToolset]
  Input should be an instance of BaseToolset [type=is_instance_of, input_value={'type': 'vertex_search',...}]
```

**Current State**: 137/155 tests passing (88%)
**Target**: 155/155 tests passing (100%)

### Objective

Refactor the shared tools layer (`agents/shared_tools/`) to use proper ADK tool instances (`BaseTool` subclasses or `FunctionTool` wrappers) instead of raw dictionaries, achieving 155/155 test pass rate while maintaining:
- R1: ADK-only tools compliance
- R5: Dual memory compliance (unchanged - App/Runner patterns from Phase 12)
- All Hard Mode rules (R1-R8)
- Existing tool semantics and capabilities

### Scope

**IN SCOPE:**
- Replace dict-based tool in `agents/shared_tools/vertex_search.py` with `VertexAiSearchTool`
- Wrap Python function tools with `FunctionTool` where needed
- Fix circular import issues in `agents/shared_tools/custom_tools.py`
- Update tests to assert against proper tool types (not dict structure)
- Achieve 155/155 test pass rate

**OUT OF SCOPE:**
- App/Runner patterns (Phase 12 complete - don't touch)
- Terraform/GCP infrastructure
- CI/CD workflows (unless required for local testing)
- Adding new tool capabilities (semantic changes only where necessary)

---

## II. Current Failure Analysis

### A. Failing Tests Breakdown

**Total Failures**: 18 tests
- `tests/unit/test_a2a_card.py`: 6 failures
- `tests/unit/test_iam_adk_lazy_loading.py`: 12 failures

**Failure Pattern**: All 18 failures have the **same root cause**:
- Error occurs at module import time (not during test execution)
- Error location: `agents/bob/agent.py:224` → `LlmAgent(..., tools=BOB_TOOLS)`
- Invalid tool: `tools[4]` is a dict: `{'type': 'vertex_search', ...}`
- Expected: `BaseTool` instance or callable

### B. Root Cause: Dict-Based Vertex Search Tool

**File**: `agents/shared_tools/vertex_search.py`

**Problem Code** (lines 101-109 and 140-149):
```python
# Legacy configuration
return {
    "type": "vertex_search",
    "config": {
        "project_id": "bobs-brain",
        "location": "us",
        "datastore_id": "bob-vertex-agent-datastore",
        "legacy": True
    }
}

# New configuration
return {
    "type": "vertex_search",
    "config": {
        "project_id": datastore_config["project_id"],
        "location": datastore_config["location"],
        "datastore_id": datastore_config["id"],
        "source_uri": env_config["source"]["uri_pattern"],
        "environment": env
    }
}
```

**Why This Fails**:
- google-adk 1.18 enforces Pydantic validation on `LlmAgent.tools`
- Each tool must be:
  - A callable (Python function), OR
  - An instance of `BaseTool`, OR
  - An instance of a toolset (e.g., `MCPToolset`)
- Dict objects fail all three validation checks

**TODO Comments** (lines 122-137):
```python
# TODO: Import and use actual ADK VertexAiSearchToolset
# from google.adk.toolsets import VertexAiSearchToolset  # ❌ Module doesn't exist
# tool = VertexAiSearchToolset(...)  # ❌ Class doesn't exist
```

**Actual ADK 1.18 API**:
```python
from google.adk.tools import VertexAiSearchTool  # ✅ Exists

tool = VertexAiSearchTool(
    data_store_id="bob-vertex-agent-datastore",
    # Optional parameters:
    # filter="...",
    # max_results=10,
)
```

### C. Secondary Issue: Circular Imports

**Warning Messages** (from test output):
```
WARNING agents.shared_tools.custom_tools:custom_tools.py:66
  Could not import analysis tools: cannot import name 'IAM_ADK_TOOLS' from
  partially initialized module 'agents.shared_tools'
  (most likely due to a circular import)
```

**Pattern**: `custom_tools.py` tries to import from agent-specific tool modules, which try to import from `shared_tools/__init__.py`, which is still initializing → circular dependency.

**Files Affected**:
- `agents/shared_tools/custom_tools.py` (imports from agents)
- `agents/bob/tools/adk_tools.py` (may import from shared_tools)
- Other agent tool modules (similar pattern)

**Impact**: Tools fail to load, causing empty tool lists and test failures.

---

## III. Available ADK Tool Classes (google-adk 1.18+)

### A. API Introspection Results

**Method**:
```python
from google.adk import tools
dir(tools)
```

**Available Tool Classes**:

| Class | Purpose | Signature |
|-------|---------|-----------|
| `BaseTool` | Base class for all tools | `__init__(*, name, description, is_long_running=False, custom_metadata=None)` |
| `VertexAiSearchTool` | Vertex AI Search (RAG) | `__init__(*, data_store_id=None, data_store_specs=None, search_engine_id=None, filter=None, max_results=None)` |
| `DiscoveryEngineSearchTool` | Discovery Engine search | Similar to VertexAiSearchTool |
| `FunctionTool` | Wrap Python functions | `__init__(func, *, require_confirmation=False)` |
| `MCPToolset` | MCP toolset wrapper | `__init__(*args, **kwargs)` |
| `APIHubToolset` | API Hub toolset | `__init__(*args, **kwargs)` |
| `AgentTool` | Agent-to-agent tool | (Advanced - for A2A delegation) |

**NOT Available** (despite TODO comments):
- ❌ `BaseToolset` (doesn't exist in `google.adk.tools`)
- ❌ `VertexAiSearchToolset` (no `google.adk.toolsets` module)

### B. Tool Validation Rules (google-adk 1.18+)

**Pydantic Validation** (in `LlmAgent.__init__`):
```python
tools: List[Union[Callable, BaseTool, MCPToolset]]
```

**Each tool must satisfy ONE of**:
1. `callable(tool)` → True (Python function/method)
2. `isinstance(tool, BaseTool)` → True (tool instance)
3. `isinstance(tool, MCPToolset)` → True (toolset instance)

**Dict objects satisfy NONE** → ValidationError

---

## IV. Proposed Tools Architecture

### A. Design Principles

1. **Type Correctness**: All tools are proper ADK instances or callables
2. **Least Privilege**: Each agent gets only needed tools
3. **Separation of Concerns**: Shared tools module owns tool construction
4. **No Circular Imports**: Tools don't depend on agent modules
5. **Backwards Compatibility**: Keep tool semantics the same where possible

### B. New Tools Pattern

#### Pattern 1: Replace Dict-Based Tools with ADK Tool Instances

**File**: `agents/shared_tools/vertex_search.py`

**BEFORE** (Broken):
```python
def get_bob_vertex_search_tool(env: Optional[str] = None) -> Any:
    # ...config loading...

    # ❌ Returns dict
    return {
        "type": "vertex_search",
        "config": {
            "project_id": "bobs-brain",
            "location": "us",
            "datastore_id": "bob-vertex-agent-datastore",
            "legacy": True
        }
    }
```

**AFTER** (Fixed):
```python
from google.adk.tools import VertexAiSearchTool
from typing import Optional

def get_bob_vertex_search_tool(env: Optional[str] = None) -> Optional[VertexAiSearchTool]:
    """
    Get Vertex AI Search tool configured for Bob.

    Returns:
        VertexAiSearchTool instance or None if config not available
    """
    # Determine environment
    if env is None:
        env = get_current_environment()

    logger.info(f"Configuring Vertex AI Search for environment: {env}")

    # Load configuration
    config = load_vertex_search_config()

    # Check for migration flag
    use_org_knowledge = os.getenv("USE_ORG_KNOWLEDGE", "false").lower() == "true"

    if not use_org_knowledge:
        # Legacy configuration
        logger.info("Using legacy Vertex Search configuration")

        # ✅ Return proper ADK tool instance
        return VertexAiSearchTool(
            data_store_id="bob-vertex-agent-datastore",
            # Note: project_id and location are inferred from credentials
            # max_results=10,  # Optional
        )

    # New org knowledge hub configuration
    if "environments" not in config or env not in config["environments"]:
        logger.error(f"No configuration found for environment: {env}")
        return None

    env_config = config["environments"][env]
    datastore_config = env_config["datastore"]

    logger.info(f"Using datastore: {datastore_config['id']} in project: {datastore_config['project_id']}")

    # ✅ Return proper ADK tool instance
    return VertexAiSearchTool(
        data_store_id=datastore_config["id"],
        # Optional: Configure search parameters
        # filter=env_config.get("filter"),
        # max_results=env_config.get("max_results", 10),
    )
```

**Key Changes**:
1. Import `VertexAiSearchTool` from `google.adk.tools`
2. Return type annotation: `Optional[VertexAiSearchTool]`
3. Return actual tool instance (not dict)
4. Remove config dict (ADK tool handles configuration internally)

---

#### Pattern 2: Wrap Python Functions with FunctionTool

**File**: `agents/shared_tools/custom_tools.py`

**BEFORE** (May be broken):
```python
def get_adk_docs_tools() -> List[Any]:
    try:
        from agents.bob.tools.adk_tools import (
            search_adk_docs,
            get_adk_api_reference,
            list_adk_documentation,
        )
        # These are plain Python functions
        return [search_adk_docs, get_adk_api_reference, list_adk_documentation]
    except ImportError as e:
        logger.warning(f"Could not import ADK docs tools: {e}")
        return []
```

**AFTER** (If functions need wrapping):
```python
from google.adk.tools import FunctionTool

def get_adk_docs_tools() -> List[FunctionTool]:
    """
    Get ADK documentation tools from Bob's implementation.

    Returns:
        List of FunctionTool instances wrapping doc search functions
    """
    try:
        from agents.bob.tools.adk_tools import (
            search_adk_docs,
            get_adk_api_reference,
            list_adk_documentation,
        )

        # ✅ Wrap functions with FunctionTool (if not already BaseTool instances)
        return [
            FunctionTool(search_adk_docs),
            FunctionTool(get_adk_api_reference),
            FunctionTool(list_adk_documentation),
        ]
    except ImportError as e:
        logger.warning(f"Could not import ADK docs tools: {e}")
        return []
```

**Note**: Only wrap if the imported functions are **plain Python functions**. If they're already `BaseTool` instances, use them directly.

---

#### Pattern 3: Fix Circular Imports

**Problem**: `custom_tools.py` imports from agent tool modules, which may import from `shared_tools/__init__.py` → circular dependency.

**Solution 1: Lazy Imports** (Recommended):
```python
def get_adk_docs_tools() -> List[Any]:
    """
    Get ADK documentation tools.

    Note: Uses lazy import to avoid circular dependencies.
    """
    # ✅ Import inside function (not at module level)
    try:
        from agents.bob.tools.adk_tools import (
            search_adk_docs,
            get_adk_api_reference,
            list_adk_documentation,
        )
        return [search_adk_docs, get_adk_api_reference, list_adk_documentation]
    except ImportError as e:
        logger.warning(f"Could not import ADK docs tools: {e}")
        return []
```

**Solution 2: Move Tool Definitions** (If needed):
- Move shared tool definitions from `agents/*/tools/` to `agents/shared_tools/`
- Agents import from `shared_tools` (one-way dependency)
- No circular imports

---

### C. Updated Tool Profiles

**File**: `agents/shared_tools/__init__.py`

**Module-Level Exports** (BEFORE):
```python
# ❌ These may contain dicts
BOB_TOOLS = get_bob_tools()
IAM_ADK_TOOLS = get_iam_adk_tools()
# ...
```

**Module-Level Exports** (AFTER):
```python
# ✅ These now contain only BaseTool instances or callables
BOB_TOOLS = get_bob_tools()  # Returns List[Union[BaseTool, Callable]]
IAM_ADK_TOOLS = get_iam_adk_tools()
# ...
```

**No changes needed** to `__init__.py` structure - the fix is in the tool factory functions (`get_bob_tools()`, etc.) that call `get_bob_vertex_search_tool()`.

---

## V. Implementation Plan

### Step 0: Context & Baseline ✅ COMPLETE

1. ✅ Confirmed repo/branch: `/home/jeremy/000-projects/iams/bobs-brain`, branch `feature/a2a-agentcards-foreman-worker`
2. ✅ Ran test suite: 137/155 passing, 18 failures
3. ✅ Identified failure pattern: All 18 failures due to dict in tools list
4. ✅ Scanned relevant docs (138, 139, etc.)

### Step 1: Inspect Shared Tools Architecture ✅ COMPLETE

1. ✅ Opened `agents/shared_tools/__init__.py`
2. ✅ Identified tool factory functions (`get_bob_tools()`, etc.)
3. ✅ Found dict-based tool in `vertex_search.py` (lines 101-109, 140-149)
4. ✅ Inspected `custom_tools.py` for circular import issues
5. ✅ API introspection: Found `VertexAiSearchTool` (not `VertexAiSearchToolset`)

**Findings**:
- Primary issue: `vertex_search.py` returns dict instead of `VertexAiSearchTool`
- Secondary issue: Circular import warnings in `custom_tools.py`
- Available ADK tools: `VertexAiSearchTool`, `FunctionTool`, `MCPToolset`, etc.

### Step 2: Design Clean Shared Tools Pattern ✅ COMPLETE

**Documented in Section IV above.**

Key design:
- Replace dict with `VertexAiSearchTool(data_store_id=...)`
- Wrap plain Python functions with `FunctionTool(func)` if needed
- Use lazy imports in `custom_tools.py` to avoid circular dependencies
- Keep tool profiles structure in `__init__.py` unchanged

### Step 3: Implement Tool Refactor 🚧 IN PROGRESS

**Order of changes**:

1. **Fix `vertex_search.py`** (Primary blocker):
   - Replace dict returns with `VertexAiSearchTool` instances
   - Update `get_bob_vertex_search_tool()`
   - Update `get_foreman_vertex_search_tool()`

2. **Fix circular imports in `custom_tools.py`** (If needed):
   - Ensure all imports are lazy (inside functions)
   - Remove any module-level imports that cause circles

3. **Verify tool factory functions**:
   - Check `get_bob_tools()`, `get_iam_adk_tools()`, etc.
   - Ensure all returned tools are `BaseTool` instances or callables
   - No dicts in any tool list

4. **Update agent modules** (If needed):
   - Verify agents import from `shared_tools` correctly
   - No changes expected (imports should work as-is)

### Step 4: Update Tests 🚧 PENDING

**Focus**:
- `tests/unit/test_a2a_card.py` (6 failing tests)
- `tests/unit/test_iam_adk_lazy_loading.py` (12 failing tests)

**Update strategy**:

1. **Remove dict-based assertions**:
   ```python
   # ❌ BEFORE (assumes dict)
   assert agent.tools[4]["type"] == "vertex_search"

   # ✅ AFTER (checks BaseTool instance)
   assert isinstance(agent.tools[4], VertexAiSearchTool)
   # OR
   assert any(isinstance(t, VertexAiSearchTool) for t in agent.tools)
   ```

2. **Update tool presence checks**:
   ```python
   # ❌ BEFORE (dict structure)
   vertex_tool = next(t for t in tools if isinstance(t, dict) and t.get("type") == "vertex_search")

   # ✅ AFTER (BaseTool instance)
   vertex_tool = next(t for t in tools if isinstance(t, VertexAiSearchTool))
   # OR
   vertex_tool = next(t for t in tools if hasattr(t, 'name') and 'vertex' in t.name.lower())
   ```

3. **Verify tool types**:
   ```python
   # ✅ Good assertions
   from google.adk.tools import BaseTool

   # All tools are valid types
   assert all(
       callable(t) or isinstance(t, BaseTool)
       for t in agent.tools
   )

   # Specific tool exists
   assert any(isinstance(t, VertexAiSearchTool) for t in agent.tools)
   ```

### Step 5: Run Tests and Iterate 🚧 PENDING

**Loop**:
1. Make changes to tools
2. Run: `pytest tests/unit/ -v`
3. If failures remain:
   - Analyze error messages
   - Identify remaining dicts or invalid tools
   - Fix and repeat
4. Stop when: **155 passed, 0 failed**

**Expected iterations**: 2-3 cycles

### Step 6: Finalize Docs 🚧 PENDING

1. Update this PLAN doc if design changed mid-flight
2. Write `141-AA-REPT-phase-13-tools-validation-and-refactor-for-google-adk-1-18.md`:
   - Executive summary
   - Before/after tools architecture
   - Test results (137/155 → 155/155)
   - Any behavior changes (tool names, ordering)
   - Recommendations for future (e.g., 6767 tools standard)

3. Stage and commit changes:
   - `docs(000-docs): add Phase 13 PLAN for tools refactor`
   - `feat(shared-tools): replace dict-based tools with VertexAiSearchTool`
   - `fix(shared-tools): resolve circular import issues`
   - `test(shared-tools): update tests for new ADK tools pattern`
   - `docs(000-docs): add Phase 13 AAR for tools refactor`

### Step 7: Console Summary 🚧 PENDING

Print concise summary:
- Final test status (should be 155/155)
- Which files in `agents/shared_tools/` were changed
- PLAN doc path
- AAR doc path
- Phase 13 status (COMPLETE or BLOCKED)

---

## VI. Testing Strategy

### A. Unit Test Coverage

**Current Failures** (18 tests):
- `test_a2a_card.py`: 6 tests
- `test_iam_adk_lazy_loading.py`: 12 tests

**Test Categories**:

1. **Import Tests** (verify no import errors):
   - `test_module_imports_without_env_vars`
   - `test_import_time_is_fast`

2. **Agent Creation Tests** (verify agents created correctly):
   - `test_create_agent_with_valid_env`
   - `test_create_app_with_valid_env`

3. **App Entrypoint Tests** (verify module-level app):
   - `test_app_symbol_exists`
   - `test_app_is_not_agent`

4. **AgentCard Tests** (verify A2A card loading):
   - `test_get_agent_card`
   - `test_agent_card_spiffe_id`
   - `test_get_agent_card_dict`

**Success Criteria**: All 18 tests pass after tools refactor.

### B. Validation Strategy

**After each change**:
1. Run full test suite: `pytest tests/unit/ -v`
2. Check for:
   - Reduced failure count
   - No new failures introduced
   - Clear error messages for remaining failures

**Final validation**:
1. Run: `pytest tests/unit/ -v --tb=short`
2. Verify: `155 passed, 0 failed`
3. Check: No import warnings for circular dependencies

---

## VII. Rollback Plan

**If Phase 13 blocked** (cannot achieve 155/155):

1. **Revert tools changes**:
   ```bash
   git checkout -- agents/shared_tools/
   ```

2. **Restore Phase 12 state**:
   - Keep App/Runner patterns (Phase 12 complete)
   - Accept 137/155 test pass rate temporarily
   - Document blocker in AAR 141

3. **Create new issue**:
   - Describe blocker (what prevented 155/155)
   - Request help from ADK team or GCP support
   - Continue with deployment at 137/155 (87% pass rate acceptable for dev)

**Blocker scenarios**:
- ADK 1.18 API doesn't support required tool patterns
- Circular imports cannot be resolved without major refactor
- Tool semantics change breaks existing agent behavior

---

## VIII. Success Criteria

| Criterion | Target | Measurement |
|-----------|--------|-------------|
| Test pass rate | 155/155 (100%) | `pytest tests/unit/ -v` |
| All tools are valid types | 100% | No Pydantic validation errors |
| No circular imports | 0 warnings | No circular import warnings in logs |
| R1 ADK-only compliance | ✅ Maintained | All tools use `google.adk.tools` |
| R5 dual memory compliance | ✅ Maintained | No changes to App/Runner patterns |
| Backwards compatibility | ✅ Maintained | Tool semantics unchanged where possible |
| Documentation complete | ✅ Done | PLAN (140) and AAR (141) created |

---

## IX. Files to Modify

### Primary Changes

1. **`agents/shared_tools/vertex_search.py`**:
   - Replace dict returns with `VertexAiSearchTool` instances
   - Update `get_bob_vertex_search_tool()`
   - Update `get_foreman_vertex_search_tool()`
   - ~30 lines changed

2. **`agents/shared_tools/custom_tools.py`** (If needed):
   - Ensure lazy imports (imports inside functions)
   - Wrap plain functions with `FunctionTool` if needed
   - ~10-20 lines changed (or no changes if already lazy)

### Test Updates

3. **`tests/unit/test_a2a_card.py`**:
   - Update assertions for BaseTool instances (not dicts)
   - ~10 lines changed

4. **`tests/unit/test_iam_adk_lazy_loading.py`**:
   - Update tool validation assertions
   - Remove dict-based checks
   - ~20 lines changed

### Documentation

5. **`000-docs/140-PP-PLAN-tools-validation-and-refactor-for-google-adk-1-18.md`** (This file)
6. **`000-docs/141-AA-REPT-phase-13-tools-validation-and-refactor-for-google-adk-1-18.md`** (To be created)

**Total Files**: ~6 files
**Total Lines**: ~70-100 lines changed

---

## X. Risk Assessment

### Low Risk

- **Tools refactor is isolated**: Only affects `agents/shared_tools/`
- **No App/Runner changes**: Phase 12 patterns remain untouched
- **No infra changes**: Pure Python code refactor
- **Clear rollback**: Revert tools files if blocked

### Medium Risk

- **Test updates required**: Must update assertions to match new tool types
- **Circular imports**: May require careful refactoring to resolve
- **Tool semantics**: Behavior changes possible if ADK tool differs from dict config

### Mitigation

- **Incremental testing**: Test after each file change
- **Small commits**: Easy to bisect if issues arise
- **Clear documentation**: PLAN and AAR explain all changes
- **Rollback plan**: Defined in Section VII

---

## XI. Next Steps After Phase 13

### Immediate (If Phase 13 succeeds)

1. **Merge Phase 12 + 13 changes**:
   - Create PR for `feature/a2a-agentcards-foreman-worker`
   - Include all App migration and tools refactor work
   - Target: Merge to `main`

2. **Tag v0.10.0-preview release**:
   - ADK 1.18+ migration complete
   - Tools validation passing
   - ARV gates green (155/155 tests)

3. **Agent Engine dev deployment** (Phase 6 continuation):
   - Deploy bob and iam-adk to Agent Engine dev
   - Validate inline source deployment
   - Test A2A communication

### Medium-Term (Future phases)

1. **A2A compliance validation** (Phase 6 continuation):
   - Test foreman → worker flows
   - Validate AgentCards
   - Run a2a-inspector and TCK tools

2. **6767 Tools Standard** (New phase):
   - Extract tools pattern as reusable standard
   - Document tool factory pattern
   - Create `6767-XXX-DR-STND-adk-tools-architecture.md`

3. **Production deployment** (Phase 7):
   - Deploy to Agent Engine prod
   - Full smoke testing
   - Production monitoring setup

---

## XII. Appendices

### Appendix A: API Introspection Results

**google-adk 1.18 Available Tools**:
```python
from google.adk.tools import (
    BaseTool,              # Base class for all tools
    VertexAiSearchTool,    # Vertex AI Search (RAG)
    DiscoveryEngineSearchTool,  # Discovery Engine
    FunctionTool,          # Wrap Python functions
    MCPToolset,            # MCP toolset wrapper
    APIHubToolset,         # API Hub toolset
    AgentTool,             # Agent-to-agent delegation
    # ... and many more
)
```

**NOT Available**:
- `BaseToolset` (doesn't exist)
- `VertexAiSearchToolset` (no `google.adk.toolsets` module)

**BaseTool Signature**:
```python
BaseTool.__init__(
    *,
    name: str,
    description: str,
    is_long_running: bool = False,
    custom_metadata: Optional[dict[str, Any]] = None
)
```

**VertexAiSearchTool Signature**:
```python
VertexAiSearchTool.__init__(
    *,
    data_store_id: Optional[str] = None,
    data_store_specs: Optional[list[types.VertexAISearchDataStoreSpec]] = None,
    search_engine_id: Optional[str] = None,
    filter: Optional[str] = None,
    max_results: Optional[int] = None,
    bypass_multi_tools_limit: bool = False
)
```

**FunctionTool Signature**:
```python
FunctionTool.__init__(
    func: Callable[..., Any],
    *,
    require_confirmation: Union[bool, Callable[..., bool]] = False
)
```

**Usage Examples**:
```python
# 1. Use built-in tool
from google.adk.tools import VertexAiSearchTool
tool1 = VertexAiSearchTool(data_store_id="my-datastore")

# 2. Wrap Python function
from google.adk.tools import FunctionTool
def my_function(query: str) -> str:
    return f"Result: {query}"

tool2 = FunctionTool(my_function)

# 3. Use in LlmAgent
from google.adk.agents import LlmAgent
agent = LlmAgent(
    model="gemini-2.0-flash-exp",
    name="my_agent",
    tools=[tool1, tool2],  # ✅ Both are BaseTool instances
)
```

### Appendix B: Circular Import Analysis

**Problem Pattern**:
```
agents/shared_tools/__init__.py (module init)
  └─> calls get_bob_tools()
      └─> calls get_vertex_search_tools()
          └─> imports from agents.bob.tools.vertex_search_tool
              └─> imports from agents.shared_tools  # ❌ Circular!
```

**Solution Pattern**:
```
agents/shared_tools/__init__.py (module init)
  └─> calls get_bob_tools()
      └─> calls get_vertex_search_tools()
          └─> lazy import inside function  # ✅ No circular dependency
```

**Lazy Import Example**:
```python
def get_vertex_search_tools() -> List[Any]:
    # ✅ Import inside function (not at module level)
    try:
        from agents.bob.tools.vertex_search_tool import (
            search_vertex_ai,
            get_vertex_search_status,
        )
        return [search_vertex_ai, get_vertex_search_status]
    except ImportError as e:
        logger.warning(f"Could not import Vertex Search tools: {e}")
        return []
```

---

**End of PLAN**
