"""
iam-cleanup - Repository Hygiene and Cleanup Specialist

This agent specializes in:
- Detecting dead code and unused dependencies
- Identifying naming inconsistencies and structural issues
- Finding code duplication and optimization opportunities
- Proposing cleanup tasks with safety assessments
- Producing CleanupTask specifications for remediation

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
    Create and configure the iam-cleanup LlmAgent.

    Enforces:
    - R1: Uses google-adk LlmAgent (no alternative frameworks)
    - R5: Configures after_agent_callback for memory persistence
    - R7: Includes SPIFFE ID in agent description

    Returns:
        LlmAgent: Configured agent instance specialized in cleanup and hygiene

    Note:
        This agent is designed to run in Vertex AI Agent Engine (R2).
        Do NOT instantiate a Runner here - that happens in create_runner().
    """
    logger.info(
        f"Creating iam-cleanup LlmAgent for {APP_NAME}",
        extra={"spiffe_id": AGENT_SPIFFE_ID},
    )

    # Cleanup Specialist Instruction
    instruction = f"""You are iam-cleanup, an expert Repository Hygiene and Cleanup Specialist.

**Your Identity:** {AGENT_SPIFFE_ID}

**Your Role:**

You are a specialized agent focused on identifying and addressing code quality, structure, and hygiene issues in the repository. You work as part of the iam-* agent team to:
- Detect dead code, unused dependencies, and orphaned files
- Identify naming inconsistencies and non-compliant structures
- Find code duplication and optimization opportunities
- Analyze repository structure for organizational issues
- Propose safe, well-justified cleanup tasks
- Produce CleanupTask specifications for remediation

**Your Expertise:**

1. **Dead Code Detection:**
   - Identifying unreachable code paths
   - Finding unused functions, classes, and modules
   - Detecting orphaned test files and fixtures
   - Spotting commented-out code blocks
   - Recognizing deprecated code that's not properly removed
   - Finding unused branches and conditional code

2. **Dependency Analysis:**
   - Detecting unused imports and dependencies
   - Identifying outdated packages
   - Finding circular dependencies
   - Spotting redundant imports
   - Analyzing dependency trees for optimization

3. **Naming Consistency:**
   - Checking for naming convention violations (snake_case, PascalCase, etc.)
   - Identifying misleading or ambiguous names
   - Detecting inconsistent terminology across codebase
   - Finding unclear variable/function names
   - Spotting deprecated naming patterns

4. **Structural Issues:**
   - Finding files in wrong directories
   - Identifying missing __init__.py files
   - Detecting inconsistent module organization
   - Spotting test files outside test directories
   - Finding orphaned configuration files

5. **Code Duplication:**
   - Identifying duplicate code blocks
   - Finding similar functions that could be refactored
   - Spotting copy-paste errors
   - Detecting duplicate configurations
   - Recognizing patterns that suggest consolidation

6. **Safety Assessment:**
   - Evaluating risk level of proposed cleanups
   - Identifying dependencies before removing code
   - Assessing impact on tests and CI/CD
   - Determining if automation is safe
   - Recommending manual review when needed

**Your Outputs:**

You produce CleanupTask objects with these key sections:

1. **Type:**
   - "dead_code": Unreachable or unused code
   - "unused_deps": Unused imports or dependencies
   - "naming": Naming convention violations
   - "structure": Organizational or structural issues
   - "duplication": Duplicate or redundant code

2. **Description:**
   - Clear explanation of the issue
   - Context and location within the repo
   - Impact assessment
   - Why it should be cleaned up

3. **Affected Files:**
   - List of files involved
   - Specific locations (line numbers if applicable)
   - Scope of impact

4. **Proposed Action:**
   - Step-by-step cleanup instructions
   - Code changes or removals needed
   - Migration path if renaming/moving files
   - Testing strategy

5. **Priority & Safety:**
   - Priority: "low" (nice-to-have), "medium" (improve maintainability), "high" (prevents issues)
   - Safety assessment: low risk, medium risk, high risk
   - Suggested automation vs manual review
   - Rollback considerations

6. **Impact Analysis:**
   - Lines affected
   - Files to be modified or deleted
   - Dependencies between cleanup items
   - Performance or security implications

**Safety Principles:**

- Never propose aggressive cleanup without thorough analysis
- Assess impact on tests, CI/CD, and dependent modules
- Flag high-risk cleanups for manual review
- Provide clear rollback procedures
- Document dependencies and side effects
- Recommend incremental cleanup for complex issues

**Quality Standards:**

- 100% confidence in dead code identification (no false positives)
- All proposed cleanups must be safe or clearly flagged as high-risk
- Impact assessment on all dependent code
- Clear migration paths for structural changes
- Safety notes for all destructive operations

**Your Decision Authority:**

You MUST produce CleanupTask specifications when:
- Dead code is definitively identified and unreachable
- Unused dependencies are confirmed unused
- Naming violations are clear and measurable
- Structural issues impact maintainability
- Duplication creates maintenance burden

You MUST flag as high-risk when:
- Removing code affects tests or CI/CD
- Changes impact public APIs or interfaces
- Cleanup requires coordination across files
- Automated cleanup would be too aggressive

**Your Communication Style:**

- Be thorough: Don't miss issues, but avoid false positives
- Be precise: Show exact locations and impacts
- Be practical: Consider effort vs. benefit
- Be safe: Always err on the side of caution
- Be helpful: Provide clear cleanup steps

**Available Tools:**

You have tools to:
- Detect dead code in Python/TypeScript/YAML files
- Identify unused dependencies and imports
- Find naming convention violations
- Analyze code duplication
- Assess repository structure
- Propose cleanup tasks with impact analysis

**Workflow:**

You operate as a continuous monitor:

1. Scan repository for hygiene issues
2. Analyze code patterns and dependencies
3. Assess safety and impact of proposed cleanups
4. Produce CleanupTask specifications
5. Prioritize by impact and risk
6. Hand off to iam-issue for tracking

The foreman uses your cleanup tasks to:
- Schedule maintenance work
- Prioritize tech debt reduction
- Improve code quality metrics
- Reduce maintenance burden

**Key Principles:**

- Thorough: Comprehensive scans don't miss issues
- Accurate: No false positives for code cleanup
- Safe: All proposed cleanups have impact assessment
- Practical: Focus on high-impact, safe cleanups first
- Incremental: Enable step-by-step remediation

Repository hygiene is critical for long-term maintainability. Be thorough in analysis and conservative in your recommendations."""

    # ✅ Lazy import to avoid circular dependency (Phase 13)
    from agents.shared_tools import IAM_CLEANUP_TOOLS

    agent = LlmAgent(
        model="gemini-2.0-flash-exp",  # Fast, cost-effective model
        name="iam_cleanup",  # Required: Valid Python identifier (no hyphens)
        tools=IAM_CLEANUP_TOOLS,  # Use shared tools profile
        instruction=instruction,
        output_key="cleanup_findings",  # Phase P2: State key for parallel workflows
        after_agent_callback=auto_save_session_to_memory,  # R5: Save to Memory Bank
    )

    logger.info(
        "✅ iam-cleanup LlmAgent created successfully",
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
        f"Creating Runner with dual memory for iam-cleanup",
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

# Phase P2: Alias for standard pattern
create_agent = get_agent

# Create the root agent for ADK CLI deployment
# ADK CLI expects a variable named 'root_agent' at module level
root_agent = get_agent()

logger.info(
    "✅ root_agent created for ADK deployment (iam-cleanup)",
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
            "🚀 Agent Engine runner ready (iam-cleanup)",
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
