# A2A Quality Gate for Department ADK IAM

**Document Type:** Standard (DR-STND)
**Doc ID:** 124
**Status:** Active
**Last Updated:** 2025-11-20

---

## I. Purpose and Scope

This document defines the **A2A Quality Gate** for the department ADK IAM (iam-senior-adk-devops-lead + iam-* specialists). The quality gate ensures that all A2A agents meet minimum standards before deployment to staging or production.

**Scope:**
- AgentCard requirements (structure, fields, metadata)
- Basic behavior validation (load card, handle requests, structured errors)
- ADK/Vertex-specific expectations (SPIFFE IDs, Hard Mode compliance)
- Manual testing workflow (a2a-inspector)
- Automated testing strategy (future CI integration)

---

## II. What is an A2A Quality Gate?

An **A2A Quality Gate** is a set of verification checks that an agent must pass before being considered deployment-ready. It validates:

1. **Protocol Compliance** - Agent implements A2A specification correctly
2. **Card Validity** - AgentCard JSON is well-formed and complete
3. **Basic Functionality** - Agent responds to simple requests without errors
4. **Department Metadata** - Required fields for multi-agent coordination
5. **Hard Mode Alignment** - Follows bobs-brain R1-R8 architectural rules

---

## III. Quality Gate Requirements

### A. AgentCard Requirements (REQUIRED)

Every A2A agent MUST expose a valid AgentCard at `/.well-known/agent-card.json`.

**Required Fields:**

```json
{
  "name": "agent-name",           // REQUIRED: kebab-case identifier
  "description": "...",            // REQUIRED: 1-2 sentence summary
  "version": "0.9.0",             // REQUIRED: semver format
  "url": "https://...",           // REQUIRED: base URL of A2A endpoint
  "capabilities": {...},          // REQUIRED: tools, skills, or specialists
  "environment": "dev|staging|prod",  // REQUIRED: deployment environment
  "department": "iam",            // REQUIRED for dept agents
  "spiffe_id": "spiffe://..."     // REQUIRED: R7 compliance
}
```

**Optional but Recommended:**

```json
{
  "tags": ["adk", "vertex", "compliance"],
  "metadata": {
    "foreman": true,              // If this agent delegates to specialists
    "specialists": [...],         // List of iam-* agents if foreman
    "hard_mode_compliant": true,  // R1-R8 compliance flag
    "rag_enabled": false          // Vertex AI Search integration
  },
  "contact": {
    "team": "build-captain",
    "email": "claude.buildcaptain@intentsolutions.io"
  }
}
```

**Validation Rules:**

1. **name** - Must match deployment name (e.g., `iam-senior-adk-devops-lead`)
2. **version** - Must match `APP_VERSION` in deployment config
3. **url** - Must be accessible HTTPS endpoint
4. **environment** - Must match actual deployment environment
5. **spiffe_id** - Must follow pattern: `spiffe://intent.solutions/agent/{name}/{env}/{region}/{version}`

### B. Basic Behavior Requirements (REQUIRED)

**1. Card Load Test**
- Agent card loads without HTTP errors (200 OK)
- JSON parses correctly (no syntax errors)
- All required fields present and valid types

**2. Simple Request Test**
- Agent responds to basic greeting: "Hello, what can you do?"
- Response is structured (not raw error)
- Response time < 30 seconds (for non-RAG queries)

**3. Error Handling Test**
- Agent returns structured error for invalid requests
- Error includes helpful message (not stack trace)
- Error follows JSON-RPC 2.0 format if applicable

**4. Protocol Compliance Test**
- Messages follow A2A protocol structure
- Request/response pairs use correct formats
- No protocol violations in debug console

### C. Department-Specific Requirements (department ADK IAM)

**For Foreman (iam-senior-adk-devops-lead):**

```json
{
  "capabilities": {
    "specialists": [
      "iam-adk",
      "iam-issue",
      "iam-fix-plan",
      "iam-fix-impl",
      "iam-qa",
      "iam-docs",
      "iam-cleanup",
      "iam-index"
    ],
    "delegation": true,
    "orchestration": true
  },
  "metadata": {
    "foreman": true,
    "department": "iam",
    "role": "orchestrator"
  }
}
```

**For Specialists (iam-*):**

```json
{
  "capabilities": {
    "tools": [...],              // List of specific tools
    "delegation": false,         // Specialists don't delegate
    "foreman": "iam-senior-adk-devops-lead"  // Parent orchestrator
  },
  "metadata": {
    "specialist": true,
    "department": "iam",
    "role": "worker"
  }
}
```

### D. Hard Mode Compliance Requirements (OPTIONAL but RECOMMENDED)

These are specific to bobs-brain's R1-R8 architecture:

**R1 - ADK-Only Implementation:**
- Agent card may include: `"framework": "google-adk"`
- No mention of LangChain, CrewAI, or other frameworks

**R2 - Vertex AI Agent Engine Runtime:**
- Agent card may include: `"runtime": "vertex-ai-agent-engine"`
- URL points to Agent Engine endpoint (not self-hosted)

**R3 - Gateway Separation:**
- If card includes `"gateway_url"`, it should point to Cloud Run proxy
- No indication of Runner running in gateway

**R7 - SPIFFE ID Propagation:**
- `spiffe_id` field REQUIRED in agent card
- SPIFFE ID logged in all A2A interactions
- Format: `spiffe://intent.solutions/agent/{name}/{env}/{region}/{version}`

---

## IV. Quality Gate Workflow

### Manual Testing with a2a-inspector (Current)

**Prerequisites:**
- A2A gateway deployed and accessible
- a2a-inspector running locally (see: 123-DR-STND-a2a-inspector-usage-and-local-setup.md)

**Steps:**

1. **Start a2a-inspector:**
   ```bash
   make a2a-inspector-dev
   # Access: http://127.0.0.1:8080
   ```

2. **Load Agent Card:**
   - Enter gateway URL: `https://a2a-gateway-dev-XXXXXXXX.run.app`
   - Verify card loads without errors
   - Verify all required fields present

3. **Test Basic Chat:**
   - Send: "Hello, what can you do?"
   - Verify response is structured
   - Verify response describes agent capabilities

4. **Test Tool Invocation (if applicable):**
   - Send request that should trigger a tool
   - Verify tool invocation appears in response
   - Verify no protocol errors in debug console

5. **Test Error Handling:**
   - Send malformed request
   - Verify structured error response
   - Verify helpful error message

6. **Verify Department Metadata:**
   - Check `capabilities.specialists` if foreman
   - Check `metadata.department` = "iam"
   - Check `spiffe_id` follows pattern

**Acceptance Criteria:**
- ✅ Agent card loads without errors
- ✅ All required fields present and valid
- ✅ Basic chat works (< 30s response)
- ✅ Errors are structured and helpful
- ✅ Department metadata correct
- ✅ No protocol violations

### Automated Testing (Future CI Integration)

**Target:** Add headless A2A quality gate to CI pipeline

**Proposed Implementation:**

```bash
# scripts/check_a2a_quality_gate.py
# Run as part of CI before deployment

# 1. Check agent card exists and is valid
curl -f https://a2a-gateway-dev.run.app/.well-known/agent-card.json

# 2. Validate JSON structure
python3 -c "
import json, requests
card = requests.get('https://.../.well-known/agent-card.json').json()
assert 'name' in card
assert 'version' in card
assert 'url' in card
assert 'capabilities' in card
assert 'environment' in card
assert 'department' in card and card['department'] == 'iam'
assert 'spiffe_id' in card
"

# 3. Test basic conversation (headless)
python3 scripts/test_a2a_conversation.py \
  --url https://a2a-gateway-dev.run.app \
  --message "Hello, what can you do?" \
  --expect-response-time 30

# 4. Validate response structure
# ... (check response is not an error, has expected fields)
```

**CI Integration:**

```yaml
# .github/workflows/a2a-quality-gate.yml
name: A2A Quality Gate

on:
  pull_request:
    branches: [main]
  workflow_dispatch:

jobs:
  a2a-quality-gate:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v3

      - name: Check Agent Card
        run: |
          python3 scripts/check_a2a_quality_gate.py \
            --env dev \
            --gateway-url ${{ secrets.A2A_GATEWAY_DEV_URL }}

      - name: Test Basic Conversation
        run: |
          python3 scripts/test_a2a_conversation.py \
            --url ${{ secrets.A2A_GATEWAY_DEV_URL }} \
            --test-suite basic

      - name: Verify Department Metadata
        run: |
          python3 scripts/verify_department_metadata.py \
            --department iam \
            --gateway-url ${{ secrets.A2A_GATEWAY_DEV_URL }}
```

**ARV Integration:**

```makefile
# Add to Makefile
check-a2a-quality-gate: ## Verify A2A quality gate (agent card + basic conversation)
	@echo "🔍 Running A2A Quality Gate..."
	@python3 scripts/check_a2a_quality_gate.py --env dev
	@echo "✅ A2A Quality Gate passed!"

# Update existing ARV gates
arv-gates: check-rag-readiness check-arv-minimum check-arv-engine-flags check-arv-spec check-a2a-quality-gate
	@echo "✅ All ARV gates passed!"
```

---

## V. Quality Gate Levels

We define three quality gate levels based on deployment environment:

### Level 1: Development (DEV)

**Purpose:** Catch obvious issues early

**Requirements:**
- ✅ Agent card loads (200 OK)
- ✅ Required fields present
- ✅ Basic greeting works

**Enforcement:** Manual via a2a-inspector (recommended but not blocking)

**Failure Mode:** Warning logged, deployment continues

### Level 2: Staging (STAGING)

**Purpose:** Validate before production

**Requirements:**
- ✅ All Level 1 requirements
- ✅ Department metadata validated
- ✅ SPIFFE ID format correct
- ✅ Error handling test passes
- ✅ Response time < 30s

**Enforcement:** Automated in CI (recommended, can be overridden)

**Failure Mode:** Deployment blocked unless override flag set

### Level 3: Production (PROD)

**Purpose:** Ensure production-ready quality

**Requirements:**
- ✅ All Level 2 requirements
- ✅ All department specialists reachable (if foreman)
- ✅ Tool invocations work correctly
- ✅ Hard Mode compliance verified (R1-R8)
- ✅ Performance benchmarks met (< 5s p95)

**Enforcement:** Automated in CI (REQUIRED, no override)

**Failure Mode:** Deployment fails, manual investigation required

---

## VI. Integration with a2a-inspector

### How a2a-inspector Fits

**a2a-inspector is the manual implementation of our quality gate.**

It provides:
- Visual agent card validation
- Interactive conversation testing
- JSON-RPC 2.0 debug console
- Protocol compliance checking

**When to use a2a-inspector:**
1. **During Development** - Quick feedback loop for A2A changes
2. **Before PR Submission** - Verify agent works before CI
3. **Debugging Issues** - Inspect raw protocol messages
4. **Integration Testing** - Test multi-agent flows (Bob → foreman → specialists)

**Automation Path:**

```
Manual (a2a-inspector)
    ↓
Scripted (check_a2a_quality_gate.py)
    ↓
CI-Integrated (arv-gates)
    ↓
Production Gate (required for deployment)
```

---

## VII. Failure Modes and Remediation

### Common Failures

**1. Agent Card Not Found (404)**
- **Cause:** Gateway not deployed or wrong URL
- **Fix:** Verify deployment, check Cloud Run logs
- **Tool:** `curl -v https://.../.well-known/agent-card.json`

**2. Invalid JSON Structure**
- **Cause:** Missing fields or malformed JSON
- **Fix:** Validate card against schema, add missing fields
- **Tool:** a2a-inspector card validation, `jq` for JSON validation

**3. Timeout on Basic Request**
- **Cause:** Agent slow to respond, or not responding
- **Fix:** Check Agent Engine logs, verify agent is running
- **Tool:** Cloud Logging, `gcloud ai agent-engines describe`

**4. Protocol Errors in Console**
- **Cause:** Incorrect JSON-RPC 2.0 format
- **Fix:** Review A2A protocol spec, fix message structure
- **Tool:** a2a-inspector debug console

**5. Missing Department Metadata**
- **Cause:** AgentCard doesn't include required department fields
- **Fix:** Add `department`, `metadata.foreman`, `capabilities.specialists`
- **Tool:** a2a-inspector card view, manual JSON inspection

---

## VIII. Exemptions and Overrides

### When to Skip Quality Gate

**Development Environment:**
- Rapid iteration requires flexibility
- Quality gate RECOMMENDED but not REQUIRED
- Failures log warnings, don't block deployment

**Exemption Process:**

1. Document reason for exemption in PR
2. Add `skip-a2a-quality-gate` label to PR
3. Deploy with override flag: `SKIP_A2A_GATE=true make deploy-dev`
4. Track exemption in AAR for this deployment

**Staging/Production:**
- Quality gate REQUIRED, exemptions rare
- Requires approval from Build Captain
- Must document in incident report if overridden

---

## IX. Future Enhancements

### Phase 1: Automation (Q1 2026)
- ✅ Scripted quality gate checks (headless)
- ✅ CI integration for dev/staging environments
- ✅ ARV gates include A2A quality

### Phase 2: Performance Testing (Q2 2026)
- Response time benchmarks (p50, p95, p99)
- Load testing for multi-agent flows
- Error rate monitoring (< 1% failure rate)

### Phase 3: Advanced Validation (Q2 2026)
- Multi-agent delegation testing (Bob → foreman → iam-*)
- Schema validation against AgentCard spec
- Security checks (auth, token validation, rate limiting)

### Phase 4: Fork a2a-inspector (Q3 2026)
- Custom department metadata validation
- Hard Mode (R1-R8) compliance checks
- Integration with ARV system
- Automated test case generation

---

## X. Related Documentation

- **123-DR-STND-a2a-inspector-usage-and-local-setup.md** - How to use a2a-inspector
- **125-DR-STND-prompt-design-for-bob-and-department-adk-iam.md** - Prompt design patterns
- **000-DR-STND-adk-agent-engine-spec-and-hardmode-rules.md** - Hard Mode rules (R1-R8)
- **121-DR-MAP-adk-spec-to-implementation-and-arv.md** - ARV implementation mapping

---

## XI. Quick Reference

### Minimum Quality Gate Checklist (Manual)

```
□ Agent card loads (200 OK)
□ name, description, version, url present
□ environment matches deployment (dev/staging/prod)
□ department = "iam"
□ spiffe_id follows pattern
□ Basic greeting works: "Hello, what can you do?"
□ Response < 30 seconds
□ Error handling returns structured error
□ No protocol violations in a2a-inspector console
□ Department metadata correct (foreman/specialists)
```

### Commands

```bash
# Manual quality gate with a2a-inspector
make a2a-inspector-dev
# Then test at http://127.0.0.1:8080

# Future: Automated quality gate
make check-a2a-quality-gate

# Future: Run as part of ARV gates
make arv-gates
```

---

**End of Document**
