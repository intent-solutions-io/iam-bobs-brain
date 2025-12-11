# Phase 26: Repo Cleanup, Canonical Scaffold, Branch Archive, v0.14.0 Release - PLAN

**Created:** 2025-12-05
**Phase:** 26 - Repository Cleanup & Structure
**Status:** Planning Complete, Execution In Progress

---

## Executive Summary

Phase 26 establishes Bob's Brain as a **canonical, client-facing repository** with clean structure, auditable branch management, and a formal v0.14.0 release documenting our recent community contributions and documentation improvements.

**Goals:**
1. Align repo structure to canonical 6767-style layout
2. Create safe, auditable branch cleanup tooling (not executed yet)
3. Refresh client-facing materials (README, CLAUDE.md, CHANGELOG)
4. Cut v0.14.0 release formalizing Phase 25 + community work

**Non-Goals:**
- NO runtime behavior changes
- NO architecture modifications
- NO new frameworks or deployment surfaces
- Everything remains: Vertex AI Agent Engine + ADK + Cloud Run gateway + Terraform + GitHub Actions

---

## Scope

### 1. Repository Structure Alignment

**Target Canonical Scaffold:**
```
bobs-brain/
├── 000-docs/                      # Single docs root (R6 compliant)
│   ├── Phase AARs & Plans
│   ├── 6767-standards/
│   └── ARCHIVED_BRANCHES.md       # New: Branch archive index
├── agents/                        # Production ADK agents
│   ├── bob/
│   ├── iam-senior-adk-devops-lead/
│   └── iam_*/
├── service/                       # Cloud Run gateways (R3)
├── infra/terraform/               # Infrastructure as Code (R4)
├── scripts/                       # CI helpers, KB sync
│   └── maintenance/               # New: cleanup_branches.sh
├── tests/                         # Test suite
├── .github/workflows/             # CI/CD (R4)
├── README.md                      # External-facing
├── CLAUDE.md                      # Operator instructions
├── CHANGELOG.md                   # Version history
└── VERSION                        # Current: 0.13.0 → 0.14.0
```

**Current Non-Canonical Directories:**
- `ai-card-examples/` - Keep (Linux Foundation PR reference)
- `github-pages/` - Keep (public docs site)
- `knowledge_store/` - Keep (ADK KB ingestion)
- `config/` - Keep (Vertex AI Search config)
- `templates/` - Keep (agent templates for IAM department)
- `tools/` - Keep (a2a-inspector and tooling)
- `archive/` - Keep (historical artifacts)

**Assessment:** Structure is already 95% aligned with canonical scaffold. No major moves needed.

### 2. Branch Cleanup Tooling

**Create (but DO NOT execute):**
- `scripts/maintenance/cleanup_branches.sh`
  - Archives all non-main branches as tags (`archive/<branch-name>`)
  - Pushes archive tags to origin
  - Deletes remote branches
  - Prunes local tracking branches
  - Requires manual `ARCHIVE` confirmation

- `000-docs/ARCHIVED_BRANCHES.md`
  - Documents the process
  - Indexes archived tags
  - Provides instructions for Jeremy to execute manually

**Rationale:**
- Main should be the only long-lived branch
- Feature branches merged and deleted
- History preserved via archive/* tags
- Safe, idempotent, auditable process

### 3. Documentation Refresh

**README.md:**
- Clear statement of what Bob's Brain is
- Architecture overview (Agent Engine + ADK + R3 gateway)
- Deployment process (CI + Terraform, no manual gcloud)
- Remove outdated references

**CLAUDE.md:**
- Align with current deployment patterns
- Emphasize GitHub Actions + Terraform (R4)
- Update with Phase 26 completion note
- Keep 000-docs/ as single doc root (R6)

**CHANGELOG.md:**
- Add v0.14.0 entry summarizing:
  - Repo scaffold alignment
  - Branch cleanup tooling
  - A2A samples contribution
  - Linux Foundation submission
  - Documentation improvements

### 4. Version 0.14.0 Release

**Current Version:** 0.13.0 (Released 2025-12-03)

**Proposed Version:** 0.14.0 (2025-12-05)

**Changes Since v0.13.0:**
- Document renumbering and archival (173-177)
- Linux Foundation AI Card submission AAR (177)
- A2A samples PR work (178, 180)
- CTO strategic initiative (179)
- Branch cleanup tooling (181-182)

**Release Artifacts:**
- VERSION file: `0.14.0`
- CHANGELOG entry
- Git tag: `v0.14.0`
- GitHub Release with notes

---

## Hard Constraints (R1-R8 Compliance)

All existing Hard Mode rules remain enforced:

**R1: ADK-Only Agents**
- ✅ No changes to agent frameworks
- ✅ All agents remain ADK-based

**R2: Vertex AI Agent Engine**
- ✅ No changes to runtime platform
- ✅ Agents deploy to Agent Engine only

**R3: Gateway Separation**
- ✅ No changes to Cloud Run gateways
- ✅ Service layer remains gateway-only

**R4: CI-Only Deployments**
- ✅ No manual gcloud commands
- ✅ All infra via Terraform + GitHub Actions

**R5: Dual Memory Model**
- ✅ No changes to memory architecture
- ✅ Session + Memory Bank unchanged

**R6: Single Docs Root**
- ✅ All docs in 000-docs/
- ✅ No new doc directories created

**R7: SPIFFE IDs**
- ✅ No changes to identity propagation
- ✅ AgentCards unchanged

**R8: Drift Detection**
- ✅ CI checks must pass
- ✅ No configuration drift introduced

---

## Risks & Mitigation

### Risk 1: Branch Deletion Accident
**Mitigation:**
- Script creates archive tags BEFORE deletion
- Requires manual `ARCHIVE` confirmation
- Jeremy executes manually (not automated)
- Full history preserved in tags

### Risk 2: Documentation Loss
**Mitigation:**
- No docs being moved or deleted
- Archive index tracks all archived content
- Git history preserves everything

### Risk 3: CI Path Breakage
**Mitigation:**
- Minimal structural changes
- Run full CI suite before PR
- Fix any path references immediately

### Risk 4: Confusion About Deployment
**Mitigation:**
- Clear README and CLAUDE.md updates
- Emphasize R4 (CI-only deployments)
- Document "NO manual gcloud" explicitly

---

## Success Criteria

**Structure:**
- [x] Repo matches canonical scaffold (minimal nesting)
- [x] No stray docs directories
- [x] All production code clearly organized

**Tooling:**
- [ ] `scripts/maintenance/cleanup_branches.sh` created
- [ ] `000-docs/ARCHIVED_BRANCHES.md` documented
- [ ] Process documented, ready for manual execution

**Documentation:**
- [ ] README.md updated and accurate
- [ ] CLAUDE.md aligned with current practices
- [ ] CHANGELOG.md includes v0.14.0 entry
- [ ] Phase 26 AAR completed

**CI:**
- [ ] All Hard Mode checks pass
- [ ] No test failures from structural changes
- [ ] GitHub Actions workflows unchanged

**Release:**
- [ ] VERSION file updated to 0.14.0
- [ ] Git tag `v0.14.0` created
- [ ] GitHub Release published
- [ ] No runtime behavior changes

---

## Timeline

**Day 1 (2025-12-05):**
- ✅ Create feature/phase-26-repo-cleanup branch
- ✅ Audit current structure
- ✅ Write Phase 26 Plan (this doc)
- ⏳ Create branch cleanup script
- ⏳ Create ARCHIVED_BRANCHES.md
- ⏳ Update README, CLAUDE.md, CHANGELOG
- ⏳ Create Phase 26 AAR

**Day 2:**
- Run CI checks
- Fix any path issues
- Create PR against main
- Merge after approval
- Execute release (VERSION, tag, GitHub Release)

**Post-Merge:**
- Jeremy manually executes `cleanup_branches.sh` when ready
- Update ARCHIVED_BRANCHES.md with tag list
- GitHub repo settings (default branch, protection, auto-delete)

---

## Deliverables

### Code/Structure:
1. `scripts/maintenance/cleanup_branches.sh` - Branch archive script
2. Minimal structural adjustments (if any)
3. Path fixes in CI workflows (if needed)

### Documentation:
1. `000-docs/181-AA-PLAN-phase-26-repo-cleanup-and-release.md` (this doc)
2. `000-docs/182-AA-REPT-phase-26-repo-cleanup-and-release-complete.md`
3. `000-docs/ARCHIVED_BRANCHES.md` - Branch archive index
4. Updated `README.md`
5. Updated `CLAUDE.md`
6. Updated `CHANGELOG.md` with v0.14.0 entry

### Release:
1. `VERSION` file: `0.14.0`
2. Git tag: `v0.14.0`
3. GitHub Release with changelog excerpt

---

## Post-Phase Actions

**For Jeremy (Manual Steps):**

1. **After PR Merge:**
   ```bash
   git checkout main
   git pull origin main
   ./scripts/maintenance/cleanup_branches.sh
   # Type 'ARCHIVE' when prompted
   ```

2. **GitHub Repo Settings:**
   - Set `main` as default branch
   - Enable branch protection on `main`
   - Enable "Automatically delete head branches" after merge

3. **GitHub Release:**
   - Create release from `v0.14.0` tag
   - Copy changelog section
   - Link to Phase 26 AAR

4. **Update ARCHIVED_BRANCHES.md:**
   - List all `archive/*` tags created
   - Add brief description of each

**For Future Phases:**
- All work on feature branches merged to main
- Branches auto-deleted after merge
- No accumulation of stale branches

---

## Alignment with Overall Strategy

**CTO Strategic Initiative (Doc 179):**
- Phase 26 supports "Reference Implementation Excellence"
- Clean repo structure = easier for others to fork
- Clear docs = lower barrier to entry
- Professional appearance = community trust

**Community Contributions:**
- Linux Foundation AI Card (PR #7)
- A2A Samples (PR #419)
- Both reference Bob's Brain as canonical example
- Clean repo reinforces this positioning

**Production Readiness:**
- v0.14.0 formalizes current state
- Clear deployment path documented
- No confusion about architecture
- Ready for external users/contributors

---

## Open Questions

**Q: Should we keep all non-canonical directories?**
**A:** YES. They all serve clear purposes:
- `ai-card-examples/` - Linux Foundation reference
- `github-pages/` - Public docs site
- `knowledge_store/` - ADK KB for agents
- `config/` - Vertex AI Search configuration
- `templates/` - IAM department scaffolding
- `tools/` - A2A inspector and utilities
- `archive/` - Historical preservation

**Q: Execute cleanup_branches.sh in this phase?**
**A:** NO. Create the tooling and docs, but Jeremy executes manually when ready. This gives time to review branches before archiving.

**Q: Any breaking changes in v0.14.0?**
**A:** NO. This is documentation and tooling only. Runtime behavior unchanged.

---

## References

**Related Docs:**
- 179-PP-PLAN-cto-strategic-community-recognition-initiative.md
- 180-AA-REPT-a2a-samples-full-production-pattern-implementation.md
- 177-AA-REPT-linux-foundation-submission-complete.md

**Hard Mode Rules:**
- 6767-DR-STND-adk-agent-engine-spec-and-hardmode-rules.md

**Previous Releases:**
- v0.13.0 (2025-12-03) - Linux Foundation PR preparation
- v0.12.0 (2025-11-30) - Phase 25 Slack hardening complete

---

**Status:** Planning Complete
**Next Action:** Create branch cleanup script and ARCHIVED_BRANCHES.md
**Owner:** Jeremy Longshore (CTO)
**Build Captain:** Claude Code

**Let's make Bob's Brain the cleanest, most professional ADK reference repo.**

---

**End of Plan**
**Version:** 1.0
**Created:** 2025-12-05
