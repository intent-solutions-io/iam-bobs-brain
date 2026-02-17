"""
Indexing and Knowledge Management Tools for iam-index agent.

These tools handle documentation indexing, knowledge base queries,
and Vertex AI Search integration.
"""

import hashlib
import json
import os
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from agents.iam_contracts import IndexEntry


def index_adk_docs(doc_source: str = "google.github.io/adk-docs") -> str:
    """
    Index official ADK documentation for semantic search.

    Args:
        doc_source: Source URL or path for ADK documentation

    Returns:
        JSON string with indexing results
    """
    try:
        # In production, this would connect to actual ADK docs
        # For now, return mock successful indexing

        indexed_sections = [
            "Getting Started Guide",
            "Agent Development",
            "Tool Implementation",
            "Memory Services",
            "A2A Protocol",
            "Deployment Guide",
            "Best Practices"
        ]

        result = {
            "status": "success",
            "source": doc_source,
            "documents_indexed": len(indexed_sections),
            "sections": indexed_sections,
            "datastore": "adk-documentation",
            "timestamp": datetime.utcnow().isoformat(),
            "index_stats": {
                "total_pages": 47,
                "total_tokens": 125000,
                "avg_relevance_score": 0.92
            }
        }

        return json.dumps(result, indent=2)

    except Exception as e:
        return json.dumps({
            "status": "error",
            "error": str(e),
            "source": doc_source
        })


def index_project_docs(doc_path: str = "000-docs") -> str:
    """
    Index project-specific documentation from 000-docs/.

    Args:
        doc_path: Path to documentation directory

    Returns:
        JSON string with indexing results
    """
    try:
        # Check if path exists
        docs_dir = Path(doc_path)
        if not docs_dir.exists():
            docs_dir = Path(f"/home/jeremy/000-projects/iams/bobs-brain/{doc_path}")

        indexed_docs = []

        # Find all markdown files
        if docs_dir.exists():
            for doc_file in docs_dir.glob("*.md"):
                # Parse document naming convention NNN-CC-ABCD-description.md
                filename = doc_file.name
                parts = filename.split("-", 3)

                if len(parts) >= 3:
                    doc_info = {
                        "filename": filename,
                        "number": parts[0],
                        "category": parts[1],
                        "type": parts[2] if len(parts) > 2 else "",
                        "size_bytes": doc_file.stat().st_size
                    }
                    indexed_docs.append(doc_info)

        result = {
            "status": "success",
            "path": str(docs_dir),
            "documents_indexed": len(indexed_docs),
            "documents": indexed_docs[:10],  # First 10 for brevity
            "datastore": "project-documentation",
            "timestamp": datetime.utcnow().isoformat(),
            "categories_found": list(set(d.get("category", "") for d in indexed_docs)),
            "total_size_kb": sum(d.get("size_bytes", 0) for d in indexed_docs) // 1024
        }

        return json.dumps(result, indent=2)

    except Exception as e:
        return json.dumps({
            "status": "error",
            "error": str(e),
            "path": doc_path
        })


def query_knowledge_base(query: str, max_results: int = 5) -> str:
    """
    Search the indexed knowledge base for relevant information.

    Args:
        query: Search query string
        max_results: Maximum number of results to return

    Returns:
        JSON string with search results
    """
    try:
        # In production, this would query Vertex AI Search
        # For now, return mock search results based on query keywords

        mock_results = []

        # Simple keyword matching for demonstration
        if "memory" in query.lower() or "dual" in query.lower():
            mock_results.append({
                "title": "Dual Memory Wiring Pattern",
                "source": "ADK Documentation",
                "relevance": 0.95,
                "snippet": "Implement dual memory with VertexAiSessionService for short-term and VertexAiMemoryBankService for long-term persistence...",
                "url": "https://google.github.io/adk-docs/memory/dual-wiring"
            })

        if "a2a" in query.lower() or "agent" in query.lower():
            mock_results.append({
                "title": "A2A Protocol Implementation",
                "source": "000-docs/045-AT-ARCH-a2a-protocol.md",
                "relevance": 0.89,
                "snippet": "Agent-to-Agent communication uses AgentCards for discovery and REST endpoints for invocation...",
                "url": "file://000-docs/045-AT-ARCH-a2a-protocol.md"
            })

        if "tool" in query.lower():
            mock_results.append({
                "title": "Tool Implementation Guide",
                "source": "ADK Documentation",
                "relevance": 0.87,
                "snippet": "Tools in ADK agents must return JSON-serializable results and handle errors gracefully...",
                "url": "https://google.github.io/adk-docs/tools/implementation"
            })

        # Default result if no keyword matches
        if not mock_results:
            mock_results.append({
                "title": "ADK Agent Development Overview",
                "source": "ADK Documentation",
                "relevance": 0.75,
                "snippet": "The Agent Development Kit (ADK) provides a framework for building production-grade AI agents...",
                "url": "https://google.github.io/adk-docs/"
            })

        result = {
            "status": "success",
            "query": query,
            "results_count": len(mock_results[:max_results]),
            "results": mock_results[:max_results],
            "datastore": "unified-knowledge-base",
            "search_latency_ms": 127,
            "timestamp": datetime.utcnow().isoformat()
        }

        return json.dumps(result, indent=2)

    except Exception as e:
        return json.dumps({
            "status": "error",
            "error": str(e),
            "query": query
        })


def sync_vertex_search(datastore_id: str = "adk-documentation") -> str:
    """
    Synchronize local indices with Vertex AI Search.

    Args:
        datastore_id: Vertex AI Search datastore identifier

    Returns:
        JSON string with sync status
    """
    try:
        # In production, this would sync with actual Vertex AI Search
        # For now, return mock sync status

        sync_stats = {
            "documents_added": 12,
            "documents_updated": 5,
            "documents_removed": 2,
            "total_documents": 147,
            "index_size_mb": 3.4
        }

        result = {
            "status": "success",
            "datastore_id": datastore_id,
            "sync_stats": sync_stats,
            "last_sync": datetime.utcnow().isoformat(),
            "next_sync": "in 6 hours",
            "sync_duration_seconds": 4.7,
            "vertex_search_config": {
                "project_id": os.getenv("PROJECT_ID", "unknown"),
                "location": os.getenv("LOCATION", "us-central1"),
                "search_tier": "FREE_TIER",
                "data_size_gb": 0.003
            }
        }

        return json.dumps(result, indent=2)

    except Exception as e:
        return json.dumps({
            "status": "error",
            "error": str(e),
            "datastore_id": datastore_id
        })


def generate_index_entry(
    title: str,
    source: str,
    content_type: str,
    summary: str,
    tags: Optional[List[str]] = None,
    keywords: Optional[List[str]] = None
) -> str:
    """
    Generate an IndexEntry object for new content.

    Args:
        title: Title of the content
        source: File path or URL
        content_type: Type of content (code, doc, config, test, example)
        summary: Brief summary of the content
        tags: Optional list of tags
        keywords: Optional list of keywords

    Returns:
        JSON string with IndexEntry data
    """
    try:
        # Validate content_type
        valid_types = ["code", "doc", "config", "test", "example"]
        if content_type not in valid_types:
            content_type = "doc"  # Default to doc

        # Generate a simple entry ID
        entry_id = hashlib.md5(f"{title}{source}".encode()).hexdigest()[:12]

        # Create IndexEntry
        entry = IndexEntry(
            title=title,
            source=source,
            content_type=content_type,  # type: ignore
            summary=summary,
            entry_id=entry_id,
            tags=tags or [],
            keywords=keywords or [],
            last_updated=datetime.utcnow(),
            relevance_score=0.85  # Default relevance
        )

        result = {
            "status": "success",
            "index_entry": entry.to_dict(),
            "datastore": "unified-knowledge-base",
            "indexed": True,
            "timestamp": datetime.utcnow().isoformat()
        }

        return json.dumps(result, indent=2, default=str)

    except Exception as e:
        return json.dumps({
            "status": "error",
            "error": str(e),
            "title": title,
            "source": source
        })


def analyze_knowledge_gaps(scope: str = "all") -> str:
    """
    Analyze the knowledge base to identify gaps and outdated content.

    Args:
        scope: Scope of analysis (all, adk, project, agents)

    Returns:
        JSON string with gap analysis report
    """
    try:
        # In production, this would analyze actual indices
        # For now, return mock gap analysis

        gaps = []
        outdated = []
        recommendations = []

        # Simulate gap detection based on scope
        if scope in ["all", "agents"]:
            gaps.append({
                "area": "Agent Testing",
                "description": "Limited documentation on unit testing ADK agents",
                "priority": "high",
                "suggested_action": "Create testing guide for ADK agents"
            })
            gaps.append({
                "area": "Error Handling",
                "description": "No comprehensive error handling patterns documented",
                "priority": "medium",
                "suggested_action": "Document error handling best practices"
            })

        if scope in ["all", "adk"]:
            outdated.append({
                "document": "ADK Migration Guide v1.0",
                "last_updated": "2024-09-15",
                "issue": "References deprecated APIs",
                "suggested_action": "Update to v2.0 API references"
            })

        if scope in ["all", "project"]:
            gaps.append({
                "area": "A2A Integration",
                "description": "Missing examples of multi-agent A2A workflows",
                "priority": "medium",
                "suggested_action": "Document A2A workflow patterns"
            })

        # Generate recommendations
        recommendations.append("Schedule quarterly knowledge base audits")
        recommendations.append("Implement automated freshness checks")
        recommendations.append("Create agent-specific documentation templates")

        result = {
            "status": "success",
            "scope": scope,
            "analysis_date": datetime.utcnow().isoformat(),
            "gaps_found": len(gaps),
            "gaps": gaps,
            "outdated_found": len(outdated),
            "outdated": outdated,
            "recommendations": recommendations,
            "coverage_stats": {
                "adk_docs": "87%",
                "project_docs": "92%",
                "agent_docs": "78%",
                "overall": "86%"
            },
            "next_audit": "2025-02-19"
        }

        return json.dumps(result, indent=2)

    except Exception as e:
        return json.dumps({
            "status": "error",
            "error": str(e),
            "scope": scope
        })


# Additional helper functions for internal use

def _calculate_relevance(query: str, content: str) -> float:
    """Calculate relevance score between query and content."""
    # Simple keyword matching for demonstration
    query_words = set(query.lower().split())
    content_words = set(content.lower().split())

    if not query_words:
        return 0.0

    overlap = len(query_words & content_words)
    return min(overlap / len(query_words), 1.0)


def _extract_keywords(text: str, max_keywords: int = 10) -> List[str]:
    """Extract keywords from text."""
    # Simple extraction for demonstration
    # In production, would use NLP techniques
    import re

    # Remove common words
    stopwords = {"the", "is", "at", "which", "on", "a", "an", "and", "or", "but", "in", "with", "to", "for"}

    words = re.findall(r'\b[a-z]+\b', text.lower())
    keywords = [w for w in words if w not in stopwords and len(w) > 3]

    # Count frequencies
    from collections import Counter
    word_freq = Counter(keywords)

    # Return top keywords
    return [word for word, _ in word_freq.most_common(max_keywords)]
