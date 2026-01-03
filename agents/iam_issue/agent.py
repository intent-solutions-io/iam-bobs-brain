"""
iam-issue - Issue Author & Formatter Specialist

This agent specializes in:
- Converting findings and audit reports into GitHub issues
- Formatting issues with proper markdown and structure
- Validating issue specs for completeness
- Generating appropriate labels and metadata
- Creating high-quality issue bodies for GitHub

Enforces:
- R1: Uses google-adk (LlmAgent)
- R2: Vertex AI Agent Engine runtime
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

def get_agent() -> LlmAgent:
    """
    Create and configure the iam-issue LlmAgent.

    Enforces:
    - R1: Uses google-adk LlmAgent (no alternative frameworks)
    - R5: Configures after_agent_callback for memory persistence
    - R7: Includes SPIFFE ID in agent description

    Returns:
        LlmAgent: Configured agent instance specialized in issue formatting

    Note:
        This agent is designed to run in Vertex AI Agent Engine (R2).
        Do NOT instantiate a Runner here - that happens in create_runner().
    """
    logger.info(
        f"Creating iam-issue LlmAgent for {APP_NAME}",
        extra={"spiffe_id": AGENT_SPIFFE_ID},
    )

    # Issue Author Instruction
    instruction = f"""You are iam-issue, an expert Issue Author and GitHub issue formatter.

**Your Identity:** {AGENT_SPIFFE_ID}

**Your Role:**

You are a specialized agent focused on creating high-quality, well-structured GitHub issues
from raw findings, audit reports, and other structured inputs. You work as part of the iam-*
agent team to:
- Transform audit findings into properly formatted GitHub issues
- Convert IssueSpec objects into GitHub-compatible markdown
- Validate issue completeness and correctness
- Generate appropriate labels and metadata
- Ensure consistency in issue formatting and structure

**Your Expertise:**

1. **Issue Formatting:**
   - Converting structured IssueSpec objects to GitHub markdown
   - Creating clear, concise issue titles and descriptions
   - Formatting reproduction steps for bugs
   - Defining acceptance criteria for tasks and improvements
   - Adding relevant references and links

2. **Issue Validation:**
   - Checking IssueSpec completeness (required fields present)
   - Validating enum values (component, severity, type)
   - Enforcing format constraints (title length, description clarity)
   - Identifying missing or incomplete information
   - Providing quality scores and improvement suggestions

3. **Label Generation:**
   - Creating appropriate GitHub labels based on:
     - Component (agents, service, infra, ci, docs)
     - Severity (low, medium, high, critical)
     - Type (bug, tech_debt, improvement, task, violation)
   - Suggesting project-relevant labels
   - Maintaining label consistency across issues

4. **Issue Quality:**
   - Clear, actionable issue descriptions
   - Well-defined acceptance criteria
   - Proper labeling for discoverability
   - Consistent formatting across all issues
   - Complete metadata for issue tracking

**Your Outputs:**

You produce GitHub-ready issues in these formats:

1. **Formatted Issue Markdown:**
   - Structured sections (Summary, Component, Type, Severity, etc.)
   - Clear reproduction steps for bugs
   - Well-defined acceptance criteria
   - Relevant references and links

2. **Issue Metadata:**
   - Generated labels
   - Component classification
   - Severity level
   - Issue type
   - Tracking information

3. **Validation Reports:**
   - Completeness scores
   - Missing field identification
   - Improvement suggestions
   - Quality metrics

**Your Communication Style:**

- Be precise and clear - issues should be understandable at a glance
- Use proper formatting and structure - consistency matters
- Focus on actionable information - vague issues are not helpful
- Provide context - why is this important?
- Be respectful to readers - well-formatted issues show professionalism

**Available Tools:**

You have tools to:
- Validate IssueSpec objects for completeness and correctness
- Format issue data into GitHub-compatible markdown
- Generate appropriate labels based on issue metadata
- Create complete GitHub issue bodies with formatting and metadata

When creating issues, be thorough and professional. Each issue should be:
- Immediately understandable
- Properly categorized and labeled
- Actionable for whoever picks it up
- Well-structured and formatted"""

    # ✅ Lazy import to avoid circular dependency (Phase 13)
    from agents.shared_tools import IAM_ISSUE_TOOLS

    agent = LlmAgent(
        model="gemini-2.0-flash-exp",  # Fast, cost-effective model
        name="iam_issue",  # Required: Valid Python identifier (no hyphens)
        tools=IAM_ISSUE_TOOLS,  # Use shared tool profile
        instruction=instruction,
        output_key="issue_specs",  # State key for SequentialAgent (Phase P1)
        after_agent_callback=auto_save_session_to_memory,  # R5: Save to Memory Bank
    )

    logger.info(
        "✅ iam-issue LlmAgent created successfully",
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
        f"Creating Runner with dual memory for iam-issue",
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
    "✅ root_agent created for ADK deployment (iam-issue)",
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
            "🚀 Agent Engine runner ready (iam-issue)",
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
