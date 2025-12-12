# Phase 37: Versioning & Tagging Guardrails - AAR

**Date:** 2025-12-12
**Status:** Complete
**Branch:** `feature/phase-37-versioning-guardrails`

## Summary

Established strict versioning and tagging rules for the repository with automated validation via CI. This pattern can be reused in future IAM department repositories.

## What Was Built

### 1. Version Check Script

**File:** `scripts/check_versioning.py`

Features:
- Reads VERSION file and validates SemVer format
- Compares against existing git tags (when available)
- Filters out legacy/special tags (v1.0.0, v5.x, v6.x)
- Handles shallow clones gracefully (format-only validation)
- Clear exit codes for different failure modes

Exit Codes:
- 0: All checks passed
- 1: VERSION file malformed or missing
- 2: Version regression detected

### 2. Make Targets

**File:** `Makefile`

New targets:
- `check-versioning` - Basic versioning check
- `check-versioning-verbose` - Detailed output with tag list

### 3. CI Integration

**File:** `.github/workflows/ci.yml`

Added `versioning-check` job:
- Runs after drift-check
- Uses `fetch-depth: 0` for full clone with tags
- Added to `ci-success` job dependencies

### 4. Runbook Documentation

**File:** `000-docs/206-RB-VERSIONING-bobs-brain-version-and-tagging-playbook.md`

Contents:
- SemVer rules and conventions
- How to bump versions (step-by-step)
- How to create tags
- Script interpretation guide
- Release checklist
- Adapting for other repos

## Files Changed

| File | Action |
|------|--------|
| `scripts/check_versioning.py` | Created |
| `Makefile` | Modified - added versioning targets |
| `.github/workflows/ci.yml` | Modified - added versioning-check job |
| `000-docs/205-AA-PLAN-phase-37-versioning-and-tagging-guardrails.md` | Created |
| `000-docs/206-RB-VERSIONING-bobs-brain-version-and-tagging-playbook.md` | Created |
| `000-docs/207-AA-REPT-phase-37-versioning-and-tagging-guardrails.md` | Created |

## Design Decisions

### Legacy Tag Handling

Found existing tags that don't follow current versioning:
- v1.0.0 (legacy)
- v5.0.0-sovereign (special release)
- v6.1.0 (legacy)

Decision: Filter these out during comparison but don't delete them. Script focuses on validating current VERSION against proper SemVer tags (v0.x series).

### VERSION vs CHANGELOG Synchronization

VERSION file is the single source of truth. CHANGELOG.md should be manually kept in sync. The script validates VERSION only; CHANGELOG validation is out of scope for this phase.

### Non-Blocking in Shallow Clones

CI environments often use shallow clones which don't include tags. Script handles this gracefully by validating format only and printing a warning.

## Current State

```
VERSION file: 0.14.1
Highest tag:  v0.14.1
Status:       Version matches highest tag (bump needed for next release)
```

## Usage

### Check Versioning

```bash
# Basic check
make check-versioning

# Verbose with tag list
make check-versioning-verbose
```

### Release Flow

1. Bump VERSION: `echo "0.14.2" > VERSION`
2. Update CHANGELOG.md
3. Run check: `make check-versioning`
4. Commit: `git commit -am "chore(release): bump version to v0.14.2"`
5. Tag: `git tag -a v0.14.2 -m "Release v0.14.2"`
6. Push: `git push && git push origin v0.14.2`

## Limitations

- Does not auto-bump versions (manual process)
- Does not validate CHANGELOG.md content
- Does not prevent duplicate tags (git handles that)

## Next Steps

1. Consider adding CHANGELOG.md validation in future phase
2. Consider adding release automation workflow
3. Apply pattern to other IAM repos

---
**Last Updated:** 2025-12-12
