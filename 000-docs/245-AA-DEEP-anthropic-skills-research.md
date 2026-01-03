# Anthropic Skills Research - Deep Dive Analysis

**Document ID:** 245-AA-DEEP-anthropic-skills-research
**Date:** 2026-01-02
**Author:** Claude Code
**Status:** COMPLETE
**Beads Story:** bobs-brain-kpe.3

---

## 1. What It Is (Executive Summary)

**Anthropic Skills** are folders of instructions, scripts, and resources that Claude loads dynamically to improve performance on specialized tasks. A skill teaches Claude how to complete specific tasks repeatably through a `SKILL.md` file containing YAML frontmatter and markdown instructions.

Skills enable "golden path packaging" - encapsulating best practices into reusable, discoverable units that Claude automatically invokes when context matches the skill's description.

---

## 2. Key Primitives to Implement/Integrate

### 2.1 SKILL.md File Structure

**Basic Format (Anthropic Standard):**
```markdown
---
name: my-skill-name
description: A clear description of what this skill does and when to use it
---

# My Skill Name

[Instructions Claude follows when skill is active]

## Examples
- Example usage 1

## Guidelines
- Guideline 1
```

**Extended Format (User's Nixtla Standard):**
```markdown
---
name: skill-name
description: "What it does. Use when X. Trigger with 'phrase1', 'phrase2'."
allowed-tools: Read,Write,Bash
version: 1.0.0
author: Jeremy Longshore <jeremy@intentsolutions.io>
license: MIT
tags:
  - category
  - subcategory
---

# Skill Title

Brief purpose statement.

## Overview
Detailed description.

### Key Capabilities
- Capability 1
- Capability 2

### When to Use
- Use case 1
- Use case 2

## Prerequisites
- Prerequisite 1

## Instructions
### Step 1: Action
Instructions...

## Output
- Output 1

## Error Handling
### Error Name
**Cause**: ...
**Solution**: ...

## Examples
### Example 1: Title
**Input**: ...
**Output**: ...

## Resources
- {baseDir}/references/doc.md
```

### 2.2 YAML Frontmatter Fields

| Field | Required | Max Length | Purpose |
|-------|----------|------------|---------|
| `name` | Yes | 64 chars | Identifier for Skill tool invocation |
| `description` | Yes | 1024 chars | Primary signal for Claude's selection |
| `allowed-tools` | No | - | Pre-approved tools during execution |
| `version` | No | - | Semantic versioning |
| `author` | No | - | Author metadata |
| `license` | No | - | License metadata |
| `tags` | No | - | Categorization |
| `mode` | No | boolean | `true` = appears in Mode Commands |
| `disable-model-invocation` | No | boolean | `true` = requires manual `/skill-name` |
| `when_to_use` | No | - | Appends to description (undocumented) |

### 2.3 Directory Structure

```
skill-name/
├── SKILL.md              # Core prompt + frontmatter (required)
├── scripts/              # Python/Bash executables
├── references/           # Documentation loaded via Read tool
└── assets/               # Templates, static files
```

### 2.4 {baseDir} Variable

Template variable resolving to skill installation directory:

```markdown
## Resources
- Skill standard: `{baseDir}/references/skill-standard.md`
```

**CRITICAL**: Never hardcode absolute paths.

### 2.5 Skill Selection Mechanism

Claude decides skill invocation through **pure language understanding**:

1. Claude receives Skill tool with `<available_skills>` section
2. Each skill formatted as: `"skill-name": description`
3. Claude's transformer matches user intent to descriptions
4. Claude invokes Skill tool with matching `command`

**No embeddings, regex, or classifiers** - pure LLM reasoning.

### 2.6 Execution Flow

1. User request matches skill description
2. Claude invokes `Skill` tool with `command: "skill-name"`
3. Two messages injected:
   - **Visible**: `<command-message>The "skill-name" skill is loading</command-message>`
   - **Hidden**: Full SKILL.md content (isMeta: true)
4. Tool permissions scoped to `allowed-tools`
5. Skill prompt expands into conversation context

### 2.7 Discovery Priority

Skills loaded in order (later overrides earlier):
1. User settings (`~/.config/claude/skills/`)
2. Project settings (`.claude/skills/`)
3. Plugin-provided skills
4. Built-in skills

### 2.8 Token Budget

- Default skill description budget: **15,000 characters**
- Typical skill prompt: 500-5,000 words

---

## 3. Minimum Interface Contract

### Skill Invocation (from Claude's perspective)

```json
{
  "tool": "Skill",
  "parameters": {
    "command": "skill-name"
  }
}
```

### Available Skills Format (in tool description)

```xml
<available_skills>
<skill>
<name>skill-name</name>
<description>What it does and when to use it</description>
<location>project|user|plugin</location>
</skill>
</available_skills>
```

### Skill Registration (Claude Code)

```bash
# Register marketplace
/plugin marketplace add anthropics/skills

# Install skill
/plugin install skill-name@marketplace-name
```

### Skill Definition Checklist (User's Nixtla Standard)

```yaml
# Compliance Checklist
- [ ] name: lowercase + hyphens, matches folder name
- [ ] description: action-oriented, <1024 chars
- [ ] version: semver format
- [ ] allowed-tools: minimal necessary
- [ ] NO deprecated fields (author in some contexts, priority, audience)
- [ ] mode: true ONLY for mode skills
- [ ] disable-model-invocation: true ONLY for infra/dangerous skills
```

---

## 4. Risks / Failure Modes / Anti-Patterns

### 4.1 Skills NOT Concurrency-Safe

Multiple simultaneous skill invocations cause context conflicts.

**Mitigation:** Only one skill active at a time.

### 4.2 Skills Don't Live in System Prompts

Skills are in the `tools` array as part of Skill meta-tool, not system prompt.

**Implication:** Dynamic loading, but different behavior than expected.

### 4.3 Hardcoded Paths Break Portability

Absolute paths fail when skill is installed elsewhere.

**Mitigation:** Always use `{baseDir}` template variable.

### 4.4 Missing Description = Skill Filtered Out

Skills MUST have `description` OR `when_to_use` or they're invisible.

**Mitigation:** Always include detailed description.

### 4.5 Overly Broad Descriptions

Too-generic descriptions cause wrong skill selection.

**Mitigation:** Include specific trigger phrases and use cases.

### 4.6 Too Many Allowed Tools

Granting excessive permissions increases risk.

**Mitigation:** Principle of least privilege in `allowed-tools`.

---

## 5. What to Copy vs Adapt

### Copy from User's Standards

**From nixtla/.claude/skills/skills-expert/SKILL.md:**
- Comprehensive YAML frontmatter structure
- Directory layout (SKILL.md, scripts/, references/, assets/)
- {baseDir} usage pattern
- Compliance checklist
- Error handling section pattern
- Examples with Input/Output format

**From claude-code-plugins/planned-skills/templates/skill-template.md:**
- Full template structure with placeholders
- All section patterns (Overview, Capabilities, Prerequisites, Instructions, Output, Error Handling, Examples, Resources)

### Adapt for Bob's AgentCard Pattern

| Skills Concept | Bob AgentCard Mapping |
|----------------|----------------------|
| `name` | AgentCard `name` |
| `description` | AgentCard `description` + skill descriptions |
| `allowed-tools` | AgentCard `capabilities` |
| SKILL.md instructions | System prompt + skill input/output schemas |
| {baseDir} | Agent module path |

### New Skills to Create for Bob

1. **bob-adk-audit** - Invoke ADK compliance checking
2. **bob-fix-workflow** - Run fix-plan → fix-impl → QA pipeline
3. **bob-portfolio-audit** - Multi-repo compliance sweep
4. **bob-documentation** - Generate AARs and docs

---

## 6. Integration Notes for Bob

### 6.1 Current State

Bob's Brain uses **AgentCards** with **skill schemas**, which is similar but different:

**AgentCard Skills:**
```json
{
  "skills": [
    {
      "name": "Skill Name",
      "description": "What it does",
      "input_schema": {...},
      "output_schema": {...},
      "id": "agent.skill_name"
    }
  ]
}
```

**SKILL.md Skills:**
```markdown
---
name: skill-name
description: What it does
---
# Instructions...
```

### 6.2 Integration Options

**Option A: Keep Separate**
- AgentCards for A2A protocol
- SKILL.md for Claude Code user experience
- No overlap

**Option B: Generate SKILL.md from AgentCards**
- Auto-generate SKILL.md files from AgentCard definitions
- Users invoke agents via Claude Code skills
- Skills translate to A2A calls

**Option C: Unified Skill Layer**
- Create unified skill definition that generates both
- Single source of truth
- More complex but cleanest

### 6.3 Skill-Based Orchestration Pattern

```markdown
# Bob's Audit Skill
---
name: bob-audit
description: |
  Run ADK compliance audit on a repository.
  Use when user asks to "audit", "check compliance", or "validate ADK rules".
  Trigger with "audit repo", "check R1-R8", "ADK compliance".
allowed-tools: Read,Grep,Glob,Bash
---

## Instructions

1. Invoke iam-senior-adk-devops-lead via A2A
2. Foreman delegates to iam-adk specialist
3. Return structured audit results
4. Format for human consumption

## Output
- Compliance status (PASS/FAIL)
- Violations list with file:line
- Recommendations
```

### 6.4 R1-R8 Compliance

| Rule | Skills Impact |
|------|---------------|
| R1 (ADK-only) | Skills are Claude Code feature, not agent code |
| R3 (Gateway separation) | Skills invoke agents via gateway |
| R6 (Single docs folder) | Skills live in `.claude/skills/`, not 000-docs/ |

---

## 7. Open Questions

1. **Should Bob expose AgentCard skills as SKILL.md files?**
   - Enables Claude Code users to invoke Bob directly
   - Would need skill → A2A translation layer

2. **Where to store Bob's skills?**
   - `.claude/skills/` in bobs-brain repo?
   - Separate skills plugin?

3. **Skill versioning strategy?**
   - Follow AgentCard versions?
   - Independent skill versions?

4. **Integration with Gastown molecules?**
   - Skills for workflow steps?
   - Molecules reference skills?

5. **Skill marketplace for IAM department?**
   - Publish as plugin?
   - Internal-only?

---

## 8. References

### External
- **Anthropic Skills Repo**: https://github.com/anthropics/skills
- **Skills API Quickstart**: https://docs.claude.com/en/api/skills-guide

### User's Standards (Master Reference)
- **skills-expert**: `/home/jeremy/000-projects/nixtla/.claude/skills/skills-expert/SKILL.md`
- **skill-template**: `/home/jeremy/000-projects/claude-code-plugins/planned-skills/templates/skill-template.md`
- **Example skills**: `/home/jeremy/000-projects/claude-code-plugins/planned-skills/generated/`

### Deep Dive
- https://leehanchung.github.io/blogs/2025/10/26/claude-skills-deep-dive/

---

## 9. Key Takeaways for Bob Orchestrator

1. **Skills = Golden Path Packaging** - Encapsulate best practices in reusable units
2. **Description is King** - Pure LLM reasoning for skill selection
3. **{baseDir} for Portability** - Never hardcode paths
4. **User has comprehensive standards** - Use nixtla/claude-code-plugins patterns
5. **AgentCards overlap with Skills** - Need integration strategy
6. **Skills could expose Bob to Claude Code users** - Skill → A2A bridge

**User Decision:** Analysis only for now, defer SKILL.md creation to implementation.

**Next Step:** Research Ralph Wiggum for autonomous loop mechanics.
