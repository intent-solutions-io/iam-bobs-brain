#!/usr/bin/env python3
"""
ADK Documentation Ingestion Script for Vertex AI Grounding

This script downloads and organizes ADK documentation for storage in GCS bucket
to be used as grounding knowledge for Bob's Brain agents.

Target Bucket: bob-vertex-agent-datastore or appropriate Vertex AI storage
"""

import json
import logging
import os
from datetime import datetime
from typing import Dict

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ADK Documentation URLs to ingest
ADK_DOCS_URLS = [
    # Core Tools Documentation
    {
        "url": "https://google.github.io/adk-docs/tools/",
        "category": "tools",
        "title": "ADK Tools Overview",
        "description": "Main tools documentation for Google ADK"
    },
    {
        "url": "https://google.github.io/adk-docs/tools/built-in-tools/",
        "category": "tools",
        "title": "ADK Built-in Tools",
        "description": "Pre-built tools available in ADK including GoogleSearchToolset, BigQueryToolset, etc."
    },

    # Custom Tools Documentation
    {
        "url": "https://google.github.io/adk-docs/tools-custom/",
        "category": "custom-tools",
        "title": "ADK Custom Tools",
        "description": "How to create custom tools for ADK agents"
    },
    {
        "url": "https://google.github.io/adk-docs/tools-custom/function-tools/",
        "category": "custom-tools",
        "title": "ADK Function Tools",
        "description": "Creating function-based custom tools with proper signatures"
    },
    {
        "url": "https://google.github.io/adk-docs/tools-custom/mcp-tools/",
        "category": "custom-tools",
        "title": "ADK MCP Tools",
        "description": "Model Context Protocol tools for external integrations"
    },

    # Google Cloud Integrations
    {
        "url": "https://google.github.io/adk-docs/tools/google-cloud/mcp-toolbox-for-databases/",
        "category": "gcp-tools",
        "title": "MCP Toolbox for Databases",
        "description": "Database integration tools via MCP for CloudSQL, Firestore, BigQuery, etc."
    },

    # Additional Research Papers
    {
        "url": "https://arxiv.org/pdf/2201.11903",
        "category": "research",
        "title": "Chain-of-Thought Prompting Research",
        "description": "Research paper on chain-of-thought prompting techniques",
        "filename": "chain_of_thought_prompting_2201.11903.pdf"
    }
]

def create_metadata(doc_info: Dict) -> Dict:
    """Create metadata for document storage."""
    return {
        "source_url": doc_info["url"],
        "category": doc_info["category"],
        "title": doc_info["title"],
        "description": doc_info["description"],
        "ingestion_timestamp": datetime.utcnow().isoformat(),
        "content_hash": "",  # Will be filled after downloading
        "file_type": "pdf" if doc_info["url"].endswith(".pdf") else "html",
        "agent_relevance": ["bob", "iam-adk", "iam-index"],  # Agents that need this knowledge
        "tags": [
            "adk",
            "google-adk",
            "vertex-ai",
            "agent-development-kit",
            doc_info["category"]
        ]
    }

def prepare_storage_structure():
    """Prepare the directory structure for storing documents."""
    base_dir = "knowledge_store"
    categories = ["tools", "custom-tools", "gcp-tools", "research", "metadata"]

    for category in categories:
        os.makedirs(f"{base_dir}/{category}", exist_ok=True)

    logger.info(f"Created storage structure in {base_dir}/")
    return base_dir

def generate_manifest():
    """Generate a manifest file for all documents to be ingested."""
    manifest = {
        "version": "1.0",
        "created": datetime.utcnow().isoformat(),
        "purpose": "ADK documentation grounding for Bob's Brain agents",
        "target_bucket": "bobs-brain-knowledge",  # Using existing knowledge bucket
        "documents": []
    }

    for doc in ADK_DOCS_URLS:
        doc_entry = {
            **doc,
            "metadata": create_metadata(doc),
            "storage_path": f"adk-docs/{doc['category']}/{doc.get('filename', doc['title'].lower().replace(' ', '_') + '.html')}"
        }
        manifest["documents"].append(doc_entry)

    # Save manifest
    with open("knowledge_store/manifest.json", "w") as f:
        json.dump(manifest, f, indent=2)

    logger.info(f"Generated manifest with {len(manifest['documents'])} documents")
    return manifest

def create_download_script():
    """Create a shell script to download all documents."""
    script_content = """#!/bin/bash
# ADK Documentation Download Script
# Downloads all ADK documentation for grounding storage

set -e

echo "Starting ADK documentation download..."
mkdir -p knowledge_store/{tools,custom-tools,gcp-tools,research}

# Download HTML pages (will need proper web scraping)
echo "Note: HTML pages need proper web scraping with BeautifulSoup or Playwright"
echo "For now, creating placeholder commands..."

# Tools documentation
# wget -O knowledge_store/tools/adk_tools_overview.html "https://google.github.io/adk-docs/tools/"
# wget -O knowledge_store/tools/adk_builtin_tools.html "https://google.github.io/adk-docs/tools/built-in-tools/"

# Custom tools documentation
# wget -O knowledge_store/custom-tools/adk_custom_tools.html "https://google.github.io/adk-docs/tools-custom/"
# wget -O knowledge_store/custom-tools/adk_function_tools.html "https://google.github.io/adk-docs/tools-custom/function-tools/"
# wget -O knowledge_store/custom-tools/adk_mcp_tools.html "https://google.github.io/adk-docs/tools-custom/mcp-tools/"

# GCP tools documentation
# wget -O knowledge_store/gcp-tools/mcp_toolbox_databases.html "https://google.github.io/adk-docs/tools/google-cloud/mcp-toolbox-for-databases/"

# Research papers (these can be downloaded directly)
echo "Downloading research paper..."
wget -O knowledge_store/research/chain_of_thought_prompting_2201.11903.pdf "https://arxiv.org/pdf/2201.11903"

echo "Download complete!"
echo "Next steps:"
echo "1. Use a proper web scraper for HTML pages"
echo "2. Convert HTML to clean text/markdown"
echo "3. Upload to GCS bucket: bob-vertex-agent-datastore"
"""

    with open("knowledge_store/download.sh", "w") as f:
        f.write(script_content)

    os.chmod("knowledge_store/download.sh", 0o755)
    logger.info("Created download script: knowledge_store/download.sh")

def create_upload_script():
    """Create a script to upload documents to GCS."""
    script_content = """#!/bin/bash
# Upload ADK Documentation to GCS for Vertex AI Grounding

set -e

PROJECT_ID="bobs-brain"
BUCKET_NAME="bob-vertex-agent-datastore"  # Or create if doesn't exist

echo "Uploading ADK documentation to GCS..."

# Create bucket if it doesn't exist
gsutil mb -p $PROJECT_ID gs://$BUCKET_NAME 2>/dev/null || echo "Bucket already exists"

# Upload all documentation with proper metadata
gsutil -m cp -r knowledge_store/* gs://$BUCKET_NAME/adk-grounding/

# Set metadata for searchability
gsutil -m setmeta -h "Content-Type:text/html" gs://$BUCKET_NAME/adk-grounding/tools/*.html
gsutil -m setmeta -h "Content-Type:text/html" gs://$BUCKET_NAME/adk-grounding/custom-tools/*.html
gsutil -m setmeta -h "Content-Type:text/html" gs://$BUCKET_NAME/adk-grounding/gcp-tools/*.html
gsutil -m setmeta -h "Content-Type:application/pdf" gs://$BUCKET_NAME/adk-grounding/research/*.pdf

echo "Upload complete!"
echo "Documents available at: gs://$BUCKET_NAME/adk-grounding/"
"""

    with open("knowledge_store/upload_to_gcs.sh", "w") as f:
        f.write(script_content)

    os.chmod("knowledge_store/upload_to_gcs.sh", 0o755)
    logger.info("Created upload script: knowledge_store/upload_to_gcs.sh")

def main():
    """Main execution function."""
    logger.info("Starting ADK documentation ingestion preparation...")

    # Prepare storage
    base_dir = prepare_storage_structure()

    # Generate manifest
    manifest = generate_manifest()

    # Create helper scripts
    create_download_script()
    create_upload_script()

    # Summary
    print("\n" + "="*60)
    print("ADK Documentation Ingestion Prepared!")
    print("="*60)
    print(f"\n📁 Storage structure created in: {base_dir}/")
    print(f"📄 Manifest with {len(manifest['documents'])} documents")
    print("📥 Download script: knowledge_store/download.sh")
    print("☁️  Upload script: knowledge_store/upload_to_gcs.sh")
    print("\n🎯 Target GCS bucket: bob-vertex-agent-datastore")
    print("\nNext steps:")
    print("1. Run download script to fetch documentation")
    print("2. Process HTML pages to clean text/markdown")
    print("3. Run upload script to push to GCS")
    print("4. Configure Vertex AI Search to index the bucket")
    print("5. Wire agents to use grounded search")

if __name__ == "__main__":
    main()
