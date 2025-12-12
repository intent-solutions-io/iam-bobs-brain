# Phase 33: Dev End-to-End Simulation

**Date:** 2025-12-11
**Status:** In Progress
**Branch:** `feature/phase-33-dev-e2e-simulation`

## Objective

Wire a repeatable dev E2E simulation path that exercises:
- Bob on Vertex AI Agent Engine (dev env)
- The Slack gateway (dev workspace / dev config)

## Inputs

- Phase 23/24 AARs (Inline deploy, Slack Bob CI)
- Agent Engine deployment scripts
- Slack gateway Terraform/module design
- `config/agent_engine_envs.yaml` (from Phase 31)

## Non-Goals

- Real prod traffic or config changes
- Calling gcloud directly
- Changing prod environment variables or secrets

## Deliverables

1. **Agent Engine Simulation Script**
   - `scripts/simulate_bob_agent_engine_dev.py`
   - Reads dev config from `config/agent_engine_envs.yaml`
   - Constructs test query for Bob
   - Prints request shape (simulation mode if no credentials)

2. **Slack Event Simulation Script**
   - `scripts/simulate_slack_event_local.py`
   - Builds fake Slack event payload
   - Invokes gateway handler locally
   - Skips signature verification if secrets missing

3. **Make Targets**
   - `simulate-dev-agent-engine`
   - `simulate-dev-slack-local`
   - `simulate-dev-e2e-all`

## Implementation Steps

1. Create plan doc (this file)
2. Create Agent Engine simulation script
3. Create Slack event simulation script
4. Add Make targets
5. Run validation checks
6. Create AAR

---
**Last Updated:** 2025-12-11
