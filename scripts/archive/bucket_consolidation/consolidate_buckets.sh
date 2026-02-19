#!/bin/bash
# Bucket Consolidation Script - Merge all Bob's Brain buckets into ONE
# Target: bobs-brain-knowledge (the main bucket)

set -e

PROJECT_ID="bobs-brain"
MAIN_BUCKET="bobs-brain-knowledge"  # This will be our SINGLE bucket

echo "========================================="
echo "BUCKET CONSOLIDATION - ONE BUCKET POLICY"
echo "========================================="
echo ""
echo "Consolidating all data into: gs://${MAIN_BUCKET}"
echo ""

# List current buckets for reference
echo "Current buckets found:"
gsutil ls -p ${PROJECT_ID} | grep "bobs-brain" || true
echo ""

# Create organized structure in main bucket
echo "Creating organized structure in main bucket..."

# 1. Move RAG data if exists
echo "Checking bobs-brain-bob-vertex-agent-rag..."
if gsutil ls gs://bobs-brain-bob-vertex-agent-rag/ 2>/dev/null; then
    echo "Moving RAG data..."
    gsutil -m cp -r gs://bobs-brain-bob-vertex-agent-rag/* gs://${MAIN_BUCKET}/rag/ || true
    echo "RAG data moved to gs://${MAIN_BUCKET}/rag/"
fi

# 2. Move staging data if exists
echo "Checking bobs-brain-adk-staging..."
if gsutil ls gs://bobs-brain-adk-staging/ 2>/dev/null; then
    echo "Moving staging data..."
    gsutil -m cp -r gs://bobs-brain-adk-staging/* gs://${MAIN_BUCKET}/staging/ || true
    echo "Staging data moved to gs://${MAIN_BUCKET}/staging/"
fi

# 3. Move logs if exists (but consider if we need these)
echo "Checking bobs-brain-bob-vertex-agent-logs..."
if gsutil ls gs://bobs-brain-bob-vertex-agent-logs/ 2>/dev/null; then
    echo "Found logs bucket - consider if these are needed"
    # Logs might be auto-generated, so we may not want to move them
    echo "Logs location: gs://bobs-brain-bob-vertex-agent-logs/"
    echo "Recommendation: Keep logs separate or delete if not needed"
fi

echo ""
echo "========================================="
echo "PROPOSED SINGLE BUCKET STRUCTURE"
echo "========================================="
echo ""
echo "gs://${MAIN_BUCKET}/"
echo "├── adk-grounding/        # ADK documentation for agent grounding"
echo "│   ├── tools/           # ADK tools documentation"
echo "│   ├── custom-tools/    # Custom tools documentation"
echo "│   ├── gcp-tools/       # GCP integration docs"
echo "│   └── research/        # Research papers"
echo "├── rag/                 # RAG/retrieval data"
echo "│   └── (moved from bob-vertex-agent-rag)"
echo "├── staging/             # Staging/temp data"
echo "│   └── (moved from adk-staging)"
echo "├── agent-configs/       # Agent configurations"
echo "├── department-docs/     # Department documentation"
echo "└── vertex-search/       # Vertex AI Search indices"
echo ""

# Create directory structure
echo "Setting up directory structure..."
# Note: GCS doesn't have real directories, but we can create placeholder objects
echo "Structure will be created as files are uploaded"

echo ""
echo "========================================="
echo "CLEANUP PLAN (DO NOT RUN YET)"
echo "========================================="
echo ""
echo "After verifying data is safely moved, delete old buckets:"
echo ""
echo "# CAREFUL - Only run after verification:"
echo "# gsutil rb gs://bobs-brain-bob-vertex-agent-rag"
echo "# gsutil rb gs://bobs-brain-adk-staging"
echo "# gsutil rb gs://bobs-brain-bob-vertex-agent-logs  # If not needed"
echo ""
echo "========================================="
echo "IMPORTANT: Review before deleting!"
echo "========================================="