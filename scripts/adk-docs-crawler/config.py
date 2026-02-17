"""
Configuration management for ADK docs crawler.

Loads and validates configuration from environment variables with sensible defaults.
"""

import logging
import os
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class CrawlerConfig:
    """Configuration for ADK documentation crawler."""

    project_id: str
    docs_bucket: str
    crawler_sa_email: Optional[str]
    crawl_delay_seconds: float
    max_chunk_tokens: int
    start_url: str
    tmp_dir: str

    def __post_init__(self):
        """Validate configuration after initialization."""
        if not self.project_id:
            raise ValueError("GCP_PROJECT_ID is required")

        if self.crawl_delay_seconds < 0:
            raise ValueError("CRAWL_DELAY_SECONDS must be non-negative")

        if self.max_chunk_tokens <= 0:
            raise ValueError("MAX_CHUNK_TOKENS must be positive")

        logger.info("Crawler configuration loaded:")
        logger.info(f"  Project ID: {self.project_id}")
        logger.info(f"  Docs Bucket: {self.docs_bucket}")
        logger.info(f"  Crawl Delay: {self.crawl_delay_seconds}s")
        logger.info(f"  Max Chunk Tokens: {self.max_chunk_tokens}")
        logger.info(f"  Start URL: {self.start_url}")


def load_config() -> CrawlerConfig:
    """
    Load configuration from environment variables.

    Required environment variables:
        GCP_PROJECT_ID: Google Cloud project ID

    Optional environment variables:
        BOB_DOCS_BUCKET: GCS bucket name (default: {project_id}-adk-docs)
        CRAWLER_SA_EMAIL: Service account email for CI/CD
        CRAWL_DELAY_SECONDS: Delay between requests (default: 1.0)
        MAX_CHUNK_TOKENS: Maximum tokens per chunk (default: 1500)
        ADK_DOCS_START_URL: Starting URL for crawler (default: https://google.github.io/adk-docs/)
        CRAWLER_TMP_DIR: Temporary directory for files (default: ./tmp)

    Returns:
        CrawlerConfig: Validated configuration object

    Raises:
        ValueError: If required environment variables are missing or invalid
    """
    project_id = os.getenv("GCP_PROJECT_ID")
    if not project_id:
        raise ValueError(
            "GCP_PROJECT_ID environment variable is required. "
            "Set it in .env.crawler or export it."
        )

    # Default bucket name based on project ID
    default_bucket = f"{project_id}-adk-docs"
    docs_bucket = os.getenv("BOB_DOCS_BUCKET", default_bucket)

    # Optional service account email (for CI/CD)
    crawler_sa_email = os.getenv("CRAWLER_SA_EMAIL")

    # Crawl delay with validation
    try:
        crawl_delay_seconds = float(os.getenv("CRAWL_DELAY_SECONDS", "1.0"))
    except ValueError as e:
        raise ValueError(f"CRAWL_DELAY_SECONDS must be a number: {e}")

    # Max chunk tokens with validation
    try:
        max_chunk_tokens = int(os.getenv("MAX_CHUNK_TOKENS", "1500"))
    except ValueError as e:
        raise ValueError(f"MAX_CHUNK_TOKENS must be an integer: {e}")

    # Start URL for crawler
    start_url = os.getenv(
        "ADK_DOCS_START_URL",
        "https://google.github.io/adk-docs/"
    )

    # Temporary directory for intermediate files
    tmp_dir = os.getenv("CRAWLER_TMP_DIR", "./tmp")

    return CrawlerConfig(
        project_id=project_id,
        docs_bucket=docs_bucket,
        crawler_sa_email=crawler_sa_email,
        crawl_delay_seconds=crawl_delay_seconds,
        max_chunk_tokens=max_chunk_tokens,
        start_url=start_url,
        tmp_dir=tmp_dir,
    )


def validate_gcp_credentials() -> bool:
    """
    Validate that GCP credentials are available.

    Returns:
        bool: True if credentials are available, False otherwise
    """
    try:
        from google.auth import default
        credentials, project = default()
        logger.info(f"GCP credentials validated. Project: {project}")
        return True
    except Exception as e:
        logger.error(f"GCP credentials validation failed: {e}")
        return False
