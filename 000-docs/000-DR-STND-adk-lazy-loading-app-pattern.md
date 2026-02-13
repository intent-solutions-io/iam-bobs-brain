# ADK Lazy-Loading App Pattern for Department ADK IAM

**Document ID**: `6774-DR-STND-adk-lazy-loading-app-pattern`
**Date**: 2025-11-21
**Status**: Standard - Required for all new agents
**Applies To**: All department adk iam agents (bob, foreman, iam-* workers)

---

## Purpose

This document defines the **lazy-loading App pattern** required for all ADK agents in department adk iam. This pattern ensures agents are compatible with **Vertex AI Agent Engine**, minimize cold start times, and follow ADK v1.19+ best practices.

---

## Problem Statement

### Current Anti-Pattern (Global Initialization)

Many agents currently use this anti-pattern:

```python
# ❌ BAD: Heavy work at import time
from google.adk.agents import LlmAgent

# Environment validation at import
if not PROJECT_ID:
    raise ValueError("PROJECT_ID required")  # Fails on import!

# Agent created at module level
root_agent = get_agent()  # ❌ Created immediately on import
```

**Problems**:
1. **Cold start overhead**: Agent is created even if never used
2. **Import-time failures**: Missing env vars crash imports
3. **Testing difficulty**: Cannot import module without full env setup
4. **Billing waste**: Agent Engine charges for unused ready-time
5. **Non-lazy RAG/Memory**: Heavy resources initialized unnecessarily

---

## Solution: Lazy-Loading App Pattern

### Target Pattern (ADK v1.19+)

```python
"""Agent module following lazy-loading App pattern."""

from google.adk.agents import LlmAgent
from google.adk import App
import os
import logging

logger = logging.getLogger(__name__)

# ✅ GOOD: Config reading (cheap, no validation yet)
PROJECT_ID = os.getenv("PROJECT_ID")
LOCATION = os.getenv("LOCATION", "us-central1")
AGENT_SPIFFE_ID = os.getenv("AGENT_SPIFFE_ID")

# Optional: Path to AgentCard (for A2A)
AGENTCARD_PATH = os.path.join(
    os.path.dirname(__file__), ".well-known", "agent-card.json"
)


def create_agent() -> LlmAgent:
    """
    Create the LlmAgent instance with all configuration.

    This function is called lazily by create_app() on first use.
    Do NOT call this at module import time.

    Returns:
        LlmAgent: Configured agent with tools and memory

    Raises:
        ValueError: If required environment variables are missing
    """
    # ✅ Validation happens here (lazy, not at import)
    if not PROJECT_ID:
        raise ValueError("PROJECT_ID environment variable required")
    if not AGENT_SPIFFE_ID:
        raise ValueError("AGENT_SPIFFE_ID environment variable required")

    logger.info(
        f"Creating agent",
        extra={"spiffe_id": AGENT_SPIFFE_ID}
    )

    # Your agent configuration
    agent = LlmAgent(
        model="gemini-2.0-flash-exp",
        name="agent_name",
        tools=[...],  # Load tools here
        instruction="...",  # Your prompt
        after_agent_callback=auto_save_session_to_memory,
    )

    logger.info(
        "✅ Agent created successfully",
        extra={"spiffe_id": AGENT_SPIFFE_ID}
    )

    return agent


def create_app() -> App:
    """
    Create the App container for this agent.

    The App wraps the agent and provides lazy initialization.
    This function can be called multiple times safely (idempotent).

    Returns:
        App: Configured app instance for Agent Engine
    """
    logger.info("Creating App container")

    # App handles lazy agent creation
    app_instance = App(
        agent=create_agent,  # Pass function, not instance!
        # Optional: Configure app-level settings
        # session_service=...,
        # memory_service=...,
    )

    logger.info("✅ App created successfully")
    return app_instance


# ✅ GOOD: Module-level app for Agent Engine
# This is evaluated lazily when Agent Engine calls it
app = create_app()


# Optional: For ADK CLI compatibility (if needed)
# This creates root_agent on-demand when accessed
def _get_root_agent():
    """Lazy accessor for root_agent (ADK CLI compatibility)."""
    return create_agent()


# Uncomment if ADK CLI support needed:
# root_agent = property(_get_root_agent)
```

---

## Key Principles

### 1. No Heavy Work at Import Time

**❌ BAD** (import-time work):
- Creating agent instances
- Validating environment variables (raising exceptions)
- Initializing network clients (Vertex Search, Memory Bank)
- Loading large data files
- Making API calls

**✅ GOOD** (import-time is cheap):
- Reading environment variables (`os.getenv()` is OK)
- Defining functions and classes
- Setting up logging configuration
- Defining constants and paths

### 2. Lazy Agent Creation

**Agent creation MUST be inside a function** that is called later:
- `create_agent()` - Creates the LlmAgent
- `create_app()` - Wraps agent in App container
- `app` - Module-level App instance (not agent!)

**Why App instead of raw agent?**
- Agent Engine expects `app` entrypoint
- App handles lazy initialization automatically
- App provides better lifecycle management
- App enables future observability hooks

### 3. Environment Validation Timing

**❌ BAD** (fails on import):
```python
# At module level
if not PROJECT_ID:
    raise ValueError("Missing PROJECT_ID")  # Crashes import!
```

**✅ GOOD** (fails on use):
```python
# Inside create_agent()
def create_agent():
    if not PROJECT_ID:
        raise ValueError("Missing PROJECT_ID")  # Only fails when agent is used
```

**Why this is better**:
- Module can be imported for testing/inspection
- Validation happens when agent is actually needed
- Clear error messages at invocation time

### 4. Idempotent App Creation

`create_app()` should be safe to call multiple times:
- Use caching if needed (e.g., `@functools.lru_cache`)
- App should not duplicate expensive resources
- Clear logging for debugging

---

## Integration with Existing Patterns

### AgentCards (A2A Protocol)

AgentCards remain at fixed paths:
```python
AGENTCARD_PATH = os.path.join(
    os.path.dirname(__file__), ".well-known", "agent-card.json"
)
```

**No change required** - AgentCard is static, agent creation is lazy.

### Dual Memory (R5 Hard Mode Rule)

Memory services still created in `create_runner()` or passed to App:
```python
def create_app() -> App:
    # Memory services created here (lazy)
    session_service = VertexAiSessionService(...)
    memory_service = VertexAiMemoryBankService(...)

    return App(
        agent=create_agent,
        session_service=session_service,
        memory_service=memory_service,
    )
```

**Why this is OK**: Services created inside function, not at import.

### Tools and Prompts (Contract-First)

Tools and prompts follow existing standards:
- Tools defined in `agents/shared_tools/`
- Prompts follow 000-DR-STND-prompt-design-and-agentcard-standard.md
- No schema duplication in prompts

**No change** - Lazy loading is orthogonal to contract design.

---

## Benefits

### 1. Faster Cold Starts

**Before (global init)**:
- Import time: ~2-5 seconds (agent creation + validation)
- First invocation: Immediate (agent already exists)

**After (lazy init)**:
- Import time: ~50-200ms (just function definitions)
- First invocation: ~2-5 seconds (agent created on demand)

**Agent Engine benefit**: Only pay for agents that are actually invoked.

### 2. Better Testing

**Before**:
```python
# ❌ Cannot import without full env
import agents.bob.agent  # Crashes if PROJECT_ID missing!
```

**After**:
```python
# ✅ Can import for testing/inspection
import agents.bob.agent  # Works even without env vars
agent = agents.bob.agent.create_agent()  # Fails here (controllable)
```

### 3. Agent Engine Compatibility

Agent Engine expects `app` entrypoint:
- Lazy initialization on first request
- Lifecycle managed by Agent Engine
- Billing based on actual usage

### 4. Observability Hooks

App pattern enables future integrations:
- AgentOps for tracing
- OpenTelemetry for metrics
- Memory Bank preloading
- Custom middleware

---

## Migration Checklist

For each agent being migrated:

- [ ] **Remove module-level `root_agent = get_agent()`**
  - Replace with `app = create_app()`

- [ ] **Create `create_agent()` function**
  - Move env validation inside this function
  - Move agent instantiation inside this function
  - Return configured LlmAgent

- [ ] **Create `create_app()` function**
  - Wrap `create_agent` in App
  - Pass function reference, not instance
  - Optionally add memory services

- [ ] **Update environment validation**
  - Move from module level to inside `create_agent()`
  - Keep `os.getenv()` at module level (cheap)

- [ ] **Test lazy loading**
  - Verify module can be imported without full env
  - Verify `create_agent()` fails with clear error if env missing
  - Verify `app` works in Agent Engine context

- [ ] **Update documentation**
  - Add comment explaining lazy pattern
  - Reference this standard doc

---

## Anti-Patterns to Avoid

### ❌ Anti-Pattern 1: Agent in App Constructor

```python
# ❌ BAD: Agent created immediately
def create_app():
    agent = create_agent()  # ❌ Called immediately!
    return App(agent=agent)
```

**Fix**: Pass function reference:
```python
# ✅ GOOD: Agent created lazily by App
def create_app():
    return App(agent=create_agent)  # ✅ Function reference
```

### ❌ Anti-Pattern 2: Global Heavy Resources

```python
# ❌ BAD: Client created at import
vertex_search_client = VertexSearchClient(...)  # ❌ Import-time work!

def create_agent():
    # Uses global client
    tools = [create_search_tool(vertex_search_client)]
```

**Fix**: Create inside function:
```python
# ✅ GOOD: Client created lazily
def create_agent():
    vertex_search_client = VertexSearchClient(...)  # ✅ Lazy
    tools = [create_search_tool(vertex_search_client)]
```

### ❌ Anti-Pattern 3: Import-Time Validation

```python
# ❌ BAD: Validation at import
if not PROJECT_ID:
    raise ValueError("Missing PROJECT_ID")  # ❌ Import fails!
```

**Fix**: Validate in function:
```python
# ✅ GOOD: Validation when used
def create_agent():
    if not PROJECT_ID:
        raise ValueError("Missing PROJECT_ID")  # ✅ Fails on use
```

---

## Testing Strategy

### Unit Tests

```python
def test_lazy_loading():
    """Verify agent is not created at import time."""
    # Import should not create agent
    import agents.bob.agent as bob

    # App should exist but agent not created yet
    assert hasattr(bob, 'app')

    # Agent created on first call
    agent = bob.create_agent()
    assert agent is not None

def test_env_validation():
    """Verify clear error when env vars missing."""
    import agents.bob.agent as bob

    # Should raise with clear message
    with pytest.raises(ValueError, match="PROJECT_ID"):
        bob.create_agent()
```

### Smoke Tests

```bash
# Test all agents can be imported
python3 -c "import agents.bob.agent; print('✅ Bob imports OK')"
python3 -c "import agents.iam_adk.agent; print('✅ iam-adk imports OK')"

# Test agent creation (with env)
export PROJECT_ID=test AGENT_SPIFFE_ID=spiffe://test
python3 -c "from agents.bob.agent import create_agent; create_agent()"
```

---

## Deployment Considerations

### Agent Engine

Agent Engine will:
1. Import your module
2. Access `app` symbol
3. Initialize on first request (lazy)
4. Reuse app across subsequent requests

**No special configuration needed** - Standard ADK deployment:
```bash
adk deploy agent_engine \
  --agent-module=agents.bob.agent \
  --agent-name=bobs-brain
```

### Local Development

For local testing with ADK CLI:
```bash
# If root_agent property is defined
adk run agents.bob.agent

# Otherwise, use app directly
adk run agents.bob.agent --app
```

---

## Future Enhancements

### 1. Observability Integration

Once all agents use App pattern:
- Add AgentOps middleware for tracing
- Add OpenTelemetry for metrics
- Add custom logging hooks

### 2. Memory Bank Preloading

App initialization can preload common facts:
```python
def create_app():
    memory_service = VertexAiMemoryBankService(...)
    # Preload Hard Mode rules (R1-R8) on init
    memory_service.preload_facts("hard_mode_rules")
    return App(...)
```

### 3. Configuration Validation

Add app-level config validator:
```python
def create_app():
    validate_config()  # Check all required env vars
    return App(...)
```

---

## References

- **ADK Documentation**: https://cloud.google.com/vertex-ai/docs/agent-development-kit
- **Agent Engine Deployment**: https://cloud.google.com/vertex-ai/docs/agent-engine
- **Gemini Strategic Engineering Guide**: (internal Google reference)
- **Contract-First Design**: 000-DR-STND-prompt-design-and-agentcard-standard.md
- **AgentCards**: 000-DR-STND-agentcards-and-a2a-contracts.md

---

## Summary

**Golden Rule**: **No heavy work at import time**.

All agents in department adk iam MUST:
1. ✅ Use `create_agent()` function for agent instantiation
2. ✅ Use `create_app()` function to wrap in App
3. ✅ Expose module-level `app` for Agent Engine
4. ✅ Move env validation inside functions, not at import
5. ✅ Keep imports cheap (definitions only)

**Template**: Use this pattern for all new agents and migrate existing agents during updates.

---

**Document Prepared By**: Build Captain (Claude Code)
**Review Status**: Standard - Required for all agents
**Next Action**: Begin LAZY-2 (migrate template agent)

---

**Change Log**:
- 2025-11-21: Initial version (LAZY-1)
