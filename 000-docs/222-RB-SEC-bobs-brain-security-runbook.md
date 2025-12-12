# Bob's Brain Security Runbook

**Date:** 2025-12-12
**Phase:** 46 - Security & IAM Hardening

## Overview

This runbook documents security practices, incident response, and operational procedures for Bob's Brain.

## Architecture Security Model

```
                    GitHub Actions (WIF)
                           │
                    ┌──────▼──────┐
                    │ Cloud Run    │ ← Service Account per Gateway
                    │ Gateways     │   (least privilege IAM)
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │ Agent Engine │ ← Service Account (aiplatform.user)
                    │ (Vertex AI)  │
                    └─────────────┘
```

## Service Accounts

| Service Account | Purpose | Key Roles |
|-----------------|---------|-----------|
| `bobs-brain-agent-engine-*` | Agent Engine runtime | aiplatform.user, ml.developer, logging.logWriter |
| `bobs-brain-a2a-gateway-*` | A2A Gateway | aiplatform.user, logging.logWriter |
| `bobs-brain-slack-webhook-*` | Slack Gateway | aiplatform.user, secretmanager.secretAccessor, logging.logWriter |
| `bobs-brain-github-actions` | CI/CD | run.admin, aiplatform.admin, storage.admin, secretmanager.admin |

## IAM Best Practices

### 1. Least Privilege

Every service account has only the permissions needed:
- **Don't use**: `roles/owner`, `roles/editor`
- **Do use**: Specific roles like `roles/run.admin`, `roles/aiplatform.user`

### 2. Service Account Separation

Each component has its own service account:
- Isolates blast radius if compromised
- Easier to audit access patterns
- Simpler to rotate credentials

### 3. Workload Identity Federation (WIF)

For CI/CD, prefer WIF over service account keys:
- No keys to leak
- Short-lived tokens
- GitHub-native identity

Enable WIF in Terraform:
```hcl
enable_wif = true
github_repository = "intent-solutions-io/bobs-brain"
```

## Secret Management

### Secret Manager Usage

All secrets should be stored in Google Secret Manager:
- `slack-bot-token` - Slack bot OAuth token
- `slack-signing-secret` - Slack app signing secret

### Secret Rotation

1. Create new secret version in Secret Manager
2. Deploy Cloud Run services to pick up new version
3. Verify functionality
4. Disable old secret version

```bash
# Create new version
echo -n "NEW_TOKEN" | gcloud secrets versions add slack-bot-token --data-file=-

# Redeploy to pick up new secret
gcloud run services update slack-webhook --platform=managed --region=us-central1

# Verify, then disable old version
gcloud secrets versions disable PREVIOUS_VERSION --secret=slack-bot-token
```

## Security Validation

### CI Security Checks

The CI pipeline runs security validation:
1. **check_security.sh** - Custom repo security scan
2. **Bandit** - Python security linting
3. **Safety** - Dependency vulnerability check

### Manual Security Audit

```bash
# Run security check locally
make check-security

# Run Bandit scan
pip install bandit
bandit -r my_agent/ service/ -ll

# Check dependencies
pip install safety
safety check
```

### What Security Checks Cover

| Check | What It Finds |
|-------|---------------|
| Service account keys | JSON keys in repo |
| Hardcoded secrets | Slack tokens, API keys, AWS keys |
| Overly permissive IAM | roles/owner, roles/editor in Terraform |
| .env files in git | Actual env files tracked |
| Secret Manager patterns | Direct token assignment vs. reference |

## Incident Response

### Secret Exposure

If a secret is exposed (committed to git, logged, etc.):

1. **Immediate**: Rotate the secret
   ```bash
   # Example: Rotate Slack bot token
   # 1. Generate new token in Slack admin
   # 2. Update Secret Manager
   echo -n "NEW_TOKEN" | gcloud secrets versions add slack-bot-token --data-file=-
   # 3. Redeploy affected services
   ```

2. **Investigate**: Check access logs
   ```bash
   # Check Secret Manager access
   gcloud logging read "resource.type=secretmanager.googleapis.com" --limit=100
   ```

3. **Remediate**: Remove from history if in git
   ```bash
   # Use git filter-branch or BFG to remove sensitive data
   ```

### Unauthorized Access

If unauthorized access is detected:

1. **Disable** affected service account immediately
   ```bash
   gcloud iam service-accounts disable SA_EMAIL
   ```

2. **Audit** IAM changes
   ```bash
   gcloud logging read "protoPayload.methodName:SetIamPolicy" --limit=100
   ```

3. **Review** Cloud Run logs
   ```bash
   gcloud logging read "resource.type=cloud_run_revision" --limit=100
   ```

### Dependency Vulnerability

If a vulnerability is found in dependencies:

1. **Assess** severity and exploitability
2. **Update** vulnerable package
   ```bash
   pip install --upgrade PACKAGE_NAME
   pip freeze > requirements.txt
   ```
3. **Test** locally
4. **Deploy** updated version

## Access Control

### Who Has Access

| Role | Access Level | How |
|------|--------------|-----|
| Maintainers | Full admin | GitHub team + GCP IAM |
| Contributors | Read + PR | GitHub permissions |
| CI/CD | Deploy only | WIF + service account |

### Auditing Access

```bash
# List IAM policies for project
gcloud projects get-iam-policy PROJECT_ID

# List service account permissions
gcloud iam service-accounts get-iam-policy SA_EMAIL
```

## Compliance Checklist

### Before Release

- [ ] No service account keys in repository
- [ ] All secrets in Secret Manager
- [ ] IAM follows least privilege
- [ ] Security CI checks pass
- [ ] Dependencies scanned for vulnerabilities
- [ ] WIF enabled for production (recommended)

### Quarterly Review

- [ ] Rotate long-lived secrets
- [ ] Review service account permissions
- [ ] Audit IAM changes
- [ ] Update dependencies
- [ ] Review Cloud Logging alerts

## Monitoring & Alerts

### Recommended Alerts

| Alert | Condition | Action |
|-------|-----------|--------|
| IAM Policy Change | `SetIamPolicy` | Review change |
| Secret Access Spike | > 10 accesses/min | Investigate |
| Auth Failure Spike | > 5 failures/min | Check for attack |
| New Service Account | Created | Verify legitimate |

### Log Queries

**IAM Changes:**
```
protoPayload.methodName:SetIamPolicy
```

**Secret Access:**
```
resource.type="secretmanager.googleapis.com"
protoPayload.methodName:"AccessSecretVersion"
```

**Auth Failures:**
```
resource.type="cloud_run_revision"
httpRequest.status>=400
```

---
**Last Updated:** 2025-12-12
