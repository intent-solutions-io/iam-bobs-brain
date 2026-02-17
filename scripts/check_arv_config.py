#!/usr/bin/env python3
"""
ARV Check: Configuration and Feature Flag Defaults

Validates that feature flags and configuration defaults follow safety principles:
- External integrations default OFF (ENABLED=false)
- Dry-run modes default ON (DRY_RUN=true)
- Destructive operations default OFF
- No hard-coded credentials or secrets

Part of: SPEC-ALIGN-ARV-EXPANSION (S3)
Rule: Feature Flag Defaults (Department Convention)

Exit codes:
  0: All checks passed
  1: Violations found
"""

import ast
import sys
from pathlib import Path
from typing import Dict, List

# ANSI colors for output
RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"


class ConfigViolation:
    """Represents a violation of config safety rules."""

    def __init__(self, file_path: str, rule: str, message: str, line_number: int = None):
        self.file_path = file_path
        self.rule = rule
        self.message = message
        self.line_number = line_number

    def __str__(self):
        location = f"{self.file_path}"
        if self.line_number:
            location += f":{self.line_number}"
        return f"{RED}✗{RESET} [{self.rule}] {location}\n  {self.message}"


def find_config_files() -> List[Path]:
    """Find all config Python files."""
    config_files = []

    # Check agents/config/
    agents_config_dir = Path("agents/config")
    if agents_config_dir.exists():
        for py_file in agents_config_dir.glob("*.py"):
            if not py_file.name.startswith("__"):
                config_files.append(py_file)

    # Check .env.example for defaults
    env_example = Path(".env.example")
    if env_example.exists():
        config_files.append(env_example)

    return config_files


def check_feature_flag_defaults_in_python(file_path: Path, content: str) -> List[ConfigViolation]:
    """Check Python config files for proper feature flag defaults."""
    violations = []

    # Known feature flags that should default to safe values
    feature_flags_must_be_false = [
        "GITHUB_ISSUE_CREATION_ENABLED",
        "SLACK_NOTIFICATIONS_ENABLED",
        "SLACK_BOB_ENABLED",
        "ORG_STORAGE_WRITE_ENABLED",
    ]

    dry_run_flags_must_be_true = [
        "GITHUB_ISSUES_DRY_RUN",
    ]

    try:
        tree = ast.parse(content)

        for node in ast.walk(tree):
            # Look for getenv calls with defaults
            if isinstance(node, ast.Call):
                if (isinstance(node.func, ast.Attribute) and
                    node.func.attr == "getenv"):

                    if len(node.args) >= 2:
                        # Get the env var name and default value
                        if isinstance(node.args[0], ast.Constant):
                            env_var = node.args[0].value

                            # Check if it's a known feature flag
                            if env_var in feature_flags_must_be_false:
                                default_val = node.args[1]

                                # Check if default is "false" or False
                                is_false = False
                                if isinstance(default_val, ast.Constant):
                                    if isinstance(default_val.value, bool) and not default_val.value:
                                        is_false = True
                                    elif isinstance(default_val.value, str) and default_val.value.lower() == "false":
                                        is_false = True

                                if not is_false:
                                    violations.append(ConfigViolation(
                                        str(file_path),
                                        "CONFIG-UNSAFE-DEFAULT",
                                        f"{env_var} must default to false/False (safety: external integrations OFF by default)",
                                        node.lineno
                                    ))

                            elif env_var in dry_run_flags_must_be_true:
                                default_val = node.args[1]

                                # Check if default is "true" or True
                                is_true = False
                                if isinstance(default_val, ast.Constant):
                                    if isinstance(default_val.value, bool) and default_val.value:
                                        is_true = True
                                    elif isinstance(default_val.value, str) and default_val.value.lower() == "true":
                                        is_true = True

                                if not is_true:
                                    violations.append(ConfigViolation(
                                        str(file_path),
                                        "CONFIG-UNSAFE-DEFAULT",
                                        f"{env_var} must default to true/True (safety: dry-run ON by default)",
                                        node.lineno
                                    ))

    except SyntaxError as e:
        violations.append(ConfigViolation(
            str(file_path),
            "CONFIG-SYNTAX-ERROR",
            f"Syntax error: {e}",
            e.lineno
        ))

    return violations


def check_env_example_defaults(file_path: Path, content: str) -> List[ConfigViolation]:
    """Check .env.example for proper default values."""
    violations = []

    # Parse .env.example file
    unsafe_patterns = {
        "GITHUB_ISSUE_CREATION_ENABLED=true": "GITHUB_ISSUE_CREATION_ENABLED must default to false",
        "SLACK_NOTIFICATIONS_ENABLED=true": "SLACK_NOTIFICATIONS_ENABLED must default to false",
        "SLACK_BOB_ENABLED=true": "SLACK_BOB_ENABLED must default to false",
        "ORG_STORAGE_WRITE_ENABLED=true": "ORG_STORAGE_WRITE_ENABLED must default to false",
        "GITHUB_ISSUES_DRY_RUN=false": "GITHUB_ISSUES_DRY_RUN must default to true",
    }

    for line_num, line in enumerate(content.split('\n'), 1):
        # Skip comments and empty lines
        if line.strip().startswith('#') or not line.strip():
            continue

        for pattern, message in unsafe_patterns.items():
            if pattern in line:
                violations.append(ConfigViolation(
                    str(file_path),
                    "CONFIG-UNSAFE-ENV-DEFAULT",
                    message,
                    line_num
                ))

    return violations


def check_hard_coded_secrets(file_path: Path, content: str) -> List[ConfigViolation]:
    """Check for hard-coded secrets or credentials."""
    violations = []

    # Patterns that indicate hard-coded secrets
    secret_patterns = [
        ("ghp_", "GitHub personal access token detected (use env var instead)"),
        ("gho_", "GitHub OAuth token detected (use env var instead)"),
        ("AIzaSy", "Google API key detected (use env var instead)"),
        ('"password":', "Hard-coded password field (use env var instead)"),
        ('"secret":', "Hard-coded secret field (use env var instead)"),
        ('"api_key":', "Hard-coded API key field (use env var instead)"),
    ]

    # Exclude certain safe contexts
    safe_contexts = [
        "# Example:",
        "# TODO:",
        "YOUR_TOKEN_HERE",
        "your-token-here",
        "example-",
    ]

    for line_num, line in enumerate(content.split('\n'), 1):
        # Skip comments
        if line.strip().startswith('#'):
            continue

        # Check for secret patterns
        for pattern, message in secret_patterns:
            if pattern in line:
                # Check if it's in a safe context
                is_safe = any(safe in line for safe in safe_contexts)
                if not is_safe:
                    violations.append(ConfigViolation(
                        str(file_path),
                        "CONFIG-HARD-CODED-SECRET",
                        message,
                        line_num
                    ))

    return violations


def check_config_file(file_path: Path) -> List[ConfigViolation]:
    """Run all checks on a single config file."""
    violations = []

    try:
        content = file_path.read_text()
    except Exception as e:
        violations.append(ConfigViolation(
            str(file_path),
            "CONFIG-FILE-ERROR",
            f"Could not read file: {e}"
        ))
        return violations

    # Run checks based on file type
    if file_path.suffix == ".py":
        violations.extend(check_feature_flag_defaults_in_python(file_path, content))
        violations.extend(check_hard_coded_secrets(file_path, content))
    elif file_path.name == ".env.example":
        violations.extend(check_env_example_defaults(file_path, content))
        violations.extend(check_hard_coded_secrets(file_path, content))

    return violations


def main():
    print(f"{BLUE}{'=' * 70}{RESET}")
    print(f"{BLUE}ARV Check: Configuration and Feature Flag Defaults{RESET}")
    print(f"{BLUE}{'=' * 70}{RESET}\n")

    # Find all config files
    config_files = find_config_files()

    if not config_files:
        print(f"{YELLOW}⚠{RESET} No config files found")
        return 1

    print(f"Found {len(config_files)} config files to check:\n")

    # Check each config file
    all_violations = []

    for config_file in config_files:
        print(f"Checking: {config_file}")
        violations = check_config_file(config_file)

        if violations:
            all_violations.extend(violations)
            print(f"  {RED}✗{RESET} {len(violations)} violation(s) found")
        else:
            print(f"  {GREEN}✓{RESET} Passed")
        print()

    # Print summary
    print(f"{BLUE}{'=' * 70}{RESET}")
    print(f"{BLUE}Summary{RESET}")
    print(f"{BLUE}{'=' * 70}{RESET}\n")

    if all_violations:
        print(f"{RED}✗ FAILED{RESET} - {len(all_violations)} violation(s) found:\n")

        # Group violations by rule
        violations_by_rule: Dict[str, List[ConfigViolation]] = {}
        for v in all_violations:
            if v.rule not in violations_by_rule:
                violations_by_rule[v.rule] = []
            violations_by_rule[v.rule].append(v)

        # Print violations grouped by rule
        for rule, violations in sorted(violations_by_rule.items()):
            print(f"{RED}[{rule}]{RESET} {len(violations)} violation(s):")
            for v in violations:
                print(f"  {v}")
            print()

        print(f"{BLUE}{'=' * 70}{RESET}")
        print(f"\n{RED}❌ ARV Check FAILED{RESET}\n")
        print("Fix the violations above to comply with config safety standards.")
        print("See: 000-docs/6767-DR-STND-adk-agent-engine-spec-and-hardmode-rules.md")
        return 1

    else:
        print(f"{GREEN}✓ All config files passed safety checks{RESET}")
        print(f"  - {len(config_files)} files checked")
        print("  - Feature flags default to safe values")
        print("  - Dry-run modes default enabled")
        print("  - No hard-coded secrets detected")
        print()
        print(f"{BLUE}{'=' * 70}{RESET}")
        print(f"{GREEN}✅ ARV Check PASSED{RESET}")
        return 0


if __name__ == "__main__":
    sys.exit(main())
