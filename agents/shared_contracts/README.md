# Shared Contracts - Structured Output Models

Pydantic V2 models for MCP tool outputs and A2A contract serialization in Bob's Brain.

## Overview

This package provides type-safe, validated output models for all MCP (Model Context Protocol) tools used by Bob's Brain agents. These models enable:

1. **Type Safety** - Strong typing for tool responses with Pydantic validation
2. **JSON Schema Generation** - Automatic schema generation for A2A AgentCard skills
3. **Consistent Error Handling** - Unified error response format across all tools
4. **A2A Protocol Compliance** - Serialization-ready models for agent-to-agent communication

## Architecture

```
agents/shared_contracts/
├── __init__.py           # Package exports
├── tool_outputs.py       # Pydantic models for MCP tools
└── README.md            # This file
```

### Design Principles

1. **Base Class Pattern**: All tool results inherit from `ToolResult`
2. **Optional Fields for Errors**: Domain-specific fields are Optional to support error cases
3. **Factory Functions**: `create_success_result()` and `create_error_result()` for consistency
4. **Validation**: Pydantic validators ensure data integrity (e.g., status matches violations)
5. **Schema Generation**: All models support `.model_json_schema()` for A2A AgentCard

## Models

### Base Models

#### ToolResult

Base class for all MCP tool outputs.

```python
from agents.shared_contracts.tool_outputs import ToolResult, create_success_result

result = create_success_result(
    ToolResult,
    "my_tool",
    data={"key": "value"}
)
```

**Fields:**
- `success: bool` - Whether tool execution succeeded
- `data: Optional[Dict]` - Tool-specific output data (None on error)
- `error: Optional[str]` - Error message if success=False
- `metadata: Dict` - Additional context (tool_name, timestamp, etc.)

### Tool-Specific Models

#### ComplianceResult

For ADK compliance checking (`check_patterns.py`).

```python
from agents.shared_contracts.tool_outputs import ComplianceResult, Violation

result = create_success_result(
    ComplianceResult,
    "check_patterns",
    status="VIOLATIONS_FOUND",
    violations=[
        Violation(
            rule="R1",
            rule_name="ADK-Only",
            type="forbidden_import",
            pattern="langchain",
            file="agents/test.py",
            line=10,
            text="import langchain"
        )
    ],
    passed=["R2", "R5"],
    compliance_score=66.7,
    risk_level="CRITICAL",
    path="/test/repo",
    rules_checked=["R1", "R2", "R5"]
)
```

**Fields:**
- `status: Literal["COMPLIANT", "VIOLATIONS_FOUND"]` - Overall status
- `violations: List[Violation]` - Detected violations
- `warnings: List[str]` - Non-blocking warnings
- `passed: List[str]` - Rule IDs that passed
- `compliance_score: float` - Percentage (0.0-100.0)
- `risk_level: Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]` - Risk assessment
- `path: str` - Path checked
- `rules_checked: List[str]` - Rules evaluated

**Validation:**
- `status="COMPLIANT"` requires `violations=[]`
- `status="VIOLATIONS_FOUND"` requires non-empty `violations`

#### SearchResult

For codebase search (`search_codebase.py`).

```python
from agents.shared_contracts.tool_outputs import SearchResult, SearchMatch

result = create_success_result(
    SearchResult,
    "search_codebase",
    query="google.adk",
    path="/repo",
    file_pattern="*.py",
    matches=[
        SearchMatch(
            file="agents/bob/agent.py",
            line_number=10,
            text="from google.adk.agents import LlmAgent"
        )
    ],
    match_count=1,
    file_count=1,
    truncated=False
)
```

**Fields:**
- `query: str` - Search pattern
- `path: str` - Directory searched
- `file_pattern: str` - File glob (e.g., "*.py")
- `matches: List[SearchMatch]` - Search results
- `match_count: int` - Total matches (before truncation)
- `file_count: int` - Unique files with matches
- `truncated: bool` - Whether results were limited

#### FileResult

For file reading (`get_file.py`).

```python
from agents.shared_contracts.tool_outputs import FileResult

result = create_success_result(
    FileResult,
    "get_file",
    path="/repo/agents/bob/agent.py",
    content="from google.adk.agents import LlmAgent\n...",
    size=1024,
    lines=42,
    encoding="utf-8"
)
```

**Fields:**
- `path: str` - Absolute file path
- `content: str` - File contents (UTF-8)
- `size: int` - File size in bytes
- `lines: int` - Line count
- `encoding: Literal["utf-8"]` - Character encoding

**Security:**
- Enforces allowed file extensions
- Denies sensitive paths (.env, credentials, keys)
- Max file size: 1MB
- Requires UTF-8 encoding

#### DependencyResult

For dependency analysis (`analyze_deps.py`).

```python
from agents.shared_contracts.tool_outputs import (
    DependencyResult,
    PythonDependencies,
    NodeDependencies,
    TerraformDependencies,
    DependencySummary,
)

result = create_success_result(
    DependencyResult,
    "analyze_deps",
    path="/repo",
    python=PythonDependencies(
        requirements_txt=["google-adk", "pydantic"],
        pyproject_toml=[]
    ),
    node=NodeDependencies(
        dependencies={"fastapi": "^0.104.0"},
        dev_dependencies={"pytest": "^7.4.0"}
    ),
    terraform=TerraformDependencies(
        providers=["google", "random"]
    ),
    summary=DependencySummary(
        python_packages=2,
        node_packages=2,
        terraform_providers=2
    ),
    issues=[]
)
```

**Fields:**
- `path: str` - Project path analyzed
- `python: PythonDependencies` - Python deps (requirements.txt, pyproject.toml)
- `node: NodeDependencies` - Node deps (package.json)
- `terraform: TerraformDependencies` - Terraform providers
- `summary: DependencySummary` - Aggregated counts
- `issues: List[str]` - Detected problems (vulnerabilities, duplicates)

## Usage Patterns

### In MCP Tools

Update tool execute functions to return structured models:

```python
# mcp/src/tools/search_codebase.py

import sys
from pathlib import Path
REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from agents.shared_contracts.tool_outputs import (
    SearchResult,
    SearchMatch,
    create_success_result,
    create_error_result,
)

async def execute(query: str, path: str = ".", file_pattern: str = "*.py") -> SearchResult:
    if not query:
        return create_error_result(
            SearchResult,
            "search_codebase",
            "Query is required"
        )

    # ... search logic ...

    return create_success_result(
        SearchResult,
        "search_codebase",
        query=query,
        path=path,
        file_pattern=file_pattern,
        matches=search_matches,
        match_count=len(search_matches),
        file_count=len(unique_files),
        truncated=False
    )
```

### In A2A AgentCards

Generate JSON schemas for skill definitions:

```python
from agents.shared_contracts.tool_outputs import ComplianceResult

# Generate schema for AgentCard
compliance_schema = ComplianceResult.model_json_schema()

# Use in .well-known/agent-card.json
skill_output_schema = {
    "type": "object",
    "properties": compliance_schema["properties"],
    "required": compliance_schema["required"]
}
```

### Error Handling

All models support error responses with None values:

```python
from agents.shared_contracts.tool_outputs import FileResult, create_error_result

# Error result
error_result = create_error_result(
    FileResult,
    "get_file",
    "File not found: /path/to/missing.py"
)

assert error_result.success is False
assert error_result.error == "File not found: /path/to/missing.py"
assert error_result.path is None  # Optional fields default to None
assert error_result.content is None
```

## Testing

Comprehensive test suite in `mcp/tests/unit/test_tool_outputs.py`:

```bash
cd /home/jeremy/000-projects/iams/bobs-brain/mcp
python3 -m pytest tests/unit/test_tool_outputs.py -v
```

**Test Coverage:**
- Base model creation (success/error)
- JSON serialization
- Validation (e.g., status matches violations)
- JSON schema generation
- All tool-specific models
- Helper functions

## Integration with A2A Protocol

These models form the foundation for A2A (Agent-to-Agent) communication:

1. **Tool Execution**: MCP tools return structured models
2. **Schema Generation**: Models provide JSON schemas for AgentCard skills
3. **Validation**: Foreman validates specialist outputs against schemas
4. **Serialization**: Models serialize cleanly to JSON for A2A transport

Example A2A flow:

```
User (Slack) → Bob → Foreman → Specialist (iam-adk)
                                    ↓
                            Tool: check_patterns()
                                    ↓
                            Returns: ComplianceResult
                                    ↓
                            JSON Schema Validation
                                    ↓
                            A2A Response Envelope
                                    ↓
Foreman ← Specialist ← A2A Protocol Transport
```

## Future Enhancements

### Planned (A2A-1/2/3)

1. **A2A Envelope Wrappers**
   - `A2ATaskEnvelope` for requests
   - `A2AResultEnvelope` for responses
   - Wrap these tool outputs for A2A protocol messages

2. **Validation Helpers**
   - Static validation (CI/CD): `scripts/check_a2a_contracts.py`
   - Runtime validation: a2a-inspector web UI

3. **Additional Tool Models**
   - `GitHubIssueResult` for issue creation
   - `TestExecutionResult` for QA runs
   - `DeploymentResult` for infrastructure changes

## References

- **Architecture**: `000-docs/6767-115-DR-STND-prompt-design-and-a2a-contracts-for-department-adk-iam.md`
- **A2A Protocol**: `000-docs/6767-DR-STND-agentcards-and-a2a-contracts.md`
- **Hard Mode Rules**: `000-docs/6767-DR-STND-adk-agent-engine-spec-and-hardmode-rules.md`
- **MCP Server**: `mcp/README.md`

## Changelog

**2025-12-20**: Initial implementation
- Created `tool_outputs.py` with Pydantic V2 models
- Implemented `ComplianceResult`, `SearchResult`, `FileResult`, `DependencyResult`
- Added factory functions `create_success_result()` and `create_error_result()`
- Comprehensive test suite (16 tests, all passing)
- Updated all MCP tools to use structured outputs
