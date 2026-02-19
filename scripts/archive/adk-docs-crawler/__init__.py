"""
Bob's Brain ADK Documentation Crawler

A production-ready crawler for extracting ADK documentation and preparing it for RAG.

Modules:
    config: Configuration management with environment validation
    adk_docs_crawler: Main crawler for ADK documentation site
    adk_docs_extract: Content extraction and parsing
    adk_docs_chunker: RAG-optimized chunking
    adk_docs_uploader: GCS upload and storage management
"""

__version__ = "1.0.0"
__author__ = "Bob's Brain Team"

from .config import CrawlerConfig, load_config

__all__ = ["CrawlerConfig", "load_config"]
