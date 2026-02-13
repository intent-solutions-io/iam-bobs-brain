# A2A Inspector: Usage and Local Setup

**Document Type:** Standard (DR-STND)
**Doc ID:** 123
**Status:** Active
**Last Updated:** 2025-11-20

---

## I. What is A2A Inspector?

**A2A Inspector** is an open-source web-based tool for debugging and validating servers that implement the Agent2Agent (A2A) protocol.

**Repository:** https://github.com/a2aproject/a2a-inspector

### Key Features

1. **Agent Card Validation**
   - Automatically fetches `/.well-known/agent-card.json`
   - Validates card structure against A2A specification
   - Displays card metadata (name, description, version, capabilities)

2. **Interactive Chat Interface**
   - Send messages to the connected A2A agent
   - View agent responses in real-time
   - Test conversation flows and tool invocations

3. **JSON-RPC 2.0 Debug Console**
   - Slide-out panel shows raw protocol messages
   - View request/response payloads
   - Identify protocol compliance issues immediately

4. **Real-Time Validation**
   - Highlights specification violations
   - Shows missing required fields
   - Validates message format and structure

---

## II. Why We Use It (Department ADK IAM Context)

For our **department ADK IAM** (foreman + iam-* specialists), A2A Inspector serves as:

1. **Development Quality Gate**
   - Verify agent cards are valid before deployment
   - Test A2A endpoints during local development
   - Catch protocol violations early

2. **Debugging Tool**
   - Inspect message flows between Bob ↔ foreman ↔ iam-* agents
   - Diagnose A2A communication issues
   - Validate AgentCard changes after refactors

3. **Integration Testing**
   - Manual smoke test for dev A2A gateway
   - Verify basic conversation flows work
   - Test error handling and structured responses

4. **Documentation Aid**
   - Live examples of proper A2A message structure
   - Reference for writing A2A quality gates (see: 124-DR-STND-a2a-quality-gate-for-department-adk-iam.md)

---

## III. Prerequisites

Before running A2A Inspector, ensure you have:

### For Docker Method (Recommended)
- Docker installed and running
- Port 8080 available (or choose different port)

### For Local Development Method
- **Python:** 3.10 or higher
- **uv:** Python package manager (`pip install uv`)
- **Node.js:** v18+ with npm
- Ports 5001 (frontend) and backend port available

---

## IV. Running A2A Inspector

### Method A: Docker (Simplest - Recommended for Quick Testing)

```bash
# Pull and run the official image (when available)
docker pull a2aproject/a2a-inspector:latest
docker run -d -p 8080:8080 a2aproject/a2a-inspector

# OR build from source
git clone https://github.com/a2aproject/a2a-inspector.git /tmp/a2a-inspector
cd /tmp/a2a-inspector
docker build -t a2a-inspector .
docker run -d -p 8080:8080 a2a-inspector
```

**Access:** http://127.0.0.1:8080

**Cleanup:**
```bash
docker ps | grep a2a-inspector  # Find container ID
docker stop <container-id>
docker rm <container-id>
```

### Method B: Local Development (For Contributing or Deep Debugging)

```bash
# Clone repository
git clone https://github.com/a2aproject/a2a-inspector.git /tmp/a2a-inspector
cd /tmp/a2a-inspector

# Install Python dependencies
uv sync

# Install Node.js dependencies
cd frontend && npm install && cd ..

# Run both services (convenience script)
chmod +x scripts/run.sh
bash scripts/run.sh
```

**Access:** http://127.0.0.1:5001

**Manual two-terminal approach:**
```bash
# Terminal 1 - Frontend (with live rebuild)
cd /tmp/a2a-inspector/frontend
npm run build -- --watch

# Terminal 2 - Backend
cd /tmp/a2a-inspector/backend
uv run app.py
```

---

## V. Using A2A Inspector with Our Dev A2A Gateway

### Step 1: Ensure Dev A2A Gateway is Running

Our department ADK IAM has an A2A gateway for dev testing:

```bash
# Check if dev A2A gateway is deployed
# (Adjust based on actual deployment)
curl https://a2a-gateway-dev-XXXXXXXX.run.app/.well-known/agent-card.json

# OR if running locally
curl http://localhost:8000/.well-known/agent-card.json
```

**Expected Response:** Valid AgentCard JSON with department metadata.

### Step 2: Open A2A Inspector

```bash
# Using Docker method
docker run -d -p 8080:8080 a2a-inspector
open http://127.0.0.1:8080

# OR using bobs-brain Make target (see Section VI)
make a2a-inspector-dev
```

### Step 3: Connect to Dev Gateway

1. **Enter Gateway URL** in inspector input field:
   ```
   https://a2a-gateway-dev-XXXXXXXX.run.app
   # OR
   http://localhost:8000
   ```

2. **Load Agent Card**
   - Inspector fetches `/.well-known/agent-card.json` automatically
   - Validates card structure
   - Displays agent metadata

3. **Verify "Good" Result:**
   - ✅ Agent card loads without errors
   - ✅ All required fields present (name, description, version, url)
   - ✅ Department metadata visible (foreman, specialists list)
   - ✅ Environment markers correct (dev/staging/prod)

### Step 4: Test Basic Conversation

1. **Send Simple Request:**
   ```
   Hello, can you describe your capabilities?
   ```

2. **Expected Behavior:**
   - Agent responds with structured description
   - No JSON-RPC protocol errors
   - Response shows in chat interface
   - Debug console shows valid request/response payloads

3. **Test Tool Invocation (if applicable):**
   ```
   List the repositories you can audit
   ```

4. **Expected Behavior:**
   - Agent invokes tools correctly
   - Tool results appear in response
   - No protocol violations in debug console

---

## VI. Bobs-Brain Integration (Make Target)

We provide a convenience Make target for running A2A Inspector against our dev gateway:

### Usage

```bash
# Start A2A Inspector (Docker method)
make a2a-inspector-dev

# This will:
# 1. Pull/build a2a-inspector Docker image
# 2. Run on port 8080
# 3. Print connection instructions for dev gateway
```

### Configuration

The Make target assumes:
- **Local dev gateway URL:** Set in `.env` as `A2A_GATEWAY_DEV_URL`
- **Default port:** 8080 (configurable via `A2A_INSPECTOR_PORT`)

**Example .env:**
```bash
# A2A Inspector settings
A2A_GATEWAY_DEV_URL=https://a2a-gateway-dev-XXXXXXXX.run.app
A2A_INSPECTOR_PORT=8080
```

---

## VII. What a "Good" Result Looks Like

When testing our department ADK IAM A2A gateway, expect:

### ✅ Agent Card Validation

```json
{
  "name": "iam-senior-adk-devops-lead",
  "description": "ADK/Vertex compliance foreman coordinating iam-* specialists",
  "version": "0.9.0",
  "url": "https://a2a-gateway-dev-XXXXXXXX.run.app",
  "capabilities": {
    "tools": ["audit_repo", "create_issue", "run_fix", ...],
    "specialists": ["iam-adk", "iam-issue", "iam-fix-plan", ...]
  },
  "environment": "dev",
  "department": "iam"
}
```

**Validation Checks Pass:**
- All required A2A fields present
- URL matches gateway endpoint
- Version matches deployment

### ✅ Basic Chat Works

**Request:**
```
What can you do?
```

**Response (Structured):**
```
I coordinate ADK/Vertex compliance audits across your repositories.

My capabilities:
- Audit repos for ADK pattern violations
- Generate IssueSpecs for drift
- Coordinate fixes via iam-fix-* specialists
- Run QA checks via iam-qa

I delegate to 8 specialists: iam-adk, iam-issue, iam-fix-plan,
iam-fix-impl, iam-qa, iam-docs, iam-cleanup, iam-index.
```

### ✅ No Protocol Errors

Debug console shows valid JSON-RPC 2.0 messages:

**Request:**
```json
{
  "jsonrpc": "2.0",
  "id": "1",
  "method": "invoke",
  "params": {
    "message": "What can you do?"
  }
}
```

**Response:**
```json
{
  "jsonrpc": "2.0",
  "id": "1",
  "result": {
    "message": "I coordinate ADK/Vertex compliance audits...",
    "metadata": {...}
  }
}
```

### ❌ Bad Results (Issues to Fix)

If you see:
- **404 on agent card:** Gateway not deployed or wrong URL
- **Invalid card structure:** AgentCard missing required fields
- **JSON-RPC errors:** Protocol implementation bug
- **Timeout:** Gateway not responding (check Cloud Run logs)
- **Tool errors:** Tool invocation failing (check agent implementation)

---

## VIII. When to Use A2A Inspector

### During Development
- After making changes to AgentCard
- When adding new A2A endpoints
- Before committing A2A protocol changes

### Before Deployment
- Manual smoke test before pushing to staging/prod
- Verify gateway responds correctly
- Test key conversation flows

### Debugging Issues
- When A2A communication fails in CI
- To inspect raw protocol messages
- To validate error handling

### Integration Testing
- After deploying new agent to Agent Engine
- When adding new iam-* specialists to department
- To verify multi-agent A2A flows (Bob → foreman → specialists)

---

## IX. Future Improvements

This is the initial manual usage doc. Future enhancements:

1. **Automated A2A Quality Gate (CI)**
   - Headless version of inspector for CI
   - Automated AgentCard validation
   - Basic conversation smoke test
   - See: 124-DR-STND-a2a-quality-gate-for-department-adk-iam.md

2. **Fork for Department-Specific Features**
   - Add department metadata validation
   - Test specialist delegation flows
   - Custom checks for Hard Mode (R1-R8) compliance

3. **Integration with ARV Checks**
   - Add to `make arv-gates`
   - Run as part of deployment pipeline
   - Block deployment on A2A validation failures

4. **Enhanced Debugging Tools**
   - Message replay capability
   - Diff tool for AgentCard versions
   - A2A flow visualization (Bob → foreman → specialists)

---

## X. Related Documentation

- **124-DR-STND-a2a-quality-gate-for-department-adk-iam.md** - Quality gate standard
- **125-DR-STND-prompt-design-for-bob-and-department-adk-iam.md** - Prompt design patterns
- **000-DR-STND-adk-agent-engine-spec-and-hardmode-rules.md** - Hard Mode rules
- **121-DR-MAP-adk-spec-to-implementation-and-arv.md** - Implementation mapping

---

## XI. Quick Reference

### Common Commands

```bash
# Start inspector (Docker)
make a2a-inspector-dev

# OR manually
docker run -d -p 8080:8080 a2a-inspector

# Access
open http://127.0.0.1:8080

# Check dev gateway is up
curl $A2A_GATEWAY_DEV_URL/.well-known/agent-card.json
```

### Expected URLs

- **Dev A2A Gateway:** Set in `.env` as `A2A_GATEWAY_DEV_URL`
- **Staging A2A Gateway:** TBD
- **Prod A2A Gateway:** TBD

### Troubleshooting

| Issue | Fix |
|-------|-----|
| Inspector won't start | Check port 8080 is free: `lsof -i :8080` |
| Can't load agent card | Verify gateway URL and network access |
| Protocol errors | Check agent implementation against A2A spec |
| Timeout | Check Cloud Run logs for backend errors |

---

**End of Document**
