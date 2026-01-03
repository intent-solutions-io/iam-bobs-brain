"""
Sequential Workflow Pattern - Standalone Template

Implements Google's Sequential Pipeline pattern using SequentialAgent.
Reference: https://developers.googleblog.com/en/developers-guide-to-multi-agent-patterns-in-adk/
"""

from google.adk.agents import SequentialAgent, LlmAgent
from typing import List, Optional


def create_sequential_workflow(
    name: str,
    agents: List[LlmAgent],
) -> SequentialAgent:
    """
    Create a sequential workflow from a list of agents.

    Each agent should have a unique output_key, and subsequent agents
    can reference previous outputs via {key} in their instructions.

    Args:
        name: Name for the workflow
        agents: List of LlmAgents to execute in order

    Returns:
        SequentialAgent wrapping the pipeline

    Example:
        >>> workflow = create_sequential_workflow(
        ...     name="analysis_pipeline",
        ...     agents=[analyzer, planner, executor],
        ... )
    """
    # Validate unique output_keys
    output_keys = [a.output_key for a in agents if hasattr(a, 'output_key')]
    if len(output_keys) != len(set(output_keys)):
        raise ValueError("All agents must have unique output_keys")

    return SequentialAgent(
        name=name,
        sub_agents=agents,
    )


def create_step_agent(
    name: str,
    instruction: str,
    output_key: str,
    model: str = "gemini-2.0-flash-exp",
    tools: Optional[List] = None,
) -> LlmAgent:
    """
    Create an agent for use in sequential workflows.

    Args:
        name: Agent name (valid Python identifier)
        instruction: System prompt (use {key} to reference state)
        output_key: State key for this agent's output
        model: LLM model to use
        tools: Optional list of tools

    Returns:
        Configured LlmAgent
    """
    return LlmAgent(
        name=name,
        model=model,
        instruction=instruction,
        output_key=output_key,
        tools=tools or [],
    )


# ============================================================================
# Example: Three-Step Pipeline
# ============================================================================


def create_analysis_pipeline() -> SequentialAgent:
    """
    Example: Create a three-step analysis pipeline.

    Pipeline: Analyze → Plan → Execute
    State: input → analysis → plan → result
    """
    analyzer = create_step_agent(
        name="analyzer",
        instruction="""Analyze the input problem and identify key issues.

Input: {user_input}

Output a structured analysis with:
1. Problem summary
2. Key issues identified
3. Recommended approach
""",
        output_key="analysis",
    )

    planner = create_step_agent(
        name="planner",
        instruction="""Based on the analysis, create an action plan.

Analysis: {analysis}

Output a structured plan with:
1. Goals
2. Steps (in order)
3. Success criteria
""",
        output_key="plan",
    )

    executor = create_step_agent(
        name="executor",
        instruction="""Execute the plan and report results.

Plan: {plan}

For each step in the plan:
1. Execute the step
2. Record the outcome
3. Report any issues

Output the final result.
""",
        output_key="result",
    )

    return create_sequential_workflow(
        name="analysis_pipeline",
        agents=[analyzer, planner, executor],
    )


__all__ = [
    "create_sequential_workflow",
    "create_step_agent",
    "create_analysis_pipeline",
]
