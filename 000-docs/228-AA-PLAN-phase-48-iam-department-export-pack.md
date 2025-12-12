# Phase 48: IAM Department Export Pack – PLAN

**Date:** 2025-12-12
**Status:** In Progress
**Branch:** `feature/phase-48-iam-department-export-pack`

## Goals

Create a comprehensive export pack enabling other repos to adopt the IAM department pattern quickly.

### What This Phase Achieves

1. **Complete Template Directory** – All agent templates with proper placeholders
2. **Installation Script** – Automated template installation
3. **Validation Script** – Post-install validation
4. **Documentation Update** – Enhanced porting guide

## Analysis

### Current State

Template directory exists at `templates/iam-department/` but incomplete:
- ✅ README.md (comprehensive)
- ✅ Makefile.snippet
- ✅ 5 .template files
- ❌ Missing most agent templates
- ❌ No installation script
- ❌ No validation script

### Source Agents (to templatize)

| Agent | Files | Status |
|-------|-------|--------|
| iam_adk | agent.py, system-prompt.md | Need template |
| iam_issue | agent.py, system-prompt.md | Need template |
| iam_fix_plan | agent.py, system-prompt.md | Need template |
| iam_fix_impl | agent.py, system-prompt.md | Need template |
| iam_qa | agent.py, system-prompt.md | Need template |
| iam_doc | agent.py | Need template |
| iam_cleanup | agent.py | Need template |
| iam_index | agent.py, system-prompt.md | Need template |

## High-Level Steps

### Step 1: Create Install Script

Create `templates/iam-department/install.sh`:
- Copy template files to target directory
- Parameter replacement prompts
- Validation checks

### Step 2: Create Validate Script

Create `templates/iam-department/validate.sh`:
- Check all files were created
- Verify no unresolved placeholders
- Run ARV minimum check

### Step 3: Update Documentation

Update README.md with:
- Install script usage
- Validation steps
- Troubleshooting

### Step 4: Create AAR

Document completion and validation.

## Design Decisions

### Why Scripts vs Manual Copy?

Scripts reduce errors and ensure consistency. Manual copy-paste with sed is error-prone.

### Why Not More Templates?

Focus on core agents (foreman + 4 specialists) for minimal viable port. Advanced agents can be added incrementally.

## Files to Create/Modify

| File | Action | Purpose |
|------|--------|---------|
| `templates/iam-department/install.sh` | Create | Installation script |
| `templates/iam-department/validate.sh` | Create | Validation script |
| `templates/iam-department/README.md` | Modify | Add script usage |
| `000-docs/228-AA-PLAN-*.md` | Create | This file |
| `000-docs/229-AA-REPT-*.md` | Create | AAR |

---
**Last Updated:** 2025-12-12
