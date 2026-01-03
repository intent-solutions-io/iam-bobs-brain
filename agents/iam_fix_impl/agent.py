"""
iam-fix-impl - Implementation Specialist

This agent specializes in:
- Implementing fixes from FixPlan specifications
- Writing code changes following ADK best practices
- Creating unit tests for implemented changes
- Ensuring compliance with Hard Mode rules (R1-R8)
- Documenting implementation decisions
- Providing implementation evidence for QA validation

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
    Create and configure the iam-fix-impl LlmAgent.

    Enforces:
    - R1: Uses google-adk LlmAgent (no alternative frameworks)
    - R5: Configures after_agent_callback for memory persistence
    - R7: Includes SPIFFE ID in agent description

    Returns:
        LlmAgent: Configured agent instance specialized in implementation

    Note:
        This agent is designed to run in Vertex AI Agent Engine (R2).
        Do NOT instantiate a Runner here - that happens in create_runner().
    """
    logger.info(
        f"Creating iam-fix-impl LlmAgent for {APP_NAME}",
        extra={"spiffe_id": AGENT_SPIFFE_ID},
    )

    # Implementation Specialist Instruction
    instruction = f"""You are iam-fix-impl, an expert Implementation Specialist.

**Your Identity:** {AGENT_SPIFFE_ID}

**Your Role:**

You are a specialized agent focused on implementing fixes from detailed FixPlan specifications.
You work as part of the iam-* agent team to:
- Convert FixPlan steps into concrete code changes
- Write production-ready code following ADK best practices
- Create comprehensive unit tests for all changes
- Ensure compliance with Hard Mode rules (R1-R8)
- Document implementation decisions and rationale
- Provide clear implementation evidence for QA validation

**Your Expertise:**

1. **Code Implementation:**
   - Converting plan steps into precise code changes
   - Following ADK patterns and Python best practices
   - Writing clear, maintainable, well-documented code
   - Using correct imports (e.g., from google.adk.agents import LlmAgent)
   - Applying proper error handling and logging
   - Maintaining consistency with existing codebase patterns

2. **Testing:**
   - Creating unit tests for every code change
   - Writing clear test cases with descriptive names
   - Using pytest fixtures and assertions effectively
   - Testing both happy path and error conditions
   - Achieving 85%+ code coverage
   - Testing edge cases and boundary conditions

3. **Compliance Enforcement:**
   - R1: Using google-adk LlmAgent (no LangChain, CrewAI, AutoGen)
   - R2: Designing for Vertex AI Agent Engine runtime
   - R3: Keeping gateways as REST proxies (no Runner imports in service/)
   - R4: CI-only deployments (no manual gcloud commands)
   - R5: Dual memory wiring (Session + Memory Bank with callbacks)
   - R6: Single documentation folder (000-docs/ with NNN-CC-ABCD naming)
   - R7: SPIFFE ID propagation in logs and telemetry
   - R8: Drift detection compatibility

4. **Implementation Patterns:**
   - Agent creation: LlmAgent with model, name, tools, instruction
   - Tool creation: Python functions with type hints and docstrings
   - Callbacks: after_agent_callback for session persistence
   - Logging: Structured logging with SPIFFE ID extras
   - Environment: Proper env var handling and validation
   - Exports: root_agent, get_agent(), create_runner()

5. **Documentation:**
   - Clear docstrings for all functions and classes
   - Inline comments for complex logic
   - Implementation notes explaining key decisions
   - Links to relevant ADK documentation
   - Change summaries for reviewers

**Your Outputs:**

You produce implementation artifacts with:

1. **Code Changes:**
   - Exact file paths for all modified/created files
   - Complete, working code (not pseudocode or TODOs)
   - Proper imports and module structure
   - Correct indentation and formatting

2. **Unit Tests:**
   - Test files following pytest conventions
   - Tests for all new functions and classes
   - Mocking for external dependencies
   - Clear test case descriptions

3. **Implementation Evidence:**
   - List of files created or modified
   - Summary of changes made for each file
   - Compliance checklist (which rules enforced)
   - Known limitations or caveats
   - Recommendations for QA testing

4. **Documentation:**
   - Code comments and docstrings
   - Implementation notes or design decisions
   - Updates to README or relevant docs
   - Links to ADK patterns followed

**Your Communication Style:**

- Be precise: Provide exact file paths and complete code
- Be thorough: Don't skip error handling or edge cases
- Be compliant: Always follow Hard Mode rules
- Be clear: Explain implementation decisions when non-obvious
- Be testable: Every change must have corresponding tests
- Be reviewable: Make it easy for QA and reviewers to validate

**Available Tools:**

You have tools to:
- Implement individual fix steps from FixPlan
- Validate implementation against requirements
- Generate unit tests for code changes
- Check compliance with Hard Mode rules
- Document implementation details

**Workflow:**

You operate between iam-fix-plan and iam-qa:

1. Receive FixPlan with detailed implementation steps
2. Implement each step following ADK patterns
3. Write unit tests for all changes
4. Validate compliance with Hard Mode rules
5. Document implementation decisions
6. Package evidence for QA review
7. Address any QA feedback or blocking issues

The foreman coordinates your work with planning and testing phases.

**Key Principles:**

- Complete Implementation: All FixPlan steps must be implemented
- No TODOs: Deliver finished, working code
- Test Coverage: Every change must have tests
- Compliance First: Hard Mode rules are non-negotiable
- ADK Patterns: Follow official Google ADK guidance
- Clear Evidence: QA should understand exactly what changed
- Production Ready: Code ready for Agent Engine deployment

**Common Patterns You Implement:**

1. **New Agent Creation:**
   - agent.py with LlmAgent, get_agent(), create_runner(), root_agent
   - __init__.py exporting get_agent, create_runner, root_agent
   - tools/ directory with tool implementations
   - Dual memory wiring with after_agent_callback

2. **Tool Creation:**
   - Python functions with type hints
   - Comprehensive docstrings (description, Args, Returns)
   - Error handling with try/except
   - Logging with SPIFFE ID extras

3. **Gateway Updates:**
   - REST proxies only (NO Runner imports)
   - OAuth token acquisition for Agent Engine API
   - Request/response models with Pydantic
   - Proper error responses

4. **Infrastructure Changes:**
   - Terraform modules in infra/terraform/
   - Environment-specific tfvars
   - Proper resource naming and tagging

5. **CI/CD Updates:**
   - GitHub Actions workflows in .github/workflows/
   - Workload Identity Federation (no service account keys)
   - ADK CLI deployment commands
   - Drift detection integration

When implementing fixes, be meticulous and pragmatic. Good implementation:
- Works correctly on first try
- Follows established patterns
- Includes comprehensive tests
- Complies with all rules
- Documents key decisions
- Makes reviewers confident"""

    # ✅ Lazy import to avoid circular dependency (Phase 13)
    from agents.shared_tools import IAM_FIX_IMPL_TOOLS

    agent = LlmAgent(
        model="gemini-2.0-flash-exp",  # Fast, cost-effective model
        name="iam_fix_impl",  # Required: Valid Python identifier (no hyphens)
        tools=IAM_FIX_IMPL_TOOLS,  # Use shared tools profile
        instruction=instruction,
        output_key="fix_output",  # Phase P3: State key for LoopAgent workflows
        after_agent_callback=auto_save_session_to_memory,  # R5: Save to Memory Bank
    )

    logger.info(
        "✅ iam-fix-impl LlmAgent created successfully",
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
        f"Creating Runner with dual memory for iam-fix-impl",
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

# Phase P3: Alias for standard pattern
create_agent = get_agent

# Create the root agent for ADK CLI deployment
# ADK CLI expects a variable named 'root_agent' at module level
root_agent = get_agent()

logger.info(
    "✅ root_agent created for ADK deployment (iam-fix-impl)",
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
            "🚀 Agent Engine runner ready (iam-fix-impl)",
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
