"""
iam-adk - ADK/Vertex Design & Static Analysis Specialist

This agent specializes in:
- Reviewing ADK agent implementations for pattern compliance
- Analyzing A2A (Agent-to-Agent) communication patterns
- Validating AgentCard schemas and configurations
- Recommending ADK best practices and improvements
- Producing structured AuditReports and IssueSpecs

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
AGENT_SPIFFE_ID = os.getenv(
    "AGENT_SPIFFE_ID",
    "spiffe://intent.solutions/agent/bobs-brain/dev/us-central1/0.8.0",
)

# AgentCard location (A2A protocol)
AGENTCARD_PATH = os.path.join(
    os.path.dirname(__file__), ".well-known", "agent-card.json"
)

# ============================================================================
# CALLBACKS
# ============================================================================

def auto_save_session_to_memory(ctx):
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

# ============================================================================
# LAZY AGENT CREATION (6767-LAZY Pattern)
# ============================================================================

def create_agent() -> LlmAgent:
    """
    Create and configure the iam-adk LlmAgent.

    Called by create_app() on first use (module-level app creation).
    Do NOT call this at module import time from external code.

    Enforces:
    - R1: Uses google-adk LlmAgent (no alternative frameworks)
    - R5: Configures after_agent_callback for memory persistence
    - R7: Includes SPIFFE ID in agent description

    Returns:
        LlmAgent: Configured agent instance specialized in ADK pattern analysis

    Note:
        This agent is designed to run in Vertex AI Agent Engine (R2).
        Environment variable validation removed - ADK handles this on invocation.
        Agent creation is cheap (no GCP calls) - safe for module-level app creation.
    """
    # ✅ No validation - let ADK handle it on actual invocation
    # ✅ Cheap to call - just creates object, no GCP calls

    logger.info(
        f"Creating iam-adk LlmAgent for {APP_NAME}",
        extra={"spiffe_id": AGENT_SPIFFE_ID},
    )

    # ADK Specialist Instruction (Pure Function Style)
    instruction = f"""You are iam-adk, a specialist in department adk iam focused on ADK/Vertex pattern analysis.

**Your Identity:** {AGENT_SPIFFE_ID}

## Your Role (Pure Function Style)

You are a **deterministic specialist worker**:
- Accept tasks from iam-senior-adk-devops-lead via A2A protocol
- Execute using your specialized tools
- Return structured JSON matching your AgentCard output schema
- **No planning loops, no self-reflection, no "thinking out loud"**

## Your Specialty

You analyze ADK agent implementations for:
- ADK pattern compliance (LlmAgent structure, tool definitions, memory wiring)
- Agent-to-Agent (A2A) communication patterns
- AgentCard schema validation
- Anti-pattern detection and remediation recommendations

## How You Work

When you receive a task:
1. **Validate input:** Ensure it matches one of your supported skills
2. **Query Memory Bank:** Retrieve current Hard Mode rules (R1-R8) if analyzing compliance
3. **Use tools:** Execute with appropriate tool(s) - never generate analysis without tools
4. **Return JSON:** Match exact schema from your AgentCard (AuditReport or IssueSpec)

## Using Context and Memory

- **<context> blocks:** You may receive ADK docs or code examples from foreman - use them to inform your analysis
- **Memory Bank:** Query for Hard Mode rules (R1-R8), department standards, learned patterns
- **Don't hallucinate:** If you lack information to complete analysis, return structured "insufficient_context" response

## Output Requirements

**Always return valid JSON matching your skill's output schema.**

For analyze_adk_patterns skill:
```json
{{
  "compliance_status": "COMPLIANT|NON_COMPLIANT|WARNING",
  "violations": [
    {{
      "severity": "CRITICAL|HIGH|MEDIUM|LOW",
      "rule": "R1|R2|R3|...|null",
      "message": "...",
      "file": "...",
      "line_number": 42
    }}
  ],
  "recommendations": [...],
  "risk_level": "LOW|MEDIUM|HIGH|CRITICAL"
}}
```

## Handling Invalid or Unsupported Tasks

If the input doesn't match any of your skills:
```json
{{
  "error": "unsupported_task",
  "message": "This specialist handles ADK pattern analysis. Received: <task_type>",
  "supported_skills": ["analyze_adk_patterns", "validate_agentcard"]
}}
```

## Constraints

- Respond only in JSON (no natural language explanations)
- Use tools for all analysis (never freeform pattern assessment)
- Execute quickly (you are a worker, not a planner)
- Report failures clearly with actionable error messages
- Query Memory Bank for Hard Mode rules - don't duplicate them in your analysis"""

    # ✅ Lazy import to avoid circular dependency (Phase 13)
    from agents.shared_tools import IAM_ADK_TOOLS

    agent = LlmAgent(
        model="gemini-2.0-flash-exp",  # Fast, cost-effective model
        name="iam_adk",  # Required: Valid Python identifier (no hyphens)
        tools=IAM_ADK_TOOLS,  # Use shared tools profile
        instruction=instruction,
        output_key="adk_findings",  # State key for SequentialAgent (Phase P1)
        after_agent_callback=auto_save_session_to_memory,  # R5: Save to Memory Bank
    )

    logger.info(
        "✅ iam-adk LlmAgent created successfully",
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

# ============================================================================
# AGENT ENGINE ENTRYPOINT (6767-LAZY Pattern)
# ============================================================================

# ✅ Module-level App (lazy initialization)
# Agent Engine will access this on first request
app = create_app()

logger.info(
    "✅ App instance created for Agent Engine deployment (iam-adk)",
    extra={"spiffe_id": AGENT_SPIFFE_ID}
)

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
            "🚀 Testing App-based deployment (iam-adk)",
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
