"""
GCS upload and storage management for ADK documentation.

Uploads extracted documents and chunks to Google Cloud Storage with proper
organization and versioning.
"""

import json
import logging
from datetime import datetime
from typing import Dict, List

from google.api_core import exceptions as gcp_exceptions
from google.cloud import storage

from .config import CrawlerConfig

logger = logging.getLogger(__name__)


class GCSUploader:
    """Upload ADK documentation to Google Cloud Storage."""

    def __init__(self, config: CrawlerConfig):
        """
        Initialize GCS uploader.

        Args:
            config: Crawler configuration with bucket name and project ID
        """
        self.config = config
        self.client = storage.Client(project=config.project_id)
        self.bucket = self.client.bucket(config.docs_bucket)

    def ensure_bucket_exists(self) -> bool:
        """
        Ensure GCS bucket exists, create if needed.

        Returns:
            True if bucket exists or was created, False otherwise
        """
        try:
            if self.bucket.exists():
                logger.info(f"GCS bucket exists: gs://{self.config.docs_bucket}")
                return True
            else:
                logger.warning(
                    f"GCS bucket does not exist: gs://{self.config.docs_bucket}. "
                    "Create it via Terraform or gcloud."
                )
                return False
        except gcp_exceptions.Forbidden as e:
            logger.error(f"Permission denied accessing bucket: {e}")
            return False
        except Exception as e:
            logger.error(f"Error checking bucket existence: {e}")
            return False

    def upload_jsonl(self, data: List[Dict], gcs_path: str) -> str:
        """
        Upload data as JSONL to GCS.

        Args:
            data: List of dictionaries to upload
            gcs_path: GCS path (without gs:// prefix)

        Returns:
            Full GCS URI

        Raises:
            RuntimeError: If upload fails
        """
        try:
            # Convert to JSONL
            jsonl_content = "\n".join(
                json.dumps(item, ensure_ascii=False) for item in data
            )

            # Upload to GCS
            blob = self.bucket.blob(gcs_path)
            blob.upload_from_string(jsonl_content, content_type="application/jsonl")

            gcs_uri = f"gs://{self.config.docs_bucket}/{gcs_path}"
            logger.info(f"Uploaded {len(data)} items to {gcs_uri}")
            return gcs_uri

        except Exception as e:
            logger.error(f"Failed to upload to {gcs_path}: {e}")
            raise RuntimeError(f"GCS upload failed: {e}")

    def upload_json(self, data: Dict, gcs_path: str) -> str:
        """
        Upload data as JSON to GCS.

        Args:
            data: Dictionary to upload
            gcs_path: GCS path (without gs:// prefix)

        Returns:
            Full GCS URI

        Raises:
            RuntimeError: If upload fails
        """
        try:
            # Convert to JSON
            json_content = json.dumps(data, indent=2, ensure_ascii=False)

            # Upload to GCS
            blob = self.bucket.blob(gcs_path)
            blob.upload_from_string(json_content, content_type="application/json")

            gcs_uri = f"gs://{self.config.docs_bucket}/{gcs_path}"
            logger.info(f"Uploaded JSON to {gcs_uri}")
            return gcs_uri

        except Exception as e:
            logger.error(f"Failed to upload to {gcs_path}: {e}")
            raise RuntimeError(f"GCS upload failed: {e}")

    def upload_pipeline_results(
        self, documents: List[Dict], chunks: List[Dict], manifest: Dict
    ) -> Dict[str, str]:
        """
        Upload all pipeline results to GCS.

        Args:
            documents: Extracted documents
            chunks: RAG chunks
            manifest: Crawl manifest

        Returns:
            Dictionary of GCS URIs for each uploaded file
        """
        logger.info("Uploading pipeline results to GCS...")

        # Ensure bucket exists
        if not self.ensure_bucket_exists():
            raise RuntimeError(
                f"Cannot upload to non-existent bucket: {self.config.docs_bucket}"
            )

        results = {}

        # Upload documents (overwrite main file)
        results["documents"] = self.upload_jsonl(documents, "adk-docs/raw/docs.jsonl")

        # Upload chunks (overwrite main file)
        results["chunks"] = self.upload_jsonl(chunks, "adk-docs/chunks/chunks.jsonl")

        # Upload manifest (keep timestamped versions)
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        results["manifest"] = self.upload_json(
            manifest, f"adk-docs/manifests/crawl-manifest-{timestamp}.json"
        )

        # Also upload latest manifest (overwrite)
        results["manifest_latest"] = self.upload_json(
            manifest, "adk-docs/manifests/crawl-manifest-latest.json"
        )

        logger.info("Pipeline results uploaded successfully:")
        for key, uri in results.items():
            logger.info(f"  {key}: {uri}")

        return results


def upload_to_gcs(
    documents: List[Dict], chunks: List[Dict], manifest: Dict, config: CrawlerConfig
) -> Dict[str, str]:
    """
    Main entry point for uploading to GCS.

    Args:
        documents: Extracted documents
        chunks: RAG chunks
        manifest: Crawl manifest
        config: Crawler configuration

    Returns:
        Dictionary of GCS URIs for uploaded files
    """
    uploader = GCSUploader(config)
    return uploader.upload_pipeline_results(documents, chunks, manifest)
