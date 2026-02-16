# ADK Department Operations Runbook

**Document ID:** 000-RB-OPS-adk-department-operations-runbook
**Title:** ADK Department Daily Operations & Troubleshooting Runbook
**Phase:** T3 (Operations & Day-to-Day Use)
**Status:** Operational Reference
**Created:** 2025-11-20
**Purpose:** Practical guide for operating the IAM department in production.

---

## I. Executive Summary

This runbook provides daily operational procedures, monitoring guidance, and troubleshooting workflows for the ADK-based IAM software engineering department.

**Audience:** DevOps teams, SREs, product operators
**Prerequisites:** IAM department deployed and integrated per 000-DR-GUIDE-porting-iam-department-to-new-repo porting guide

---

## II. Quick Reference

### Daily Operations Checklist

- [ ] Check pipeline execution metrics (success rate, duration)
- [ ] Review new issues created by iam-issue
- [ ] Validate QA verdicts from iam-qa
- [ ] Monitor ARV gate status
- [ ] Check for failed pipeline runs
- [ ] Review agent logs for errors

### Emergency Contacts

- **Build Captain:** claude.buildcaptain@intentsolutions.io (CI/CD alerts only)
- **Product Team:** [Your team contact]
- **On-Call Engineer:** [Your on-call rotation]

### Key URLs

- **GitHub Repository:** [Your repo URL]
- **CI/CD Dashboard:** GitHub Actions
- **Agent Engine Console:** https://console.cloud.google.com/vertex-ai/agent-engine
- **Cloud Logging:** https://console.cloud.google.com/logs
- **Cloud Trace:** https://console.cloud.google.com/traces

---

## III. Architecture Overview for Operators

### Component Map

```
User/Slack → Bob (Orchestrator)
                ↓
          iam-senior-adk-devops-lead (Foreman)
                ↓
    ┌───────────┴─────────────┐
    ↓           ↓             ↓
iam-adk    iam-issue    iam-qa    (Specialists)
    ↓           ↓             ↓
 Findings  IssueSpecs   Verdicts
    ↓           ↓             ↓
         PipelineResult
```

### Pipeline Modes

1. **preview** - Analysis only, no artifacts created
2. **dry-run** - Generate IssueSpecs, no GitHub interaction
3. **create** - Full pipeline with GitHub issue creation

**Safety:** Always start with `preview` mode, escalate to `create` only after validation.

---

## IV. Daily Operations

### A. Monitoring Pipeline Health

**1. Check Pipeline Execution Metrics**

```bash
# View recent pipeline runs
cd /path/to/repo
grep "pipeline_run_id" logs/pipeline.log | tail -20

# Check success rate
grep "PipelineResult" logs/pipeline.log | grep -c "error: null"
```

**Expected:**
- Success rate > 90%
- Average duration < 5 minutes for typical audits
- No repeated failures on same repo

**2. Review Pipeline Results**

```bash
# List recent IssueSpecs generated
ls -lt pipeline_artifacts/issues/*.json | head -10

# Check QA verdicts
grep "QAVerdict" logs/pipeline.log | grep "verdict: pass"
```

**Red Flags:**
- Zero issues found on known problematic modules (false negatives)
- Excessive issues (> 100) on single run (false positives or real crisis)
- All QA verdicts = "fail" (agent misconfigured)

**3. Monitor Agent Health**

```bash
# Validate configuration (CONF2)
make check-config  # See 116-DR-STND-config-and-feature-flags-standard-v1.md

# Check agent availability
make check-arv-minimum

# Test foreman responsiveness
python scripts/test_foreman_health.py
```

**Expected:**
- Configuration validation passes (all required vars set)
- All ARV checks pass
- Foreman responds within 2 seconds

---

### B. Reviewing Generated Issues

**1. Access IssueSpecs**

```bash
# View pending issues (dry-run mode)
cat pipeline_artifacts/issues/YYYY-MM-DD/*.json | jq .

# Check GitHub issues (create mode)
gh issue list --label "iam-department" --state open
```

**2. Validate Issue Quality**

For each IssueSpec, check:
- [ ] **Title** is clear and actionable
- [ ] **Body** provides sufficient context (file, line, problem, suggestion)
- [ ] **Priority** is appropriate (low/medium/high/critical)
- [ ] **Category** is accurate (adk-compliance, security, performance, etc.)
- [ ] **Related files** list is complete

**3. Triage and Assign**

```bash
# Bulk assign issues to team
gh issue list --label "iam-department" --json number,title \
  | jq -r '.[] | "\(.number) \(.title)"' \
  | xargs -I {} gh issue edit {} --assignee @me

# Add milestone
gh issue list --label "iam-department" \
  | xargs -I {} gh issue edit {} --milestone "Q1-2025"
```

---

### C. Running Manual Pipelines

**1. Single Repository Audit**

```bash
# Preview mode (safe, no artifacts)
python scripts/run_swe_pipeline_once.py \
  --repo-path /path/to/repo \
  --task "Audit for ADK compliance" \
  --mode preview

# Dry-run (generates IssueSpecs locally)
python scripts/run_swe_pipeline_once.py \
  --repo-path /path/to/repo \
  --task "Check memory wiring patterns" \
  --mode dry-run

# Create mode (writes GitHub issues)
python scripts/run_swe_pipeline_once.py \
  --repo-path /path/to/repo \
  --task "Find security vulnerabilities" \
  --mode create \
  --env prod  # Use prod agent configurations
```

**2. Scheduled Audits**

Set up cron jobs or scheduled workflows:

```bash
# Daily ADK compliance check (preview)
0 2 * * * cd /path/to/repo && make run-swe-pipeline-demo

# Weekly security audit (create mode)
0 3 * * 1 cd /path/to/repo && python scripts/run_swe_pipeline_once.py \
  --repo-path . --task "Security audit" --mode create
```

**3. Slack-Triggered Pipelines**

```bash
# Check Slack webhook health
curl https://your-slack-webhook.run.app/health

# View recent Slack events
gcloud logging read "resource.type=cloud_run_revision AND \
  resource.labels.service_name=slack-webhook" \
  --limit 50 --format json
```

---

## V. Failure Modes & Debugging

### A. Pipeline Failures

**Symptom:** `PipelineResult.error` is not null

**Common Causes:**

1. **Agent not responding**
   ```bash
   # Check agent deployment
   gcloud ai reasoning-engines list \
     --project=PROJECT_ID \
     --region=LOCATION \
     --filter="displayName:iam-senior-adk-devops-lead"

   # Test agent directly
   curl -X POST https://AGENT_ENGINE_URL/query \
     -H "Authorization: Bearer $(gcloud auth print-access-token)" \
     -d '{"message": "test"}'
   ```

2. **Correlation ID not propagated**
   ```bash
   # Check logs for correlation ID
   grep "pipeline_run_id: abc123" logs/pipeline.log

   # If missing, check A2A adapter
   cat agents/a2a/adapter.py | grep correlation_id
   ```

3. **Timeout exceeded**
   ```bash
   # Check pipeline duration
   grep "pipeline_duration_seconds" logs/pipeline.log | awk '{print $2}' | sort -n

   # If > 600s, investigate slow agents
   grep "agent_step" logs/pipeline.log | grep "duration"
   ```

**Resolution:**
- Restart failed pipeline run with same `pipeline_run_id`
- Check agent logs for errors
- Verify network connectivity to Agent Engine

---

### B. No Issues Found (False Negatives)

**Symptom:** Pipeline completes successfully but `total_issues_found = 0` on known problematic code

**Diagnostic Steps:**

1. **Check iam-adk system prompt**
   ```bash
   cat agents/iam-adk/system-prompt.md | grep -A 10 "What to look for"

   # Ensure product-specific patterns are included
   ```

2. **Verify repos.yaml configuration**
   ```bash
   cat agents/config/repos.yaml | grep -A 5 "primary: true"

   # Check:
   # - repo_hint matches configured repository
   # - key_directories are correct
   # - analysis patterns include relevant file types
   ```

3. **Test iam-adk directly**
   ```bash
   python -c "
   from agents.a2a.adapter import call_agent_local
   from agents.a2a.contracts import A2AAgentCall

   call = A2AAgentCall(
       agent_role='iam-adk',
       prompt='Analyze /path/to/problematic/file.py for ADK compliance',
       correlation_id='test-123'
   )
   result = call_agent_local('iam-adk', call)
   print(result)
   "
   ```

4. **Review RAG configuration (if enabled)**
   ```bash
   make check-rag-readiness

   # Ensure knowledge sources are indexed
   gsutil ls gs://YOUR_KNOWLEDGE_BUCKET/
   ```

**Resolution:**
- Update agent system prompts with product-specific checks
- Add product-specific tools to iam-adk
- Re-index knowledge sources if RAG is stale

---

### C. Too Many Issues (False Positives)

**Symptom:** Single pipeline run creates > 100 IssueSpecs

**Diagnostic Steps:**

1. **Review issue distribution**
   ```bash
   # Check issue categories
   jq -r .category pipeline_artifacts/issues/*.json | sort | uniq -c

   # Check affected files
   jq -r '.related_files[]' pipeline_artifacts/issues/*.json | sort | uniq -c
   ```

2. **Validate with iam-qa**
   ```bash
   # Check QA verdicts
   grep "QAVerdict" logs/pipeline.log | jq .verdict

   # If many "needs-review", investigate iam-qa criteria
   cat agents/iam-qa/system-prompt.md | grep -A 10 "Validation Criteria"
   ```

3. **Test iam-issue quality**
   ```bash
   # Sample 10 random IssueSpecs
   find pipeline_artifacts/issues -name "*.json" | shuf -n 10 | xargs cat | jq .

   # Check for duplicate issues
   jq -r .title pipeline_artifacts/issues/*.json | sort | uniq -d
   ```

**Resolution:**
- Tune iam-adk sensitivity (update system prompt)
- Improve iam-issue deduplication logic
- Add iam-qa pre-filters for low-value findings

---

### D. ARV Gate Failures

**Symptom:** `make check-arv-minimum` fails

**Common Issues:**

1. **Missing agent.py**
   ```bash
   # Check agent structure
   find agents/iam-* -name "agent.py"

   # If missing:
   cp templates/iam-department/agents/iam-adk/agent.py.template \
     agents/iam-adk/agent.py
   # Remove .template extension, customize
   ```

2. **Missing system prompts**
   ```bash
   find agents/iam-* -name "system-prompt.md"

   # Create from template if missing
   ```

3. **Broken imports**
   ```bash
   # Test imports
   python -c "from agents.shared_contracts import PipelineRequest; print('OK')"

   # Check PYTHONPATH
   echo $PYTHONPATH
   ```

**Resolution:**
- Run `scripts/check_arv_minimum.py --verbose` for detailed errors
- Compare to bobs-brain reference implementation
- Fix structure/imports, re-run ARV checks

---

## VI. Monitoring & Observability

### A. Key Metrics

**1. Pipeline Metrics**

Track in dashboards:
- **Success Rate:** % of pipeline runs completing without errors
- **Issue Throughput:** Number of IssueSpecs generated per day
- **False Positive Rate:** % of issues closed as "won't fix"
- **Pipeline Duration:** P50, P95, P99 (target < 5 minutes)

**2. Agent Metrics**

- **Agent Availability:** % uptime for iam-* agents
- **Response Time:** P50, P95 per agent (target < 2s)
- **Error Rate:** Errors per 1000 invocations
- **Token Usage:** Total tokens consumed per agent (cost tracking)

**3. Quality Metrics**

- **Issue Resolution Time:** Days from creation to closure
- **QA Pass Rate:** % of fixes passing iam-qa validation
- **Documentation Coverage:** % of issues with updated docs

### B. Logging

**1. Structured Logging Format**

All pipeline logs should include:
```json
{
  "pipeline_run_id": "uuid",
  "correlation_id": "uuid",
  "agent": "iam-adk",
  "step": "analysis",
  "status": "started|completed|failed",
  "duration_ms": 1234,
  "timestamp": "2025-11-20T10:00:00Z",
  "message": "Analysis complete, found 5 issues"
}
```

**2. Log Queries**

```bash
# Failed pipeline runs
gcloud logging read "jsonPayload.status='failed'" \
  --project=PROJECT_ID \
  --limit 50

# Slow pipeline runs (> 5 minutes)
gcloud logging read "jsonPayload.duration_ms > 300000" \
  --project=PROJECT_ID

# Specific correlation ID
gcloud logging read "jsonPayload.correlation_id='abc-123'" \
  --project=PROJECT_ID
```

### C. Alerting

**Critical Alerts:**
- Pipeline success rate drops below 80% (30-minute window)
- Any agent fails ARV checks
- Zero issues found for 3+ consecutive runs (possible false negatives)
- Pipeline duration exceeds 10 minutes

**Warning Alerts:**
- Pipeline success rate 80-90%
- Agent response time > 5 seconds (P95)
- More than 50 issues generated in single run

**Alert Channels:**
- Slack: #iam-department-alerts
- Email: oncall@yourcompany.com
- PagerDuty: (for critical only)

---

## VII. Configuration Management

### A. Environment Variables

**Core Configuration:**
```bash
# Check current config
env | grep "PRODUCT_NAME\|PROJECT_ID\|LOCATION"

# Update config (requires redeployment)
vim .env
# ... edit values ...
make deploy  # Or trigger CI/CD
```

**Per-Agent Configuration:**
```bash
# Check agent-specific settings
cat agents/config/agent_engine_config.py

# Update reasoning engine IDs (per environment)
vim agents/config/agent_engine_config.py
# PROD_CONFIG["iam-senior-adk-devops-lead"].reasoning_engine_id = "..."
```

### B. Feature Flags

```bash
# Check enabled features
cat agents/config/features.py

# Toggle RAG
vim agents/config/features.py
# ENABLE_RAG = True  # False to disable

# Toggle Slack integration
# ENABLE_SLACK = True

# Redeploy to apply changes
make deploy
```

### C. repos.yaml Updates

```bash
# Add new repository
vim agents/config/repos.yaml
# repositories:
#   - name: "new-repo"
#     full_name: "org/new-repo"
#     ...

# Validate repos.yaml
python -c "
import yaml
with open('agents/config/repos.yaml') as f:
    config = yaml.safe_load(f)
    print(f'Configured {len(config[\"repositories\"])} repositories')
"
```

---

## VIII. Common Operational Scenarios

### Scenario 1: Onboarding New Repository

**Steps:**
1. Add repository to `agents/config/repos.yaml`
2. Create synthetic test data in `tests/data/synthetic_repo/NEW_REPO/`
3. Run preview pipeline:
   ```bash
   python scripts/run_swe_pipeline_once.py \
     --repo-path tests/data/synthetic_repo/NEW_REPO \
     --task "Initial audit" \
     --mode preview
   ```
4. Review results, tune agent prompts as needed
5. Run dry-run to generate IssueSpecs
6. Review IssueSpecs for quality
7. Enable create mode for production use

### Scenario 2: Adjusting Issue Sensitivity

**Problem:** Too many/too few issues generated

**Solution:**

**For iam-adk (audit agent):**
```bash
vim agents/iam-adk/system-prompt.md

# Increase sensitivity:
# - Add more specific anti-patterns to look for
# - Lower severity threshold for reporting

# Decrease sensitivity:
# - Add exceptions ("ignore X in test files")
# - Raise severity threshold
```

**For iam-issue (issue creator):**
```bash
vim agents/iam-issue/system-prompt.md

# Add deduplication logic:
# - "If multiple findings in same file, group into one issue"
# - "Skip issues with priority=low in mature modules"
```

**For iam-qa (quality gate):**
```bash
vim agents/iam-qa/system-prompt.md

# Add quality filters:
# - "Mark as 'needs-review' if issue body < 50 words"
# - "Fail issues without clear reproduction steps"
```

### Scenario 3: Debugging Slow Pipeline

**Steps:**

1. **Profile pipeline execution:**
   ```bash
   grep "agent_step" logs/pipeline.log | grep "duration_ms" | \
     awk '{print $2, $4}' | sort -k2 -n
   ```

2. **Identify bottleneck agent:**
   - iam-adk: Likely analyzing too many files
   - iam-issue: Generating excessive IssueSpecs
   - iam-qa: Running complex validation

3. **Optimize slow agent:**
   ```bash
   # For iam-adk:
   # - Add more aggressive file exclusions in repos.yaml
   # - Limit analysis scope per invocation

   # For iam-qa:
   # - Cache validation results
   # - Parallelize checks
   ```

4. **Consider horizontal scaling:**
   ```bash
   # Deploy multiple instances of slow agent
   # Update A2A adapter to load-balance calls
   ```

### Scenario 4: Rollback After Bad Deployment

**Steps:**

1. **Identify last good version:**
   ```bash
   git log --oneline | head -10
   # Note commit SHA of last stable version
   ```

2. **Revert to last good commit:**
   ```bash
   git revert <bad-commit-sha>
   git push origin main

   # Or full rollback:
   git reset --hard <last-good-commit-sha>
   git push --force origin main  # Use with caution!
   ```

3. **Redeploy via CI/CD:**
   - GitHub Actions will automatically deploy reverted version

4. **Verify rollback:**
   ```bash
   make check-arv-minimum
   python scripts/run_swe_pipeline_once.py --mode preview
   ```

5. **Post-mortem:**
   - Document what went wrong in AAR
   - Add regression tests to prevent recurrence

---

## IX. Maintenance Tasks

### A. Weekly

- [ ] Review generated issues, close false positives
- [ ] Check for new ADK documentation updates
- [ ] Update knowledge base if RAG enabled (re-index)
- [ ] Review agent performance metrics
- [ ] Tune system prompts based on feedback

### B. Monthly

- [ ] Run `bobs-brain` alignment audit (compare to latest patterns)
- [ ] Update ADK and dependencies (`pip install --upgrade google-adk`)
- [ ] Review and archive old pipeline logs
- [ ] Conduct team retrospective on IAM department effectiveness
- [ ] Update ops runbook with new learnings

### C. Quarterly

- [ ] Major version upgrades (ADK, Agent Engine)
- [ ] Security audit of agent configurations
- [ ] Cost analysis and optimization
- [ ] Evaluate new agent specialists (iam-fix, iam-doc, etc.)
- [ ] Update porting guide with template improvements

---

## X. Safety & Guardrails

### A. Mode Progression

**Always follow this sequence:**

1. **preview** - Safe exploration, no side effects
2. **dry-run** - Generate artifacts locally, review quality
3. **create** - Production use with GitHub integration

**Never skip preview → dry-run → create progression on new repos or after major changes.**

### B. Issue Creation Throttling

```bash
# Set rate limits in agents/config/repos.yaml
github:
  issue_creation:
    enabled: true
    max_issues_per_run: 20  # Prevent spam
    max_issues_per_day: 100
    cooldown_hours: 1  # Wait before next run
```

### C. Manual Review Gates

**Before enabling create mode:**
- [ ] Review at least 10 IssueSpecs from dry-run
- [ ] Confirm zero false positives in sample
- [ ] Get team sign-off on issue quality
- [ ] Set GitHub label "iam-department" for tracking
- [ ] Configure issue template and assignees

### D. Emergency Shutdown

**If pipeline is misbehaving:**

1. **Disable issue creation immediately:**
   ```bash
   vim agents/config/repos.yaml
   # github.issue_creation.enabled: false
   git commit -m "emergency: disable issue creation" && git push
   ```

2. **Stop scheduled runs:**
   ```bash
   # Disable cron jobs
   crontab -e
   # Comment out IAM department jobs
   ```

3. **Investigate root cause:**
   - Check recent commits
   - Review pipeline logs
   - Test agents individually

4. **Gradual re-enable:**
   - Start with preview mode
   - Validate fixes with dry-run
   - Slowly ramp up to create mode

---

## XI. Troubleshooting Quick Reference

| Symptom | Likely Cause | Quick Fix |
|---------|--------------|-----------|
| Pipeline fails with "agent not found" | Agent not deployed | Check Agent Engine, redeploy |
| No issues found on bad code | Agent prompt too lenient | Tune iam-adk system prompt |
| Too many duplicate issues | iam-issue dedup broken | Update iam-issue grouping logic |
| QA always fails | iam-qa criteria too strict | Review iam-qa system prompt |
| Pipeline takes > 10 minutes | Analyzing too many files | Update repos.yaml exclusions |
| ARV checks fail | Missing agent.py or imports | Run `check_arv_minimum.py --verbose` |
| Correlation IDs missing | A2A adapter not wired | Check A2A adapter implementation |
| RAG returns no results | Datastore not indexed | Run `scripts/setup_vertex_search.sh` |

---

## XII. Runbook Maintenance

**This runbook should be updated:**
- After any operational incident (add new troubleshooting section)
- When new agents are added (update architecture, monitoring)
- When ops procedures change (update daily checklist)
- Quarterly (review all sections for accuracy)

**Ownership:** DevOps team + IAM department maintainers

**Change Process:**
1. Propose update via PR
2. Review with ops team
3. Merge after approval
4. Announce changes in #iam-department Slack channel

---

**Document Status:** Operational Reference
**Last Updated:** 2025-11-20
**Maintained by:** Build Captain (claude.buildcaptain@intentsolutions.io)
**Next Review:** 2025-12-20

**Related Docs:**
- 000-DR-STND-iam-department-template-scope-and-rules.md (template scope)
- 000-DR-GUIDE-porting-iam-department-to-new-repo-DR-GUIDE-porting-iam-department-to-new-repo.md (porting guide)
- 000-DR-STND-iam-department-integration-checklist.md (integration checklist)
- 000-DR-GUIDE-iam-department-user-guide-DR-GUIDE-how-to-use-bob-and-iam-department-for-swe.md (usage guide)
- **118-DR-STND-cicd-pipeline-for-iam-department.md** (CI/CD pipeline standard - CICD-DEPT)
- **119-RB-OPS-deployment-operator-runbook.md** (deployment operations runbook - CICD-DEPT)
