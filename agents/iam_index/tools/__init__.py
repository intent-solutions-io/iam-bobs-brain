"""
Indexing and Knowledge Management Tools for iam-index agent.
"""

from .indexing_tools import (
    analyze_knowledge_gaps,
    generate_index_entry,
    index_adk_docs,
    index_project_docs,
    query_knowledge_base,
    sync_vertex_search,
)

__all__ = [
    "analyze_knowledge_gaps",
    "generate_index_entry",
    "index_adk_docs",
    "index_project_docs",
    "query_knowledge_base",
    "sync_vertex_search"
]
