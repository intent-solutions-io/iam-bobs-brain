"""
RAG-optimized chunking for ADK documentation.

Splits documents into semantic chunks suitable for embedding and retrieval.
Preserves heading context and code blocks.
"""

import hashlib
import logging
from typing import Dict, List

from .config import CrawlerConfig

logger = logging.getLogger(__name__)


class DocumentChunker:
    """Chunk documents for RAG ingestion."""

    def __init__(self, config: CrawlerConfig):
        """
        Initialize chunker.

        Args:
            config: Crawler configuration with max_chunk_tokens
        """
        self.config = config
        self.chunk_counter = 0

    def estimate_tokens(self, text: str) -> int:
        """
        Estimate token count for text.

        Uses rough heuristic: 1 token ≈ 4 characters.

        Args:
            text: Text to estimate

        Returns:
            Estimated token count
        """
        return len(text) // 4

    def split_long_section(self, section: Dict, max_tokens: int) -> List[Dict]:
        """
        Split a long section into smaller chunks.

        Args:
            section: Section dictionary with text and code_blocks
            max_tokens: Maximum tokens per chunk

        Returns:
            List of section chunks
        """
        text = section['text']
        code_blocks = section.get('code_blocks', [])

        # If section is small enough, return as-is
        if self.estimate_tokens(text) <= max_tokens:
            return [section]

        # Split by paragraphs
        paragraphs = text.split('\n\n')
        chunks = []
        current_chunk_text = []
        current_token_count = 0

        for para in paragraphs:
            para_tokens = self.estimate_tokens(para)

            # If single paragraph is too large, split by sentences
            if para_tokens > max_tokens:
                sentences = para.split('. ')
                for sentence in sentences:
                    sentence_tokens = self.estimate_tokens(sentence)
                    if current_token_count + sentence_tokens > max_tokens:
                        # Save current chunk
                        if current_chunk_text:
                            chunks.append({
                                'heading_path': section['heading_path'],
                                'text': '\n\n'.join(current_chunk_text),
                                'code_blocks': []  # Code blocks stay with first chunk
                            })
                        current_chunk_text = [sentence]
                        current_token_count = sentence_tokens
                    else:
                        current_chunk_text.append(sentence)
                        current_token_count += sentence_tokens
            else:
                # Check if adding paragraph exceeds limit
                if current_token_count + para_tokens > max_tokens:
                    # Save current chunk
                    if current_chunk_text:
                        chunks.append({
                            'heading_path': section['heading_path'],
                            'text': '\n\n'.join(current_chunk_text),
                            'code_blocks': []
                        })
                    current_chunk_text = [para]
                    current_token_count = para_tokens
                else:
                    current_chunk_text.append(para)
                    current_token_count += para_tokens

        # Add remaining text as final chunk
        if current_chunk_text:
            chunks.append({
                'heading_path': section['heading_path'],
                'text': '\n\n'.join(current_chunk_text),
                'code_blocks': []
            })

        # Attach code blocks to first chunk only
        if chunks and code_blocks:
            chunks[0]['code_blocks'] = code_blocks

        logger.debug(f"Split section into {len(chunks)} chunks")
        return chunks

    def chunk_document(self, doc: Dict) -> List[Dict]:
        """
        Chunk a document into RAG-optimized pieces.

        Args:
            doc: Document dictionary from extractor

        Returns:
            List of chunk dictionaries
        """
        chunks = []

        for section in doc['sections']:
            # Split section if too large
            section_chunks = self.split_long_section(
                section,
                self.config.max_chunk_tokens
            )

            for chunk_section in section_chunks:
                # Generate chunk ID
                chunk_content = (
                    f"{doc['doc_id']}"
                    f"{'|'.join(chunk_section['heading_path'])}"
                    f"{chunk_section['text'][:100]}"
                )
                chunk_id = hashlib.sha256(chunk_content.encode()).hexdigest()[:16]

                chunk = {
                    'chunk_id': chunk_id,
                    'doc_id': doc['doc_id'],
                    'url': doc['url'],
                    'title': doc['title'],
                    'heading_path': chunk_section['heading_path'],
                    'text': chunk_section['text'],
                    'code_blocks': chunk_section.get('code_blocks', []),
                    'last_crawled_at': doc['last_crawled_at'],
                    'source_type': doc['source_type'],
                    'estimated_tokens': self.estimate_tokens(chunk_section['text'])
                }
                chunks.append(chunk)
                self.chunk_counter += 1

        logger.info(f"Generated {len(chunks)} chunks from document {doc['doc_id']}")
        return chunks


def chunk_all_documents(documents: List[Dict], config: CrawlerConfig) -> List[Dict]:
    """
    Chunk all documents for RAG ingestion.

    Args:
        documents: List of extracted documents
        config: Crawler configuration

    Returns:
        List of chunk dictionaries
    """
    chunker = DocumentChunker(config)
    all_chunks = []

    for doc in documents:
        try:
            doc_chunks = chunker.chunk_document(doc)
            all_chunks.extend(doc_chunks)
        except Exception as e:
            logger.error(f"Failed to chunk document {doc['doc_id']}: {e}")
            continue

    logger.info(
        f"Successfully chunked {len(documents)} documents into "
        f"{len(all_chunks)} chunks"
    )
    return all_chunks
