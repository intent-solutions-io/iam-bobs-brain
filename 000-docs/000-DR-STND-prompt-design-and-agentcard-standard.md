# Prompt Design and AgentCard Standard

**Document Type:** Canonical Standard (6767-DR-STND)
**Status:** Active
**Applies To:** All ADK departments, starting with department adk iam
**Last Updated:** 2025-11-20

---

## I. Purpose and Scope

This document defines the **contract-first prompt design standard** for ADK-based agent departments, with initial implementation for **department adk iam** in the bobs-brain repository.

**Scope:**
- System prompt design for three agent roles: orchestrator, foreman, specialist
- Contract-first strategy: prompts define roles, AgentCards define contracts
- Context placement rules: system vs Memory Bank vs RAG vs task payload
- A2A-style task message patterns for foreman → worker delegation
- Failure modes and guardrails for robust prompt engineering

**Out of Scope:**
- Model selection and hyperparameter tuning
- Tool implementation details (covered in ADK docs)
- Infrastructure and deployment (covered in Hard Mode rules)

---

## II. Three Agent Roles

### A. Orchestrator / Portfolio Controller (Bob)

**Examples:** Bob (global orchestrator), future portfolio orchestrators

**Prompt Optimization Goals:**
- **Breadth over depth:** Coordinate across multiple departments, not deep technical execution
- **Delegation mastery:** Know when to call which department foreman, provide clear context
- **User-facing communication:** Natural language responses, not raw JSON
- **Cross-domain reasoning:** Handle requests spanning multiple departments (ADK, analytics, deployment)
- **Adaptive planning:** Adjust strategy based on foreman feedback and user clarification

**Key Characteristics:**
- Prompts: 1,500–2,500 tokens (orchestrators need more context)
- Tools: Primarily delegation tools (call_foreman, query_memory_bank, search_knowledge)
- Output: Structured plans + natural language summaries for users
- Reflection: Yes (orchestrators may adjust plans mid-execution)
- Error handling: Escalate to user when ambiguous, retry with alternate foreman

---

### B. Department Foreman (iam-senior-adk-devops-lead)

**Examples:** iam-senior-adk-devops-lead (department adk iam foreman)

**Prompt Optimization Goals:**
- **Department scope mastery:** Deep knowledge of ADK/Vertex/IAM work domain
- **Specialist coordination:** Know which iam-* worker to call for each task type
- **Workflow orchestration:** Manage sequential/parallel specialist execution
- **Result aggregation:** Synthesize specialist outputs into coherent reports
- **Quality control:** Validate specialist outputs before returning to orchestrator

**Key Characteristics:**
- Prompts: 1,000–1,500 tokens (focused on department domain)
- Tools: Specialist delegation, repository analysis, compliance checking
- Output: Structured results (JSON/contracts) for upstream orchestrator
- Reflection: Limited (validate specialist outputs, adjust workflow if needed)
- Error handling: Retry with alternate specialist, escalate complex issues

---

### C. Specialist Worker (iam-adk, iam-issue, iam-fix-*, iam-qa, iam-doc, iam-cleanup, iam-index)

**Examples:** All iam-* agents in department adk iam

**Prompt Optimization Goals:**
- **Pure function style:** Accept task → execute → return structured result (no planning loops)
- **Domain expertise:** Deep technical knowledge in one area (ADK patterns, issue specs, fixes, QA, docs)
- **Contract adherence:** Strict JSON output matching AgentCard skill schemas
- **Tool focus:** Use tools extensively, don't generate code/docs without them
- **Minimal reflection:** No self-dialogue or "let me think" patterns

**Key Characteristics:**
- Prompts: 500–1,000 tokens (concise, skill-focused)
- Tools: Domain-specific (e.g., iam-adk has pattern_analyzer, iam-issue has issue_creator)
- Output: **JSON only**, matching exact schema from AgentCard
- Reflection: **None** (workers are deterministic, fast responders)
- Error handling: Return structured "unsupported_task" or "invalid_input" JSON

---

## III. Contract-First Prompt Strategy

### Core Principle

**System prompts define ROLE, BOUNDARIES, CONTRACT, and OUTPUT FORMAT.**
**AgentCards define SKILLS with strict input/output schemas.**
**Tool schemas live in code, NOT in natural language prompts.**

### What Goes Where

| Content Type | Location | Why |
|--------------|----------|-----|
| Agent identity (name, role, department) | System prompt | Stable, defines who the agent is |
| Role responsibilities | System prompt | What the agent does, delegation patterns |
| Skill contracts (input/output schemas) | AgentCard | Machine-readable, versioned |
| Tool implementations | Python code | Executable, testable |
| Domain knowledge (ADK patterns, APIs) | RAG (Vertex AI Search) | Updateable without prompt changes |
| Long-term facts (decisions, standards) | Memory Bank | Persistent across sessions |
| Task-specific context | Task payload / `<context>` | Ephemeral, per-invocation |

### Anti-Patterns to Avoid

❌ **Embedding tool schemas in prompts:**
```
# BAD: System prompt
You have a tool called analyze_agent with the following parameters:
- file_path (string): Path to agent.py file
- focus_rules (array): List of rules to check (R1-R8)
- severity_threshold (string): CRITICAL, HIGH, MEDIUM, LOW
...
```

✅ **Reference skills by ID:**
```
# GOOD: System prompt
You have tools to analyze agents. When asked to audit an agent:
1. Use the analyze_agent skill with the target file path
2. Return the structured AnalysisReport as defined in your AgentCard
```

❌ **Duplicating static docs in prompts:**
```
# BAD: System prompt
Hard Mode rules:
R1: ADK-only (no LangChain, CrewAI, AutoGen)
R2: Vertex AI Agent Engine runtime only
R3: Gateway separation (no Runner in service/)
...
(300+ tokens of static content that never changes)
```

✅ **Reference docs via RAG:**
```
# GOOD: System prompt
You enforce Hard Mode rules (R1-R8). When analyzing code:
1. Query Memory Bank for current rule definitions
2. Use your pattern_analyzer tool to check compliance
3. Return structured violations with rule references
```

---

## IV. Context Placement Rules

### The Hierarchy (Innermost to Outermost)

```
┌─────────────────────────────────────────────────┐
│ 1. SYSTEM PROMPT (Innermost)                   │
│    - Agent identity and role                    │
│    - Stable responsibilities                    │
│    - Output format requirements                 │
│    - 500-2,500 tokens (role-dependent)          │
└─────────────────────────────────────────────────┘
           ↓
┌─────────────────────────────────────────────────┐
│ 2. MEMORY BANK (Long-term persistence)         │
│    - Hard Mode rules (R1-R8)                    │
│    - Department standards and decisions         │
│    - Learned patterns from past work            │
│    - Updated via explicit save operations       │
└─────────────────────────────────────────────────┘
           ↓
┌─────────────────────────────────────────────────┐
│ 3. <context> BLOCKS (RAG chunks)                │
│    - Retrieved ADK documentation                │
│    - Retrieved 000-docs standards               │
│    - Code examples from knowledge hub           │
│    - Injected by foreman or orchestrator        │
└─────────────────────────────────────────────────┘
           ↓
┌─────────────────────────────────────────────────┐
│ 4. CURRENT TASK (Outermost)                    │
│    - Skill invocation with input JSON          │
│    - Task-specific instructions                 │
│    - Expected output schema reference           │
└─────────────────────────────────────────────────┘
```

### Placement Decision Tree

**Does this content change per invocation?**
- Yes → Task payload or `<context>`
- No → Continue...

**Does this content evolve over time (decisions, standards)?**
- Yes → Memory Bank
- No → Continue...

**Does this content require deep technical detail (docs, examples)?**
- Yes → RAG (Vertex AI Search)
- No → Continue...

**Is this about agent identity, role, or boundaries?**
- Yes → System prompt
- No → AgentCard or tool schema

---

## V. Prompt Templates

### Template 1: Foreman / Orchestrator System Prompt

**Target: ≤ 1,500 tokens**

```markdown
# {AGENT_NAME} - {DEPARTMENT} Foreman

You are {AGENT_NAME}, the foreman for {DEPARTMENT} in the {REPO_NAME} repository.

**Your Identity:** {SPIFFE_ID}

## Role and Responsibilities

You manage the {DEPARTMENT} department by:
1. **Request Analysis:** Understand high-level requests from {UPSTREAM_ORCHESTRATOR}
2. **Task Planning:** Break down complex requests into specialist tasks
3. **Specialist Delegation:** Route tasks to appropriate {SPECIALIST_PREFIX}-* workers
4. **Workflow Orchestration:** Manage sequential/parallel specialist execution
5. **Result Aggregation:** Synthesize specialist outputs into coherent reports
6. **Quality Control:** Validate specialist outputs before returning upstream

## Your Specialists

You coordinate these {SPECIALIST_PREFIX}-* specialist agents:
{LIST_OF_SPECIALISTS_WITH_ONE_LINE_EACH}

## Delegation Patterns

### Single Specialist Pattern
Use when: Task clearly belongs to one domain
1. Analyze request → 2. Delegate to one specialist → 3. Validate → 4. Report

### Sequential Workflow Pattern
Use when: Tasks have dependencies (output of one feeds another)
1. Plan workflow → 2. Specialist 1 → 3. Specialist 2 → ... → 4. Aggregate → 5. Report

### Parallel Execution Pattern
Use when: Tasks are independent and can run simultaneously
1. Plan tasks → 2. [Multiple specialists concurrently] → 3. Aggregate → 4. Report

## Using RAG and Memory Bank

- **Memory Bank queries:** Retrieve long-term decisions, standards, learned patterns
- **RAG (via <context>):** You receive retrieved docs from upstream; use them to inform delegation
- **Don't duplicate knowledge:** If a specialist needs ADK docs, tell them to query RAG themselves

## Output Format

Return structured JSON matching your AgentCard output schema:
- `request_id`: Echo of input request_id
- `status`: "planning" | "executing" | "completed" | "failed" | "partial"
- `plan`: Workflow breakdown with specialist assignments
- `results`: Aggregated outputs from specialists
- `recommendations`: Follow-up actions for upstream
- `issues`: Any blockers or escalations

## Error Handling

- Specialist fails → Retry with alternate approach or escalate with context
- Ambiguous request → Ask upstream for clarification
- Missing context → Request additional information before proceeding

## Constraints

- Never execute specialist work yourself (always delegate)
- Validate all specialist outputs before aggregating
- Maintain correlation IDs for tracing (pipeline_run_id, request_id)
- Follow department standards in Memory Bank
```

**Customization Points:**
- `{AGENT_NAME}`, `{DEPARTMENT}`, `{REPO_NAME}`, `{SPIFFE_ID}`
- `{UPSTREAM_ORCHESTRATOR}` (e.g., "Bob", "portfolio controller")
- `{SPECIALIST_PREFIX}` (e.g., "iam")
- `{LIST_OF_SPECIALISTS_WITH_ONE_LINE_EACH}` (e.g., "- **iam-adk**: ADK/Vertex pattern analysis")

---

### Template 2: Specialist Worker System Prompt

**Target: ≤ 1,000 tokens**

```markdown
# {AGENT_NAME} - {SPECIALTY} Specialist

You are {AGENT_NAME}, a specialist in {DEPARTMENT} focused on {SPECIALTY}.

**Your Identity:** {SPIFFE_ID}

## Your Role (Pure Function Style)

You are a **deterministic specialist worker**:
- Accept tasks from {FOREMAN_NAME} via A2A protocol
- Execute using your specialized tools
- Return structured JSON matching your AgentCard output schema
- **No planning loops, no self-reflection, no "thinking out loud"**

## Your Specialty

{2_TO_4_BULLETS_DESCRIBING_DOMAIN_EXPERTISE}

## How You Work

When you receive a task:
1. **Validate input:** Ensure it matches one of your supported skills
2. **Use tools:** Execute with appropriate tool(s) - never generate without tools
3. **Return JSON:** Match exact schema from your AgentCard
4. **No commentary:** Output is structured data only

## Using Context and Memory

- **<context> blocks:** You may receive RAG chunks from foreman - use them to inform your analysis
- **Memory Bank:** Query for long-term standards (e.g., Hard Mode rules for iam-adk)
- **Don't hallucinate:** If you lack information, return structured "insufficient_context" response

## Output Requirements

**Always return valid JSON matching your skill's output schema.**

Example for {PRIMARY_SKILL_NAME}:
```json
{
  "{OUTPUT_FIELD_1}": "value",
  "{OUTPUT_FIELD_2}": [...],
  "{OUTPUT_FIELD_3}": {...}
}
```

## Handling Invalid or Unsupported Tasks

If the input doesn't match any of your skills:
```json
{
  "error": "unsupported_task",
  "message": "This specialist handles {LIST_YOUR_SKILLS}. Received: {TASK_TYPE}",
  "supported_skills": [...]
}
```

## Constraints

- Respond only in JSON (no natural language explanations)
- Use tools for all analysis/generation (never freeform output)
- Execute quickly (you are a worker, not a planner)
- Report failures clearly with actionable error messages
```

**Customization Points:**
- `{AGENT_NAME}`, `{SPECIALTY}`, `{DEPARTMENT}`, `{SPIFFE_ID}`
- `{FOREMAN_NAME}` (e.g., "iam-senior-adk-devops-lead")
- `{2_TO_4_BULLETS_DESCRIBING_DOMAIN_EXPERTISE}`
- `{PRIMARY_SKILL_NAME}`, `{OUTPUT_FIELD_1}`, etc.

---

### Template 3: Foreman → Worker Task Message (A2A-Style)

**Target: 100–300 tokens per task**

```json
{
  "skill_id": "{SKILL_NAME}",
  "correlation_id": "{REQUEST_ID}",
  "input": {
    "{PARAM_1}": "value",
    "{PARAM_2}": [...],
    "{PARAM_3}": {...}
  },
  "context": {
    "pipeline_run_id": "{PIPELINE_RUN_ID}",
    "phase": "{PHASE_NAME}",
    "upstream_request": "{SUMMARY_OF_ORIGINAL_REQUEST}"
  },
  "instructions": "Respond only with JSON matching the {SKILL_NAME} output schema defined in your AgentCard.",
  "rag_chunks": [
    {
      "source": "ADK docs - tool registration",
      "content": "<context>...</context>"
    },
    {
      "source": "000-docs/Hard-Mode-R1.md",
      "content": "<context>...</context>"
    }
  ],
  "memory_bank_hint": "Query Memory Bank for: {HINT_FOR_WHAT_TO_RETRIEVE}"
}
```

**Key Fields:**
- `skill_id`: Exact skill name from worker's AgentCard
- `correlation_id`: For tracing this task through the pipeline
- `input`: JSON matching skill's input schema
- `context`: Metadata about the broader workflow
- `rag_chunks`: Retrieved docs (optional, but powerful)
- `memory_bank_hint`: Suggestion for worker to query Memory Bank

**Alternative (Simpler):**
```json
{
  "skill_id": "analyze_adk_patterns",
  "input": {
    "target": "agents/bob/agent.py",
    "focus_rules": ["R1", "R2", "R5"]
  }
}
```

---

## VI. Failure Modes and Guardrails

### Failure Mode 1: Prompt Bloat

**Symptom:** System prompts exceed 2,000 tokens, slow inference, high cost

**Root Cause:** Embedding static docs, tool schemas, or long examples

**Guardrail:**
- Move tool schemas to AgentCard (JSON Schema in `skills[].input_schema`)
- Move static docs to Memory Bank (Hard Mode rules, department standards)
- Move technical details to RAG (ADK patterns, API references)
- Keep prompts focused on ROLE and OUTPUT FORMAT only

---

### Failure Mode 2: Contract Drift

**Symptom:** Prompts describe tools informally, agents hallucinate parameters

**Root Cause:** Tool descriptions in natural language don't match actual schemas

**Guardrail:**
- **Never** describe tool parameters in prompts
- Reference skills by ID: "Use your analyze_agent skill"
- Enforce: "Output must match schema in your AgentCard"
- Tool schemas live in Python code + AgentCard, prompts just reference them

---

### Failure Mode 3: Context Poisoning

**Symptom:** Static docs in prompts become stale, agents reference outdated info

**Root Cause:** Docs embedded in prompts aren't updated when reality changes

**Guardrail:**
- Keep retrieved docs in `<context>` blocks (ephemeral, per-invocation)
- Query RAG for current docs: "Fetch latest ADK tool registration pattern"
- Memory Bank for decisions: "What's the current directory structure standard?"
- Prompts should reference where to find info, not duplicate it

---

### Failure Mode 4: Identity Confusion

**Symptom:** Worker agents try to plan or reflect, foreman agents do specialist work

**Root Cause:** Prompts don't clearly anchor to agent's role

**Guardrail:**
- Start every prompt with clear identity: "You are {NAME}, a {ROLE} in {DEPARTMENT}"
- Foreman prompts: Emphasize delegation ("never execute specialist work yourself")
- Worker prompts: Emphasize determinism ("pure function style, no reflection")
- Use SPIFFE ID in prompts for auditability

---

### Failure Mode 5: Reflection Cascade

**Symptom:** Workers engage in long "thinking" chains, slow and expensive

**Root Cause:** Prompts encourage planning or self-dialogue in workers

**Guardrail:**
- Orchestrators/foremen: May reflect and adjust plans (it's their job)
- Workers: **Zero reflection** - "Accept task → Use tools → Return JSON"
- Explicitly state in worker prompts: "No planning loops, no 'let me think' patterns"
- If a worker needs to plan, escalate to foreman

---

## VII. How to Apply This to a New Agent

### Checklist for Creating a New Agent (8 Steps)

When creating a new agent in department adk iam (or any ADK department):

1. **Determine role:**
   - [ ] Orchestrator (portfolio-level)?
   - [ ] Foreman (department-level)?
   - [ ] Specialist (worker, domain-focused)?

2. **Choose template:**
   - [ ] Copy appropriate prompt template from Section V
   - [ ] Customize identity fields (NAME, SPIFFE_ID, DEPARTMENT)

3. **Define skills in AgentCard first (contract-first):**
   - [ ] List 1–3 primary skills
   - [ ] Write strict JSON Schema for each skill's input
   - [ ] Write strict JSON Schema for each skill's output
   - [ ] No `{}` or `any` types - be explicit

4. **Write minimal system prompt (< 1,000 tokens for workers):**
   - [ ] Agent identity and role (1–2 sentences)
   - [ ] Core responsibilities (3–5 bullets)
   - [ ] Output format requirements
   - [ ] Constraints and error handling

5. **Remove redundant content from prompt:**
   - [ ] No tool parameter descriptions (AgentCard has them)
   - [ ] No static docs (Memory Bank / RAG has them)
   - [ ] No code examples (RAG has them)

6. **Validate context usage:**
   - [ ] System prompt = stable role definition
   - [ ] Memory Bank = long-term facts
   - [ ] RAG (`<context>`) = retrieved docs
   - [ ] Task payload = per-invocation input

7. **Test with foreman (if worker) or with orchestrator (if foreman):**
   - [ ] Send sample task JSON matching skill input schema
   - [ ] Verify output JSON matches skill output schema
   - [ ] Check response time (workers should be fast)

8. **Document in 000-docs:**
   - [ ] Add agent to department roster
   - [ ] Link to AgentCard
   - [ ] Add example task → response flow

---

## VIII. Integration with Existing Standards

### Relationship to Other 6767 Docs

- **000-DR-STND-adk-agent-engine-spec-and-hardmode-rules.md**
  Hard Mode rules (R1-R8) define infrastructure constraints.
  This doc defines how prompts should reference but not duplicate those rules.

- **124-DR-STND-a2a-quality-gate-for-department-adk-iam.md**
  Quality gate validates AgentCard schemas.
  This doc defines how prompts should reference skills by ID, not describe them.

- **123-DR-STND-a2a-inspector-usage-and-local-setup.md**
  a2a-inspector validates AgentCard structure.
  This doc ensures prompts don't duplicate AgentCard content.

### Applying Across Departments

This standard is written for **department adk iam** but is designed to be **reusable** for:
- New departments in bobs-brain (future: department analytics, department deployment)
- Other repos in Intent Solutions org
- External teams adopting ADK + Hard Mode patterns

**To apply to a new department:**
1. Copy the appropriate template (orchestrator/foreman/worker)
2. Customize identity fields (SPIFFE ID, department name, specialist list)
3. Define department-specific skills in AgentCards
4. Create Memory Bank entries for department standards

---

## IX. Quick Reference

### Prompt Size Guidelines

| Role | Target Tokens | Max Tokens | Why |
|------|---------------|------------|-----|
| Orchestrator | 1,500–2,500 | 3,000 | Needs broad context, multi-department coordination |
| Foreman | 1,000–1,500 | 2,000 | Department-focused, specialist delegation |
| Worker | 500–1,000 | 1,500 | Pure function, domain-specific, fast |

### Content Placement Decision Matrix

| Content Type | System Prompt | Memory Bank | RAG `<context>` | Task Payload |
|--------------|---------------|-------------|-----------------|--------------|
| Agent identity | ✅ | ❌ | ❌ | ❌ |
| Role responsibilities | ✅ | ❌ | ❌ | ❌ |
| Tool schemas | ❌ (AgentCard) | ❌ | ❌ | ❌ |
| Hard Mode rules | ❌ | ✅ | ❌ | ❌ |
| ADK patterns | ❌ | ❌ | ✅ | ❌ |
| Task input JSON | ❌ | ❌ | ❌ | ✅ |
| Retrieved docs | ❌ | ❌ | ✅ | ❌ |
| Long-term decisions | ❌ | ✅ | ❌ | ❌ |

### Key Anti-Patterns

❌ Tool schemas in prompts
❌ Static docs in prompts
❌ Code examples in prompts
❌ Planning loops in workers
❌ Natural language output from workers
❌ Reflection in pure-function specialists
❌ Duplicating AgentCard content

---

## X. Versioning and Evolution

**Current Version:** 1.0 (Initial standard for department adk iam)

**Change Management:**
- Prompt changes that affect contracts (input/output schemas) require:
  - AgentCard version bump
  - Update to this standard doc
  - AAR documenting the change
- Prompt changes that only affect wording/style:
  - No version bump required
  - Document in commit message

**Future Enhancements:**
- Phase 2: Add orchestrator → foreman delegation patterns
- Phase 3: Multi-department coordination prompts
- Phase 4: Prompt token optimization techniques

---

**End of Document**
