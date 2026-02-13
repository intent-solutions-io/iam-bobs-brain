# Live RAG & Agent Engine Rollout Plan

**Document ID:** 000-DR-STND-live-rag-and-agent-engine-rollout-plan-DR-STND-live-rag-and-agent-engine-rollout-plan
**Created:** 2025-11-20
**Phase:** AE3 (Live RAG & Engine Rollout + Safety)
**Status:** Standard (Rollout Plan)

---

## Purpose

This document defines the **rollout strategy** for enabling live Vertex AI Search (RAG) and Agent Engine features across Bob's Brain department. It provides a feature flag matrix, progression gates, and safety mechanisms to ensure controlled, incremental rollout without disrupting production.

## Rollout Philosophy

### Principles

1. **Default OFF:** All new features start disabled across all environments
2. **Gradual Progression:** OFF → EXPERIMENTAL (dev) → STAGING → PROD
3. **Environment Gating:** No production flags enabled without staging validation
4. **Feature Independence:** Each feature can be rolled back independently
5. **Safety First:** ARV checks block deployments if flags misconfigured
6. **Observable Rollout:** Metrics and logs track feature usage and health

### Why Feature Flags?

- **Risk Mitigation:** Enable features incrementally, rollback instantly if issues
- **Testing in Production:** Validate features with real traffic safely
- **Gradual Migration:** Shift from current Bob (…6448) to next-gen ADK department
- **Independent Rollouts:** Enable RAG, foreman, iam-* agents on different schedules
- **Environment Parity:** Dev/staging match production config minus flag state

---

## Feature Flag Matrix

### Feature Categories

**1. Live RAG (Vertex AI Search):**
- Enable semantic search over ADK/Vertex documentation
- Replace placeholder responses with real knowledge retrieval
- Gradual rollout per agent (Bob, foreman, iam-*)

**2. Agent Engine Mode (Multi-Agent Orchestration):**
- Enable Agent-to-Agent calls via Agent Engine
- Replace local stubs with real Agent Engine HTTP calls
- Gradual rollout per agent pair (e.g., foreman → iam-adk)

**3. Gateway Routing:**
- Enable Option B routing (Slack → a2a_gateway → Agent Engine)
- Replace direct Agent Engine calls with multi-agent orchestration
- Controlled rollout by environment

### Feature Flag Definitions

| Flag Name | Category | Purpose | Default |
|-----------|----------|---------|---------|
| `LIVE_RAG_BOB_ENABLED` | RAG | Enable Vertex Search for Bob | `False` |
| `LIVE_RAG_FOREMAN_ENABLED` | RAG | Enable Vertex Search for foreman | `False` |
| `LIVE_RAG_IAM_ADK_ENABLED` | RAG | Enable Vertex Search for iam-adk | `False` |
| `ENGINE_MODE_FOREMAN_TO_IAM_ADK` | A2A | Enable foreman → iam-adk via Engine | `False` |
| `ENGINE_MODE_FOREMAN_TO_IAM_ISSUE` | A2A | Enable foreman → iam-issue via Engine | `False` |
| `ENGINE_MODE_BOB_TO_FOREMAN` | A2A | Enable Bob → foreman via Engine | `False` |
| `SLACK_SWE_PIPELINE_MODE_ENABLED` | Gateway | Enable Option B routing (Slack → a2a_gateway) | `False` |
| `AGENT_ENGINE_BOB_NEXT_GEN_ENABLED` | Migration | Route Bob traffic to next-gen engine | `False` |
| `AGENT_ENGINE_BOB_NEXT_GEN_PERCENT` | Migration | % traffic to next-gen Bob (0-100) | `0` |

### Environment-Specific Flag States

All flags have **environment-aware defaults**:

```python
# Example from agents/config/features.py

def get_feature_state(flag_name: str, env: str) -> bool:
    """Get feature flag state for environment."""
    # Production flags must be explicitly enabled
    # Dev/staging can have experimental flags

    if env == "prod":
        # All flags OFF by default in production
        return os.getenv(flag_name, "false").lower() == "true"
    elif env == "staging":
        # Staging can enable flags for validation
        return os.getenv(flag_name, "false").lower() == "true"
    else:  # dev
        # Dev can experiment freely
        return os.getenv(flag_name, "false").lower() == "true"
```

---

## Rollout Progression Matrix

### Stage 0: OFF (Default - All Environments)

**Status:** All features disabled, stubs/placeholders active

| Feature | Dev | Staging | Prod | Notes |
|---------|-----|---------|------|-------|
| Live RAG (all agents) | OFF | OFF | OFF | Placeholder responses |
| Engine Mode (all A2A) | OFF | OFF | OFF | Local stubs |
| Option B routing | OFF | OFF | OFF | Direct to Agent Engine |
| Next-gen Bob | OFF | OFF | OFF | Current Bob (…6448) active |

**Behavior:**
- Bob (…6448) serves all production traffic
- Foreman uses local stub implementations for iam-*
- No Vertex AI Search queries
- Slack routes directly to Agent Engine (Option A)

---

### Stage 1: EXPERIMENTAL (Dev Only)

**Status:** Early testing in dev environment, expect breakage

| Feature | Dev | Staging | Prod | Prerequisites |
|---------|-----|---------|------|---------------|
| LIVE_RAG_BOB_ENABLED | ON | OFF | OFF | Vertex Search datastore configured |
| LIVE_RAG_FOREMAN_ENABLED | ON | OFF | OFF | Vertex Search datastore configured |
| LIVE_RAG_IAM_ADK_ENABLED | ON | OFF | OFF | Vertex Search datastore configured |
| ENGINE_MODE_FOREMAN_TO_IAM_ADK | ON | OFF | OFF | iam-adk deployed to dev Engine |
| SLACK_SWE_PIPELINE_MODE_ENABLED | ON | OFF | OFF | a2a_gateway deployed to dev |

**Duration:** 1-2 weeks

**Goals:**
- Validate Vertex Search integration works
- Test A2A calls via Agent Engine
- Debug issues in dev without production impact
- Iterate on prompts and tool configurations

**Success Criteria:**
- ✅ Vertex Search returns relevant results
- ✅ A2A calls complete successfully
- ✅ No authentication or network errors
- ✅ Performance acceptable (< 5s p95)
- ✅ Logs and correlation IDs working

**Rollback Plan:**
- Set all dev flags to `false`
- Restart dev services
- Dev returns to Stage 0 behavior

---

### Stage 2: STAGING (Pre-Production Validation)

**Status:** Production-like testing with full topology

| Feature | Dev | Staging | Prod | Prerequisites |
|---------|-----|---------|------|---------------|
| LIVE_RAG_BOB_ENABLED | ON | ON | OFF | Stage 1 success criteria met |
| LIVE_RAG_FOREMAN_ENABLED | ON | ON | OFF | Stage 1 success criteria met |
| LIVE_RAG_IAM_ADK_ENABLED | ON | ON | OFF | Stage 1 success criteria met |
| ENGINE_MODE_FOREMAN_TO_IAM_ADK | ON | ON | OFF | iam-adk deployed to staging Engine |
| ENGINE_MODE_FOREMAN_TO_IAM_ISSUE | ON | ON | OFF | iam-issue deployed to staging Engine |
| SLACK_SWE_PIPELINE_MODE_ENABLED | ON | ON | OFF | a2a_gateway deployed to staging |

**Duration:** 1-2 weeks

**Goals:**
- Validate features in production-like environment
- Run end-to-end SWE pipeline tests
- Load test with realistic traffic patterns
- Verify observability and alerts working

**Success Criteria:**
- ✅ All Stage 1 criteria still met
- ✅ End-to-end SWE pipeline completes successfully
- ✅ Load tests pass (100 concurrent requests)
- ✅ Monitoring dashboards show healthy metrics
- ✅ No memory leaks or performance degradation
- ✅ ARV checks pass in staging CI

**Rollback Plan:**
- Set staging flags to `false`
- Redeploy staging services
- Investigate issues before re-enabling

---

### Stage 3: PROD EXPERIMENTAL (Canary - 5%)

**Status:** Early production exposure, limited blast radius

| Feature | Dev | Staging | Prod | Prerequisites |
|---------|-----|---------|------|---------------|
| LIVE_RAG_BOB_ENABLED | ON | ON | ON (5%) | Stage 2 success criteria met |
| AGENT_ENGINE_BOB_NEXT_GEN_PERCENT | - | - | 5 | Next-gen Bob deployed to prod |

**Duration:** 1 week

**Goals:**
- Validate features with real production traffic
- Monitor error rates and user satisfaction
- Collect performance data under real load
- Build confidence for broader rollout

**Success Criteria:**
- ✅ Error rate < 1% for flagged requests
- ✅ Latency p95 < 2x baseline
- ✅ User satisfaction maintained
- ✅ No rollbacks triggered
- ✅ Monitoring shows healthy behavior

**Rollback Plan:**
- Set AGENT_ENGINE_BOB_NEXT_GEN_PERCENT to `0`
- Or set flags to `false`
- Traffic immediately returns to current Bob
- Post-mortem required before retry

---

### Stage 4: PROD GRADUAL (Canary - 25%, 50%, 100%)

**Status:** Progressive rollout to full production

| Feature | Dev | Staging | Prod | Duration |
|---------|-----|---------|------|----------|
| LIVE_RAG_BOB_ENABLED | ON | ON | ON (25%) | 1 week |
| LIVE_RAG_BOB_ENABLED | ON | ON | ON (50%) | 1 week |
| LIVE_RAG_BOB_ENABLED | ON | ON | ON (100%) | - |
| AGENT_ENGINE_BOB_NEXT_GEN_PERCENT | - | - | 25 → 50 → 100 | 3 weeks total |

**Duration:** 3-4 weeks total

**Goals:**
- Gradually shift all production traffic to next-gen
- Monitor metrics at each stage
- Validate no regressions at scale
- Retire current Bob (…6448) once 100% on next-gen

**Success Criteria (Each Stage):**
- ✅ Error rate remains < 1%
- ✅ Latency p95 within acceptable range
- ✅ User satisfaction maintained or improved
- ✅ No critical incidents
- ✅ Monitoring green across all dashboards

**Rollback Plan:**
- Reduce AGENT_ENGINE_BOB_NEXT_GEN_PERCENT to previous stage
- Or set to `0` for immediate fallback
- Document issues and address before re-ramping

---

### Stage 5: FULL PRODUCTION (Next-Gen Standard)

**Status:** Current Bob (…6448) deprecated, next-gen is canonical

| Feature | Dev | Staging | Prod | Notes |
|---------|-----|---------|------|-------|
| LIVE_RAG_BOB_ENABLED | ON | ON | ON | All agents using Vertex Search |
| ENGINE_MODE_FOREMAN_TO_IAM_ADK | ON | ON | ON | Full multi-agent orchestration |
| ENGINE_MODE_FOREMAN_TO_IAM_ISSUE | ON | ON | ON | Full multi-agent orchestration |
| ENGINE_MODE_BOB_TO_FOREMAN | ON | ON | ON | Bob → foreman via Engine |
| SLACK_SWE_PIPELINE_MODE_ENABLED | ON | ON | ON | Option B routing active |
| AGENT_ENGINE_BOB_NEXT_GEN_PERCENT | - | - | 100 | Next-gen Bob is canonical |

**Duration:** Indefinite (new baseline)

**Behavior:**
- Next-gen Bob (ADK-based) serves all production traffic
- Foreman orchestrates iam-* agents via Agent Engine
- All agents use Vertex AI Search for knowledge
- Slack routes via a2a_gateway (Option B)
- Current Bob (…6448) deprecated and eventually decommissioned

**Rollback Plan:**
- If catastrophic issues, revert AGENT_ENGINE_BOB_NEXT_GEN_PERCENT to `0`
- Requires significant effort (Stage 5 is meant to be stable)
- Prefer fixing forward vs rolling back at this stage

---

## Feature Flag Implementation

### Configuration Module Structure

**File:** `agents/config/features.py`

```python
"""
Feature Flags for Agent Engine Rollout (Phase AE3)

This module defines feature flags for controlled rollout of:
- Live RAG (Vertex AI Search)
- Agent Engine mode (A2A calls)
- Gateway routing (Option B)
- Next-gen Bob migration
"""

import os
from typing import Literal

Environment = Literal["dev", "staging", "prod"]

# ==============================================================================
# FEATURE FLAG DEFINITIONS
# ==============================================================================

# Live RAG (Vertex AI Search)
LIVE_RAG_BOB_ENABLED = "LIVE_RAG_BOB_ENABLED"
LIVE_RAG_FOREMAN_ENABLED = "LIVE_RAG_FOREMAN_ENABLED"
LIVE_RAG_IAM_ADK_ENABLED = "LIVE_RAG_IAM_ADK_ENABLED"

# Agent Engine Mode (A2A Calls)
ENGINE_MODE_FOREMAN_TO_IAM_ADK = "ENGINE_MODE_FOREMAN_TO_IAM_ADK"
ENGINE_MODE_FOREMAN_TO_IAM_ISSUE = "ENGINE_MODE_FOREMAN_TO_IAM_ISSUE"
ENGINE_MODE_BOB_TO_FOREMAN = "ENGINE_MODE_BOB_TO_FOREMAN"

# Gateway Routing
SLACK_SWE_PIPELINE_MODE_ENABLED = "SLACK_SWE_PIPELINE_MODE_ENABLED"

# Migration Flags
AGENT_ENGINE_BOB_NEXT_GEN_ENABLED = "AGENT_ENGINE_BOB_NEXT_GEN_ENABLED"
AGENT_ENGINE_BOB_NEXT_GEN_PERCENT = "AGENT_ENGINE_BOB_NEXT_GEN_PERCENT"

# ==============================================================================
# HELPER FUNCTIONS
# ==============================================================================

def get_current_environment() -> Environment:
    """Detect current environment."""
    env_str = os.getenv("DEPLOYMENT_ENV", "dev").lower()
    if env_str in ("prod", "production"):
        return "prod"
    elif env_str in ("staging", "stage"):
        return "staging"
    else:
        return "dev"

def is_feature_enabled(flag_name: str, env: Environment = None) -> bool:
    """Check if a feature flag is enabled."""
    if env is None:
        env = get_current_environment()

    # All flags OFF by default (safety first)
    return os.getenv(flag_name, "false").lower() == "true"

def get_traffic_percent(flag_name: str = AGENT_ENGINE_BOB_NEXT_GEN_PERCENT) -> int:
    """Get traffic percentage for canary rollout (0-100)."""
    try:
        percent = int(os.getenv(flag_name, "0"))
        return max(0, min(100, percent))  # Clamp to [0, 100]
    except ValueError:
        return 0

# ==============================================================================
# CONVENIENCE FUNCTIONS
# ==============================================================================

def is_live_rag_enabled_for_bob() -> bool:
    """Check if Bob should use Vertex AI Search."""
    return is_feature_enabled(LIVE_RAG_BOB_ENABLED)

def is_live_rag_enabled_for_foreman() -> bool:
    """Check if foreman should use Vertex AI Search."""
    return is_feature_enabled(LIVE_RAG_FOREMAN_ENABLED)

def should_use_next_gen_bob() -> bool:
    """Check if request should route to next-gen Bob (canary logic)."""
    if not is_feature_enabled(AGENT_ENGINE_BOB_NEXT_GEN_ENABLED):
        return False

    percent = get_traffic_percent()
    if percent == 0:
        return False
    if percent >= 100:
        return True

    # Simple canary: random percentage
    import random
    return random.random() * 100 < percent

def should_use_option_b_routing() -> bool:
    """Check if Slack should route via a2a_gateway (Option B)."""
    return is_feature_enabled(SLACK_SWE_PIPELINE_MODE_ENABLED)
```

### Usage in Code

**Example: Bob agent checks RAG flag**
```python
from agents.config.features import is_live_rag_enabled_for_bob

if is_live_rag_enabled_for_bob():
    # Use Vertex AI Search
    results = vertex_search.query(prompt)
else:
    # Use placeholder response
    results = "RAG not enabled yet (Phase AE3)"
```

**Example: a2a_gateway checks engine mode**
```python
from agents.config.features import is_feature_enabled, ENGINE_MODE_FOREMAN_TO_IAM_ADK

if is_feature_enabled(ENGINE_MODE_FOREMAN_TO_IAM_ADK):
    # Real Agent Engine call
    response = call_agent_engine(agent_role="iam-adk", request=...)
else:
    # Stubbed response
    response = "[STUB] iam-adk not enabled yet"
```

---

## Safety Mechanisms

### ARV Check: Engine Flags Validation

**File:** `scripts/check_arv_engine_flags.py`

**Purpose:** Ensure feature flags are not misconfigured before deployment

**Checks:**

1. **Production Flags OFF by Default:**
   - No production flags enabled without explicit environment variable
   - Prevents accidental production enablement

2. **Prerequisites Met:**
   - If `ENGINE_MODE_FOREMAN_TO_IAM_ADK=true`, then iam-adk must be deployed
   - If `LIVE_RAG_BOB_ENABLED=true`, then Vertex Search datastore must exist

3. **Staging Before Prod:**
   - No production flag enabled without staging validation
   - Check that staging has flag enabled before prod

4. **Traffic Percentage Sanity:**
   - `AGENT_ENGINE_BOB_NEXT_GEN_PERCENT` must be 0-100
   - Prod traffic percent must not exceed 100

**Exit Codes:**
- `0` - All checks passed
- `1` - Flag misconfiguration detected (blocks deployment)
- `2` - Error during checks

**CI Integration:**
```yaml
# .github/workflows/ci.yml

arv-engine-flags:
  runs-on: ubuntu-latest
  needs: [arv-check]  # After ARV minimum check
  steps:
    - uses: actions/checkout@v4
    - name: Run ARV engine flags check
      run: make check-arv-engine-flags
```

### Make Target

```makefile
check-arv-engine-flags: ## Check ARV engine flags safety (Phase AE3)
	@echo "$(BLUE)🔍 Checking Engine Flags Safety...$(NC)"
	@$(PYTHON) scripts/check_arv_engine_flags.py
	@echo ""
```

---

## Monitoring & Observability

### Key Metrics to Monitor

**Feature Flag Usage:**
- `feature_flag_enabled{flag_name, env}` - Boolean gauge per flag
- `feature_flag_requests{flag_name, env}` - Count of requests using flag
- `feature_flag_errors{flag_name, env}` - Errors when flag enabled

**Canary Rollout:**
- `bob_next_gen_traffic_percent` - Current canary percentage
- `bob_next_gen_requests` - Requests to next-gen Bob
- `bob_current_requests` - Requests to current Bob (…6448)
- `bob_next_gen_error_rate` - Error rate for next-gen
- `bob_current_error_rate` - Error rate for current (baseline)

**A2A Calls:**
- `a2a_calls_total{agent_role, env}` - Count of A2A calls
- `a2a_calls_stubbed{agent_role}` - Count of stubbed vs real calls
- `a2a_latency{agent_role, env}` - Latency distribution

**RAG Usage:**
- `vertex_search_queries{agent, env}` - Count of Vertex Search queries
- `vertex_search_latency{agent}` - Query latency
- `vertex_search_errors{agent}` - Query errors

### Alerting Rules

**Critical Alerts:**
- Error rate > 5% when flag enabled → Page on-call
- Latency p95 > 2x baseline when flag enabled → Page on-call
- Canary rollout regression detected → Auto-rollback

**Warning Alerts:**
- Flag enabled in prod without staging validation → Warn in Slack
- Traffic percent > 50% without manual approval → Warn in Slack
- Unexpected flag state change → Audit log review

---

## Rollback Procedures

### Immediate Rollback (Emergency)

**Trigger:** Critical production issues, error rate spike, user complaints

**Steps:**
1. Set problematic flag to `false` in production environment
2. Redeploy affected services (or restart if env var change)
3. Verify traffic returns to baseline behavior
4. Page on-call team
5. Create incident report

**Example:**
```bash
# Emergency rollback of next-gen Bob
gcloud run services update a2a-gateway \
  --set-env-vars AGENT_ENGINE_BOB_NEXT_GEN_ENABLED=false \
  --region us-central1

# Or instant canary rollback
gcloud run services update a2a-gateway \
  --set-env-vars AGENT_ENGINE_BOB_NEXT_GEN_PERCENT=0 \
  --region us-central1
```

### Gradual Rollback (Canary Reduction)

**Trigger:** Minor issues, performance degradation, user feedback

**Steps:**
1. Reduce canary percentage by 50% (e.g., 50% → 25%)
2. Monitor metrics for stabilization
3. If issues persist, reduce further or disable completely
4. Investigate root cause
5. Address issues before re-ramping

---

## Timeline Summary

| Stage | Duration | Cumulative | Key Milestone |
|-------|----------|------------|---------------|
| Stage 0: OFF | - | - | Baseline (all features disabled) |
| Stage 1: Dev Experimental | 1-2 weeks | 2 weeks | Features working in dev |
| Stage 2: Staging Validation | 1-2 weeks | 4 weeks | Features validated in staging |
| Stage 3: Prod 5% Canary | 1 week | 5 weeks | Real production traffic exposure |
| Stage 4: Prod 25% | 1 week | 6 weeks | Broader production exposure |
| Stage 4: Prod 50% | 1 week | 7 weeks | Majority on next-gen |
| Stage 4: Prod 100% | - | 7+ weeks | Full rollout complete |
| Stage 5: Deprecation | 2 weeks | 9+ weeks | Current Bob decommissioned |

**Total Time to Full Production:** ~7-9 weeks from Stage 0

---

## Related Documents

- **101-AT-ARCH-agent-engine-topology-and-envs.md** - Agent Engine deployment topology (Phase AE1)
- **102-AT-ARCH-cloud-run-gateways-and-agent-engine-routing.md** - Gateway architecture (Phase AE2)
- **agents/config/features.py** - Feature flags implementation (Phase AE3)
- **agents/config/agent_engine.py** - Agent Engine ID configuration (Phase AE1)
- **scripts/check_arv_engine_flags.py** - ARV engine flags safety check (Phase AE3)

---

## Changelog

| Date | Change | Author |
|------|--------|--------|
| 2025-11-20 | Initial rollout plan and feature flag strategy | Build Captain (Phase AE3) |

---

**Status:** Standard (Rollout Plan)
**Next Steps:** Implement feature flags module and ARV engine flags check
