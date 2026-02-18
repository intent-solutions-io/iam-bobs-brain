"""
Foreman orchestration tools for iam-senior-adk-devops-lead.

These tools enable the foreman to:
- Delegate tasks to iam-* specialists
- Create and manage task plans
- Analyze repository state
- Aggregate results from multiple agents
"""

from .delegation import delegate_to_specialist
from .planning import aggregate_results, create_task_plan
from .repository import analyze_repository

__all__ = [
    "aggregate_results",
    "analyze_repository",
    "create_task_plan",
    "delegate_to_specialist",
]
