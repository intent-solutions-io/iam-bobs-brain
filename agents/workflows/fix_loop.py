"""
Fix Loop Workflow - Phase P3: Quality Gates Pattern.

Implements Google's Generator-Critic and Iterative Refinement patterns
using ADK's LoopAgent primitive.

Reference: https://developers.googleblog.com/en/developers-guide-to-multi-agent-patterns-in-adk/

Pattern: Generator-Critic + Iterative Refinement
- Generator (iam-fix-impl): Produces implementation
- Critic (iam-qa): Reviews and signals PASS/FAIL
- Loop continues until PASS or max_iterations reached

State Flow:
┌─────────────────────────────────────────────────────────────┐
│                     fix_loop (LoopAgent)                    │
│                     max_iterations=3                        │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              fix_review (SequentialAgent)            │   │
│  │                                                      │   │
│  │  ┌──────────────┐      ┌──────────────┐             │   │
│  │  │ iam-fix-impl │ ──→  │   iam-qa     │             │   │
│  │  │  (generator) │      │   (critic)   │             │   │
│  │  │              │      │              │             │   │
│  │  │ output_key:  │      │ output_key:  │             │   │
│  │  │ fix_output   │      │ qa_result    │             │   │
│  │  └──────────────┘      └──────┬───────┘             │   │
│  │                               │                      │   │
│  │                    ┌──────────┴──────────┐          │   │
│  │                    │                     │          │   │
│  │               PASS: escalate       FAIL: retry      │   │
│  │                    │                     │          │   │
│  └────────────────────┼─────────────────────┼──────────┘   │
│                       │                     │              │
│                  exit loop             next iteration      │
└───────────────────────┴─────────────────────┴──────────────┘
"""

from google.adk.agents import LoopAgent, SequentialAgent, LlmAgent
import logging

logger = logging.getLogger(__name__)


def create_fix_review() -> SequentialAgent:
    """
    Create generator-critic pair as SequentialAgent.

    This is the inner sequential workflow that:
    1. Generator (iam-fix-impl): Produces implementation -> fix_output
    2. Critic (iam-qa): Reviews implementation -> qa_result

    The LoopAgent wraps this to enable retries on FAIL.

    Returns:
        SequentialAgent: Generator-critic pair for fix review
    """
    # Import agent factories (lazy to avoid circular imports)
    from agents.iam_fix_impl.agent import create_agent as create_iam_fix_impl
    from agents.iam_qa.agent import create_agent as create_iam_qa

    logger.info("Creating fix-review generator-critic pair")

    review = SequentialAgent(
        name="fix_review",
        sub_agents=[
            create_iam_fix_impl(),  # output_key="fix_output"
            create_iam_qa(),        # output_key="qa_result", reads {fix_output}
        ],
    )

    logger.info("✅ fix_review SequentialAgent created: iam-fix-impl → iam-qa")
    return review


def create_fix_loop(max_iterations: int = 3) -> LoopAgent:
    """
    Create iterative refinement loop using LoopAgent.

    The loop continues until:
    - iam-qa signals PASS (escalate=True in callback), OR
    - max_iterations reached (default: 3)

    This implements Google's Iterative Refinement pattern where
    the generator keeps improving until the critic approves.

    Args:
        max_iterations: Maximum loop iterations before failure (default: 3)

    Returns:
        LoopAgent: Configured loop agent for fix iteration
    """
    logger.info(f"Creating fix loop with max_iterations={max_iterations}")

    loop = LoopAgent(
        name="fix_loop",
        sub_agents=[create_fix_review()],
        max_iterations=max_iterations,
    )

    logger.info(f"✅ fix_loop LoopAgent created with max_iterations={max_iterations}")
    return loop


def create_qa_escalation_callback():
    """
    Create callback function for QA escalation.

    This callback can be attached to iam-qa to signal early loop exit
    when the implementation passes review.

    Usage:
        When QA result shows PASS status, set ctx.actions.escalate = True
        to exit the LoopAgent early.

    Returns:
        Callable: Callback function for QA escalation

    Note:
        This is a utility function. The actual callback logic depends on
        how the LLM structures its response. In practice, the escalation
        should be triggered based on the qa_result state key content.
    """
    def qa_escalation_callback(ctx):
        """After-agent callback to signal loop exit on QA PASS."""
        try:
            # Check if QA passed
            qa_result = ctx.state.get("qa_result", {})

            # Handle both string and dict responses
            if isinstance(qa_result, str):
                # Check for PASS keyword in string response
                if "PASS" in qa_result.upper() and "FAIL" not in qa_result.upper():
                    ctx.actions.escalate = True
                    logger.info("✅ QA PASSED - signaling loop exit via escalate")
            elif isinstance(qa_result, dict):
                # Check status field in dict response
                status = qa_result.get("status", "").upper()
                if status == "PASS":
                    ctx.actions.escalate = True
                    logger.info("✅ QA PASSED - signaling loop exit via escalate")
        except Exception as e:
            logger.warning(f"Error in QA escalation callback: {e}")
            # Don't escalate on error - let the loop continue

    return qa_escalation_callback


# Export functions for workflow module
__all__ = [
    "create_fix_review",
    "create_fix_loop",
    "create_qa_escalation_callback",
]
