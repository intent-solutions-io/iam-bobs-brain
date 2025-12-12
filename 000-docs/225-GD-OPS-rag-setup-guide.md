# RAG Setup Guide for Bob's Brain

**Date:** 2025-12-12
**Phase:** 47 - RAG / Knowledge Base Wiring

## Overview

This guide walks through setting up Vertex AI Search for Bob and foreman RAG capabilities.

## Prerequisites

- GCP project with billing enabled
- Vertex AI API enabled
- Discovery Engine API enabled
- GCS bucket with documents to index

## Architecture

```
GCS Bucket                    Vertex AI Search
┌─────────────────┐           ┌─────────────────┐
│ datahub-intent/ │───────────│ Datastore       │
│ └── bobs-brain/ │  (index)  │ (unstructured)  │
│     └── docs/   │           └────────┬────────┘
└─────────────────┘                    │
                                       │ (query)
                            ┌──────────▼──────────┐
                            │ Bob Agent           │
                            │ (VertexAiSearchTool)│
                            └─────────────────────┘
```

## Step 1: Enable APIs

```bash
# Set your project
export PROJECT_ID=bobs-brain

# Enable required APIs
gcloud services enable discoveryengine.googleapis.com --project=$PROJECT_ID
gcloud services enable aiplatform.googleapis.com --project=$PROJECT_ID
```

## Step 2: Create Datastore

### Development Datastore

```bash
gcloud ai search datastores create bobs-brain-dev-rag \
  --location=us \
  --project=$PROJECT_ID \
  --type=unstructured \
  --display-name="Bob's Brain Dev RAG"
```

### Staging Datastore

```bash
gcloud ai search datastores create bobs-brain-staging-rag \
  --location=us \
  --project=$PROJECT_ID \
  --type=unstructured \
  --display-name="Bob's Brain Staging RAG"
```

### Production Datastore

```bash
gcloud ai search datastores create bobs-brain-prod-rag \
  --location=us \
  --project=$PROJECT_ID \
  --type=unstructured \
  --display-name="Bob's Brain Production RAG"
```

## Step 3: Import Documents

### From GCS

```bash
# Dev environment
gcloud ai search documents import \
  --datastore=bobs-brain-dev-rag \
  --location=us \
  --project=$PROJECT_ID \
  --gcs-uri="gs://datahub-intent-dev/bobs-brain/**"

# Production environment
gcloud ai search documents import \
  --datastore=bobs-brain-prod-rag \
  --location=us \
  --project=$PROJECT_ID \
  --gcs-uri="gs://datahub-intent/bobs-brain/**"
```

### Check Import Status

```bash
gcloud ai search operations list \
  --location=us \
  --project=$PROJECT_ID
```

## Step 4: Configure Environment Variables

Add to your `.env` file:

```bash
# Vertex AI Search Configuration
VERTEX_SEARCH_PROJECT_ID=bobs-brain
VERTEX_SEARCH_LOCATION=us

# Environment-specific datastore IDs
VERTEX_SEARCH_DATASTORE_ID_DEV=bobs-brain-dev-rag
VERTEX_SEARCH_DATASTORE_ID_STAGING=bobs-brain-staging-rag
VERTEX_SEARCH_DATASTORE_ID_PROD=bobs-brain-prod-rag

# Current environment (dev|staging|prod)
DEPLOYMENT_ENV=dev
```

## Step 5: Verify Configuration

### Run RAG Readiness Check

```bash
make check-rag-readiness-verbose
```

Expected output:
```
✅ Configuration Module: VALID
✅ Tool Factory: WORKING
✅ Documentation: PRESENT
✅ Config Template: COMPLETE

✅ RAG READY
```

### Test Search Query

```python
from agents.tools.vertex_search import get_bob_vertex_search_tool

tool = get_bob_vertex_search_tool()
results = tool.search("How do ADK agents work?")
print(results)
```

## Step 6: IAM Permissions

The Agent Engine service account needs permissions:

```bash
# Get the Agent Engine SA email
SA_EMAIL=$(gcloud iam service-accounts list \
  --project=$PROJECT_ID \
  --filter="displayName:Agent Engine" \
  --format="value(email)")

# Grant Discovery Engine viewer
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$SA_EMAIL" \
  --role="roles/discoveryengine.viewer"

# Grant GCS access for source documents
gcloud storage buckets add-iam-policy-binding gs://datahub-intent \
  --member="serviceAccount:$SA_EMAIL" \
  --role="roles/storage.objectViewer"
```

## Troubleshooting

### "Datastore not found"

- Verify datastore ID matches exactly
- Check location (us, eu, global)
- Ensure APIs are enabled

### "Permission denied"

- Check service account has discoveryengine.viewer role
- Verify GCS bucket access for source documents

### "No results returned"

- Check documents were imported successfully
- Verify search query syntax
- Check datastore has completed indexing

### Check Datastore Status

```bash
gcloud ai search datastores describe bobs-brain-dev-rag \
  --location=us \
  --project=$PROJECT_ID
```

## Configuration Files

### config/vertex_search.yaml

Environment-specific datastore configuration.

### agents/config/rag.py

RAG configuration module with validation.

### agents/tools/vertex_search.py

Tool factory for creating VertexAiSearchTool instances.

## Refresh Data

To refresh indexed documents:

```bash
# Re-import documents (creates new version)
gcloud ai search documents import \
  --datastore=bobs-brain-dev-rag \
  --location=us \
  --project=$PROJECT_ID \
  --gcs-uri="gs://datahub-intent-dev/bobs-brain/**" \
  --reconciliation-mode=incremental
```

For full refresh:

```bash
# Purge and re-import
gcloud ai search documents purge \
  --datastore=bobs-brain-dev-rag \
  --location=us \
  --project=$PROJECT_ID \
  --force

gcloud ai search documents import \
  --datastore=bobs-brain-dev-rag \
  --location=us \
  --project=$PROJECT_ID \
  --gcs-uri="gs://datahub-intent-dev/bobs-brain/**"
```

---
**Last Updated:** 2025-12-12
