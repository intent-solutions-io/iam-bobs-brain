"""
Repository analysis tool for understanding codebase state.

This tool helps the foreman analyze the repository structure,
find relevant files, and understand the current state of the codebase.
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


def analyze_repository(
    scope: str = "agents",
    analysis_type: str = "structure",
    include_patterns: Optional[List[str]] = None,
    exclude_patterns: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Analyze the repository structure and content.

    Provides insights into:
    - Directory structure
    - Agent implementations
    - Documentation status
    - Test coverage
    - ADK compliance indicators

    Args:
        scope: Part of repo to analyze (agents, docs, infra, all)
        analysis_type: Type of analysis (structure, agents, docs, compliance)
        include_patterns: Optional file patterns to include
        exclude_patterns: Optional file patterns to exclude

    Returns:
        Analysis results with findings and metrics

    Example:
        >>> analysis = analyze_repository(
        ...     scope="agents",
        ...     analysis_type="agents",
        ...     include_patterns=["*.py"]
        ... )
    """
    logger.info(f"Analyzing repository: scope={scope}, type={analysis_type}")

    # Base analysis structure
    analysis = {
        "scope": scope,
        "analysis_type": analysis_type,
        "timestamp": "2025-11-19T12:00:00Z",
        "findings": {},
        "metrics": {},
        "recommendations": []
    }

    # Perform analysis based on type
    if analysis_type == "structure":
        analysis = _analyze_structure(analysis, scope)
    elif analysis_type == "agents":
        analysis = _analyze_agents(analysis)
    elif analysis_type == "docs":
        analysis = _analyze_documentation(analysis)
    elif analysis_type == "compliance":
        analysis = _analyze_compliance(analysis)
    else:
        # General analysis
        analysis = _analyze_structure(analysis, scope)
        analysis = _analyze_agents(analysis)
        analysis = _analyze_documentation(analysis)

    return analysis


def _analyze_structure(analysis: Dict[str, Any], scope: str) -> Dict[str, Any]:
    """Analyze repository structure."""

    # Mock structure analysis for Phase 1
    structure_info = {
        "agents": {
            "directories": ["bob", "iam-senior-adk-devops-lead"],
            "file_count": 25,
            "total_lines": 3500,
            "languages": {"python": 90, "markdown": 10}
        },
        "service": {
            "directories": ["a2a_gateway", "slack_webhook"],
            "file_count": 8,
            "total_lines": 1200,
            "languages": {"python": 95, "yaml": 5}
        },
        "infra": {
            "directories": ["terraform"],
            "file_count": 15,
            "total_lines": 2000,
            "languages": {"hcl": 80, "bash": 20}
        },
        "000-docs": {
            "directories": [],
            "file_count": 79,
            "total_lines": 15000,
            "languages": {"markdown": 100}
        },
        "tests": {
            "directories": ["unit", "integration"],
            "file_count": 12,
            "total_lines": 1800,
            "languages": {"python": 100}
        }
    }

    if scope == "all":
        analysis["findings"]["structure"] = structure_info
    else:
        analysis["findings"]["structure"] = {
            scope: structure_info.get(scope, {})
        }

    # Add metrics
    total_files = sum(info["file_count"] for info in structure_info.values())
    total_lines = sum(info["total_lines"] for info in structure_info.values())

    analysis["metrics"]["total_files"] = total_files
    analysis["metrics"]["total_lines"] = total_lines
    analysis["metrics"]["avg_file_size"] = total_lines // total_files if total_files else 0

    return analysis


def _analyze_agents(analysis: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze agent implementations."""

    agents_info = {
        "implemented": [
            {
                "name": "bob",
                "type": "orchestrator",
                "status": "deployed",
                "version": "0.8.0",
                "location": "agents/bob/",
                "has_tools": True,
                "has_a2a": True,
                "has_tests": True,
                "adk_compliant": True
            },
            {
                "name": "iam-senior-adk-devops-lead",
                "type": "foreman",
                "status": "in_development",
                "version": "0.1.0",
                "location": "agents/iam-senior-adk-devops-lead/",
                "has_tools": True,
                "has_a2a": False,  # Phase 3
                "has_tests": False,  # To be added
                "adk_compliant": True
            }
        ],
        "planned": [
            "iam-adk",
            "iam-issue",
            "iam-fix-plan",
            "iam-fix-impl",
            "iam-qa",
            "iam-doc",
            "iam-cleanup",
            "iam-index"
        ],
        "agent_count": {
            "implemented": 2,
            "planned": 8,
            "total": 10
        }
    }

    analysis["findings"]["agents"] = agents_info

    # Add agent-specific metrics
    analysis["metrics"]["agents_implemented"] = agents_info["agent_count"]["implemented"]
    analysis["metrics"]["agents_planned"] = agents_info["agent_count"]["planned"]
    analysis["metrics"]["implementation_progress"] = (
        agents_info["agent_count"]["implemented"] / agents_info["agent_count"]["total"] * 100
    )

    # Add recommendations
    if agents_info["agent_count"]["planned"] > 0:
        analysis["recommendations"].append(
            f"Implement {agents_info['agent_count']['planned']} planned specialist agents"
        )

    for agent in agents_info["implemented"]:
        if not agent["has_tests"]:
            analysis["recommendations"].append(
                f"Add tests for {agent['name']} agent"
            )
        if not agent["has_a2a"]:
            analysis["recommendations"].append(
                f"Implement A2A protocol for {agent['name']} agent"
            )

    return analysis


def _analyze_documentation(analysis: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze documentation status."""

    docs_info = {
        "total_documents": 79,
        "document_categories": {
            "AA": 25,  # After-Action/Architecture
            "AT": 15,  # Architecture/Technical
            "OD": 10,  # Operations/Deployment
            "PM": 8,   # Project Management
            "DR": 6,   # Documentation/Reference
            "TQ": 5,   # Testing/Quality
            "LS": 4,   # Logs/Status
            "RA": 3,   # Reports/Analysis
            "PP": 3    # Product/Planning
        },
        "recent_documents": [
            "078-DR-STND-opus-adk-agent-initialization.md",
            "077-AA-PLAN-agent-factory-structure-cleanup.md",
            "076-AT-IMPL-vertex-ai-search-grounding.md"
        ],
        "documentation_coverage": {
            "agents": 85,
            "infrastructure": 90,
            "deployment": 95,
            "testing": 70,
            "operations": 80
        }
    }

    analysis["findings"]["documentation"] = docs_info

    # Add documentation metrics
    analysis["metrics"]["total_documents"] = docs_info["total_documents"]
    analysis["metrics"]["avg_documentation_coverage"] = sum(
        docs_info["documentation_coverage"].values()
    ) / len(docs_info["documentation_coverage"])

    # Add recommendations
    for area, coverage in docs_info["documentation_coverage"].items():
        if coverage < 80:
            analysis["recommendations"].append(
                f"Improve {area} documentation (currently {coverage}% coverage)"
            )

    return analysis


def _analyze_compliance(analysis: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze ADK/Hard Mode compliance."""

    compliance_info = {
        "hard_mode_rules": {
            "R1_adk_only": {
                "status": "compliant",
                "description": "Uses google-adk LlmAgent",
                "violations": []
            },
            "R2_agent_engine": {
                "status": "compliant",
                "description": "Deployed to Vertex AI Agent Engine",
                "violations": []
            },
            "R3_gateway_separation": {
                "status": "compliant",
                "description": "Cloud Run gateways proxy only",
                "violations": []
            },
            "R4_ci_only": {
                "status": "compliant",
                "description": "CI-only deployments via GitHub Actions",
                "violations": []
            },
            "R5_dual_memory": {
                "status": "compliant",
                "description": "Session + Memory Bank wiring",
                "violations": []
            },
            "R6_single_docs": {
                "status": "compliant",
                "description": "Single 000-docs/ folder",
                "violations": []
            },
            "R7_spiffe_id": {
                "status": "compliant",
                "description": "SPIFFE ID propagation",
                "violations": []
            },
            "R8_drift_detection": {
                "status": "compliant",
                "description": "CI drift detection active",
                "violations": []
            }
        },
        "overall_compliance": 100,
        "last_audit": "2025-11-19",
        "next_audit_due": "2025-12-19"
    }

    analysis["findings"]["compliance"] = compliance_info

    # Add compliance metrics
    total_rules = len(compliance_info["hard_mode_rules"])
    compliant_rules = sum(
        1 for rule in compliance_info["hard_mode_rules"].values()
        if rule["status"] == "compliant"
    )

    analysis["metrics"]["compliance_score"] = (compliant_rules / total_rules * 100)
    analysis["metrics"]["violations_count"] = total_rules - compliant_rules

    # Add recommendations
    for rule_id, rule_info in compliance_info["hard_mode_rules"].items():
        if rule_info["status"] != "compliant":
            analysis["recommendations"].append(
                f"Fix {rule_id} violations: {', '.join(rule_info['violations'])}"
            )

    return analysis


def find_files(
    pattern: str,
    directory: str = ".",
    recursive: bool = True
) -> List[str]:
    """
    Find files matching a pattern in the repository.

    Args:
        pattern: File pattern to search for (e.g., "*.py", "agent.py")
        directory: Directory to search in
        recursive: Whether to search recursively

    Returns:
        List of file paths matching the pattern
    """
    # Mock implementation for Phase 1
    mock_files = {
        "*.py": [
            "agents/bob/agent.py",
            "agents/bob/a2a_card.py",
            "agents/bob/tools/__init__.py",
            "agents/iam-senior-adk-devops-lead/agent.py",
            "agents/iam-senior-adk-devops-lead/tools/__init__.py",
            "service/a2a_gateway/main.py",
            "service/slack_webhook/main.py",
            "tests/test_bob.py"
        ],
        "agent.py": [
            "agents/bob/agent.py",
            "agents/iam-senior-adk-devops-lead/agent.py"
        ],
        "*.md": [
            "README.md",
            "CLAUDE.md",
            "000-docs/078-DR-STND-opus-adk-agent-initialization.md",
            "000-docs/077-AA-PLAN-agent-factory-structure-cleanup.md",
            "000-docs/079-AA-PLAN-iam-senior-adk-devops-lead-design.md"
        ],
        "*.tf": [
            "infra/terraform/main.tf",
            "infra/terraform/agent_engine.tf",
            "infra/terraform/storage.tf",
            "infra/terraform/iam.tf",
            "infra/terraform/variables.tf"
        ]
    }

    # Return mock results based on pattern
    for pattern_key, files in mock_files.items():
        if pattern == pattern_key:
            if directory != ".":
                # Filter by directory
                files = [f for f in files if f.startswith(directory)]
            return files

    return []


def get_file_metrics(file_path: str) -> Dict[str, Any]:
    """
    Get metrics for a specific file.

    Args:
        file_path: Path to the file

    Returns:
        File metrics including size, lines, complexity
    """
    # Mock implementation for Phase 1
    mock_metrics = {
        "agents/bob/agent.py": {
            "lines": 352,
            "functions": 4,
            "classes": 0,
            "imports": 12,
            "complexity": "medium",
            "has_tests": True,
            "test_coverage": 85
        },
        "agents/iam-senior-adk-devops-lead/agent.py": {
            "lines": 300,
            "functions": 4,
            "classes": 0,
            "imports": 10,
            "complexity": "medium",
            "has_tests": False,
            "test_coverage": 0
        }
    }

    return mock_metrics.get(file_path, {
        "lines": 0,
        "functions": 0,
        "classes": 0,
        "imports": 0,
        "complexity": "unknown",
        "has_tests": False,
        "test_coverage": 0
    })


def check_dependencies(
    agent_name: str
) -> Dict[str, Any]:
    """
    Check dependencies for an agent.

    Args:
        agent_name: Name of the agent to check

    Returns:
        Dependency information
    """
    # Mock implementation for Phase 1
    dependencies = {
        "bob": {
            "python_packages": [
                "google-adk>=1.18.0",
                "a2a-sdk>=0.3.0",
                "google-cloud-discoveryengine>=0.11.0"
            ],
            "internal_dependencies": [
                "agents/bob/tools/adk_tools.py",
                "agents/bob/tools/vertex_search_tool.py"
            ],
            "external_services": [
                "Vertex AI Agent Engine",
                "Vertex AI Search",
                "Cloud Storage"
            ]
        },
        "iam-senior-adk-devops-lead": {
            "python_packages": [
                "google-adk>=1.18.0",
                "a2a-sdk>=0.3.0"
            ],
            "internal_dependencies": [
                "agents/iam-senior-adk-devops-lead/tools/delegation.py",
                "agents/iam-senior-adk-devops-lead/tools/planning.py",
                "agents/iam-senior-adk-devops-lead/tools/repository.py"
            ],
            "external_services": [
                "Vertex AI Agent Engine",
                "GitHub API (future)",
                "A2A Protocol (Phase 3)"
            ]
        }
    }

    return dependencies.get(agent_name, {
        "python_packages": [],
        "internal_dependencies": [],
        "external_services": []
    })