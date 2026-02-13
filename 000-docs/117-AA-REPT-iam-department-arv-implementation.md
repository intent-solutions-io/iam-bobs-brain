# IAM Department ARV Implementation

**Document Number:** 117-AA-REPT-iam-department-arv-implementation
**Status:** Active
**Date:** 2025-11-20
**Phase:** ARV-DEPT (Agent Readiness Verification - Department)
**Author:** Build Captain (Claude)

---

## Executive Summary

This document defines the Agent Readiness Verification (ARV) framework for the IAM/ADK department in Bob's Brain. ARV provides a comprehensive, single-command readiness check that validates configuration, tests, RAG, Agent Engine, storage, and notification infrastructure.

**Key Achievement:**
- ✅ Single command (`make arv-department`) runs 7 comprehensive checks
- ✅ CI-enforced readiness gate blocks bad merges
- ✅ Reusable pattern for other departments

**ARV Status:** 7 checks defined, 4 required, 3 optional (feature-gated)

---

## What Is ARV?

**Agent Readiness Verification (ARV)** is a framework that answers: **"Is this department ready to run?"**

### Design Principles

1. **Comprehensive** - Validates all aspects (config, tests, features)
2. **Environment-Aware** - Different requirements for dev/staging/prod
3. **Feature-Gated** - Optional checks only run when features enabled
4. **CI-Enforced** - Blocks merges when readiness fails
5. **Developer-Friendly** - Clear pass/fail output with details

### ARV vs Individual Checks

**Before ARV-DEPT:**
```bash
# Must run 5+ separate checks
make check-config
make check-arv-minimum
make check-arv-engine-flags
make check-rag-readiness
pytest tests/unit
```

**After ARV-DEPT:**
```bash
# One command runs all checks
make arv-department
```

---

## ARV Checklist

### 7 Checks Across 5 Categories

#### CONFIG (1 check)
| ID | Description | Required | Command |
|----|-------------|----------|---------|
| `config-basic` | Environment configuration validation | ✅ Yes | `check_config_all.py` |

**Purpose:** Validates all 36 environment variables against inventory, checks conditional requirements

#### TESTS (2 checks)
| ID | Description | Required | Command |
|----|-------------|----------|---------|
| `tests-unit` | Unit tests for agents | ✅ Yes | `pytest tests/unit` |
| `tests-swe-pipeline` | Portfolio/SWE pipeline tests | ✅ Yes | `pytest test_swe_pipeline.py` |

**Purpose:** Ensures code quality and pipeline functionality

#### RAG (1 check)
| ID | Description | Required | Command |
|----|-------------|----------|---------|
| `rag-readiness` | RAG config and Vertex AI Search | ⚠️ Conditional | `check_rag_readiness.py` |

**Required When:** `LIVE_RAG_BOB_ENABLED=true` OR `LIVE_RAG_FOREMAN_ENABLED=true`
**Purpose:** Validates Vertex AI Search connectivity, datastore config, query smoke test

#### ENGINE (2 checks)
| ID | Description | Required | Command |
|----|-------------|----------|---------|
| `engine-flags-safety` | Agent Engine flags safety | ✅ Yes | `check_arv_engine_flags.py` |
| `arv-minimum-requirements` | Minimum structural requirements | ✅ Yes | `check_arv_minimum.py` |

**Purpose:** Validates Engine flag configurations and agent structural integrity

#### STORAGE (1 check)
| ID | Description | Required | Command |
|----|-------------|----------|---------|
| `storage-readiness` | Org-wide GCS storage | ⚠️ Conditional | `check_org_storage_readiness.py` |

**Required When:** `ORG_STORAGE_WRITE_ENABLED=true`
**Purpose:** Validates GCS bucket connectivity and write permissions

---

## How It Works

### Architecture

```
make arv-department
    ↓
scripts/run_arv_department.py
    ↓
agents/arv/spec.py (checklist definition)
    ↓
agents/arv/check_impl.py (execution logic)
    ↓
Existing scripts (subprocess calls)
    ↓
ArvResult (pass/fail + details)
```

### Execution Flow

1. **Load Checklist** - Read checks from `agents/arv/spec.py`
2. **Filter by Environment** - Apply env-specific requirements
3. **Check Conditions** - Evaluate feature flag requirements
4. **Execute Checks** - Run each applicable check via subprocess
5. **Collect Results** - Gather pass/fail status and details
6. **Print Report** - Grouped by category with clear status
7. **Exit Code** - 0 if all required checks passed, 1 if any failed

### Conditional Logic

**Example: RAG Check**
```python
# If RAG flags are OFF, check is SKIPPED
if not (LIVE_RAG_BOB_ENABLED or LIVE_RAG_FOREMAN_ENABLED):
    return ArvResult(passed=True, skipped=True, details="RAG not enabled")

# If RAG flags are ON, check is REQUIRED
else:
    run check_rag_readiness.py
    return ArvResult based on exit code
```

---

## Usage

### Local Development

**Run all checks:**
```bash
make arv-department
```

**Run with verbose output:**
```bash
make arv-department-verbose
```

**List all checks:**
```bash
make arv-department-list
```

**Run specific category:**
```bash
python3 scripts/run_arv_department.py --category config
python3 scripts/run_arv_department.py --category tests
```

**Check different environment:**
```bash
DEPLOYMENT_ENV=staging make arv-department
```

### CI/CD

**Automatic Execution:**
- Runs on every push to `main`, `develop`, `feature/**`
- Runs on all PRs to `main` and `develop`
- Blocks CI if any required check fails

**Workflow:** `.github/workflows/ci.yml`
**Job:** `arv-department`
**Trigger:** After `drift-check` passes

```yaml
arv-department:
  needs: drift-check
  steps:
    - name: Run ARV Department Check
      run: make arv-department
      env:
        DEPLOYMENT_ENV: dev
```

### Before Deploying

**Recommended Workflow:**
1. Make changes to agents/config/features
2. Run `make arv-department` locally
3. Fix any failures
4. Commit and push
5. CI runs ARV automatically
6. Merge when CI passes

---

## Output Format

### Example Success (All Required Checks Passed)

```
======================================================================
ARV – IAM/ADK Department Readiness Verification
======================================================================
Environment: DEV

Running 7 checks...

[CONFIG] Configuration validation (env vars, feature flags)
  ✅ config-basic – PASSED

[TESTS] Test suite execution (unit, integration, pipeline)
  ✅ tests-unit – PASSED
  ✅ tests-swe-pipeline – PASSED

[RAG] RAG (Vertex AI Search) readiness and connectivity
  ⚠️ rag-readiness – SKIPPED
     SKIPPED: LIVE_RAG_BOB_ENABLED=true OR LIVE_RAG_FOREMAN_ENABLED=true

[ENGINE] Agent Engine structural requirements and flags
  ✅ engine-flags-safety – PASSED
  ✅ arv-minimum-requirements – PASSED

[STORAGE] GCS storage connectivity and permissions
  ⚠️ storage-readiness – SKIPPED
     SKIPPED: ORG_STORAGE_WRITE_ENABLED=true

======================================================================
SUMMARY
======================================================================
Total checks:    7
  Passed:        4
  Failed:        0
  Skipped:       3

Required checks: 4
  Passed:        4
  Failed:        0

✅ RESULT: PASSED

All 4 required checks passed.
3 optional checks were skipped (feature flags disabled).
======================================================================
```

### Example Failure (Config Missing)

```
======================================================================
ARV – IAM/ADK Department Readiness Verification
======================================================================
Environment: DEV

Running 7 checks...

[CONFIG] Configuration validation (env vars, feature flags)
  ❌ config-basic – FAILED
     Exit code: 1

[TESTS] Test suite execution (unit, integration, pipeline)
  ✅ tests-unit – PASSED
  ✅ tests-swe-pipeline – PASSED

...

======================================================================
SUMMARY
======================================================================
Total checks:    7
  Passed:        3
  Failed:        1
  Skipped:       3

Required checks: 4
  Passed:        3
  Failed:        1

❌ RESULT: FAILED

1 required checks failed.
Fix the failures above before proceeding.
======================================================================
```

---

## Adding New Checks

### Step 1: Define Check in `agents/arv/spec.py`

```python
ArvCheck(
    id="new-check-id",
    description="What this check validates",
    category="config",  # or tests, rag, engine, storage, notifications
    required=True,  # or False for conditional checks
    command="python3 scripts/check_new_thing.py",
    required_when="SOME_FLAG=true",  # Optional condition
    envs=["dev", "staging", "prod"],  # Applicable environments
)
```

### Step 2: Update Conditional Logic (if needed)

If the check is conditional, update `agents/arv/check_impl.py`:

```python
def check_conditional_requirement(check: ArvCheck) -> tuple[bool, str]:
    # ... existing conditions ...

    if "SOME_FLAG=true" in condition and is_feature_flag_enabled("SOME_FLAG"):
        return True, "SOME_FLAG is enabled"
```

### Step 3: Test Locally

```bash
make arv-department-list  # Verify check appears
make arv-department        # Run full suite
```

### Step 4: Update Documentation

Add the new check to this document's checklist section.

---

## Troubleshooting

### "Required check failed: config-basic"

**Problem:** Configuration validation failed

**Solution:**
1. Run `make check-config` directly to see details
2. Check `.env` file has all required variables
3. Verify feature flag dependencies are met
4. See `116-DR-STND-config-and-feature-flags-standard-v1.md`

### "Required check failed: tests-unit"

**Problem:** Unit tests failed

**Solution:**
1. Run `pytest tests/unit -v` to see specific failures
2. Fix failing tests
3. Re-run `make arv-department`

### "Check timed out after 5 minutes"

**Problem:** A check is taking too long

**Solution:**
1. Investigate the specific check that timed out
2. Check for infinite loops or hanging processes
3. Consider optimizing the check or increasing timeout

### "Skipped checks not running when flag enabled"

**Problem:** Conditional check still skipped despite flag being ON

**Solution:**
1. Verify flag is set: `echo $LIVE_RAG_BOB_ENABLED`
2. Check flag value is exactly `true` (case-sensitive)
3. Run with verbose: `make arv-department-verbose`
4. Check `agents/arv/check_impl.py` condition logic

---

## Files Reference

| File | Purpose | Location |
|------|---------|----------|
| ARV Spec | Check definitions | `agents/arv/spec.py` |
| Check Implementation | Execution logic | `agents/arv/check_impl.py` |
| ARV Runner | Main script | `scripts/run_arv_department.py` |
| Makefile Targets | Commands | `Makefile` (arv-department targets) |
| CI Workflow | Automation | `.github/workflows/ci.yml` |

---

## Operator Playbook

### Daily Operations

**Before Merging to Main:**
```bash
# 1. Run ARV locally
make arv-department

# 2. If failures, fix them
make check-config           # Fix config issues
pytest tests/unit           # Fix test failures

# 3. Re-run ARV
make arv-department

# 4. When PASSED, commit and push
git add .
git commit -m "fix: resolve ARV failures"
git push
```

### When CI Fails ARV

1. **View CI logs** - Check GitHub Actions for specific failure
2. **Reproduce locally** - Run `make arv-department` in same environment
3. **Fix root cause** - Address the specific failing check
4. **Push fix** - CI will re-run ARV automatically

### Feature Flag Rollout

**When enabling a new feature:**

1. **Update flags** in `.env`:
   ```bash
   LIVE_RAG_BOB_ENABLED=true
   ```

2. **Run ARV** to verify new requirements:
   ```bash
   make arv-department
   # Now RAG checks become REQUIRED
   ```

3. **Fix any new failures** (e.g., missing datastore IDs)

4. **Deploy when ARV passes**

---

## Relationship to Other ARV Checks

### Existing Individual Checks

These checks still exist and can be run individually:

- `make check-config` - Config validation only
- `make check-rag-readiness` - RAG only
- `make check-arv-minimum` - Minimum requirements only
- `make check-arv-engine-flags` - Engine flags only

### Unified ARV vs Individual Checks

**Use `make arv-department` when:**
- Verifying overall readiness before merge/deploy
- Running in CI as comprehensive gate
- Checking after major changes

**Use individual checks when:**
- Debugging specific failure
- Iterating on single feature (RAG, config, etc.)
- Quick smoke test

---

## Related Documentation

**Canonical Standards (6767 prefix):**
- `000-DR-STND-arv-minimum-gate.md` - ARV minimum requirements
- `000-DR-STND-iam-department-integration-checklist.md` - Department integration
- `000-RB-OPS-adk-department-operations-runbook.md` - Operations

**Repo-Local Documentation:**
- `116-DR-STND-config-and-feature-flags-standard-v1.md` - Config standard
- This doc (`117`) - ARV implementation

**Code:**
- `agents/arv/` - ARV framework modules
- `scripts/run_arv_department.py` - Main runner

---

## Version History

- **v1.0** (2025-11-20) - Initial ARV-DEPT implementation
  - 7 checks across 5 categories
  - 4 required, 3 optional (feature-gated)
  - CI integration complete
  - Make targets added

---

## Future Enhancements

**Planned:**
- [ ] Add notification checks (Slack/GitHub dry-run)
- [ ] Add staging/prod environment variants
- [ ] Add performance benchmarks (check execution time)
- [ ] Add ARV history tracking (pass rate over time)
- [ ] Add --fix mode (attempt automatic fixes)

**Considered:**
- Portfolio-wide ARV (run across multiple repos)
- ARV dashboard (web UI for results)
- ARV badges (GitHub README status)

---

**Status:** ✅ Active
**Next Review:** After LIVE3 completion
**Maintainer:** Build Captain (bobs-brain repo)

---

**Last Updated:** 2025-11-20
