"""
Cleanup Tools Module

Exports cleanup detection and analysis tools for iam-cleanup agent.
"""

from .cleanup_tools import (
    analyze_structure,
    detect_dead_code,
    detect_unused_dependencies,
    find_code_duplication,
    identify_naming_issues,
    propose_cleanup_task,
)

__all__ = [
    "analyze_structure",
    "detect_dead_code",
    "detect_unused_dependencies",
    "find_code_duplication",
    "identify_naming_issues",
    "propose_cleanup_task",
]
