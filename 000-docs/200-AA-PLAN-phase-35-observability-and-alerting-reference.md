# Phase 35: Observability & Alerting Reference

**Date:** 2025-12-11
**Status:** In Progress
**Branch:** `feature/phase-35-observability-alerting-reference`

## Objective

Capture a reusable observability pattern for Bob/foreman with dashboard and alert definitions that can be used as a template for other repos.

## Inputs

- GCP Cloud Monitoring metrics for Vertex AI Agent Engine
- Cloud Run metrics for gateways
- Existing deployment patterns

## Non-Goals

- Actually creating dashboards/alerts via live API calls
- Hard-coding private project IDs
- Deploying monitoring infrastructure

## Deliverables

1. **Dashboard Definitions**
   - `infra/terraform/monitoring/dashboards_bobs_brain.json`
   - Panels for Agent Engine metrics, gateway health, latency

2. **Alert Definitions**
   - `infra/terraform/monitoring/alerts_bobs_brain.yaml`
   - Error rate, latency, dead agent alerts per environment

3. **Observability Playbook**
   - `000-docs/201-RB-OBSERVABILITY-bobs-brain-dashboard-and-alert-playbook.md`
   - Which metrics matter and why
   - How to adapt for new projects

4. **CLAUDE.md Update**
   - Observability checklist for deployments

## Implementation Steps

1. Create plan doc (this file)
2. Create monitoring directory structure
3. Create dashboard definition
4. Create alert definition
5. Create observability playbook
6. Update CLAUDE.md
7. Create AAR

---
**Last Updated:** 2025-12-11
