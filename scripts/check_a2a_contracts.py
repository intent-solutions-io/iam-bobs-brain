#!/usr/bin/env python3
"""
A2A Contract Validation Script

Validates AgentCard JSON files for schema compliance and A2A contract correctness.
Implements quality gates from 6767-DR-STND-a2a-quality-gates.md.

Usage:
    python3 scripts/check_a2a_contracts.py [agentcard_path]
    python3 scripts/check_a2a_contracts.py --all
    python3 scripts/check_a2a_contracts.py --check-implementation agents/iam_adk

Validation Layers:
1. JSON Syntax: Valid JSON structure
2. Required Fields: name, version, spiffe_id, skills present
3. Schema Compliance: Skills have valid input/output schemas
4. 6767 Standards: Follows naming conventions and best practices
5. Implementation Match (optional): AgentCard matches actual agent.py

Exit Codes:
    0 - All validations passed
    1 - Validation errors found
    2 - Script error (file not found, etc.)
"""

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# ============================================================================
# VALIDATION RULES (6767 Standards)
# ============================================================================

REQUIRED_AGENTCARD_FIELDS = [
    "name",
    "description",
    "version",
    "spiffe_id",
    "skills"
]

REQUIRED_SKILL_FIELDS = [
    "id",  # A2A v0.3.0 uses "id" instead of "skill_id"
    "name",
    "description",
    "input_schema",
    "output_schema"
]

# Skill naming pattern: {department}.{verb}_{noun}
SKILL_ID_PATTERN = re.compile(r"^[a-z]+\.[a-z]+_[a-z_]+$")

# Semantic version pattern: major.minor.patch
VERSION_PATTERN = re.compile(r"^\d+\.\d+\.\d+$")

# SPIFFE ID pattern
SPIFFE_ID_PATTERN = re.compile(
    r"^spiffe://[a-z0-9.-]+/agent/[a-z0-9-]+/[a-z]+/[a-z0-9-]+/\d+\.\d+\.\d+$"
)


# ============================================================================
# VALIDATION FUNCTIONS
# ============================================================================

def validate_json_syntax(file_path: Path) -> Tuple[bool, str, Optional[Dict]]:
    """
    Layer 1: Validate JSON syntax.

    Returns: (valid, message, parsed_json)
    """
    try:
        with open(file_path) as f:
            data = json.load(f)
        return True, "✅ Valid JSON syntax", data
    except json.JSONDecodeError as e:
        return False, f"❌ Invalid JSON: {e}", None
    except FileNotFoundError:
        return False, f"❌ File not found: {file_path}", None


def validate_required_fields(data: Dict) -> Tuple[bool, List[str]]:
    """
    Layer 2: Validate required fields present.

    Returns: (valid, list_of_errors)
    """
    errors = []

    for field in REQUIRED_AGENTCARD_FIELDS:
        if field not in data:
            errors.append(f"Missing required field: '{field}'")

    return len(errors) == 0, errors


def validate_skills(skills: List[Dict]) -> Tuple[bool, List[str]]:
    """
    Layer 3: Validate skill definitions.

    Returns: (valid, list_of_errors)
    """
    errors = []

    if not isinstance(skills, list):
        return False, ["Skills must be an array"]

    if len(skills) == 0:
        errors.append("No skills defined (must have at least one)")

    for idx, skill in enumerate(skills):
        skill_prefix = f"skills[{idx}]"

        # Check required skill fields
        for field in REQUIRED_SKILL_FIELDS:
            if field not in skill:
                errors.append(f"{skill_prefix}: Missing required field '{field}'")

        # Validate skill_id format
        if "skill_id" in skill:
            if not SKILL_ID_PATTERN.match(skill["skill_id"]):
                errors.append(
                    f"{skill_prefix}: Invalid skill_id format. "
                    "Expected: {{department}}.{{verb}}_{{noun}} (e.g., 'iam.check_compliance')"
                )

        # Validate schemas are objects (not empty {})
        for schema_field in ["input_schema", "output_schema"]:
            if schema_field in skill:
                schema = skill[schema_field]
                if not isinstance(schema, dict):
                    errors.append(f"{skill_prefix}.{schema_field}: Must be an object")
                elif len(schema) == 0:
                    errors.append(
                        f"{skill_prefix}.{schema_field}: Empty schema not allowed. "
                        "Define explicit type and properties."
                    )
                elif "type" not in schema:
                    errors.append(f"{skill_prefix}.{schema_field}: Missing 'type' field")

    return len(errors) == 0, errors


def validate_6767_standards(data: Dict) -> Tuple[bool, List[str]]:
    """
    Layer 4: Validate compliance with 6767 standards.

    Returns: (valid, list_of_errors)
    """
    errors = []

    # Validate version format
    if "version" in data:
        if not VERSION_PATTERN.match(data["version"]):
            errors.append(
                f"Invalid version format: '{data['version']}'. "
                "Expected semantic version (e.g., '0.1.0')"
            )

    # Validate SPIFFE ID format
    if "spiffe_id" in data:
        if not SPIFFE_ID_PATTERN.match(data["spiffe_id"]):
            errors.append(
                f"Invalid SPIFFE ID format: '{data['spiffe_id']}'. "
                "Expected: spiffe://domain/agent/name/env/region/version"
            )

    # Check that SPIFFE ID version matches AgentCard version
    if "spiffe_id" in data and "version" in data:
        spiffe_version = data["spiffe_id"].split("/")[-1]
        if spiffe_version != data["version"]:
            errors.append(
                f"Version mismatch: AgentCard version '{data['version']}' "
                f"does not match SPIFFE ID version '{spiffe_version}'"
            )

    return len(errors) == 0, errors


def validate_agentcard(file_path: Path, check_implementation: bool = False) -> Tuple[bool, List[str]]:
    """
    Run all validation layers on an AgentCard.

    Returns: (valid, list_of_all_errors)
    """
    all_errors = []

    # Layer 1: JSON Syntax
    valid, message, data = validate_json_syntax(file_path)
    if not valid:
        return False, [message]

    # Layer 2: Required Fields
    valid, errors = validate_required_fields(data)
    if not valid:
        all_errors.extend(errors)

    # Layer 3: Skills
    if "skills" in data:
        valid, errors = validate_skills(data["skills"])
        if not valid:
            all_errors.extend(errors)

    # Layer 4: 6767 Standards
    valid, errors = validate_6767_standards(data)
    if not valid:
        all_errors.extend(errors)

    # Layer 5: Implementation Match (optional, not yet implemented)
    if check_implementation:
        all_errors.append(
            "⚠️  Implementation validation not yet implemented (future enhancement)"
        )

    return len(all_errors) == 0, all_errors


# ============================================================================
# MAIN EXECUTION
# ============================================================================

def find_all_agentcards(root_dir: Path = Path(".")) -> List[Path]:
    """Find all AgentCard JSON files in agents/ directory."""
    agentcards = []
    agents_dir = root_dir / "agents"

    if not agents_dir.exists():
        return []

    for agent_dir in agents_dir.iterdir():
        if agent_dir.is_dir():
            card_path = agent_dir / ".well-known" / "agent-card.json"
            if card_path.exists():
                agentcards.append(card_path)

    return agentcards


def main():
    parser = argparse.ArgumentParser(
        description="Validate A2A AgentCard contracts",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )

    parser.add_argument(
        "agentcard_path",
        nargs="?",
        type=Path,
        help="Path to AgentCard JSON file (e.g., agents/iam-adk/.well-known/agent-card.json)"
    )

    parser.add_argument(
        "--all",
        action="store_true",
        help="Validate all AgentCards in agents/ directory"
    )

    parser.add_argument(
        "--check-implementation",
        action="store_true",
        help="Cross-check AgentCard against agent.py implementation (future)"
    )

    args = parser.parse_args()

    # Determine which AgentCards to validate
    if args.all:
        agentcards = find_all_agentcards()
        if not agentcards:
            print("❌ No AgentCards found in agents/ directory")
            return 2
    elif args.agentcard_path:
        agentcards = [args.agentcard_path]
    else:
        parser.print_help()
        return 2

    # Validate each AgentCard
    print(f"\n{'='*70}")
    print("A2A Contract Validation")
    print(f"{'='*70}\n")

    total_errors = 0
    results = []

    for card_path in agentcards:
        print(f"📄 Validating: {card_path}")

        valid, errors = validate_agentcard(card_path, args.check_implementation)

        if valid:
            print("   ✅ PASSED\n")
            results.append((str(card_path), True, []))
        else:
            print("   ❌ FAILED")
            for error in errors:
                print(f"      • {error}")
            print()
            results.append((str(card_path), False, errors))
            total_errors += len(errors)

    # Summary
    print(f"{'='*70}")
    print("Summary")
    print(f"{'='*70}")

    passed = sum(1 for _, valid, _ in results if valid)
    failed = len(results) - passed

    print(f"\nTotal AgentCards: {len(results)}")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")

    if total_errors > 0:
        print(f"\nTotal Errors: {total_errors}")
        print("\n❌ Validation FAILED - Fix errors above")
        return 1
    else:
        print("\n✅ All validations PASSED")
        return 0


if __name__ == "__main__":
    sys.exit(main())
