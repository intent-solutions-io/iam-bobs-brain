# Ralph Wiggum Research - Deep Dive Analysis

**Document ID:** 246-AA-DEEP-ralph-wiggum-research
**Date:** 2026-01-02
**Author:** Claude Code
**Status:** COMPLETE
**Beads Story:** bobs-brain-kpe.4

---

## 1. What It Is (Executive Summary)

**Ralph Wiggum** is an official Anthropic Claude Code plugin that creates autonomous development loops using a **Stop hook** to intercept exit attempts and re-feed the same prompt until completion. Named after the Simpsons character (embodying persistent iteration despite setbacks), it turns Claude into a "while true" loop for complex, multi-step tasks.

Core philosophy: Claude works on a task, tries to exit, the Stop hook blocks exit and re-feeds the prompt, Claude reads its own previous work in files, then iterates and improves. This continues until a **completion promise** is detected or max iterations reached.

---

## 2. Key Primitives to Implement/Integrate

### 2.1 Stop Hook Mechanism

**Location:** `hooks/stop-hook.sh`

**Flow:**
```
1. User runs: /ralph-loop "task" --completion-promise "DONE"
2. Claude works on task (iteration 1)
3. Claude tries to exit
4. Stop hook blocks exit (exit code 2)
5. Stop hook checks for "DONE" in output
6. Not found → re-feed original prompt
7. Claude sees modified files + git history
8. Claude reads own previous work
9. Repeat until "DONE" or max iterations
```

**Key Properties:**
- Loop happens INSIDE current session (no external bash loops)
- Prompt never changes between iterations
- State persists in files and git history
- Claude autonomously improves by reading its own past work

### 2.2 Commands

| Command | Purpose | Parameters |
|---------|---------|------------|
| `/ralph-loop` | Start iterative loop | `"<prompt>" --max-iterations <n> --completion-promise "<text>"` |
| `/cancel-ralph` | Cancel active loop | None |

**Example:**
```bash
/ralph-loop "Build a REST API for todos. Requirements: CRUD operations, input validation, tests. Output <promise>COMPLETE</promise> when done." --completion-promise "COMPLETE" --max-iterations 50
```

### 2.3 Completion Promise Pattern

**Single Exact Match:**
- `--completion-promise "COMPLETE"` triggers exit when output contains exactly "COMPLETE"
- Only one completion condition per loop
- Cannot differentiate outcomes (SUCCESS vs BLOCKED)
- Rely on `--max-iterations` as primary safety mechanism

**Best Practices for Prompts:**
```markdown
Build a REST API for todos.

When complete:
- All CRUD endpoints working
- Input validation in place
- Tests passing (coverage > 80%)
- README with API docs
- Output: <promise>COMPLETE</promise>
```

### 2.4 Self-Referential Feedback Loop

| Aspect | How It Works |
|--------|-------------|
| **Persistent Prompt** | Same prompt never changes |
| **Persistent State** | Previous work remains in files |
| **Autonomous Improvement** | Claude reads its own past work |
| **Context Accumulation** | Each iteration sees all prior modifications |

### 2.5 Plugin Structure

```
plugins/ralph-wiggum/
├── .claude-plugin/          # Plugin configuration
├── commands/                # /ralph-loop, /cancel-ralph
├── hooks/
│   └── stop-hook.sh         # Exit interception logic
├── scripts/                 # Utility scripts
└── README.md
```

### 2.6 TDD Loop Pattern

The most effective use case - Test-Driven Development:

```markdown
Implement feature X following TDD:
1. Write failing tests
2. Implement feature
3. Run tests
4. If any fail, debug and fix
5. Refactor if needed
6. Repeat until all green
7. Output: <promise>COMPLETE</promise>
```

This works because:
- Tests provide automatic verification
- Failures are deterministic feedback
- Claude can read test output to understand what's wrong
- Progress is measurable and observable

---

## 3. Minimum Interface Contract

### Stop Hook Interface

```bash
# Stop hook receives:
# - Exit code from Claude
# - Full session output
# - Original prompt
# - Iteration count

# Stop hook returns:
# - Exit code 0: Allow exit (completion detected)
# - Exit code 2: Block exit, re-feed prompt
```

### Command Interface

```bash
# Start loop
/ralph-loop "<prompt>" --max-iterations <n> --completion-promise "<text>"

# Cancel loop
/cancel-ralph
```

### Completion Detection

```bash
# Exact string match in output
--completion-promise "COMPLETE"

# Detects:
✅ "Task COMPLETE, all tests passing"
✅ "<promise>COMPLETE</promise>"
❌ "Complete" (case sensitive)
❌ "COMPLETED" (not exact match)
```

---

## 4. Risks / Failure Modes / Anti-Patterns

### 4.1 Cost Explosion

Autonomous loops consume tokens rapidly.

**Example:** 50-iteration loop on medium codebase = $50-100+ in API costs

**Mitigation:**
- Always set `--max-iterations`
- Start with low iterations (10-20) and increase
- Include escape hatch in prompt

### 4.2 Infinite Loops

Loop never reaches completion promise.

**Causes:**
- Vague prompts without clear criteria
- Impossible tasks
- External dependency failures
- Prompt too complex for single-session Claude

**Mitigation:**
```markdown
After 15 iterations, if not complete:
- Document what's blocking progress
- List what was attempted
- Suggest alternative approaches
- Output: <promise>BLOCKED</promise>
```

### 4.3 Single Outcome Limitation

Cannot differentiate success vs failure outcomes.

**Problem:**
- `--completion-promise` only checks one string
- Can't use "SUCCESS" for good outcome and "BLOCKED" for failure

**Mitigation:**
- Use `--max-iterations` as safety net
- Design prompts with single clear success path
- Handle ambiguous outcomes after loop exits

### 4.4 Prompt Quality Dependency

Success depends heavily on operator skill.

**Bad Prompt (Vague):**
```
Build a todo API and make it good.
```

**Good Prompt (Clear Criteria):**
```
Build a REST API for todos.

Requirements:
- CRUD endpoints (/todos GET, POST, PUT, DELETE)
- Input validation (title required, max 200 chars)
- Tests with >80% coverage
- README with curl examples

Output <promise>COMPLETE</promise> when ALL requirements met.
```

### 4.5 No Checkpoint Recovery

If session crashes mid-loop, must restart from iteration 1.

**Mitigation:**
- Work in git-tracked directories
- Use `bd` for task tracking
- Design prompts for incremental progress

---

## 5. What to Copy vs Adapt

### Copy for Bob's Autonomous Loops

| Ralph Concept | Bob Adaptation |
|---------------|----------------|
| Stop hook | A2A callback that checks completion |
| Completion promise | Schema field in specialist output |
| Max iterations | Budget limit in foreman |
| Prompt re-feed | Re-invoke specialist with same input |

### Adapt for Vertex Agent Engine

| Ralph Feature | Agent Engine Adaptation |
|--------------|------------------------|
| Local file persistence | Memory Bank for state |
| Git history | Session memory + audit trail |
| Stop hook (shell) | after_agent_callback (Python) |
| /ralph-loop command | Foreman workflow orchestration |

### New Patterns for Bob

**1. Portfolio Audit Loop:**
```python
# Foreman starts audit loop
audit_result = {
    "status": "in_progress",
    "repos_checked": 0,
    "total_repos": 15,
    "completion_promise": "PORTFOLIO_COMPLETE"
}

# Loop until all repos audited
while audit_result["repos_checked"] < audit_result["total_repos"]:
    # Invoke specialist
    # Update progress
    # Check for completion
```

**2. Fix-Until-Pass Loop:**
```python
# TDD-style loop for fix implementation
fix_result = {
    "status": "in_progress",
    "tests_passing": False,
    "iteration": 0,
    "max_iterations": 20
}

# Loop until tests pass
while not fix_result["tests_passing"] and fix_result["iteration"] < fix_result["max_iterations"]:
    # iam-fix-impl attempts fix
    # iam-qa runs tests
    # Check test results
    # Feed failure back to fix-impl
```

**3. Self-Improving Prompt Pattern:**
```python
# Agent reads its own previous output
previous_attempt = memory_bank.read("last_fix_attempt")
test_failures = memory_bank.read("test_failures")

# Claude reasons about what went wrong
# Attempts improved fix
# Writes new attempt to memory
```

---

## 6. Integration Notes for Bob

### 6.1 Stop Hook as A2A Callback

**Ralph's shell-based Stop hook:**
```bash
# hooks/stop-hook.sh
# Intercept exit, check for completion, re-feed prompt
```

**Bob's Python-based equivalent:**
```python
def after_agent_callback(callback_context):
    """Ralph-style loop check after specialist execution."""
    output = callback_context.output

    # Check for completion promise
    if "COMPLETE" in str(output):
        return output  # Allow completion

    # Check iteration limit
    if callback_context.iteration >= callback_context.max_iterations:
        return {"status": "MAX_ITERATIONS", "output": output}

    # Re-invoke with same input (loop continues)
    callback_context.iteration += 1
    return InvokeAgentRequest(
        agent_id=callback_context.agent_id,
        input=callback_context.original_input
    )
```

### 6.2 Completion Promise in Specialist Contracts

**AgentCard skill output schema:**
```json
{
  "output_schema": {
    "type": "object",
    "properties": {
      "status": {
        "type": "string",
        "enum": ["COMPLETE", "IN_PROGRESS", "BLOCKED"]
      },
      "completion_promise": {
        "type": "string",
        "description": "Phrase indicating task is done"
      },
      "result": { "type": "object" }
    }
  }
}
```

**Foreman checks completion:**
```python
if specialist_output["status"] == "COMPLETE":
    return specialist_output["result"]
elif specialist_output["status"] == "BLOCKED":
    escalate_to_human()
else:
    # Continue loop
    increment_iteration()
```

### 6.3 R1-R8 Compliance

| Rule | Ralph Impact |
|------|--------------|
| R1 (ADK-only) | Ralph is Claude Code plugin, not agent code |
| R2 (Agent Engine) | Adapt Stop hook to `after_agent_callback` |
| R3 (Gateway) | Loops run inside agents, not in gateway |
| R5 (Memory) | Use Memory Bank for state persistence |
| R8 (Drift) | Track iteration count in session |

### 6.4 Foreman Loop Orchestration

**Current Foreman patterns:**
- Single specialist
- Sequential specialists
- Parallel specialists

**New pattern - Iterative loop:**
- Call specialist
- Check completion
- If not complete, re-call with same input + feedback
- Track iterations
- Exit on completion or max iterations

```python
class ForemanLoopPattern:
    """Ralph-style loop pattern for foreman."""

    def execute_loop(
        self,
        specialist: str,
        input: dict,
        completion_promise: str,
        max_iterations: int = 20
    ):
        iteration = 0
        while iteration < max_iterations:
            result = self.invoke_specialist(specialist, input)

            if completion_promise in str(result):
                return {"status": "COMPLETE", "result": result}

            # Augment input with feedback
            input["previous_attempt"] = result
            input["iteration"] = iteration + 1

            iteration += 1

        return {"status": "MAX_ITERATIONS", "result": result}
```

---

## 7. Open Questions

1. **How to handle Vertex Agent Engine session limits?**
   - Long-running loops may hit context limits
   - Need strategy for session continuation

2. **Memory Bank for loop state?**
   - Use Memory Bank instead of file-based state?
   - Persist iteration count, previous attempts

3. **Multi-specialist loops?**
   - Ralph loops single Claude instance
   - Bob may need to loop across specialists (fix → test → fix)

4. **Cost tracking for budget limits?**
   - Track token usage per iteration
   - Implement budget-based termination

5. **Human-in-the-loop integration?**
   - Escalate to Slack when loop gets stuck
   - Request human guidance, resume loop

---

## 8. References

### External
- **Official Plugin**: https://github.com/anthropics/claude-plugins-official/tree/main/plugins/ralph-wiggum
- **Original Technique**: https://ghuntley.com/ralph/
- **Ralph Orchestrator**: https://github.com/mikeyobrien/ralph-orchestrator
- **Deep Dive Blog**: https://paddo.dev/blog/ralph-wiggum-autonomous-loops/

### Real-World Results
- 6 repositories generated overnight (Y Combinator hackathon)
- $50k contract completed for $297 in API costs
- Complete programming language ("Cursed") built over 3 months

---

## 9. Key Takeaways for Bob Orchestrator

1. **Stop hook pattern is essential** - Intercept completion, check promise, loop if needed
2. **Completion promise enables clean exit** - Define clear success criteria upfront
3. **Self-referential loops work** - Claude can read own work and improve
4. **Max iterations is safety net** - Always set limits
5. **TDD is ideal pattern** - Tests provide automatic verification
6. **Adapt to after_agent_callback** - Port shell hook to Python callback
7. **Memory Bank replaces file state** - Persist loop state in Vertex memory

**User Decision:** Analysis only for now, defer implementation to integration phase.

**Next Step:** Research AP2 (Agent Payments Protocol) for budget mandate patterns.
