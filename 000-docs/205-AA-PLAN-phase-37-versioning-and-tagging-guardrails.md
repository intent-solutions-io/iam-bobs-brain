# Phase 37: Versioning & Tagging Guardrails

**Date:** 2025-12-12
**Status:** In Progress
**Branch:** `feature/phase-37-versioning-guardrails`

## Objective

Establish strict versioning and tagging rules for this repo (and future templates):

1. Capture versioning rules in documentation
2. Create a validation script that checks VERSION file against git tags
3. Wire validation into CI as a non-blocking check

## Versioning Rules

### What "Good" Looks Like

- Tags follow SemVer: `vX.Y.Z` (e.g., `v0.14.1`)
- VERSION file contains version without `v` prefix (e.g., `0.14.1`)
- Monotonic increasing: new version ≥ highest existing tag
- Release notes in CHANGELOG.md or AA-REPT docs

### Version Sources

**Primary:** `VERSION` file (single source of truth)
**Secondary:** CHANGELOG.md, AA-REPT docs (should match)

### Tag Format

- Required: `v` prefix + SemVer (`v0.14.1`)
- Optional: Annotated tag with release message

## Implementation

### 1. Version Check Script

`scripts/check_versioning.py`:
- Reads VERSION file
- Validates SemVer format
- Compares against existing git tags
- Reports if version is valid for new release

### 2. CI Integration

Add job in CI workflow:
- Runs on push to main
- Non-blocking (warning only) if tags unavailable
- Fails if VERSION is malformed or < highest tag

### 3. Runbook Documentation

`000-docs/206-RB-VERSIONING-bobs-brain-version-and-tagging-playbook.md`:
- How to bump versions
- How to create tags
- How to interpret script failures
- How other repos should copy this pattern

## Current State

**VERSION file:** `0.14.1`

**Existing Tags (relevant):**
- v0.14.1 (latest proper SemVer)
- v0.14.0
- v0.13.0
- ...

**Legacy Tags (to note but not fix):**
- v5.0.0-sovereign (special release, ignore)
- v6.1.0 (legacy, ignore)
- v1.0.0 (legacy, ignore)

## Fallbacks

- If git tags unavailable in CI (shallow clone): Skip comparison, validate format only
- If non-SemVer tags exist: Skip them in comparison, note in AAR

## Success Criteria

- [ ] `scripts/check_versioning.py` validates VERSION format
- [ ] Script compares against existing tags (when available)
- [ ] CI job wired (non-blocking if tags missing)
- [ ] Runbook documents the process

---
**Last Updated:** 2025-12-12
