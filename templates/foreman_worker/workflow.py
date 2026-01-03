"""
Foreman-Worker Pattern - Standalone Template

Implements Google's Hierarchical Decomposition pattern with specialized workers.
Reference: https://developers.googleblog.com/en/developers-guide-to-multi-agent-patterns-in-adk/
"""

from google.adk.agents import LlmAgent
from typing import Dict, List, Optional, Any
import logging

logger = logging.getLogger(__name__)


# ============================================================================
# Worker Agent Factories
# ============================================================================


def create_worker(
    name: str,
    role: str,
    instruction: str,
    output_key: str,
    tools: Optional[List] = None,
    model: str = "gemini-2.0-flash-exp",
) -> LlmAgent:
    """
    Create a specialized worker agent.

    Workers are deterministic function agents that:
    - Accept structured input
    - Execute domain-specific tasks
    - Return structured output

    Args:
        name: Agent name (valid Python identifier)
        role: Short description of worker's role
        instruction: System prompt defining behavior
        output_key: State key for worker output
        tools: Domain-specific tools for this worker
        model: LLM model to use

    Returns:
        Configured worker LlmAgent
    """
    return LlmAgent(
        name=name,
        model=model,
        instruction=instruction,
        output_key=output_key,
        tools=tools or [],
    )


def create_worker_registry(workers: List[LlmAgent]) -> Dict[str, LlmAgent]:
    """
    Create a registry mapping worker names to agents.

    Args:
        workers: List of worker agents

    Returns:
        Dict mapping worker names to agents
    """
    return {w.name: w for w in workers}


# ============================================================================
# Delegation Tool Factory
# ============================================================================


def create_delegation_tool(worker_registry: Dict[str, LlmAgent]):
    """
    Create a delegation tool for the foreman.

    This tool allows the foreman to delegate tasks to workers
    and receive their results.

    Args:
        worker_registry: Mapping of worker names to agents

    Returns:
        Delegation tool function
    """

    def delegate_to_worker(worker_name: str, task: dict) -> dict:
        """
        Delegate a task to a specialist worker.

        Args:
            worker_name: Name of the worker to delegate to
            task: Task specification with required inputs

        Returns:
            Worker result or error
        """
        if worker_name not in worker_registry:
            return {
                "status": "error",
                "message": f"Unknown worker: {worker_name}",
                "available_workers": list(worker_registry.keys()),
            }

        worker = worker_registry[worker_name]
        logger.info(f"Delegating to {worker_name}: {task}")

        # In production, this would execute the worker
        # For template, we return a placeholder
        return {
            "status": "delegated",
            "worker": worker_name,
            "task": task,
            "message": f"Task delegated to {worker_name}. Use Runner to execute.",
        }

    return delegate_to_worker


# ============================================================================
# Foreman Agent Factory
# ============================================================================


def create_foreman(
    name: str,
    workers: List[LlmAgent],
    model: str = "gemini-2.0-flash-exp",
) -> LlmAgent:
    """
    Create a foreman agent that orchestrates workers.

    The foreman:
    - Receives high-level requests
    - Decomposes into worker tasks
    - Delegates to appropriate workers
    - Aggregates results

    Args:
        name: Foreman agent name
        workers: List of worker agents to coordinate
        model: LLM model to use

    Returns:
        Configured foreman LlmAgent
    """
    # Build worker capability description
    worker_descriptions = []
    for w in workers:
        output_key = getattr(w, 'output_key', 'result')
        worker_descriptions.append(f"- {w.name}: output_key='{output_key}'")

    worker_list = "\n".join(worker_descriptions)

    instruction = f"""You are a foreman agent that orchestrates specialist workers.

## Your Role
- Analyze incoming requests
- Decompose complex tasks into worker tasks
- Delegate to appropriate workers
- Aggregate and return results

## Available Workers
{worker_list}

## Delegation Patterns

### Single Worker Pattern
When task clearly belongs to one domain:
1. Identify the right worker
2. Delegate with clear task specification
3. Return worker result

### Sequential Pattern
When tasks depend on each other:
1. Delegate to first worker
2. Use result as input to next worker
3. Continue chain

### Parallel Pattern
When tasks are independent:
1. Identify all required workers
2. Delegate to all concurrently
3. Aggregate results

## Constraints
- NEVER execute worker tasks yourself
- ALWAYS delegate to appropriate worker
- Validate worker outputs before aggregating
- Return structured JSON responses
"""

    # Create worker registry and delegation tool
    registry = create_worker_registry(workers)
    delegation_tool = create_delegation_tool(registry)

    return LlmAgent(
        name=name,
        model=model,
        instruction=instruction,
        tools=[delegation_tool],
    )


# ============================================================================
# Example: Analysis Department
# ============================================================================


def create_analysis_department():
    """
    Example: Create a foreman with analysis workers.

    Foreman coordinates:
    - Code analyzer
    - Security reviewer
    - Documentation checker
    """
    code_analyzer = create_worker(
        name="code_analyzer",
        role="Code analysis specialist",
        instruction="""You analyze code for quality and patterns.

Task: {task}

Output structured analysis:
{
  "quality_score": 0-100,
  "issues": [...],
  "recommendations": [...]
}
""",
        output_key="code_analysis",
    )

    security_reviewer = create_worker(
        name="security_reviewer",
        role="Security analysis specialist",
        instruction="""You review code for security vulnerabilities.

Task: {task}

Output structured review:
{
  "risk_level": "LOW|MEDIUM|HIGH|CRITICAL",
  "vulnerabilities": [...],
  "mitigations": [...]
}
""",
        output_key="security_review",
    )

    doc_checker = create_worker(
        name="doc_checker",
        role="Documentation analysis specialist",
        instruction="""You check documentation completeness.

Task: {task}

Output structured check:
{
  "coverage": 0-100,
  "missing_docs": [...],
  "suggestions": [...]
}
""",
        output_key="doc_check",
    )

    foreman = create_foreman(
        name="analysis_foreman",
        workers=[code_analyzer, security_reviewer, doc_checker],
    )

    return {
        "foreman": foreman,
        "workers": [code_analyzer, security_reviewer, doc_checker],
    }


__all__ = [
    "create_worker",
    "create_worker_registry",
    "create_delegation_tool",
    "create_foreman",
    "create_analysis_department",
]
