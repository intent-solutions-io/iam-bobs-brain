#!/usr/bin/env python3
"""
Main entry point for ADK documentation crawler.

Usage:
    python -m tools.adk_docs_crawler
    or
    make crawl-adk-docs
"""

import json
import logging
import sys
from pathlib import Path

from .adk_docs_chunker import chunk_all_documents
from .adk_docs_crawler import ADKDocsCrawler
from .adk_docs_extract import extract_all_documents
from .adk_docs_uploader import upload_to_gcs
from .config import load_config, validate_gcp_credentials


def setup_logging(verbose: bool = False) -> None:
    """
    Setup logging configuration.

    Args:
        verbose: Enable debug logging
    """
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def main() -> int:
    """
    Main pipeline execution.

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    # Parse simple arguments
    verbose = "--verbose" in sys.argv or "-v" in sys.argv

    # Setup logging
    setup_logging(verbose)
    logger = logging.getLogger(__name__)

    logger.info("=" * 80)
    logger.info("Bob's Brain - ADK Documentation Crawler")
    logger.info("=" * 80)

    try:
        # 1. Load configuration
        logger.info("\n[1/6] Loading configuration...")
        config = load_config()

        # Validate GCP credentials
        logger.info("\n[2/6] Validating GCP credentials...")
        if not validate_gcp_credentials():
            logger.error(
                "GCP credentials validation failed. Set GOOGLE_APPLICATION_CREDENTIALS or run 'gcloud auth application-default login'"
            )
            return 1

        # Create tmp directory
        tmp_dir = Path(config.tmp_dir)
        tmp_dir.mkdir(exist_ok=True)

        # 3. Crawl documentation
        logger.info("\n[3/6] Crawling ADK documentation...")
        crawler = ADKDocsCrawler(config)
        crawled_pages = crawler.crawl_site()

        if not crawled_pages:
            logger.error("No pages crawled. Check start URL and network connectivity.")
            return 1

        # Save crawl manifest
        manifest_path = tmp_dir / "adk_docs_manifest.json"
        crawler.save_manifest(str(manifest_path))

        # 4. Extract content
        logger.info("\n[4/6] Extracting content...")
        documents = extract_all_documents(crawled_pages)

        if not documents:
            logger.error("No documents extracted. Check crawler output.")
            return 1

        # Save documents to tmp
        docs_path = tmp_dir / "docs.jsonl"
        with open(docs_path, "w", encoding="utf-8") as f:
            for doc in documents:
                f.write(json.dumps(doc, ensure_ascii=False) + "\n")
        logger.info(f"Documents saved to: {docs_path}")

        # 5. Chunk for RAG
        logger.info("\n[5/6] Chunking documents for RAG...")
        chunks = chunk_all_documents(documents, config)

        if not chunks:
            logger.error("No chunks generated. Check extraction output.")
            return 1

        # Save chunks to tmp
        chunks_path = tmp_dir / "chunks.jsonl"
        with open(chunks_path, "w", encoding="utf-8") as f:
            for chunk in chunks:
                f.write(json.dumps(chunk, ensure_ascii=False) + "\n")
        logger.info(f"Chunks saved to: {chunks_path}")

        # 6. Upload to GCS
        logger.info("\n[6/6] Uploading to Google Cloud Storage...")
        with open(manifest_path, encoding="utf-8") as f:
            manifest = json.load(f)

        gcs_uris = upload_to_gcs(documents, chunks, manifest, config)

        # Summary
        logger.info("\n" + "=" * 80)
        logger.info("PIPELINE COMPLETE!")
        logger.info("=" * 80)
        logger.info(f"Pages crawled:      {len(crawled_pages)}")
        logger.info(f"Documents extracted: {len(documents)}")
        logger.info(f"Chunks generated:   {len(chunks)}")
        logger.info("")
        logger.info("GCS Upload Results:")
        for key, uri in gcs_uris.items():
            logger.info(f"  {key}: {uri}")
        logger.info("")
        logger.info(f"Local files saved to: {tmp_dir}/")
        logger.info("=" * 80)

        return 0

    except KeyboardInterrupt:
        logger.warning("\nCrawl interrupted by user")
        return 1
    except Exception as e:
        logger.error(f"Pipeline failed: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
