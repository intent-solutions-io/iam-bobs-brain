# Agent Engine Dev Wiring & Smoke Test Guide (AE3)

**Phase:** AE-DEV-WIREUP / AE3
**Status:** Complete (dev-only)
**Date:** 2025-11-20
**Category:** DR - Documentation & Reference

## Overview

This guide documents the dev wiring for Vertex AI Agent Engine + A2A gateway completed in Phase AE-DEV-WIREUP. It covers:

- **AE1**: Agent Engine config module (centralized configuration)
- **AE2**: A2A gateway implementation (HTTP proxy with Agent Engine client)
- **AE3**: Dev smoke test + ARV check (validation and testing)

**Purpose:** Enable full Slack → Cloud Run → Agent Engine → Bob/IAM flow in dev.

**Scope:** DEV ONLY. Staging and prod require additional safety checks and feature flags (future phases).

---

## Architecture

### Flow Diagram

```
User/Agent
    ↓
Slack or Direct HTTP
    ↓
service/a2a_gateway/  (Cloud Run - FastAPI)
    ├── Reads: agents/config/agent_engine.py
    ├── Uses: agent_engine_client.py
    └── Calls: Vertex AI Agent Engine REST API
        ↓
    Agent Engine (Managed Runtime)
        ↓
    Bob / IAM agents (ADK-based)
        ↓
    Response
```

### Key Components

| Component | Location | Purpose |
|-----------|----------|---------|
| **Agent Engine Config** | `agents/config/agent_engine.py` | Single source of truth for Engine IDs, project, location |
| **Config Inventory** | `agents/config/inventory.py` | Registers all AGENT_ENGINE_*_ID_* env vars |
| **A2A Gateway** | `service/a2a_gateway/main.py` | FastAPI app exposing `/a2a/run` endpoint |
| **Agent Engine Client** | `service/a2a_gateway/agent_engine_client.py` | Helper for calling Agent Engine via REST API |
| **Dev Smoke Test** | `scripts/run_agent_engine_dev_smoke.py` | Validation script for end-to-end flow |
| **ARV Check** | `agents/arv/spec.py` | ARV gate for smoke test (optional) |

---

## 1. Agent Engine Configuration (AE1)

### Config Module: `agents/config/agent_engine.py`

**Single Source of Truth** for Agent Engine IDs, project, location, and SPIFFE IDs.

#### Key Functions

```python
# Get current environment (dev, staging, prod)
from agents.config.agent_engine import get_current_environment

env = get_current_environment()  # Returns "dev" | "staging" | "prod"
```

```python
# Build agent config for specific role + env
from agents.config.agent_engine import build_agent_config

config = build_agent_config(agent_role="bob", env="dev")
# Returns AgentEngineConfig with:
#   - reasoning_engine_id
#   - project_id
#   - location
#   - spiffe_id
#   - notes
```

```python
# Construct resource paths
from agents.config.agent_engine import (
    make_reasoning_engine_path,
    get_reasoning_engine_url
)

# Full resource name for API calls
path = make_reasoning_engine_path(engine_id="12345")
# → "projects/my-project/locations/us-central1/reasoningEngines/12345"

# HTTPS URL for REST API
url = get_reasoning_engine_url(engine_id="12345")
# → "https://us-central1-aiplatform.googleapis.com/v1/.../reasoningEngines/12345:query"
```

#### Environment Variables

Follow pattern: `AGENT_ENGINE_{AGENT}_{ENV}`

**Example:**
```bash
# Bob
export AGENT_ENGINE_BOB_ID_DEV="bob-engine-dev-123"
export AGENT_ENGINE_BOB_ID_STAGING="bob-engine-staging-456"
export AGENT_ENGINE_BOB_ID_PROD="5828234061910376448"  # Canonical prod

# Foreman
export AGENT_ENGINE_FOREMAN_ID_DEV="foreman-engine-dev-789"

# IAM Specialists
export AGENT_ENGINE_IAM_ADK_ID_DEV="iam-adk-dev-321"
export AGENT_ENGINE_IAM_ISSUE_ID_DEV="iam-issue-dev-654"
```

**Alternative Naming (Aliases):**
```bash
export GCP_PROJECT_ID="my-project"      # or PROJECT_ID
export VERTEX_LOCATION="us-central1"    # or LOCATION
```

#### Config Validation

```bash
# Validate config for current environment
python3 scripts/check_config_all.py

# Or via Makefile
make check-config
```

---

## 2. A2A Gateway (AE2)

### Gateway Service: `service/a2a_gateway/`

FastAPI app that proxies A2A protocol calls to Agent Engine.

#### Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/.well-known/agent.json` | GET | AgentCard for A2A discovery |
| `/query` | POST | Direct query to Agent Engine (legacy) |
| `/a2a/run` | POST | **A2A protocol endpoint** (AE2) |
| `/health` | GET | Health check |
| `/` | GET | Service info |

#### A2A Protocol: `/a2a/run`

**Request:**
```json
{
  "agent_role": "bob",
  "prompt": "What is ADK?",
  "session_id": "optional-session-id",
  "correlation_id": "optional-correlation-id",
  "caller_spiffe_id": "spiffe://intent.solutions/agent/caller/...",
  "context": { "optional": "data" },
  "env": "dev"
}
```

**Response:**
```json
{
  "response": "ADK stands for Agent Development Kit...",
  "session_id": "session-abc123",
  "correlation_id": "corr-xyz789",
  "target_spiffe_id": "spiffe://intent.solutions/agent/bobs-brain/dev/...",
  "metadata": {
    "agent_role": "bob",
    "env": "dev",
    "engine_id": "bob-engine-dev-123"
  },
  "error": null
}
```

#### Agent Engine Client: `agent_engine_client.py`

Helper module for calling Agent Engine from the gateway.

**Key Function:**
```python
from agent_engine_client import call_agent_engine

result = await call_agent_engine(
    agent_role="bob",
    prompt="Test query",
    session_id="s1",
    correlation_id="c1",
    context={"repo": "bobs-brain"},
    env="dev",
)

# Returns AgentEngineResponse:
#   - response: str
#   - session_id: Optional[str]
#   - metadata: Dict
#   - error: Optional[str]
```

**What it does:**
1. Reads agent config via `build_agent_config(agent_role, env)`
2. Gets OAuth token via ADC (`google.auth.default()`)
3. Builds request payload with query, session_id, context
4. Adds headers: Authorization, X-Correlation-ID, X-SPIFFE-ID
5. Calls Agent Engine REST API via httpx
6. Handles errors: HTTP errors, timeouts, auth failures
7. Returns parsed response with metadata

---

## 3. Dev Smoke Test (AE3)

### Smoke Test Script: `scripts/run_agent_engine_dev_smoke.py`

Validates end-to-end dev wiring.

#### Usage

```bash
# Basic test (defaults to Bob)
python3 scripts/run_agent_engine_dev_smoke.py

# Or via Makefile
make agent-engine-dev-smoke

# Test specific agent
python3 scripts/run_agent_engine_dev_smoke.py --agent foreman

# Custom prompt
python3 scripts/run_agent_engine_dev_smoke.py --prompt "Analyze this code"

# Verbose output
python3 scripts/run_agent_engine_dev_smoke.py --verbose
make agent-engine-dev-smoke-verbose
```

#### What it Tests

1. **Environment detection** - Confirms `DEPLOYMENT_ENV=dev`
2. **Agent config** - Verifies `AGENT_ENGINE_{AGENT}_ID_DEV` is set
3. **Authentication** - Gets OAuth token via ADC
4. **Agent Engine call** - Sends synthetic request via `call_agent_engine()`
5. **Response parsing** - Validates response structure and content

#### Exit Codes

| Code | Meaning | Action |
|------|---------|--------|
| 0 | Test passed | ✅ Dev wiring works |
| 1 | Test failed | ❌ Fix config, auth, or Agent Engine |
| 2 | Agent not configured | ℹ️ Non-blocking (expected if not set up) |

#### Example Output

```
================================================================================
AGENT ENGINE DEV SMOKE TEST (AE3)
================================================================================

Environment: dev
Agent Role: bob

Checking Agent Engine configuration...
✅ Agent configured:
   Engine ID: bob-engine-dev-123

Test Prompt: Hello! This is a dev smoke test. Please respond briefly.

Calling Agent Engine via agent_engine_client...
✅ Agent Engine response received:

Response:
--------------------------------------------------------------------------------
Hello! I'm Bob, your AI assistant. This smoke test confirms our dev wiring
is working correctly. The Agent Engine received your request and I'm responding
successfully.
--------------------------------------------------------------------------------

Session ID: session-abc-123

================================================================================
✅ SMOKE TEST PASSED
================================================================================

Summary:
  - Agent: bob
  - Environment: dev
  - Engine ID: bob-engine-dev-123
  - Response Length: 147 chars
  - Session ID: session-abc-123

The dev wiring is working correctly!
You can now:
  1. Test other agents (--agent foreman, --agent iam-adk)
  2. Deploy to staging when ready
```

### ARV Check

Smoke test is registered as an optional ARV check:

```python
# In agents/arv/spec.py
ArvCheck(
    id="agent-engine-dev-smoke",
    description="Agent Engine dev smoke test",
    category="engine",
    required=False,  # Optional - doesn't block
    command="python3 scripts/run_agent_engine_dev_smoke.py",
    envs=["dev"],
)
```

Run via ARV:
```bash
make arv-department
# Includes agent-engine-dev-smoke (if configured)
```

---

## 4. Local Development Setup

### Prerequisites

1. **GCP Project** with Vertex AI enabled
2. **Agent deployed** to Agent Engine (Bob, foreman, or IAM agent)
3. **Application Default Credentials**:
   ```bash
   gcloud auth application-default login
   ```

### Environment Configuration

Create `.env` file:
```bash
# Copy template
cp .env.example .env

# Edit .env with your values
DEPLOYMENT_ENV=dev
PROJECT_ID=your-gcp-project
LOCATION=us-central1

# Agent Engine IDs
AGENT_ENGINE_BOB_ID_DEV=your-bob-engine-id
AGENT_ENGINE_FOREMAN_ID_DEV=your-foreman-engine-id

# SPIFFE ID
AGENT_SPIFFE_ID=spiffe://intent.solutions/agent/bobs-brain/dev/us-central1/0.9.0
```

### Validation

```bash
# Validate config
make check-config

# Test Agent Engine wiring
make agent-engine-dev-smoke

# Run ARV checks
make arv-department
```

---

## 5. Open Questions / TODOs

### Before Staging/Prod Rollout

- [ ] **Feature flags for staging/prod**
  - Add `ENGINE_MODE_*_STAGING` / `ENGINE_MODE_*_PROD` flags
  - Implement gradual rollout controls

- [ ] **Multi-agent routing**
  - Test foreman → iam-adk → iam-issue flows
  - Validate A2A protocol across agent boundaries

- [ ] **Error handling**
  - Define retry strategies for Agent Engine calls
  - Implement circuit breaker for repeated failures

- [ ] **Monitoring & observability**
  - Set up Cloud Logging for gateway requests
  - Add trace correlation between gateway and Agent Engine
  - Create dashboards for Agent Engine latency

- [ ] **Security hardening**
  - Verify SPIFFE ID propagation in all calls
  - Audit IAM permissions for Agent Engine access
  - Review ADC scopes and service accounts

- [ ] **Load testing**
  - Test gateway under concurrent requests
  - Validate Agent Engine scaling behavior
  - Measure p50/p95/p99 latencies

- [ ] **Staging wiring**
  - Create staging Agent Engine deployments
  - Set up staging gateway (Cloud Run)
  - Test with staging credentials

- [ ] **Production readiness**
  - Complete staging validation
  - Document rollback procedures
  - Create production runbook
  - Set up alerts and on-call rotation

---

## 6. Troubleshooting

### "Agent not configured"

**Symptom:**
```
ℹ️  Agent 'bob' is NOT configured for dev
```

**Fix:**
```bash
# Set Agent Engine ID for dev
export AGENT_ENGINE_BOB_ID_DEV=your-engine-id

# Or add to .env
echo "AGENT_ENGINE_BOB_ID_DEV=your-engine-id" >> .env
```

### "Authentication failed"

**Symptom:**
```
❌ Agent Engine call failed:
   Error: Authentication failed
```

**Fix:**
```bash
# Ensure ADC is set up
gcloud auth application-default login

# Verify credentials
gcloud auth application-default print-access-token
```

### "HTTP 404: reasoningEngine not found"

**Symptom:**
```
❌ Agent Engine HTTP error: 404 - reasoningEngine not found
```

**Fix:**
```bash
# Verify Agent Engine is deployed
gcloud ai reasoning-engines list --region=us-central1

# Check Engine ID matches
echo $AGENT_ENGINE_BOB_ID_DEV
```

### "Timeout after 30s"

**Symptom:**
```
❌ Agent Engine timeout after 30.0s
```

**Fix:**
1. Check Agent Engine status in Cloud Console
2. Increase timeout in `call_agent_engine()` if needed
3. Verify Agent Engine has sufficient resources

---

## 7. Related Documentation

| Document | Purpose |
|----------|---------|
| `agents/config/agent_engine.py` | Config module implementation |
| `agents/config/inventory.py` | Environment variable registry |
| `service/a2a_gateway/main.py` | Gateway implementation |
| `service/a2a_gateway/agent_engine_client.py` | Agent Engine client |
| `scripts/run_agent_engine_dev_smoke.py` | Smoke test script |
| `agents/arv/spec.py` | ARV checks definition |
| `tests/unit/test_agent_engine_client.py` | Client unit tests |
| `CLAUDE.md` | Project overview and rules |

---

## 8. Summary

**AE-DEV-WIREUP Phase Complete**

✅ **AE1**: Agent Engine config module
  - Centralized configuration in `agents/config/agent_engine.py`
  - 21 environment variables registered in inventory
  - Config validator updated

✅ **AE2**: A2A gateway implementation
  - FastAPI gateway with `/a2a/run` endpoint
  - Agent Engine client with ADC auth
  - 11 unit tests (all passing)

✅ **AE3**: Dev smoke test + ARV
  - Smoke test script with Makefile targets
  - ARV check registered (optional)
  - Documentation guide (this file)

**Next:** Staging wiring (feature flags, staging deployments, production rollout)

**Dev wiring validated and ready for use.**

---

_Last Updated: 2025-11-20_
_Phase: AE-DEV-WIREUP / AE3 Complete_
_Status: Dev-only (staging/prod TBD)_
