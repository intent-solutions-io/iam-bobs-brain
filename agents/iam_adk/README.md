# iam-adk - ADK/Vertex Design & Static Analysis Specialist

**Version:** 0.8.0
**Status:** Active
**Model:** gemini-2.0-flash-exp
**Runtime:** Vertex AI Agent Engine

## Overview

`iam-adk` is a specialized agent within the iam-* department responsible for ADK pattern analysis, A2A protocol compliance checking, and Hard Mode rules enforcement.

## Purpose

This agent ensures that all agents in the bobs-brain agent factory follow:
- Google ADK best practices and patterns
- Hard Mode rules (R1-R8) for architectural consistency
- Agent-to-Agent (A2A) communication protocols
- Code quality standards (type hints, documentation, error handling)

## Core Responsibilities

### 1. ADK Pattern Analysis
- Review `agent.py` implementations for LlmAgent compliance
- Validate tool implementations (FunctionTool patterns)
- Check memory wiring (Session + Memory Bank)
- Assess agent composition (Sequential/Parallel/Loop agents)
- Verify callback implementations

### 2. Hard Mode Rules Enforcement
Validate compliance with the eight Hard Mode rules:

- **R1:** ADK-only implementation (no LangChain, CrewAI, AutoGen)
- **R2:** Vertex AI Agent Engine runtime (not self-hosted)
- **R3:** Gateway separation (no Runner in service/)
- **R4:** CI-only deployments (GitHub Actions with WIF)
- **R5:** Dual memory wiring (Session + Memory Bank with callback)
- **R6:** Single documentation folder (000-docs/)
- **R7:** SPIFFE ID propagation (logs, headers, telemetry)
- **R8:** Drift detection (CI enforcement)

### 3. A2A Protocol Compliance
- Validate AgentCard definitions (agent_card.yaml)
- Check input/output schema definitions
- Review capability declarations
- Verify tool-based delegation patterns

### 4. Quality Assurance
- Static code analysis (AST-based)
- Import validation (detect forbidden frameworks)
- Type hint coverage checks
- Documentation adequacy assessment
- Test coverage recommendations

## Input Format

The agent accepts structured requests:

```json
{
  "task_type": "analyze_agent" | "validate_pattern" | "check_a2a" | "audit_compliance",
  "target": "agents/agent-name/agent.py" | "agents/agent-name" | "<code snippet>",
  "pattern_name": "tool_definition" | "memory_wiring" | etc (optional),
  "focus_rules": ["R1", "R5", "R7"] (optional),
  "severity_threshold": "CRITICAL" | "HIGH" | "MEDIUM" | "LOW" (default: LOW)
}
```

## Output Formats

### AuditReport
Comprehensive compliance assessment:
```json
{
  "compliance_status": "COMPLIANT" | "NON_COMPLIANT" | "WARNING",
  "violations": [
    {
      "severity": "CRITICAL" | "HIGH" | "MEDIUM" | "LOW",
      "rule": "R1" | "R2" | ... | null,
      "message": "Description",
      "file": "path/to/file.py",
      "line_number": 42
    }
  ],
  "recommendations": ["Actionable suggestions"],
  "metrics": {
    "has_get_agent": true,
    "has_root_agent": true,
    "has_dual_memory": true,
    "has_callback": true,
    "uses_type_hints": true,
    "has_spiffe_id": true
  },
  "risk_level": "LOW" | "MEDIUM" | "HIGH" | "CRITICAL"
}
```

### IssueSpec
Individual issue specification (consumed by iam-issue):
```json
{
  "title": "Missing dual memory wiring",
  "severity": "HIGH",
  "rule_violated": "R5",
  "affected_files": ["agents/agent-name/agent.py"],
  "description": "Agent lacks VertexAiMemoryBankService...",
  "proposed_fix": {
    "approach": "Add memory service to create_runner()",
    "code_examples": "memory_service = VertexAiMemoryBankService(...)",
    "references": "000-docs/6767-002-AT-FLOW-memory-patterns.md"
  },
  "impact": "Sessions not persisted to Memory Bank",
  "effort": "MEDIUM"
}
```

## Available Tools

### 1. analyze_agent_code(file_path: str)
**Purpose:** Comprehensive agent.py file analysis

**Checks:**
- Import compliance (R1)
- LlmAgent structure
- Memory wiring (R5)
- Callback implementation
- SPIFFE ID propagation (R7)
- Type hints and documentation

**Example:**
```python
result = analyze_agent_code("agents/bob/agent.py")
```

### 2. validate_adk_pattern(pattern_name: str, code_snippet: str)
**Purpose:** Validate specific ADK patterns

**Supported Patterns:**
- `tool_definition` - FunctionTool with docstring/type hints
- `agent_composition` - Sequential/Parallel/Loop agents
- `memory_wiring` - Session + Memory Bank setup
- `callback_implementation` - after_agent_callback structure
- `llm_agent_creation` - LlmAgent initialization

**Example:**
```python
result = validate_adk_pattern("tool_definition", """
def my_tool(x: int) -> str:
    '''Tool docstring'''
    return str(x)
""")
```

### 3. check_a2a_compliance(agent_dir: str)
**Purpose:** Check A2A protocol compliance

**Checks:**
- AgentCard presence (agent_card.yaml or Python)
- Input/output schemas
- Capability declarations
- Documentation (README.md)

**Example:**
```python
result = check_a2a_compliance("agents/bob")
```

## Usage Examples

### Example 1: Comprehensive Agent Audit
```python
# Request
{
  "task_type": "analyze_agent",
  "target": "agents/iam-issue/agent.py",
  "severity_threshold": "MEDIUM"
}

# Response (AuditReport)
{
  "compliance_status": "WARNING",
  "violations": [
    {
      "severity": "HIGH",
      "rule": "R5",
      "message": "Missing VertexAiMemoryBankService",
      "file": "agents/iam-issue/agent.py",
      "line_number": 45
    }
  ],
  "recommendations": [
    "Add VertexAiMemoryBankService to create_runner()",
    "Implement after_agent_callback for session persistence"
  ],
  "risk_level": "MEDIUM"
}
```

### Example 2: Pattern Validation
```python
# Request
{
  "task_type": "validate_pattern",
  "pattern_name": "tool_definition",
  "target": "def search(q): return results"
}

# Response
{
  "valid": false,
  "pattern": "tool_definition",
  "issues": [
    {
      "severity": "HIGH",
      "message": "Missing docstring with Args/Returns"
    },
    {
      "severity": "MEDIUM",
      "message": "Parameter 'q' missing type hint"
    }
  ],
  "example": "def search(q: str) -> str:\n    '''...\n    Args:\n        q: ...\n    '''"
}
```

### Example 3: A2A Compliance Check
```python
# Request
{
  "task_type": "check_a2a",
  "target": "agents/bob"
}

# Response
{
  "compliant": true,
  "has_agent_card": true,
  "issues": [],
  "recommendations": [
    "Consider creating agent_card.yaml for easier tooling"
  ]
}
```

## Integration with iam-* Department

### Reports To
- **iam-senior-adk-devops-lead** - Coordinates audits and reviews

### Provides Output To
- **iam-issue** - Structured IssueSpecs for tracking
- **iam-fix-plan** - Pattern recommendations and examples
- **iam-doc** - Documentation standards and gaps

### Collaborates With
- **iam-index** - Queries ADK documentation knowledge base
- **iam-qa** - Validates fix implementations

## Local Development

### Run Analysis Locally
```bash
cd /home/jeremy/000-projects/iams/bobs-brain

# Activate virtual environment
source .venv/bin/activate

# Test agent creation
python3 -c "from agents.iam_adk import get_agent; a = get_agent(); print('✅ Agent created')"

# Run tool directly (for testing)
python3 -c "
from agents.iam_adk.tools import analyze_agent_code
result = analyze_agent_code('agents/bob/agent.py')
print(result)
"
```

### Run Tests
```bash
# Unit tests
pytest tests/unit/test_iam_adk.py -v

# Integration tests
pytest tests/integration/test_iam_adk_integration.py -v
```

## Deployment

This agent deploys to Vertex AI Agent Engine via GitHub Actions (R4: CI-only):

```bash
# DO NOT deploy manually
# Deployments MUST go through CI/CD

# To trigger deployment:
git push origin main  # Automatic dev deployment
# OR
# Use GitHub Actions UI for staging/prod
```

## Hard Mode Compliance

This agent itself is fully compliant with Hard Mode rules:

- ✅ **R1:** Uses google-adk LlmAgent only
- ✅ **R2:** Deployed to Vertex AI Agent Engine
- ✅ **R3:** No Runner imports in gateway code
- ✅ **R4:** CI-only deployment enforced
- ✅ **R5:** Dual memory with callback
- ✅ **R6:** Documentation in 000-docs/
- ✅ **R7:** SPIFFE ID in all logs
- ✅ **R8:** Passes drift detection

## Files Structure

```
agents/iam-adk/
├── README.md                   # This file
├── agent.py                    # LlmAgent implementation
├── agent_card.yaml             # A2A protocol card
├── system-prompt.md            # Detailed role and behavior
├── __init__.py                 # Module exports
└── tools/
    ├── __init__.py
    └── analysis_tools.py       # Static analysis tools
```

## Version History

- **0.8.0** - Initial implementation
  - Core analysis tools (analyze_agent_code, validate_adk_pattern, check_a2a_compliance)
  - Hard Mode rules enforcement
  - A2A protocol compliance
  - Structured output formats (AuditReport, IssueSpec)

## Related Documentation

- `000-docs/6767-001-PP-ARCH-agent-factory-structure.md` - Agent factory pattern
- `000-docs/6767-002-AT-FLOW-agent-interaction-patterns.md` - A2A patterns
- `000-docs/6767-003-AT-RULE-hard-mode-rules.md` - Hard Mode rules (R1-R8)
- `agents/bob/README.md` - Bob orchestrator agent

## Contact

- **Owner:** iam-senior-adk-devops-lead
- **Repository:** https://github.com/jeremylongshore/iam-bob-adk
- **Version:** 0.8.0
- **Last Updated:** 2025-11-19
