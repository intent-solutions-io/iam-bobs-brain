# RAG Operations Runbook

**Date:** 2025-12-12
**Phase:** 47 - RAG / Knowledge Base Wiring

## Overview

Operational procedures for maintaining Bob's Brain RAG infrastructure.

## Daily Operations

### Health Check

```bash
# Check datastore status
make check-rag-readiness

# Expected: ✅ RAG READY
```

### Monitor Document Count

```bash
gcloud ai search datastores describe bobs-brain-prod-rag \
  --location=us \
  --project=bobs-brain \
  --format="value(documentCount)"
```

## Data Refresh Procedures

### Incremental Update

Add new documents without reindexing existing:

```bash
gcloud ai search documents import \
  --datastore=bobs-brain-prod-rag \
  --location=us \
  --project=bobs-brain \
  --gcs-uri="gs://datahub-intent/bobs-brain/**" \
  --reconciliation-mode=incremental
```

### Full Reindex

When document structure changes significantly:

```bash
# 1. Purge existing documents
gcloud ai search documents purge \
  --datastore=bobs-brain-prod-rag \
  --location=us \
  --project=bobs-brain \
  --force

# 2. Re-import all documents
gcloud ai search documents import \
  --datastore=bobs-brain-prod-rag \
  --location=us \
  --project=bobs-brain \
  --gcs-uri="gs://datahub-intent/bobs-brain/**"

# 3. Monitor import status
gcloud ai search operations list \
  --location=us \
  --project=bobs-brain
```

### Scheduled Refresh

Configure via Cloud Scheduler:

```bash
# Create scheduled job for daily refresh
gcloud scheduler jobs create http rag-daily-refresh \
  --schedule="0 3 * * *" \
  --uri="https://discoveryengine.googleapis.com/v1/projects/bobs-brain/locations/us/dataStores/bobs-brain-prod-rag:importDocuments" \
  --message-body='{"gcsSource":{"inputUris":["gs://datahub-intent/bobs-brain/**"]},"reconciliationMode":"INCREMENTAL"}' \
  --oauth-service-account-email=SA_EMAIL \
  --location=us-central1
```

## Incident Response

### High Query Latency

1. **Check datastore health:**
   ```bash
   gcloud ai search datastores describe bobs-brain-prod-rag \
     --location=us --project=bobs-brain
   ```

2. **Check for ongoing imports:**
   ```bash
   gcloud ai search operations list \
     --location=us --project=bobs-brain --filter="metadata.state!=SUCCEEDED"
   ```

3. **Scale up if needed:**
   - Vertex AI Search auto-scales, but check quota limits
   - Review Quotas & Limits in GCP Console

### Search Returns No Results

1. **Verify datastore has documents:**
   ```bash
   gcloud ai search datastores describe bobs-brain-prod-rag \
     --location=us --project=bobs-brain --format="value(documentCount)"
   ```

2. **Check document import status:**
   ```bash
   gcloud ai search operations list \
     --location=us --project=bobs-brain
   ```

3. **Test with known document:**
   ```bash
   # Search for a document you know exists
   python -c "
   from agents.tools.vertex_search import get_bob_vertex_search_tool
   tool = get_bob_vertex_search_tool()
   print(tool.search('KNOWN_DOCUMENT_KEYWORD'))
   "
   ```

### Permission Errors

1. **Verify service account roles:**
   ```bash
   gcloud projects get-iam-policy bobs-brain \
     --flatten="bindings[].members" \
     --filter="bindings.role:discoveryengine"
   ```

2. **Add missing role:**
   ```bash
   gcloud projects add-iam-policy-binding bobs-brain \
     --member="serviceAccount:SA_EMAIL" \
     --role="roles/discoveryengine.viewer"
   ```

### Stale Data

1. **Check last import time:**
   ```bash
   gcloud ai search operations list \
     --location=us --project=bobs-brain \
     --filter="metadata.@type:ImportDocumentsMetadata" \
     --limit=5 --sort-by="~createTime"
   ```

2. **Trigger refresh:**
   ```bash
   gcloud ai search documents import \
     --datastore=bobs-brain-prod-rag \
     --location=us --project=bobs-brain \
     --gcs-uri="gs://datahub-intent/bobs-brain/**" \
     --reconciliation-mode=incremental
   ```

## Monitoring

### Key Metrics

| Metric | Alert Threshold | Action |
|--------|-----------------|--------|
| Query latency P99 | > 5s | Check datastore health |
| Error rate | > 1% | Check permissions, quota |
| Document count | < expected | Verify import succeeded |

### Cloud Logging Queries

**Search queries:**
```
resource.type="discoveryengine.googleapis.com/DataStore"
resource.labels.data_store_id="bobs-brain-prod-rag"
```

**Import operations:**
```
resource.type="discoveryengine.googleapis.com/DataStore"
protoPayload.methodName="ImportDocuments"
```

**Errors:**
```
resource.type="discoveryengine.googleapis.com/DataStore"
severity>=ERROR
```

## Backup and Recovery

### Export Documents

```bash
# Export to GCS for backup
gcloud ai search documents export \
  --datastore=bobs-brain-prod-rag \
  --location=us --project=bobs-brain \
  --gcs-destination-prefix="gs://bobs-brain-backups/rag/"
```

### Restore from Backup

```bash
# Create new datastore
gcloud ai search datastores create bobs-brain-restored-rag \
  --location=us --project=bobs-brain --type=unstructured

# Import from backup
gcloud ai search documents import \
  --datastore=bobs-brain-restored-rag \
  --location=us --project=bobs-brain \
  --gcs-uri="gs://bobs-brain-backups/rag/**"
```

## Environment Management

### Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `VERTEX_SEARCH_PROJECT_ID` | GCP project | bobs-brain |
| `VERTEX_SEARCH_LOCATION` | Datastore region | us |
| `VERTEX_SEARCH_DATASTORE_ID_DEV` | Dev datastore | bobs-brain-dev-rag |
| `VERTEX_SEARCH_DATASTORE_ID_STAGING` | Stage datastore | bobs-brain-staging-rag |
| `VERTEX_SEARCH_DATASTORE_ID_PROD` | Prod datastore | bobs-brain-prod-rag |
| `DEPLOYMENT_ENV` | Current env | dev, staging, prod |

### Configuration Files

- `config/vertex_search.yaml` - Environment configurations
- `agents/config/rag.py` - Python configuration module
- `.env` - Runtime environment variables

## Contacts

| Role | Contact |
|------|---------|
| RAG Owner | Platform Team |
| GCP Admin | Infrastructure Team |
| On-call | PagerDuty |

---
**Last Updated:** 2025-12-12
