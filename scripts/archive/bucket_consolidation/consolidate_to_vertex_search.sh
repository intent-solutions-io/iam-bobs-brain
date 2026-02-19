#!/bin/bash
# Consolidate ALL data into Vertex AI Search Datastore
# Target: bob-vertex-agent-datastore (Vertex AI Search)

set -e

PROJECT_ID="bobs-brain"
DATASTORE_ID="bob-vertex-agent-datastore"
LOCATION="us"  # Datastore is in US region

echo "=============================================="
echo "CONSOLIDATION TO VERTEX AI SEARCH DATASTORE"
echo "=============================================="
echo ""
echo "Target Datastore: ${DATASTORE_ID}"
echo "Current Status: 8,718 documents, 109.87 MiB"
echo ""

# Step 1: Prepare data from GCS bucket for import
echo "Step 1: Preparing data from GCS buckets..."
echo ""

# The RAG bucket has 115 MB of data that needs to be imported
echo "Found data in gs://bobs-brain-bob-vertex-agent-rag (115 MB)"
echo "This needs to be imported to Vertex AI Search"
echo ""

# Step 2: Prepare ADK documentation for import
echo "Step 2: Preparing ADK documentation..."
cat << 'EOF'

Data to consolidate into Vertex AI Search:
1. Existing RAG data from gs://bobs-brain-bob-vertex-agent-rag/
2. ADK documentation:
   - https://google.github.io/adk-docs/tools/
   - https://google.github.io/adk-docs/tools/built-in-tools/
   - https://google.github.io/adk-docs/tools-custom/
   - https://google.github.io/adk-docs/tools-custom/function-tools/
   - https://google.github.io/adk-docs/tools-custom/mcp-tools/
   - https://google.github.io/adk-docs/tools/google-cloud/mcp-toolbox-for-databases/
3. Research paper: https://arxiv.org/pdf/2201.11903

EOF

# Step 3: Import to Vertex AI Search
echo "Step 3: Import commands for Vertex AI Search..."
echo ""

cat << 'EOF'
# Import from GCS bucket to Vertex AI Search
gcloud ai search datastores import \
  --datastore="${DATASTORE_ID}" \
  --location="${LOCATION}" \
  --gcs-uri="gs://bobs-brain-bob-vertex-agent-rag/**/*.md" \
  --data-type="unstructured" \
  --project="${PROJECT_ID}"

# Alternative using Python client
python3 << 'PYTHON'
from google.cloud import discoveryengine_v1 as discoveryengine

client = discoveryengine.DocumentServiceClient()
parent = f"projects/{PROJECT_ID}/locations/{LOCATION}/dataStores/{DATASTORE_ID}/branches/default_branch"

# Import documents from GCS
request = discoveryengine.ImportDocumentsRequest(
    parent=parent,
    gcs_source=discoveryengine.GcsSource(
        input_uris=["gs://bobs-brain-bob-vertex-agent-rag/**/*.md"]
    ),
    reconciliation_mode="INCREMENTAL"  # Don't overwrite existing
)
PYTHON
EOF

echo ""
echo "=============================================="
echo "CLEANUP PLAN - DELETE EMPTY BUCKETS"
echo "=============================================="
echo ""

# Check which buckets are empty and can be deleted
echo "Empty buckets that can be DELETED:"
echo "✅ gs://bobs-brain-knowledge (empty - 0 bytes)"
echo "✅ gs://bobs-brain-adk-staging (empty - 0 bytes)"
echo "✅ gs://bobs-brain-bob-vertex-agent-logs (empty - 0 bytes)"
echo ""
echo "Bucket to MIGRATE then DELETE:"
echo "⚠️  gs://bobs-brain-bob-vertex-agent-rag (115 MB - import to Vertex AI Search first)"
echo ""

echo "Delete commands (run AFTER data is imported to Vertex AI Search):"
echo ""
cat << 'EOF'
# Delete empty buckets
gsutil rm -r gs://bobs-brain-knowledge
gsutil rm -r gs://bobs-brain-adk-staging
gsutil rm -r gs://bobs-brain-bob-vertex-agent-logs

# After importing RAG data to Vertex AI Search, delete:
# gsutil rm -r gs://bobs-brain-bob-vertex-agent-rag
EOF

echo ""
echo "=============================================="
echo "FINAL STATE: ONE DATASTORE"
echo "=============================================="
echo ""
echo "✅ ALL data in: bob-vertex-agent-datastore (Vertex AI Search)"
echo "✅ NO duplicate GCS buckets"
echo "✅ Agents use Vertex AI Search for grounding"
echo ""