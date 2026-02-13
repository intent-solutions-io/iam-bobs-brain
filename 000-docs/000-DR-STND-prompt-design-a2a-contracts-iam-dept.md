# Prompt Design and A2A Contract Standard for Department ADK IAM

**Document ID**: `000-DR-STND-prompt-design-a2a-contracts-iam-dept`
**Date**: 2025-11-21
**Status**: Standard - Required for all department agents
**Applies To**: Bob, iam-senior-adk-devops-lead (foreman), and all iam-* specialists

---

## Purpose

This document defines the canonical prompt design and A2A contract patterns for department adk iam. These standards ensure agents are:
- **Concise**: System prompts stay under token budgets for cost and latency
- **Contract-first**: Schemas live in code/AgentCards, not prose in prompts
- **Maintainable**: Changes to schemas don't require prompt rewrites
- **A2A-ready**: Designed for Agent-to-Agent protocol compliance

---

## Roles & Hierarchy

### Bob (Global Orchestrator)
- **Role**: Top-level orchestrator handling user requests
- **Scope**: Cross-department coordination, high-level task routing
- **Communication**: Receives natural language from users, delegates structured tasks to departments
- **Location**: `agents/bob/agent.py`

### iam-senior-adk-devops-lead (Department Foreman)
- **Role**: Department gateway between Bob and iam-* specialists
- **Scope**: ADK/Vertex AI/Agent Engine domain expertise and team coordination
- **Communication**:
  - Receives structured requests from Bob
  - Delegates to iam-* specialists via A2A protocol
  - Aggregates results and reports back to Bob
- **Location**: `agents/iam-senior-adk-devops-lead/`

### iam-* Specialists (Focused Workers)
- **Role**: Single-responsibility execution agents
- **Scope**: Narrow, well-defined tasks (ADK analysis, issue creation, fix planning, etc.)
- **Communication**:
  - Receives task JSON from foreman matching AgentCard input schema
  - Executes using tools/RAG/memory
  - Returns result JSON matching AgentCard output schema
- **Agents**:
  - `iam-adk`: ADK/Vertex design and static analysis
  - `iam-issue`: GitHub issue specification and creation
  - `iam-fix-plan`: Fix planning and design
  - `iam-fix-impl`: Implementation and coding
  - `iam-qa`: Testing and CI/CD verification
  - `iam-doc`: Documentation and AAR creation
  - `iam-cleanup`: Repository hygiene
  - `iam-index`: Knowledge management

---

## Prompt Design Rules

### Token Budget Targets

**Why Token Limits Matter:**
- Lower latency (faster first-token time)
- Lower cost (prompt tokens are charged per request)
- Forces clarity and focus
- Reduces risk of context window saturation

**Targets:**
- **Foreman**: ≤ 1,500 tokens (~2,000 words)
- **Specialists**: ≤ 1,000 tokens (~1,300 words)
- **Bob**: ≤ 2,000 tokens (global orchestrator needs more context)

**How to Stay Under Budget:**
1. No tool schemas in prompts (schemas live in AgentCards)
2. No long policy documents or business logic (use RAG/Memory Bank)
3. Reference contracts by name, don't duplicate them
4. Use bullet points, not paragraphs
5. Remove examples that belong in tests/docs

---

### System Prompt Structure

All system prompts MUST follow this structure:

#### 1. Role & Identity (Required)
```
You are [agent name], [one-sentence role description].

Identity:
- SPIFFE ID: [full SPIFFE ID]
- Role: [Foreman/Specialist/Orchestrator]
- Reports to: [parent agent]
- Manages: [child agents if applicable]
```

**Purpose**: Clear identity and position in hierarchy

#### 2. Boundaries (Required)
```
Scope:
- You ARE responsible for: [3-5 bullets]
- You are NOT responsible for: [2-3 bullets]
```

**Purpose**: Prevent scope creep and clarify delegation points

#### 3. Input/Output Contract (Required)
```
Input:
- Receive: [contract type name] from [parent agent]
- Format: JSON matching [contract name] schema

Output:
- Return: [contract type name]
- Format: JSON matching [contract name] schema
- No prose, no explanations, only structured data
```

**Purpose**: Reference contracts without duplicating schemas

#### 4. Behavior (Required for Specialists)
```
Execution Rules:
- Accept single task at a time
- No planning loops, no reflection, no "thinking out loud"
- Use tools immediately when needed
- Return results or errors, never hang
```

**Purpose**: Pure worker behavior, no autonomous exploration

#### 5. Guardrails (Optional)
```
Constraints:
- Max execution time: [N] minutes
- Max retries: [N]
- Failure handling: [return error JSON with reason]
```

**Purpose**: Operational safety nets

---

### Contract-First Design Philosophy

**Core Principle**: **Schemas live in code and AgentCards, not in prompts.**

#### Bad Example (Schema Duplication):
```markdown
You return IssueSpec with these fields:
- id: string (UUID)
- type: one of "adk_violation", "pattern_drift", "security"
- severity: one of "critical", "high", "medium", "low"
- title: string (max 100 chars)
- description: string
- file_path: optional string
- line_start: optional integer
...
```
❌ **Problems**:
- 15+ lines of prompt tokens wasted
- Schema changes require prompt updates
- Easy to get out of sync with actual code

#### Good Example (Contract Reference):
```markdown
Output:
- Return: IssueSpec (defined in agents/shared_contracts.py)
- Format: JSON matching IssueSpec dataclass
- See AgentCard for exact schema
```
✅ **Benefits**:
- 3 lines instead of 15+
- Schema lives in single source of truth (code)
- AgentCard JSON schema is generated from dataclass

---

### What Belongs Where

| Content Type | Belongs In | Does NOT Belong In |
|--------------|-----------|-------------------|
| **Role definition** | System prompt | ❌ |
| **Execution rules** | System prompt | ❌ |
| **Contract names** | System prompt | ❌ |
| **JSON schemas** | ❌ | AgentCard + dataclasses |
| **Tool descriptions** | ❌ | AgentCard + tool code |
| **Business logic** | ❌ | Tool implementations |
| **Policy documents** | ❌ | RAG/Memory Bank/docs |
| **Long examples** | ❌ | Tests + documentation |
| **Changelog** | ❌ | Git history + AARs |

---

## A2A / AgentCard Integration

### AgentCard Location
Each agent MUST have an AgentCard at:
```
agents/<agent_name>/.well-known/agent-card.json
```

### AgentCard Contents
```json
{
  "name": "iam-adk",
  "description": "ADK/Vertex design and static analysis specialist",
  "version": "0.1.0",
  "spiffe_id": "spiffe://intent.solutions/agent/iam-adk/dev/us-central1/0.1.0",
  "authentication": {
    "required": true,
    "methods": ["spiffe"]
  },
  "skills": [
    {
      "name": "analyze_adk_patterns",
      "description": "Analyze repository for ADK pattern compliance",
      "input_schema": { "$ref": "#/components/schemas/AnalysisRequest" },
      "output_schema": { "$ref": "#/components/schemas/AnalysisReport" }
    }
  ],
  "components": {
    "schemas": {
      "AnalysisRequest": { ... },
      "AnalysisReport": { ... }
    }
  }
}
```

### Schema Alignment
1. **Python contracts** define the canonical structure (`agents/shared_contracts.py`)
2. **AgentCard JSON schemas** mirror the Python contracts
3. **System prompts** reference the contract names only

**Workflow:**
1. Define/update Python dataclass (e.g., `IssueSpec`)
2. Generate/update AgentCard JSON schema to match
3. System prompt says "Returns IssueSpec" (no schema duplication)

### Validation
Two-layer validation ensures compliance:
1. **Static** (CI): `scripts/check_a2a_contracts.py` validates AgentCard structure
2. **Runtime** (optional): a2a-inspector web UI tests actual behavior

See: `tools/a2a-inspector/README.md` for details

---

## Foreman-Specific Patterns

### Orchestrator Responsibilities
The foreman is a **middle manager**, not a worker. It must:
1. **Analyze incoming requests** from Bob
2. **Plan workflows** (which specialists, in what order)
3. **Delegate tasks** to specialists via A2A
4. **Aggregate results** from specialists
5. **Report back** to Bob with unified output

### Delegation Pattern
```
Input from Bob → Analyze → Plan Workflow → Delegate to Specialists → Aggregate → Output to Bob
```

### Multi-Specialist Coordination
- **Sequential**: When outputs depend on each other (e.g., fix-plan → fix-impl → qa)
- **Parallel**: When tasks are independent (e.g., doc + cleanup)
- **Conditional**: Based on specialist outputs (e.g., only doc if qa passes)

### Foreman Prompt Constraints
- Must reference specialist capabilities by name
- Must NOT duplicate specialist logic
- Must define clear aggregation rules
- Should handle specialist failures gracefully

---

## Specialist-Specific Patterns

### Pure Worker Behavior
Specialists are **executors**, not planners. They must:
1. **Accept structured input** matching AgentCard schema
2. **Execute immediately** using tools/RAG/memory
3. **Return structured output** matching AgentCard schema
4. **No autonomous exploration** or reflection loops

### Specialist Prompt Template
```markdown
You are [name], a specialist worker for [specific task].

Identity:
- SPIFFE ID: [full ID]
- Reports to: iam-senior-adk-devops-lead
- Scope: [1-2 sentences]

Behavior:
- Accept single task JSON matching [InputType]
- Execute using tools: [tool1, tool2, ...]
- Return JSON matching [OutputType]
- No planning, no reflection, no loops

Output Format:
- Success: { "status": "success", "result": [OutputType] }
- Error: { "status": "error", "reason": "..." }

Contract: [InputType] → [OutputType] (defined in agents/shared_contracts.py)
```

### Tool Usage
- Specialists MAY use tools, but tool schemas are NOT in the prompt
- Tools are wired at agent creation time (in `agent.py`)
- AgentCard lists available tools by name only

---

## Security & IAM Mindset

### SPIFFE Identity
Every agent has a unique SPIFFE ID:
```
spiffe://intent.solutions/agent/<agent-name>/<env>/<region>/<version>
```

**Examples:**
- `spiffe://intent.solutions/agent/bob/prod/us-central1/1.0.0`
- `spiffe://intent.solutions/agent/iam-adk/dev/us-central1/0.1.0`

### Least Privilege Principle
- **Bob**: Broad view, can access any department
- **Foreman**: Department-scoped, can access all iam-* specialists
- **Specialists**: Narrow scope, minimal access

**Implication for Prompts:**
- Foreman prompt: "You coordinate iam-* specialists"
- Specialist prompt: "You only do [narrow task], delegate everything else"

### Service Account Mapping (Future)
Each agent will eventually have its own GCP service account:
- Bob → `bob@bobs-brain.iam.gserviceaccount.com`
- Foreman → `iam-foreman@bobs-brain.iam.gserviceaccount.com`
- Specialists → `iam-adk@bobs-brain.iam.gserviceaccount.com`, etc.

**Prompt Impact**: Minimal, but agents should assume they operate under restricted permissions.

---

## Migration Checklist

When updating an existing agent to follow this standard:

- [ ] **Measure current prompt size** (use token counter)
- [ ] **Identify schema duplication** (grep for JSON examples in prompt)
- [ ] **Extract schemas** to AgentCard and shared_contracts.py
- [ ] **Rewrite prompt** using template above
- [ ] **Verify token count** (must be under target)
- [ ] **Update AgentCard** to match new contracts
- [ ] **Test A2A compliance** (static validator + optional inspector)
- [ ] **Update tests** if prompt structure changed
- [ ] **Commit with clear message**: `refactor(agents): migrate [agent] to contract-first prompt design`

---

## Examples

### Before (Schema Duplication)
```markdown
You are iam-issue. You create GitHub issues.

When you receive a request, analyze it and return:
{
  "id": "string (UUID)",
  "type": "string (one of: adk_violation, pattern_drift, security, performance, tech_debt, missing_doc, config_error)",
  "severity": "string (one of: critical, high, medium, low, info)",
  "title": "string (max 100 characters)",
  "description": "string (markdown formatted)",
  "file_path": "string (optional, path to affected file)",
  "line_start": "integer (optional)",
  "line_end": "integer (optional)",
  ...
}

Always include all fields. If optional fields are not applicable, use null.
Make sure the title is concise...
```
**Token count**: ~200 tokens for schema alone

### After (Contract Reference)
```markdown
You are iam-issue, a specialist worker for GitHub issue creation.

Identity:
- SPIFFE ID: spiffe://intent.solutions/agent/iam-issue/dev/us-central1/0.1.0
- Reports to: iam-senior-adk-devops-lead

Behavior:
- Accept: AnalysisReport (from iam-adk)
- Execute: Create IssueSpec with title, body, labels
- Return: IssueSpec (JSON)

Contract: AnalysisReport → IssueSpec (defined in agents/shared_contracts.py)

Guardrails:
- Max issues per request: 10
- Return error if analysis invalid
```
**Token count**: ~80 tokens (60% reduction)

---

## Enforcement

### CI/CD Integration
- Static validator (`scripts/check_a2a_contracts.py`) runs in CI
- Fails if AgentCards invalid or missing required fields
- Part of ARV gate for agent readiness

### Code Review Checklist
When reviewing prompt changes:
1. Is the prompt under token budget?
2. Does it reference contracts, not duplicate schemas?
3. Is the AgentCard updated to match?
4. Are there examples that should live in tests/docs instead?

### Monitoring (Future)
- Track prompt token usage in telemetry
- Alert if prompts grow beyond budgets
- Dashboard showing prompt sizes over time

---

## References

- **Contract Definitions**: `agents/shared_contracts.py`
- **A2A Validation**: `tools/a2a-inspector/README.md`
- **AgentCard Standard**: `000-docs/000-DR-STND-agentcards-and-a2a-contracts.md` (if exists)
- **ADK Documentation**: `https://google.github.io/adk-docs/`
- **A2A Protocol Spec**: `https://a2a-protocol.org/`

---

## Summary

**Golden Rules:**
1. ✅ Prompts ≤ 1,500 tokens (foreman) / ≤ 1,000 tokens (specialist)
2. ✅ Schemas in code/AgentCards, NOT in prompts
3. ✅ Contracts referenced by name only
4. ✅ AgentCards aligned with shared_contracts.py
5. ✅ Specialists are pure workers (no planning loops)
6. ✅ Foreman is orchestrator (delegates, aggregates)

**Template**: Use the structures in this doc for all new agents and migrate existing agents during updates.

---

**Document Prepared By**: Build Captain (Claude Code)
**Review Status**: Standard - Required for all department adk iam agents
**Next Action**: Apply to foreman + iam-adk (Phase 1), then roll out to remaining specialists

---

**Change Log**:
- 2025-11-21: Initial version (Phase: Prompt + AgentCard Alignment 1)
