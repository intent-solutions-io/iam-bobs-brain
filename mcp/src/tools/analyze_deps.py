"""Analyze dependencies tool."""

import logging
import sys
from pathlib import Path
from typing import List

# Add agents/ to Python path for imports
REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from agents.shared_contracts.tool_outputs import (
    DependencyResult,
    PythonDependencies,
    NodeDependencies,
    TerraformDependencies,
    DependencySummary,
    create_success_result,
    create_error_result,
)

logger = logging.getLogger(__name__)


async def execute(path: str = ".") -> DependencyResult:
    """
    Analyze project dependencies.

    Args:
        path: Project directory to analyze (default: current directory)

    Returns:
        DependencyResult with Python, Node, Terraform dependencies and summary
    """
    base_path = Path(path)

    if not base_path.exists():
        return create_error_result(
            DependencyResult, "analyze_deps", f"Path not found: {path}"
        )

    logger.info(f"Analyzing dependencies in: {path}")

    # Python dependencies
    requirements_list = _parse_requirements(base_path / "requirements.txt")
    pyproject_deps = _parse_pyproject(base_path / "pyproject.toml")

    python = PythonDependencies(
        requirements_txt=requirements_list,
        pyproject_toml=pyproject_deps.get("dependencies", []),
    )

    # Node dependencies
    package_json_data = _parse_package_json(base_path / "package.json")
    node = NodeDependencies(
        dependencies=package_json_data.get("dependencies", {}),
        dev_dependencies=package_json_data.get("devDependencies", {}),
    )

    # Terraform providers
    tf_providers_list = _parse_terraform(base_path)
    terraform = TerraformDependencies(providers=tf_providers_list)

    # Calculate summary
    python_count = len(requirements_list) + len(pyproject_deps.get("dependencies", []))
    node_count = len(package_json_data.get("dependencies", {})) + len(
        package_json_data.get("devDependencies", {})
    )
    terraform_count = len(tf_providers_list)

    summary = DependencySummary(
        python_packages=python_count,
        node_packages=node_count,
        terraform_providers=terraform_count,
    )

    # TODO: Add dependency issue detection (vulnerabilities, duplicates, etc.)
    issues = []

    return create_success_result(
        DependencyResult,
        "analyze_deps",
        path=str(base_path),
        python=python,
        node=node,
        terraform=terraform,
        summary=summary,
        issues=issues,
    )


def _parse_requirements(path: Path) -> List[str]:
    """Parse requirements.txt."""
    if not path.exists():
        return []
    try:
        content = path.read_text()
        deps = []
        for line in content.strip().split("\n"):
            line = line.strip()
            if line and not line.startswith("#"):
                pkg = line.split("==")[0].split(">=")[0].split("<=")[0].split("~=")[0]
                deps.append(pkg.strip())
        return deps
    except Exception:
        return []


def _parse_pyproject(path: Path) -> dict:
    """Parse pyproject.toml."""
    if not path.exists():
        return {}
    try:
        import tomllib
        data = tomllib.loads(path.read_bytes().decode())
        result = {}
        if "tool" in data and "poetry" in data["tool"]:
            poetry = data["tool"]["poetry"]
            if "dependencies" in poetry:
                result["dependencies"] = list(poetry["dependencies"].keys())
        if "project" in data and "dependencies" in data["project"]:
            result["dependencies"] = data["project"]["dependencies"]
        return result
    except Exception:
        return {}


def _parse_package_json(path: Path) -> dict:
    """Parse package.json."""
    if not path.exists():
        return {}
    try:
        import json
        data = json.loads(path.read_text())
        return {
            "dependencies": data.get("dependencies", {}),
            "devDependencies": data.get("devDependencies", {})
        }
    except Exception:
        return {}


def _parse_terraform(base_path: Path) -> List[str]:
    """Find Terraform providers."""
    providers = []
    for tf_file in base_path.glob("**/*.tf"):
        try:
            content = tf_file.read_text()
            for line in content.split("\n"):
                if "provider" in line and "{" in line:
                    parts = line.split('"')
                    if len(parts) >= 2:
                        providers.append(parts[1])
        except Exception:
            continue
    return list(set(providers))
