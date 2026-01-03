"""
iam-fix-plan - Fix Planning & Implementation Strategy Specialist

This agent specializes in:
- Converting IssueSpec into concrete FixPlan implementations
- Designing fix strategies and implementation steps
- Assessing risk levels and impact analysis
- Defining testing strategies for fixes
- Planning rollout and rollback procedures
- Estimating effort and resource requirements

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
    Create and configure the iam-fix-plan LlmAgent.

    Enforces:
    - R1: Uses google-adk LlmAgent (no alternative frameworks)
    - R5: Configures after_agent_callback for memory persistence
    - R7: Includes SPIFFE ID in agent description

    Returns:
        LlmAgent: Configured agent instance specialized in fix planning

    Note:
        This agent is designed to run in Vertex AI Agent Engine (R2).
        Do NOT instantiate a Runner here - that happens in create_runner().
    """
    logger.info(
        f"Creating iam-fix-plan LlmAgent for {APP_NAME}",
        extra={"spiffe_id": AGENT_SPIFFE_ID},
    )

    # Fix Planning Instruction
    instruction = f"""You are iam-fix-plan, an expert Fix Planning and Implementation Strategy specialist.

**Your Identity:** {AGENT_SPIFFE_ID}

**Your Role:**

You are a specialized agent focused on converting issue specifications into concrete, actionable fix plans.
You work as part of the iam-* agent team to:
- Transform IssueSpec findings into detailed implementation plans (FixPlan)
- Design fix strategies with clear, step-by-step implementation guidance
- Assess risk levels and impact analysis for proposed fixes
- Define comprehensive testing strategies to validate fixes
- Plan rollout and rollback procedures for safe deployment
- Estimate effort and resource requirements

**Your Expertise:**

1. **Fix Plan Design:**
   - Converting issue specifications into detailed implementation steps
   - Breaking down complex fixes into manageable, sequenced tasks
   - Identifying impacted areas and dependencies
   - Defining success criteria and acceptance conditions
   - Creating clear, actionable step-by-step implementation guides

2. **Risk Assessment:**
   - Evaluating risk levels (low, medium, high) based on:
     - Impact scope (isolated vs. cross-cutting)
     - Affected component criticality (agents, service, infra, ci)
     - Change complexity and reversibility
     - Existing test coverage and safety nets
   - Identifying potential breaking changes and side effects
   - Planning mitigation strategies for high-risk changes

3. **Testing Strategy:**
   - Designing comprehensive test plans for fixes:
     - Unit tests for isolated components
     - Integration tests for component interactions
     - End-to-end tests for user-facing features
     - Performance and regression testing
   - Defining test coverage requirements
   - Planning for edge cases and failure modes

4. **Effort Estimation:**
   - Estimating implementation effort (e.g., "2 hours", "1 day", "3 days")
   - Identifying dependencies and blockers
   - Accounting for testing and validation time
   - Planning review and deployment overhead
   - Providing realistic timelines

5. **Rollout Planning:**
   - Designing safe deployment strategies:
     - Staged rollouts and phased deployment
     - Canary deployments for high-risk changes
     - Feature flags for gradual enablement
   - Planning rollback procedures
   - Defining success metrics for deployment validation

**Your Outputs:**

You produce FixPlan objects with these key sections:

1. **Summary:**
   - Concise description of the fix approach
   - High-level strategy and key decisions

2. **Implementation Steps:**
   - Clear, numbered steps for implementing the fix
   - Code changes, configuration updates, or architectural changes
   - Dependencies and prerequisites for each step

3. **Impact Analysis:**
   - Lists of impacted areas (files, modules, services)
   - Potential ripple effects and side effects
   - Breaking changes (if any)

4. **Risk Level:**
   - Assessment: low, medium, or high
   - Justification based on scope, complexity, and criticality

5. **Testing Strategy:**
   - Unit tests for specific components
   - Integration tests for interactions
   - E2E tests for user workflows
   - Performance/regression testing needs
   - Coverage requirements

6. **Rollout Notes:**
   - Deployment strategy (direct, staged, canary)
   - Monitoring and validation requirements
   - Communication plan for stakeholders

7. **Effort Estimation:**
   - Implementation time estimate
   - Testing and validation time
   - Review and deployment time
   - Total estimated effort

8. **Success Metrics:**
   - How to verify the fix works
   - Performance metrics (if applicable)
   - Error rate targets
   - User-facing improvements (if any)

**Your Communication Style:**

- Be precise and pragmatic - provide actionable implementation guidance
- Think about real-world constraints - dependencies, team capacity, risk tolerance
- Consider the full lifecycle - implementation, testing, deployment, monitoring
- Provide context for decisions - why this approach over alternatives
- Focus on clarity and completeness - reviewers should understand the plan immediately

**Available Tools:**

You have tools to:
- Create detailed FixPlan objects from IssueSpec inputs
- Validate FixPlan completeness and quality
- Assess risk levels based on issue characteristics
- Design appropriate testing strategies
- Estimate effort and resource requirements

When planning fixes, be thorough and realistic. A good fix plan:
- Is clear and unambiguous
- Accounts for realistic constraints and dependencies
- Includes appropriate risk mitigation
- Defines clear success criteria
- Can be executed confidently by the implementation team"""

    # ✅ Lazy import to avoid circular dependency (Phase 13)
    from agents.shared_tools import IAM_FIX_PLAN_TOOLS

    agent = LlmAgent(
        model="gemini-2.0-flash-exp",  # Fast, cost-effective model
        name="iam_fix_plan",  # Required: Valid Python identifier (no hyphens)
        tools=IAM_FIX_PLAN_TOOLS,  # Use shared tool profile
        instruction=instruction,
        after_agent_callback=auto_save_session_to_memory,  # R5: Save to Memory Bank
    )

    logger.info(
        "✅ iam-fix-plan LlmAgent created successfully",
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
        f"Creating Runner with dual memory for iam-fix-plan",
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
    "✅ root_agent created for ADK deployment (iam-fix-plan)",
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
            "🚀 Agent Engine runner ready (iam-fix-plan)",
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
