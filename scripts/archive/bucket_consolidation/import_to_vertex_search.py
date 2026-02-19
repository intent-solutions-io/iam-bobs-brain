#!/usr/bin/env python3
"""
Import all data to Vertex AI Search Datastore
Consolidates everything into bob-vertex-agent-datastore
"""

import logging
from typing import List

from google.cloud import discoveryengine_v1 as discoveryengine
from google.cloud import storage

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
PROJECT_ID = "bobs-brain"
LOCATION = "us"  # Datastore is in US region
DATASTORE_ID = "bob-vertex-agent-datastore"
RAG_BUCKET = "bobs-brain-bob-vertex-agent-rag"


def list_bucket_files(bucket_name: str) -> List[str]:
    """List all files in a GCS bucket."""
    client = storage.Client(project=PROJECT_ID)
    bucket = client.bucket(bucket_name)

    files = []
    for blob in bucket.list_blobs():
        files.append(f"gs://{bucket_name}/{blob.name}")

    return files


def import_documents_from_gcs(gcs_uris: List[str]):
    """Import documents from GCS to Vertex AI Search."""
    client = discoveryengine.DocumentServiceClient()

    parent = f"projects/{PROJECT_ID}/locations/{LOCATION}/dataStores/{DATASTORE_ID}/branches/default_branch"

    # Create import request
    request = discoveryengine.ImportDocumentsRequest(
        parent=parent,
        gcs_source=discoveryengine.GcsSource(input_uris=gcs_uris),
        reconciliation_mode="INCREMENTAL",  # Don't overwrite existing docs
    )

    # Start the import operation
    operation = client.import_documents(request=request)

    logger.info(f"Import operation started: {operation.name}")
    logger.info("This is a long-running operation. Check the console for progress.")

    return operation


def check_datastore_status():
    """Check current status of the datastore."""
    client = discoveryengine.DataStoreServiceClient()

    datastore_name = (
        f"projects/{PROJECT_ID}/locations/{LOCATION}/dataStores/{DATASTORE_ID}"
    )

    try:
        datastore = client.get_data_store(name=datastore_name)
        logger.info(f"Datastore: {datastore.display_name}")
        logger.info(f"State: {datastore.state}")
        return True
    except Exception as e:
        logger.error(f"Error accessing datastore: {e}")
        return False


def main():
    """Main consolidation workflow."""
    print("=" * 60)
    print("VERTEX AI SEARCH CONSOLIDATION")
    print("=" * 60)
    print(f"\nTarget Datastore: {DATASTORE_ID}")
    print("Current: 8,718 documents, 109.87 MiB")
    print("")

    # Step 1: Check datastore
    print("Step 1: Checking datastore access...")
    if not check_datastore_status():
        print("❌ Cannot access datastore. Check permissions.")
        return
    print("✅ Datastore accessible\n")

    # Step 2: List files to import
    print("Step 2: Listing files in RAG bucket...")
    try:
        rag_files = list_bucket_files(RAG_BUCKET)
        print(f"Found {len(rag_files)} files in gs://{RAG_BUCKET}")

        # Filter for markdown and text files
        docs_to_import = [f for f in rag_files if f.endswith((".md", ".txt", ".json"))]
        print(f"Documents to import: {len(docs_to_import)}")
    except Exception as e:
        print(f"❌ Error listing bucket: {e}")
        docs_to_import = []

    # Step 3: Import to Vertex AI Search
    if docs_to_import:
        print("\nStep 3: Starting import to Vertex AI Search...")
        print("Files to import:")
        for doc in docs_to_import[:5]:  # Show first 5
            print(f"  - {doc}")
        if len(docs_to_import) > 5:
            print(f"  ... and {len(docs_to_import) - 5} more")

        confirm = input("\nProceed with import? (y/n): ")
        if confirm.lower() == "y":
            operation = import_documents_from_gcs(docs_to_import)
            print(f"\n✅ Import started: {operation.name}")
            print("Monitor progress in the Cloud Console:")
            print(
                f"https://console.cloud.google.com/vertex-ai/search/dataStores/{DATASTORE_ID}"
            )

    # Step 4: Cleanup plan
    print("\n" + "=" * 60)
    print("CLEANUP PLAN")
    print("=" * 60)
    print("\nAfter import completes, delete these empty buckets:")
    print("  gsutil rm -r gs://bobs-brain-knowledge")
    print("  gsutil rm -r gs://bobs-brain-adk-staging")
    print("  gsutil rm -r gs://bobs-brain-bob-vertex-agent-logs")
    print("\nAfter verifying RAG data is imported:")
    print("  gsutil rm -r gs://bobs-brain-bob-vertex-agent-rag")

    print("\n✅ Final state: ALL data in bob-vertex-agent-datastore")


if __name__ == "__main__":
    main()
