# AgentCard JSON Schema Example

This document demonstrates how to use Pydantic structured output models to generate JSON schemas for A2A AgentCard skill definitions.

## Generating JSON Schemas

All models in `tool_outputs.py` support `.model_json_schema()` for A2A AgentCard compatibility:

```python
from agents.shared_contracts.tool_outputs import ComplianceResult

# Generate full JSON schema
full_schema = ComplianceResult.model_json_schema()

# Extract for AgentCard skill output
skill_output_schema = {
    "type": "object",
    "properties": {
        "status": full_schema["properties"]["status"],
        "violations": full_schema["properties"]["violations"],
        "compliance_score": full_schema["properties"]["compliance_score"],
        "risk_level": full_schema["properties"]["risk_level"],
        # ... other fields
    },
    "required": ["success"],  # From base ToolResult
    "additionalProperties": False
}
```

## Example: iam-adk AgentCard Skill

Here's how to define the `check_adk_compliance` skill in `.well-known/agent-card.json`:

```json
{
  "@context": "https://a2a.sh/agent-card/v1",
  "agentId": "iam-adk",
  "name": "ADK Compliance Checker",
  "description": "Checks code against ADK Hard Mode rules (R1-R8)",
  "skills": [
    {
      "skillId": "check_adk_compliance",
      "name": "Check ADK Compliance",
      "description": "Validates code against Hard Mode rules and returns violations",
      "inputSchema": {
        "type": "object",
        "properties": {
          "target": {
            "type": "string",
            "description": "Directory or file path to check"
          },
          "focus_rules": {
            "type": "array",
            "items": {
              "type": "string",
              "enum": ["R1", "R2", "R3", "R4", "R5", "R6", "R7", "R8"]
            },
            "description": "Specific rules to check (default: all)"
          }
        },
        "required": ["target"]
      },
      "outputSchema": {
        "type": "object",
        "properties": {
          "success": {
            "type": "boolean",
            "description": "Whether the tool execution completed successfully"
          },
          "status": {
            "type": "string",
            "enum": ["COMPLIANT", "VIOLATIONS_FOUND"],
            "description": "Overall compliance status (None on error)"
          },
          "violations": {
            "type": "array",
            "items": {
              "type": "object",
              "properties": {
                "rule": {
                  "type": "string",
                  "description": "Rule ID that was violated (e.g., 'R1', 'R2')"
                },
                "rule_name": {
                  "type": "string",
                  "description": "Human-readable rule name"
                },
                "type": {
                  "type": "string",
                  "description": "Violation type (e.g., 'forbidden_import', 'forbidden_in_service')"
                },
                "pattern": {
                  "type": "string",
                  "description": "Pattern that triggered the violation"
                },
                "file": {
                  "type": "string",
                  "description": "File path where violation was found"
                },
                "line": {
                  "type": "integer",
                  "description": "Line number of violation"
                },
                "text": {
                  "type": "string",
                  "description": "Code snippet containing violation (truncated)"
                }
              },
              "required": ["rule", "rule_name", "type", "pattern", "file", "line", "text"]
            },
            "description": "List of compliance violations found (empty if COMPLIANT)"
          },
          "warnings": {
            "type": "array",
            "items": {
              "type": "string"
            },
            "description": "Non-blocking warnings (e.g., unknown rules checked)"
          },
          "passed": {
            "type": "array",
            "items": {
              "type": "string"
            },
            "description": "Rule IDs that passed checks"
          },
          "compliance_score": {
            "type": "number",
            "minimum": 0.0,
            "maximum": 100.0,
            "description": "Percentage of rules passed (0.0 = all failed, 100.0 = all passed, None on error)"
          },
          "risk_level": {
            "type": "string",
            "enum": ["LOW", "MEDIUM", "HIGH", "CRITICAL"],
            "description": "Overall risk level based on violation severity (None on error)"
          },
          "path": {
            "type": "string",
            "description": "Path that was checked (None on error)"
          },
          "rules_checked": {
            "type": "array",
            "items": {
              "type": "string"
            },
            "description": "List of rule IDs checked"
          },
          "error": {
            "type": ["string", "null"],
            "description": "Error message if success=false"
          },
          "metadata": {
            "type": "object",
            "description": "Additional context (tool name, timestamp, execution time, etc.)",
            "properties": {
              "tool_name": {"type": "string"},
              "timestamp": {"type": "string", "format": "date-time"},
              "execution_time_ms": {"type": "number"}
            }
          }
        },
        "required": ["success"]
      }
    }
  ]
}
```

## Automated Schema Generation Script

To automate this, create a script to generate AgentCard schemas:

```python
#!/usr/bin/env python3
"""Generate AgentCard skill schemas from Pydantic models."""

import json
from agents.shared_contracts.tool_outputs import (
    ComplianceResult,
    SearchResult,
    FileResult,
    DependencyResult,
)

def generate_skill_output_schema(model_class):
    """Generate AgentCard-compatible output schema."""
    schema = model_class.model_json_schema()

    # Include $defs if present (for nested models)
    output_schema = {
        "type": "object",
        "properties": schema["properties"],
        "required": schema.get("required", ["success"]),
    }

    # Add nested definitions
    if "$defs" in schema:
        output_schema["$defs"] = schema["$defs"]

    return output_schema

# Generate for all models
schemas = {
    "ComplianceResult": generate_skill_output_schema(ComplianceResult),
    "SearchResult": generate_skill_output_schema(SearchResult),
    "FileResult": generate_skill_output_schema(FileResult),
    "DependencyResult": generate_skill_output_schema(DependencyResult),
}

# Save to file
with open("agentcard_schemas.json", "w") as f:
    json.dump(schemas, f, indent=2)

print("Generated AgentCard schemas for all models ✓")
```

## Example A2A Task/Result Flow

### 1. Foreman sends task to iam-adk

```json
{
  "task_id": "compliance-check-001",
  "skill_id": "check_adk_compliance",
  "input": {
    "target": "/home/user/project/agents/bob",
    "focus_rules": ["R1", "R2", "R5"]
  }
}
```

### 2. iam-adk executes and returns ComplianceResult

```json
{
  "task_id": "compliance-check-001",
  "status": "completed",
  "output": {
    "success": true,
    "status": "COMPLIANT",
    "violations": [],
    "warnings": [],
    "passed": ["R1", "R2", "R5"],
    "compliance_score": 100.0,
    "risk_level": "LOW",
    "path": "/home/user/project/agents/bob",
    "rules_checked": ["R1", "R2", "R5"],
    "error": null,
    "metadata": {
      "tool_name": "check_patterns",
      "timestamp": "2025-12-20T15:00:00Z",
      "execution_time_ms": 250
    }
  }
}
```

### 3. Foreman validates against outputSchema

```python
from pydantic import ValidationError
from agents.shared_contracts.tool_outputs import ComplianceResult

# Parse result from iam-adk
result_data = response["output"]

try:
    # Validate against ComplianceResult model
    validated_result = ComplianceResult(**result_data)

    # Check compliance
    if validated_result.status == "COMPLIANT":
        print(f"✓ Target is compliant (score: {validated_result.compliance_score}%)")
    else:
        print(f"✗ Found {len(validated_result.violations)} violations")
        for violation in validated_result.violations:
            print(f"  - {violation.rule}: {violation.file}:{violation.line}")

except ValidationError as e:
    print(f"Invalid response from iam-adk: {e}")
```

## Benefits

1. **Type Safety**: Foreman validates specialist outputs at runtime
2. **Schema Contract**: AgentCard defines strict input/output contracts
3. **Documentation**: JSON schemas self-document expected data structures
4. **Tooling**: IDEs autocomplete based on Pydantic models
5. **Versioning**: Models can be versioned alongside AgentCard specs

## References

- **A2A Protocol**: https://a2a.sh/
- **AgentCard Spec**: `.well-known/agent-card.json`
- **Pydantic Docs**: https://docs.pydantic.dev/latest/
- **Bob's Brain Standards**: `000-docs/6767-DR-STND-agentcards-and-a2a-contracts.md`

## Next Steps

1. Generate schemas for all iam-* specialists
2. Implement A2A envelope wrappers (A2ATaskEnvelope, A2AResultEnvelope)
3. Add runtime validation in foreman's orchestration logic
4. Create CI checks to ensure AgentCards match Pydantic schemas
