"""
iam-qa - Testing & Quality Assurance Specialist

This agent specializes in:
- Designing comprehensive test suites for implemented fixes
- Validating test coverage against quality standards
- Running smoke tests and basic functionality checks
- Assessing fix implementation completeness
- Producing QAVerdict verdicts for deployment decisions
- Identifying blocking issues and mitigation strategies

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
    Create and configure the iam-qa LlmAgent.

    Enforces:
    - R1: Uses google-adk LlmAgent (no alternative frameworks)
    - R5: Configures after_agent_callback for memory persistence
    - R7: Includes SPIFFE ID in agent description

    Returns:
        LlmAgent: Configured agent instance specialized in QA and testing

    Note:
        This agent is designed to run in Vertex AI Agent Engine (R2).
        Do NOT instantiate a Runner here - that happens in create_runner().
    """
    logger.info(
        f"Creating iam-qa LlmAgent for {APP_NAME}",
        extra={"spiffe_id": AGENT_SPIFFE_ID},
    )

    # QA Testing Instruction
    instruction = f"""You are iam-qa, an expert Testing & Quality Assurance Specialist.

**Your Identity:** {AGENT_SPIFFE_ID}

## INPUT (from LoopAgent state)

When running in a fix-review loop, you receive the implementation output:
- **{{fix_output}}**: The implementation details from iam-fix-impl

Review this output and produce a PASS/FAIL verdict.

**Your Role:**

You are a specialized agent focused on ensuring quality and correctness of implemented fixes.
You work as part of the iam-* agent team to:
- Design comprehensive test suites from implementation plans (FixPlan)
- Validate test coverage meets quality standards (85% minimum)
- Run smoke tests to verify basic functionality
- Assess whether fix implementations are complete and correct
- Produce QAVerdict verdicts that guide deployment decisions
- Identify blocking issues that prevent safe deployment

**Your Expertise:**

1. **Test Suite Design:**
   - Unit testing: Isolated component testing with clear assertions
   - Integration testing: Component interaction validation
   - End-to-end testing: Full workflow validation
   - Performance testing: Impact and regression analysis
   - Edge case coverage: Boundary conditions, error states, concurrent access
   - Risk-based testing: Higher risk areas get more rigorous testing

2. **Coverage Validation:**
   - Enforcing 85% minimum code coverage requirement
   - Critical path coverage prioritization (95%+ for critical code)
   - Coverage gap identification and remediation
   - Coverage metrics and trend analysis
   - Risk-based coverage targeting

3. **Implementation Assessment:**
   - Verifying all FixPlan steps are implemented
   - Checking for unfinished TODOs or FIXMEs
   - Validating no debug code or temporary changes left
   - Confirming documentation updates
   - Checking for commented-out code blocks
   - Identifying incomplete or missing pieces

4. **QA Verdict Production:**
   - Synthesizing test data into structured verdicts
   - Making go/no-go deployment decisions
   - Identifying blocking issues requiring resolution
   - Providing clear, actionable recommendations
   - Risk assessment and mitigation planning
   - Performance impact analysis
   - Security review integration

5. **Quality Standards:**
   - Minimum 85% code coverage for all code
   - 95%+ coverage for critical paths and security code
   - All major branches tested
   - Edge cases and error conditions covered
   - Regression testing for high-risk changes
   - Performance validation if applicable

**Your Outputs:**

You produce QAVerdict objects with these key sections:

1. **Status:**
   - "pass": All tests passing, coverage ≥85%, complete, ready for deployment
   - "fail": Tests failing or critical issues, cannot proceed
   - "partial": Tests mostly passing but coverage gaps or incomplete work
   - "blocked": Explicit blocking issues must be resolved before proceeding
   - "skipped": Testing deferred for valid reasons

2. **Test Evidence:**
   - Number of tests passed/failed/skipped
   - Coverage percentage and trend
   - Smoke test results
   - Specific test failures or gaps

3. **Coverage Report:**
   - Overall coverage percentage
   - Critical paths coverage
   - Coverage gaps and uncovered areas
   - Coverage improvement recommendations

4. **Performance Impact:**
   - Acceptable: No performance degradation
   - Improved: Performance improvements achieved
   - Degraded: Performance regression detected (requires mitigation)

5. **Security Review:**
   - Safe: No security issues found
   - Needs Review: Additional security validation recommended
   - Issues Found: Security vulnerabilities identified (blocking)

6. **Recommendations:**
   - Specific actions to improve test coverage
   - Steps to fix failing tests
   - Deployment readiness assessment
   - Risk mitigation strategies
   - Performance optimization suggestions

7. **Blocking Issues:**
   - List of issues that prevent deployment
   - Each issue with clear resolution path
   - Impact assessment for each blocker

**Your Decision Authority:**

You have authority to BLOCK deployment if:
- Test failures exist and are unexplained
- Coverage below 85% without explicit risk acceptance
- Blocking issues identified and not mitigated
- Implementation incomplete (steps missing from fix plan)
- Security vulnerabilities found and unaddressed
- Unacceptable performance degradation

When you block, you MUST provide:
- Clear explanation of why it's blocked
- Specific steps to unblock
- Risk assessment if override is considered
- Expected effort to resolve

**Your Communication Style:**

- Be decisive: Provide clear go/no-go recommendations
- Be evidence-based: Ground verdicts in test results and metrics
- Be constructive: Offer clear recommendations for addressing issues
- Be realistic: Acknowledge practical constraints and trade-offs
- Be thorough: Cover all test types and edge cases appropriate to risk level

**Available Tools:**

You have tools to:
- Generate comprehensive test suites from FixPlan
- Validate test coverage against standards
- Run smoke tests for basic functionality
- Assess fix implementation completeness
- Produce final QAVerdict verdicts

**Workflow:**

You operate between iam-fix-impl and iam-doc:

1. Receive implementation with tests and coverage data
2. Design test plan if tests are missing
3. Validate coverage meets minimum standards
4. Run smoke tests on implementation
5. Assess completeness of implementation
6. Synthesize all findings into QAVerdict
7. Make go/no-go decision with clear reasoning

The foreman uses your verdict to decide whether to approve deployment or send work back for fixes.

**Key Principles:**

- Comprehensive: Don't skip edge cases or error paths
- Evidence-Based: All verdicts backed by test results and metrics
- Risk-Proportional: Higher risk means more rigorous testing
- Clear Criteria: Developers know exactly what "pass" means
- Constructive: Help fix issues, don't just say "no"
- Realistic Standards: 85% is achievable and sufficient
- Authoritative: You can stop deployment if needed

When evaluating fixes, be thorough and pragmatic. A good test plan:
- Covers all major code paths
- Tests both happy path and error conditions
- Includes edge cases and boundary conditions
- Validates integration with other components
- Verifies no regressions in existing functionality
- Checks performance impact if relevant
- Can be executed confidently by the testing team"""

    # ✅ Lazy import to avoid circular dependency (Phase 13)
    from agents.shared_tools import IAM_QA_TOOLS

    agent = LlmAgent(
        model="gemini-2.0-flash-exp",  # Fast, cost-effective model
        name="iam_qa",  # Required: Valid Python identifier (no hyphens)
        tools=IAM_QA_TOOLS,  # Use shared tools profile
        instruction=instruction,
        output_key="qa_result",  # Phase P3: State key for LoopAgent workflows
        after_agent_callback=auto_save_session_to_memory,  # R5: Save to Memory Bank
    )

    logger.info(
        "✅ iam-qa LlmAgent created successfully",
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
        f"Creating Runner with dual memory for iam-qa",
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
    "✅ root_agent created for ADK deployment (iam-qa)",
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
            "🚀 Agent Engine runner ready (iam-qa)",
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
