# 000-DR-STND-github-issue-creation-guardrails-DR-STND-github-issue-creation-guardrails.md

**Date Created:** 2025-11-20
**Category:** DR - Documentation & Reference
**Type:** STND - Standard
**Status:** ACTIVE ✅

---

## Executive Summary

Establishes comprehensive safety guardrails for GitHub issue creation in the SWE pipeline. All write operations are **disabled by default** and require explicit feature flags, repository allowlists, and authentication.

---

## Purpose

Phase GHC extends the SWE pipeline with **guarded GitHub issue creation** while maintaining strict safety controls:

- **Default behavior:** Preview mode (no creation)
- **Safety layers:** Feature flags + allowlists + authentication
- **Operational modes:** Preview, dry-run, and create
- **Fail-safe design:** Multiple checks prevent accidental creation

---

## Architecture

###Safety Layers

```
Pipeline Request (mode = "create")
    ↓
Safety Check 1: Feature Flag Enabled?
    ↓ (No) → Block with message
Safety Check 2: Repo in Allowlist?
    ↓ (No) → Block with message
Safety Check 3: GitHub Token Present?
    ↓ (No) → Block with message
Safety Check 4: Valid Permissions?
    ↓ (No) → API error
✅ All Passed → Create Issue
```

### Components

1. **GitHubClient.create_issue()** - Low-level API wrapper
2. **Feature flag system** - Configuration layer
3. **Pipeline modes** - User-facing controls
4. **CLI integration** - Accessible interface

---

## Feature Flag System

### Configuration

**Module:** `agents/config/github_features.py`

**Environment Variables:**

```bash
# Master switch (default: false)
GITHUB_ISSUE_CREATION_ENABLED=false

# Allowlist (default: empty = no repos)
GITHUB_ISSUE_CREATION_ALLOWED_REPOS=
```

### Examples

**Disabled (default - safe mode):**
```bash
# No configuration needed - disabled by default
export GITHUB_ISSUE_CREATION_ENABLED=false
export GITHUB_ISSUE_CREATION_ALLOWED_REPOS=
```

**Enabled for specific repos:**
```bash
export GITHUB_ISSUE_CREATION_ENABLED=true
export GITHUB_ISSUE_CREATION_ALLOWED_REPOS=bobs-brain,test-repo
```

**Enabled for all repos (use with extreme caution):**
```bash
export GITHUB_ISSUE_CREATION_ENABLED=true
export GITHUB_ISSUE_CREATION_ALLOWED_REPOS=*
```

### Python API

```python
from agents.config.github_features import (
    can_create_issues_for_repo,
    get_feature_status_summary
)

# Check if creation is allowed
if can_create_issues_for_repo("bobs-brain"):
    # Safe to create issues
    pass
else:
    # Blocked by feature flags
    pass

# Get human-readable status
status = get_feature_status_summary()
print(status['message'])
# "🚫 GitHub issue creation is DISABLED (safe mode)"
```

---

## Pipeline Modes

### Mode: `preview` (Default)

**Behavior:**
- Issues identified but NOT created
- Shows helpful hints about other modes
- **Zero risk** - no GitHub API calls

**When to use:**
- Default for all pipelines
- Testing and development
- When you just want to see what issues exist

**Example:**
```bash
python3 scripts/run_swe_pipeline_once.py \
  --repo-id bobs-brain \
  --mode preview
```

**Output:**
```
🐙 GITHUB ISSUE HANDLING
Mode: preview
Repository: jeremylongshore/bobs-brain
✓ Preview mode: Issues identified but not created on GitHub
  Run with --mode=dry-run to see GitHub issue payloads
  Run with --mode=create to create issues (requires feature flags)
```

---

### Mode: `dry-run`

**Behavior:**
- Converts IssueSpecs to GitHub payloads
- Shows exactly what would be created
- **Zero risk** - no GitHub API calls

**When to use:**
- Verify issue formatting before creation
- Review labels and assignments
- Test adapter logic

**Example:**
```bash
python3 scripts/run_swe_pipeline_once.py \
  --repo-id bobs-brain \
  --mode dry-run
```

**Output:**
```
🐙 GITHUB ISSUE HANDLING
Mode: dry-run
Repository: jeremylongshore/bobs-brain
🔍 Dry-run mode: Showing GitHub issue payloads (no creation)

Issue 1/3:
============================================================
Title: Fix ADK agent initialization pattern
Labels: severity: high, priority: high, adk, compliance, bug
------------------------------------------------------------
## Fix ADK agent initialization pattern

### Summary
Found violation of ADK agent initialization pattern...

### Location
**File:** `agents/example/agent.py`
**Lines:** 42-55
...
============================================================

✓ Dry-run complete. No issues were created.
  To actually create issues, use --mode=create with proper feature flags
```

---

### Mode: `create`

**Behavior:**
- **Checks ALL safety layers**
- Creates issues on GitHub if all checks pass
- Provides detailed error messages if blocked

**When to use:**
- Production pipeline runs
- When you actually want to create tracked issues
- After verifying with dry-run mode

**Safety checks performed:**
1. Feature flag enabled?
2. Repo in allowlist?
3. GitHub token present?
4. API permissions valid?

**Example:**
```bash
# Set feature flags first!
export GITHUB_ISSUE_CREATION_ENABLED=true
export GITHUB_ISSUE_CREATION_ALLOWED_REPOS=bobs-brain
export GITHUB_TOKEN=ghp_your_token_here

python3 scripts/run_swe_pipeline_once.py \
  --repo-id bobs-brain \
  --mode create
```

**Output (success):**
```
🐙 GITHUB ISSUE HANDLING
Mode: create
Repository: jeremylongshore/bobs-brain
🚀 Create mode: Attempting to create GitHub issues...
✅ Safety checks passed. Creating 3 issues...

  ✅ Created issue #42: Fix ADK agent initialization pattern
     https://github.com/jeremylongshore/bobs-brain/issues/42
  ✅ Created issue #43: Update tool wiring for Memory Bank
     https://github.com/jeremylongshore/bobs-brain/issues/43
  ✅ Created issue #44: Add missing AAR documentation
     https://github.com/jeremylongshore/bobs-brain/issues/44

✓ Created 3/3 GitHub issues
```

**Output (blocked by feature flags):**
```
🐙 GITHUB ISSUE HANDLING
Mode: create
Repository: jeremylongshore/bobs-brain
🚀 Create mode: Attempting to create GitHub issues...
❌ GitHub issue creation BLOCKED by feature flags

   🚫 GitHub issue creation is DISABLED (safe mode)
   💡 Set GITHUB_ISSUE_CREATION_ENABLED=true to enable
   ℹ️  Add 'bobs-brain' to GITHUB_ISSUE_CREATION_ALLOWED_REPOS

✓ Issues identified but not created (blocked by safety)
```

**Output (missing token):**
```
🐙 GITHUB ISSUE HANDLING
Mode: create
Repository: jeremylongshore/bobs-brain
🚀 Create mode: Attempting to create GitHub issues...
❌ GitHub token not found
   Set GITHUB_TOKEN environment variable to create issues
✓ Issues identified but not created (no token)
```

---

## GitHub Client API

### create_issue() Method

**Location:** `agents/tools/github_client.py`

**Signature:**
```python
def create_issue(
    self,
    owner: str,
    repo: str,
    payload: Dict[str, Any]
) -> CreatedIssue:
    """
    Create a new issue in a GitHub repository.

    IMPORTANT: This is a WRITE operation.
    Requires authentication and appropriate permissions.
    """
```

**Payload Structure:**
```python
payload = {
    "title": "Issue title (required)",
    "body": "Issue description (optional)",
    "labels": ["bug", "priority: high"],  # Optional
    "assignees": ["jeremylongshore"],     # Optional
    "milestone": 1                         # Optional
}
```

**Returns:**
```python
@dataclass
class CreatedIssue:
    number: int             # Issue number (e.g., 42)
    html_url: str          # Full GitHub URL
    title: str             # Issue title
    state: str             # "open" or "closed"
    body: Optional[str]    # Issue description
    labels: List[str]      # Applied labels
    assignees: List[str]   # Assigned users
```

**Safety Features:**
- Requires GitHub token (fails if missing)
- Validates title field (required)
- Comprehensive error handling
- Returns structured result for tracking

**Example:**
```python
from agents.tools.github_client import get_client

client = get_client()  # Requires GITHUB_TOKEN

payload = {
    "title": "Fix ADK pattern violation",
    "body": "Found non-compliant agent initialization...",
    "labels": ["adk", "bug"]
}

try:
    issue = client.create_issue(
        owner="jeremylongshore",
        repo="bobs-brain",
        payload=payload
    )
    print(f"Created: {issue.html_url}")
except GitHubAuthError as e:
    print(f"Auth failed: {e}")
```

---

## Issue Adapter Integration

### Conversion Flow

```
IssueSpec (internal contract)
    ↓ issue_spec_to_github_payload()
GitHub Payload (API format)
    ↓ client.create_issue()
CreatedIssue (result)
```

**Example:**
```python
from agents.iam_issue.github_issue_adapter import issue_spec_to_github_payload
from agents.tools.github_client import get_client

# Convert IssueSpec to payload
payload = issue_spec_to_github_payload(
    issue=issue_spec,
    assignees=["jeremylongshore"],
    milestone=1
)

# Create on GitHub
client = get_client()
created = client.create_issue(
    owner="jeremylongshore",
    repo="bobs-brain",
    payload=payload
)

print(f"Created issue #{created.number}")
```

---

## Testing

### Test Suite

**Location:** `tests/test_github_features.py`

**Coverage:**
- ✅ Feature flag loading (17 tests)
- ✅ Environment variable parsing
- ✅ Allowlist validation
- ✅ Wildcard handling
- ✅ Safety gate logic
- ✅ Status summary formatting

**Run tests:**
```bash
# All feature flag tests
python3 -m pytest tests/test_github_features.py -v

# With coverage
python3 -m pytest tests/test_github_features.py --cov=agents.config.github_features

# Specific test class
python3 -m pytest tests/test_github_features.py::TestCanCreateIssuesForRepo -v
```

**Test Results:**
```
============================= test session starts ==============================
tests/test_github_features.py::TestGitHubFeatureConfig 3 passed
tests/test_github_features.py::TestLoadGitHubFeatureConfig 6 passed
tests/test_github_features.py::TestCanCreateIssuesForRepo 5 passed
tests/test_github_features.py::TestGetFeatureStatusSummary 3 passed
============================== 17 passed in 0.06s ==============================
```

---

## Best Practices

### Development

1. **Always start in preview mode**
   - Default is safe
   - No risk of accidental creation

2. **Use dry-run before create**
   - Verify payload formatting
   - Check labels and assignments
   - Confirm issue count

3. **Enable feature flags explicitly**
   - Never commit `.env` with enabled flags
   - Use repo-specific allowlists
   - Avoid wildcard in production

### Production

1. **Minimal allowlist**
   - Only repos that need it
   - Review periodically
   - Remove unused repos

2. **Secure token management**
   - Use GitHub Actions secrets
   - Never commit tokens
   - Rotate regularly
   - Minimum required scopes

3. **Monitor creation**
   - Log all creation attempts
   - Track success/failure rates
   - Alert on unexpected patterns

---

## Troubleshooting

### Issue: "GitHub issue creation BLOCKED by feature flags"

**Cause:** Feature flag not enabled or repo not in allowlist

**Solutions:**
```bash
# 1. Enable feature flag
export GITHUB_ISSUE_CREATION_ENABLED=true

# 2. Add repo to allowlist
export GITHUB_ISSUE_CREATION_ALLOWED_REPOS=bobs-brain

# 3. Verify configuration
python3 agents/config/github_features.py
```

---

### Issue: "GitHub token not found"

**Cause:** GITHUB_TOKEN environment variable not set

**Solutions:**
```bash
# 1. Set token
export GITHUB_TOKEN=ghp_your_token_here

# 2. Verify token works
curl -H "Authorization: Bearer $GITHUB_TOKEN" \
  https://api.github.com/user
```

---

### Issue: "Failed to create issue: 403 Forbidden"

**Cause:** Token lacks required permissions

**Solutions:**
1. Generate new token at https://github.com/settings/tokens
2. Required scope: `repo` (or `public_repo` for public repos only)
3. Verify repo access permissions

---

### Issue: "Rate limit exceeded"

**Cause:** Too many API requests

**Solutions:**
- Use authenticated requests (5000/hour vs 60/hour)
- Implement caching for repeated operations
- Batch issue creation
- Wait for rate limit reset (check `X-RateLimit-Reset` header)

---

## Related Documentation

- **Phase GH1:** `096-DR-STND-repo-registry-and-target-selection.md`
- **Phase GH2:** `097-AT-ARCH-github-integration-and-repo-ingest.md`
- **Phase GH3:** `098-AA-REPT-github-integration-phases-gh1-gh2-gh3.md`
- **SWE Pipeline:** `094-AT-ARCH-iam-swe-pipeline-orchestration.md`

---

## Summary

Phase GHC provides **guarded GitHub issue creation** with multiple safety layers:

- ✅ Disabled by default (safe mode)
- ✅ Three operational modes (preview, dry-run, create)
- ✅ Feature flag system with allowlists
- ✅ Token validation and auth checks
- ✅ Comprehensive error handling
- ✅ Full test coverage (17 tests)
- ✅ Clear error messages and hints

**Key Principle:** Multiple independent checks ensure issues are only created when explicitly intended and properly authorized.

---

**Document Version:** 1.0.0
**Last Updated:** 2025-11-20
**Status:** Active
**Owner:** iam-senior-adk-devops-lead

---
