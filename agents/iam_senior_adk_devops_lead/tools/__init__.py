"""
Foreman orchestration tools for iam-senior-adk-devops-lead.

These tools enable the foreman to:
- Delegate tasks to iam-* specialists
- Create and manage task plans
- Analyze repository state
- Aggregate results from multiple agents
"""

from .delegation import delegate_to_specialist
from .planning import create_task_plan, aggregate_results
from .repository import analyze_repository

__all__ = [
    "delegate_to_specialist",
    "create_task_plan",
    "aggregate_results",
    "analyze_repository",
]