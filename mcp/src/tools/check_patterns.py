"""Check patterns tool - validates code against ADK Hard Mode rules."""

import logging
from pathlib import Path
from typing import Dict, List

logger = logging.getLogger(__name__)

RULE_CHECKS = {
    "R1": {
        "name": "ADK-Only",
        "description": "No LangChain, CrewAI, or custom frameworks",
        "forbidden": ["langchain", "crewai", "autogen", "llama_index"],
    },
    "R2": {
        "name": "Agent Engine Runtime",
        "description": "Must use Vertex AI Agent Engine",
        "required": ["google.adk", "vertexai"],
    },
    "R3": {
        "name": "Gateway Separation",
        "description": "No Runner in service/",
        "forbidden_in_service": ["Runner", "InMemoryRunner"],
    },
    "R5": {
        "name": "Dual Memory",
        "description": "VertexAiSessionService + VertexAiMemoryBankService",
        "required_in_agents": ["VertexAiSessionService"],
    },
    "R7": {
        "name": "SPIFFE ID",
        "description": "Identity propagation",
        "patterns": ["spiffe", "identity", "caller"],
    },
    "R8": {
        "name": "Drift Detection",
        "description": "CI blocks forbidden imports",
        "check_ci": True,
    }
}


async def execute(path: str = ".", rules: List[str] = None) -> dict:
    """Check code against ADK patterns."""
    base_path = Path(path)

    if not base_path.exists():
        return {"error": f"Path not found: {path}"}

    rules = rules or list(RULE_CHECKS.keys())

    logger.info(f"Checking patterns in {path} for rules: {rules}")

    results = {
        "path": str(base_path),
        "rules_checked": rules,
        "violations": [],
        "warnings": [],
        "passed": [],
        "compliance_score": 0.0
    }

    for rule_id in rules:
        if rule_id not in RULE_CHECKS:
            results["warnings"].append(f"Unknown rule: {rule_id}")
            continue

        rule = RULE_CHECKS[rule_id]
        violations = _check_rule(base_path, rule_id, rule)

        if violations:
            results["violations"].extend(violations)
        else:
            results["passed"].append(rule_id)

    total_rules = len([r for r in rules if r in RULE_CHECKS])
    if total_rules > 0:
        results["compliance_score"] = len(results["passed"]) / total_rules * 100

    results["status"] = "COMPLIANT" if not results["violations"] else "VIOLATIONS_FOUND"

    return results


def _check_rule(base_path: Path, rule_id: str, rule: dict) -> List[dict]:
    """Check a single rule."""
    violations = []

    if "forbidden" in rule:
        for forbidden in rule["forbidden"]:
            matches = _find_pattern(base_path, forbidden, "*.py")
            for match in matches:
                violations.append({
                    "rule": rule_id,
                    "rule_name": rule["name"],
                    "type": "forbidden_import",
                    "pattern": forbidden,
                    "file": match["file"],
                    "line": match["line"],
                    "text": match["text"]
                })

    if "forbidden_in_service" in rule:
        service_path = base_path / "service"
        if service_path.exists():
            for forbidden in rule["forbidden_in_service"]:
                matches = _find_pattern(service_path, forbidden, "*.py")
                for match in matches:
                    violations.append({
                        "rule": rule_id,
                        "rule_name": rule["name"],
                        "type": "forbidden_in_service",
                        "pattern": forbidden,
                        "file": match["file"],
                        "line": match["line"],
                        "text": match["text"]
                    })

    return violations


def _find_pattern(base_path: Path, pattern: str, file_pattern: str) -> List[dict]:
    """Find pattern matches in files."""
    matches = []
    for file_path in base_path.rglob(file_pattern):
        if ".git" in str(file_path) or "__pycache__" in str(file_path):
            continue
        try:
            content = file_path.read_text()
            for line_num, line in enumerate(content.split("\n"), 1):
                if pattern.lower() in line.lower():
                    matches.append({
                        "file": str(file_path),
                        "line": line_num,
                        "text": line.strip()[:100]
                    })
        except Exception:
            continue
    return matches
