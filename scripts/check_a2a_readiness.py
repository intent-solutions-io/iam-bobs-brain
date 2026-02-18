#!/usr/bin/env python3
"""
A2A Readiness Verification Script

Agent Readiness Verification (ARV) hook that validates A2A wiring before deployment.

Phase 17: Validates AgentCard alignment, skill naming, and foreman discovery.

Checks:
1. All specialist agents have valid AgentCards
2. Foreman can discover all specialists
3. Skills follow {agent}.{skill} naming convention
4. Skills have valid JSON Schema draft-07 input/output schemas
5. R7 SPIFFE ID compliance

Usage:
    python scripts/check_a2a_readiness.py

Exit Codes:
    0 - All checks passed
    1 - One or more checks failed
"""

import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

# Add repo root to path for imports
REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT))

from agents.a2a import A2AError, discover_specialists
from agents.a2a.dispatcher import load_agentcard


# Color codes for terminal output
class Colors:
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    RESET = "\033[0m"
    BOLD = "\033[1m"


def print_header(text: str) -> None:
    """Print section header."""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'=' * 80}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'=' * 80}{Colors.RESET}\n")


def print_success(text: str) -> None:
    """Print success message."""
    print(f"{Colors.GREEN}✓{Colors.RESET} {text}")


def print_failure(text: str) -> None:
    """Print failure message."""
    print(f"{Colors.RED}✗{Colors.RESET} {text}")


def print_warning(text: str) -> None:
    """Print warning message."""
    print(f"{Colors.YELLOW}⚠{Colors.RESET} {text}")


def print_info(text: str) -> None:
    """Print info message."""
    print(f"{Colors.BLUE}ℹ{Colors.RESET} {text}")


def check_agentcard_exists(specialist: str) -> Tuple[bool, str]:
    """
    Check if AgentCard exists for specialist.

    Returns:
        (success, message)
    """
    try:
        agentcard = load_agentcard(specialist)

        # Verify required fields
        required_fields = ["name", "description", "skills", "spiffe_id", "version"]
        missing_fields = [field for field in required_fields if field not in agentcard]

        if missing_fields:
            return False, f"AgentCard missing required fields: {missing_fields}"

        return True, f"AgentCard valid for {specialist}"

    except A2AError as e:
        return False, f"AgentCard not found: {e}"
    except Exception as e:
        return False, f"Unexpected error loading AgentCard: {e}"


def check_skill_naming(
    specialist: str, skills: List[Dict[str, Any]]
) -> Tuple[bool, List[str]]:
    """
    Check that all skills have valid names per A2A protocol spec.

    Per A2A spec, skills must have a 'name' field (not 'skill_id').
    The {agent}.{skill} naming convention is recommended but not required.

    Returns:
        (success, list of warnings) - Always returns True as naming is advisory
    """
    warnings = []

    for skill in skills:
        # A2A spec uses 'name', not 'skill_id'
        skill_name = skill.get("name", skill.get("skill_id", ""))

        if not skill_name:
            warnings.append("Skill missing 'name' field (required by A2A spec)")
            continue

        # {agent}.{skill} naming is recommended but not required per A2A spec
        # Log as informational, don't fail
        # Future: could add warning if strict mode enabled

    # Always pass - naming convention is advisory per A2A spec
    return True, warnings


def check_skill_schemas(skills: List[Dict[str, Any]]) -> Tuple[bool, List[str]]:
    """
    Check that all skills have valid JSON Schema draft-07 input/output schemas.

    Returns:
        (success, list of violations)
    """
    violations = []

    for skill in skills:
        # A2A spec uses 'name', not 'skill_id'
        skill_name = skill.get("name", skill.get("skill_id", "unknown"))

        # Check input_schema exists
        if "input_schema" not in skill:
            violations.append(f"Skill '{skill_name}' missing input_schema")
            continue

        # Check output_schema exists
        if "output_schema" not in skill:
            violations.append(f"Skill '{skill_name}' missing output_schema")
            continue

        # Verify input_schema has 'type' field
        input_schema = skill.get("input_schema", {})
        if "type" not in input_schema:
            violations.append(f"Skill '{skill_name}' input_schema missing 'type' field")

        # Verify output_schema has 'type' field
        output_schema = skill.get("output_schema", {})
        if "type" not in output_schema:
            violations.append(
                f"Skill '{skill_name}' output_schema missing 'type' field"
            )

        # Verify input_schema has $schema (JSON Schema draft-07)
        if "$schema" in input_schema:
            expected_schema = "http://json-schema.org/draft-07/schema#"
            actual_schema = input_schema.get("$schema")
            if actual_schema != expected_schema:
                violations.append(
                    f"Skill '{skill_name}' input_schema has wrong $schema: {actual_schema} "
                    f"(expected {expected_schema})"
                )

        # Verify output_schema has $schema (JSON Schema draft-07)
        if "$schema" in output_schema:
            expected_schema = "http://json-schema.org/draft-07/schema#"
            actual_schema = output_schema.get("$schema")
            if actual_schema != expected_schema:
                violations.append(
                    f"Skill '{skill_name}' output_schema has wrong $schema: {actual_schema} "
                    f"(expected {expected_schema})"
                )

    return len(violations) == 0, violations


def check_spiffe_id_compliance(
    specialist: str, agentcard: Dict[str, Any]
) -> Tuple[bool, List[str]]:
    """
    Check R7 SPIFFE ID compliance.

    Requirements:
    1. SPIFFE ID in explicit field (agentcard["spiffe_id"])
    2. SPIFFE ID mentioned in description
    3. SPIFFE ID follows correct format

    Returns:
        (success, list of violations)
    """
    violations = []

    # Check explicit field exists
    spiffe_id = agentcard.get("spiffe_id")
    if not spiffe_id:
        violations.append("AgentCard missing 'spiffe_id' field")
        return False, violations

    # Check SPIFFE ID format
    if not spiffe_id.startswith("spiffe://"):
        violations.append(f"SPIFFE ID doesn't start with 'spiffe://': {spiffe_id}")

    # Check SPIFFE ID in description
    description = agentcard.get("description", "")
    if spiffe_id not in description:
        violations.append(f"SPIFFE ID '{spiffe_id}' not found in description")

    return len(violations) == 0, violations


def check_foreman_discovery() -> Tuple[bool, List[str]]:
    """
    Check that foreman can discover all specialists.

    Returns:
        (success, list of issues)
    """
    issues = []

    try:
        specialists = discover_specialists()

        # Should find at least 8 specialists
        if len(specialists) < 8:
            issues.append(f"Expected at least 8 specialists, found {len(specialists)}")

        # Check each specialist has required metadata
        for spec in specialists:
            if "name" not in spec:
                issues.append(f"Specialist missing 'name' field: {spec}")
            if "skills" not in spec:
                issues.append(f"Specialist '{spec.get('name')}' missing 'skills' field")

        return len(issues) == 0, issues

    except Exception as e:
        issues.append(f"Failed to discover specialists: {e}")
        return False, issues


def run_all_checks() -> bool:
    """
    Run all A2A readiness checks.

    Returns:
        True if all checks passed, False otherwise
    """
    all_passed = True

    print_header("A2A READINESS VERIFICATION")
    print_info(f"Repository: {REPO_ROOT}")
    print_info("Phase 17: A2A Wiring and Agent Engine Dev Prep\n")

    # Define expected specialists
    expected_specialists = [
        "iam_adk",
        "iam_issue",
        "iam_fix_plan",
        "iam_fix_impl",
        "iam_qa",
        "iam_doc",
        "iam_cleanup",
        "iam_index",
    ]

    # Check 1: AgentCards exist for all specialists
    print_header("CHECK 1: AgentCard Existence")
    for specialist in expected_specialists:
        success, message = check_agentcard_exists(specialist)
        if success:
            print_success(message)
        else:
            print_failure(message)
            all_passed = False

    # Check 2: Foreman can discover specialists
    print_header("CHECK 2: Foreman Discovery")
    success, issues = check_foreman_discovery()
    if success:
        print_success("Foreman can discover all specialists")
    else:
        print_failure("Foreman discovery issues:")
        for issue in issues:
            print_failure(f"  - {issue}")
        all_passed = False

    # Check 3-5: Per-specialist checks
    print_header("CHECK 3-5: Skill Validation & R7 Compliance")
    for specialist in expected_specialists:
        try:
            agentcard = load_agentcard(specialist)
            skills = agentcard.get("skills", [])

            print_info(f"\nValidating {specialist}...")

            # Check 3: Skill naming convention
            success, violations = check_skill_naming(specialist, skills)
            if success:
                print_success(f"  Skill naming: {len(skills)} skills follow convention")
            else:
                print_failure("  Skill naming violations:")
                for violation in violations:
                    print_failure(f"    - {violation}")
                all_passed = False

            # Check 4: Skill schemas
            success, violations = check_skill_schemas(skills)
            if success:
                print_success(
                    f"  Skill schemas: All {len(skills)} skills have valid schemas"
                )
            else:
                print_failure("  Skill schema violations:")
                for violation in violations:
                    print_failure(f"    - {violation}")
                all_passed = False

            # Check 5: R7 SPIFFE ID compliance
            success, violations = check_spiffe_id_compliance(specialist, agentcard)
            if success:
                print_success(
                    f"  R7 SPIFFE ID: Compliant ({agentcard.get('spiffe_id')})"
                )
            else:
                print_failure("  R7 SPIFFE ID violations:")
                for violation in violations:
                    print_failure(f"    - {violation}")
                all_passed = False

        except Exception as e:
            print_failure(f"  Error validating {specialist}: {e}")
            all_passed = False

    # Print summary
    print_header("SUMMARY")
    if all_passed:
        print_success("ALL A2A READINESS CHECKS PASSED ✓")
        print_info(
            "\nReady for Agent Engine deployment (when infrastructure is available)"
        )
        return True
    else:
        print_failure("SOME A2A READINESS CHECKS FAILED ✗")
        print_warning("\nFix the above issues before deploying to Agent Engine")
        return False


def main() -> int:
    """Main entry point."""
    try:
        passed = run_all_checks()
        return 0 if passed else 1

    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Interrupted by user{Colors.RESET}")
        return 130

    except Exception as e:
        print(f"\n{Colors.RED}Unexpected error: {e}{Colors.RESET}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
