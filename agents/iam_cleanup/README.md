# iam-cleanup - Repository Hygiene and Cleanup Specialist

**Agent Type:** LlmAgent (ADK)
**Model:** gemini-2.0-flash-exp
**Status:** Active Development
**Version:** 0.8.0+

## Purpose

The iam-cleanup agent is a specialized hygiene and cleanup agent responsible for identifying code quality issues, organizational problems, and maintenance burden in the repository. It ensures the codebase stays clean, well-structured, and maintainable by proactively detecting and proposing solutions for common hygiene problems.

## Responsibilities

### 1. Dead Code Detection
- Identify unreachable code paths
- Find unused functions, classes, and modules
- Detect orphaned test files and fixtures
- Spot commented-out code blocks
- Recognize deprecated code not properly removed
- Find unused branches and conditional code

### 2. Dependency Analysis
- Detect unused imports and dependencies
- Identify outdated or problematic packages
- Find circular dependencies
- Spot redundant imports
- Analyze dependency trees for optimization

### 3. Naming Consistency
- Check for naming convention violations
- Identify misleading or ambiguous names
- Detect inconsistent terminology
- Find unclear variable/function names
- Spot deprecated naming patterns

### 4. Structural Analysis
- Find files in wrong directories
- Identify missing __init__.py files
- Detect inconsistent module organization
- Spot test files outside test directories
- Find orphaned configuration files

### 5. Code Duplication
- Identify duplicate code blocks
- Find similar functions that could be refactored
- Spot copy-paste errors
- Detect duplicate configurations
- Recognize patterns suggesting consolidation

### 6. Safety Assessment
- Evaluate risk level of proposed cleanups
- Identify dependencies before removing code
- Assess impact on tests and CI/CD
- Determine if automation is safe
- Recommend manual review when needed

## Tools

### detect_dead_code
Scan for dead code and unreachable code paths.

**Parameters:**
- `scan_path`: Root directory to scan (default: ".")
- `file_patterns`: List of file patterns (default: Python/TypeScript)
- `include_comments`: Check for commented code blocks (default: True)

**Returns:** Dictionary with dead code findings, orphaned files, commented code blocks, statistics, and recommendations

### detect_unused_dependencies
Identify unused imports and dependencies.

**Parameters:**
- `scan_path`: Root directory to scan
- `requirements_file`: Path to requirements.txt or similar

**Returns:** Dictionary with unused imports, packages, duplicates, version issues, and recommendations

### identify_naming_issues
Find naming convention violations and inconsistencies.

**Parameters:**
- `scan_path`: Root directory to scan
- `file_patterns`: List of file patterns to check

**Returns:** Dictionary with naming violations, inconsistent patterns, unclear names, and recommendations

### find_code_duplication
Detect code duplication and refactoring opportunities.

**Parameters:**
- `scan_path`: Root directory to scan
- `minimum_block_size`: Minimum lines to consider duplication (default: 5)

**Returns:** Dictionary with duplicate blocks, similar functions, duplicate configs, and recommendations

### analyze_structure
Analyze repository structure for organizational issues.

**Parameters:**
- `scan_path`: Root directory to scan

**Returns:** Dictionary with structural issues, missing files, misplaced files, orphaned configs, and recommendations

### propose_cleanup_task
Create a CleanupTask specification with full safety assessment.

**Parameters:**
- `task_type`: Type of cleanup (dead_code, unused_deps, naming, structure, duplication)
- `description`: Clear description of the issue
- `affected_files`: List of files involved
- `proposed_action`: Step-by-step cleanup instructions
- `priority`: Priority level (low, medium, high)
- `is_automated`: Whether cleanup can be safely automated
- `safety_notes`: Special safety considerations

**Returns:** Dictionary with CleanupTask specification including task_id, type, description, affected_files, proposed_action, priority, safety assessment, and rollback plan

## Hard Mode Compliance (R1-R8)

### R1: ADK-Only Implementation
Uses google-adk LlmAgent exclusively - no LangChain, CrewAI, or AutoGen.

### R2: Vertex AI Agent Engine Runtime
Designed for deployment to Vertex AI Agent Engine with proper memory services.

### R3: Gateway Separation
No Runner imports in service/ - agents run in Agent Engine, gateways proxy only.

### R4: CI-Only Deployments
Deployed exclusively through GitHub Actions with Workload Identity Federation.

### R5: Dual Memory Wiring
Uses VertexAiSessionService for short-term cache and VertexAiMemoryBankService for persistent memory.

### R6: Single Documentation Folder
All documentation in 000-docs/ with NNN-CC-ABCD naming convention.

### R7: SPIFFE ID Propagation
Includes SPIFFE ID in all logs: `spiffe://intent.solutions/agent/bobs-brain/<env>/<region>/<version>`

### R8: Drift Detection
Enforced by CI scripts - violations block deployment.

## Integration with iam-* Team

### Upstream
- Receives requests from **iam-adk** (pattern findings) and **foreman** (manual triggers)
- Consults **iam-index** for codebase knowledge

### Produces
- **CleanupTask** specifications for repository hygiene issues
- Safety assessments and risk analysis
- Prioritized cleanup recommendations

### Downstream
- Hands off to **iam-issue** for issue creation
- Coordinates with **iam-fix-plan** for cleanup implementation planning
- Works with **iam-fix-impl** on actual cleanup execution

## Key Principles

1. **Thorough:** Comprehensive scans identify all classes of issues
2. **Accurate:** No false positives - only definitively identified issues
3. **Safe:** All cleanups have impact assessment and rollback plans
4. **Practical:** Focus on high-impact cleanups that reduce maintenance burden
5. **Incremental:** Enable step-by-step remediation rather than aggressive rewrites
6. **Conservative:** Flag uncertain cases for manual review

## Example Usage

### Scan for Dead Code
```
User: "Scan agents/ for dead code"

iam-cleanup:
1. Scans Python files in agents/
2. Identifies unused functions
3. Checks test coverage
4. Produces CleanupTask specs
5. Hands off to iam-issue
```

### Detect Naming Issues
```
User: "Check for naming convention violations in service/"

iam-cleanup:
1. Analyzes Python/TypeScript in service/
2. Identifies non-snake_case functions
3. Flags inconsistent patterns
4. Creates CleanupTasks
5. Proposes safe rename strategy
```

### Find Duplication
```
User: "Find code duplication in agents/bob/tools/"

iam-cleanup:
1. Scans for duplicate code blocks
2. Identifies refactoring opportunities
3. Assesses consolidation complexity
4. Proposes utility functions
5. Creates CleanupTasks with safety notes
```

## Configuration

### Environment Variables
- `PROJECT_ID` - GCP project identifier (required)
- `LOCATION` - GCP region (default: us-central1)
- `AGENT_ENGINE_ID` - Vertex AI Agent Engine ID (required)
- `APP_NAME` - Application name (default: bobs-brain)
- `AGENT_SPIFFE_ID` - SPIFFE identity (default: dev environment)

### Logging
Agent logs include:
- SPIFFE ID for traceability
- Session ID for memory linkage
- Scan statistics and findings
- Errors with full stack traces

## Testing

Run unit tests:
```bash
pytest tests/unit/test_iam_cleanup.py -v
```

Run cleanup detection on local repo:
```bash
# Requires agent to be instantiated
python3 -c "from agents.iam_cleanup import get_agent; print(get_agent())"
```

## Deployment

Deploy via GitHub Actions (enforced by R4):
```bash
# Automatic on PR/push to main
git push origin main

# Manual trigger for specific environments
# Go to: https://github.com/jeremylongshore/iam-bob-adk/actions
# Run "Deploy to Vertex AI Agent Engine"
```

## Related Documentation

- [000-docs/] - Phase plans and AARs
- [agents/iam_contracts.py] - CleanupTask specification
- [agents/iam_adk/] - Pattern compliance auditing
- [agents/iam_issue/] - Issue creation from cleanup tasks

## Support

For questions or issues with iam-cleanup:
1. Check this README
2. Review related agent documentation
3. Check 000-docs/ for phase documentation
4. File an issue on GitHub

---

**Last Updated:** 2025-11-19
**Version:** 0.8.0
**Status:** Production-ready (Hard Mode compliant)
