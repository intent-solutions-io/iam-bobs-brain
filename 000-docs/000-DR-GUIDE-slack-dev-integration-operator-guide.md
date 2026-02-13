# Slack Dev Integration - Operator Guide

**Date:** 2025-11-20
**Phase:** SLACK-ENDTOEND-DEV (Complete)
**Status:** ✅ Production-Ready
**Category:** DR - Documentation & Reference
**Document Type:** GUIDE - Operator guide for Slack integration

---

## Executive Summary

This guide provides step-by-step instructions for enabling, configuring, testing, and disabling the Slack bot integration with Bob's Brain in **development environments only**.

**What You Get:**
- Talk to Bob via @bobs_brain mentions in Slack
- Full Agent Engine integration (Option B: via a2a_gateway preferred)
- Feature flag safety (SLACK_BOB_ENABLED)
- Comprehensive smoke tests
- Clear enable/disable procedures

**Safety First:**
- Dev-only by default
- Disabled unless explicitly enabled
- Configuration validation prevents misconfiguration
- Graceful degradation when disabled

---

## Architecture Overview

### Flow Diagram
```
User mentions @bobs_brain in Slack
    ↓
Slack App sends event webhook
    ↓
Cloud Run: service/slack_webhook/ (FastAPI)
    ↓
Feature Flag Check: SLACK_BOB_ENABLED=true?
    ↓
[Option B - Preferred] A2A Gateway (service/a2a_gateway/)
    ↓
Vertex AI Agent Engine (Bob)
    ↓
Response back to Slack thread
```

### Key Components

1. **Slack App** (`A099YKLCM1N` - bobs_brain)
   - Event subscriptions for app_mention
   - Bot OAuth token (SLACK_BOT_TOKEN)
   - Signing secret for verification

2. **Cloud Run Service** (`slack-webhook`)
   - FastAPI service at `service/slack_webhook/main.py`
   - Version: 0.7.0 (SLACK-ENDTOEND-DEV)
   - Feature flag: `SLACK_BOB_ENABLED`

3. **Routing Options**
   - **Option B** (preferred): Via `a2a_gateway` using A2A protocol
   - **Option A** (fallback): Direct to Agent Engine REST API

4. **Agent Engine**
   - Bob deployed to Vertex AI Agent Engine
   - Agent role: "bob"
   - Supports session continuity

---

## Prerequisites

### Required Access
- [ ] GCP project access (`bobs-brain` or your dev project)
- [ ] Slack workspace admin (to configure Slack app)
- [ ] GitHub repository access (for env var secrets)
- [ ] Cloud Run deployment permissions

### Required Tools
- [ ] `gcloud` CLI (authenticated)
- [ ] `gh` CLI (optional, for GitHub Actions)
- [ ] Python 3.12+ (for smoke tests)
- [ ] `make` (for convenience targets)

---

## Step-by-Step Enable Guide

### Step 1: Set Environment Variables

#### Option A: Local Development (.env file)

```bash
# Copy template
cp .env.example .env

# Edit .env and set:
SLACK_BOB_ENABLED=true
SLACK_BOT_TOKEN=xoxb-your-bot-token-here
SLACK_SIGNING_SECRET=your-signing-secret-here
A2A_GATEWAY_URL=https://a2a-gateway-xxx.run.app  # Optional but recommended

# Also ensure Agent Engine vars are set (for Option A fallback):
PROJECT_ID=bobs-brain
LOCATION=us-central1
AGENT_ENGINE_ID=your-agent-engine-id
```

**Where to find Slack credentials:**
1. Go to https://api.slack.com/apps
2. Select "bobs_brain" app (`A099YKLCM1N`)
3. **Bot Token**: OAuth & Permissions → Bot User OAuth Token (starts with `xoxb-`)
4. **Signing Secret**: Basic Information → App Credentials → Signing Secret

#### Option B: Cloud Run Deployment (GitHub Secrets)

```bash
# Set GitHub secrets (one-time setup):
gh secret set SLACK_BOT_TOKEN --body "xoxb-your-token"
gh secret set SLACK_SIGNING_SECRET --body "your-secret"
gh secret set SLACK_BOB_ENABLED --body "true"
gh secret set A2A_GATEWAY_URL --body "https://a2a-gateway-xxx.run.app"

# Verify secrets are set:
gh secret list
```

### Step 2: Deploy or Run Locally

#### Local Development Server

```bash
# Start the Slack webhook service
cd service/slack_webhook
uvicorn main:app --reload --port 8080

# In another terminal, run smoke test:
make slack-dev-smoke
```

**Note:** For local development, you'll need to expose port 8080 to the internet for Slack webhooks (use ngrok or similar).

#### Cloud Run Deployment

```bash
# ✅ CORRECT: Via GitHub Actions (Terraform-based deployment)
gh workflow run deploy-slack-gateway-dev.yml

# ❌ DEPRECATED - DO NOT USE (R4 Violation)
# Manual deployments violate Hard Mode R4 (CI-only deployments)
# See 000-DR-STND-slack-gateway-deploy-pattern.md for correct approach

# gcloud run deploy slack-webhook \
#   --source service/slack_webhook \
#   --region us-central1 \
#   --set-env-vars="SLACK_BOB_ENABLED=true" \
#   --update-secrets="SLACK_BOT_TOKEN=SLACK_BOT_TOKEN:latest,SLACK_SIGNING_SECRET=SLACK_SIGNING_SECRET:latest" \
#   --allow-unauthenticated

# Get service URL (still valid for inspection)
gcloud run services describe slack-webhook \
  --region=us-central1 \
  --format='value(status.url)'
```

### Step 3: Configure Slack App Event Subscriptions

1. Go to https://api.slack.com/apps → bobs_brain
2. Navigate to **Event Subscriptions**
3. Set **Request URL** to:
   - Local: `https://your-ngrok-url.ngrok.io/slack/events`
   - Cloud Run: `https://slack-webhook-xxx.run.app/slack/events`
4. Under **Subscribe to bot events**, ensure:
   - `app_mention` is enabled
   - `message.im` is enabled (for DMs)
5. Click **Save Changes**

### Step 4: Validate Configuration

```bash
# Check health endpoint
make slack-dev-smoke-health

# Expected output:
# ✅ PASS - Health endpoint reachable
# ✅ PASS - Service: slack-webhook v0.7.0
# ✅ PASS - Slack bot enabled: True
# ✅ PASS - Config valid: True
# ✅ PASS - Routing: a2a_gateway  # or "direct_agent_engine"
```

### Step 5: Run Smoke Tests

```bash
# Test local service
make slack-dev-smoke

# Test with detailed output
make slack-dev-smoke-verbose

# Test Cloud Run deployment
make slack-dev-smoke-cloud
```

**Expected Results:**
- ✅ Health endpoint reachable
- ✅ URL verification challenge passes
- ✅ Synthetic event accepted
- ⚠️ Check Cloud Run logs for actual Bob response

### Step 6: Test in Real Slack

1. Open your Slack workspace (Intent Solutions Inc)
2. Go to any channel where bobs_brain is added
3. Mention Bob: `@bobs_brain Hello! This is a test.`
4. Wait 5-10 seconds for response
5. Bob should respond in the same thread

**Troubleshooting:**
- No response? Check Cloud Run logs: `make deploy-logs`
- Check health: `curl https://slack-webhook-xxx.run.app/health`
- Verify routing method in health response

---

## Monitoring & Logs

### Health Check

```bash
# Local
curl http://localhost:8080/health

# Cloud Run
curl $(gcloud run services describe slack-webhook \
  --region=us-central1 \
  --format='value(status.url)')/health
```

**Health Response:**
```json
{
  "status": "healthy",
  "service": "slack-webhook",
  "version": "0.7.0",
  "slack_bot_enabled": true,
  "config_valid": true,
  "missing_vars": [],
  "routing": "a2a_gateway",
  "a2a_gateway_url": "https://a2a-gateway-xxx.run.app"
}
```

### Cloud Run Logs

```bash
# View logs
gcloud run services logs read slack-webhook \
  --region=us-central1 \
  --limit=50

# Filter for errors
gcloud run services logs read slack-webhook \
  --region=us-central1 \
  --limit=100 | grep ERROR

# Follow logs in real-time
gcloud run services logs tail slack-webhook --region=us-central1
```

**Key Log Messages:**
- `Slack bot is ENABLED and configured (routing: a2a_gateway)` - Startup success
- `Routing to a2a_gateway (Option B - via a2a protocol)` - Request routing
- `A2A gateway response received` - Successful Agent Engine call

---

## Disabling Slack Integration

### Option 1: Feature Flag (Recommended)

```bash
# Update environment variable
gcloud run services update slack-webhook \
  --region=us-central1 \
  --set-env-vars="SLACK_BOB_ENABLED=false"

# Or update GitHub secret:
gh secret set SLACK_BOB_ENABLED --body "false"

# Redeploy via GitHub Actions
gh workflow run deploy-slack-webhook.yml
```

**Result:**
- Service continues running
- Health endpoint still works
- Slack events are ignored gracefully
- No errors or crashes

### Option 2: Remove Slack App Event Subscription

1. Go to https://api.slack.com/apps → bobs_brain
2. Navigate to **Event Subscriptions**
3. Toggle **Enable Events** to OFF
4. Click **Save Changes**

**Result:**
- Slack stops sending events
- Service still healthy but idle
- Can re-enable anytime

### Option 3: Delete Cloud Run Service (Nuclear)

```bash
# Delete the service entirely
gcloud run services delete slack-webhook --region=us-central1

# Verify deletion
gcloud run services list --region=us-central1
```

**Result:**
- Complete removal
- Must redeploy to restore
- Only use for permanent decommissioning

---

## Troubleshooting Guide

### Issue: Health check shows `config_valid: false`

**Symptoms:**
```json
{
  "config_valid": false,
  "missing_vars": ["SLACK_BOT_TOKEN", "SLACK_SIGNING_SECRET"]
}
```

**Fix:**
1. Set missing environment variables
2. Redeploy or restart service
3. Re-check health endpoint

### Issue: Health check shows `routing: misconfigured`

**Symptoms:**
```json
{
  "routing": "misconfigured"
}
```

**Fix:**
- Set either `A2A_GATEWAY_URL` (preferred)
- Or all of: `PROJECT_ID`, `LOCATION`, `AGENT_ENGINE_ID`

### Issue: Slack events timeout (no response)

**Symptoms:**
- Bob doesn't respond in Slack
- Cloud Run logs show `HTTP error during agent call: 504`

**Fix:**
1. Check Agent Engine deployment:
   ```bash
   make agent-engine-dev-smoke
   ```
2. Check a2a_gateway health:
   ```bash
   curl https://a2a-gateway-xxx.run.app/health
   ```
3. Increase Cloud Run timeout (currently 60s for A2A):
   ```bash
   gcloud run services update slack-webhook \
     --region=us-central1 \
     --timeout=300
   ```

### Issue: Slack signature verification fails

**Symptoms:**
- Cloud Run logs show `Invalid Slack signature`
- HTTP 401 errors

**Fix:**
1. Verify `SLACK_SIGNING_SECRET` matches Slack app
2. Check timestamp drift (> 5 minutes causes failures)
3. Ensure raw body is used for signature calculation

### Issue: Smoke test fails with "Service not running"

**Symptoms:**
```
❌ FAIL - Service connection
     Could not connect to http://localhost:8080
```

**Fix:**
1. Start local service:
   ```bash
   cd service/slack_webhook && uvicorn main:app --port 8080
   ```
2. Or test Cloud Run instead:
   ```bash
   make slack-dev-smoke-cloud
   ```

---

## Configuration Reference

### Environment Variables

| Variable | Required When | Default | Description |
|----------|---------------|---------|-------------|
| `SLACK_BOB_ENABLED` | Always | `false` | Master feature flag for Slack bot |
| `SLACK_BOT_TOKEN` | Enabled | None | Slack Bot OAuth token (xoxb-...) |
| `SLACK_SIGNING_SECRET` | Enabled | None | Slack app signing secret |
| `A2A_GATEWAY_URL` | Optional | None | A2A gateway URL (Option B routing) |
| `PROJECT_ID` | Fallback | None | GCP project ID (Option A routing) |
| `LOCATION` | Fallback | None | GCP region (Option A routing) |
| `AGENT_ENGINE_ID` | Fallback | None | Agent Engine ID (Option A routing) |

### Routing Decision Logic

```python
if A2A_GATEWAY_URL:
    # Option B: Route via a2a_gateway (preferred)
    POST {A2A_GATEWAY_URL}/a2a/run with A2AAgentCall payload
else:
    # Option A: Direct Agent Engine (fallback)
    POST {AGENT_ENGINE_URL} with query payload
```

### Feature Flag Behavior Matrix

| SLACK_BOB_ENABLED | Config Valid | Behavior |
|-------------------|--------------|----------|
| `false` | N/A | Service healthy, events ignored |
| `true` | `false` | Service degraded, events fail |
| `true` | `true` | Service healthy, events processed |

---

## Make Targets Reference

```bash
make slack-dev-smoke              # Run basic smoke test (localhost)
make slack-dev-smoke-verbose      # Run with detailed output
make slack-dev-smoke-health       # Health check only (quick)
make slack-dev-smoke-cloud        # Test Cloud Run deployment
```

---

## Security Considerations

### Secrets Management

1. **NEVER commit secrets to git**
   - `.env` is in `.gitignore`
   - Use GitHub Secrets for CI/CD
   - Use GCP Secret Manager for Cloud Run

2. **Rotate credentials regularly**
   - Regenerate Slack tokens quarterly
   - Update GitHub Secrets after rotation
   - Redeploy services with new secrets

3. **Signature verification**
   - Always enabled in production
   - Prevents replay attacks (5-minute window)
   - HMAC-SHA256 validation

### Network Security

1. **Cloud Run requires authentication**
   - Slack webhook endpoint is `--allow-unauthenticated`
   - Protected by signature verification
   - A2A gateway protected by default

2. **TLS everywhere**
   - Slack → Cloud Run: HTTPS (Slack requirement)
   - Cloud Run → Agent Engine: HTTPS (GCP default)

---

## Production Deployment Considerations

**WARNING:** This guide is for **DEV ONLY**. Before enabling in staging/prod:

1. **LIVE3 Safety Gates**
   - Ensure `SLACK_ENABLE_PROD=true` is explicitly set
   - Review LIVE3 staging/prod safety documentation
   - Test in staging first

2. **Environment Separation**
   - Use separate Slack apps for dev/staging/prod
   - Use separate Cloud Run services
   - Use separate Agent Engine deployments

3. **Monitoring & Alerting**
   - Set up Cloud Monitoring alerts for errors
   - Monitor response latency (<5s target)
   - Track Slack event processing success rate

4. **Rate Limiting**
   - Consider implementing rate limiting
   - Monitor Slack API usage
   - Implement circuit breakers for Agent Engine calls

---

## Related Documentation

- **Phase C Audit:** `6771-LS-SITR-phase-c-slack-integration-audit.md`
- **AE-DEV-WIREUP:** `6768-DR-GUIDE-agent-engine-dev-wiring-and-smoke-test.md`
- **Roadmap:** `6770-DR-ROADMAP-bobs-brain-you-are-here.md`
- **LIVE3 Rollout:** (search for LIVE3 docs if needed)

---

## Support & Contacts

- **Slack App ID:** `A099YKLCM1N`
- **Slack Bot ID:** `B099A7GK2AW`
- **Slack App Name:** `bobs_brain`
- **Workspace:** Intent Solutions Inc
- **Service Version:** 0.7.0 (SLACK-ENDTOEND-DEV)

---

## Changelog

| Date | Version | Changes |
|------|---------|---------|
| 2025-11-20 | 1.0 | Initial operator guide for SLACK-ENDTOEND-DEV |

---

**Last Updated:** 2025-11-20
**Phase:** SLACK-ENDTOEND-DEV (S4 - Complete)
**Next Action:** Follow enable guide above to start talking to Bob in Slack!
