# Prompt Design for Bob and Department ADK IAM

**Document Type:** Standard (DR-STND)
**Doc ID:** 125
**Status:** Active
**Last Updated:** 2025-11-20

---

## I. Purpose and Scope

This document defines the **prompt design standard** for Bob (global orchestrator) and department ADK IAM (iam-senior-adk-devops-lead foreman + iam-* specialists).

**Purpose:**
- Establish consistent prompt engineering patterns across all agents
- Align with Google ADK best practices and A2A protocol requirements
- Define what belongs in prompts vs RAG vs documentation
- Ensure prompts support tool use, delegation, and multi-agent coordination

**Scope:**
- System prompt structure for LlmAgent instances
- A2A task prompts (structured delegation messages)
- Token budget management
- Safety and guardrail considerations
- Integration with Vertex AI Search (RAG)

---

## II. Prompt Design Philosophy

### Core Principles

**1. Prompts Define Role, RAG Provides Knowledge**
- Prompts: Role, responsibilities, workflow, tool usage, A2A coordination
- RAG: Technical details, API references, code examples, best practices
- Docs: Architecture, standards, runbooks, AARs

**2. Structured Over Chatty**
- Agents communicate via structured A2A messages (JSON-RPC 2.0)
- Task prompts are directive, not conversational
- Clear inputs/outputs, minimal ambiguity

**3. Tool-First Design**
- Prompts assume tool availability and usage
- Tools are primary action mechanism (not LLM generation)
- Tool descriptions guide agent behavior

**4. Delegation Clarity**
- Foreman prompts emphasize coordination and delegation
- Specialist prompts emphasize focused expertise
- A2A messages include context for delegated tasks

**5. Token Efficiency**
- System prompts: 500-1500 tokens (compact, focused)
- Task prompts: 100-500 tokens (directive, structured)
- Use RAG for verbose technical content

---

## III. System Prompt Structure

### Standard Template for LlmAgent

Every agent's system prompt should follow this structure:

```markdown
# Agent Name and Role

You are [AGENT_NAME], a [ROLE] in the [DEPARTMENT] department.

## Core Responsibilities

1. [Primary responsibility 1]
2. [Primary responsibility 2]
3. [Primary responsibility 3]

## Tools Available

You have access to the following tools:
- **[tool_name]**: [Brief description and when to use]
- **[tool_name]**: [Brief description and when to use]

## Workflow

When handling a task:
1. [Step 1]
2. [Step 2]
3. [Step 3]

## A2A Coordination

### As Foreman (if applicable):
- Delegate tasks to specialists via A2A protocol
- Specialists: [list of iam-* agents]
- Format delegation messages as structured JSON-RPC 2.0

### As Specialist (if applicable):
- Accept tasks from foreman via A2A protocol
- Return structured results (IssueSpec, FixPlan, QA report, etc.)
- Report failures clearly with actionable context

## Output Format

[Describe expected output structure for this agent]

## Constraints

- [Key constraint 1]
- [Key constraint 2]
- [Key constraint 3]
```

### Example: iam-senior-adk-devops-lead (Foreman)

```markdown
# IAM Senior ADK DevOps Lead - Foreman Agent

You are iam-senior-adk-devops-lead, a foreman orchestrator in the department ADK IAM.

## Core Responsibilities

1. Coordinate ADK/Vertex compliance audits across repositories
2. Delegate specialized tasks to iam-* specialist agents
3. Synthesize results and produce actionable reports
4. Manage multi-phase workflows (audit → issue → fix → QA → docs)

## Tools Available

You have access to the following tools:
- **audit_repo**: Trigger iam-adk to analyze repo for ADK pattern violations
- **create_issue**: Delegate to iam-issue to create GitHub IssueSpec
- **create_fix_plan**: Delegate to iam-fix-plan to design remediation
- **run_fix**: Delegate to iam-fix-impl to execute fixes
- **run_qa**: Delegate to iam-qa to validate changes
- **update_docs**: Delegate to iam-docs to update 000-docs/

## Workflow

When handling a compliance audit:
1. Use audit_repo to identify violations via iam-adk
2. Use create_issue to turn findings into structured IssueSpecs via iam-issue
3. Use create_fix_plan to design remediation via iam-fix-plan
4. Use run_fix to execute changes via iam-fix-impl
5. Use run_qa to validate via iam-qa
6. Use update_docs to record in AARs via iam-docs

## A2A Coordination

### As Foreman:
- Delegate tasks to 8 specialists: iam-adk, iam-issue, iam-fix-plan, iam-fix-impl, iam-qa, iam-docs, iam-cleanup, iam-index
- Format delegation messages as structured JSON-RPC 2.0 via A2A protocol
- Include context: repo path, phase, objectives, constraints
- Collect and synthesize specialist results into final report

## Output Format

Return structured workflow summary:
- Phase completed
- Specialists used
- Key findings
- Actions taken
- Next steps

## Constraints

- Never execute fixes directly; always delegate to iam-fix-impl
- Never create issues directly; always delegate to iam-issue
- Ensure all phases have corresponding AAR in 000-docs/
- Follow Hard Mode rules (R1-R8) in all recommendations
```

### Example: iam-adk (Specialist)

```markdown
# IAM ADK - ADK/Vertex Design and Analysis Specialist

You are iam-adk, an ADK/Vertex design and static analysis specialist in the department ADK IAM.

## Core Responsibilities

1. Analyze repositories for ADK pattern violations
2. Compare implementations against official ADK/Vertex documentation
3. Identify anti-patterns (LangChain, custom frameworks, Runner in gateways)
4. Produce structured findings with remediation guidance

## Tools Available

You have access to the following tools:
- **search_adk_docs**: Search official ADK documentation via Vertex AI Search
- **scan_repo**: Scan repository for ADK patterns and anti-patterns
- **compare_pattern**: Compare local code against ADK reference patterns

## Workflow

When analyzing a repository:
1. Search ADK docs to refresh current patterns
2. Scan repo for agent implementations, tools, memory wiring, A2A setup
3. Compare findings against ADK best practices
4. Identify violations and anti-patterns
5. Return structured findings with severity, location, remediation

## A2A Coordination

### As Specialist:
- Accept audit tasks from iam-senior-adk-devops-lead via A2A protocol
- Return structured findings as JSON objects (violation array)
- Include: file path, line number, pattern violated, remediation steps

## Output Format

Return findings as structured JSON array:
```json
[
  {
    "severity": "high|medium|low",
    "pattern": "R1|R2|R3|...",
    "file": "path/to/file.py",
    "line": 42,
    "violation": "Description of what's wrong",
    "remediation": "Specific steps to fix"
  }
]
```

## Constraints

- Only flag violations that contradict official ADK/Vertex docs
- Provide actionable remediation (not vague suggestions)
- Reference specific ADK documentation sections
- Flag all Hard Mode (R1-R8) violations as high severity
```

---

## IV. A2A Task Prompts

### Structured Delegation Messages

When foreman delegates to specialists, use structured JSON-RPC 2.0 messages:

**Template:**
```json
{
  "jsonrpc": "2.0",
  "id": "unique-task-id",
  "method": "invoke",
  "params": {
    "task": "audit_repo",
    "context": {
      "repo_path": "/path/to/repo",
      "phase": "phase-1-adk-alignment",
      "objectives": [
        "Identify ADK pattern violations",
        "Check Hard Mode (R1-R8) compliance"
      ],
      "constraints": [
        "Focus on agents/ directory only",
        "Flag high-severity violations only"
      ]
    }
  }
}
```

### Task Prompt Principles

**1. Directive Over Conversational**
- ❌ "Could you please help me audit this repo?"
- ✅ "Audit repo at /path/to/repo for ADK violations. Focus: agents/ directory. Phase: phase-1-adk-alignment."

**2. Structured Context**
- Include: task, repo path, phase, objectives, constraints
- Avoid: chatty explanations, unnecessary backstory

**3. Clear Success Criteria**
- Define what constitutes task completion
- Specify expected output format
- Set time/scope boundaries

**4. Error Handling**
- Specify what to do if task fails
- Define escalation path
- Request structured error reports

---

## V. Token Budget Management

### Token Allocation Strategy

**System Prompts:**
- **Bob (orchestrator)**: 1000-1500 tokens (complex coordination)
- **Foreman (iam-senior-adk-devops-lead)**: 800-1200 tokens (delegation focus)
- **Specialists (iam-*)**: 500-800 tokens (focused expertise)

**Task Prompts:**
- **Simple delegation**: 100-200 tokens
- **Complex audit**: 300-500 tokens
- **Multi-phase workflow**: 400-600 tokens

**RAG Context:**
- **ADK documentation**: 2000-4000 tokens per query
- **Internal docs (000-docs/)**: 1000-2000 tokens per query
- **Code examples**: 500-1000 tokens per snippet

### Total Context Window Budget

Assume Gemini 2.0 Flash context window: ~1M tokens

**Typical Allocation:**
```
System prompt:        1,000 tokens
Task prompt:            500 tokens
RAG context:          3,000 tokens
Conversation history: 5,000 tokens
Tool outputs:         2,000 tokens
Reserved buffer:      3,500 tokens (for safety)
-----------------------------------------
Total used:          15,000 tokens (1.5% of 1M)
```

**Safety Margin:**
- Never exceed 50% of context window (500k tokens)
- Reserve 20% for unexpected tool outputs
- Monitor token usage via telemetry

---

## VI. What Belongs Where

### Prompts (System + Task)

**Include:**
- Role and responsibilities
- Workflow and decision logic
- Tool descriptions (brief)
- A2A coordination patterns
- Output format expectations
- Critical constraints

**Exclude:**
- Technical details (API schemas, config options)
- Code examples (unless minimal illustration)
- Lengthy documentation
- Historical context (unless critical)

### RAG (Vertex AI Search)

**Include:**
- Official ADK documentation
- Vertex AI Agent Engine guides
- A2A protocol specifications
- Code examples and templates
- Best practices and patterns
- Internal 000-docs/ standards

**Exclude:**
- Operational runbooks (keep in docs for humans)
- Credentials and secrets
- Temporary or draft content

### Documentation (000-docs/)

**Include:**
- Architecture standards
- Phase plans and AARs
- Hard Mode rules (R1-R8)
- Quality gate specifications
- Deployment procedures
- Incident postmortems

**Exclude:**
- Content that changes frequently (use RAG)
- Agent-specific prompts (keep with agent code)
- Verbose API references (use RAG)

---

## VII. Safety and Guardrails

### Prompt Injection Prevention

**1. Input Validation**
- Sanitize user inputs before including in task prompts
- Escape special characters in JSON-RPC messages
- Validate A2A message structure before processing

**2. Scope Limitation**
- Define clear boundaries for agent actions
- Constrain file system access to specific directories
- Limit GCP API calls to approved operations

**3. Output Sanitization**
- Strip sensitive information from tool outputs
- Redact credentials and API keys
- Validate output format before returning to foreman

### Safety Keywords

**High-Risk Operations:**
- Deployment: "deploy", "apply", "terraform apply", "gcloud deploy"
- Deletion: "delete", "rm -rf", "DROP TABLE", "destroy"
- Credential Access: "secret", "key", "token", "password"

**Safety Rules:**
- Flag high-risk operations for human approval
- Never include credentials in prompts or outputs
- Log all destructive operations with justification

---

## VIII. Prompt Evolution and Versioning

### When to Update Prompts

**1. ADK/Vertex Documentation Changes**
- Monitor official docs for new patterns
- Update prompts to reflect latest best practices
- Document changes in AAR

**2. Agent Behavior Issues**
- If agent consistently misinterprets tasks
- If delegation patterns fail
- If tool usage is suboptimal

**3. New Capabilities**
- When new tools are added
- When new specialists join department
- When A2A protocol evolves

### Versioning Strategy

**Prompt Files:**
```
agents/iam-senior-adk-devops-lead/prompts/
├── system-prompt.md         # Current version
├── system-prompt-v1.md      # First version (archive)
├── system-prompt-v2.md      # Second version (archive)
└── CHANGELOG.md             # Version history
```

**Changelog Format:**
```markdown
# Prompt Changelog

## v3 (2025-11-20)
- Added explicit A2A delegation patterns
- Clarified specialist coordination workflow
- Reduced token count from 1200 to 900

## v2 (2025-11-15)
- Added tool descriptions
- Updated workflow steps
- Fixed ambiguity in output format

## v1 (2025-11-10)
- Initial version
```

---

## IX. Testing and Validation

### Prompt Quality Criteria

**1. Clarity**
- Can another engineer understand the agent's role from the prompt?
- Are responsibilities unambiguous?
- Is the workflow clear and actionable?

**2. Completeness**
- Does the prompt cover all expected scenarios?
- Are edge cases addressed?
- Is error handling defined?

**3. Conciseness**
- Is every sentence necessary?
- Can any section be moved to RAG or docs?
- Is token usage justified?

**4. Consistency**
- Do all department agents use similar prompt structure?
- Are naming conventions consistent?
- Do A2A patterns match across agents?

### Testing Procedure

**1. Dry Run**
- Provide prompt to agent with sample task
- Verify agent interprets task correctly
- Check tool usage and output format

**2. A2A Integration**
- Test delegation from foreman to specialist
- Verify message format (JSON-RPC 2.0)
- Confirm specialist returns expected structure

**3. Edge Cases**
- Malformed inputs
- Missing context
- Tool failures
- Timeout scenarios

**4. Token Usage**
- Measure actual token consumption
- Verify stays within budget
- Optimize if exceeding limits

---

## X. ADK-Specific Prompt Patterns

### Tool-First Thinking

ADK agents are **tool users**, not code generators.

**Pattern:**
```markdown
When handling [TASK]:
1. Use [TOOL] to [ACTION]
2. Process results
3. Use [TOOL] to [NEXT_ACTION]
4. Return structured output
```

**Anti-Pattern:**
```markdown
When handling [TASK]:
1. Analyze the problem
2. Consider various approaches
3. Generate code to solve it
4. Explain the solution
```

### Memory Integration

ADK agents use dual memory (Session + Memory Bank).

**Pattern:**
```markdown
## Memory Usage

- **Session Memory**: Current task context, intermediate results
- **Memory Bank**: Historical workflows, learned patterns, AAR insights

When starting a new task:
1. Query Memory Bank for similar past tasks
2. Load relevant context into session
3. Execute task with historical context
4. Save results to Memory Bank for future reference
```

### A2A Coordination

ADK agents communicate via A2A protocol (JSON-RPC 2.0).

**Pattern:**
```markdown
## A2A Delegation

To delegate to iam-adk:
```json
{
  "jsonrpc": "2.0",
  "id": "audit-task-001",
  "method": "invoke",
  "params": {
    "task": "audit_repo",
    "repo": "/path/to/repo",
    "focus": ["agents/", "service/"],
    "phase": "phase-1-adk-alignment"
  }
}
```

Expected response:
```json
{
  "jsonrpc": "2.0",
  "id": "audit-task-001",
  "result": {
    "findings": [...],
    "severity_counts": {...}
  }
}
```
```

---

## XI. Examples: Before and After

### Before: Chatty, Unstructured Prompt

```markdown
You are a helpful AI assistant that helps with ADK and Vertex AI tasks.
When someone asks you to audit a repository, you should look at the code
and try to find any problems with how they're using ADK. You should be
thorough and helpful, and explain what you find in a friendly way. If you
see anything that doesn't match the ADK documentation, let them know and
suggest how to fix it. You can use tools if you need to, but make sure to
explain what you're doing so the user understands.
```

**Issues:**
- Chatty and conversational (wastes tokens)
- Vague responsibilities ("try to find problems")
- No workflow structure
- No output format
- No A2A coordination
- No tool-first thinking

### After: Structured, Tool-First Prompt

```markdown
# IAM ADK - ADK/Vertex Design and Analysis Specialist

You are iam-adk, an ADK/Vertex design and static analysis specialist.

## Core Responsibilities

1. Analyze repositories for ADK pattern violations
2. Compare implementations against official ADK documentation
3. Identify anti-patterns and Hard Mode (R1-R8) violations

## Tools Available

- **search_adk_docs**: Query official ADK documentation via RAG
- **scan_repo**: Analyze repository structure and code patterns

## Workflow

When auditing a repository:
1. Use search_adk_docs to retrieve current ADK best practices
2. Use scan_repo to identify agent implementations and patterns
3. Compare findings against ADK standards
4. Return structured violation list

## Output Format

```json
[
  {
    "severity": "high",
    "file": "agents/bob/agent.py",
    "line": 42,
    "violation": "Using custom framework instead of ADK LlmAgent",
    "remediation": "Replace CustomAgent with google.adk.agents.LlmAgent"
  }
]
```

## A2A Coordination

Accept tasks from iam-senior-adk-devops-lead as JSON-RPC 2.0 messages.
Return structured findings array.
```

**Improvements:**
- Clear role and responsibilities (no ambiguity)
- Tool-first workflow (specific tools, specific actions)
- Structured output format (JSON array)
- A2A coordination defined
- Token-efficient (500 tokens vs 150+ in chatty version)

---

## XII. Integration with Vertex AI Search (RAG)

### Prompt + RAG Collaboration

**Prompts define:**
- When to query RAG
- What to query for
- How to use retrieved context

**RAG provides:**
- Technical documentation
- Code examples
- Best practices

### Example: ADK Documentation Lookup

**In System Prompt:**
```markdown
## Using RAG

When designing agent implementations:
1. Use search_adk_docs to retrieve relevant patterns
2. Query format: "ADK [TOPIC] best practices" (e.g., "ADK tool registration best practices")
3. Apply retrieved patterns to current task
4. Cross-check local code against ADK examples
```

**In Workflow:**
```markdown
When auditing memory configuration:
1. Query: "ADK dual memory Session MemoryBank patterns"
2. Retrieve: Official examples of VertexAiSessionService + VertexAiMemoryBankService
3. Compare: Local implementation vs official pattern
4. Flag: Any deviations from documented patterns
```

### RAG Query Best Practices

**Effective Queries:**
- ✅ "ADK LlmAgent tool registration examples"
- ✅ "Vertex AI Agent Engine deployment patterns"
- ✅ "A2A protocol JSON-RPC message format"

**Ineffective Queries:**
- ❌ "How do I use ADK?" (too broad)
- ❌ "agent stuff" (vague)
- ❌ "best practices" (no context)

---

## XIII. Prompt Design Checklist

Before finalizing an agent's system prompt, verify:

```markdown
□ Role clearly defined in first sentence
□ Core responsibilities listed (3-5 items)
□ Tools described with when/how to use
□ Workflow structured as numbered steps
□ A2A coordination explained (foreman or specialist)
□ Output format specified with example
□ Constraints and boundaries listed
□ Token count: 500-1500 for system prompt
□ No technical details that belong in RAG
□ No operational details that belong in 000-docs
□ Tested with sample task (dry run)
□ A2A integration tested (if applicable)
□ Versioned and logged in CHANGELOG.md
```

---

## XIV. Future Enhancements

### Phase 1: Prompt Templates (Q1 2026)
- Create prompt generator script
- Template library for common agent types
- Automated prompt validation

### Phase 2: Dynamic Prompts (Q2 2026)
- Prompt adaptation based on task complexity
- Context-aware prompt expansion
- Automatic RAG query injection

### Phase 3: Prompt Optimization (Q2 2026)
- Token usage analytics
- A/B testing for prompt variations
- Automated prompt tuning based on success rates

### Phase 4: Multi-Agent Prompt Coordination (Q3 2026)
- Shared prompt vocabulary across department
- Standardized A2A message templates
- Cross-agent prompt consistency validation

---

## XV. Related Documentation

- **123-DR-STND-a2a-inspector-usage-and-local-setup.md** - A2A testing tool
- **124-DR-STND-a2a-quality-gate-for-department-adk-iam.md** - Quality gate standard
- **000-DR-STND-adk-agent-engine-spec-and-hardmode-rules.md** - Hard Mode rules (R1-R8)
- **121-DR-MAP-adk-spec-to-implementation-and-arv.md** - Implementation mapping

---

## XVI. Quick Reference

### Prompt Design Principles

1. **Prompts = Role, RAG = Knowledge, Docs = Standards**
2. **Structured > Chatty**
3. **Tool-First > Generation-First**
4. **Directive > Conversational**
5. **Token-Efficient > Verbose**

### Token Budgets

- Bob (orchestrator): 1000-1500 tokens
- Foreman: 800-1200 tokens
- Specialists: 500-800 tokens
- Task prompts: 100-500 tokens
- RAG context: 2000-4000 tokens per query

### Common Patterns

```markdown
# [AGENT_NAME] - [ROLE]

## Core Responsibilities
1. [Primary task]
2. [Secondary task]
3. [Tertiary task]

## Tools Available
- **[tool]**: [When to use]

## Workflow
1. [Step using tool]
2. [Step using tool]
3. [Return structured output]

## A2A Coordination
[Foreman or Specialist pattern]

## Output Format
[JSON or structured format]

## Constraints
- [Key limitation]
```

---

**End of Document**
