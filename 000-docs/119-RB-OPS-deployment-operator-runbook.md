# Deployment Operator Runbook

**Document Number:** 119-RB-OPS-deployment-operator-runbook
**Status:** Active
**Date:** 2025-11-20
**Phase:** CICD-DEPT
**Author:** Build Captain (Claude)

---

## Quick Reference

```bash
# Daily operations
make arv-department          # Verify readiness
make deploy-dev              # Deploy to dev
make deploy-status           # Check deployment status
make deploy-logs ENV=dev     # View deployment logs

# Emergency
make deploy-dev              # Skip ARV: set skip_arv=true in workflow UI
make deploy-help             # Show all deployment commands
```

---

## Pre-Deployment Checklist

### Before Every Deployment

- [ ] CI passing on main branch (check GitHub Actions)
- [ ] ARV checks passing locally: `make arv-department`
- [ ] No open critical issues in GitHub
- [ ] Changes reviewed and approved in PR
- [ ] CHANGELOG.md updated (for staging/prod)
- [ ] Team notified (for staging/prod)

---

## Deployment Procedures

### Deploy to Dev

**Frequency:** Multiple times per day
**Approval:** None (automatic after ARV)
**Rollback:** Manual (redeploy previous version)

```bash
# 1. Verify CI passed
open https://github.com/jeremylongshore/bobs-brain/actions

# 2. Run ARV locally
make arv-department

# 3. Trigger deployment
make deploy-dev

# 4. Monitor deployment
make deploy-status

# 5. Check logs if needed
make deploy-logs ENV=dev

# 6. Verify in GCP Console
open https://console.cloud.google.com/vertex-ai/agent-engine
```

**Expected Duration:** 5-10 minutes

**Success Criteria:**
- ✅ ARV gate passed
- ✅ Agent Engine deployed
- ✅ Gateways deployed
- ✅ Endpoint verification passed

---

### Deploy to Staging

**Frequency:** 2-3 times per week
**Approval:** 1 reviewer required
**Rollback:** Manual (redeploy previous version)

```bash
# 1. Verify dev deployment succeeded and tested
make deploy-status

# 2. Update CHANGELOG.md
# Add staging deployment notes

# 3. Run ARV locally
make arv-department

# 4. Trigger deployment
make deploy-staging

# 5. Approve in GitHub Actions UI
open https://github.com/jeremylongshore/bobs-brain/actions
# Click "Review deployments" → Select "staging" → Approve

# 6. Monitor deployment
make deploy-status

# 7. Run smoke tests
# Test critical user flows in staging

# 8. Verify health
make deploy-logs ENV=staging
```

**Expected Duration:** 10-15 minutes (+ approval time)

**Success Criteria:**
- ✅ ARV gate passed (stricter checks)
- ✅ Manual approval granted
- ✅ Staging deployment successful
- ✅ Smoke tests passed

---

### Deploy to Production

**Frequency:** Weekly or as needed
**Approval:** 2+ reviewers required (Engineering Lead + Manager)
**Rollback:** Automated (on failure) or manual

```bash
# 1. Verify staging deployment succeeded and tested
make deploy-status

# 2. Create git tag for version
git tag -a v0.9.0 -m "Release v0.9.0"
git push origin v0.9.0

# 3. Update CHANGELOG.md and README
# Document production changes

# 4. Run ARV locally (strict mode)
make arv-department

# 5. Notify team
# Slack/email: "Production deployment starting"

# 6. Trigger deployment (requires confirmation)
make deploy-prod
# Type: DEPLOY_TO_PRODUCTION

# 7. First approval (Engineering Lead)
open https://github.com/jeremylongshore/bobs-brain/actions
# Engineering Lead: Review → Approve

# 8. Second approval (Manager/Director)
# Manager/Director: Review → Approve

# 9. Monitor deployment closely
watch -n 5 'make deploy-status'

# 10. Run post-deployment tests
# Execute comprehensive test suite

# 11. Monitor for errors
make deploy-logs ENV=prod

# 12. Verify health in GCP Console
open https://console.cloud.google.com/vertex-ai/agent-engine

# 13. Notify team of completion
# Slack/email: "Production deployment complete"
```

**Expected Duration:** 20-30 minutes (+ approval time)

**Success Criteria:**
- ✅ Pre-deployment checks passed
- ✅ ARV gate passed (zero tolerance)
- ✅ Multiple approvals granted
- ✅ Production deployment successful
- ✅ Post-deployment tests passed
- ✅ No increase in error rates
- ✅ Team notified

---

## Monitoring & Verification

### Check Deployment Status

```bash
# View status of all deployments
make deploy-status

# View logs from specific environment
make deploy-logs ENV=dev
make deploy-logs ENV=staging
make deploy-logs ENV=prod

# View in GCP Console
https://console.cloud.google.com/vertex-ai/agent-engine
https://console.cloud.google.com/run
https://console.cloud.google.com/traces/list
```

### Health Checks

**Agent Engine:**
- Check Agent Engine console for errors
- Verify traces in Cloud Trace
- Monitor latency and error rates

**Gateways:**
- Test Slack webhook: Send test message
- Check Cloud Run logs for errors
- Verify endpoints responding

---

## Troubleshooting

### Deployment Failed

**Problem:** Deployment failed in GitHub Actions

**Steps:**
1. Check logs: `make deploy-logs ENV=dev`
2. Identify failing job (arv-gate, deploy-agent-engine, deploy-gateways)
3. If ARV failed:
   - Run locally: `make arv-department-verbose`
   - Fix failing checks
   - Re-trigger deployment
4. If deployment failed:
   - Check GCP Console for errors
   - Verify environment variables set
   - Verify secrets set
   - Re-trigger deployment

### ARV Gate Blocking Deployment

**Problem:** ARV checks failing, blocking deployment

**Steps:**
1. Run verbose ARV: `make arv-department-verbose`
2. Identify failing check:
   - `config-basic`: Fix .env configuration
   - `tests-unit`: Fix failing tests
   - `rag-readiness`: Check RAG configuration
   - `engine-flags-safety`: Fix Agent Engine flags
3. Fix issues locally
4. Re-run ARV: `make arv-department`
5. Re-trigger deployment when ARV passes

### Emergency Deployment (Skip ARV)

**⚠️ USE ONLY IN TRUE EMERGENCIES**

**Steps:**
1. Go to GitHub Actions → Deploy to Dev
2. Click "Run workflow"
3. Set `skip_arv` to `true`
4. Acknowledge risk and proceed
5. **IMMEDIATELY** file issue to fix ARV failures
6. Plan fix deployment ASAP

### Rollback Production

**Problem:** Production deployment causing errors

**Steps:**
1. If automated rollback didn't trigger:
   ```bash
   # Get previous successful version
   git log --oneline

   # Checkout previous version
   git checkout <previous-commit>

   # Trigger emergency deployment
   make deploy-prod
   ```
2. Notify team immediately
3. Investigate root cause
4. File post-mortem issue

---

## Common Issues

### "GitHub CLI not found"

```bash
# Install gh CLI
# macOS: brew install gh
# Linux: https://cli.github.com/manual/installation

# Authenticate
gh auth login
```

### "Environment variables not set"

**Solution:**
1. Go to repo Settings → Environments
2. Select environment (dev/staging/prod)
3. Add variables: `DEV_PROJECT_ID`, `DEV_REGION`, `DEV_STAGING_BUCKET`

### "Approval stuck waiting"

**Solution:**
1. Check GitHub Actions workflow
2. Click "Review deployments"
3. Select environment
4. Click "Approve deployment"

### "WIF authentication failed"

**Solution:**
1. Verify secrets set:
   - `GCP_WORKLOAD_IDENTITY_PROVIDER`
   - `GCP_SERVICE_ACCOUNT`
2. Check WIF setup in GCP Console
3. Verify service account has permissions

---

## Daily Operations Checklist

### Morning

- [ ] Check overnight deployments: `make deploy-status`
- [ ] Review GCP Console for errors
- [ ] Check Slack for deployment notifications

### Before Deployment

- [ ] CI passing: Check GitHub Actions
- [ ] ARV passing: `make arv-department`
- [ ] Team notified (staging/prod only)

### After Deployment

- [ ] Deployment succeeded: `make deploy-status`
- [ ] Health checks passed
- [ ] No errors in logs: `make deploy-logs ENV=<env>`
- [ ] Team notified of completion (staging/prod)

### End of Day

- [ ] All deployments completed or rolled back
- [ ] No critical issues open
- [ ] Documentation updated
- [ ] Team handoff completed

---

## Escalation

### When to Escalate

- ARV blocking critical fix deployment
- Production deployment failed with automated rollback
- Repeated deployment failures (3+ times)
- Security issue discovered in deployment
- Data loss or corruption

### Escalation Contacts

- **Engineering Lead:** [Name/Slack]
- **Manager/Director:** [Name/Slack]
- **On-Call Engineer:** [PagerDuty/Slack]
- **Security Team:** [Email/Slack]

---

## Related Documentation

- `118-DR-STND-cicd-pipeline-for-iam-department.md` - Full CI/CD standard
- `117-AA-REPT-iam-department-arv-implementation.md` - ARV framework
- `116-DR-STND-config-and-feature-flags-standard-v1.md` - Configuration standard
- `000-RB-OPS-adk-department-operations-runbook.md` - General operations

---

**Status:** ✅ Active
**Owner:** DevOps/Operations Team
**Last Updated:** 2025-11-20
