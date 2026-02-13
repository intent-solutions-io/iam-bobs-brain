# AgentCards and A2A Contracts Standard

**Document Type:** Canonical Standard (6767-DR-STND)
**Status:** Active
**Applies To:** All ADK departments, starting with department adk iam
**Last Updated:** 2025-11-20

---

## I. Purpose and Scope

This document defines the **AgentCard and A2A contract standard** for ADK-based agent departments in the bobs-brain repository, with initial implementation for **department adk iam**.

**Purpose:**
- Establish machine-readable contracts for agent skills and capabilities
- Define structured A2A-style task messages for foreman → worker delegation
- Align with the official A2A Protocol specification where applicable
- Enable validation, testing, and future external A2A integration

**Scope:**
- AgentCard JSON structure and location conventions
- Skill definition patterns (input/output schemas, naming)
- A2A task envelope format for internal delegation
- Versioning and evolution strategies
- Validation and testing requirements

**Out of Scope:**
- External A2A network protocol (covered separately)
- Deployment and infrastructure (covered in Hard Mode rules)
- Tool implementation details (covered in ADK docs)

---

## II. AgentCard Basics (Our Repo Rules)

### What is an AgentCard in This Project?

An **AgentCard** is a JSON manifest that describes:
- **Identity**: Agent name, version, SPIFFE ID
- **Skills**: Machine-readable capabilities with strict input/output schemas
- **Authentication**: How to authenticate with this agent
- **Capabilities**: Streaming, push notifications, etc.
- **Metadata**: Department, role, runtime info

**Key Principle:** AgentCards are **contracts, not documentation**.
- System prompts enforce behavior
- Tools implement functionality
- AgentCards define the **interface** between agents

### Where AgentCards Live

```
agents/
├── iam-senior-adk-devops-lead/
│   ├── .well-known/
│   │   └── agent-card.json       # Foreman AgentCard
│   └── agent.py
│
├── iam_adk/
│   ├── .well-known/
│   │   └── agent-card.json       # Worker AgentCard
│   └── agent.py
│
└── (other iam-* agents)
    ├── .well-known/
    │   └── agent-card.json
    └── agent.py
```

**Rules:**
- Every agent MUST have `.well-known/agent-card.json` in its directory
- File MUST be valid JSON
- File MUST be version-controlled (not generated at runtime)
- Path SHOULD be referenced in agent.py via `AGENTCARD_PATH` constant

### Relationship to System Prompts and Tools

| Component | Responsibility | Example |
|-----------|----------------|---------|
| **System Prompt** | Define role, boundaries, output format | "You are iam-adk, a specialist in..." |
| **AgentCard** | Define skills with strict schemas | `{"skill_id": "iam.check_adk_compliance", "input_schema": {...}}` |
| **Tools (Python)** | Implement actual functionality | `def analyze_agent_code(...) -> dict:` |
| **A2A Messages** | Reference skills by ID | `{"skill_id": "iam.check_adk_compliance", "input": {...}}` |

**Anti-Pattern:**
❌ Duplicating tool schemas in system prompts
❌ Describing skills in natural language when you have a schema
❌ Having schema in AgentCard that doesn't match tool implementation

**Correct Pattern:**
✅ System prompt: "Use your analyze_agent skill"
✅ AgentCard: Defines `iam.check_adk_compliance` with exact input/output schema
✅ Tool: Python function matching that schema
✅ A2A message: `{"skill_id": "iam.check_adk_compliance", "input": {"target": "..."}}`

---

## III. Skill / Contract Pattern

### Skill Naming Convention

**Pattern:** `{department}.{verb}_{noun}`

**Examples:**
- `iam.check_adk_compliance` (department: iam, action: check ADK compliance)
- `iam.open_issue_from_finding` (department: iam, action: open issue from finding)
- `iam.run_qa_checks` (department: iam, action: run QA checks)
- `iam.aggregate_portfolio_report` (department: iam, action: aggregate portfolio report)

**Rules:**
- Use lowercase with underscores (snake_case)
- Start with department prefix (`iam.` for department adk iam)
- Use verbs that describe the action
- Keep it concise but unambiguous

### Skill Structure

Each skill in an AgentCard MUST have:

```json
{
  "skill_id": "iam.check_adk_compliance",
  "name": "Check ADK Compliance",
  "description": "Analyze agent code for ADK pattern compliance and Hard Mode rule violations",
  "input_schema": {
    "type": "object",
    "required": ["target"],
    "properties": {
      "target": {
        "type": "string",
        "description": "File path or directory to analyze"
      },
      "focus_rules": {
        "type": "array",
        "items": {
          "type": "string",
          "enum": ["R1", "R2", "R3", "R4", "R5", "R6", "R7", "R8"]
        },
        "description": "Specific Hard Mode rules to focus on (optional)"
      },
      "severity_threshold": {
        "type": "string",
        "enum": ["CRITICAL", "HIGH", "MEDIUM", "LOW"],
        "default": "LOW",
        "description": "Only report issues at or above this severity"
      }
    }
  },
  "output_schema": {
    "type": "object",
    "required": ["compliance_status", "violations"],
    "properties": {
      "compliance_status": {
        "type": "string",
        "enum": ["COMPLIANT", "NON_COMPLIANT", "WARNING"]
      },
      "violations": {
        "type": "array",
        "items": {
          "type": "object",
          "required": ["severity", "message"],
          "properties": {
            "severity": {
              "type": "string",
              "enum": ["CRITICAL", "HIGH", "MEDIUM", "LOW"]
            },
            "rule": {
              "type": "string",
              "description": "Hard Mode rule violated (R1-R8) or null"
            },
            "message": {"type": "string"},
            "file": {"type": "string"},
            "line_number": {"type": "integer"}
          }
        }
      },
      "risk_level": {
        "type": "string",
        "enum": ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
      }
    }
  }
}
```

### Schema Requirements

**Mandatory:**
- ✅ All schemas MUST be valid JSON Schema (draft-07 or later)
- ✅ All schemas MUST define `type` for every field
- ✅ All schemas SHOULD define `required` arrays
- ✅ All schemas SHOULD use `enum` for constrained values
- ✅ All schemas SHOULD include `description` for non-obvious fields

**Forbidden:**
- ❌ Empty schemas: `{}` or `{"type": "object"}` with no properties
- ❌ `any` types without justification
- ❌ Vague descriptions like "input data" or "result object"
- ❌ Schemas that don't match actual tool implementations

---

## IV. A2A Task Pattern for Foreman → Worker

### Canonical Task Envelope

When **iam-senior-adk-devops-lead** (foreman) delegates to a worker (iam-adk, iam-issue, etc.), the task payload follows this structure:

```json
{
  "skill_id": "iam.check_adk_compliance",
  "source_agent": "iam-senior-adk-devops-lead",
  "target_agent": "iam-adk",
  "input": {
    "target": "agents/bob/agent.py",
    "focus_rules": ["R1", "R2", "R5"],
    "severity_threshold": "HIGH"
  },
  "context": {
    "pipeline_run_id": "uuid-1234",
    "repo_hint": "bobs-brain",
    "phase": "adk-compliance-audit",
    "rag_chunks": [
      {
        "source": "ADK docs - LlmAgent patterns",
        "content": "<context>...</context>"
      }
    ]
  },
  "metadata": {
    "trace_id": "trace-5678",
    "priority": "high",
    "requested_by": "Bob",
    "timeout_seconds": 300
  }
}
```

**Required Fields:**
- `skill_id`: Exact skill ID from target agent's AgentCard
- `source_agent`: Name of calling agent
- `target_agent`: Name of worker agent
- `input`: Object conforming to skill's `input_schema`

**Optional Fields:**
- `context`: Additional context for the task (RAG chunks, pipeline info)
- `metadata`: Tracing, priorities, timeouts

### Task Envelope Principles

1. **Contract-First:** Input MUST match skill's `input_schema`
2. **Traceability:** Include `trace_id` or `pipeline_run_id` for debugging
3. **Self-Contained:** Worker should need minimal external state
4. **Metadata Separation:** Context vs input vs metadata are distinct
5. **Immutable:** Once sent, task envelope shouldn't be modified

### Worker Response Envelope

Workers MUST return structured responses:

```json
{
  "skill_id": "iam.check_adk_compliance",
  "target_agent": "iam-adk",
  "source_agent": "iam-senior-adk-devops-lead",
  "status": "ok",
  "output": {
    "compliance_status": "NON_COMPLIANT",
    "violations": [...],
    "risk_level": "HIGH"
  },
  "metadata": {
    "trace_id": "trace-5678",
    "execution_time_ms": 1234,
    "worker_version": "0.9.0"
  }
}
```

**Error Response:**
```json
{
  "skill_id": "iam.check_adk_compliance",
  "target_agent": "iam-adk",
  "source_agent": "iam-senior-adk-devops-lead",
  "status": "error",
  "error": "unsupported_skill",
  "error_details": {
    "message": "Skill 'iam.unknown_skill' not found",
    "supported_skills": ["iam.check_adk_compliance", "iam.validate_agentcard"]
  },
  "metadata": {
    "trace_id": "trace-5678"
  }
}
```

---

## V. Placement & Versioning

### AgentCard Versioning

**Version Field:**
```json
{
  "name": "iam-adk",
  "version": "0.9.0",
  ...
}
```

**Versioning Rules:**
- Use **semantic versioning** (major.minor.patch)
- Version SHOULD track app/agent version
- Breaking schema changes → major version bump
- New skills (additive) → minor version bump
- Bug fixes, description changes → patch version bump

### Schema Evolution

**Additive Changes (Safe):**
- ✅ Adding new optional fields to input_schema
- ✅ Adding new skills
- ✅ Adding new enum values (if backward compatible)
- ✅ Improving descriptions

**Breaking Changes (Require Version Bump):**
- ❌ Removing fields from schemas
- ❌ Changing field types
- ❌ Making optional fields required
- ❌ Removing skills
- ❌ Changing skill_id naming

**Migration Strategy:**
- For breaking changes:
  1. Create new skill with different ID (e.g., `iam.check_compliance_v2`)
  2. Deprecate old skill (document in AgentCard)
  3. Migrate callers over time
  4. Remove old skill in next major version

---

## VI. Inspector / Validation Rules

### Validation Layers

**Layer 1: JSON Syntax (Always)**
- AgentCard MUST be valid JSON
- All referenced schemas MUST be valid JSON Schema
- No syntax errors, trailing commas, etc.

**Layer 2: Required Fields (Always)**
- `name`, `version`, `skills` MUST be present
- Each skill MUST have `skill_id`, `input_schema`, `output_schema`

**Layer 3: Schema Compliance (Enforced in CI)**
- Input payloads MUST validate against declared `input_schema`
- Output payloads SHOULD validate against declared `output_schema`
- No empty `{}` schemas without justification

**Layer 4: A2A Protocol Compliance (Future)**
- AgentCard structure matches official A2A spec
- Validated via `a2a-inspector` or equivalent

### Validation Tools

**Current (Basic):**
```bash
# Check JSON syntax and required fields
make check-a2a-contracts
```

**Future (Comprehensive):**
```bash
# Full A2A protocol validation
make check-a2a-contracts-full

# Interactive inspection
make a2a-inspector-dev
```

### CI Integration (Documented Intent)

**Near-Term Goal:**
```yaml
# .github/workflows/arv-a2a-contracts.yml
jobs:
  validate-agentcards:
    steps:
      - name: Check AgentCard JSON syntax
        run: make check-a2a-contracts

      - name: Validate against A2A spec
        run: make check-a2a-contracts-full  # TODO: implement
```

**Enforcement:**
- Validation failures SHOULD block PRs
- Exception process: document in PR why validation skipped
- Exemptions tracked in AAR

---

## VII. How to Add a New AgentCard

### Checklist (10 Steps)

When adding a new agent to department adk iam (or any department):

#### 1. Determine Agent Identity
- [ ] Choose agent name (e.g., `iam-fix-impl`)
- [ ] Determine role (foreman or specialist?)
- [ ] Assign SPIFFE ID following pattern: `spiffe://intent.solutions/agent/{name}/{env}/{region}/{version}`

#### 2. Create Directory Structure
```bash
mkdir -p agents/iam-fix-impl/.well-known
touch agents/iam-fix-impl/.well-known/agent-card.json
```

#### 3. Define Core Skills (2-5 skills recommended)
- [ ] List primary responsibilities
- [ ] Choose skill IDs following naming convention: `iam.{verb}_{noun}`
- [ ] Identify input parameters (what does this skill need?)
- [ ] Identify output structure (what does this skill return?)

#### 4. Write Input Schemas (Strict)
- [ ] Use JSON Schema with explicit `type` for all fields
- [ ] Define `required` array
- [ ] Use `enum` for constrained values
- [ ] Add `description` for each field
- [ ] **No `{}` empty schemas**

#### 5. Write Output Schemas (Strict)
- [ ] Match what the tool actually returns
- [ ] Include success and error cases
- [ ] Use consistent field names across skills (e.g., `status`, `error`, `data`)

#### 6. Create AgentCard JSON
```json
{
  "name": "iam-fix-impl",
  "version": "0.9.0",
  "description": "Implementation specialist for executing fixes",
  "spiffe_id": "spiffe://intent.solutions/agent/iam-fix-impl/dev/us-central1/0.9.0",
  "capabilities": {
    "streaming": false
  },
  "skills": [
    {
      "skill_id": "iam.execute_fix_plan",
      "name": "Execute Fix Plan",
      "description": "...",
      "input_schema": {...},
      "output_schema": {...}
    }
  ],
  "authentication": {
    "type": "gcp_agent_identity"
  },
  "metadata": {
    "department": "iam",
    "role": "specialist",
    "runtime": "vertex-ai-agent-engine"
  }
}
```

#### 7. Add AGENTCARD_PATH to Agent Code
```python
# agents/iam-fix-impl/agent.py
from pathlib import Path

AGENTCARD_PATH = Path(__file__).parent / ".well-known" / "agent-card.json"
```

#### 8. Validate Locally
```bash
# Check JSON syntax
python3 -c "import json; json.load(open('agents/iam-fix-impl/.well-known/agent-card.json'))"

# Run repo validation
make check-a2a-contracts
```

#### 9. Update System Prompt (Contract-Aware)
- [ ] Reference skills by ID in prompt: "Use your execute_fix_plan skill"
- [ ] Do NOT duplicate schemas in prompt
- [ ] Emphasize JSON-only output matching AgentCard schemas

#### 10. Write Tests
- [ ] Unit test: AgentCard loads without errors
- [ ] Unit test: Each skill's input/output matches schema
- [ ] Integration test: Foreman → worker task envelope works

---

## VIII. Integration with Existing Standards

### Relationship to 6767 Prompt Design Standard

**000-DR-STND-prompt-design-and-agentcard-standard.md** defines:
- How prompts should be structured (role-focused, not schema-focused)
- Where content belongs (system vs Memory Bank vs RAG vs task)

**This doc (AgentCard standard)** defines:
- How skills are defined (JSON Schema with strict types)
- How agents communicate (A2A task envelopes)
- What contracts look like (machine-readable, testable)

**Together they enforce:**
- Prompts reference skills by ID: ✅ "Use your check_compliance skill"
- Prompts do NOT duplicate schemas: ❌ "The input has fields: target, rules, severity..."
- AgentCards define the contract: ✅ Strict JSON Schema
- Tools implement the contract: ✅ Python functions matching schema

### Relationship to Hard Mode Rules

**000-DR-STND-adk-agent-engine-spec-and-hardmode-rules.md:**
- R1: ADK-only implementation
- R2: Vertex AI Agent Engine runtime
- R7: SPIFFE ID propagation

**This doc:**
- AgentCards include SPIFFE ID (R7)
- AgentCards reference ADK/Vertex runtime (R2)
- AgentCards are structured contracts for ADK agents (R1)

---

## IX. Examples

### Example 1: Foreman AgentCard (iam-senior-adk-devops-lead)

```json
{
  "name": "iam-senior-adk-devops-lead",
  "version": "0.9.0",
  "description": "Department foreman for ADK/Vertex/IAM work. Coordinates iam-* specialist agents.",
  "spiffe_id": "spiffe://intent.solutions/agent/iam-senior-adk-devops-lead/dev/us-central1/0.9.0",
  "capabilities": {
    "streaming": false
  },
  "skills": [
    {
      "skill_id": "iam.run_portfolio_audit",
      "name": "Run Portfolio Audit",
      "description": "Orchestrate full ADK compliance audit across multiple repositories",
      "input_schema": {
        "type": "object",
        "required": ["repos"],
        "properties": {
          "repos": {
            "type": "array",
            "items": {"type": "string"},
            "description": "List of repository identifiers to audit"
          },
          "focus_areas": {
            "type": "array",
            "items": {
              "type": "string",
              "enum": ["adk_patterns", "a2a_compliance", "hard_mode_rules"]
            },
            "description": "Areas to focus audit on"
          },
          "priority": {
            "type": "string",
            "enum": ["low", "medium", "high", "urgent"],
            "default": "medium"
          }
        }
      },
      "output_schema": {
        "type": "object",
        "required": ["status", "reports"],
        "properties": {
          "status": {
            "type": "string",
            "enum": ["completed", "partial", "failed"]
          },
          "reports": {
            "type": "array",
            "items": {
              "type": "object",
              "required": ["repo", "compliance_status"],
              "properties": {
                "repo": {"type": "string"},
                "compliance_status": {
                  "type": "string",
                  "enum": ["COMPLIANT", "NON_COMPLIANT", "WARNING"]
                },
                "violations": {"type": "integer"},
                "risk_level": {
                  "type": "string",
                  "enum": ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
                }
              }
            }
          }
        }
      }
    }
  ],
  "authentication": {
    "type": "gcp_agent_identity"
  },
  "metadata": {
    "department": "iam",
    "role": "foreman",
    "runtime": "vertex-ai-agent-engine",
    "specialists": [
      "iam-adk",
      "iam-issue",
      "iam-fix-plan",
      "iam-fix-impl",
      "iam-qa",
      "iam-doc",
      "iam-cleanup",
      "iam-index"
    ]
  }
}
```

### Example 2: Worker AgentCard (iam-adk)

```json
{
  "name": "iam-adk",
  "version": "0.9.0",
  "description": "ADK/Vertex pattern analysis specialist. Analyzes agent code for compliance.",
  "spiffe_id": "spiffe://intent.solutions/agent/iam-adk/dev/us-central1/0.9.0",
  "capabilities": {
    "streaming": false
  },
  "skills": [
    {
      "skill_id": "iam.check_adk_compliance",
      "name": "Check ADK Compliance",
      "description": "Analyze agent code for ADK pattern compliance and Hard Mode rule violations",
      "input_schema": {
        "type": "object",
        "required": ["target"],
        "properties": {
          "target": {
            "type": "string",
            "description": "File path or directory to analyze"
          },
          "focus_rules": {
            "type": "array",
            "items": {
              "type": "string",
              "enum": ["R1", "R2", "R3", "R4", "R5", "R6", "R7", "R8"]
            },
            "description": "Specific Hard Mode rules to check (optional)"
          }
        }
      },
      "output_schema": {
        "type": "object",
        "required": ["compliance_status", "violations"],
        "properties": {
          "compliance_status": {
            "type": "string",
            "enum": ["COMPLIANT", "NON_COMPLIANT", "WARNING"]
          },
          "violations": {
            "type": "array",
            "items": {
              "type": "object",
              "required": ["severity", "message"],
              "properties": {
                "severity": {
                  "type": "string",
                  "enum": ["CRITICAL", "HIGH", "MEDIUM", "LOW"]
                },
                "rule": {"type": "string"},
                "message": {"type": "string"},
                "file": {"type": "string"},
                "line_number": {"type": "integer"}
              }
            }
          },
          "risk_level": {
            "type": "string",
            "enum": ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
          }
        }
      }
    }
  ],
  "authentication": {
    "type": "gcp_agent_identity"
  },
  "metadata": {
    "department": "iam",
    "role": "specialist",
    "runtime": "vertex-ai-agent-engine",
    "foreman": "iam-senior-adk-devops-lead"
  }
}
```

---

## X. Future Enhancements

### Phase 1: Basic AgentCards (Current)
- ✅ Define AgentCard structure
- ✅ Create AgentCards for foreman + one worker
- ✅ Add JSON syntax validation

### Phase 2: Full Schema Validation (Q1 2026)
- Implement full JSON Schema validation in CI
- Validate input/output payloads against declared schemas
- Add schema evolution tracking

### Phase 3: External A2A Integration (Q2 2026)
- Wire AgentCards to real A2A protocol endpoints
- Integrate with a2a-inspector for protocol validation
- Support external agent discovery via AgentCards

### Phase 4: Dynamic AgentCard Discovery (Q2 2026)
- Serve AgentCards via HTTP `/.well-known/agent-card.json`
- Enable runtime AgentCard queries
- Support multi-agent orchestration via card discovery

---

## XI. Quick Reference

### AgentCard Minimum Required Fields

```json
{
  "name": "string (required)",
  "version": "string (required, semver)",
  "description": "string (required)",
  "spiffe_id": "string (required, R7)",
  "skills": [
    {
      "skill_id": "string (required)",
      "name": "string (required)",
      "description": "string (required)",
      "input_schema": "object (required, strict)",
      "output_schema": "object (required, strict)"
    }
  ],
  "authentication": "object (required)",
  "metadata": "object (optional, but recommended)"
}
```

### Skill Naming Cheatsheet

| Pattern | Example | When to Use |
|---------|---------|-------------|
| `{dept}.check_{noun}` | `iam.check_adk_compliance` | Validation/verification |
| `{dept}.run_{noun}` | `iam.run_qa_checks` | Execution/processing |
| `{dept}.create_{noun}` | `iam.create_issue_spec` | Generation/creation |
| `{dept}.aggregate_{noun}` | `iam.aggregate_portfolio_report` | Synthesis/combination |
| `{dept}.analyze_{noun}` | `iam.analyze_agent_code` | Analysis/inspection |

### Common Schema Patterns

**File/Directory Target:**
```json
{
  "target": {
    "type": "string",
    "description": "File path or directory"
  }
}
```

**Priority Levels:**
```json
{
  "priority": {
    "type": "string",
    "enum": ["low", "medium", "high", "urgent"],
    "default": "medium"
  }
}
```

**Status Enums:**
```json
{
  "status": {
    "type": "string",
    "enum": ["ok", "error", "partial", "skipped"]
  }
}
```

**Severity Levels:**
```json
{
  "severity": {
    "type": "string",
    "enum": ["CRITICAL", "HIGH", "MEDIUM", "LOW"]
  }
}
```

---

## IX. References

**Official A2A Protocol Resources:**
- A2A Protocol Specification: https://a2a-protocol.org/
- A2A Inspector Tool: https://github.com/a2aproject/a2a-inspector
- A2A Inspector Web UI: https://a2aprotocol.ai/a2a-inspector

**Google Cloud Platform / ADK Resources:**
- Google ADK Documentation: https://cloud.google.com/vertex-ai/docs/agent-development-kit
- Vertex AI Agent Engine: https://cloud.google.com/vertex-ai/docs/agent-engine
- Agent Engine Inline Deployment Discussion: https://discuss.google.dev/t/deploying-agents-with-inline-source-on-vertex-ai-agent-engine/288935

**Related Internal Standards (Canonical Docs):**
- `000-DR-STND-adk-agent-engine-spec-and-hardmode-rules.md` - ADK/Agent Engine specification
- `000-DR-STND-inline-source-deployment-for-vertex-agent-engine.md` - Inline source deployment
- `000-DR-STND-prompt-design-a2a-contracts-iam-dept.md` - Prompt design with A2A contracts
- `000-AA-REPT-a2a-inspector-integration-for-department-adk-iam.md` - a2a-inspector integration

---

**End of Document**
