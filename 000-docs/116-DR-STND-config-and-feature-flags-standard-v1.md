# Configuration and Feature Flags Standard v1.0

**Document Number:** 116-DR-STND-config-and-feature-flags-standard-v1
**Status:** Active
**Date:** 2025-11-20
**Phase:** CONF (Configuration Centralization)
**Author:** Build Captain (Claude)

---

## Executive Summary

This document defines the configuration and feature flags standard for Bob's Brain (bobs-brain repo). It establishes a **single source of truth** for all environment variables, feature flags, and runtime configuration, with validation enforced in CI/CD pipelines.

**Key Components:**
- **Config Inventory**: `agents/config/inventory.py` (36 variables tracked)
- **Validation Script**: `scripts/check_config_all.py` (exit 0=valid, 1=invalid)
- **Make Target**: `make check-config` (local + CI usage)
- **CI Integration**: Automatic validation in `arv-check` job

---

## Configuration Architecture

### 1. Single Source of Truth

All environment variables are enumerated in **`agents/config/inventory.py`**:

```python
@dataclass
class EnvVarSpec:
    """Specification for a single environment variable."""
    name: str                          # Variable name
    required: bool                     # Always required?
    default: Optional[str]             # Default value
    description: str                   # Human-readable description
    category: VarCategory              # Classification
    envs: List[Environment]            # Applicable environments
    required_when: Optional[str]       # Conditional requirement
    deprecated: bool                   # Deprecation status
    canonical_replacement: Optional[str]  # Replacement var
```

**Total Variables Tracked:** 36
**Categories:** 7 (core, rag, features, storage, notifications, github, slack_bot)

### 2. Variable Categories

#### Core Variables (8 vars)
**Purpose:** Essential GCP and application configuration

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `PROJECT_ID` | Yes | - | GCP project ID |
| `LOCATION` | Yes | us-central1 | GCP region |
| `AGENT_SPIFFE_ID` | Yes | - | SPIFFE identity |
| `DEPLOYMENT_ENV` | No | dev | Environment (dev/staging/prod) |
| `APP_NAME` | No | bobs-brain | Application name |
| `APP_VERSION` | No | 0.8.0 | Application version |
| `AGENT_ENGINE_ID` | No | - | Agent Engine ID |
| `PUBLIC_URL` | No | - | Public A2A endpoint |

#### RAG Variables (5 vars)
**Purpose:** Vertex AI Search datastores per environment

- `VERTEX_SEARCH_PROJECT_ID`
- `VERTEX_SEARCH_LOCATION`
- `VERTEX_SEARCH_DATASTORE_ID_DEV`
- `VERTEX_SEARCH_DATASTORE_ID_STAGING`
- `VERTEX_SEARCH_DATASTORE_ID_PROD`

**Conditional Requirement:**
Required when `LIVE_RAG_BOB_ENABLED=true` OR `LIVE_RAG_FOREMAN_ENABLED=true`

#### Feature Flags (9 vars)
**Purpose:** Control rollout of LIVE1-3, RAG, Agent Engine, Blue/Green features

**All default to FALSE for safety:**

| Feature Flag | Phase | Description |
|--------------|-------|-------------|
| `LIVE_RAG_BOB_ENABLED` | LIVE2 | Enable RAG for Bob |
| `LIVE_RAG_FOREMAN_ENABLED` | LIVE2 | Enable RAG for foreman |
| `ENGINE_MODE_FOREMAN_TO_IAM_ADK` | LIVE2 | A2A via Agent Engine |
| `ENGINE_MODE_FOREMAN_TO_IAM_ISSUE` | LIVE2 | A2A via Agent Engine |
| `ENGINE_MODE_FOREMAN_TO_IAM_FIX` | LIVE2 | A2A via Agent Engine |
| `SLACK_SWE_PIPELINE_MODE_ENABLED` | LIVE3 | Slack → A2A gateway |
| `AGENT_ENGINE_BOB_NEXT_GEN_ENABLED` | Blue/Green | Next-gen routing |
| `AGENT_ENGINE_BOB_NEXT_GEN_PERCENT` | Blue/Green | Traffic % (0-100) |
| `BLUE_GREEN_SHADOW_TRAFFIC_ENABLED` | Blue/Green | Shadow traffic |

#### Storage Variables (2 vars)
**Purpose:** Org-wide GCS bucket (LIVE1-GCS)

- `ORG_STORAGE_BUCKET` (optional)
- `ORG_STORAGE_WRITE_ENABLED` (default: false)

**Conditional Requirement:**
`ORG_STORAGE_BUCKET` required when `ORG_STORAGE_WRITE_ENABLED=true`

#### Notification Variables (3 vars)
**Purpose:** Slack notifications (LIVE3A)

- `SLACK_NOTIFICATIONS_ENABLED` (default: false)
- `SLACK_SWE_CHANNEL_WEBHOOK_URL` (preferred)
- `SLACK_SWE_CHANNEL_ID` (alternative)

**Conditional Requirement:**
Webhook URL OR Channel ID required when `SLACK_NOTIFICATIONS_ENABLED=true`

#### GitHub Variables (4 vars)
**Purpose:** GitHub issue creation (LIVE3B)

- `GITHUB_TOKEN` (optional)
- `GITHUB_ISSUE_CREATION_ENABLED` (default: false)
- `GITHUB_ISSUE_CREATION_ALLOWED_REPOS` (allowlist)
- `GITHUB_ISSUES_DRY_RUN` (default: true)

**Conditional Requirement:**
`GITHUB_TOKEN` required when `GITHUB_ISSUE_CREATION_ENABLED=true`

#### Slack Bot Variables (4 vars)
**Purpose:** Slack integration (separate from notifications)

- `SLACK_BOT_TOKEN`
- `SLACK_SIGNING_SECRET`
- `SLACK_APP_ID`
- `SLACK_WEBHOOK_URL` (deprecated → use `SLACK_SWE_CHANNEL_WEBHOOK_URL`)

---

## Validation System

### 1. Local Validation

**Command:**
```bash
make check-config
```

**What it does:**
1. Reads current `DEPLOYMENT_ENV` (default: dev)
2. Validates against `agents/config/inventory.py`
3. Checks:
   - Required variables are set
   - Conditional requirements are met (feature flags)
   - No invalid values (e.g., feature flags must be boolean-like)
   - Deprecation warnings

**Exit Codes:**
- `0` = Valid configuration
- `1` = Invalid (missing required vars, invalid values)

**Output Format:**
```
======================================================================
Configuration Validation for Environment: DEV
======================================================================

✅ REQUIRED VARIABLES (3 OK):
   ✓ PROJECT_ID = your-gcp-project-id
   ✓ LOCATION = us-central1
   ✓ AGENT_SPIFFE_ID = spiffe://...

❌ REQUIRED VARIABLES MISSING (1):
   ✗ VERTEX_SEARCH_DATASTORE_ID_DEV
      Required when: LIVE_RAG_*_ENABLED=true

⚠️  DEPRECATED VARIABLES (1):
   ! SLACK_WEBHOOK_URL
      Use instead: SLACK_SWE_CHANNEL_WEBHOOK_URL

SUMMARY:
Required variables: 3/4 OK
❌ Configuration is INVALID for DEV
```

### 2. CI Validation

**Workflow:** `.github/workflows/ci.yml`
**Job:** `arv-check` (Agent Readiness Verification)
**Step:** Runs before ARV minimum and engine flags checks

```yaml
- name: Validate configuration (CONF2)
  run: make check-config
  env:
    DEPLOYMENT_ENV: dev
```

**Blocks CI if:**
- Required variables are missing
- Feature flags have invalid values
- Conditional requirements are not met

---

## Usage Examples

### Development Setup

1. **Copy environment template:**
   ```bash
   cp .env.example .env
   ```

2. **Fill in required values:**
   ```bash
   # Core Configuration
   PROJECT_ID=my-gcp-project
   LOCATION=us-central1
   AGENT_SPIFFE_ID=spiffe://intent.solutions/agent/bobs-brain/dev/us-central1/0.8.0
   ```

3. **Validate configuration:**
   ```bash
   make check-config
   ```

### Enabling RAG (LIVE2)

```bash
# 1. Enable RAG flags
LIVE_RAG_BOB_ENABLED=true
LIVE_RAG_FOREMAN_ENABLED=true

# 2. Provide datastore ID (now REQUIRED)
VERTEX_SEARCH_DATASTORE_ID_DEV=adk-documentation-dev

# 3. Validate
make check-config
```

### Enabling Notifications (LIVE3A)

```bash
# 1. Enable notifications
SLACK_NOTIFICATIONS_ENABLED=true

# 2. Provide webhook URL (now REQUIRED)
SLACK_SWE_CHANNEL_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL

# 3. Validate
make check-config
```

### Enabling GitHub Issues (LIVE3B)

```bash
# 1. Enable issue creation
GITHUB_ISSUE_CREATION_ENABLED=true

# 2. Provide token (now REQUIRED)
GITHUB_TOKEN=ghp_your_token_here

# 3. Set allowlist
GITHUB_ISSUE_CREATION_ALLOWED_REPOS=bobs-brain,test-repo

# 4. Disable dry-run (when ready)
GITHUB_ISSUES_DRY_RUN=false

# 5. Validate
make check-config
```

---

## Safety Principles

### 1. All Features OFF by Default

**Every feature flag and write operation defaults to FALSE/disabled:**

- `LIVE_RAG_*_ENABLED` → false
- `ENGINE_MODE_*` → false
- `ORG_STORAGE_WRITE_ENABLED` → false
- `SLACK_NOTIFICATIONS_ENABLED` → false
- `GITHUB_ISSUE_CREATION_ENABLED` → false
- `GITHUB_ISSUES_DRY_RUN` → true (safe default)

**Rationale:**
Prevents accidental writes, notifications, or resource usage without explicit opt-in.

### 2. Conditional Requirements

**Variables only become required when their feature is enabled:**

| When | Then Required |
|------|---------------|
| `LIVE_RAG_*_ENABLED=true` | `VERTEX_SEARCH_DATASTORE_ID_*` |
| `ORG_STORAGE_WRITE_ENABLED=true` | `ORG_STORAGE_BUCKET` |
| `SLACK_NOTIFICATIONS_ENABLED=true` | `SLACK_SWE_CHANNEL_WEBHOOK_URL` |
| `GITHUB_ISSUE_CREATION_ENABLED=true` | `GITHUB_TOKEN` |

### 3. Environment-Aware Validation

**Different requirements for different environments:**

- **Dev:** Only core vars required (PROJECT_ID, LOCATION, AGENT_SPIFFE_ID)
- **Staging:** Same as dev + staging-specific datastores
- **Prod:** All prod-specific resources required

**Environment Detection:**
`DEPLOYMENT_ENV` → auto-detected from `PROJECT_ID` pattern if not set

---

## Deprecation Policy

### Current Deprecations

| Deprecated | Replacement | Reason |
|------------|-------------|--------|
| `SLACK_WEBHOOK_URL` | `SLACK_SWE_CHANNEL_WEBHOOK_URL` | More explicit naming (LIVE3A) |

**Handling:**
- Validation script warns if deprecated vars are set
- Suggests canonical replacement
- Continues to work (backward compatibility)
- Plan to remove in future version

---

## Integration with ARV Gates

**Config validation is the FIRST ARV gate:**

```
arv-check job:
  1. ✅ Validate configuration (CONF2)
  2. ✅ Check ARV minimum requirements
  3. ✅ Check ARV engine flags (Phase AE3)
```

**Rationale:**
No point checking agent readiness if basic configuration is invalid.

---

## Files Reference

| File | Purpose | Location |
|------|---------|----------|
| Config Inventory | Single source of truth | `agents/config/inventory.py` |
| Validation Script | CI/local validation | `scripts/check_config_all.py` |
| Environment Template | User configuration | `.env.example` |
| Config Modules | Feature-specific config | `agents/config/*.py` |
| CI Workflow | Automated checks | `.github/workflows/ci.yml` |
| Makefile | Developer commands | `Makefile` |

---

## Related Documentation

**Canonical Standards (6767 prefix):**
- `000-DR-STND-arv-minimum-gate.md` - ARV minimum requirements
- `000-DR-STND-live-rag-and-agent-engine-rollout-plan.md` - LIVE1-3 phases
- `000-RB-OPS-adk-department-operations-runbook.md` - Operations

**Phase Documentation:**
- `113-AA-REPT-live1-gcs-implementation.md` - LIVE1-GCS (org storage)
- `NNN-AA-REPT-conf-implementation.md` - This phase (TBD)

---

## Troubleshooting

### "Required variables missing"

**Problem:**
```
❌ REQUIRED VARIABLES MISSING (1):
   ✗ PROJECT_ID
```

**Solution:**
1. Check if `.env` file exists (`cp .env.example .env`)
2. Fill in missing required values
3. Run `make check-config` again

### "Conditional requirement not met"

**Problem:**
```
❌ REQUIRED VARIABLES MISSING (1):
   ✗ VERTEX_SEARCH_DATASTORE_ID_DEV
      Required when: LIVE_RAG_*_ENABLED=true
```

**Solution:**
Either:
- **Option A:** Disable the feature flag (`LIVE_RAG_BOB_ENABLED=false`)
- **Option B:** Provide the required variable (`VERTEX_SEARCH_DATASTORE_ID_DEV=...`)

### "CI fails with config validation"

**Problem:**
CI job `arv-check` fails at "Validate configuration" step

**Solution:**
1. Ensure `.env.example` is up to date with all required vars
2. Check GitHub Secrets contain all required values
3. Verify `DEPLOYMENT_ENV` is set correctly in CI

### "Deprecated variable warning"

**Problem:**
```
⚠️  DEPRECATED VARIABLES (1):
   ! SLACK_WEBHOOK_URL
      Use instead: SLACK_SWE_CHANNEL_WEBHOOK_URL
```

**Solution:**
Update `.env` to use the canonical replacement. Deprecated vars still work but will be removed in future versions.

---

## Version History

- **v1.0** (2025-11-20) - Initial standard
  - Config inventory with 36 variables
  - Validation script and Make target
  - CI integration in ARV gates
  - Safety-first design (all features OFF by default)

---

**Status:** ✅ Active
**Next Review:** After LIVE3 completion
**Maintainer:** Build Captain (bobs-brain repo)

---

**Last Updated:** 2025-11-20
