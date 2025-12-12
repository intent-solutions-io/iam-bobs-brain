# Phase 47: RAG / Knowledge Base Wiring – PLAN

**Date:** 2025-12-12
**Status:** In Progress
**Branch:** `feature/phase-47-rag-knowledge-base-wiring`

## Goals

Document and validate the existing RAG infrastructure, ensuring operational readiness.

### What This Phase Achieves

1. **Setup Guide** – Document how to configure Vertex AI Search for Bob
2. **Validation Script** – Enhance RAG readiness checks
3. **Terraform Documentation** – Document knowledge hub variables
4. **Operational Runbook** – RAG troubleshooting and maintenance

## Analysis

### Current State

The RAG infrastructure is largely complete:
- ✅ `config/vertex_search.yaml` - Configuration per environment
- ✅ `agents/shared_tools/vertex_search.py` - Tool factory
- ✅ `agents/config/rag.py` - RAG configuration module
- ✅ `agents/tools/vertex_search.py` - Tool wrapper
- ✅ `infra/terraform/knowledge_hub.tf` - GCS and Vertex Search stubs
- ✅ `scripts/check_rag_readiness.py` - ARV gate

### What Needs Enhancement

1. **Setup Guide** - Step-by-step datastore creation
2. **Environment Variables** - Document in .env.example
3. **CI Integration** - RAG validation in CI
4. **Runbook** - Operational procedures

## High-Level Steps

### Step 1: Create RAG Setup Guide

Document in `000-docs/225-GD-OPS-rag-setup-guide.md`:
- Prerequisites
- Datastore creation steps
- Configuration verification
- Troubleshooting

### Step 2: Update .env.example

Add RAG configuration section with all required variables.

### Step 3: Create Operational Runbook

Document in `000-docs/226-RB-OPS-rag-operations-runbook.md`:
- Data refresh procedures
- Monitoring and alerts
- Common issues and fixes

### Step 4: Documentation AAR

Create completion report.

## Design Decisions

### Why Not Create New Infrastructure?

The RAG infrastructure already exists:
- Datastores can be created via gcloud
- Terraform manages GCS buckets
- Code is ready to use real datastores

Focus on documentation and operational readiness.

## Files to Create/Modify

| File | Action | Purpose |
|------|--------|---------|
| `000-docs/224-AA-PLAN-*.md` | Create | This file |
| `000-docs/225-GD-OPS-rag-setup-guide.md` | Create | Setup guide |
| `000-docs/226-RB-OPS-rag-operations-runbook.md` | Create | Operational runbook |
| `.env.example` | Modify | Add RAG variables |
| `000-docs/227-AA-REPT-*.md` | Create | AAR |

---
**Last Updated:** 2025-12-12
