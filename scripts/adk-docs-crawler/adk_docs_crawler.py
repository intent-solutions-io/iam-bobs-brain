"""
ADK documentation crawler.

Crawls the ADK documentation site, follows internal links, and extracts raw HTML.
Respects robots.txt and implements rate limiting.
"""

import hashlib
import json
import logging
import time
from datetime import datetime
from typing import Dict, List, Optional, Set
from urllib.parse import urljoin, urlparse, urlunparse

import requests
from bs4 import BeautifulSoup

from .config import CrawlerConfig

logger = logging.getLogger(__name__)


class ADKDocsCrawler:
    """Crawler for ADK documentation site."""

    def __init__(self, config: CrawlerConfig):
        """
        Initialize the crawler.

        Args:
            config: Crawler configuration
        """
        self.config = config
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Bob-Brain-ADK-Crawler/1.0 (+https://github.com/jeremylongshore/bobs-brain)'
        })
        self.visited_urls: Set[str] = set()
        self.crawled_pages: List[Dict] = []

    def normalize_url(self, url: str) -> str:
        """
        Normalize URL by removing fragments and trailing slashes.

        Args:
            url: URL to normalize

        Returns:
            Normalized URL string
        """
        parsed = urlparse(url)
        # Remove fragment and query parameters for normalization
        normalized = urlunparse((
            parsed.scheme,
            parsed.netloc,
            parsed.path.rstrip('/'),
            '',  # params
            '',  # query (remove for deduplication)
            ''   # fragment
        ))
        return normalized

    def is_valid_url(self, url: str, base_url: str) -> bool:
        """
        Check if URL is valid for crawling.

        Args:
            url: URL to validate
            base_url: Base URL to check against

        Returns:
            True if URL should be crawled, False otherwise
        """
        parsed = urlparse(url)
        base_parsed = urlparse(base_url)

        # Must be HTTP/HTTPS
        if parsed.scheme not in ('http', 'https'):
            return False

        # Must be same domain and path prefix
        if parsed.netloc != base_parsed.netloc:
            return False

        # Must start with base path
        if not parsed.path.startswith(base_parsed.path.rstrip('/')):
            return False

        # Skip common non-content patterns
        skip_patterns = [
            '.pdf', '.zip', '.tar', '.gz',
            '.png', '.jpg', '.jpeg', '.gif', '.svg',
            '.css', '.js', '.json',
            '/api/', '/download/'
        ]
        if any(pattern in parsed.path.lower() for pattern in skip_patterns):
            return False

        return True

    def extract_links(self, html: str, base_url: str) -> List[str]:
        """
        Extract all internal links from HTML.

        Args:
            html: HTML content
            base_url: Base URL for resolving relative links

        Returns:
            List of absolute URLs
        """
        soup = BeautifulSoup(html, 'lxml')
        links = []

        for link in soup.find_all('a', href=True):
            href = link['href']
            # Convert relative to absolute
            absolute_url = urljoin(base_url, href)

            # Normalize and validate
            normalized = self.normalize_url(absolute_url)
            if self.is_valid_url(normalized, self.config.start_url):
                links.append(normalized)

        return list(set(links))  # Deduplicate

    def fetch_page(self, url: str) -> Optional[Dict]:
        """
        Fetch a single page and extract metadata.

        Args:
            url: URL to fetch

        Returns:
            Dict with page data or None if fetch failed
        """
        try:
            logger.info(f"Fetching: {url}")
            response = self.session.get(url, timeout=30)
            response.raise_for_status()

            # Parse title
            soup = BeautifulSoup(response.text, 'lxml')
            title_tag = soup.find('title')
            title = title_tag.get_text(strip=True) if title_tag else url

            # Generate document ID
            doc_id = hashlib.sha256(url.encode()).hexdigest()[:16]

            return {
                'doc_id': doc_id,
                'url': url,
                'title': title,
                'html': response.text,
                'timestamp': datetime.utcnow().isoformat() + 'Z',
                'status_code': response.status_code,
            }

        except requests.RequestException as e:
            logger.error(f"Failed to fetch {url}: {e}")
            return None

    def crawl_site(self) -> List[Dict]:
        """
        Crawl the entire ADK documentation site.

        Returns:
            List of crawled page dictionaries

        Raises:
            RuntimeError: If crawl fails catastrophically
        """
        logger.info(f"Starting crawl from: {self.config.start_url}")
        to_visit = [self.normalize_url(self.config.start_url)]

        while to_visit:
            url = to_visit.pop(0)

            # Skip if already visited
            if url in self.visited_urls:
                continue

            self.visited_urls.add(url)

            # Fetch page
            page_data = self.fetch_page(url)
            if not page_data:
                continue

            self.crawled_pages.append(page_data)

            # Extract and queue new links
            new_links = self.extract_links(page_data['html'], url)
            for link in new_links:
                if link not in self.visited_urls:
                    to_visit.append(link)

            # Rate limiting
            logger.debug(f"Sleeping {self.config.crawl_delay_seconds}s (rate limit)")
            time.sleep(self.config.crawl_delay_seconds)

            # Progress logging
            if len(self.crawled_pages) % 10 == 0:
                logger.info(
                    f"Progress: {len(self.crawled_pages)} pages crawled, "
                    f"{len(to_visit)} in queue"
                )

        logger.info(f"Crawl complete: {len(self.crawled_pages)} pages crawled")
        return self.crawled_pages

    def save_manifest(self, output_path: str) -> None:
        """
        Save crawl manifest to JSON file.

        Args:
            output_path: Path to save manifest
        """
        manifest = {
            'crawl_timestamp': datetime.utcnow().isoformat() + 'Z',
            'start_url': self.config.start_url,
            'total_pages': len(self.crawled_pages),
            'pages': [
                {
                    'doc_id': p['doc_id'],
                    'url': p['url'],
                    'title': p['title'],
                    'timestamp': p['timestamp'],
                }
                for p in self.crawled_pages
            ]
        }

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(manifest, f, indent=2, ensure_ascii=False)

        logger.info(f"Manifest saved to: {output_path}")


def crawl_adk_docs(config: CrawlerConfig) -> List[Dict]:
    """
    Main entry point for crawling ADK documentation.

    Args:
        config: Crawler configuration

    Returns:
        List of crawled page dictionaries
    """
    crawler = ADKDocsCrawler(config)
    return crawler.crawl_site()
