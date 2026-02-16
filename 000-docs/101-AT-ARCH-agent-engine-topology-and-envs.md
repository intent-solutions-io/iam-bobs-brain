# Agent Engine Topology and Environments

**Document ID:** 101-AT-ARCH-agent-engine-topology-and-envs
**Created:** 2025-11-20
**Phase:** AE1 (Agent Engine Deployment Model)
**Status:** Design

---

## Purpose

This document defines the **Vertex AI Agent Engine deployment topology** for Bob's Brain and the IAM Agent Engineering Department. It specifies how agents are deployed across environments, their logical identities, and the migration path from current to next-generation architecture.

## Environments

The department operates in three environments:

| Environment | Purpose | Deployment Policy |
|-------------|---------|-------------------|
| **dev** | Development and experimentation | Continuous deployment from `main` branch |
| **staging** | Pre-production validation | Manual promotion from dev |
| **prod** | Production workloads | Manual promotion from staging with ARV gates |

## Agent Engine Deployment Topology

### Current State (Pre-Migration)

**Bob (Canonical Production Agent):**
- **Reasoning Engine ID:** `projects/205354194989/locations/us-central1/reasoningEngines/5828234061910376448`
- **Region:** `us-central1`
- **Status:** Active production agent (pre-ADK architecture)
- **SPIFFE ID:** `spiffe://intent.solutions/agent/bobs-brain/prod/us-central1/0.8.0`

This is the current production Bob agent serving live Slack traffic.

### Target State (ADK Multi-Agent Department)

#### Agent Grouping Strategy

We will deploy agents as **separate reasoning engines per agent role**:

**Rationale:**
- Clear separation of concerns
- Independent scaling and versioning
- Easier observability and debugging
- Matches A2A protocol design (agent-to-agent calls)

**Alternative Considered:** Single reasoning engine with multiple tools
- **Rejected:** Would blur agent boundaries and make A2A routing complex

#### Agents in Agent Engine

The following agents will run as standalone reasoning engines:

1. **Bob (Orchestrator)**
   - Role: Global orchestrator, handles Slack requests, delegates to departments
   - Deployment: All environments (dev, staging, prod)

2. **iam-senior-adk-devops-lead (Foreman)**
   - Role: Department foreman, orchestrates SWE pipeline
   - Deployment: All environments
   - Calls: iam-* specialist agents

3. **iam-adk (ADK Design Specialist)**
   - Role: ADK/Vertex pattern analysis and design
   - Deployment: Staging/prod (dev uses local stub)

4. **iam-issue (Issue Management)**
   - Role: Convert violations to structured issues
   - Deployment: Staging/prod (dev uses local stub)

#### Tools Behind Foreman

The following iam-* agents will initially run as **tools/functions within the foreman**, not as separate engines:

- **iam-fix-plan:** Fix planning logic
- **iam-fix-impl:** Code change implementation
- **iam-qa:** Quality assurance verification
- **iam-doc:** Documentation updates
- **iam-cleanup:** Tech debt identification
- **iam-index:** Knowledge indexing

**Migration Path:** These may become standalone engines in future phases if:
- They need independent scaling
- They're called from multiple parents (not just foreman)
- A2A protocol benefits outweigh coordination complexity

### Environment-Specific Deployment

#### Development Environment

| Agent | Reasoning Engine ID | Region | Notes |
|-------|-------------------|--------|-------|
| **bob** | `projects/PROJECT_ID/locations/us-central1/reasoningEngines/BOB_DEV_PLACEHOLDER` | us-central1 | Dev instance for testing |
| **iam-senior-adk-devops-lead** | `projects/PROJECT_ID/locations/us-central1/reasoningEngines/FOREMAN_DEV_PLACEHOLDER` | us-central1 | Dev foreman |
| **iam-adk** | (local stub) | - | Not deployed to Engine in dev |
| **iam-issue** | (local stub) | - | Not deployed to Engine in dev |

**SPIFFE IDs (Dev):**
- Bob: `spiffe://intent.solutions/agent/bobs-brain/dev/us-central1/0.9.0`
- Foreman: `spiffe://intent.solutions/agent/bobs-brain-foreman/dev/us-central1/0.9.0`

**Characteristics:**
- Rapid iteration
- May use local stubs for iam-* agents
- RAG may use test/mock datastores
- Correlation IDs enabled for tracing

#### Staging Environment

| Agent | Reasoning Engine ID | Region | Notes |
|-------|-------------------|--------|-------|
| **bob** | `projects/PROJECT_ID/locations/us-central1/reasoningEngines/BOB_STAGING_PLACEHOLDER` | us-central1 | Pre-prod validation |
| **iam-senior-adk-devops-lead** | `projects/PROJECT_ID/locations/us-central1/reasoningEngines/FOREMAN_STAGING_PLACEHOLDER` | us-central1 | Pre-prod foreman |
| **iam-adk** | `projects/PROJECT_ID/locations/us-central1/reasoningEngines/IAM_ADK_STAGING_PLACEHOLDER` | us-central1 | Real engine |
| **iam-issue** | `projects/PROJECT_ID/locations/us-central1/reasoningEngines/IAM_ISSUE_STAGING_PLACEHOLDER` | us-central1 | Real engine |

**SPIFFE IDs (Staging):**
- Bob: `spiffe://intent.solutions/agent/bobs-brain/staging/us-central1/0.9.0`
- Foreman: `spiffe://intent.solutions/agent/bobs-brain-foreman/staging/us-central1/0.9.0`
- iam-adk: `spiffe://intent.solutions/agent/bobs-brain-iam-adk/staging/us-central1/0.9.0`
- iam-issue: `spiffe://intent.solutions/agent/bobs-brain-iam-issue/staging/us-central1/0.9.0`

**Characteristics:**
- Matches production topology
- Real Vertex AI Search datastores (staging-specific)
- Full A2A protocol between engines
- ARV gates enforced before promotion

#### Production Environment

| Agent | Reasoning Engine ID | Region | Notes |
|-------|-------------------|--------|-------|
| **bob (current)** | `projects/205354194989/locations/us-central1/reasoningEngines/5828234061910376448` | us-central1 | **Current canonical** |
| **bob (next-gen)** | `projects/PROJECT_ID/locations/us-central1/reasoningEngines/BOB_PROD_NEXT_GEN_PLACEHOLDER` | us-central1 | **Future ADK version** |
| **iam-senior-adk-devops-lead** | `projects/PROJECT_ID/locations/us-central1/reasoningEngines/FOREMAN_PROD_PLACEHOLDER` | us-central1 | Production foreman |
| **iam-adk** | `projects/PROJECT_ID/locations/us-central1/reasoningEngines/IAM_ADK_PROD_PLACEHOLDER` | us-central1 | Production specialist |
| **iam-issue** | `projects/PROJECT_ID/locations/us-central1/reasoningEngines/IAM_ISSUE_PROD_PLACEHOLDER` | us-central1 | Production specialist |

**SPIFFE IDs (Prod):**
- Bob (current): `spiffe://intent.solutions/agent/bobs-brain/prod/us-central1/0.8.0`
- Bob (next-gen): `spiffe://intent.solutions/agent/bobs-brain/prod/us-central1/0.9.0`
- Foreman: `spiffe://intent.solutions/agent/bobs-brain-foreman/prod/us-central1/0.9.0`
- iam-adk: `spiffe://intent.solutions/agent/bobs-brain-iam-adk/prod/us-central1/0.9.0`
- iam-issue: `spiffe://intent.solutions/agent/bobs-brain-iam-issue/prod/us-central1/0.9.0`

**Characteristics:**
- High availability
- Production Vertex AI Search datastores
- Full observability (correlation IDs, structured logging)
- Strict ARV gates
- Blue/green deployment support

### Logical Naming Convention

All reasoning engines follow this pattern:

```
projects/{PROJECT_ID}/locations/{REGION}/reasoningEngines/{NUMERIC_ID}
```

**Logical Names (for config/docs):**
```
{agent-role}-{environment}

Examples:
- bob-dev
- bob-staging
- bob-prod
- foreman-dev
- foreman-staging
- foreman-prod
- iam-adk-staging
- iam-adk-prod
```

These logical names map to actual reasoning engine IDs via configuration (see `config/agent_engine.yaml`).

## Migration Strategy: Current → Next-Gen

### Phase 1: Parallel Deployment
- **Current Bob (…6448)** remains active in production
- **Next-gen Bob** deployed to dev/staging only
- Traffic routing:
  - Production Slack traffic → Current Bob
  - Dev/staging traffic → Next-gen Bob
- Duration: 2-4 weeks

### Phase 2: Shadow Traffic
- **Next-gen Bob** deployed to production (separate engine)
- Traffic duplication:
  - Primary: Current Bob (…6448)
  - Shadow: Next-gen Bob (observability only)
- Comparison:
  - Response quality
  - Latency
  - Error rates
- Duration: 1-2 weeks

### Phase 3: Canary Rollout
- Gradually shift production traffic:
  - 5% → Next-gen Bob
  - 25% → Next-gen Bob
  - 50% → Next-gen Bob
  - 100% → Next-gen Bob
- Monitor:
  - User satisfaction
  - Slack command success rates
  - Pipeline completion rates
- Rollback plan: Shift traffic back to current Bob
- Duration: 2-3 weeks

### Phase 4: Deprecation
- **Current Bob (…6448)** marked deprecated
- Grace period: 2 weeks for emergency rollback
- Decommission: Archive engine, update docs
- **Next-gen Bob** becomes canonical production

### Rollback Safety

At any point during migration:
1. Shift Slack traffic back to current Bob via gateway config
2. Disable next-gen engines (set `AGENT_ENGINE_ENABLED=false`)
3. Fall back to local/stub implementations for iam-*

**Rollback Trigger Conditions:**
- Error rate > 5%
- User complaints > baseline
- Latency > 2x baseline
- Pipeline success rate < 90%

## Gateway Pattern and Responsibilities

### Cloud Run Services

Two gateway services sit between external traffic and Agent Engine:

#### 1. slack_webhook Service
- **Purpose:** Handle Slack webhook events
- **Responsibilities:**
  - Validate Slack signatures
  - Parse slash commands and events
  - Route to appropriate agent (Bob, foreman, etc.)
  - Return formatted Slack responses
- **Routing:**
  - Slack → `slack_webhook` → `a2a_gateway` → Agent Engine
- **Region:** `us-central1` (primary)
- **Scaling:** Auto-scale based on Slack traffic

#### 2. a2a_gateway Service
- **Purpose:** Internal Agent-to-Agent HTTP gateway
- **Responsibilities:**
  - Accept A2A HTTP requests (JSON `A2AAgentCall`)
  - Resolve target reasoning engine ID
  - Forward to Agent Engine via REST API
  - Return results as JSON `A2AAgentResult`
- **Routing:**
  - `slack_webhook` → `a2a_gateway` → Agent Engine
  - Foreman (Agent Engine) → `a2a_gateway` → iam-* agents (Agent Engine)
- **Region:** `us-central1` (primary)
- **Scaling:** Auto-scale based on A2A request volume

### Why Two Services?

**Separation of Concerns:**
- `slack_webhook`: Slack-specific logic (signature validation, formatting)
- `a2a_gateway`: Agent-agnostic protocol translation

**Benefits:**
- Other clients (API, CLI) can use `a2a_gateway` directly
- Slack-specific changes don't affect A2A protocol
- Easier testing (mock A2A gateway for Slack tests)

**Alternative Considered:** Single gateway for both
- **Rejected:** Mixes Slack logic with A2A protocol, harder to test

## Configuration Management

### Agent Engine IDs

Managed in `config/agent_engine.yaml` (or Python equivalent):

```yaml
environments:
  dev:
    bob:
      reasoning_engine_id: "projects/PROJECT_ID/locations/us-central1/reasoningEngines/BOB_DEV_PLACEHOLDER"
      region: "us-central1"
      spiffe_id: "spiffe://intent.solutions/agent/bobs-brain/dev/us-central1/0.9.0"
    foreman:
      reasoning_engine_id: "projects/PROJECT_ID/locations/us-central1/reasoningEngines/FOREMAN_DEV_PLACEHOLDER"
      region: "us-central1"
      spiffe_id: "spiffe://intent.solutions/agent/bobs-brain-foreman/dev/us-central1/0.9.0"

  staging:
    # ... similar structure

  prod:
    bob_current:
      reasoning_engine_id: "projects/205354194989/locations/us-central1/reasoningEngines/5828234061910376448"
      region: "us-central1"
      spiffe_id: "spiffe://intent.solutions/agent/bobs-brain/prod/us-central1/0.8.0"
      notes: "Current canonical Bob (pre-ADK)"
    bob_next_gen:
      reasoning_engine_id: "projects/PROJECT_ID/locations/us-central1/reasoningEngines/BOB_PROD_NEXT_GEN_PLACEHOLDER"
      region: "us-central1"
      spiffe_id: "spiffe://intent.solutions/agent/bobs-brain/prod/us-central1/0.9.0"
      notes: "Next-gen ADK Bob"
```

### Environment Detection

Use existing `DEPLOYMENT_ENV` environment variable:
- `dev` → Development engines
- `staging` → Staging engines
- `prod` → Production engines (with current/next-gen selection)

### Traffic Routing Config

During migration, use feature flags:
- `PROD_BOB_VERSION`: `"current"` | `"next-gen"`
- `PROD_BOB_CANARY_PERCENT`: `0` to `100`

## Observability

### Correlation IDs

All requests through Agent Engine carry:
- **pipeline_run_id:** UUID for entire pipeline run
- **agent_invocation_id:** UUID for this specific agent call
- **trace_id:** Vertex AI trace ID (when available)

### Logging

Each Agent Engine call logged with:
- Correlation IDs
- Agent role and environment
- Reasoning engine ID
- Request/response sizes
- Latency
- Success/error status

### Monitoring

Key metrics per agent and environment:
- **Availability:** Uptime, error rate
- **Latency:** p50, p95, p99 response times
- **Usage:** Requests per minute, tokens consumed
- **Quality:** User satisfaction, task completion rate

### Alerts

- Error rate > 5% for 5 minutes
- Latency p95 > 10s
- Agent Engine unavailable
- Canary traffic showing regression

## Security

### Authentication

Agent Engine calls authenticated via:
- **Service Account:** Each Cloud Run service uses dedicated SA
- **IAM Permissions:** `aiplatform.reasoningEngines.query`
- **VPC:** Agent Engine in VPC, services in same VPC

### Authorization

- Agents can only call their designated downstream agents
- Foreman → iam-* (allowed)
- iam-* → Foreman (blocked)

### Secrets

- No secrets in reasoning engine configs
- Secrets injected via:
  - GCP Secret Manager
  - Environment variables in Cloud Run

## Versioning

### Agent Versions

Embedded in SPIFFE ID:
```
spiffe://intent.solutions/agent/bobs-brain/prod/us-central1/0.9.0
                                                                ^^^^
                                                                version
```

**Versioning Strategy:**
- Major: Breaking changes to A2A protocol or contracts
- Minor: New features, non-breaking changes
- Patch: Bug fixes

### Reasoning Engine Updates

- **In-place:** Not recommended (hard to rollback)
- **Blue/green:** Deploy new engine, switch traffic, deprecate old
- **Canary:** Gradual traffic shift between versions

## Future Enhancements

### Multi-Region

Currently: `us-central1` only

**Future:** Multi-region for:
- High availability (regional failover)
- Lower latency (geo-distributed)
- Compliance (data residency)

**Regions to Consider:**
- `us-east1` (backup)
- `europe-west1` (EU compliance)
- `asia-east1` (APAC latency)

### Cross-Project Agents

Currently: All agents in same project

**Future:** Agents in separate projects for:
- Billing isolation
- Quota management
- Organizational boundaries

**Requires:** Cross-project IAM + VPC peering

### Agent Mesh

Currently: Star topology (foreman → iam-*)

**Future:** Mesh topology where any agent can call any other
- Requires: Enhanced A2A routing
- Benefit: More flexible agent interactions
- Risk: Increased complexity

## Related Documents

- **102-AT-ARCH-cloud-run-gateways-and-agent-engine-routing.md** - Gateway design (Phase AE2)
- **000-DR-STND-live-rag-and-agent-engine-rollout-plan.md** - Rollout plan (Phase AE3)
- **config/agent_engine.yaml** - Reasoning engine ID configuration
- **agents/config/features.py** - Feature flags for gradual rollout

## Changelog

| Date | Change | Author |
|------|--------|--------|
| 2025-11-20 | Initial Agent Engine topology design | Build Captain (Phase AE1) |

---

**Status:** Design
**Next Steps:** Implement config module (Phase AE1, Task 2)
