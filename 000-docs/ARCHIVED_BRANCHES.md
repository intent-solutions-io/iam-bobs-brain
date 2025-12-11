# ARCHIVED_BRANCHES – bobs-brain

This file tracks branches that have been archived into tags of the form `archive/<branch-name>`.

---

## Overview

**Purpose:** Maintain a clean repository with `main` as the only long-lived branch while preserving complete Git history of all feature/development work.

**Method:** Archive branch tips as Git tags before deletion, ensuring no history is lost.

**Benefits:**
- Clean branch list (only `main` visible)
- Full history preserved via tags
- Easy to restore archived branches if needed
- Auditable process with confirmation gates

---

## Process

### Archiving Branches

**Script:** `scripts/maintenance/cleanup_branches.sh`

**When to Run:**
- After major releases
- When branch list becomes cluttered
- Before external collaborators join
- As part of periodic repo maintenance

**How to Execute:**

```bash
# 1. Ensure you're on main and up to date
git checkout main
git pull origin main

# 2. Run the cleanup script
./scripts/maintenance/cleanup_branches.sh

# 3. Review the branch list displayed

# 4. Type 'ARCHIVE' when prompted to confirm

# 5. Update this file (ARCHIVED_BRANCHES.md) with new tags
```

**What the Script Does:**

1. **Discovery** - Lists all remote branches except `main`
2. **Confirmation** - Requires typing `ARCHIVE` to proceed
3. **Tag Creation** - Creates `archive/<branch-name>` tags at branch tips
4. **Push Tags** - Pushes all archive tags to origin
5. **Delete Branches** - Removes remote branches from origin
6. **Prune Local** - Cleans up local tracking branches

**Safety Features:**
- Manual confirmation required (`ARCHIVE` prompt)
- Tags created BEFORE deletion
- Full history preserved
- Idempotent (can be run multiple times)

---

## Restoring Archived Branches

If you need to restore an archived branch:

```bash
# List available archive tags
git tag | grep "^archive/"

# Restore specific branch from tag
git checkout -b restored-branch-name archive/original-branch-name

# Push to origin if needed
git push origin restored-branch-name
```

---

## Tag Index

> **NOTE:** This section will be populated after the first run of `cleanup_branches.sh`.
>
> For each archive tag, add an entry with:
> - Tag name
> - Brief description of what the branch contained
> - Date archived

### Phase 26 (Initial Cleanup) - Not Yet Executed

Pending manual execution by Jeremy. Once run, tags will be listed here.

**Expected Tags** (based on current remote branches):
- TBD - will be populated after script execution

---

## Branch Management Policy

**Going Forward (Post-Phase 26):**

1. **Feature Branches**
   - Created from `main` for each feature/phase
   - Format: `feature/<phase-name>` or `feature/<feature-name>`
   - Merged to `main` via PR
   - Automatically deleted after merge (GitHub setting)

2. **Main Branch**
   - Only long-lived branch
   - Protected (required PR reviews)
   - Direct commits disabled
   - Default branch for clones

3. **Release Tags**
   - Format: `v0.X.Y` (semantic versioning)
   - Created at each release
   - Permanent, never deleted

4. **Archive Tags**
   - Format: `archive/<branch-name>`
   - Created before branch deletion
   - Permanent, never deleted

---

## GitHub Repository Settings

**Recommended Settings** (Jeremy to configure in GitHub UI):

1. **Default Branch:** `main`
2. **Branch Protection for `main`:**
   - Require pull request reviews before merging
   - Require status checks to pass (CI workflows)
   - Require linear history
   - Include administrators
3. **Automatically Delete Head Branches:** Enabled
4. **Merge Strategy:** Squash and merge (or merge commit)

---

## History

### Phase 26 (2025-12-05)
- Created `scripts/maintenance/cleanup_branches.sh`
- Established branch archival process
- Created this index document
- **Status:** Tooling ready, not yet executed

---

## References

**Related Docs:**
- `scripts/maintenance/cleanup_branches.sh` - Archive script
- `181-AA-PLAN-phase-26-repo-cleanup-and-release.md` - Phase 26 planning
- `182-AA-REPT-phase-26-repo-cleanup-and-release-complete.md` - Phase 26 AAR

**GitHub Docs:**
- [Managing Branches](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-branches-in-your-repository)
- [Branch Protection Rules](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches)

---

**Last Updated:** 2025-12-05
**Maintained By:** Jeremy Longshore (CTO)
**Status:** Active, pending first execution
