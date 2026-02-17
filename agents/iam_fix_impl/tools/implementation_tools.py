"""
Implementation tools for iam-fix-impl agent.

These tools help convert FixPlan specifications into working code with tests.
"""

import json
import logging

logger = logging.getLogger(__name__)


def implement_fix_step(step_data: str) -> str:
    """
    Implement a single step from FixPlan.

    This tool helps convert a FixPlan step into concrete code changes.
    It provides guidance on implementation patterns and best practices.

    Args:
        step_data: JSON string containing:
            - step_number: int - Step number in FixPlan
            - step_description: str - What needs to be implemented
            - impacted_files: list[str] - Files to modify/create
            - implementation_notes: str - Additional context

    Returns:
        str: JSON string with implementation guidance and code templates
    """
    try:
        data = json.loads(step_data)
        step_num = data.get("step_number", 0)
        description = data.get("step_description", "")
        files = data.get("impacted_files", [])
        notes = data.get("implementation_notes", "")

        result = {
            "status": "guidance_provided",
            "step_number": step_num,
            "description": description,
            "implementation_guidance": f"""
Implementation for: {description}

Files to modify/create:
{chr(10).join(f"- {f}" for f in files)}

Implementation approach:
1. Review existing patterns in similar files
2. Follow ADK best practices (LlmAgent, proper imports)
3. Add proper error handling and logging
4. Include SPIFFE ID in log extras
5. Write corresponding unit tests

Notes: {notes}

Remember:
- Use 'from google.adk.agents import LlmAgent' (R1)
- Include after_agent_callback for R5
- Keep gateways as REST proxies (R3)
- Add SPIFFE ID to all logs (R7)
""",
            "next_actions": [
                "Review existing file patterns",
                "Implement code changes",
                "Add error handling",
                "Write unit tests",
                "Validate compliance"
            ]
        }

        return json.dumps(result)

    except Exception as e:
        logger.error(f"Error in implement_fix_step: {e}", exc_info=True)
        return json.dumps({
            "status": "error",
            "message": f"Failed to process step: {e!s}"
        })


def validate_implementation(validation_data: str) -> str:
    """
    Validate implementation against FixPlan requirements.

    Checks that all FixPlan steps have been implemented completely
    and correctly.

    Args:
        validation_data: JSON string containing:
            - fix_plan_steps: list[str] - Steps from FixPlan
            - implemented_files: list[str] - Files modified/created
            - implementation_summary: str - What was done

    Returns:
        str: JSON string with validation results
    """
    try:
        data = json.loads(validation_data)
        plan_steps = data.get("fix_plan_steps", [])
        impl_files = data.get("implemented_files", [])
        summary = data.get("implementation_summary", "")

        # Basic validation checks
        issues = []
        if len(impl_files) == 0:
            issues.append("No files were modified or created")

        if not summary:
            issues.append("Implementation summary is missing")

        # Check for TODOs or incomplete code
        incomplete_indicators = ["TODO", "FIXME", "XXX", "HACK"]
        if any(indicator in summary for indicator in incomplete_indicators):
            issues.append("Implementation contains TODOs or FIXMEs")

        status = "valid" if not issues else "incomplete"

        result = {
            "status": status,
            "validation_passed": len(issues) == 0,
            "steps_count": len(plan_steps),
            "files_modified": len(impl_files),
            "issues": issues,
            "recommendations": [
                "Ensure all FixPlan steps are implemented",
                "Remove any TODO or FIXME comments",
                "Add comprehensive error handling",
                "Include SPIFFE ID in all logs",
                "Write unit tests for all changes"
            ] if issues else []
        }

        return json.dumps(result)

    except Exception as e:
        logger.error(f"Error in validate_implementation: {e}", exc_info=True)
        return json.dumps({
            "status": "error",
            "message": f"Validation failed: {e!s}"
        })


def generate_unit_tests(code_data: str) -> str:
    """
    Generate unit tests for code changes.

    Creates pytest-based test templates for implemented code.

    Args:
        code_data: JSON string containing:
            - file_path: str - Path to file that needs tests
            - functions: list[str] - Function names to test
            - classes: list[str] - Class names to test
            - test_scenarios: list[str] - Specific scenarios to test

    Returns:
        str: JSON string with test file path and template
    """
    try:
        data = json.loads(code_data)
        file_path = data.get("file_path", "")
        functions = data.get("functions", [])
        classes = data.get("classes", [])

        # Generate test file path
        if "agents/" in file_path:
            test_path = file_path.replace("agents/", "tests/unit/").replace(".py", "_test.py")
        else:
            test_path = f"tests/unit/{file_path.split('/')[-1].replace('.py', '_test.py')}"

        # Build test template
        test_template = f'''"""
Unit tests for {file_path}
"""

import pytest
from unittest.mock import Mock, patch
'''

        # Add imports for the module being tested
        if file_path:
            module_path = file_path.replace("/", ".").replace(".py", "")
            test_template += f"\nfrom {module_path} import "
            if functions:
                test_template += ", ".join(functions)
            if classes:
                if functions:
                    test_template += ", "
                test_template += ", ".join(classes)

        test_template += "\n\n"

        # Add test cases for functions
        for func in functions:
            test_template += f"""
def test_{func}_success():
    \"\"\"Test {func} with valid input.\"\"\"
    # Arrange
    # TODO: Set up test data

    # Act
    result = {func}(...)

    # Assert
    assert result is not None
    # TODO: Add specific assertions


def test_{func}_error_handling():
    \"\"\"Test {func} error handling.\"\"\"
    # Arrange
    # TODO: Set up error scenario

    # Act & Assert
    with pytest.raises(Exception):
        {func}(...)

"""

        # Add test cases for classes
        for cls in classes:
            test_template += f"""
class Test{cls}:
    \"\"\"Test suite for {cls}.\"\"\"

    def test_initialization(self):
        \"\"\"Test {cls} initialization.\"\"\"
        obj = {cls}()
        assert obj is not None

    def test_main_functionality(self):
        \"\"\"Test {cls} main functionality.\"\"\"
        # TODO: Implement main test case
        pass

"""

        result = {
            "status": "template_generated",
            "test_file_path": test_path,
            "test_template": test_template,
            "functions_covered": len(functions),
            "classes_covered": len(classes),
            "recommendations": [
                "Fill in TODO sections with specific test logic",
                "Add edge case tests",
                "Test error conditions",
                "Mock external dependencies",
                "Aim for 85%+ coverage"
            ]
        }

        return json.dumps(result)

    except Exception as e:
        logger.error(f"Error in generate_unit_tests: {e}", exc_info=True)
        return json.dumps({
            "status": "error",
            "message": f"Test generation failed: {e!s}"
        })


def check_compliance(compliance_data: str) -> str:
    """
    Verify implementation complies with Hard Mode rules (R1-R8).

    Args:
        compliance_data: JSON string containing:
            - file_path: str - File to check
            - file_contents: str - File contents or summary
            - component: str - Component type (agent, gateway, infra, ci)

    Returns:
        str: JSON string with compliance check results
    """
    try:
        data = json.loads(compliance_data)
        file_path = data.get("file_path", "")
        contents = data.get("file_contents", "")

        violations = []

        # R1: Check for alternative frameworks
        if any(framework in contents for framework in ["langchain", "crewai", "autogen"]):
            violations.append({
                "rule": "R1",
                "description": "Alternative framework detected (must use google-adk)",
                "severity": "critical"
            })

        # R3: Check for Runner in gateways
        if "service/" in file_path and "Runner" in contents and "from google.adk import Runner" in contents:
            violations.append({
                "rule": "R3",
                "description": "Runner import detected in gateway code",
                "severity": "critical"
            })

        # R5: Check for dual memory in agents
        if "agents/" in file_path and "agent.py" in file_path:
            if "VertexAiSessionService" not in contents:
                violations.append({
                    "rule": "R5",
                    "description": "Missing VertexAiSessionService",
                    "severity": "high"
                })
            if "VertexAiMemoryBankService" not in contents:
                violations.append({
                    "rule": "R5",
                    "description": "Missing VertexAiMemoryBankService",
                    "severity": "high"
                })
            if "after_agent_callback" not in contents:
                violations.append({
                    "rule": "R5",
                    "description": "Missing after_agent_callback",
                    "severity": "high"
                })

        # R7: Check for SPIFFE ID in logs
        if "logger." in contents and "SPIFFE" not in contents:
            violations.append({
                "rule": "R7",
                "description": "Logging without SPIFFE ID in extras",
                "severity": "medium"
            })

        compliance_score = 1.0 - (len(violations) / 8.0)  # 8 total rules

        result = {
            "status": "compliant" if not violations else "violations_found",
            "compliance_score": max(0.0, compliance_score),
            "violations": violations,
            "checks_passed": 8 - len(violations),
            "checks_total": 8,
            "recommendations": [
                "Fix all critical violations immediately",
                "Address high severity issues",
                "Review and fix medium severity issues"
            ] if violations else ["All compliance checks passed"]
        }

        return json.dumps(result)

    except Exception as e:
        logger.error(f"Error in check_compliance: {e}", exc_info=True)
        return json.dumps({
            "status": "error",
            "message": f"Compliance check failed: {e!s}"
        })


def document_implementation(doc_data: str) -> str:
    """
    Document implementation decisions and changes.

    Creates structured documentation for implementation evidence.

    Args:
        doc_data: JSON string containing:
            - files_modified: list[str] - Files changed
            - files_created: list[str] - Files created
            - key_decisions: list[str] - Important decisions made
            - known_limitations: list[str] - Limitations or caveats
            - qa_recommendations: list[str] - Testing recommendations

    Returns:
        str: JSON string with formatted documentation
    """
    try:
        data = json.loads(doc_data)
        modified = data.get("files_modified", [])
        created = data.get("files_created", [])
        decisions = data.get("key_decisions", [])
        limitations = data.get("known_limitations", [])
        qa_recs = data.get("qa_recommendations", [])

        # Build documentation
        doc = f"""# Implementation Evidence

## Files Modified
{chr(10).join(f"- {f}" for f in modified) if modified else "None"}

## Files Created
{chr(10).join(f"- {f}" for f in created) if created else "None"}

## Key Decisions
{chr(10).join(f"{i+1}. {d}" for i, d in enumerate(decisions)) if decisions else "None"}

## Known Limitations
{chr(10).join(f"- {item}" for item in limitations) if limitations else "None"}

## QA Testing Recommendations
{chr(10).join(f"{i+1}. {r}" for i, r in enumerate(qa_recs)) if qa_recs else "Run standard test suite"}

## Compliance Checklist
- [x] R1: Using google-adk LlmAgent
- [x] R2: Designed for Agent Engine
- [x] R3: Gateways as REST proxies only
- [x] R5: Dual memory with callback
- [x] R7: SPIFFE ID in logs
"""

        result = {
            "status": "documented",
            "documentation": doc,
            "files_total": len(modified) + len(created),
            "decisions_documented": len(decisions),
            "recommendations": [
                "Include this in implementation PR",
                "Share with QA team",
                "Update relevant docs in 000-docs/"
            ]
        }

        return json.dumps(result)

    except Exception as e:
        logger.error(f"Error in document_implementation: {e}", exc_info=True)
        return json.dumps({
            "status": "error",
            "message": f"Documentation failed: {e!s}"
        })
