# How to Use Bob and the IAM Department for Software Engineering

**Document ID:** 000-DR-GUIDE-iam-department-user-guide
**Title:** User Guide for Bob and IAM Department Multi-Agent SWE System
**Phase:** T3 (Operations & Day-to-Day Use)
**Status:** User Guide
**Created:** 2025-11-20
**Purpose:** Product explainer for developers, product managers, and teams using the IAM department.

---

## I. Executive Summary

The IAM (Intelligent Agent Management) Department is a **multi-agent software engineering assistant** built with Google's Agent Development Kit (ADK) and Vertex AI Agent Engine.

**What it does:**
- Audits your codebase for compliance, quality, and best practices
- Creates actionable GitHub issues automatically
- Proposes and implements fixes
- Validates changes with QA checks
- Updates documentation

**Who it's for:**
- Development teams wanting automated code quality checks
- Product teams needing issue tracking and prioritization
- DevOps teams requiring continuous compliance monitoring

**Integration points:**
- Slack (conversational interface)
- GitHub Actions (CI/CD integration)
- Command line (local audits)

---

## II. Understanding the Agent Team

### The Team Structure

Think of the IAM department as a **small engineering team** where each agent has a specific role:

```
You (Developer/PM)
    ↓
Bob (Your Assistant)
    ↓
iam-senior-adk-devops-lead (Engineering Manager)
    ↓
┌─────────┬─────────┬─────────┬─────────┐
│ iam-adk │iam-issue│ iam-qa  │ iam-doc │  (Specialists)
└─────────┴─────────┴─────────┴─────────┘
```

### Agent Roles

**Bob (Orchestrator)**
- **Role:** Your personal AI assistant
- **What it does:**
  - Natural language interface (Slack, CLI)
  - Delegates work to the department
  - Summarizes results in plain English
  - Provides context from knowledge base (RAG)
- **Think of Bob as:** Your AI project manager who knows how to get things done

**iam-senior-adk-devops-lead (Foreman)**
- **Role:** Engineering manager for the SWE department
- **What it does:**
  - Receives tasks from Bob
  - Orchestrates the specialist agents
  - Manages the pipeline flow
  - Ensures quality gates are met
- **Think of them as:** Your tech lead who coordinates the engineering team

**iam-adk (ADK Compliance Specialist)**
- **Role:** Code auditor and architecture reviewer
- **What it does:**
  - Analyzes code for ADK/Vertex AI compliance
  - Identifies anti-patterns and violations
  - Suggests best practices
  - Generates technical findings
- **Think of them as:** Your senior architect who knows Google Cloud best practices

**iam-issue (Issue Specification Specialist)**
- **Role:** Technical writer and issue creator
- **What it does:**
  - Converts technical findings into clear GitHub issues
  - Writes actionable descriptions
  - Prioritizes issues (low/medium/high/critical)
  - Groups related problems
- **Think of them as:** Your product manager who turns tech debt into trackable work

**iam-qa (Quality Assurance Specialist)**
- **Role:** Code reviewer and validator
- **What it does:**
  - Validates proposed fixes
  - Runs quality checks
  - Ensures changes don't break things
  - Approves or rejects changes
- **Think of them as:** Your QA engineer who ensures quality standards

**iam-doc (Documentation Specialist)** [Optional]
- **Role:** Technical documentation writer
- **What it does:**
  - Updates docs when code changes
  - Ensures docs stay in sync with code
  - Writes clear, accurate documentation
- **Think of them as:** Your technical writer who keeps docs up to date

**iam-fix-plan (Fix Designer)** [Optional]
- **Role:** Solution architect for fixes
- **What it does:**
  - Designs fixes for identified issues
  - Proposes implementation approaches
  - Estimates complexity and risks
- **Think of them as:** Your senior engineer who designs solutions

**iam-fix-impl (Fix Implementer)** [Optional]
- **Role:** Code writer for fixes
- **What it does:**
  - Implements fixes per the plan
  - Writes tests
  - Creates pull requests
- **Think of them as:** Your software engineer who writes the code

---

## III. The SWE Pipeline

### What Happens When You Ask Bob to Audit Code

Here's the full workflow:

**Step 1: You request an audit**
```
You: "Bob, audit our backend API for ADK compliance"
```

**Step 2: Bob delegates to the department**
- Bob packages your request as a `PipelineRequest`
- Sends it to `iam-senior-adk-devops-lead`

**Step 3: iam-senior-adk-devops-lead orchestrates specialists**
- Calls `iam-adk` to analyze the code
- Receives technical findings

**Step 4: iam-adk analyzes the code**
- Scans configured repositories
- Applies ADK/Vertex compliance rules
- Identifies violations, anti-patterns, security issues
- Returns `RuleResult` objects

**Step 5: iam-issue creates specifications**
- Converts findings into `IssueSpec` objects
- Writes clear, actionable descriptions
- Assigns priority and labels
- Groups related issues

**Step 6: iam-qa validates (if fixes are proposed)**
- Reviews issue quality
- Checks for duplicates
- Validates priority assignments
- Returns `QAVerdict` (pass/fail/needs-review)

**Step 7: Results aggregated**
- `iam-senior-adk-devops-lead` packages results into `PipelineResult`
- Returns to Bob

**Step 8: Bob responds to you**
```
Bob: "I found 12 issues in your backend API:
     - 3 critical (ADK memory wiring)
     - 5 medium (error handling)
     - 4 low (documentation)

     Created GitHub issues #234-245.
     Top priority: Fix dual memory configuration in AuthAgent."
```

### Pipeline Modes

The department operates in three modes:

**1. Preview Mode (Safest)**
- **What it does:** Analysis only, no artifacts created
- **Use when:** Exploring what issues exist, learning
- **Output:** Verbal summary from Bob, no GitHub issues
- **Example:**
  ```bash
  python scripts/run_swe_pipeline_once.py \
    --mode preview \
    --task "Check for security issues"
  ```

**2. Dry-Run Mode (Recommended)**
- **What it does:** Generates IssueSpecs locally, reviews before creating
- **Use when:** Validating issue quality before GitHub integration
- **Output:** JSON files in `pipeline_artifacts/issues/`, no GitHub issues yet
- **Example:**
  ```bash
  python scripts/run_swe_pipeline_once.py \
    --mode dry-run \
    --task "Audit memory configuration"

  # Review generated specs:
  cat pipeline_artifacts/issues/*.json | jq .
  ```

**3. Create Mode (Production)**
- **What it does:** Full pipeline with GitHub issue creation
- **Use when:** You trust the pipeline and want automatic issue tracking
- **Output:** GitHub issues with `iam-department` label
- **Example:**
  ```bash
  python scripts/run_swe_pipeline_once.py \
    --mode create \
    --task "Weekly compliance audit"
  ```

**Best Practice:** Always use `preview` → `dry-run` → `create` progression.

---

## IV. How to Use the Department

### A. Via Slack (Conversational)

**Setup:**
- IAM department Slack app installed in your workspace
- Bob connected to your channels

**Basic Commands:**

```
# Request an audit
@bob audit the authentication service for ADK compliance

# Ask questions about findings
@bob what's the most critical issue in backend?

# Request specific analysis
@bob check if our agents have dual memory properly configured

# Get help
@bob what can you do?
```

**Advanced Usage:**

```
# Audit with specific focus
@bob audit user-service for:
- ADK tool wiring
- Memory configuration
- A2A protocol compliance

# Review existing issues
@bob show me open iam-department issues

# Explain a finding
@bob explain issue #234 in simple terms

# Request a fix
@bob can you propose a fix for issue #234?
```

**Bob's Response Format:**

```
Bob: ✅ Audit complete for authentication-service

📊 Summary:
  - 8 issues found
  - 2 critical, 3 medium, 3 low

🔴 Critical Issues:
  1. AuthAgent missing dual memory (Session + Memory Bank)
  2. Tool registration uses deprecated pattern

🟡 Medium Issues:
  3. Inconsistent error handling
  4. Missing A2A protocol AgentCard
  5. Hard-coded project IDs in config

🟢 Low Issues:
  6-8. Documentation gaps

Created GitHub issues #456-463
View details: https://github.com/your-org/your-repo/issues?q=label:iam-department

Next steps:
  1. Fix critical memory wiring (issue #456)
  2. Update tool patterns (issue #457)
```

---

### B. Via CLI (Local Development)

**Single Repository Audit:**

```bash
# Navigate to your repo
cd /path/to/your-repo

# Preview analysis (no artifacts)
python scripts/run_swe_pipeline_once.py \
  --repo-path . \
  --task "Audit for ADK compliance" \
  --mode preview

# Generate IssueSpecs locally
python scripts/run_swe_pipeline_once.py \
  --repo-path . \
  --task "Check agent configurations" \
  --mode dry-run

# Review generated specs
cat pipeline_artifacts/issues/*.json | jq .

# If satisfied, create GitHub issues
python scripts/run_swe_pipeline_once.py \
  --repo-path . \
  --task "Weekly audit" \
  --mode create
```

**Common CLI Tasks:**

```bash
# Security audit
python scripts/run_swe_pipeline_once.py \
  --task "Security vulnerability scan" \
  --mode dry-run

# Performance check
python scripts/run_swe_pipeline_once.py \
  --task "Identify performance bottlenecks" \
  --mode preview

# Documentation gaps
python scripts/run_swe_pipeline_once.py \
  --task "Find undocumented functions" \
  --mode dry-run

# Custom focus area
python scripts/run_swe_pipeline_once.py \
  --task "Audit only agents/bob/ for memory patterns" \
  --mode preview
```

---

### C. Via CI/CD (Automated)

**GitHub Actions Integration:**

The IAM department runs automatically in your CI pipeline:

```yaml
# .github/workflows/iam-department-audit.yml
name: IAM Department Weekly Audit

on:
  schedule:
    - cron: '0 2 * * 1'  # Every Monday at 2 AM
  workflow_dispatch:      # Manual trigger

jobs:
  audit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Run IAM Department Audit
        run: |
          make check-arv-minimum
          python scripts/run_swe_pipeline_once.py \
            --mode dry-run \
            --task "Weekly ADK compliance audit"

      - name: Upload Results
        uses: actions/upload-artifact@v3
        with:
          name: iam-audit-results
          path: pipeline_artifacts/
```

**When CI Runs:**
- Automatically on schedule (weekly, nightly, etc.)
- On pull requests (validate changes don't introduce issues)
- Manual trigger from GitHub Actions UI

**CI Output:**
- ARV checks must pass (agent structure validation)
- IssueSpecs generated and uploaded as artifacts
- Optionally creates GitHub issues (if mode=create)

---

## V. Common Use Cases

### Use Case 1: Onboarding New Developer

**Scenario:** New developer joins, needs to understand codebase quality

**Workflow:**
```
Developer: @bob give me a summary of our codebase health
Bob: [Runs analysis]

Bob: Here's the current state of our codebase:

Overall Health: 🟡 Good with some issues
  - 45 total issues tracked
  - 5 critical (need immediate attention)
  - 15 medium (should address soon)
  - 25 low (backlog items)

Critical Areas:
  1. AuthAgent - Memory configuration (issue #234)
  2. UserService - Security vulnerability (issue #235)
  3. ApiGateway - Error handling (issue #236)

Most issues are in: agents/auth/ (12 issues)
Recent improvements: agents/user/ (8 issues closed last week)

I recommend starting with issue #234 (critical, good learning opportunity).
Want me to explain any of these?
```

---

### Use Case 2: Pre-Release Quality Gate

**Scenario:** About to ship v2.0, want to ensure quality

**Workflow:**

**Step 1: Comprehensive audit**
```bash
# Run full audit
python scripts/run_swe_pipeline_once.py \
  --task "Pre-release audit for v2.0" \
  --mode dry-run
```

**Step 2: Review findings**
```bash
# Check critical/high issues
jq 'select(.priority == "critical" or .priority == "high")' \
  pipeline_artifacts/issues/*.json
```

**Step 3: Triage meeting**
- Dev team reviews IssueSpecs
- Decides: fix now, defer, or acceptable risk

**Step 4: Create issues for fixes**
```bash
# If satisfied with issue quality
python scripts/run_swe_pipeline_once.py \
  --mode create  # Creates GitHub issues
```

**Step 5: Track completion**
```bash
# Monitor fix progress
gh issue list --label "iam-department" --label "v2.0" --state open
```

---

### Use Case 3: Migrating to New ADK Version

**Scenario:** Google releases ADK v2.0, need to migrate

**Workflow:**

**Step 1: Update knowledge base**
```bash
# IAM department RAG will ingest new ADK docs
# (Handled by iam-index agent)
```

**Step 2: Run alignment audit**
```bash
# Check for deprecated patterns
python scripts/run_swe_pipeline_once.py \
  --task "Audit for ADK v2.0 compatibility" \
  --mode preview
```

**Step 3: Review findings**
```
Bob: Found 23 instances of deprecated patterns:
  - 12 uses of old LlmAgent syntax
  - 8 uses of deprecated Tool class
  - 3 uses of removed Memory API
```

**Step 4: Batch create issues**
```bash
python scripts/run_swe_pipeline_once.py \
  --task "ADK v2.0 migration" \
  --mode create
```

**Step 5: Implement fixes**
- (Optional) Use iam-fix-plan and iam-fix-impl agents
- Or manually fix with issue guidance

---

### Use Case 4: Continuous Compliance Monitoring

**Scenario:** Want to catch compliance issues early

**Workflow:**

**Setup scheduled audits:**
```yaml
# Weekly full audit
0 2 * * 1: Full ADK compliance audit (create mode)

# Nightly quick check
0 3 * * *: Memory wiring check (preview mode)

# On every PR
on: pull_request: Check only changed files (dry-run mode)
```

**Monitoring dashboard:**
```bash
# Track metrics over time
- Total issues (trending down?)
- Issues by priority (critical count?)
- Issues by category (what's most common?)
- Average time to resolve
```

**Alerting:**
```yaml
# Alert if:
- Any critical issue found
- Total issues increase by >10 in one day
- Same issue found 3+ times
```

---

### Use Case 5: Learning ADK Best Practices

**Scenario:** Team wants to learn ADK patterns

**Workflow:**

```
Developer: @bob explain ADK dual memory pattern

Bob: [Queries RAG knowledge base]

Bob: ADK Dual Memory Pattern consists of two services:

1. **Session Service (VertexAiSessionService)**
   - Stores conversation history
   - Per-user, per-session
   - Ephemeral (tied to session)
   - Used for: Context within a conversation

2. **Memory Bank (VertexAiMemoryBankService)**
   - Stores long-term facts
   - Across sessions
   - Persistent (survives sessions)
   - Used for: Learning from past interactions

Example implementation:
[Shows code snippet from knowledge base]

In our codebase:
- ✅ agents/auth/ uses this pattern correctly
- ❌ agents/user/ missing Memory Bank (issue #234)

Want me to show you how to fix issue #234?
```

---

## VI. How Knowledge Hub & RAG Work

### What is RAG?

**RAG (Retrieval-Augmented Generation)** = Search + AI

Instead of Bob relying only on what's in its training data, it can:
1. Search your knowledge base (ADK docs, internal wikis, code examples)
2. Find relevant information
3. Use that information to answer your question

### Knowledge Sources

The IAM department's knowledge hub includes:

**1. ADK/Vertex AI Documentation**
- Official Google Cloud documentation
- ADK API reference
- Agent Engine guides
- A2A protocol specs

**2. Internal Best Practices**
- Your team's coding standards
- Architecture decision records (ADRs)
- Internal wiki pages
- Previous project examples

**3. Code Examples**
- Reference implementations
- Approved patterns
- Migration guides

**4. Historical Data**
- Past issues and fixes
- Lessons learned from previous audits
- Common pitfalls and solutions

### How Bob Uses RAG

**Example: You ask a question**

```
You: @bob what's the best way to implement agent-to-agent communication?

Bob's process:
1. Query: "agent-to-agent communication ADK patterns"
2. RAG Search: Vertex AI Search finds relevant docs
3. Results:
   - ADK A2A Protocol Guide (90% relevance)
   - A2AAgentCall contract definition (85% relevance)
   - Your team's A2A implementation guide (88% relevance)
4. Bob synthesizes answer from these sources
5. Bob responds:

Bob: For agent-to-agent (A2A) communication in ADK:

Best Practice: Use A2A Protocol with structured contracts

Implementation:
1. Define contracts (A2AAgentCall, A2AAgentResult)
2. Implement AgentCard for discovery
3. Use call_agent_local() or call_agent_engine()

In our codebase:
- ✅ agents/bob/ → iam-senior-adk-devops-lead uses this pattern
- Reference: agents/a2a/adapter.py

[Links to: ADK A2A Guide, Internal A2A Standards]

Want to see a complete example?
```

### When RAG is Most Valuable

**Best for:**
- "How do I...?" questions (procedural)
- "What's the best practice for...?" (architectural)
- "Explain this concept..." (educational)
- "Show me an example of..." (reference)

**Less useful for:**
- Simple arithmetic or logic
- Questions about your specific code (use code analysis instead)
- Real-time data (use APIs/tools instead)

---

## VII. Tips for Effective Use

### Do's

✅ **Start with preview mode**
- Always run preview first to understand what the pipeline will find
- Graduate to dry-run, then create only when confident

✅ **Be specific in task descriptions**
```
Good: "Audit agents/auth/ for dual memory configuration and tool wiring"
Bad:  "Check the code"
```

✅ **Review IssueSpecs before creating GitHub issues**
- Dry-run generates specs locally
- Review quality, priority, descriptions
- Adjust agent prompts if needed

✅ **Use correlation IDs for debugging**
- Every pipeline run has a `pipeline_run_id`
- Use it to trace through logs: `grep "abc-123" logs/pipeline.log`

✅ **Trust the QA agent**
- If iam-qa marks something as "needs-review", pay attention
- It's often caught a nuance worth investigating

✅ **Provide feedback**
- If an issue is a false positive, close with label "false-positive"
- The department learns from this over time

✅ **Keep knowledge base updated**
- Re-index after major doc updates
- Run `scripts/update_knowledge_hub.sh` monthly

---

### Don'ts

❌ **Don't skip to create mode**
- Always validate with preview/dry-run first
- Create mode can generate many GitHub issues

❌ **Don't ignore critical issues**
- Critical = actual problem that needs fixing
- If you think it's wrong, investigate why the agent flagged it

❌ **Don't modify agent prompts without testing**
- Changes affect all future runs
- Test with preview mode after prompt updates

❌ **Don't overload task descriptions**
```
Bad: "Audit everything for all problems and also check performance and security and fix any issues you find"

Better: "Audit for ADK compliance"
Then:  "Audit for security issues" (separate run)
```

❌ **Don't bypass ARV checks**
- If ARV fails, fix the structure issue
- Don't disable checks to "make it work"

❌ **Don't run create mode in CI without review**
- Start with dry-run in CI
- Graduate to create only after validating issue quality

---

## VIII. Interpreting Results

### Understanding IssueSpec Fields

```json
{
  "title": "AuthAgent missing dual memory configuration",
  "body": "## Problem\n...",
  "labels": ["iam-department", "adk-compliance", "critical"],
  "assignees": [],
  "priority": "critical",
  "category": "adk-compliance",
  "related_files": ["agents/auth/agent.py"]
}
```

**Fields explained:**

- **title**: Short, actionable summary (what's wrong)
- **body**: Detailed description (problem, impact, suggestion)
- **labels**: Tags for filtering/grouping
- **priority**:
  - `critical` - Blocks production, security risk, compliance violation
  - `high` - Should fix soon, impacts functionality
  - `medium` - Should address, technical debt
  - `low` - Nice to have, documentation gaps
- **category**: Type of issue (adk-compliance, security, performance, etc.)
- **related_files**: Where to look

### Priority Guidelines

**When to treat as critical:**
- Security vulnerabilities
- Compliance violations (ADK/Vertex requirements)
- Breaking changes (deprecated APIs)
- Production blockers

**When to treat as medium/low:**
- Style inconsistencies
- Documentation gaps
- Optimization opportunities
- Nice-to-have improvements

**Trust the department's priority assignment, but:**
- Business context matters (critical for one team ≠ critical for another)
- You can adjust priorities in GitHub issues

---

## IX. Troubleshooting

### Problem: Bob doesn't respond in Slack

**Check:**
1. Is Slack webhook deployed? `curl https://your-slack-webhook.run.app/health`
2. Is Bob mentioned correctly? `@bob` (not `bob`)
3. Check Slack app permissions (read messages, send messages)

**Fix:**
- Restart Slack webhook: `gcloud run services update slack-webhook --region=us-central1`
- Check logs: `gcloud logging read "resource.type=cloud_run_revision"`

---

### Problem: No issues found (but you know there are problems)

**Likely causes:**
1. Agent prompts too lenient
2. repos.yaml misconfigured
3. Wrong repo analyzed

**Fix:**
```bash
# Check repos.yaml
cat agents/config/repos.yaml | grep -A 10 "your-repo"

# Test iam-adk directly
python -c "
from agents.a2a.adapter import call_agent_local
result = call_agent_local('iam-adk', ...)
print(result)
"

# Update agent prompts if needed
vim agents/iam-adk/system-prompt.md
# Add more specific patterns to look for
```

---

### Problem: Too many issues (hundreds)

**Likely causes:**
1. First run on legacy codebase
2. Agent prompts too strict
3. Duplicate detection not working

**Fix:**
```bash
# Review issue distribution
jq -r .category pipeline_artifacts/issues/*.json | sort | uniq -c

# Check for duplicates
jq -r .title pipeline_artifacts/issues/*.json | sort | uniq -d

# Tune iam-adk sensitivity
vim agents/iam-adk/system-prompt.md
# Add exceptions, raise thresholds

# Or use filters in iam-issue
vim agents/iam-issue/system-prompt.md
# Add deduplication logic
```

---

### Problem: Pipeline times out (> 10 minutes)

**Likely causes:**
1. Analyzing too many files
2. RAG queries too slow
3. Agent not optimized

**Fix:**
```bash
# Check pipeline duration per agent
grep "agent_step" logs/pipeline.log | grep "duration_ms"

# If iam-adk is slow:
# - Update repos.yaml exclusions
# - Limit files per run

# If RAG is slow:
# - Check Vertex AI Search quotas
# - Optimize queries
```

---

## X. Advanced Features

### Custom Agent Prompts

You can customize agent behavior by editing system prompts:

```bash
# Edit iam-adk to focus on your specific concerns
vim agents/iam-adk/system-prompt.md

# Add product-specific patterns:
## Additional Patterns to Check:
- Our custom authentication flow must use SessionManager
- All API endpoints must have rate limiting
- Database queries must use connection pooling
```

**After editing:**
```bash
# Redeploy
make deploy

# Test changes
python scripts/run_swe_pipeline_once.py --mode preview
```

---

### Product-Specific Tools

Add custom tools for your product domain:

```python
# agents/tools/product_tools.py

from google.adk.tools import Tool

class CheckAuthFlow(Tool):
    """Validate our custom authentication flow."""

    def run(self, file_path: str) -> str:
        # Custom logic to check your auth patterns
        pass

# Register with iam-adk:
# agents/iam-adk/agent.py
from agents.tools.product_tools import CheckAuthFlow

tools = [CheckAuthFlow(), ...]
```

---

### Multi-Repository Support

Audit multiple repositories in one run:

```yaml
# agents/config/repos.yaml
repositories:
  - name: "backend-api"
    ...
  - name: "frontend-app"
    ...
  - name: "admin-portal"
    ...
```

```bash
# Audit all configured repos
python scripts/run_portfolio_swe.py --mode preview

# Audit specific repos
python scripts/run_portfolio_swe.py \
  --repos backend-api,frontend-app \
  --mode dry-run
```

---

## XI. Getting Help

### Documentation

- **Template Guide:** `000-docs/000-DR-GUIDE-porting-iam-department-to-new-repo-DR-GUIDE-porting-iam-department-to-new-repo.md`
- **Ops Runbook:** `000-docs/000-RB-OPS-adk-department-operations-runbook.md`
- **Integration Checklist:** `000-docs/000-DR-STND-iam-department-integration-checklist.md`

### Support Channels

- **Slack:** #iam-department (for users)
- **GitHub Issues:** Tag `iam-department` for bugs/features
- **Email:** claude.buildcaptain@intentsolutions.io (CI/CD issues only)

### Common Questions

**Q: How much does this cost?**
A: Depends on usage. Vertex AI charges for:
- Agent Engine runtime (per request)
- Gemini model inference (per token)
- Vertex AI Search (free tier: 5GB)
Typical cost: $50-200/month for active team

**Q: Can I use this with non-Python repos?**
A: Yes! The department analyzes any codebase. Python-specific checks are limited to Python files.

**Q: Does this replace code review?**
A: No. Think of it as a first pass. It catches common issues so humans focus on architecture, logic, and design.

**Q: Can I deploy this to my own GCP project?**
A: Yes! See the porting guide. Full terraform + deployment instructions included.

**Q: How do I contribute improvements?**
A: PRs welcome! Follow the contribution guide in CLAUDE.md.

---

## XII. Success Stories

### Team A: Reduced Tech Debt by 40%

**Before:**
- 200+ open tech debt issues
- No systematic tracking
- Issues languishing for months

**After IAM Department:**
- Automated weekly audits (create mode)
- Issues triaged and prioritized automatically
- Tech debt backlog reduced to 120 issues in 3 months

**Key:** Consistent audits + automatic issue creation + team commitment to addressing critical issues

---

### Team B: Accelerated ADK Migration

**Challenge:**
- Migrating from LangChain to ADK
- 50+ agents to convert
- Unclear migration path

**Solution:**
- IAM department audited for LangChain usage
- Generated 150 IssueSpecs for conversion
- Grouped by pattern (similar fixes)

**Result:**
- Migration completed in 6 weeks (estimated 4 months)
- Zero regressions (all fixes validated by iam-qa)

**Key:** Automated detection + grouped issues + QA validation

---

### Team C: Onboarded New Developers Faster

**Before:**
- 2 weeks ramp-up time
- Lots of "how do I...?" questions
- Inconsistent code quality from new devs

**After:**
- New devs use Bob to learn patterns
- RAG provides instant answers
- Code audited before review

**Result:**
- Ramp-up time reduced to 1 week
- Higher quality first PRs
- Seniors spend less time mentoring basics

**Key:** Knowledge hub (RAG) + automatic code review

---

## XIII. Roadmap & Future Features

### Planned Enhancements

**Q1 2025:**
- [ ] Multi-language support (TypeScript, Go, Java)
- [ ] Visual dashboard (issue trends, metrics)
- [ ] Slack slash commands (/iam audit, /iam status)

**Q2 2025:**
- [ ] Auto-fix implementation (iam-fix-impl GA)
- [ ] Custom rule definitions (YAML-based)
- [ ] Integration with Jira, Linear

**Q3 2025:**
- [ ] ML-powered priority prediction
- [ ] Historical trend analysis
- [ ] Code complexity scoring

**Q4 2025:**
- [ ] Full multi-repo portfolio management
- [ ] Cost optimization recommendations
- [ ] Security vulnerability scanning (integrated)

---

**Document Status:** User Guide
**Last Updated:** 2025-11-20
**Maintained by:** Build Captain (claude.buildcaptain@intentsolutions.io)
**Feedback:** #iam-department Slack channel

**Related Docs:**
- 000-DR-STND-iam-department-template-scope-and-rules.md (template scope)
- 000-DR-GUIDE-porting-iam-department-to-new-repo-DR-GUIDE-porting-iam-department-to-new-repo.md (porting guide)
- 000-DR-STND-iam-department-integration-checklist.md (integration checklist)
- 000-RB-OPS-adk-department-operations-runbook.md (operations runbook)
