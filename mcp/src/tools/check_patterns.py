"""Check patterns tool - validates code against ADK Hard Mode rules."""

import logging
import sys
from pathlib import Path
from typing import Dict, List, Literal

# Add agents/ to Python path for imports
REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from agents.shared_contracts.tool_outputs import (
    ComplianceResult,
    Violation,
    create_success_result,
    create_error_result,
)

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


async def execute(path: str = ".", rules: List[str] = None) -> ComplianceResult:
    """
    Check code against ADK Hard Mode rules.

    Args:
        path: Directory to check (default: current directory)
        rules: List of rule IDs to check (default: all rules)

    Returns:
        ComplianceResult with violations, warnings, and compliance score
    """
    base_path = Path(path)

    if not base_path.exists():
        return create_error_result(
            ComplianceResult, "check_patterns", f"Path not found: {path}"
        )

    rules = rules or list(RULE_CHECKS.keys())

    logger.info(f"Checking patterns in {path} for rules: {rules}")

    violations_list = []
    warnings_list = []
    passed_list = []

    for rule_id in rules:
        if rule_id not in RULE_CHECKS:
            warnings_list.append(f"Unknown rule: {rule_id}")
            continue

        rule = RULE_CHECKS[rule_id]
        rule_violations = _check_rule(base_path, rule_id, rule)

        if rule_violations:
            violations_list.extend(rule_violations)
        else:
            passed_list.append(rule_id)

    # Calculate compliance score
    total_rules = len([r for r in rules if r in RULE_CHECKS])
    compliance_score = (len(passed_list) / total_rules * 100) if total_rules > 0 else 0.0

    # Determine risk level based on violations
    risk_level = _calculate_risk_level(violations_list)

    # Determine status
    status: Literal["COMPLIANT", "VIOLATIONS_FOUND"] = (
        "COMPLIANT" if not violations_list else "VIOLATIONS_FOUND"
    )

    return create_success_result(
        ComplianceResult,
        "check_patterns",
        status=status,
        violations=violations_list,
        warnings=warnings_list,
        passed=passed_list,
        compliance_score=compliance_score,
        risk_level=risk_level,
        path=str(base_path),
        rules_checked=rules,
    )


def _check_rule(base_path: Path, rule_id: str, rule: dict) -> List[Violation]:
    """Check a single rule."""
    violations = []

    if "forbidden" in rule:
        for forbidden in rule["forbidden"]:
            matches = _find_pattern(base_path, forbidden, "*.py")
            for match in matches:
                violations.append(
                    Violation(
                        rule=rule_id,
                        rule_name=rule["name"],
                        type="forbidden_import",
                        pattern=forbidden,
                        file=match["file"],
                        line=match["line"],
                        text=match["text"],
                    )
                )

    if "forbidden_in_service" in rule:
        service_path = base_path / "service"
        if service_path.exists():
            for forbidden in rule["forbidden_in_service"]:
                matches = _find_pattern(service_path, forbidden, "*.py")
                for match in matches:
                    violations.append(
                        Violation(
                            rule=rule_id,
                            rule_name=rule["name"],
                            type="forbidden_in_service",
                            pattern=forbidden,
                            file=match["file"],
                            line=match["line"],
                            text=match["text"],
                        )
                    )

    return violations


def _calculate_risk_level(
    violations: List[Violation],
) -> Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]:
    """Calculate overall risk level from violations."""
    if not violations:
        return "LOW"

    # Count critical violations (R1, R2 - framework violations)
    critical_rules = {"R1", "R2"}
    critical_count = sum(
        1 for v in violations if v.rule in critical_rules
    )

    if critical_count > 0:
        return "CRITICAL"
    elif len(violations) >= 10:
        return "HIGH"
    elif len(violations) >= 3:
        return "MEDIUM"
    else:
        return "LOW"


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
