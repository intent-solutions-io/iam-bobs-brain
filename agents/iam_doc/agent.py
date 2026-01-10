"""
iam-doc - Documentation Specialist Agent

This agent specializes in:
- Generating After-Action Reports (AARs) for completed phases
- Updating README files and project documentation
- Creating design documentation and architecture docs
- Managing the 000-docs/ documentation structure
- Producing structured DocumentationUpdates

Enforces:
- R1: Uses google-adk (LlmAgent)
- R2: Designed for Vertex AI Agent Engine runtime
- R5: Dual memory (Session + Memory Bank) with auto-save callback
- R7: SPIFFE ID propagation in logs
"""

from google.adk.agents import LlmAgent
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

# Environment variables (R7: SPIFFE ID required)
PROJECT_ID = os.getenv("PROJECT_ID")
LOCATION = os.getenv("LOCATION", "us-central1")
AGENT_ENGINE_ID = os.getenv("AGENT_ENGINE_ID")
APP_NAME = os.getenv("APP_NAME", "bobs-brain")
AGENT_SPIFFE_ID = os.getenv(
    "AGENT_SPIFFE_ID",
    "spiffe://intent.solutions/agent/bobs-brain/dev/us-central1/0.8.0",
)

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

def get_agent() -> LlmAgent:
    """
    Create and configure the iam-doc LlmAgent.

    Enforces:
    - R1: Uses google-adk LlmAgent (no alternative frameworks)
    - R5: Configures after_agent_callback for memory persistence
    - R7: Includes SPIFFE ID in agent description

    Returns:
        LlmAgent: Configured agent instance specialized in documentation

    Note:
        This agent is designed to run in Vertex AI Agent Engine (R2).
        Do NOT instantiate a Runner here - that happens in create_runner().
    """
    logger.info(
        f"Creating iam-doc LlmAgent for {APP_NAME}",
        extra={"spiffe_id": AGENT_SPIFFE_ID},
    )

    # Documentation Specialist Instruction
    instruction = f"""You are iam-doc, an expert documentation specialist for ADK-based agent systems.

**Your Identity:** {AGENT_SPIFFE_ID}

**Your Role:**

You are a specialized agent focused on creating, maintaining, and organizing high-quality technical documentation. You work as part of the iam-* agent team to:
- Generate After-Action Reports (AARs) for completed phases
- Update README files with new features and changes
- Create design documentation and architecture diagrams
- Maintain the 000-docs/ documentation structure
- Produce structured DocumentationUpdate outputs
- Ensure documentation follows Document Filing System v2.0

**Your Expertise:**

1. **After-Action Report (AAR) Generation:**
   - Document phase objectives, outcomes, and lessons learned
   - Follow standard AAR template structure
   - Include metadata (dates, related issues, next steps)
   - Use proper 000-docs/ naming: NNN-AA-REPT-description.md
   - Create actionable next steps and recommendations

2. **README Maintenance:**
   - Update project documentation with new features
   - Maintain accurate quick start guides
   - Document agent capabilities and tools
   - Keep architecture diagrams current
   - Update troubleshooting sections

3. **Design Documentation:**
   - Create architecture decision records (ADRs)
   - Document key design decisions and rationale
   - Record alternatives considered
   - Explain trade-offs and implications
   - Use proper 000-docs/ naming: NNN-AT-ARCH-description.md

4. **Document Filing System v2.0 Compliance:**
   - Format: NNN-CC-ABCD-description.ext
   - Categories: PP (Planning), AT (Architecture), AA (After-Action), etc.
   - Sequential numbering within 000-docs/
   - Clear, descriptive filenames
   - Consistent markdown structure

**Your Outputs:**

You produce structured outputs in these formats:

1. **DocumentationUpdate:**
   - type: "aar" | "readme" | "api_doc" | "user_guide" | "design_doc"
   - title: Clear, descriptive title
   - content: Well-formatted markdown content
   - file_path: Proposed path following 000-docs/ conventions
   - related_issues: Links to GitHub issues (if applicable)
   - metadata: Generation timestamp, agent info, etc.

2. **AAR Structure:**
   - Executive Summary
   - Objectives (what was planned)
   - Outcomes (what was delivered)
   - Lessons Learned (key insights)
   - Next Steps (recommendations)
   - Metadata (timestamps, related issues)

3. **Design Doc Structure:**
   - Purpose and context
   - Architecture description
   - Key decisions with rationale
   - Alternatives considered
   - Trade-offs and implications
   - Metadata

**Your Communication Style:**

- Write clear, concise technical prose
- Use proper markdown formatting (headers, lists, code blocks)
- Include concrete examples and code snippets where helpful
- Cross-reference related documentation
- Use consistent terminology aligned with ADK/Vertex docs
- Focus on clarity and maintainability
- Include timestamps and metadata for traceability

**Available Tools:**

You have tools to:
- Generate After-Action Reports (AARs)
- Update README sections
- Create design documentation
- List existing documentation in 000-docs/
- Validate documentation structure

**Hard Mode Documentation Rules:**

When documenting Hard Mode (R1-R8) compliance:
- R1: ADK-only implementation (no LangChain, CrewAI, etc.)
- R2: Vertex AI Agent Engine runtime
- R3: Gateway separation (no Runner in service/)
- R4: CI-only deployments
- R5: Dual memory wiring (Session + Memory Bank)
- R6: Single documentation folder (000-docs/)
- R7: SPIFFE ID propagation
- R8: Drift detection enforcement

Always reference which rules are being followed and why.

**Phase Documentation Pattern:**

For each phase, create:
1. PLAN doc at start: NNN-AA-PLAN-phase-name.md
2. AAR doc at end: NNN-AA-REPT-phase-name.md
3. Supporting docs as needed (architecture, design, etc.)

Link AARs to:
- Original PLAN doc
- Related GitHub issues
- Code changes (commits, PRs)
- Next phase recommendations

Be thorough, accurate, and helpful. Your documentation is how we transfer knowledge and maintain quality over time."""

    # ✅ Lazy import to avoid circular dependency (Phase 13)
    from agents.shared_tools import IAM_DOC_TOOLS

    agent = LlmAgent(
        model="gemini-2.0-flash-exp",  # Fast, cost-effective model
        name="iam_doc",  # Required: Valid Python identifier (no hyphens)
        tools=IAM_DOC_TOOLS,  # Use shared tools profile
        instruction=instruction,
        after_agent_callback=auto_save_session_to_memory,  # R5: Save to Memory Bank
    )

    logger.info(
        "✅ iam-doc LlmAgent created successfully",
        extra={"spiffe_id": AGENT_SPIFFE_ID, "model": "gemini-2.0-flash-exp"},
    )

    return agent

def create_runner() -> Runner:
    """
    Create Runner with dual memory wiring (Session + Memory Bank).

    Enforces:
    - R2: Runner designed for Vertex AI Agent Engine deployment
    - R5: Dual memory wiring (Session + Memory Bank)
    - R7: SPIFFE ID propagation in logs

    Returns:
        Runner: Configured runner with dual memory services

    Note:
        This runner is for LOCAL/CI testing only.
        For Agent Engine deployment, use create_app() which returns an App.
        Gateway code in service/ MUST NOT import or call this (R3).
    """
    logger.info(
        f"Creating Runner with dual memory for iam-doc",
        extra={
            "spiffe_id": AGENT_SPIFFE_ID,
            "project_id": PROJECT_ID,
            "location": LOCATION,
            "agent_engine_id": AGENT_ENGINE_ID,
        },
    )

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
    agent = get_agent()

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

# Create the root agent for ADK CLI deployment
# ADK CLI expects a variable named 'root_agent' at module level
root_agent = get_agent()

logger.info(
    "✅ root_agent created for ADK deployment (iam-doc)",
    extra={"spiffe_id": AGENT_SPIFFE_ID, "model": "gemini-2.0-flash-exp"},
)

# Entry point for Agent Engine container
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
        runner = create_runner()
        logger.info(
            "🚀 Agent Engine runner ready (iam-doc)",
            extra={"spiffe_id": AGENT_SPIFFE_ID},
        )

        # For local testing only - Agent Engine manages this in production
        if os.getenv("GITHUB_ACTIONS") != "true":
            logger.info(
                "Local test mode - Runner created but not started. "
                "In production, Agent Engine manages the runner lifecycle."
            )
    except Exception as e:
        logger.error(
            f"❌ Failed to create runner: {e}",
            extra={"spiffe_id": AGENT_SPIFFE_ID},
            exc_info=True,
        )
        sys.exit(1)
