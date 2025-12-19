"""
Quality Gates Pattern - Standalone Template

Implements Google's Generator-Critic + Iterative Refinement patterns using LoopAgent.
Reference: https://developers.googleblog.com/en/developers-guide-to-multi-agent-patterns-in-adk/
"""

from google.adk.agents import LoopAgent, SequentialAgent, LlmAgent
from typing import Callable, Optional
import logging

logger = logging.getLogger(__name__)


def create_escalation_callback(verdict_key: str = "verdict") -> Callable:
    """
    Create callback that exits loop on PASS.

    The callback checks the verdict state key and signals escalation
    (loop exit) when the critic approves the output.

    Args:
        verdict_key: State key containing critic verdict

    Returns:
        Callback function for after_agent_callback
    """
    def escalation_callback(ctx):
        verdict = ctx.state.get(verdict_key, {})

        # Handle dict verdict
        if isinstance(verdict, dict):
            if verdict.get("status", "").upper() == "PASS":
                ctx.actions.escalate = True
                logger.info("Quality PASSED - exiting loop")
                return

        # Handle string verdict
        if isinstance(verdict, str):
            if "PASS" in verdict.upper():
                ctx.actions.escalate = True
                logger.info("Quality PASSED - exiting loop")
                return

        logger.info("Quality FAILED - continuing loop")

    return escalation_callback


def create_quality_loop(
    name: str,
    generator: LlmAgent,
    critic: LlmAgent,
    max_iterations: int = 3,
) -> LoopAgent:
    """
    Create a quality gate loop with generator-critic pattern.

    Args:
        name: Name for the loop
        generator: Agent that produces output
        critic: Agent that evaluates output (must output PASS/FAIL)
        max_iterations: Maximum retry attempts (REQUIRED, prevents infinite loops)

    Returns:
        LoopAgent wrapping the generator-critic pair
    """
    if max_iterations < 1:
        raise ValueError("max_iterations must be at least 1")

    # Add escalation callback to critic if not present
    if not critic.after_agent_callback:
        critic_output_key = getattr(critic, 'output_key', 'verdict')
        critic.after_agent_callback = create_escalation_callback(critic_output_key)

    # Create generator-critic pair
    review_pair = SequentialAgent(
        name=f"{name}_review",
        sub_agents=[generator, critic],
    )

    # Wrap in loop
    return LoopAgent(
        name=name,
        sub_agents=[review_pair],
        max_iterations=max_iterations,
    )


def create_generator_agent(
    name: str = "generator",
    instruction: str = "",
    output_key: str = "generated_output",
    model: str = "gemini-2.0-flash-exp",
    feedback_key: Optional[str] = "verdict",
) -> LlmAgent:
    """
    Create a generator agent that improves based on critic feedback.

    Args:
        name: Agent name
        instruction: Base instruction (feedback reference added automatically)
        output_key: State key for output
        model: LLM model to use
        feedback_key: State key for critic feedback

    Returns:
        Configured generator LlmAgent
    """
    # Add feedback incorporation to instruction
    full_instruction = f"""{instruction}

If previous feedback exists in {{{feedback_key}}}, incorporate it to improve your output.
"""

    return LlmAgent(
        name=name,
        model=model,
        instruction=full_instruction,
        output_key=output_key,
    )


def create_critic_agent(
    name: str = "critic",
    criteria: str = "quality and completeness",
    input_key: str = "generated_output",
    output_key: str = "verdict",
    model: str = "gemini-2.0-flash-exp",
) -> LlmAgent:
    """
    Create a critic agent that evaluates generator output.

    Args:
        name: Agent name
        criteria: What to evaluate for
        input_key: State key containing output to review
        output_key: State key for verdict
        model: LLM model to use

    Returns:
        Configured critic LlmAgent with escalation callback
    """
    instruction = f"""You are a quality reviewer. Evaluate the output for {criteria}.

Output to review: {{{input_key}}}

Output EXACTLY this JSON format:
{{
  "status": "PASS" or "FAIL",
  "reason": "Brief explanation",
  "issues": ["list", "of", "issues"] or []
}}

PASS if the output meets quality standards.
FAIL if improvements are needed (list specific issues).
"""

    agent = LlmAgent(
        name=name,
        model=model,
        instruction=instruction,
        output_key=output_key,
    )

    # Add escalation callback
    agent.after_agent_callback = create_escalation_callback(output_key)

    return agent


# ============================================================================
# Example: Content Generation with QA
# ============================================================================


def create_content_qa_loop(max_iterations: int = 3) -> LoopAgent:
    """
    Example: Create a content generation loop with QA gates.

    Generator produces content, critic reviews it.
    Loop continues until PASS or max iterations.
    """
    generator = create_generator_agent(
        name="content_generator",
        instruction="""Generate high-quality content based on the request.

Request: {user_input}

Create content that is:
1. Clear and well-structured
2. Accurate and informative
3. Engaging and readable
""",
        output_key="content",
        feedback_key="qa_verdict",
    )

    critic = create_critic_agent(
        name="content_reviewer",
        criteria="clarity, accuracy, structure, and engagement",
        input_key="content",
        output_key="qa_verdict",
    )

    return create_quality_loop(
        name="content_qa_loop",
        generator=generator,
        critic=critic,
        max_iterations=max_iterations,
    )


__all__ = [
    "create_escalation_callback",
    "create_quality_loop",
    "create_generator_agent",
    "create_critic_agent",
    "create_content_qa_loop",
]
