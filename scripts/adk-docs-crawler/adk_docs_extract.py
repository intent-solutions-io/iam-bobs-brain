"""
Content extraction from ADK documentation HTML.

Parses HTML and extracts structured content including headings, body text,
and code blocks in canonical JSON format for RAG ingestion.
"""

import logging
from typing import Dict, List

from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class ContentExtractor:
    """Extract structured content from ADK documentation HTML."""

    def __init__(self):
        """Initialize content extractor."""
        self.code_block_counter = 0

    def extract_code_blocks(self, soup: BeautifulSoup) -> List[Dict]:
        """
        Extract code blocks with language detection.

        Args:
            soup: BeautifulSoup parsed HTML

        Returns:
            List of code block dictionaries
        """
        code_blocks = []

        # Find all code blocks (both <pre><code> and standalone <pre>)
        for pre in soup.find_all('pre'):
            code_tag = pre.find('code')
            if code_tag:
                code_text = code_tag.get_text()
                # Try to detect language from class
                classes = code_tag.get('class', [])
                language = None
                for cls in classes:
                    if cls.startswith('language-'):
                        language = cls.replace('language-', '')
                        break
                    elif cls.startswith('lang-'):
                        language = cls.replace('lang-', '')
                        break
            else:
                code_text = pre.get_text()
                language = None

            if code_text.strip():
                code_blocks.append({
                    'language': language or 'text',
                    'code': code_text.strip()
                })

        logger.debug(f"Extracted {len(code_blocks)} code blocks")
        return code_blocks

    def extract_sections(self, soup: BeautifulSoup) -> List[Dict]:
        """
        Extract content sections organized by heading hierarchy.

        Args:
            soup: BeautifulSoup parsed HTML

        Returns:
            List of section dictionaries with heading paths and content
        """
        sections = []
        current_heading_path: List[str] = []
        current_text_parts: List[str] = []
        current_code_blocks: List[Dict] = []

        # Remove script, style, nav, footer
        for tag in soup(['script', 'style', 'nav', 'footer', 'header']):
            tag.decompose()

        # Find main content area (common patterns)
        main_content = (
            soup.find('main') or
            soup.find('article') or
            soup.find('div', class_='content') or
            soup.find('div', id='content') or
            soup.body or
            soup
        )

        def finalize_section():
            """Save current section if it has content."""
            if current_text_parts or current_code_blocks:
                sections.append({
                    'heading_path': current_heading_path.copy(),
                    'text': '\n\n'.join(current_text_parts),
                    'code_blocks': current_code_blocks.copy()
                })
                current_text_parts.clear()
                current_code_blocks.clear()

        # Process elements in order
        for element in main_content.find_all(['h1', 'h2', 'h3', 'p', 'pre', 'ul', 'ol', 'div']):
            if element.name in ['h1', 'h2', 'h3']:
                # Finalize previous section
                finalize_section()

                # Update heading path
                level = int(element.name[1])  # h1 -> 1, h2 -> 2, etc.
                heading_text = element.get_text(strip=True)

                # Adjust heading path based on level
                current_heading_path = current_heading_path[:level-1]
                current_heading_path.append(heading_text)

                logger.debug(f"Section: {' > '.join(current_heading_path)}")

            elif element.name == 'pre':
                # Code block
                code_tag = element.find('code')
                if code_tag:
                    code_text = code_tag.get_text()
                    classes = code_tag.get('class', [])
                    language = None
                    for cls in classes:
                        if cls.startswith('language-'):
                            language = cls.replace('language-', '')
                            break
                else:
                    code_text = element.get_text()
                    language = None

                if code_text.strip():
                    current_code_blocks.append({
                        'language': language or 'text',
                        'code': code_text.strip()
                    })

            elif element.name in ['p', 'ul', 'ol', 'div']:
                # Regular text content
                text = element.get_text(strip=True)
                if text and len(text) > 10:  # Filter out very short snippets
                    current_text_parts.append(text)

        # Finalize last section
        finalize_section()

        logger.info(f"Extracted {len(sections)} sections")
        return sections

    def extract_content(self, html: str, url: str, doc_id: str, title: str, timestamp: str) -> Dict:
        """
        Extract structured content from HTML.

        Args:
            html: Raw HTML content
            url: Page URL
            doc_id: Document identifier
            title: Page title
            timestamp: Crawl timestamp

        Returns:
            Canonical document dictionary
        """
        logger.info(f"Extracting content from: {url}")
        soup = BeautifulSoup(html, 'lxml')

        # Extract sections
        sections = self.extract_sections(soup)

        # Build canonical document
        doc = {
            'doc_id': doc_id,
            'url': url,
            'title': title,
            'sections': sections,
            'last_crawled_at': timestamp,
            'source_type': 'adk-docs'
        }

        logger.info(f"Extracted {len(sections)} sections from {url}")
        return doc


def extract_all_documents(crawled_pages: List[Dict]) -> List[Dict]:
    """
    Extract content from all crawled pages.

    Args:
        crawled_pages: List of crawled page dictionaries from crawler

    Returns:
        List of extracted document dictionaries
    """
    extractor = ContentExtractor()
    documents = []

    for page in crawled_pages:
        try:
            doc = extractor.extract_content(
                html=page['html'],
                url=page['url'],
                doc_id=page['doc_id'],
                title=page['title'],
                timestamp=page['timestamp']
            )
            documents.append(doc)
        except Exception as e:
            logger.error(f"Failed to extract content from {page['url']}: {e}")
            continue

    logger.info(f"Successfully extracted {len(documents)}/{len(crawled_pages)} documents")
    return documents
