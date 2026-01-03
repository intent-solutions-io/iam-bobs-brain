"""
iam-index - Knowledge Management Specialist Agent Implementation

This module defines the knowledge indexing and retrieval specialist agent
that manages Vertex AI Search integration and maintains the knowledge base.
"""

from google.adk.agents import LlmAgent
from google.adk import Runner
from google.adk.sessions import VertexAiSessionService
from google.adk.memory import VertexAiMemoryBankService
import os
import logging
from typing import Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Environment variables
PROJECT_ID = os.getenv("PROJECT_ID")
LOCATION = os.getenv("LOCATION", "us-central1")
AGENT_ENGINE_ID = os.getenv("AGENT_ENGINE_ID")
APP_NAME = os.getenv("APP_NAME", "iam-index")
AGENT_SPIFFE_ID = os.getenv(
    "AGENT_SPIFFE_ID",
    "spiffe://intent.solutions/agent/iam-index/dev/us-central1/0.1.0"
)

def auto_save_session_to_memory(ctx):
    """
    After-agent callback to persist session to Memory Bank.

    Enforces R5: Dual memory wiring requirement.
    """
    try:
        if hasattr(ctx, "_invocation_context"):
            invocation_ctx = ctx._invocation_context
            memory_svc = invocation_ctx.memory_service
            session = invocation_ctx.session

            if memory_svc and session:
                memory_svc.add_session_to_memory(session)
                logger.info(
                    f"✅ Saved iam-index session {session.id} to Memory Bank",
                    extra={"spiffe_id": AGENT_SPIFFE_ID, "session_id": session.id}
                )
            else:
                logger.warning(
                    "Memory service or session not available",
                    extra={"spiffe_id": AGENT_SPIFFE_ID}
                )
        else:
            logger.warning(
                "Invocation context not available",
                extra={"spiffe_id": AGENT_SPIFFE_ID}
            )
    except Exception as e:
        logger.error(
            f"Failed to save session to Memory Bank: {e}",
            extra={"spiffe_id": AGENT_SPIFFE_ID},
            exc_info=True
        )
        # Never block agent execution

def get_agent() -> LlmAgent:
    """
    Factory function to create the iam-index Knowledge Management Specialist agent.

    Returns:
        LlmAgent configured with knowledge management tools and dual memory.
    """
    logger.info(
        f"Creating iam-index agent for {APP_NAME}",
        extra={"spiffe_id": AGENT_SPIFFE_ID}
    )

    instruction = f"""You are iam-index, the Knowledge Management Specialist for the ADK/Agent Engineering Department in bobs-brain.

**Your Identity:** {AGENT_SPIFFE_ID}

## ROLE & RESPONSIBILITIES

You are the department's **knowledge steward**, responsible for:

1. **Documentation Indexing**
   - Index ADK/Vertex AI documentation for semantic search
   - Maintain mappings from docs to Vertex AI Search indices
   - Keep documentation synchronized and searchable

2. **Code Pattern Cataloging**
   - Index common ADK patterns and implementations
   - Maintain a searchable catalog of code examples
   - Track pattern evolution and best practices

3. **Knowledge Base Management**
   - Ensure all agents can query the knowledge base
   - Provide retrieval abstractions for other agents
   - Maintain knowledge freshness and accuracy

4. **Gap Analysis**
   - Identify missing documentation or patterns
   - Report knowledge gaps to iam-doc for documentation
   - Suggest areas needing better coverage

5. **Search Integration**
   - Manage Vertex AI Search datastores
   - Optimize search relevance and accuracy
   - Monitor search performance metrics

## TOOLS AVAILABLE

- **index_adk_docs**: Index official ADK documentation
- **index_project_docs**: Index project-specific documentation (000-docs/)
- **query_knowledge_base**: Search the indexed knowledge base
- **sync_vertex_search**: Synchronize with Vertex AI Search
- **generate_index_entry**: Create IndexEntry objects for new content
- **analyze_knowledge_gaps**: Identify missing or outdated knowledge

## WORKING PRINCIPLES

### Knowledge Organization
- Follow Document Filing System v2.0 for categorization
- Use consistent tagging and keywords
- Maintain clear source attributions
- Version-track important changes

### Search Optimization
- Balance semantic and keyword search strategies
- Optimize for common query patterns
- Maintain high relevance scores (>0.8)
- Monitor and improve search accuracy

### Integration Support
- Provide simple APIs for other agents to query knowledge
- Abstract away Vertex AI Search complexity
- Return structured, actionable results
- Cache frequently accessed knowledge

### Quality Standards
- Freshness: Update indices within 24 hours of changes
- Coverage: Index 100% of ADK docs and 000-docs/
- Accuracy: Maintain >90% search relevance
- Performance: Sub-second query response times

## COMMUNICATION PATTERNS

### With Other Agents
- **iam-adk**: Provide ADK pattern references and examples
- **iam-doc**: Report documentation gaps and suggest updates
- **iam-fix-plan**: Supply relevant code patterns and solutions
- **iam-qa**: Provide test patterns and quality guidelines
- **All agents**: Answer knowledge queries promptly

### Output Formats
- Return IndexEntry objects for new indexed content
- Provide search results with relevance scores
- Include source links and snippets
- Generate knowledge gap reports

## HARD MODE COMPLIANCE (R1-R8)

You must enforce all Hard Mode rules:
- R1: ADK-only implementation
- R2: Vertex AI Agent Engine runtime
- R3: Gateway separation
- R4: CI-only deployments
- R5: Dual memory wiring
- R6: Single documentation folder
- R7: SPIFFE ID propagation
- R8: Drift detection compliance

## EXAMPLE QUERIES

1. "Index the latest ADK documentation"
2. "Find examples of dual memory wiring"
3. "What patterns exist for A2A communication?"
4. "Identify knowledge gaps in our agent documentation"
5. "Sync 000-docs/ with Vertex AI Search"

Remember: You are the **knowledge nexus** - all agents rely on you for accurate, timely information retrieval."""

    # ✅ Lazy import to avoid circular dependency (Phase 13)
    from agents.shared_tools import IAM_INDEX_TOOLS

    agent = LlmAgent(
        model="gemini-2.0-flash-exp",
        name="iam_index",  # Python identifier (no hyphens)
        tools=IAM_INDEX_TOOLS,  # Use shared tools profile
        instruction=instruction,
        after_agent_callback=auto_save_session_to_memory
    )

    logger.info(
        "✅ iam-index agent created",
        extra={
            "spiffe_id": AGENT_SPIFFE_ID,
            "model": "gemini-2.0-flash-exp",
            "tools_count": 6,
            "name": "iam_index"
        }
    )

    return agent

def create_runner() -> Runner:
    """
    Create Runner with dual memory wiring (Session + Memory Bank).

    Enforces R5: Both session and memory services are required.

    Returns:
        Runner configured with dual memory services.
    """
    logger.info(
        "Creating Runner with dual memory for iam-index",
        extra={"spiffe_id": AGENT_SPIFFE_ID}
    )

    # R5: Dual memory wiring
    session_service = VertexAiSessionService(
        project=PROJECT_ID,
        location=LOCATION
    )

    memory_service = VertexAiMemoryBankService(
        project=PROJECT_ID,
        location=LOCATION
    )

    # Create the agent
    agent = get_agent()

    # Create Runner with both services
    runner = Runner(
        agent=agent,
        session_service=session_service,
        memory_service=memory_service
    )

    logger.info(
        "✅ Runner created with dual memory services",
        extra={
            "spiffe_id": AGENT_SPIFFE_ID,
            "has_session_service": True,
            "has_memory_service": True
        }
    )

    return runner

# Module-level agent for ADK CLI deployment
root_agent = get_agent()

logger.info(
    "✅ root_agent created for ADK deployment",
    extra={
        "spiffe_id": AGENT_SPIFFE_ID,
        "agent_name": "iam_index"
    }
)

if __name__ == "__main__":
    """
    Entry point for Agent Engine container.
    Only for CI smoke tests, not production execution.
    """
    import sys

    # R4: CI-only guard
    if os.getenv("GITHUB_ACTIONS") != "true":
        logger.warning(
            "⚠️ Running iam-index locally. Production must use "
            "Vertex AI Agent Engine via GitHub Actions (R4).",
            extra={"spiffe_id": AGENT_SPIFFE_ID}
        )

    try:
        runner = create_runner()
        logger.info(
            "🚀 iam-index runner ready",
            extra={"spiffe_id": AGENT_SPIFFE_ID}
        )

        # For local testing only
        if os.getenv("GITHUB_ACTIONS") != "true":
            logger.info(
                "Local test mode - Runner created but not started. "
                "In production, Agent Engine manages the runner lifecycle."
            )
    except Exception as e:
        logger.error(
            f"❌ Failed to create iam-index runner: {e}",
            extra={"spiffe_id": AGENT_SPIFFE_ID},
            exc_info=True
        )
        sys.exit(1)