# ARV Minimum Gate Standard for Bob's Brain

**Document ID:** 000-DR-STND-arv-minimum-gate-DR-STND-arv-minimum-gate-for-bobs-brain
**Created:** 2025-11-20
**Phase:** RC2 (Observability)
**Status:** Active

---

## Purpose

This document defines the **Agent Readiness Verification (ARV) Minimum Gate** for the Bob's Brain ADK/Agent Engineering Department. The ARV minimum gate ensures that all agents meet baseline structural and observability requirements before deployment.

## What ARV Minimum Enforces

The ARV minimum check (`scripts/check_arv_minimum.py`) validates that:

### 1. Structured Logging Infrastructure (Phase RC2)
- **Logging helper exists:** `agents/utils/logging.py` is present and importable
- **Key functions available:**
  - `get_logger()`
  - `log_pipeline_start()`
  - `log_pipeline_complete()`
  - `log_agent_step()`
  - `log_github_operation()`

### 2. Correlation ID Wiring (Phase RC2)
- **PipelineRequest has pipeline_run_id:** Auto-generated UUID for each pipeline run
- **PipelineResult has pipeline_run_id:** Correlation ID flows through entire pipeline
- **Field structure:** `pipeline_run_id` field exists and is properly typed

### 3. Foreman Orchestrator Observability
- **Logging imports:** Orchestrator imports structured logging helper
- **Correlation ID usage:** `pipeline_run_id` is used throughout orchestrator
- **Logging calls present:** Pipeline start, completion, agent steps logged

### 4. IAM-* Agent Structure
For each `iam-*` agent directory (excluding `iam_senior_adk_devops_lead` orchestrator module):
- **agent.py exists:** Main agent implementation file present
- **Valid Python syntax:** agent.py parses without syntax errors
- **Documentation present:** Has README.md, prompts/system.md, or docs/ directory
- **Test coverage (warning):** Test files exist (non-blocking if missing)

## Where It Runs

### CI Pipeline
The ARV check runs in the `.github/workflows/ci.yml` pipeline as the `arv-check` job:

```yaml
arv-check:
  runs-on: ubuntu-latest
  needs: drift-check  # Only run if drift check passes
  steps:
    - uses: actions/checkout@v4
    - name: Set up Python
      uses: actions/setup-python@v5
      with:
        python-version: '3.11'
    - name: Install dependencies
      run: pip install -r requirements.txt || echo "Requirements not found, continuing"
    - name: Run ARV minimum check
      run: make check-arv-minimum
```

**Execution Order:**
1. `drift-check` (R8: Hard Mode violations)
2. **`arv-check`** ← Configuration and ARV gates
   - Configuration validation (CONF2) - see `116-DR-STND-config-and-feature-flags-standard-v1.md`
   - ARV minimum requirements (this doc)
   - ARV engine flags (Phase AE3)
3. `lint`, `test`, `security` (only if drift and ARV pass)

**Blocking Behavior:**
- If ARV check fails (exit code 1), all downstream jobs are blocked
- Warnings (test coverage, missing docs) do not block pipeline
- Only hard failures (missing required files, syntax errors) block

### Make Targets
The ARV check is accessible via Make targets:

```bash
make check-arv-minimum           # Run ARV check (concise output)
make check-arv-minimum-verbose   # Run with detailed output
make arv-gates                   # Run all ARV gates (RAG + minimum)
```

**Combined ARV Gates:**
The `arv-gates` target runs all Agent Readiness Verification checks:
- `check-config`: Validates environment configuration (CONF2)
- `check-rag-readiness`: Validates RAG configuration (Phase RC1)
- `check-arv-minimum`: Validates minimum requirements (Phase RC2)
- `check-arv-engine-flags`: Validates engine flags safety (Phase AE3)

## Exit Codes

| Exit Code | Meaning | Pipeline Behavior |
|-----------|---------|-------------------|
| `0` | ARV minimum met | Continue to lint/test |
| `1` | Requirements not met (blocking) | Fail pipeline |
| `2` | Error during checks | Fail pipeline |

## Who Can Override or Update

### Override Policy
**ARV minimum checks should NOT be overridden.** These are fundamental structural requirements for agent readiness and observability.

If you believe you need an exception:
1. Document the reason in a GitHub issue
2. Tag the issue with `arv-exception`
3. Get approval from:
   - Build Captain (claude.buildcaptain@intentsolutions.io)
   - Senior DevOps Lead (conceptually iam-senior-adk-devops-lead)

### Update Process
To update ARV minimum requirements:

**1. Modify Check Script**
Edit `scripts/check_arv_minimum.py` to add/remove checks:
- Add new checkers in `ARVMinimumChecker` class
- Update `run()` method to call new checkers
- Update report generation to include new checks

**2. Update Documentation**
Update this document (000-DR-STND-arv-minimum-gate) with:
- New requirements in "What ARV Minimum Enforces"
- Rationale for the change
- Expected impact on existing agents

**3. Staged Rollout**
For breaking changes (new required structures):
1. Add check as **warning** first (Phase N)
2. Give teams 1-2 sprints to comply
3. Promote to **error** (Phase N+1)

**4. Update CI**
No changes needed to `.github/workflows/ci.yml` unless:
- Changing job dependencies
- Adding new ARV gate types beyond minimum

## Warnings vs Errors

### Errors (Blocking)
These **fail the pipeline** (exit code 1):
- Logging helper missing or not importable
- Correlation IDs not wired in contracts
- Orchestrator missing logging or correlation ID usage
- IAM-* agent missing agent.py
- IAM-* agent has syntax errors

### Warnings (Non-Blocking)
These **do not fail the pipeline** but appear in output:
- IAM-* agent missing documentation (README, prompts/, docs/)
- IAM-* agent missing test coverage
- RAG config contains placeholder values (Phase RC1)

**Rationale:** Test coverage and docs are important but not deployment-blockers. They should be tracked and improved, but shouldn't prevent valid agents from deploying.

## Example Output

### Passing Check
```
============================================================
ARV MINIMUM GATE CHECK (Phase RC2)
============================================================
✅ Logging Helper: PRESENT
✅ Correlation IDs: WIRED
✅ Foreman Orchestrator: READY
✅ IAM-* Agents: READY

✅ ARV MINIMUM MET

⚠️  Warnings (not blockers):
  - iam_issue: no test coverage found
  - iam_adk: no test coverage found

💡 Next Steps:
  - ARV minimum requirements met
  - Ready to proceed with deployment
  - Address warnings for production readiness
============================================================
```

### Failing Check
```
============================================================
ARV MINIMUM GATE CHECK (Phase RC2)
============================================================
✅ Logging Helper: PRESENT
✅ Correlation IDs: WIRED
❌ Foreman Orchestrator: NOT READY
✅ IAM-* Agents: READY

❌ ARV MINIMUM NOT MET

❌ Blocking Issues:
  - Orchestrator doesn't import logging helper
  - Orchestrator doesn't use pipeline_run_id correlation IDs

💡 Next Steps:
  - Fix blocking issues above
  - Ensure all iam-* agents have agent.py and docs
  - Verify correlation ID wiring
============================================================
```

## Integration with Other Gates

### Relationship to Drift Detection (R8)
```
CI Pipeline Order:
1. drift-check (R8: Hard Mode violations)
   ↓ (blocks if failed)
2. arv-check (ARV minimum requirements)
   ↓ (blocks if failed)
3. lint, test, security
```

**drift-check** ensures we haven't violated Hard Mode rules (ADK-only, no LangChain, etc.)
**arv-check** ensures we have proper observability and structure

Both must pass before code quality checks run.

### Relationship to RAG Readiness (Phase RC1)
```
make arv-gates
  ├── check-rag-readiness (Phase RC1)
  │   ├── RAG config module exists
  │   ├── Tool factory works
  │   ├── Environment variables documented
  │   └── .env.example has RAG section
  │
  └── check-arv-minimum (Phase RC2)
      ├── Logging helper exists
      ├── Correlation IDs wired
      ├── Orchestrator has observability
      └── IAM-* agents have structure
```

Combined ARV gates ensure both RAG foundation and observability are ready.

## Future Enhancements

### Planned (Phase RC3+)
- **Memory wiring check:** Validate Session + Memory Bank for all agents
- **A2A card validation:** Check AgentCard structure for deployed agents
- **Tool profile check:** Verify tools are properly registered
- **Deployment readiness:** Check Terraform configs exist for new agents

### Under Consideration
- **Performance thresholds:** Minimum performance benchmarks for agents
- **Security scan:** Basic security checks (secrets, permissions)
- **Doc quality scoring:** Automated documentation quality metrics

## Related Documents

### Operational Standards
- **093-DR-STND-bob-rag-readiness-standard.md** - RAG readiness standard (Phase RC1)
- **094-AT-ARCH-iam-swe-pipeline-orchestration.md** - Pipeline architecture
- **000-DR-STND-arv-minimum-gate-DR-STND-arv-minimum-gate-for-bobs-brain.md** - This document (ARV minimum gate)
- **000-RB-OPS-adk-department-operations-runbook-RB-OPS-adk-department-operations-runbook.md** - Daily operations and troubleshooting

### Template & Porting Documentation
- **000-DR-STND-iam-department-template-scope-and-rules-DR-STND-iam-department-template-scope-and-rules.md** - Template scope and reusability
- **000-DR-GUIDE-porting-iam-department-to-new-repo-DR-GUIDE-porting-iam-department-to-new-repo.md** - Step-by-step porting guide
- **000-DR-STND-iam-department-integration-checklist-DR-STND-iam-department-integration-checklist.md** - Integration checklist
- **000-DR-GUIDE-iam-department-user-guide-DR-GUIDE-how-to-use-bob-and-iam-department-for-swe.md** - User guide

### Repository Guidance
- **CLAUDE.md** - Repository guidance and ARV gate usage
- **README.md** - Quick start and architecture overview
- **templates/iam-department/README.md** - Template quick start

## Changelog

| Date | Change | Author |
|------|--------|--------|
| 2025-11-20 | Initial ARV minimum gate standard | Build Captain (Phase RC2) |

---

**Status:** Active
**Next Review:** Phase RC3 (Release Packaging)
