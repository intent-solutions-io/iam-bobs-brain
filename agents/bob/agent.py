"""
Bob's Brain - Core Agent Implementation

This module defines the LlmAgent with dual memory wiring:
- VertexAiSessionService (short-term conversation cache)
- VertexAiMemoryBankService (long-term persistent memory)

Enforces:
- R1: Uses google-adk (LlmAgent)
- R2: Designed for Vertex AI Agent Engine runtime
- R5: Dual memory (Session + Memory Bank) with auto-save callback
- R7: SPIFFE ID propagation in logs

LAZY-LOADING PATTERN (6767-LAZY):
- Uses create_agent() for lazy agent instantiation
- Uses create_app() to wrap in App for Agent Engine
- Exposes module-level `app` (not agent!)
- No import-time validation or heavy work
"""

from google.adk.agents import LlmAgent
from google.adk.apps import App
from google.adk import Runner
from google.adk.sessions import VertexAiSessionService
from google.adk.memory import VertexAiMemoryBankService
import os
import logging
from typing import Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# ============================================================================
# CONFIGURATION (Cheap reads, no validation yet)
# ============================================================================

# Environment variables (R7: SPIFFE ID required)
# Note: os.getenv() is cheap - no validation at import time
PROJECT_ID = os.getenv("PROJECT_ID")
LOCATION = os.getenv("LOCATION", "us-central1")
AGENT_ENGINE_ID = os.getenv("AGENT_ENGINE_ID")
APP_NAME = os.getenv("APP_NAME", "bobs-brain")
AGENT_SPIFFE_ID = os.getenv("AGENT_SPIFFE_ID")


def auto_save_session_to_memory(callback_context=None, **kwargs):
    """
    After-agent callback to persist session to Memory Bank.

    This callback is invoked after each agent turn to save the conversation
    session to the Memory Bank for long-term persistence.

    Enforces R5: Dual memory wiring requirement.

    Args:
        ctx: Agent context with invocation_context containing memory_service and session

    Note:
        - Never blocks agent execution (errors are logged but not raised)
        - Includes SPIFFE ID in logs (R7)
    """
    try:
        # Handle both old (ctx) and new (callback_context) API
        ctx = callback_context or kwargs.get('ctx')
        if ctx is None:
            logger.debug("No callback context provided, skipping memory save")
            return

        if hasattr(ctx, "invocation_context"):
            invocation_ctx = ctx.invocation_context
        elif hasattr(ctx, "_invocation_context"):
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


# ============================================================================
# LAZY AGENT CREATION (6767-LAZY Pattern)
# ============================================================================

def create_agent() -> LlmAgent:
    """
    Create and configure the LlmAgent.

    Called by create_app() on first use (module-level app creation).
    Do NOT call this at module import time from external code.

    Enforces:
    - R1: Uses google-adk LlmAgent (no alternative frameworks)
    - R5: Configures after_agent_callback for memory persistence
    - R7: Includes SPIFFE ID in agent description

    Returns:
        LlmAgent: Configured agent instance specialized in ADK expertise

    Note:
        This agent is designed to run in Vertex AI Agent Engine (R2).
        Environment variable validation removed - ADK handles this on invocation.
        Agent creation is cheap (no GCP calls) - safe for module-level app creation.
    """
    # ✅ No validation - let ADK handle it on actual invocation
    # ✅ Cheap to call - just creates object, no GCP calls

    logger.info(
        f"Creating LlmAgent for {APP_NAME}", extra={"spiffe_id": AGENT_SPIFFE_ID}
    )

    # Enhanced ADK Expert Instruction (Phase 1: ADK grounding)
    base_instruction = f"""You are Bob, an expert Google Agent Development Kit (ADK) specialist.

**Your Identity:** {AGENT_SPIFFE_ID}

**Your Expertise:**

You are THE authoritative source for Google ADK knowledge. You help developers:
- Design and build AI agents using Google ADK
- Understand ADK architecture patterns and best practices
- Implement tools, multi-agent systems, and workflows
- Deploy agents to Vertex AI Agent Engine
- Debug agent issues and optimize performance
- Integrate with Google Cloud services (BigQuery, Vertex AI Search, Memory Bank)

**Core ADK Concepts You Master:**

1. **Agent Types:**
   - LlmAgent: LLM-powered agents with tools and reasoning (model, name, tools, instruction)
   - SequentialAgent: Execute sub-agents in strict order with shared state
   - ParallelAgent: Execute sub-agents concurrently for independent tasks
   - LoopAgent: Iterative execution with max_iterations for refinement
   - BaseAgent: Base class for custom agent implementations

2. **Tool Integration:**
   - FunctionTool: Wrap Python functions with type hints and docstrings
   - AgentTool: Delegate tasks to other agents
   - Pre-built toolsets: GoogleApiToolset, BigQueryToolset, VertexAiSearchTool, MCPToolset
   - Tool best practices: clear naming, parameter validation, comprehensive docstrings

3. **Multi-Agent Coordination:**
   - sub_agents list: Hierarchical agent composition
   - transfer_to_agent(name): Transfer control to named agent
   - AgentTool: Tool-based delegation pattern
   - Workflow agents: SequentialAgent, ParallelAgent, LoopAgent for orchestration

4. **Deployment & Runtime:**
   - Vertex AI Agent Engine: Fully managed agent runtime (recommended)
   - adk deploy agent_engine: Deploy command with flags
   - Runner pattern: Runner(agent, session_service, memory_service)
   - InMemoryRunner: For local testing with .run_debug()
   - Cloud Trace: Automatic telemetry with --trace_to_cloud flag

5. **Session & Memory Management:**
   - VertexAiSessionService: Short-term conversation cache (required for production)
   - VertexAiMemoryBankService: Long-term semantic memory (persistent knowledge)
   - Dual memory pattern: Session + Memory Bank with auto-save callback
   - State scoping: 'user:' (persistent), 'app:' (application), 'temp:' (invocation-only)

6. **Key ADK Patterns:**
   - Agent creation: LlmAgent(model='gemini-2.5-flash', tools=[...], instruction='...')
   - Tool creation: def func(param: type) -> type: with Args/Returns docstring
   - Agent composition: SequentialAgent(sub_agents=[agent1, agent2, agent3])
   - State management: output_key='result' and instruction='Use {{result}}'
   - Callbacks: after_agent_callback for session persistence and custom logic

**Your Communication Style:**

- Provide specific, actionable code examples using official ADK patterns
- Reference exact import statements: from google.adk.agents import LlmAgent
- Explain both what and why for complex patterns
- Cite best practices from official Google ADK documentation
- Help debug by analyzing agent structure, tools, services, and configurations
- Guide deployment from local testing (InMemoryRunner) to production (Agent Engine)

**Available Documentation Tools:**

You have TWO ways to access ADK documentation:

1. **Semantic Search (search_vertex_ai)** - AI-powered understanding
   - Use for natural language questions
   - Understands meaning and context
   - Best for: "How do I...", "What's the difference...", concept questions
   - Example: search_vertex_ai("How do I create a multi-agent workflow?")

2. **Keyword Search (search_adk_docs)** - Fast exact matching
   - Use for specific terms, class names, function names
   - Best for: API lookups, exact references, class definitions
   - Example: search_adk_docs("VertexAiSessionService")

3. **API Reference (get_adk_api_reference)** - Detailed class docs
   - Use for complete API documentation of specific classes
   - Example: get_adk_api_reference("LlmAgent")

Documentation covers:
- Complete Python API reference (all classes, methods, parameters)
- ADK CLI reference (adk create, adk run, adk deploy, adk web)
- Deployment guides for Vertex AI Agent Engine
- Multi-agent coordination patterns
- Tool integration examples
- Session and memory management
- Safety and security best practices

When users ask about ADK, provide expert guidance with accurate code examples, deployment commands, and architectural recommendations based on official Google patterns.

Be concise, accurate, and helpful. Focus on teaching developers to build production-ready agents."""

    # ✅ Lazy import to avoid circular dependency (Phase 13)
    from agents.shared_tools import BOB_TOOLS

    agent = LlmAgent(
        model="gemini-2.0-flash-exp",  # Fast, cost-effective model
        name="bobs_brain",  # Required: Valid Python identifier (no hyphens)
        tools=BOB_TOOLS,  # Use shared tool profile
        instruction=base_instruction,
        after_agent_callback=auto_save_session_to_memory,  # R5: Save to Memory Bank
    )

    logger.info(
        "✅ LlmAgent created successfully",
        extra={"spiffe_id": AGENT_SPIFFE_ID, "model": "gemini-2.0-flash-exp"},
    )

    return agent


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
        "Creating App container for Bob",
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
        "✅ App created successfully for Bob",
        extra={
            "spiffe_id": AGENT_SPIFFE_ID,
            "app_name": APP_NAME,
        }
    )

    return app_instance


# ============================================================================
# BACKWARDS COMPATIBILITY (Optional)
# ============================================================================

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
        Gateway code in service/ MUST NOT import or call this (R3).
    """
    logger.warning(
        "⚠️  create_runner() is deprecated for Agent Engine deployment. "
        "Use create_app() for Agent Engine. create_runner() is for local/CI testing only.",
        extra={"spiffe_id": AGENT_SPIFFE_ID}
    )

    logger.info(
        f"Creating Runner with dual memory for {APP_NAME}",
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

    # R5: Wire dual memory to Runner
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


# ============================================================================
# AGENT ENGINE ENTRYPOINT (6767-LAZY Pattern)
# ============================================================================

# ✅ Module-level App (lazy initialization)
# Agent Engine will access this on first request
app = create_app()

logger.info(
    "✅ App instance created for Agent Engine deployment (Bob)",
    extra={"spiffe_id": AGENT_SPIFFE_ID}
)


# ============================================================================
# MAIN (For local testing only)
# ============================================================================

if __name__ == "__main__":
    """
    This entry point is used when the container is deployed to
    Vertex AI Agent Engine (R2).

    Do NOT run this locally for production (R4: CI-only deployments).
    Local execution is only for CI smoke tests.
    """
    import sys

    # CI-only guard (R4)
    if os.getenv("GITHUB_ACTIONS") != "true":
        logger.warning(
            "⚠️  Running agent locally. Production deployments must use "
            "Vertex AI Agent Engine via GitHub Actions (R4).",
            extra={"spiffe_id": AGENT_SPIFFE_ID},
        )

    try:
        # Use new App pattern
        logger.info(
            "🚀 Testing App-based deployment (Bob)",
            extra={"spiffe_id": AGENT_SPIFFE_ID},
        )

        # App is already created at module level
        logger.info(
            "✅ App instance ready for Agent Engine",
            extra={"spiffe_id": AGENT_SPIFFE_ID}
        )

        # For local testing only - Agent Engine manages this in production
        if os.getenv("GITHUB_ACTIONS") != "true":
            logger.info(
                "Local test mode - App created successfully. "
                "In production, Agent Engine manages the app lifecycle."
            )
    except Exception as e:
        logger.error(
            f"❌ Failed to create app: {e}",
            extra={"spiffe_id": AGENT_SPIFFE_ID},
            exc_info=True,
        )
        sys.exit(1)
