#!/usr/bin/env python3
"""
ARV Check: Gateway Separation and Service Compliance (R3)

Validates that all services in service/ directory follow gateway patterns:
- NO google.adk.Runner imports
- NO LlmAgent construction
- NO direct model API calls
- Only REST API calls to Agent Engine
- OAuth2 token authentication patterns

Part of: SPEC-ALIGN-ARV-EXPANSION (S3)
Rule: R3 (Gateway Separation)

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


class ServiceViolation:
    """Represents a violation of service/gateway rules."""

    def __init__(
        self, file_path: str, rule: str, message: str, line_number: int = None
    ):
        self.file_path = file_path
        self.rule = rule
        self.message = message
        self.line_number = line_number

    def __str__(self):
        location = f"{self.file_path}"
        if self.line_number:
            location += f":{self.line_number}"
        return f"{RED}✗{RESET} [{self.rule}] {location}\n  {self.message}"


def find_service_files() -> List[Path]:
    """Find all Python files in service/ directory."""
    service_dir = Path("service")
    if not service_dir.exists():
        print(
            f"{YELLOW}⚠{RESET} service/ directory not found (okay if no gateways yet)"
        )
        return []

    service_files = []
    for py_file in service_dir.rglob("*.py"):
        # Skip __pycache__ and test files
        if "__pycache__" in str(py_file) or py_file.name.startswith("test_"):
            continue
        service_files.append(py_file)

    return service_files


def check_prohibited_runner_imports(
    file_path: Path, content: str
) -> List[ServiceViolation]:
    """Check for prohibited Runner imports (R3 violation)."""
    violations = []

    try:
        tree = ast.parse(content)
        for node in ast.walk(tree):
            # Check for Runner imports
            if isinstance(node, ast.ImportFrom):
                if node.module and "google.adk" in node.module:
                    for alias in node.names:
                        if alias.name == "Runner":
                            violations.append(
                                ServiceViolation(
                                    str(file_path),
                                    "R3-RUNNER-IMPORT",
                                    "Runner imported in service/ (gateways must not run Runners locally)",
                                    node.lineno,
                                )
                            )

            # Check for LlmAgent imports (agents should not be constructed in services)
            elif isinstance(node, ast.ImportFrom):
                if node.module and "google.adk.agents" in node.module:
                    for alias in node.names:
                        if alias.name == "LlmAgent":
                            violations.append(
                                ServiceViolation(
                                    str(file_path),
                                    "R3-LLMAGENT-IMPORT",
                                    "LlmAgent imported in service/ (agents belong in agents/, not services)",
                                    node.lineno,
                                )
                            )

    except SyntaxError as e:
        violations.append(
            ServiceViolation(
                str(file_path), "R3-SYNTAX-ERROR", f"Syntax error: {e}", e.lineno
            )
        )

    return violations


def check_direct_model_calls(file_path: Path, content: str) -> List[ServiceViolation]:
    """Check for direct model API calls bypassing Agent Engine."""
    violations = []

    # Patterns that indicate direct model calls in gateways
    prohibited_patterns = [
        (
            "model.generate_content",
            "Direct model.generate_content() call (use Agent Engine REST API instead)",
        ),
        (
            "GenerativeModel",
            "Direct GenerativeModel usage (gateways should call Agent Engine, not models)",
        ),
        (
            "genai.GenerativeModel",
            "Direct genai.GenerativeModel usage (gateways should call Agent Engine)",
        ),
        (
            ".predict(",
            "Direct Vertex AI predict call (use Agent Engine REST API instead)",
        ),
    ]

    for pattern, message in prohibited_patterns:
        if pattern in content:
            # Find line number (simple search, not AST)
            for i, line in enumerate(content.split("\n"), 1):
                if pattern in line and not line.strip().startswith("#"):
                    violations.append(
                        ServiceViolation(
                            str(file_path), "R3-DIRECT-MODEL-CALL", message, i
                        )
                    )
                    break

    return violations


def check_runner_usage(file_path: Path, content: str) -> List[ServiceViolation]:
    """Check for Runner instantiation or usage."""
    violations = []

    # Patterns that indicate Runner usage
    prohibited_patterns = [
        ("Runner(", "Runner instantiation (gateways must not run Runners)"),
        ("runner.run(", "Runner.run() call (gateways must proxy to Agent Engine)"),
        (
            "runner.run_async(",
            "Runner.run_async() call (gateways must proxy to Agent Engine)",
        ),
    ]

    for pattern, message in prohibited_patterns:
        if pattern in content:
            for i, line in enumerate(content.split("\n"), 1):
                if pattern in line and not line.strip().startswith("#"):
                    violations.append(
                        ServiceViolation(str(file_path), "R3-RUNNER-USAGE", message, i)
                    )
                    break

    return violations


def check_agent_engine_patterns(
    file_path: Path, content: str
) -> List[ServiceViolation]:
    """Check for proper Agent Engine REST API patterns (positive check)."""
    violations = []

    # Look for Agent Engine REST API patterns (these are GOOD)
    good_patterns = [
        "aiplatform.googleapis.com",
        "Authorization",
        "Bearer",
        "access_token",
        "requests.post",
        "httpx.post",
    ]

    has_good_pattern = any(pattern in content for pattern in good_patterns)

    # If file is a main service file (main.py, app.py) and has no good patterns, warn
    if file_path.name in ["main.py", "app.py"] and len(content) > 100:
        if not has_good_pattern:
            violations.append(
                ServiceViolation(
                    str(file_path),
                    "R3-MISSING-AGENT-ENGINE-PATTERN",
                    "No Agent Engine REST API patterns detected (expected HTTP calls to aiplatform.googleapis.com)",
                    None,
                )
            )

    return violations


def check_service_file(file_path: Path) -> List[ServiceViolation]:
    """Run all checks on a single service file."""
    violations = []

    try:
        content = file_path.read_text()
    except Exception as e:
        violations.append(
            ServiceViolation(
                str(file_path), "R3-FILE-ERROR", f"Could not read file: {e}"
            )
        )
        return violations

    # Run all checks
    violations.extend(check_prohibited_runner_imports(file_path, content))
    violations.extend(check_direct_model_calls(file_path, content))
    violations.extend(check_runner_usage(file_path, content))
    violations.extend(check_agent_engine_patterns(file_path, content))

    return violations


def main():
    print(f"{BLUE}{'=' * 70}{RESET}")
    print(f"{BLUE}ARV Check: Gateway Separation and Service Compliance (R3){RESET}")
    print(f"{BLUE}{'=' * 70}{RESET}\n")

    # Find all service files
    service_files = find_service_files()

    if not service_files:
        print(
            f"{GREEN}✓{RESET} No service files found (or service/ directory doesn't exist)"
        )
        print("  This is okay if all services use Agent Engine directly")
        return 0

    print(f"Found {len(service_files)} service files to check:\n")

    # Check each service file
    all_violations = []

    for service_file in service_files:
        print(f"Checking: {service_file}")
        violations = check_service_file(service_file)

        if violations:
            all_violations.extend(violations)
            # Separate warnings from errors
            errors = [
                v
                for v in violations
                if not v.rule.endswith("-MISSING-AGENT-ENGINE-PATTERN")
            ]
            warnings = [
                v
                for v in violations
                if v.rule.endswith("-MISSING-AGENT-ENGINE-PATTERN")
            ]

            if errors:
                print(f"  {RED}✗{RESET} {len(errors)} violation(s) found")
            if warnings:
                print(f"  {YELLOW}⚠{RESET} {len(warnings)} warning(s)")
        else:
            print(f"  {GREEN}✓{RESET} Passed")
        print()

    # Print summary
    print(f"{BLUE}{'=' * 70}{RESET}")
    print(f"{BLUE}Summary{RESET}")
    print(f"{BLUE}{'=' * 70}{RESET}\n")

    # Separate warnings from errors
    errors = [
        v
        for v in all_violations
        if not v.rule.endswith("-MISSING-AGENT-ENGINE-PATTERN")
    ]
    warnings = [
        v for v in all_violations if v.rule.endswith("-MISSING-AGENT-ENGINE-PATTERN")
    ]

    if errors:
        print(f"{RED}✗ FAILED{RESET} - {len(errors)} violation(s) found:\n")

        # Group violations by rule
        violations_by_rule: Dict[str, List[ServiceViolation]] = {}
        for v in errors:
            if v.rule not in violations_by_rule:
                violations_by_rule[v.rule] = []
            violations_by_rule[v.rule].append(v)

        # Print violations grouped by rule
        for rule, violations in sorted(violations_by_rule.items()):
            print(f"{RED}[{rule}]{RESET} {len(violations)} violation(s):")
            for v in violations:
                print(f"  {v}")
            print()

        if warnings:
            print(f"{YELLOW}⚠ WARNINGS{RESET} - {len(warnings)} warning(s):\n")
            for w in warnings:
                print(f"  {w}")
            print()

        print(f"{BLUE}{'=' * 70}{RESET}")
        print(f"\n{RED}❌ ARV Check FAILED{RESET}\n")
        print("Fix the violations above to comply with R3 (Gateway Separation).")
        print("See: 000-docs/6767-DR-STND-adk-agent-engine-spec-and-hardmode-rules.md")
        return 1

    else:
        if warnings:
            print(f"{YELLOW}⚠{RESET} Warnings found (non-blocking):\n")
            for w in warnings:
                print(f"  {w}")
            print()

        print(f"{GREEN}✓ All service files passed gateway compliance checks{RESET}")
        print(f"  - {len(service_files)} files checked")
        print("  - No Runner imports detected")
        print("  - No direct model API calls detected")
        print("  - Gateway separation maintained")
        print()
        print(f"{BLUE}{'=' * 70}{RESET}")
        print(f"{GREEN}✅ ARV Check PASSED{RESET}")
        return 0


if __name__ == "__main__":
    sys.exit(main())
