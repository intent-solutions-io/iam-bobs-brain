# Phase 32: Reference Template Hardening

**Date:** 2025-12-11
**Status:** In Progress
**Branch:** `feature/phase-32-reference-template-hardening`

## Objective

Make bobs-brain explicitly usable as a reference/template for future IAM/agent repos. Harden documentation so new teams can follow the pattern independently.

## Non-Goals

- Renaming the repository
- Changing runtime architecture
- Modifying agent behavior

## Deliverables

1. **Flat Index of Key Documents**
   - `000-docs/191-INDEX-bobs-brain-reference-map.md`
   - Sections: Phases & AARs, Standards, Runbooks, Infrastructure

2. **New Engineer Quickstart**
   - `000-docs/192-OVERVIEW-new-engineer-quickstart.md`
   - Repo purpose, architecture, first commands

3. **CLAUDE.md Template Instructions**
   - "Using bobs-brain as a Template" section
   - Steps for new repos
   - "Do not do this" list

4. **Cleanup Verification**
   - Confirm 000-docs/ stays flat (no nested dirs)
   - Mark any legacy docs in INDEX

## Implementation Steps

1. Create reference map index
2. Create new engineer quickstart
3. Update CLAUDE.md with template instructions
4. Verify 000-docs/ structure
5. Create AAR

---
**Last Updated:** 2025-12-11
