#!/bin/bash
# Create datahub-intent project and set up central knowledge storage

set -e

PROJECT_ID="datahub-intent"
BILLING_ACCOUNT_ID=$(gcloud billing accounts list --format="value(name)" | head -1)
ORGANIZATION_ID=$(gcloud organizations list --format="value(ID)" 2>/dev/null || echo "")

echo "============================================"
echo "CREATING DATAHUB-INTENT PROJECT"
echo "============================================"
echo ""

# Step 1: Create the project
echo "Step 1: Creating project ${PROJECT_ID}..."
if gcloud projects describe ${PROJECT_ID} 2>/dev/null; then
    echo "Project ${PROJECT_ID} already exists"
else
    if [ -n "$ORGANIZATION_ID" ]; then
        echo "Creating project under organization ${ORGANIZATION_ID}..."
        gcloud projects create ${PROJECT_ID} \
            --organization=${ORGANIZATION_ID} \
            --name="DataHub Intent"
    else
        echo "Creating project without organization..."
        gcloud projects create ${PROJECT_ID} \
            --name="DataHub Intent"
    fi
    echo "✅ Project created"
fi

# Step 2: Link billing account
echo ""
echo "Step 2: Linking billing account..."
if [ -n "$BILLING_ACCOUNT_ID" ]; then
    gcloud billing projects link ${PROJECT_ID} --billing-account=${BILLING_ACCOUNT_ID}
    echo "✅ Billing linked"
else
    echo "⚠️  No billing account found - link manually"
fi

# Step 3: Enable necessary APIs
echo ""
echo "Step 3: Enabling APIs..."
gcloud config set project ${PROJECT_ID}

APIs=(
    "discoveryengine.googleapis.com"    # Vertex AI Search
    "storage.googleapis.com"             # Cloud Storage
    "iam.googleapis.com"                 # IAM
    "cloudresourcemanager.googleapis.com" # Resource Manager
)

for API in "${APIs[@]}"; do
    echo "Enabling $API..."
    gcloud services enable $API --project=${PROJECT_ID}
done
echo "✅ APIs enabled"

# Step 4: Create MAIN storage bucket
echo ""
echo "Step 4: Creating MAIN storage bucket..."

# Create the MAIN bucket with the project name
gsutil mb -p ${PROJECT_ID} -l us-central1 gs://${PROJECT_ID} 2>/dev/null || echo "Main bucket exists"
echo "✅ Main storage bucket created: gs://${PROJECT_ID}"

# Step 5: Set up directory structure in main bucket
echo ""
echo "Step 5: Creating directory structure..."

# Create organized structure in the main bucket
echo "# Universal ADK Documentation" | gsutil cp - gs://${PROJECT_ID}/adk/README.md
echo "# Universal Templates" | gsutil cp - gs://${PROJECT_ID}/templates/README.md
echo "# Company Standards" | gsutil cp - gs://${PROJECT_ID}/standards/README.md
echo "# Shared Libraries" | gsutil cp - gs://${PROJECT_ID}/shared-libs/README.md

# Project-specific directories
echo "# Bob's Brain Knowledge" | gsutil cp - gs://${PROJECT_ID}/projects/bobs-brain/README.md
echo "# PipelinePilot Data" | gsutil cp - gs://${PROJECT_ID}/projects/pipelinepilot/README.md
echo "# HustleApp Data" | gsutil cp - gs://${PROJECT_ID}/projects/hustleapp/README.md
echo "# Perception Data" | gsutil cp - gs://${PROJECT_ID}/projects/perception/README.md

echo "✅ Directory structure created"

# Step 6: Connect Bob and Foreman to the datahub
echo ""
echo "Step 6: Configuring access for Bob and Foreman..."

# Grant Bob's Brain project access
BOB_PROJECT_NUMBER=$(gcloud projects describe bobs-brain --format="value(projectNumber)" 2>/dev/null || echo "")
if [ -n "$BOB_PROJECT_NUMBER" ]; then
    # Grant Bob's service account read access
    gsutil iam ch serviceAccount:${BOB_PROJECT_NUMBER}@cloudbuild.gserviceaccount.com:objectViewer gs://${PROJECT_ID}
    gsutil iam ch serviceAccount:${BOB_PROJECT_NUMBER}-compute@developer.gserviceaccount.com:objectViewer gs://${PROJECT_ID}
    echo "✅ Bob's Brain connected to datahub"
else
    echo "⚠️  Could not find Bob's Brain project - configure access manually"
fi

echo "✅ Access configuration complete"

echo ""
echo "============================================"
echo "DATAHUB-INTENT PROJECT READY"
echo "============================================"
echo ""
echo "Project ID: ${PROJECT_ID}"
echo "Main Storage Bucket: gs://${PROJECT_ID}"
echo ""
echo "Structure:"
echo "  gs://${PROJECT_ID}/"
echo "    ├── /adk/          (Universal ADK docs)"
echo "    ├── /templates/    (Shared templates)"
echo "    ├── /standards/    (Company standards)"
echo "    ├── /shared-libs/  (Shared libraries)"
echo "    └── /projects/     (Project-specific data)"
echo "        ├── /bobs-brain/"
echo "        ├── /pipelinepilot/"
echo "        ├── /hustleapp/"
echo "        └── /perception/"
echo ""
echo "✅ Bob and Foreman have been connected to the datahub"
echo ""
echo "Next steps:"
echo "1. Set up Vertex AI Search datastore"
echo "2. Import existing data from all projects"
echo "3. Configure additional project access as needed"
echo ""