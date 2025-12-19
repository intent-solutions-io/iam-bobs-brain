"""
Parallel Workflow Pattern - Standalone Template

Implements Google's Parallel Fan-Out pattern using ParallelAgent.
Reference: https://developers.googleblog.com/en/developers-guide-to-multi-agent-patterns-in-adk/
"""

from google.adk.agents import ParallelAgent, SequentialAgent, LlmAgent
from typing import List, Optional


def create_parallel_workflow(
    name: str,
    parallel_agents: List[LlmAgent],
    aggregator: Optional[LlmAgent] = None,
) -> SequentialAgent:
    """
    Create a parallel workflow with optional aggregation.

    Each parallel agent must have a unique output_key to prevent
    race conditions when writing to shared state.

    Args:
        name: Name for the workflow
        parallel_agents: Agents to run concurrently
        aggregator: Optional agent to combine results

    Returns:
        SequentialAgent containing parallel + aggregator

    Example:
        >>> workflow = create_parallel_workflow(
        ...     name="analysis_workflow",
        ...     parallel_agents=[adk_checker, cleanup_checker],
        ...     aggregator=result_combiner,
        ... )
    """
    # Validate unique output_keys (CRITICAL for parallel execution)
    output_keys = [a.output_key for a in parallel_agents if hasattr(a, 'output_key')]
    if len(output_keys) != len(set(output_keys)):
        raise ValueError(
            "All parallel agents MUST have unique output_keys to prevent race conditions"
        )

    # Create parallel fan-out
    parallel = ParallelAgent(
        name=f"{name}_parallel",
        sub_agents=parallel_agents,
    )

    # Build workflow
    if aggregator:
        return SequentialAgent(
            name=name,
            sub_agents=[parallel, aggregator],
        )
    else:
        # Return just the parallel agent wrapped in sequential for consistency
        return SequentialAgent(
            name=name,
            sub_agents=[parallel],
        )


def create_aggregator_agent(
    name: str = "aggregator",
    input_keys: List[str] = None,
    output_key: str = "aggregated_result",
    model: str = "gemini-2.0-flash-exp",
) -> LlmAgent:
    """
    Create an aggregator agent that combines parallel results.

    Args:
        name: Agent name
        input_keys: State keys to aggregate (e.g., ["result_a", "result_b"])
        output_key: State key for combined output
        model: LLM model to use

    Returns:
        Configured aggregator LlmAgent
    """
    input_keys = input_keys or []
    input_refs = ", ".join(f"{{{k}}}" for k in input_keys)

    instruction = f"""Aggregate results from parallel agents.

Inputs:
{chr(10).join(f'- {k}: {{{k}}}' for k in input_keys)}

Combine these results into a unified report:
1. Summary of key findings from each source
2. Common issues across sources
3. Unique issues from each source
4. Prioritized recommendations
"""

    return LlmAgent(
        name=name,
        model=model,
        instruction=instruction,
        output_key=output_key,
    )


# ============================================================================
# Example: Multi-Source Analysis
# ============================================================================


def create_multi_source_analysis() -> SequentialAgent:
    """
    Example: Create a parallel analysis workflow.

    Concurrent: Source A, Source B, Source C
    Then: Aggregator combines results
    """
    source_a = LlmAgent(
        name="source_a_analyzer",
        model="gemini-2.0-flash-exp",
        instruction="""Analyze the input from Source A perspective.
        
Input: {user_input}

Output findings specific to Source A analysis.
""",
        output_key="source_a_findings",
    )

    source_b = LlmAgent(
        name="source_b_analyzer",
        model="gemini-2.0-flash-exp",
        instruction="""Analyze the input from Source B perspective.
        
Input: {user_input}

Output findings specific to Source B analysis.
""",
        output_key="source_b_findings",
    )

    source_c = LlmAgent(
        name="source_c_analyzer",
        model="gemini-2.0-flash-exp",
        instruction="""Analyze the input from Source C perspective.
        
Input: {user_input}

Output findings specific to Source C analysis.
""",
        output_key="source_c_findings",
    )

    aggregator = create_aggregator_agent(
        name="result_aggregator",
        input_keys=["source_a_findings", "source_b_findings", "source_c_findings"],
        output_key="aggregated_analysis",
    )

    return create_parallel_workflow(
        name="multi_source_analysis",
        parallel_agents=[source_a, source_b, source_c],
        aggregator=aggregator,
    )


__all__ = [
    "create_parallel_workflow",
    "create_aggregator_agent",
    "create_multi_source_analysis",
]
