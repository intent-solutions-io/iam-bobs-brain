"""
iam-index A2A AgentCard

Provides AgentCard for iam-index, the knowledge management specialist.

Enforces R7: SPIFFE ID must be included in card metadata.
"""

import os
from typing import Any, Dict, List

from pydantic import BaseModel, Field


class AgentCard(BaseModel):
    """AgentCard model for A2A protocol."""
    name: str = Field(..., description="Agent name")
    version: str = Field(..., description="Agent version")
    url: str = Field(..., description="Agent public URL")
    description: str = Field(..., description="Agent description (must include SPIFFE ID per R7)")
    capabilities: List[str] = Field(default_factory=list, description="Agent capabilities")
    default_input_modes: List[str] = Field(default_factory=lambda: ["text"], description="Supported input modes")
    default_output_modes: List[str] = Field(default_factory=lambda: ["text"], description="Supported output modes")
    skills: List[Dict[str, Any]] = Field(default_factory=list, description="Agent skills")


def get_agent_card() -> AgentCard:
    """Get iam-index's AgentCard."""
    app_name = os.getenv("APP_NAME", "iam-index")
    app_version = os.getenv("APP_VERSION", "0.10.0")
    public_url = os.getenv("PUBLIC_URL", "https://iam-index.intent.solutions")
    spiffe_id = os.getenv("AGENT_SPIFFE_ID", "spiffe://intent.solutions/agent/iam-index/dev/us-central1/0.10.0")

    description = f"""iam-index - Knowledge Management Specialist

**Identity:** {spiffe_id}

iam-index manages Vertex AI Search integration, indexes code and documentation, and maintains the knowledge base for department access.
"""

    capabilities = ["vertex_search_management", "code_indexing", "doc_indexing", "knowledge_base_maintenance"]

    skills = [
        {
            "skill_id": "iam_index.index_code_repository",
            "name": "Index Code Repository",
            "description": "Index code repository for searchability in Vertex AI Search",
            "input_schema": {
                "type": "object",
                "required": ["repo_path"],
                "properties": {
                    "repo_path": {"type": "string"},
                    "file_patterns": {"type": "array", "items": {"type": "string"}},
                    "exclude_patterns": {"type": "array", "items": {"type": "string"}}
                }
            },
            "output_schema": {
                "type": "object",
                "required": ["indexing_result"],
                "properties": {
                    "indexing_result": {
                        "type": "object",
                        "required": ["status", "files_indexed"],
                        "properties": {
                            "status": {"type": "string", "enum": ["SUCCESS", "PARTIAL", "FAILED"]},
                            "files_indexed": {"type": "integer"},
                            "datastore_id": {"type": "string"},
                            "index_timestamp": {"type": "string"}
                        }
                    }
                }
            }
        },
        {
            "skill_id": "iam_index.index_documentation",
            "name": "Index Documentation",
            "description": "Index documentation files into Vertex AI Search datastore",
            "input_schema": {
                "type": "object",
                "required": ["docs_path"],
                "properties": {
                    "docs_path": {"type": "string"},
                    "doc_types": {"type": "array", "items": {"type": "string"}}
                }
            },
            "output_schema": {
                "type": "object",
                "required": ["indexing_result"],
                "properties": {
                    "indexing_result": {
                        "type": "object",
                        "required": ["status", "docs_indexed"],
                        "properties": {
                            "status": {"type": "string"},
                            "docs_indexed": {"type": "integer"},
                            "datastore_id": {"type": "string"}
                        }
                    }
                }
            }
        },
        {
            "skill_id": "iam_index.search_knowledge_base",
            "name": "Search Knowledge Base",
            "description": "Search indexed knowledge base using Vertex AI Search",
            "input_schema": {
                "type": "object",
                "required": ["query"],
                "properties": {
                    "query": {"type": "string"},
                    "max_results": {"type": "integer", "default": 10},
                    "filter": {"type": "object"}
                }
            },
            "output_schema": {
                "type": "object",
                "required": ["search_results"],
                "properties": {
                    "search_results": {
                        "type": "object",
                        "required": ["results", "total_count"],
                        "properties": {
                            "results": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "title": {"type": "string"},
                                        "snippet": {"type": "string"},
                                        "source": {"type": "string"},
                                        "relevance_score": {"type": "number"}
                                    }
                                }
                            },
                            "total_count": {"type": "integer"}
                        }
                    }
                }
            }
        },
        {
            "skill_id": "iam_index.update_knowledge_base",
            "name": "Update Knowledge Base",
            "description": "Update knowledge base with new or modified content",
            "input_schema": {
                "type": "object",
                "required": ["updates"],
                "properties": {
                    "updates": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "operation": {"type": "string", "enum": ["add", "update", "delete"]},
                                "document_id": {"type": "string"},
                                "content": {"type": "object"}
                            }
                        }
                    }
                }
            },
            "output_schema": {
                "type": "object",
                "required": ["update_result"],
                "properties": {
                    "update_result": {
                        "type": "object",
                        "required": ["status", "updates_applied"],
                        "properties": {
                            "status": {"type": "string"},
                            "updates_applied": {"type": "integer"},
                            "failed_updates": {"type": "integer"}
                        }
                    }
                }
            }
        }
    ]

    return AgentCard(name=app_name, version=app_version, url=public_url, description=description,
                     capabilities=capabilities, default_input_modes=["text"], default_output_modes=["text"], skills=skills)


def get_agent_card_dict() -> Dict[str, Any]:
    """Get iam-index's AgentCard as dictionary."""
    card = get_agent_card()
    card_dict = card.model_dump()
    spiffe_id = os.getenv("AGENT_SPIFFE_ID", "spiffe://intent.solutions/agent/iam-index/dev/us-central1/0.10.0")
    card_dict["spiffe_id"] = spiffe_id
    return card_dict


__all__ = ["AgentCard", "get_agent_card", "get_agent_card_dict"]
