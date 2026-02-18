#!/usr/bin/env python3
"""
ARV Check: Agent Structure and ADK Compliance (R1)

Validates that all agents in agents/ directory follow ADK patterns:
- Use google.adk.agents.LlmAgent
- No alternative frameworks (LangChain, CrewAI, AutoGen)
- Proper factory pattern (get_agent(), root_agent)
- ADK tool system usage

Part of: SPEC-ALIGN-ARV-EXPANSION (S3)
Rule: R1 (ADK-Only Implementation)

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


class AgentViolation:
    """Represents a violation of agent structure rules."""

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


def find_agent_files() -> List[Path]:
    """Find all agent.py files in agents/ directory."""
    agents_dir = Path("agents")
    if not agents_dir.exists():
        print(f"{RED}✗{RESET} agents/ directory not found")
        return []

    agent_files = []
    for agent_dir in agents_dir.iterdir():
        if not agent_dir.is_dir():
            continue
        if agent_dir.name in ["__pycache__", "utils", "config", "a2a"]:
            continue

        agent_py = agent_dir / "agent.py"
        if agent_py.exists():
            agent_files.append(agent_py)

    return agent_files


def check_prohibited_imports(file_path: Path, content: str) -> List[AgentViolation]:
    """Check for prohibited framework imports."""
    violations = []

    prohibited = {
        "langchain": "LangChain framework detected (use google.adk instead)",
        "crewai": "CrewAI framework detected (use google.adk instead)",
        "autogen": "AutoGen framework detected (use google.adk instead)",
        "openai": "Direct OpenAI API usage detected (use ADK with Vertex AI)",
    }

    try:
        tree = ast.parse(content)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    for prohibited_module, message in prohibited.items():
                        if alias.name.startswith(prohibited_module):
                            violations.append(
                                AgentViolation(
                                    str(file_path),
                                    "R1-PROHIBITED-IMPORT",
                                    f"{message}: import {alias.name}",
                                    node.lineno,
                                )
                            )

            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    for prohibited_module, message in prohibited.items():
                        if node.module.startswith(prohibited_module):
                            violations.append(
                                AgentViolation(
                                    str(file_path),
                                    "R1-PROHIBITED-IMPORT",
                                    f"{message}: from {node.module} import ...",
                                    node.lineno,
                                )
                            )

    except SyntaxError as e:
        violations.append(
            AgentViolation(
                str(file_path), "R1-SYNTAX-ERROR", f"Syntax error: {e}", e.lineno
            )
        )

    return violations


def check_adk_imports(file_path: Path, content: str) -> List[AgentViolation]:
    """Check for required ADK imports."""
    violations = []

    # Check for LlmAgent import
    has_llm_agent = False
    has_adk_import = False

    try:
        tree = ast.parse(content)
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                if node.module and "google.adk" in node.module:
                    has_adk_import = True
                    for alias in node.names:
                        if alias.name == "LlmAgent":
                            has_llm_agent = True

    except SyntaxError:
        # Already reported in check_prohibited_imports
        pass

    if not has_adk_import:
        violations.append(
            AgentViolation(
                str(file_path),
                "R1-MISSING-ADK-IMPORT",
                "No google.adk imports found (agents must use ADK primitives)",
            )
        )

    if not has_llm_agent:
        violations.append(
            AgentViolation(
                str(file_path),
                "R1-MISSING-LLMAGENT",
                "LlmAgent not imported from google.adk.agents (required for ADK agents)",
            )
        )

    return violations


def check_agent_factory_pattern(file_path: Path, content: str) -> List[AgentViolation]:
    """Check for required factory pattern (get_agent() and root_agent)."""
    violations = []

    has_get_agent = False
    has_root_agent = False

    try:
        tree = ast.parse(content)

        for node in ast.walk(tree):
            # Check for get_agent() function
            if isinstance(node, ast.FunctionDef) and node.name == "get_agent":
                has_get_agent = True

            # Check for root_agent assignment
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id == "root_agent":
                        has_root_agent = True

    except SyntaxError:
        # Already reported in check_prohibited_imports
        pass

    if not has_get_agent:
        violations.append(
            AgentViolation(
                str(file_path),
                "R1-MISSING-FACTORY",
                "get_agent() factory function not found (required for agent construction pattern)",
            )
        )

    if not has_root_agent:
        violations.append(
            AgentViolation(
                str(file_path),
                "R1-MISSING-ROOT-AGENT",
                "root_agent not exported (required for ADK CLI deployment: root_agent = get_agent())",
            )
        )

    return violations


def check_direct_model_calls(file_path: Path, content: str) -> List[AgentViolation]:
    """Check for direct model API calls bypassing ADK."""
    violations = []

    # Patterns that indicate direct model calls
    prohibited_patterns = [
        (
            "model.generate_content",
            "Direct model.generate_content() call (use ADK agent instead)",
        ),
        ("GenerativeModel", "Direct GenerativeModel usage (use ADK LlmAgent instead)"),
        (
            "genai.GenerativeModel",
            "Direct genai.GenerativeModel usage (use ADK LlmAgent instead)",
        ),
    ]

    for pattern, message in prohibited_patterns:
        if pattern in content:
            # Find line number (simple search, not AST)
            for i, line in enumerate(content.split("\n"), 1):
                if pattern in line:
                    violations.append(
                        AgentViolation(
                            str(file_path), "R1-DIRECT-MODEL-CALL", message, i
                        )
                    )
                    break

    return violations


def check_agent_file(file_path: Path) -> List[AgentViolation]:
    """Run all checks on a single agent file."""
    violations = []

    try:
        content = file_path.read_text()
    except Exception as e:
        violations.append(
            AgentViolation(str(file_path), "R1-FILE-ERROR", f"Could not read file: {e}")
        )
        return violations

    # Run all checks
    violations.extend(check_prohibited_imports(file_path, content))
    violations.extend(check_adk_imports(file_path, content))
    violations.extend(check_agent_factory_pattern(file_path, content))
    violations.extend(check_direct_model_calls(file_path, content))

    return violations


def main():
    print(f"{BLUE}{'=' * 70}{RESET}")
    print(f"{BLUE}ARV Check: Agent Structure and ADK Compliance (R1){RESET}")
    print(f"{BLUE}{'=' * 70}{RESET}\n")

    # Find all agent files
    agent_files = find_agent_files()

    if not agent_files:
        print(f"{YELLOW}⚠{RESET} No agent files found in agents/ directory")
        return 1

    print(f"Found {len(agent_files)} agent files to check:\n")

    # Check each agent
    all_violations = []

    for agent_file in agent_files:
        print(f"Checking: {agent_file}")
        violations = check_agent_file(agent_file)

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
        violations_by_rule: Dict[str, List[AgentViolation]] = {}
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
        print("Fix the violations above to comply with R1 (ADK-Only Implementation).")
        print("See: 000-docs/6767-DR-STND-adk-agent-engine-spec-and-hardmode-rules.md")
        return 1

    else:
        print(f"{GREEN}✓ All agent files passed ADK compliance checks{RESET}")
        print(f"  - {len(agent_files)} agents checked")
        print("  - No prohibited frameworks detected")
        print("  - ADK imports verified")
        print("  - Factory patterns present")
        print()
        print(f"{BLUE}{'=' * 70}{RESET}")
        print(f"{GREEN}✅ ARV Check PASSED{RESET}")
        return 0


if __name__ == "__main__":
    sys.exit(main())
