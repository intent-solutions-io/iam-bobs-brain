"""Analyze dependencies tool."""

import logging
from pathlib import Path
from typing import List

logger = logging.getLogger(__name__)


async def execute(path: str = ".") -> dict:
    """Analyze project dependencies."""
    base_path = Path(path)

    if not base_path.exists():
        return {"error": f"Path not found: {path}"}

    logger.info(f"Analyzing dependencies in: {path}")

    result = {
        "path": str(base_path),
        "python": {},
        "node": {},
        "terraform": {}
    }

    # Python
    requirements = _parse_requirements(base_path / "requirements.txt")
    if requirements:
        result["python"]["requirements.txt"] = requirements

    pyproject = _parse_pyproject(base_path / "pyproject.toml")
    if pyproject:
        result["python"]["pyproject.toml"] = pyproject

    # Node
    package_json = _parse_package_json(base_path / "package.json")
    if package_json:
        result["node"]["package.json"] = package_json

    # Terraform
    tf_providers = _parse_terraform(base_path)
    if tf_providers:
        result["terraform"]["providers"] = tf_providers

    result["summary"] = {
        "python_packages": len(requirements) + len(pyproject.get("dependencies", [])),
        "node_packages": len(package_json.get("dependencies", {})) + len(package_json.get("devDependencies", {})),
        "terraform_providers": len(tf_providers)
    }

    return result


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
