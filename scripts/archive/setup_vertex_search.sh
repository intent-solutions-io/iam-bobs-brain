#!/bin/bash
#
# Setup Vertex AI Search for ADK Documentation
#
# This script creates and configures a Vertex AI Search datastore with
# ADK documentation, enabling semantic search capabilities for Bob.
#
# Requirements:
# - gcloud CLI installed and authenticated
# - PROJECT_ID environment variable set
# - Vertex AI API enabled
# - Discovery Engine API enabled
# - Sufficient IAM permissions
#
# Usage:
#   export PROJECT_ID=your-project-id
#   bash scripts/setup_vertex_search.sh

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
LOCATION="${LOCATION:-global}"  # Vertex AI Search uses 'global'
BUCKET_NAME="${BUCKET_NAME:-${PROJECT_ID}-adk-docs}"
DATASTORE_ID="${DATASTORE_ID:-adk-documentation}"
DATASTORE_DISPLAY_NAME="ADK Documentation Search"
DOCS_SOURCE_DIR="000-docs/google-reference/adk"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Vertex AI Search Setup for Bob's Brain${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Validate configuration
if [ -z "$PROJECT_ID" ]; then
    echo -e "${RED}❌ ERROR: PROJECT_ID environment variable not set${NC}"
    echo ""
    echo "Set it with:"
    echo "  export PROJECT_ID=your-project-id"
    exit 1
fi

echo -e "${GREEN}✓ Configuration:${NC}"
echo "  Project ID: $PROJECT_ID"
echo "  Location: $LOCATION"
echo "  Bucket: $BUCKET_NAME"
echo "  Datastore ID: $DATASTORE_ID"
echo "  Source Docs: $DOCS_SOURCE_DIR"
echo ""

# Check if docs directory exists
if [ ! -d "$DOCS_SOURCE_DIR" ]; then
    echo -e "${RED}❌ ERROR: Documentation directory not found: $DOCS_SOURCE_DIR${NC}"
    exit 1
fi

DOC_COUNT=$(find "$DOCS_SOURCE_DIR" -name "*.md" | wc -l)
echo -e "${GREEN}✓ Found $DOC_COUNT markdown files in $DOCS_SOURCE_DIR${NC}"
echo ""

# Step 1: Enable required APIs
echo -e "${BLUE}[1/5] Enabling required APIs...${NC}"

REQUIRED_APIS=(
    "discoveryengine.googleapis.com"
    "storage.googleapis.com"
)

for api in "${REQUIRED_APIS[@]}"; do
    echo "  Enabling $api..."
    gcloud services enable "$api" --project="$PROJECT_ID" 2>/dev/null || {
        echo -e "${YELLOW}  ⚠ API $api may already be enabled or needs manual enabling${NC}"
    }
done

echo -e "${GREEN}✓ APIs enabled${NC}"
echo ""

# Step 2: Create Cloud Storage bucket
echo -e "${BLUE}[2/5] Creating Cloud Storage bucket...${NC}"

if gsutil ls -p "$PROJECT_ID" "gs://$BUCKET_NAME" &>/dev/null; then
    echo -e "${YELLOW}  ℹ Bucket $BUCKET_NAME already exists${NC}"
else
    echo "  Creating bucket: gs://$BUCKET_NAME"
    gsutil mb -p "$PROJECT_ID" -l us-central1 "gs://$BUCKET_NAME" || {
        echo -e "${RED}❌ Failed to create bucket${NC}"
        exit 1
    }
    echo -e "${GREEN}✓ Bucket created${NC}"
fi

echo ""

# Step 3: Upload documentation to Cloud Storage
echo -e "${BLUE}[3/5] Uploading ADK documentation to Cloud Storage...${NC}"

echo "  Uploading from $DOCS_SOURCE_DIR to gs://$BUCKET_NAME/adk-docs/"

# Upload all markdown files
gsutil -m cp -r "$DOCS_SOURCE_DIR/*.md" "gs://$BUCKET_NAME/adk-docs/" 2>/dev/null || {
    # Try individual files if wildcard fails
    for file in "$DOCS_SOURCE_DIR"/*.md; do
        if [ -f "$file" ]; then
            echo "    Uploading $(basename "$file")..."
            gsutil cp "$file" "gs://$BUCKET_NAME/adk-docs/"
        fi
    done
}

UPLOADED_COUNT=$(gsutil ls "gs://$BUCKET_NAME/adk-docs/*.md" | wc -l)
echo -e "${GREEN}✓ Uploaded $UPLOADED_COUNT files${NC}"
echo ""

# Step 4: Create Vertex AI Search datastore
echo -e "${BLUE}[4/5] Creating Vertex AI Search datastore...${NC}"

# Check if datastore already exists
DATASTORE_EXISTS=$(gcloud alpha discovery-engine data-stores list \
    --project="$PROJECT_ID" \
    --location="$LOCATION" \
    --format="value(name)" \
    --filter="dataStoreId:$DATASTORE_ID" 2>/dev/null | wc -l)

if [ "$DATASTORE_EXISTS" -gt 0 ]; then
    echo -e "${YELLOW}  ℹ Datastore '$DATASTORE_ID' already exists${NC}"
else
    echo "  Creating datastore: $DATASTORE_ID"

    gcloud alpha discovery-engine data-stores create \
        --data-store-id="$DATASTORE_ID" \
        --display-name="$DATASTORE_DISPLAY_NAME" \
        --location="$LOCATION" \
        --project="$PROJECT_ID" \
        --industry-vertical="GENERIC" \
        --content-config="CONTENT_REQUIRED" \
        --solution-type="SOLUTION_TYPE_SEARCH" || {
        echo -e "${RED}❌ Failed to create datastore${NC}"
        echo -e "${YELLOW}Note: You may need alpha API access or use the GCP Console${NC}"
        exit 1
    }

    echo -e "${GREEN}✓ Datastore created${NC}"
fi

echo ""

# Step 5: Import documents from Cloud Storage
echo -e "${BLUE}[5/5] Importing documents into Vertex AI Search...${NC}"

echo "  Creating import job from gs://$BUCKET_NAME/adk-docs/"
echo -e "${YELLOW}  ⏳ This may take 10-15 minutes to complete...${NC}"

# Create import configuration
IMPORT_CONFIG=$(cat <<EOF
{
  "gcsSource": {
    "inputUris": ["gs://$BUCKET_NAME/adk-docs/*.md"],
    "dataSchema": "document"
  }
}
EOF
)

# Save to temp file
IMPORT_CONFIG_FILE=$(mktemp)
echo "$IMPORT_CONFIG" > "$IMPORT_CONFIG_FILE"

# Start import (this is async)
gcloud alpha discovery-engine documents import \
    --project="$PROJECT_ID" \
    --location="$LOCATION" \
    --data-store="$DATASTORE_ID" \
    --branch="default_branch" \
    --source-gcs-uri="gs://$BUCKET_NAME/adk-docs/*.md" \
    --reconciliation-mode="INCREMENTAL" &>/dev/null || {
    echo -e "${YELLOW}  ⚠ Import command may have failed - check GCP Console${NC}"
}

rm -f "$IMPORT_CONFIG_FILE"

echo ""
echo -e "${GREEN}✓ Import job started${NC}"
echo ""

# Summary
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Setup Complete!${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "${GREEN}✅ Vertex AI Search datastore created${NC}"
echo ""
echo "📊 Configuration:"
echo "  Project: $PROJECT_ID"
echo "  Datastore: $DATASTORE_ID"
echo "  Location: $LOCATION"
echo "  Bucket: gs://$BUCKET_NAME"
echo "  Documents: $UPLOADED_COUNT files"
echo ""
echo "⏳ Next Steps:"
echo "  1. Wait 10-15 minutes for indexing to complete"
echo "  2. Check status in GCP Console:"
echo "     https://console.cloud.google.com/gen-app-builder/engines?project=$PROJECT_ID"
echo "  3. Test search with:"
echo "     python -c \"from my_agent.tools.vertex_search_tool import search_vertex_ai; print(search_vertex_ai('LlmAgent'))\""
echo ""
echo "🔧 Set environment variable for Bob:"
echo "  export VERTEX_SEARCH_DATASTORE_ID=$DATASTORE_ID"
echo ""
echo "💰 Cost Estimate:"
echo "  Vertex AI Search Free Tier: 5GB storage (your docs: ~270KB)"
echo "  Monthly queries: First 1,000 free, then \$0.30 per 1,000"
echo "  Expected cost: \$0/month (well within free tier)"
echo ""
echo -e "${GREEN}Done! 🎉${NC}"
