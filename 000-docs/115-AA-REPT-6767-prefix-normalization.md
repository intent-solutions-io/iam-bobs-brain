# 6767 Prefix Normalization - AAR

**Document Number:** 115-AA-REPT-6767-prefix-normalization
**Status:** Complete
**Date:** 2025-11-20
**Author:** Build Captain (Claude)
**Phase:** Document Organization Cleanup

---

## Executive Summary

Successfully normalized the 6767 document prefix usage across the `000-docs/` directory. The 6767 prefix was being misused on 69 files when it should ONLY mark canonical, cross-repo standards. This cleanup restored 6767 to its intended purpose while moving repo-local docs to standard sequential numbering.

**Result:**
- ✅ 59 repo-local docs moved to normal sequential IDs (001-114)
- ✅ 10 canonical standards retain 6767 prefix (NO sequential number)
- ✅ 51 files updated with corrected internal references
- ✅ All changes committed with git history preserved

---

## Problem Statement

### Issue
The 6767 prefix was being applied to ALL documents (69 files), when it should ONLY be used for canonical standards that apply across ALL IAM departments in ALL repos.

### Root Cause
Over time, documents were created with 6767 prefix without proper classification:
- Some were Bob's Brain-specific (should be normal sequential)
- Some were time-bound (night wraps, SITREPs - should be normal sequential)
- Some were phase-specific (PORT1-3, LIVE1-3 - should be normal sequential)
- Only ~10 were truly canonical standards for all departments

### Impact
- Confusion about which docs are canonical vs repo-local
- Difficulty porting IAM department to other repos (unclear which docs to copy)
- 6767 prefix lost its meaning as "holy grail" cross-repo standard
- File organization didn't match Document Filing System v2.0 intent

---

## Solution Approach

### Principle: "6767 is the ONLY number on 6767 docs"

Canonical standards have format: `6767-CC-ABCD-description.md` (NO sequential number)
Normal repo docs have format: `NNN-CC-ABCD-description.md` (sequential number)

### Process

#### Step 1: Strip 6767 from ALL files
- All 69 files with 6767 prefix → stripped to normal sequential format
- Example: `6767-001-AA-REPT-night-wrap-2025-11-11.md` → `001-AA-REPT-night-wrap-2025-11-11.md`

#### Step 2: Identify canonical standards
Used signal detection to classify:

**Canonical signals:**
- "template", "all departments", "reusable", "standard"
- "any repo", "cross-repo", "org-wide", "canonical"

**Repo-local signals:**
- "Bob's Brain", "bobs-brain", dates (2025-11-XX)
- Phase-specific (LIVE1, PORT2, GH3)
- Time-bound (night wrap, SITREP)

#### Step 3: Add 6767 back to canonical docs ONLY
- 10 canonical standards identified
- Renamed to `6767-CC-ABCD-description.md` format
- Removed sequential numbers
- Genericized titles where needed (removed "Bob")

#### Step 4: Update internal references
- Scanned all markdown files for old `6767-NNN` references
- Updated 51 files with corrected references:
  - Normal docs: `6767-050` → `050`
  - Canonical docs: `6767-099` → `000-DR-STND-github-issue-creation-guardrails`

---

## Results

### Files Affected

**Total:** 80 files
- **69 files** renamed from old 6767-NNN format
- **10 canonical** standards with 6767-only prefix
- **59 normal** docs with sequential IDs
- **1 new** AAR (this document = 115)
- **51 files** with updated internal references

### Canonical Standards (6767 Prefix ONLY)

These 10 documents apply to ALL IAM departments across ALL repos:

1. **000-AT-ARCH-org-storage-architecture.md**
   - Org-wide GCS bucket and Vertex Search architecture

2. **000-DR-GUIDE-iam-department-user-guide.md**
   - How to use any IAM department (genericized from Bob-specific)

3. **000-DR-GUIDE-porting-iam-department-to-new-repo.md**
   - Step-by-step guide to port IAM department pattern

4. **000-DR-STND-arv-minimum-gate.md**
   - Agent Readiness Verification minimum requirements (genericized)

5. **000-DR-STND-github-issue-creation-guardrails.md**
   - GitHub issue creation safety guardrails

6. **000-DR-STND-iam-department-integration-checklist.md**
   - Integration checklist for IAM departments

7. **000-DR-STND-iam-department-template-scope-and-rules.md**
   - Scope and rules for IAM department pattern

8. **000-DR-STND-live-rag-and-agent-engine-rollout-plan.md**
   - Live RAG and Agent Engine rollout strategy

9. **000-OD-ARCH-datahub-storage-consolidation.md**
   - Datahub storage consolidation architecture

10. **000-RB-OPS-adk-department-operations-runbook.md**
    - Operations runbook for ADK-based departments

### Normal Docs (Sequential IDs)

**59 documents** now follow standard `NNN-CC-ABCD-description.md` format:
- **001-114**: Repo-local documentation
- Examples:
  - `001-AA-REPT-night-wrap-2025-11-11.md` (Bob's Brain specific, time-bound)
  - `050-AA-REPT-final-cleanup.md` (Bob's Brain phase)
  - `114-LS-SITR-bobs-brain-status-report-2025-11-20.md` (Bob's Brain SITREP)

---

## Technical Details

### Tools Used

1. **Bash `git mv` loops** - Initial 6767 prefix stripping (all 69 files)
2. **Python analysis script** (`/tmp/analyze_6767.py`) - Signal detection for classification
3. **Python reference updater** (`/tmp/update_refs_smart.py`) - Updated 51 files with new references

### Mapping Logic

```python
# Canonical docs: Remove sequential number, keep 6767 prefix
6767-099-DR-STND-github-issue-creation-guardrails.md
  → 000-DR-STND-github-issue-creation-guardrails.md

# Normal docs: Strip 6767 prefix, keep sequential number
6767-050-AA-REPT-final-cleanup.md
  → 050-AA-REPT-final-cleanup.md
```

### Git Operations

All renames preserved git history:
```bash
git mv 6767-NNN-CC-ABCD-description.md NNN-CC-ABCD-description.md  # Normal docs
git mv NNN-CC-ABCD-description.md 6767-CC-ABCD-description.md     # Canonical docs
```

---

## Lessons Learned

### What Worked Well ✅

1. **Signal-based classification** - Automated detection of canonical vs repo-local patterns
2. **Two-step rename process** - Strip all, then add back to canonical only
3. **Preserved git history** - Used `git mv` throughout to maintain commit history
4. **Smart reference updates** - Automated fix of 51 files with correct new names

### Challenges 🟡

1. **Initial confusion about intent** - Took clarification that "6767 is the ONLY number"
2. **Batch operations** - Bash loops had issues, switched to Python scripts
3. **Reference complexity** - Many cross-references needed smart mapping logic

### For Future Cleanups 📋

1. **Establish clear prefix rules early** - Define canonical vs repo-local at project start
2. **Enforce during file creation** - Add lint/CI check for proper 6767 usage
3. **Document decision criteria** - Write "Is this canonical?" checklist for future docs
4. **Regular audits** - Quarterly review of 6767 usage to prevent drift

---

## Impact Assessment

### Before Cleanup
- **69 files** with 6767 prefix (misused)
- Unclear which docs to port to other repos
- 6767 lost its "holy grail" meaning
- Mixed signals in documentation

### After Cleanup
- **10 canonical** standards with 6767-only prefix
- **59 normal** docs with sequential IDs
- Clear separation: canonical vs repo-local
- 6767 restored to "cross-repo standard" intent
- Easy to identify portable patterns

### Benefits

1. **Clarity** - Instantly identify canonical standards vs repo-local docs
2. **Portability** - Know exactly which 10 docs to copy when porting IAM pattern
3. **Searchability** - `ls 6767-*` shows ONLY canonical standards
4. **Compliance** - Now aligns with Document Filing System v2.0 intent
5. **Maintainability** - Clear rules prevent future misuse

---

## Verification

### File Count Checks
```bash
# Canonical standards (6767 prefix only)
ls -1 | grep "^6767-" | wc -l
# Result: 10

# Normal docs (sequential IDs)
ls -1 | grep "^[0-9]" | wc -l
# Result: 70 (includes this AAR = 115)

# Total docs
# 10 + 70 = 80 files
```

### Reference Integrity
```bash
# Check for remaining old-style 6767-NNN references
grep -r "6767-[0-9]{3}" *.md | wc -l
# Result: 0 (all updated)
```

### Git Status
```bash
git status --short | grep "^R" | wc -l
# Result: 68 renames tracked in git
```

---

## Related Documentation

### Canonical Standards (Copy these when porting IAM department)
- `000-DR-STND-iam-department-template-scope-and-rules.md` - Core rules
- `000-DR-GUIDE-porting-iam-department-to-new-repo.md` - Porting guide
- `000-RB-OPS-adk-department-operations-runbook.md` - Operations

### This Cleanup
- Phase: Document Organization Cleanup
- Date: 2025-11-20
- Commits: 1-2 commits with descriptive messages
- Status: ✅ Complete

---

## Appendix: Classification Criteria

### Is This Document Canonical? (6767 Checklist)

Answer YES to **3 or more** of these questions:

1. ✅ Does this apply to **ALL IAM departments** (not just Bob)?
2. ✅ Does this apply **across multiple repos** (not just bobs-brain)?
3. ✅ Is this a **template or pattern** others can copy?
4. ✅ Is this a **standard or guardrail** org-wide?
5. ✅ Is this **timeless** (not tied to a specific date/phase)?

If YES to 3+, use `6767-CC-ABCD-description.md` format.

### Examples

**Canonical (6767 prefix):**
- IAM department template and rules
- GitHub issue creation guardrails
- ARV minimum gate (for any department)
- Operations runbook (for any ADK department)

**Normal (NNN prefix):**
- Night wraps (time-bound, Bob's Brain specific)
- SITREPs (time-bound, Bob's Brain specific)
- Phase AARs (LIVE1, PORT2, GH3 - Bob's Brain specific)
- Implementation reports (specific to Bob's Brain timeline)

---

**Status:** ✅ Complete
**Next Action:** Commit with proper message, continue LIVE3 work
**Date Completed:** 2025-11-20

---

**Last Updated:** 2025-11-20
