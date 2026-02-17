# Cloud Run Gateways and Agent Engine Routing

**Document ID:** 102-AT-ARCH-cloud-run-gateways-and-agent-engine-routing
**Created:** 2025-11-20
**Phase:** AE2 (Cloud Run Gateway Design)
**Status:** Design (Stubbed Implementation)

---

## Purpose

This document defines the **Cloud Run gateway architecture** for Bob's Brain, detailing how external traffic (Slack) and internal agent-to-agent (A2A) calls route through gateway services to Vertex AI Agent Engine.

This is the detailed gateway design companion to the Agent Engine topology document (101).

## Architecture Overview

### Gateway Layer

Two Cloud Run services act as gateways between external/internal traffic and Agent Engine:

```
External Traffic (Slack)
    ↓
slack_webhook (Cloud Run)
    ↓
    ├── Option A (current): Direct to Agent Engine
    │   └→ Bob's Agent Engine
    │
    └── Option B (Phase AE3): Via A2A Gateway
        └→ a2a_gateway (Cloud Run)
            └→ Agent Engine (Bob, foreman, iam-*)
```

### Why Two Gateways?

**Separation of Concerns:**
- `slack_webhook`: Slack-specific logic (signature validation, formatting, event parsing)
- `a2a_gateway`: Protocol-agnostic A2A routing and Agent Engine proxy

**Benefits:**
1. Other clients (API, CLI, web UI) can use `a2a_gateway` directly without Slack logic
2. Slack-specific changes don't affect A2A protocol
3. Easier testing (mock A2A gateway for Slack tests)
4. Clean agent-to-agent communication protocol
5. Future-proof for multi-agent orchestration

**Alternative Considered:** Single combined gateway
- **Rejected:** Mixes concerns, harder to test, less reusable

---

## Gateway 1: slack_webhook

### Purpose

Handle Slack webhook events and proxy to appropriate backend (Agent Engine or A2A Gateway).

### Location

- **Code:** `service/slack_webhook/main.py`
- **Deployment:** Cloud Run service in `us-central1`
- **URL Pattern:** `https://slack-webhook-SERVICE_HASH-uc.a.run.app`

### Responsibilities

1. **Slack Event Handling:**
   - Receive webhook events from Slack
   - Validate Slack signatures (HMAC-SHA256)
   - Handle URL verification challenges
   - Parse `app_mention`, `message.im`, and `message.channels` events

2. **Request Routing:**
   - **Option A (current, default):** Direct proxy to Agent Engine
   - **Option B (Phase AE3):** Route SWE pipeline commands through A2A Gateway

3. **Response Formatting:**
   - Format agent responses for Slack
   - Post replies to channels/threads
   - Handle Slack-specific formatting (mentions, links, code blocks)

4. **Error Handling:**
   - Return 200 to Slack on all paths (prevent retries)
   - Log errors but don't expose internals to Slack
   - Handle bot loops (ignore bot messages)

### Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/slack/events` | POST | Receive Slack events |
| `/health` | GET | Health check |
| `/` | GET | Service metadata |

### Configuration (Environment Variables)

```bash
# Required
SLACK_BOT_TOKEN=xoxb-...              # Slack bot OAuth token
SLACK_SIGNING_SECRET=...              # Slack app signing secret
PROJECT_ID=your-gcp-project
LOCATION=us-central1
AGENT_ENGINE_ID=5828234061910376448   # Current Bob

# Phase AE2: New routing configuration
SLACK_SWE_PIPELINE_MODE=local         # local (default) | engine (Phase AE3)
A2A_GATEWAY_URL=https://a2a-gateway-SERVICE_HASH-uc.a.run.app

# Other
PORT=8080                             # Service port
DEPLOYMENT_ENV=prod                   # Environment detection
```

### Routing Logic

#### Option A: Direct to Agent Engine (Current, Default)

```
Slack Event
    ↓
slack_webhook.query_agent_engine()
    ↓
POST {AGENT_ENGINE_URL}/query
Body: {"query": "...", "session_id": "user_channel"}
    ↓
Agent Engine (Bob)
    ↓
Response to Slack
```

#### Option B: Via A2A Gateway (Phase AE3, Commented)

```
Slack Event
    ↓
slack_webhook detects SLACK_SWE_PIPELINE_MODE=engine
    ↓
POST {A2A_GATEWAY_URL}/a2a/run
Body: {
  "agent_role": "foreman",
  "prompt": "...",
  "session_id": "user_channel",
  "caller_spiffe_id": "spiffe://intent.solutions/slack/webhook",
  "env": "prod"
}
    ↓
a2a_gateway routes to Agent Engine
    ↓
Foreman (iam-senior-adk-devops-lead)
    ↓
Response to Slack
```

### Request Flow Example

**Slack → slack_webhook → Agent Engine:**

1. User mentions @Bob in Slack: `@Bob analyze this repo`
2. Slack sends webhook to slack_webhook `/slack/events`
3. slack_webhook:
   - Validates Slack signature
   - Extracts text, removes mention
   - Calls `query_agent_engine("analyze this repo", "user_channel")`
4. query_agent_engine:
   - Checks `SLACK_SWE_PIPELINE_MODE` (currently "local")
   - POSTs to Agent Engine REST API
5. Agent Engine returns response
6. slack_webhook posts response to Slack thread

### Security

- **Slack Signature Validation:** HMAC-SHA256 with `SLACK_SIGNING_SECRET`
- **Timestamp Check:** Reject requests older than 5 minutes
- **Bot Loop Prevention:** Ignore messages from bot_id
- **Retry Handling:** Ignore x-slack-retry-num headers

### Scaling

- **Auto-scaling:** Based on Slack event volume
- **Min Instances:** 1 (production), 0 (dev/staging)
- **Max Instances:** 10
- **Concurrency:** 80 requests per instance
- **Timeout:** 60s per request

---

## Gateway 2: a2a_gateway

### Purpose

Internal Agent-to-Agent (A2A) protocol gateway for routing agent calls to Vertex AI Agent Engine.

### Location

- **Code:** `service/a2a_gateway/main.py`
- **Deployment:** Cloud Run service in `us-central1`
- **URL Pattern:** `https://a2a-gateway-SERVICE_HASH-uc.a.run.app`

### Responsibilities

1. **A2A Protocol Implementation:**
   - Accept standardized `A2AAgentCall` requests
   - Return standardized `A2AAgentResult` responses
   - Maintain protocol contracts for agent-to-agent communication

2. **Agent Engine Routing:**
   - Resolve target agent's reasoning engine ID
   - Build Agent Engine REST API requests
   - Proxy calls to appropriate Agent Engine instances
   - Handle multi-environment routing (dev/staging/prod)

3. **Identity and Tracing:**
   - Propagate SPIFFE IDs (caller and target)
   - Maintain correlation IDs (pipeline_run_id)
   - Log all A2A calls for observability

4. **AgentCard Publishing:**
   - Serve AgentCard at `/.well-known/agent.json`
   - Enable agent discovery via A2A protocol

### Endpoints

| Endpoint | Method | Purpose | Phase |
|----------|--------|---------|-------|
| `/.well-known/agent.json` | GET | AgentCard for discovery | Active |
| `/query` | POST | Legacy direct query endpoint | Active |
| `/a2a/run` | POST | A2A protocol endpoint | AE2 (Stubbed) |
| `/health` | GET | Health check | Active |
| `/` | GET | Service metadata | Active |

### A2A Protocol Data Models

#### A2AAgentCall (Request)

```python
{
  "agent_role": str,              # Target agent (bob, foreman, iam-adk, etc.)
  "prompt": str,                  # Task description
  "context": dict | None,         # Optional additional context
  "correlation_id": str | None,   # Optional tracing ID (auto-generated if missing)
  "caller_spiffe_id": str | None, # SPIFFE ID of calling agent
  "session_id": str | None,       # Optional session for continuity
  "env": str | None               # Target environment (defaults to current)
}
```

**Example:**
```json
{
  "agent_role": "iam-adk",
  "prompt": "Audit this repo for ADK compliance",
  "correlation_id": "12345-67890-pipeline-run",
  "caller_spiffe_id": "spiffe://intent.solutions/agent/bobs-brain-foreman/prod/us-central1/0.9.0",
  "env": "prod"
}
```

#### A2AAgentResult (Response)

```python
{
  "response": str,                  # Agent's response text
  "session_id": str | None,         # Session ID for continuity
  "metadata": dict | None,          # Additional metadata (tokens, latency, etc.)
  "error": str | None,              # Error message if failed
  "correlation_id": str | None,     # Correlation ID from request
  "target_spiffe_id": str | None    # SPIFFE ID of target agent
}
```

**Example (Stubbed Response in Phase AE2):**
```json
{
  "response": "[STUB - Phase AE2] A2A call to iam-adk\n...",
  "session_id": "abc-123-def-456",
  "correlation_id": "12345-67890-pipeline-run",
  "target_spiffe_id": "spiffe://intent.solutions/agent/bobs-brain-iam-adk/stub/us-central1/0.9.0",
  "metadata": {
    "stub": true,
    "phase": "AE2",
    "agent_role": "iam-adk"
  }
}
```

### POST /a2a/run Implementation

**Phase AE2 (Current):** Stubbed implementation
- Accepts `A2AAgentCall` payload
- Validates request shape
- Returns mock `A2AAgentResult`
- Logs correlation IDs and caller identity
- No real Agent Engine calls

**Phase AE3 (Future):** Real implementation
- Check feature flags for agent_role + env
- Use `agents.utils.a2a_adapter.call_agent_engine()` to call Agent Engine
- Return real Agent Engine responses
- Enable gradually via feature flags

### Request Flow Example

**foreman → a2a_gateway → iam-adk (Phase AE3):**

1. Foreman agent needs ADK analysis
2. Foreman builds A2AAgentCall:
   ```python
   {
     "agent_role": "iam-adk",
     "prompt": "Audit this repo",
     "correlation_id": "pipeline-12345",
     "caller_spiffe_id": "spiffe://.../foreman/prod/..."
   }
   ```
3. Foreman POSTs to `{A2A_GATEWAY_URL}/a2a/run`
4. a2a_gateway (Phase AE3):
   - Checks feature flag `LIVE_RAG_IAM_ADK_ENABLED`
   - Resolves iam-adk reasoning engine ID from config
   - Calls Agent Engine REST API
   - Returns iam-adk's response
5. Foreman receives A2AAgentResult

### Security

- **Service Account Auth:** Each Cloud Run service uses dedicated SA
- **IAM Permissions:** `aiplatform.reasoningEngines.query`
- **SPIFFE ID Validation:** Log and trace all caller identities
- **VPC Integration:** Services in same VPC as Agent Engine
- **No Secrets in Payloads:** Secrets injected via Secret Manager

### Scaling

- **Auto-scaling:** Based on A2A request volume
- **Min Instances:** 1 (production), 0 (dev/staging)
- **Max Instances:** 20 (higher than slack_webhook for burst capacity)
- **Concurrency:** 100 requests per instance
- **Timeout:** 90s per request (longer for multi-agent orchestration)

---

## Routing Flows

### Flow 1: Slack → Bob (Current Production)

```
┌────────┐
│ Slack  │
│ User   │
└───┬────┘
    │ @Bob analyze repo
    ↓
┌──────────────────┐
│ slack_webhook    │
│ (Cloud Run)      │
│                  │
│ Option A:        │
│ Direct to Engine │
└────────┬─────────┘
         │ POST /query
         │ {"query": "...", "session_id": "..."}
         ↓
┌──────────────────────────────┐
│ Agent Engine                 │
│ Bob (…6448)                  │
│ us-central1                  │
└──────────┬───────────────────┘
           │ Response
           ↓
     ┌─────────────┐
     │   Slack     │
     │  Response   │
     └─────────────┘
```

### Flow 2: Slack → Foreman → iam-* (Phase AE3, via A2A)

```
┌────────┐
│ Slack  │
│ User   │
└───┬────┘
    │ @Bob audit this repo
    ↓
┌──────────────────┐
│ slack_webhook    │
│ (Cloud Run)      │
│                  │
│ Option B:        │
│ Route via A2A    │
└────────┬─────────┘
         │ POST /a2a/run
         │ A2AAgentCall(agent_role="foreman", ...)
         ↓
┌──────────────────┐
│ a2a_gateway      │
│ (Cloud Run)      │
│                  │
│ Routes to Engine │
└────────┬─────────┘
         │ POST {reasoning_engine_id}:query
         ↓
┌───────────────────────────────┐
│ Agent Engine                  │
│ Foreman                       │
│ (iam-senior-adk-devops-lead)  │
└────────┬──────────────────────┘
         │ Orchestrates pipeline
         ↓
┌──────────────────┐
│ a2a_gateway      │ ← Foreman calls iam-* agents
│ (Cloud Run)      │
│                  │
│ Routes to Engine │
└────────┬─────────┘
         │ POST {iam_adk_engine_id}:query
         ↓
┌───────────────────────────────┐
│ Agent Engine                  │
│ iam-adk                       │
│ (ADK specialist)              │
└────────┬──────────────────────┘
         │ Analysis complete
         ↓
     [Response flows back through foreman to Slack]
```

### Flow 3: Agent-to-Agent (Phase AE3)

```
┌──────────────────────────────┐
│ Agent Engine                 │
│ Foreman                      │
│ (running in Agent Engine)    │
└──────────┬───────────────────┘
           │ Needs iam-adk analysis
           │ (via agents.utils.a2a_adapter)
           ↓
┌──────────────────┐
│ a2a_gateway      │
│ (Cloud Run)      │
│                  │
│ POST /a2a/run    │
│ A2AAgentCall     │
└────────┬─────────┘
         │ Resolves iam-adk engine ID
         │ POST {iam_adk_engine_id}:query
         ↓
┌───────────────────────────────┐
│ Agent Engine                  │
│ iam-adk                       │
│ (ADK specialist)              │
└────────┬──────────────────────┘
           │ A2AAgentResult
           ↓
        Foreman receives result
```

---

## Configuration Management

### Environment Variables

Both gateways use environment variables for configuration (no secrets in code):

**slack_webhook:**
```bash
# Slack credentials (from Secret Manager)
SLACK_BOT_TOKEN=xoxb-...
SLACK_SIGNING_SECRET=...

# Agent Engine
PROJECT_ID=205354194989
LOCATION=us-central1
AGENT_ENGINE_ID=5828234061910376448

# Phase AE2: Routing
SLACK_SWE_PIPELINE_MODE=local         # local | engine
A2A_GATEWAY_URL=https://...

# Deployment
DEPLOYMENT_ENV=prod
PORT=8080
```

**a2a_gateway:**
```bash
# Agent Engine
PROJECT_ID=205354194989
LOCATION=us-central1
AGENT_ENGINE_ID=5828234061910376448
AGENT_ENGINE_URL=https://us-central1-aiplatform.googleapis.com/v1/...

# AgentCard
APP_NAME=bobs-brain
APP_VERSION=0.6.0
PUBLIC_URL=https://a2a-gateway-...
AGENT_SPIFFE_ID=spiffe://intent.solutions/agent/bobs-brain/prod/...

# Deployment
PORT=8080
```

### Feature Flags (Phase AE3)

Feature flags (from `agents/config/features.py`) control when real Agent Engine calls are enabled:

- `LIVE_RAG_BOB_ENABLED`: Enable live RAG for Bob
- `ENGINE_MODE_FOREMAN_TO_IAM_ADK`: Enable foreman → iam-adk via Engine
- `ENGINE_MODE_FOREMAN_TO_IAM_ISSUE`: Enable foreman → iam-issue via Engine
- `SLACK_SWE_PIPELINE_MODE_ENABLED`: Enable Option B routing

See Phase AE3 rollout plan (000-DR-STND-live-rag-and-agent-engine-rollout-plan) for feature flag strategy.

---

## Phase Status

### Phase AE2 (Current) - Design & Stubs

**Completed:**
- ✅ A2AAgentCall and A2AAgentResult data models defined
- ✅ POST /a2a/run endpoint implemented (stubbed)
- ✅ SLACK_SWE_PIPELINE_MODE config added
- ✅ Option B routing path commented in slack_webhook
- ✅ Correlation ID and SPIFFE ID support in place
- ✅ Documentation complete (this document)

**Stubbed (not yet enabled):**
- 🔶 POST /a2a/run returns mock responses
- 🔶 Option B routing commented out in slack_webhook
- 🔶 No real Agent Engine calls via a2a_adapter
- 🔶 Feature flags not yet created

### Phase AE3 (Future) - Real Implementation

**Planned:**
- ⏳ Create `agents/config/features.py` with all feature flags
- ⏳ Implement real Agent Engine calls in a2a_gateway
- ⏳ Enable Option B routing in slack_webhook behind flag
- ⏳ Add ARV check for engine flags (`check_arv_engine_flags.py`)
- ⏳ Gradual rollout per environment (dev → staging → prod)
- ⏳ Create rollout plan doc (000-DR-STND-live-rag-and-agent-engine-rollout-plan)

---

## Observability

### Logging

Both gateways use structured logging with correlation IDs:

**slack_webhook logs:**
```json
{
  "timestamp": "2025-11-20T10:00:00Z",
  "level": "INFO",
  "event": "Slack event received",
  "user": "U123456",
  "channel": "C789012",
  "text_length": 42,
  "routing_mode": "local"
}
```

**a2a_gateway logs:**
```json
{
  "timestamp": "2025-11-20T10:00:01Z",
  "level": "INFO",
  "event": "A2A call received (STUB)",
  "agent_role": "iam-adk",
  "caller_spiffe_id": "spiffe://.../foreman/...",
  "correlation_id": "12345-67890",
  "env": "prod"
}
```

### Metrics

Key metrics to monitor:

**slack_webhook:**
- Slack events received per minute
- Routing mode distribution (local vs engine)
- Response latency (p50, p95, p99)
- Error rate
- Slack signature validation failures

**a2a_gateway:**
- A2A calls per minute
- Agent role distribution
- Stub vs real call ratio (Phase AE3)
- Agent Engine latency
- Error rate by agent role

### Tracing

Correlation IDs flow through entire request path:

```
Slack request
  ↓ [generates pipeline_run_id]
slack_webhook
  ↓ [includes correlation_id in A2AAgentCall]
a2a_gateway
  ↓ [includes correlation_id in Agent Engine call]
Agent Engine (foreman)
  ↓ [uses pipeline_run_id in all logging]
Agent Engine (iam-adk)
  ↓ [returns results with correlation_id]
Response to Slack
```

---

## Deployment

### Terraform Resources

Both gateways deployed via Terraform:

```hcl
# service/a2a_gateway/terraform/main.tf
resource "google_cloud_run_service" "a2a_gateway" {
  name     = "a2a-gateway"
  location = "us-central1"

  template {
    spec {
      containers {
        image = "gcr.io/${var.project_id}/a2a-gateway:${var.version}"

        env {
          name  = "PROJECT_ID"
          value = var.project_id
        }
        # ... other env vars
      }
    }
  }
}

# Similar for slack_webhook
```

### CI/CD

GitHub Actions workflows deploy gateways:

**.github/workflows/deploy-a2a-gateway.yml:**
- Triggered on push to `main` affecting `service/a2a_gateway/`
- Builds Docker image
- Pushes to GCR
- Deploys to Cloud Run
- Runs smoke tests

**.github/workflows/deploy-slack-webhook.yml:**
- Similar for slack_webhook
- Includes Slack signature validation tests

### Blue/Green Deployment

For production updates:

1. Deploy new revision with traffic=0
2. Run smoke tests against new revision
3. Gradually shift traffic: 5% → 25% → 50% → 100%
4. Monitor error rates and latency
5. Rollback if needed (instant)

---

## Testing

### Unit Tests

**service/a2a_gateway/test_main.py:**
- Test A2AAgentCall/Result serialization
- Test POST /a2a/run stub responses
- Test AgentCard generation
- Test error handling

**service/slack_webhook/test_main.py:**
- Test Slack signature validation
- Test event parsing
- Test Option A routing (current)
- Test Option B routing (commented, will enable in Phase AE3)

### Integration Tests

**tests/integration/test_gateways.py:**
- Deploy gateways to dev environment
- Send real Slack events
- Verify responses
- Test A2A protocol end-to-end (Phase AE3)

### Load Tests

**tests/load/locustfile.py:**
- Simulate 100-1000 concurrent Slack events
- Measure latency under load
- Verify auto-scaling behavior
- Test gateway failover

---

## Security Considerations

### Slack Webhook Security

1. **Signature Validation:** HMAC-SHA256 with signing secret
2. **Timestamp Validation:** Reject requests older than 5 minutes
3. **Bot Loop Prevention:** Ignore messages from bot_id
4. **Secret Management:** Token and secret from Secret Manager
5. **No Direct DB Access:** All data via Agent Engine API

### A2A Gateway Security

1. **Service Account Auth:** Dedicated SA per gateway
2. **IAM Least Privilege:** Only `reasoningEngines.query` permission
3. **VPC Integration:** Private communication with Agent Engine
4. **SPIFFE ID Validation:** Log and trace all caller identities
5. **No Credentials in Code:** All secrets via Secret Manager

### Network Security

1. **Cloud Armor:** WAF rules for DDoS protection
2. **TLS:** HTTPS only, TLS 1.2+ enforced
3. **VPC Peering:** Agent Engine in VPC, gateways access via VPC connector
4. **Egress Control:** Restrict outbound traffic to GCP APIs only

---

## Troubleshooting

### Common Issues

**Issue:** Slack webhook returns 401 "Invalid signature"
- **Cause:** Wrong `SLACK_SIGNING_SECRET` or timestamp drift
- **Fix:** Verify secret, check system time sync

**Issue:** A2A gateway returns 503 "Agent Engine unavailable"
- **Cause:** Agent Engine not deployed or wrong ID
- **Fix:** Verify reasoning engine ID in config, check Agent Engine status

**Issue:** Option B routing not working (Phase AE3)
- **Cause:** `SLACK_SWE_PIPELINE_MODE` not set to "engine"
- **Fix:** Set config, check feature flags, verify A2A_GATEWAY_URL

**Issue:** High latency on /a2a/run
- **Cause:** Agent Engine cold start or complex task
- **Fix:** Increase timeout, check Agent Engine logs, consider warmup

---

## Related Documents

- **101-AT-ARCH-agent-engine-topology-and-envs.md** - Agent Engine deployment topology (Phase AE1)
- **000-DR-STND-live-rag-and-agent-engine-rollout-plan.md** - Rollout plan with feature flags (Phase AE3)
- **agents/config/agent_engine.py** - Agent Engine ID configuration
- **agents/utils/a2a_adapter.py** - A2A adapter for Agent Engine calls
- **service/a2a_gateway/main.py** - A2A gateway implementation
- **service/slack_webhook/main.py** - Slack webhook implementation

---

## Changelog

| Date | Change | Author |
|------|--------|--------|
| 2025-11-20 | Initial gateway design and documentation | Build Captain (Phase AE2) |

---

**Status:** Design (Phase AE2 - Stubbed Implementation)
**Next Steps:** Create Phase AE3 rollout plan (000-DR-STND-live-rag-and-agent-engine-rollout-plan) and feature flags module
