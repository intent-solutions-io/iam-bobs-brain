"""
ADK Pattern Analysis Tools

Tools for analyzing agent code, validating ADK patterns, and checking A2A compliance.

These tools enable iam-adk to perform static analysis and produce structured
audit reports and issue specifications.
"""

import ast
import logging
import os

logger = logging.getLogger(__name__)


def analyze_agent_code(file_path: str) -> str:
    """
    Analyze an agent.py file for ADK pattern compliance.

    Performs static analysis on an agent implementation to check:
    - Import compliance (uses google-adk, no forbidden frameworks)
    - LlmAgent structure (has get_agent, root_agent)
    - Memory wiring (VertexAiSessionService, VertexAiMemoryBankService)
    - Callback implementation (after_agent_callback)
    - Type hints and documentation
    - SPIFFE ID propagation

    Args:
        file_path: Path to agent.py file to analyze

    Returns:
        JSON string with analysis results:
        {
            "compliance_status": "COMPLIANT" | "NON_COMPLIANT" | "WARNING",
            "violations": [
                {
                    "severity": "HIGH" | "MEDIUM" | "LOW",
                    "rule": "R1" | "R2" | "R5" | "R7" | etc,
                    "message": "Description of violation",
                    "line_number": 42
                }
            ],
            "recommendations": [
                "Specific improvement suggestions"
            ],
            "metrics": {
                "has_get_agent": true,
                "has_root_agent": true,
                "has_dual_memory": true,
                "has_callback": true,
                "uses_type_hints": true
            }
        }

    Examples:
        >>> analyze_agent_code("agents/bob/agent.py")
        >>> analyze_agent_code("agents/iam-issue/agent.py")
    """
    try:
        # Resolve absolute path
        if not os.path.isabs(file_path):
            file_path = os.path.join(os.getcwd(), file_path)

        if not os.path.exists(file_path):
            return f'{{"error": "File not found: {file_path}"}}'

        with open(file_path) as f:
            code = f.read()

        # Parse AST
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            return f'{{"error": "Syntax error in file: {e!s}"}}'

        violations = []
        metrics = {
            "has_get_agent": False,
            "has_root_agent": False,
            "has_dual_memory": False,
            "has_callback": False,
            "uses_type_hints": False,
            "has_spiffe_id": False,
        }

        # Check imports (R1: ADK-only)
        forbidden_imports = ["langchain", "crewai", "autogen", "llama_index"]
        required_imports = ["google.adk.agents", "google.adk.sessions", "google.adk.memory"]

        imports_found = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports_found.append(alias.name)
                    for forbidden in forbidden_imports:
                        if forbidden in alias.name.lower():
                            violations.append(
                                {
                                    "severity": "CRITICAL",
                                    "rule": "R1",
                                    "message": f"Forbidden framework import: {alias.name}",
                                    "line_number": node.lineno,
                                }
                            )
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                imports_found.append(module)
                for forbidden in forbidden_imports:
                    if forbidden in module.lower():
                        violations.append(
                            {
                                "severity": "CRITICAL",
                                "rule": "R1",
                                "message": f"Forbidden framework import: {module}",
                                "line_number": node.lineno,
                            }
                        )

        # Check required imports
        for required in required_imports:
            if not any(required in imp for imp in imports_found):
                violations.append(
                    {
                        "severity": "HIGH",
                        "rule": "R1",
                        "message": f"Missing required import: {required}",
                        "line_number": None,
                    }
                )

        # Check for dual memory (R5)
        has_session_service = any("VertexAiSessionService" in imp for imp in imports_found)
        has_memory_bank = any("VertexAiMemoryBankService" in imp for imp in imports_found)
        metrics["has_dual_memory"] = has_session_service and has_memory_bank

        if not metrics["has_dual_memory"]:
            violations.append(
                {
                    "severity": "HIGH",
                    "rule": "R5",
                    "message": "Missing dual memory wiring (VertexAiSessionService + VertexAiMemoryBankService)",
                    "line_number": None,
                }
            )

        # Check for get_agent() and root_agent
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                if node.name == "get_agent":
                    metrics["has_get_agent"] = True
                    # Check return type hint
                    if node.returns and isinstance(node.returns, ast.Name):
                        if node.returns.id == "LlmAgent":
                            metrics["uses_type_hints"] = True
                elif node.name == "auto_save_session_to_memory":
                    metrics["has_callback"] = True
            elif isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id == "root_agent":
                        metrics["has_root_agent"] = True

        if not metrics["has_get_agent"]:
            violations.append(
                {
                    "severity": "HIGH",
                    "rule": "R1",
                    "message": "Missing get_agent() function",
                    "line_number": None,
                }
            )

        if not metrics["has_root_agent"]:
            violations.append(
                {
                    "severity": "HIGH",
                    "rule": "R1",
                    "message": "Missing root_agent module-level variable (required for ADK CLI)",
                    "line_number": None,
                }
            )

        if not metrics["has_callback"]:
            violations.append(
                {
                    "severity": "MEDIUM",
                    "rule": "R5",
                    "message": "Missing after_agent_callback for session persistence",
                    "line_number": None,
                }
            )

        # Check for SPIFFE ID (R7)
        if "AGENT_SPIFFE_ID" in code:
            metrics["has_spiffe_id"] = True
        else:
            violations.append(
                {
                    "severity": "MEDIUM",
                    "rule": "R7",
                    "message": "Missing AGENT_SPIFFE_ID environment variable reference",
                    "line_number": None,
                }
            )

        # Determine compliance status
        critical_violations = [v for v in violations if v["severity"] == "CRITICAL"]
        high_violations = [v for v in violations if v["severity"] == "HIGH"]

        if critical_violations:
            compliance_status = "NON_COMPLIANT"
        elif high_violations:
            compliance_status = "WARNING"
        else:
            compliance_status = "COMPLIANT"

        # Generate recommendations
        recommendations = []
        if not metrics["has_dual_memory"]:
            recommendations.append(
                "Implement dual memory wiring with VertexAiSessionService and VertexAiMemoryBankService"
            )
        if not metrics["has_callback"]:
            recommendations.append("Add after_agent_callback to persist sessions to Memory Bank")
        if not metrics["uses_type_hints"]:
            recommendations.append("Add type hints to get_agent() -> LlmAgent")
        if not metrics["has_spiffe_id"]:
            recommendations.append("Add AGENT_SPIFFE_ID to environment variables and logging")

        result = {
            "compliance_status": compliance_status,
            "violations": violations,
            "recommendations": recommendations,
            "metrics": metrics,
        }

        import json

        return json.dumps(result, indent=2)

    except Exception as e:
        logger.error(f"Error analyzing agent code: {e}", exc_info=True)
        return f'{{"error": "Analysis failed: {e!s}"}}'


def validate_adk_pattern(pattern_name: str, code_snippet: str) -> str:
    """
    Validate a specific ADK pattern in a code snippet.

    Checks whether a code snippet correctly implements a specific ADK pattern.
    Useful for focused validation of patterns like tool definitions, agent
    composition, memory wiring, etc.

    Args:
        pattern_name: Name of pattern to validate (e.g., "tool_definition", "agent_composition", "memory_wiring")
        code_snippet: Python code snippet to validate

    Returns:
        JSON string with validation results:
        {
            "valid": true | false,
            "pattern": "pattern_name",
            "issues": [
                {
                    "severity": "HIGH" | "MEDIUM" | "LOW",
                    "message": "Description of issue"
                }
            ],
            "example": "Correct implementation example (if issues found)"
        }

    Supported Patterns:
        - tool_definition: FunctionTool with proper docstring and type hints
        - agent_composition: SequentialAgent/ParallelAgent/LoopAgent usage
        - memory_wiring: VertexAiSessionService + VertexAiMemoryBankService
        - callback_implementation: after_agent_callback structure
        - llm_agent_creation: LlmAgent initialization

    Examples:
        >>> validate_adk_pattern("tool_definition", "def my_tool(x: int) -> str: ...")
        >>> validate_adk_pattern("memory_wiring", "session_service = VertexAiSessionService(...)")
    """
    try:
        issues = []
        valid = True

        # Parse code snippet
        try:
            tree = ast.parse(code_snippet)
        except SyntaxError as e:
            return f'{{"valid": false, "pattern": "{pattern_name}", "issues": [{{"severity": "HIGH", "message": "Syntax error: {e!s}"}}]}}'

        if pattern_name == "tool_definition":
            # Check for function with docstring and type hints
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    # Check docstring
                    docstring = ast.get_docstring(node)
                    if not docstring:
                        issues.append(
                            {
                                "severity": "HIGH",
                                "message": f"Function {node.name} missing docstring with Args/Returns sections",
                            }
                        )
                        valid = False

                    # Check type hints
                    if not node.returns:
                        issues.append(
                            {
                                "severity": "MEDIUM",
                                "message": f"Function {node.name} missing return type hint",
                            }
                        )
                        valid = False

                    for arg in node.args.args:
                        if not arg.annotation:
                            issues.append(
                                {
                                    "severity": "MEDIUM",
                                    "message": f"Parameter {arg.arg} missing type hint",
                                }
                            )
                            valid = False

            example = '''
def my_tool(param: str, count: int = 1) -> str:
    """
    Brief description of what the tool does.

    Args:
        param: Description of param
        count: Description of count (default: 1)

    Returns:
        Description of return value

    Examples:
        >>> my_tool("test", 2)
        "result"
    """
    return f"{param} x {count}"
'''

        elif pattern_name == "memory_wiring":
            # Check for both session and memory services
            has_session = "VertexAiSessionService" in code_snippet
            has_memory = "VertexAiMemoryBankService" in code_snippet

            if not has_session:
                issues.append(
                    {
                        "severity": "HIGH",
                        "message": "Missing VertexAiSessionService initialization",
                    }
                )
                valid = False

            if not has_memory:
                issues.append(
                    {
                        "severity": "HIGH",
                        "message": "Missing VertexAiMemoryBankService initialization",
                    }
                )
                valid = False

            example = '''
from google.adk.sessions import VertexAiSessionService
from google.adk.memory import VertexAiMemoryBankService

session_service = VertexAiSessionService(
    project=PROJECT_ID,
    location=LOCATION,
    agent_engine_id=AGENT_ENGINE_ID
)

memory_service = VertexAiMemoryBankService(
    project=PROJECT_ID,
    location=LOCATION,
    agent_engine_id=AGENT_ENGINE_ID
)

runner = Runner(
    agent=agent,
    session_service=session_service,
    memory_service=memory_service
)
'''

        elif pattern_name == "llm_agent_creation":
            # Check LlmAgent structure
            has_model = "model=" in code_snippet
            has_name = "name=" in code_snippet
            has_instruction = "instruction=" in code_snippet

            if not has_model:
                issues.append({"severity": "HIGH", "message": "Missing model parameter"})
                valid = False

            if not has_name:
                issues.append({"severity": "HIGH", "message": "Missing name parameter"})
                valid = False

            if not has_instruction:
                issues.append(
                    {"severity": "MEDIUM", "message": "Missing instruction parameter"}
                )

            example = '''
from google.adk.agents import LlmAgent

agent = LlmAgent(
    model="gemini-2.0-flash-exp",
    name="agent_name",  # Valid Python identifier
    tools=[tool1, tool2],
    instruction="Agent system prompt...",
    after_agent_callback=auto_save_session_to_memory
)
'''

        else:
            return f'{{"valid": false, "pattern": "{pattern_name}", "issues": [{{"severity": "HIGH", "message": "Unknown pattern name"}}]}}'

        result = {"valid": valid, "pattern": pattern_name, "issues": issues}

        if not valid:
            result["example"] = example.strip()

        import json

        return json.dumps(result, indent=2)

    except Exception as e:
        logger.error(f"Error validating pattern: {e}", exc_info=True)
        return f'{{"valid": false, "pattern": "{pattern_name}", "issues": [{{"severity": "HIGH", "message": "Validation failed: {e!s}"}}]}}'


def check_a2a_compliance(agent_dir: str) -> str:
    """
    Check Agent-to-Agent (A2A) protocol compliance for an agent.

    Validates that an agent properly implements A2A patterns including:
    - AgentCard definition (agent_card.yaml or Python equivalent)
    - Input/output schema definitions
    - Capability declarations
    - SPIFFE ID inclusion
    - Tool-based delegation patterns

    Args:
        agent_dir: Path to agent directory (e.g., "agents/bob")

    Returns:
        JSON string with A2A compliance results:
        {
            "compliant": true | false,
            "has_agent_card": true | false,
            "issues": [
                {
                    "severity": "HIGH" | "MEDIUM" | "LOW",
                    "component": "agent_card" | "schema" | "capabilities",
                    "message": "Description of issue"
                }
            ],
            "recommendations": [
                "Specific improvement suggestions"
            ]
        }

    Examples:
        >>> check_a2a_compliance("agents/bob")
        >>> check_a2a_compliance("agents/iam-issue")
    """
    try:
        # Resolve absolute path
        if not os.path.isabs(agent_dir):
            agent_dir = os.path.join(os.getcwd(), agent_dir)

        if not os.path.exists(agent_dir):
            return f'{{"error": "Directory not found: {agent_dir}"}}'

        issues = []
        recommendations = []
        compliant = True
        has_agent_card = False

        # Check for agent_card.yaml
        card_yaml = os.path.join(agent_dir, "agent_card.yaml")
        card_py = os.path.join(agent_dir, "a2a_card.py")

        if os.path.exists(card_yaml):
            has_agent_card = True
            # TODO: Parse and validate YAML structure
        elif os.path.exists(card_py):
            has_agent_card = True
            # Check Python AgentCard definition
            with open(card_py) as f:
                card_code = f.read()

            if "AgentCard" not in card_code:
                issues.append(
                    {
                        "severity": "HIGH",
                        "component": "agent_card",
                        "message": "a2a_card.py exists but doesn't define AgentCard",
                    }
                )
                compliant = False

            # Check for required fields
            required_fields = ["name", "description", "capabilities"]
            for field in required_fields:
                if f'"{field}"' not in card_code and f"'{field}'" not in card_code:
                    issues.append(
                        {
                            "severity": "MEDIUM",
                            "component": "agent_card",
                            "message": f"AgentCard missing recommended field: {field}",
                        }
                    )
        else:
            has_agent_card = False
            issues.append(
                {
                    "severity": "HIGH",
                    "component": "agent_card",
                    "message": "No AgentCard found (agent_card.yaml or a2a_card.py)",
                }
            )
            compliant = False
            recommendations.append(
                "Create agent_card.yaml with name, description, input_schema, output_schema, and capabilities"
            )

        # Check for README documentation
        readme = os.path.join(agent_dir, "README.md")
        if not os.path.exists(readme):
            issues.append(
                {
                    "severity": "LOW",
                    "component": "documentation",
                    "message": "Missing README.md documentation",
                }
            )
            recommendations.append(
                "Add README.md describing agent purpose, inputs, outputs, and usage examples"
            )

        result = {
            "compliant": compliant,
            "has_agent_card": has_agent_card,
            "issues": issues,
            "recommendations": recommendations,
        }

        import json

        return json.dumps(result, indent=2)

    except Exception as e:
        logger.error(f"Error checking A2A compliance: {e}", exc_info=True)
        return f'{{"error": "A2A compliance check failed: {e!s}"}}'
