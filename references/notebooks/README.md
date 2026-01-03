# User Manual - ADK & Agent Engine Reference Materials

**Last Updated:** 2025-11-11
**Category:** 001-usermanual

---

## Overview

This directory contains official Google Cloud reference notebooks for building agents with ADK and deploying to Vertex AI Agent Engine and Cloud Run.

These tutorials serve as implementation references for Bob's Brain hard mode architecture (R1: ADK, R2: Agent Engine).

---

## Notebooks

### 1. Multi-Agent Systems on Vertex AI with Claude
**File:** `tutorial_multi_agent_systems_on_vertexai_with_claude.ipynb`
**Size:** 102KB
**Source:** [GoogleCloudPlatform/generative-ai](https://github.com/GoogleCloudPlatform/generative-ai/blob/main/agents/agent_engine/tutorial_multi_agent_systems_on_vertexai_with_claude.ipynb)

**Topics Covered:**
- Building multi-agent systems on Vertex AI
- Agent-to-Agent (A2A) protocol implementation
- Vertex AI Agent Engine deployment
- Claude integration with Vertex AI
- Multi-agent orchestration patterns

**Relevant to:**
- R1: ADK agent implementation
- R2: Vertex AI Agent Engine runtime
- R7: Agent identity and discovery (A2A protocol)

### 2. Getting Started with Memory for ADK in Cloud Run
**File:** `get_started_with_memory_for_adk_in_cloud_run.ipynb`
**Size:** 30KB
**Source:** [GoogleCloudPlatform/generative-ai](https://github.com/GoogleCloudPlatform/generative-ai/blob/main/agents/cloud_run/agents_with_memory/get_started_with_memory_for_adk_in_cloud_run.ipynb)

**Topics Covered:**
- ADK memory services (Session + Memory Bank)
- Deploying ADK agents to Cloud Run
- Memory persistence patterns
- Session management
- Cloud Run configuration for agents

**Relevant to:**
- R5: Dual memory wiring (Session + Memory Bank)
- R3: Cloud Run as gateway (with proper separation)
- Agent state management

### 3. Getting Started with Agent Engine - Terraform Deployment
**File:** `tutorial_get_started_with_agent_engine_terraform_deployment.ipynb`
**Size:** 49KB
**Source:** [GoogleCloudPlatform/generative-ai](https://github.com/GoogleCloudPlatform/generative-ai/blob/main/agents/agent_engine/tutorial_get_started_with_agent_engine_terraform_deployment.ipynb)

**Topics Covered:**
- Terraform infrastructure for Vertex AI Agent Engine
- Agent Engine resource provisioning
- Docker container deployment to Agent Engine
- Infrastructure as Code (IaC) best practices
- CI/CD integration patterns

**Relevant to:**
- R2: Vertex AI Agent Engine runtime deployment
- R4: CI-only deployments (Terraform + GitHub Actions)
- Phase 4: Infrastructure setup (infra/)
- Docker container deployment workflow

---

## How to Use These Notebooks

### Local Jupyter
```bash
cd 000-docs/001-usermanual
jupyter notebook
```

### Google Colab
1. Go to [Google Colab](https://colab.research.google.com/)
2. File → Upload notebook
3. Select notebook from this directory

### VS Code
```bash
code 000-docs/001-usermanual/tutorial_multi_agent_systems_on_vertexai_with_claude.ipynb
```

---

## Relationship to Bob's Brain

These notebooks demonstrate patterns used in Bob's Brain:

| Notebook Topic | Bob's Brain Implementation |
|----------------|----------------------------|
| **Multi-Agent Systems** | A2A protocol in `my_agent/a2a_card.py` |
| **Agent Engine Deployment** | Container runtime in `my_agent/agent.py` |
| **Memory Services** | Dual memory in `create_runner()` (R5) |
| **Cloud Run Deployment** | Gateways in `service/` (R3 compliant) |
| **Session Management** | `auto_save_session_to_memory()` callback |
| **Terraform Deployment** | Infrastructure in `infra/` (Phase 4) |

---

## Key Differences: Bob's Brain Hard Mode

While these notebooks are excellent references, Bob's Brain enforces stricter rules:

### ✅ What We Keep
- ADK LlmAgent for agent implementation
- Vertex AI Agent Engine for production runtime
- Session + Memory Bank dual memory pattern
- A2A protocol for agent discovery

### ⚠️ What We Change
- **R3: Cloud Run Role** - Bob's Brain uses Cloud Run ONLY as a protocol gateway (proxy to Agent Engine via REST), NOT as an agent runtime
- **R4: CI-Only Deploys** - All deployments via GitHub Actions, not manual gcloud commands
- **R8: Drift Detection** - Automatic scanning blocks framework violations

---

## Additional Resources

- **Google ADK Docs:** https://cloud.google.com/vertex-ai/docs/agent-development-kit
- **Vertex AI Agent Engine:** https://cloud.google.com/vertex-ai/docs/agent-engine
- **A2A Protocol Spec:** https://github.com/google/adk-python/blob/main/docs/a2a.md
- **Bob's Brain CLAUDE.md:** Hard mode rules (R1-R8) and implementation guide

---

## Deployment Status

### Production System (Already Deployed) ✅

**Location:** `bob-vertex-agent/`

Bob's Brain is **already deployed and running** in production:
- **Project:** `bobs-brain`
- **Slack webhook:** `https://slack-webhook-eow2wytafa-uc.a.run.app`
- **Runtime:** Vertex AI Agent Engine + Cloud Functions
- **Status:** Operational ✅

**No redeployment needed.** The production system is working.

### Hard Mode Implementation (Reference/Code Complete)

**Location:** `my_agent/`, `service/`, `infra/terraform/`

The Hard Mode version is **code complete** but **not deployed**:
- All phases complete (1-4)
- Terraform infrastructure ready
- Docker configurations prepared
- Documentation comprehensive

**Purpose:** Reference implementation demonstrating Hard Mode architecture (R1-R8 compliance).

**Decision:** No deployment planned. Existing production system is sufficient.

---

## Notes

- These notebooks are maintained by Google Cloud
- Last downloaded: 2025-11-11
- Check source repos for updates
- Notebooks may contain patterns that violate Bob's Brain hard mode (e.g., running Runner in Cloud Run)
- Use as reference, adapt to follow R1-R8 constraints

---

**Category:** User Manual
**Audience:** Developers implementing agents with ADK
**Maintenance:** Download latest versions periodically from source repos
**Deployment Status:** Production system deployed in `bob-vertex-agent/`, Hard Mode reference in `my_agent/`
