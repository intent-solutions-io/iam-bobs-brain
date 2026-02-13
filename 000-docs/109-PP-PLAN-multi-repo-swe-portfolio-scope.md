# 109-PP-PLAN-multi-repo-swe-portfolio-scope.md

**Date Created:** 2025-11-20
**Category:** PP - Product & Planning
**Type:** PLAN - Planning Document
**Status:** IN PROGRESS 🟡
**Phase:** PORT1 (Multi-Repo Registry + Config)

---

## Executive Summary

This document defines the **Multi-Repo SWE Portfolio** scope for transforming Bob's Brain from a single-repository IAM department into a **portfolio auditor** capable of analyzing, fixing, and improving multiple product repositories simultaneously.

**Current State:** Bob's Brain operates on a single repository (bobs-brain itself)
**Target State:** Portfolio auditor managing 3+ product repos with aggregated reporting

---

## Motivation

### Why Multi-Repo?

The IAM department was designed as a **reusable template** (see 000-DR-STND-iam-department-template-scope-and-rules, 000-DR-GUIDE-porting-iam-department-to-new-repo, 000-DR-STND-iam-department-integration-checklist) for other product repositories. However, the current implementation has limitations:

1. **Single-Repo Focus:** Pipeline only analyzes the current repository
2. **Manual Switching:** Must run pipeline separately for each repo
3. **No Aggregation:** Can't see portfolio-wide quality metrics
4. **Limited Discovery:** Can't identify cross-repo patterns or issues

### Benefits of Portfolio Auditor

1. **Cross-Repo Visibility:** See quality metrics across entire portfolio
2. **Automated Sweeps:** Run scheduled audits on all repos
3. **Pattern Detection:** Identify common issues across products
4. **Prioritization:** Focus on repos with most critical issues
5. **Scalability:** Add new repos without code changes

---

## Architecture Overview

### Three-Phase Approach

```
PHASE PORT1: Registry + Single-Repo Support
    ↓
PHASE PORT2: Portfolio Orchestrator + Aggregation
    ↓
PHASE PORT3: CI Integration + Slack Notifications
```

---

## PHASE PORT1: Multi-Repo Registry + Config (CURRENT)

### Goal
Enable SWE pipeline to target different repositories by ID from a centralized registry.

### What We Built

#### 1. Repository Registry (`config/repos.yaml`)
**Location:** `config/repos.yaml`

**Structure:**
```yaml
repos:
  - id: bobs-brain
    display_name: "Bob's Brain"
    description: "Primary Bob/IAM department repo"
    local_path: "."  # Current repo
    github_owner: "jeremylongshore"
    github_repo: "bobs-brain"
    default_branch: "main"
    tags: ["adk", "agents", "core", "production"]
    allow_write: false
    arv_profile:
      requires_rag: true
      requires_iam_dept: true
      requires_tests: true
      requires_dual_memory: true
    slack_channel: "#bobs-brain-alerts"

  - id: diagnosticpro
    display_name: "DiagnosticPro"
    description: "DiagnosticPro repair platform"
    local_path: "external"  # Not checked out yet
    github_owner: "TBD"
    github_repo: "diagnostic-platform"
    # ... (see config/repos.yaml for full structure)
```

**Key Fields:**
- `id`: Unique identifier (e.g., "bobs-brain", "diagnosticpro")
- `display_name`: Human-friendly name
- `local_path`: "." (current), "external" (not available), or relative path
- `arv_profile`: Agent Readiness Verification requirements
- `slack_channel`: Notification destination (placeholder)

**Current Repos:**
1. `bobs-brain` - Current repo (local_path=".")
2. `bobs-brain-sandbox` - Sandbox repo (local_path="external")
3. `diagnosticpro` - Product repo (local_path="external")
4. `pipelinepilot` - Product repo (local_path="external")
5. `iam1-template` - Template repo (local_path="external")

#### 2. Registry Loader Module (`agents/config/repos.py`)
**Location:** `agents/config/repos.py`

**Key Components:**
- `RepoConfig` dataclass with metadata fields
- `ARVProfile` dataclass for readiness requirements
- `get_repo_by_id(repo_id)` - Lookup by ID
- `list_repos(tag=None)` - List all or filtered by tag
- Singleton registry with lazy loading

**New Properties:**
- `repo.is_local` - True if repo is available locally
- `repo.is_current_repo` - True if this is "." (current repo)

#### 3. Pipeline Integration (`orchestrator.py`)
**Location:** `agents/iam_senior_adk_devops_lead/orchestrator.py`

**New Function:**
```python
def run_swe_pipeline_for_repo(
    repo_id: str,
    mode: str = "preview",
    task: str = "Audit ADK patterns and compliance",
    env: str = "dev"
) -> PipelineResult
```

**Behavior:**
1. Looks up `repo_id` in registry
2. If not found: Returns error result with `metadata.error="repo_not_found"`
3. If `local_path="external"`: Returns skipped result with `metadata.status="skipped"`
4. If local: Runs full SWE pipeline with ARV profile metadata

**Example Usage:**
```python
# Analyze bobs-brain (local)
result = run_swe_pipeline_for_repo("bobs-brain", mode="preview")
# → Runs full pipeline

# Analyze diagnosticpro (external)
result = run_swe_pipeline_for_repo("diagnosticpro", mode="preview")
# → Returns SKIPPED result

# Analyze non-existent repo
result = run_swe_pipeline_for_repo("fake-repo", mode="preview")
# → Returns ERROR result
```

### Testing

**Test Scenarios:**
1. ✅ Local repo (bobs-brain): Runs full pipeline successfully
2. ✅ External repo (diagnosticpro): Skips with clear message
3. ✅ Non-existent repo: Returns error with helpful guidance

**Test Command:**
```bash
python3 -c "from agents.iam_senior_adk_devops_lead.orchestrator import run_swe_pipeline_for_repo; result = run_swe_pipeline_for_repo('bobs-brain'); print(f'{result.total_issues_found} issues found')"
```

### Commits
- `feat(config): add multi-repo registry with enhanced metadata` (config/repos.yaml, agents/config/repos.py)
- `feat(orchestrator): add run_swe_pipeline_for_repo for multi-repo support` (orchestrator.py)

### Documentation
- `096-DR-STND-repo-registry-and-target-selection.md` (existing, still accurate)
- `109-PP-PLAN-multi-repo-swe-portfolio-scope.md` (this document)

---

## PHASE PORT2: Portfolio Orchestrator + Aggregated Reports (NEXT)

### Goal
Run SWE pipeline across **multiple repos** and produce **aggregated portfolio-level reports**.

### Planned Components

#### 1. Portfolio Orchestrator Module
**Location:** `agents/iam_senior_adk_devops_lead/portfolio_orchestrator.py`

**Key Function:**
```python
def run_portfolio_swe(
    repo_ids: Optional[List[str]] = None,  # If None, run on all local repos
    mode: str = "preview",
    task: str = "Portfolio quality audit",
    env: str = "dev",
    parallel: bool = False
) -> PortfolioResult
```

**Behavior:**
1. If `repo_ids` not specified, get all repos with `local_path != "external"`
2. For each repo:
   - Call `run_swe_pipeline_for_repo(repo_id, mode, task, env)`
   - Capture result
3. Aggregate results into `PortfolioResult`
4. Generate summary statistics

**Planned Aggregation:**
- Total repos analyzed
- Total issues found across all repos
- Issues by severity distribution
- Issues by type distribution
- Compliance scores by repo
- Repo risk ranking (based on issue count, severity, ARV profile)

#### 2. PortfolioResult Dataclass
**Location:** `agents/shared_contracts.py`

**Structure:**
```python
@dataclass
class PerRepoResult:
    """Results for a single repo in portfolio run."""
    repo_id: str
    display_name: str
    status: Literal["completed", "skipped", "error"]
    pipeline_result: Optional[PipelineResult]
    duration_seconds: float
    error_message: Optional[str] = None

@dataclass
class PortfolioResult:
    """Aggregated results from portfolio-wide SWE pipeline run."""
    portfolio_run_id: str  # UUID for this portfolio run
    repos: List[PerRepoResult]

    # Aggregated metrics
    total_repos_analyzed: int
    total_repos_skipped: int
    total_repos_errored: int
    total_issues_found: int
    total_issues_fixed: int

    # Issue breakdown
    issues_by_severity: Dict[str, int]  # {"critical": 5, "high": 10, ...}
    issues_by_type: Dict[str, int]  # {"adk_violation": 8, "missing_doc": 3, ...}

    # Repo rankings
    repos_by_issue_count: List[Tuple[str, int]]  # Sorted descending
    repos_by_compliance_score: List[Tuple[str, float]]  # Sorted ascending

    # Timing
    portfolio_duration_seconds: float
    timestamp: datetime
```

#### 3. Portfolio CLI Script
**Location:** `scripts/run_portfolio_swe.py`

**Usage:**
```bash
# Run on all local repos (default)
python3 scripts/run_portfolio_swe.py

# Run on specific repos
python3 scripts/run_portfolio_swe.py --repos bobs-brain,diagnosticpro

# Run in dry-run mode
python3 scripts/run_portfolio_swe.py --mode dry-run

# Save output to file
python3 scripts/run_portfolio_swe.py --output portfolio-report.json
```

**Features:**
- Rich console output with tables
- JSON export for downstream tools
- Markdown report generation
- Integration with ARV checks (optional)

#### 4. Integration with ARV Minimum
**Location:** `scripts/check_arv_minimum.py`

**Enhancement:**
Add `--portfolio` flag to run ARV checks across all local repos:

```bash
make check-arv-portfolio
# → Runs check_arv_minimum.py --portfolio
```

**Output:**
```
============================================================
ARV MINIMUM GATE CHECK - PORTFOLIO MODE
============================================================
Checking 3 local repositories...

bobs-brain: ✅ PASSED
diagnosticpro: ⚠️  SKIPPED (external)
pipelinepilot: ⚠️  SKIPPED (external)

Portfolio Summary:
  Repos checked: 1
  Repos passed: 1
  Repos failed: 0
  Repos skipped: 2
============================================================
```

### Deliverables

1. `agents/iam_senior_adk_devops_lead/portfolio_orchestrator.py` - Core orchestrator
2. `agents/shared_contracts.py` - Add PortfolioResult + PerRepoResult
3. `scripts/run_portfolio_swe.py` - CLI for running portfolio audits
4. `scripts/check_arv_minimum.py` - Add --portfolio flag
5. `Makefile` - Add `make run-portfolio-audit` target
6. `110-AA-REPT-portfolio-orchestrator-implementation.md` - AAR for PORT2

---

## PHASE PORT3: CI Integration + Slack Shapes (DESIGN ONLY)

### Goal
Design how portfolio auditor integrates with CI/CD and future Slack notifications.

**IMPORTANT:** This phase is **design-only**. No actual Slack webhooks or CI triggers will be implemented.

### Planned Components

#### 1. GitHub Actions Workflow
**Location:** `.github/workflows/portfolio-swe.yml`

**Structure:**
```yaml
name: Portfolio SWE Audit

on:
  workflow_dispatch:  # Manual trigger
    inputs:
      repos:
        description: 'Repo IDs to audit (comma-separated, or "all")'
        required: false
        default: 'all'
      mode:
        description: 'Pipeline mode'
        required: false
        default: 'preview'
        type: choice
        options:
          - preview
          - dry-run
          - create

  schedule:
    - cron: '0 0 * * 1'  # Weekly on Monday at midnight (optional, commented out)

jobs:
  portfolio-audit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run portfolio audit
        run: |
          python3 scripts/run_portfolio_swe.py \
            --repos ${{ github.event.inputs.repos || 'all' }} \
            --mode ${{ github.event.inputs.mode || 'preview' }} \
            --output portfolio-report.json
      - name: Upload report artifact
        uses: actions/upload-artifact@v3
        with:
          name: portfolio-report
          path: portfolio-report.json
```

**Triggers:**
- **Manual:** `workflow_dispatch` with repo/mode inputs
- **Scheduled:** Weekly audit (commented out by default)
- **Pull Request:** (Future) Run on PRs that modify multiple repos

#### 2. Slack-Friendly Output Shape (Design Only)
**Location:** Design in `111-AT-ARCH-portfolio-ci-slack-integration-design.md`

**Slack Message Structure:**
```json
{
  "blocks": [
    {
      "type": "header",
      "text": {
        "type": "plain_text",
        "text": "🔍 Portfolio SWE Audit Complete"
      }
    },
    {
      "type": "section",
      "fields": [
        {"type": "mrkdwn", "text": "*Repos Analyzed:* 3"},
        {"type": "mrkdwn", "text": "*Total Issues:* 47"},
        {"type": "mrkdwn", "text": "*Issues Fixed:* 12"},
        {"type": "mrkdwn", "text": "*Duration:* 2.3s"}
      ]
    },
    {
      "type": "section",
      "text": {
        "type": "mrkdwn",
        "text": "*Top Issues:*\n• bobs-brain: 25 issues (🔴 High priority)\n• diagnosticpro: 15 issues\n• pipelinepilot: 7 issues"
      }
    },
    {
      "type": "actions",
      "elements": [
        {
          "type": "button",
          "text": {"type": "plain_text", "text": "View Full Report"},
          "url": "https://github.com/jeremylongshore/bobs-brain/actions/runs/12345"
        }
      ]
    }
  ]
}
```

**Key Principles:**
- Use Slack Block Kit for rich formatting
- Include portfolio summary at top
- Show per-repo breakdown
- Link to full CI report
- Include severity/priority indicators

**NO IMPLEMENTATION:** This is design-only. Actual Slack integration is blocked until later phases.

#### 3. Design Document
**Location:** `111-AT-ARCH-portfolio-ci-slack-integration-design.md`

**Contents:**
- GitHub Actions workflow design
- Slack message formats (for all result types)
- Integration points with existing systems
- Safety/rollout plan
- Future enhancements

#### 4. Documentation Updates
**Locations:**
- `README.md` - Add portfolio auditor section
- `CLAUDE.md` - Update with portfolio commands
- `000-docs/000-RB-OPS-adk-department-operations-runbook-RB-OPS-adk-department-operations-runbook.md` - Add portfolio operations

### Deliverables

1. `.github/workflows/portfolio-swe.yml` - Workflow definition
2. `111-AT-ARCH-portfolio-ci-slack-integration-design.md` - Design doc
3. `README.md` - Portfolio section
4. `CLAUDE.md` - Portfolio usage instructions
5. Update existing runbooks with portfolio info

---

## Repository Scope

### Initial Portfolio (Phase PORT1)

| Repo ID | Display Name | Local Path | Status | Priority |
|---------|-------------|------------|--------|----------|
| bobs-brain | Bob's Brain | `.` | ✅ Active | High |
| bobs-brain-sandbox | Sandbox | `external` | ⏳ External | Low |
| diagnosticpro | DiagnosticPro | `external` | ⏳ External | Medium |
| pipelinepilot | PipelinePilot | `external` | ⏳ External | Medium |
| iam1-template | IAM1 Template | `external` | ⏳ External | Low |

### Adding New Repos

**Process:**
1. Add entry to `config/repos.yaml`
2. Set `local_path` appropriately:
   - `"."` if current repo
   - `"../other-repo"` if checked out locally
   - `"external"` if not available
3. Configure `arv_profile` based on repo requirements
4. Set `slack_channel` placeholder
5. Test with `run_swe_pipeline_for_repo(new_repo_id)`

**Example:**
```yaml
- id: new-product
  display_name: "New Product"
  description: "New product repository"
  local_path: "../new-product"  # Relative path from bobs-brain
  github_owner: "jeremylongshore"
  github_repo: "new-product"
  default_branch: "main"
  tags: ["product", "firebase"]
  allow_write: false
  arv_profile:
    requires_rag: false
    requires_iam_dept: true  # Will port IAM department template
    requires_tests: true
  slack_channel: "#new-product-alerts"
```

---

## Success Criteria

### PORT1 (Current Phase)
- ✅ Registry with 5+ repos defined
- ✅ Registry loader module with `get_repo_by_id()` and `list_repos()`
- ✅ `run_swe_pipeline_for_repo()` function
- ✅ Local repos run successfully
- ✅ External repos skip gracefully
- ✅ Non-existent repos return clear errors
- 🟡 Plan doc created (this document)

### PORT2 (Next Phase)
- [ ] `run_portfolio_swe()` function
- [ ] `PortfolioResult` + `PerRepoResult` dataclasses
- [ ] Portfolio CLI script
- [ ] ARV portfolio mode
- [ ] JSON/Markdown report export
- [ ] AAR doc created

### PORT3 (Design Phase)
- [ ] GitHub Actions workflow designed
- [ ] Slack message shapes documented
- [ ] Integration design doc created
- [ ] README/CLAUDE updated with portfolio info

---

## Timeline

| Phase | Duration | Status | Deliverables |
|-------|----------|--------|--------------|
| PORT1 | 1-2 days | ✅ COMPLETE | Registry + single-repo support |
| PORT2 | 2-3 days | ⏳ PENDING | Portfolio orchestrator + aggregation |
| PORT3 | 1-2 days | ⏳ PENDING | CI design + Slack shapes (design only) |

**Total Estimated:** 4-7 days

---

## Risks & Mitigations

### Risk 1: External Repos Not Available
**Impact:** Can't test portfolio features on real multi-repo scenarios
**Mitigation:** Use synthetic test fixtures and stubs for external repos

### Risk 2: Performance with Many Repos
**Impact:** Portfolio audit may be slow with 10+ repos
**Mitigation:**
- Implement parallel execution in PORT2
- Add timeout/cancellation support
- Cache results for unchanged repos

### Risk 3: Conflicting ARV Requirements
**Impact:** Different repos may have incompatible ARV profiles
**Mitigation:**
- Document ARV profile standards in 000-DR-STND-arv-minimum-gate
- Validate new repos against standards before adding to registry
- Allow per-repo ARV overrides in portfolio config

---

## Future Enhancements (Post-PORT3)

### Multi-Workspace Support
- Support repos in different directories/workspaces
- Git worktree integration for parallel checkouts

### Smart Repo Selection
- Auto-detect repos that need attention based on:
  - Time since last audit
  - Recent commit activity
  - Known issues
  - ARV profile changes

### Portfolio Dashboard
- Web UI for viewing portfolio health
- Historical trend charts
- Drill-down into per-repo details

### Cross-Repo Pattern Detection
- Identify common anti-patterns across repos
- Suggest global fixes
- Template synchronization

---

## Related Documentation

### Existing Standards
- `093-DR-STND-bob-rag-readiness-standard.md` - RAG readiness (Phase RC1)
- `094-AT-ARCH-iam-swe-pipeline-orchestration.md` - Pipeline architecture
- `096-DR-STND-repo-registry-and-target-selection.md` - Registry standard
- `000-DR-STND-arv-minimum-gate-DR-STND-arv-minimum-gate-for-bobs-brain.md` - ARV minimum gate
- `000-DR-STND-iam-department-template-scope-and-rules-DR-STND-iam-department-template-scope-and-rules.md` - Template scope
- `000-RB-OPS-adk-department-operations-runbook-RB-OPS-adk-department-operations-runbook.md` - Operations runbook

### PORT Phase Docs (This Series)
- `109-PP-PLAN-multi-repo-swe-portfolio-scope.md` - This document (PORT1 plan)
- `110-AA-REPT-portfolio-orchestrator-implementation.md` - PORT2 AAR (future)
- `111-AT-ARCH-portfolio-ci-slack-integration-design.md` - PORT3 design (future)

---

## Summary

The Multi-Repo SWE Portfolio transforms Bob's Brain from a single-repository IAM department into a comprehensive portfolio auditor capable of:

✅ **PORT1 Complete:**
- Centralized repository registry with rich metadata
- Local path awareness (current, relative, external)
- Single-repo pipeline function with graceful skipping
- Foundation for portfolio-level operations

🟡 **PORT2 In Progress:**
- Portfolio orchestrator for multi-repo audits
- Aggregated quality metrics and reporting
- CLI for running portfolio sweeps
- ARV portfolio mode

⏳ **PORT3 Planned:**
- CI/CD integration design
- Slack notification shapes (design only)
- Documentation updates

This enables the IAM department to scale from maintaining one repo to managing an entire portfolio of products, with comprehensive visibility and automated quality gates.

---

**Document Version:** 1.0.0
**Last Updated:** 2025-11-20
**Status:** In Progress (PORT1 Complete, PORT2/PORT3 Pending)
**Owner:** iam-senior-adk-devops-lead
**Phase:** PORT1 → PORT2 → PORT3

---

**Timestamp:** 2025-11-20T03:50:00Z
