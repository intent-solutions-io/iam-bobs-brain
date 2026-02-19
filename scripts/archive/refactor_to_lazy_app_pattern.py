#!/usr/bin/env python3
"""
Script to automatically refactor agents to lazy-loading App pattern (6774).

This script automates the migration of agents from the old pattern (module-level
root_agent = get_agent()) to the new lazy App pattern (module-level app = create_app()).

Usage:
    python3 scripts/refactor_to_lazy_app_pattern.py agents/iam_senior_adk_devops_lead/agent.py
    python3 scripts/refactor_to_lazy_app_pattern.py agents/iam_issue/agent.py
"""

import re
import sys
from pathlib import Path


def refactor_agent_file(file_path: Path) -> None:
    """
    Refactor an agent file to lazy-loading App pattern.

    Args:
        file_path: Path to agent.py file to refactor
    """
    print(f"📝 Refactoring {file_path}...")

    # Read file
    content = file_path.read_text()

    # 1. Update docstring to add LAZY-LOADING PATTERN note
    if "LAZY-LOADING PATTERN" not in content:
        # Find docstring closing and add note before it
        content = re.sub(
            r'(""")\n\nfrom google.adk',
            r"\1\n\nLAZY-LOADING PATTERN (6774):\n"
            r"- Uses create_agent() for lazy agent instantiation\n"
            r"- Uses create_app() to wrap in App for Agent Engine\n"
            r"- Exposes module-level `app` (not agent!)\n"
            r"- No import-time validation or heavy work\n\1\n\nfrom google.adk",
            content,
        )

    # 2. Add App to imports if not present
    if (
        "from google.adk import Runner" in content
        and "from google.adk import App" not in content
    ):
        content = content.replace(
            "from google.adk import Runner", "from google.adk import App, Runner"
        )

    # 3. Remove import-time environment validation
    # Pattern: if not PROJECT_ID: raise ValueError(...)
    validation_pattern = r"\n# Validate required environment variables\n(?:if not \w+:\n    raise ValueError\([^\)]+\)\n)+"
    if re.search(validation_pattern, content):
        # Add comment instead
        content = re.sub(
            validation_pattern,
            "\n# Note: Environment validation moved to create_agent() (lazy loading)\n",
            content,
        )

    # 4. Rename get_agent() to create_agent() and add validation
    if "def get_agent() -> LlmAgent:" in content:
        # Find get_agent function and rename
        content = content.replace(
            "def get_agent() -> LlmAgent:", "def create_agent() -> LlmAgent:"
        )

        # Update docstring
        content = re.sub(
            r'(def create_agent\(\) -> LlmAgent:\n    """\n    Create and configure the LlmAgent\.)',
            r"\1\n\n    This function is called lazily by create_app() on first use.\n    Do NOT call this at module import time.",
            content,
        )

        # Add validation at start of create_agent()
        # Find the function body start (after docstring)
        create_agent_match = re.search(
            r'def create_agent\(\) -> LlmAgent:.*?"""\n(    logger\.info)',
            content,
            re.DOTALL,
        )
        if create_agent_match:
            # Insert validation before first logger.info
            validation_code = """    # ✅ Validation happens here (lazy, not at import)
    if not PROJECT_ID:
        raise ValueError("PROJECT_ID environment variable is required")
    if not LOCATION:
        raise ValueError("LOCATION environment variable is required")
    if not AGENT_ENGINE_ID:
        raise ValueError("AGENT_ENGINE_ID environment variable is required")

"""
            content = (
                content[: create_agent_match.start(1)]
                + validation_code
                + content[create_agent_match.start(1) :]
            )

    # 5. Add create_app() function after create_agent()
    if "def create_app() -> App:" not in content:
        # Find end of create_agent() function
        create_agent_end = re.search(
            r"(    return agent\n\n)\ndef create_runner", content
        )
        if create_agent_end:
            create_app_code = '''
def create_app() -> App:
    """
    Create the App container for this agent.

    The App wraps the agent and provides lazy initialization compatible
    with Vertex AI Agent Engine. This function can be called multiple times
    safely (idempotent).

    Enforces:
    - R2: App designed for Vertex AI Agent Engine deployment
    - R5: Dual memory wiring (Session + Memory Bank)
    - R7: SPIFFE ID propagation in logs

    Returns:
        App: Configured app instance for Agent Engine

    Note:
        This is the entry point for Agent Engine deployment.
        The agent is created lazily on first invocation.
    """
    logger.info(
        "Creating App container",
        extra={"spiffe_id": AGENT_SPIFFE_ID}
    )

    # Validate required env vars before app creation
    if not PROJECT_ID or not AGENT_ENGINE_ID:
        raise ValueError("PROJECT_ID and AGENT_ENGINE_ID are required for App creation")

    # R5: Create memory services (lazy, inside function)
    session_service = VertexAiSessionService(
        project_id=PROJECT_ID,
        location=LOCATION,
        agent_engine_id=AGENT_ENGINE_ID
    )
    logger.info("✅ Session service initialized", extra={"spiffe_id": AGENT_SPIFFE_ID})

    memory_service = VertexAiMemoryBankService(
        project=PROJECT_ID,
        location=LOCATION,
        agent_engine_id=AGENT_ENGINE_ID
    )
    logger.info("✅ Memory Bank service initialized", extra={"spiffe_id": AGENT_SPIFFE_ID})

    # Create App with lazy agent creation
    # Pass create_agent as function reference (not called yet!)
    app_instance = App(
        agent=create_agent,  # ✅ Function reference, not instance
        app_name=APP_NAME,
        session_service=session_service,
        memory_service=memory_service,
    )

    logger.info(
        "✅ App created successfully",
        extra={"spiffe_id": AGENT_SPIFFE_ID, "app_name": APP_NAME}
    )

    return app_instance


# ============================================================================
# BACKWARDS COMPATIBILITY (Optional)
# ============================================================================

'''
            content = (
                content[: create_agent_end.end(1)]
                + create_app_code
                + content[create_agent_end.end(1) :]
            )

    # 6. Mark create_runner() as DEPRECATED
    if "DEPRECATED:" not in content and "def create_runner() -> Runner:" in content:
        # Add deprecation warning
        content = re.sub(
            r'def create_runner\(\) -> Runner:\n    """\n    Create Runner',
            r'def create_runner() -> Runner:\n    """\n    Create Runner',
            content,
        )
        content = re.sub(
            r'(def create_runner\(\) -> Runner:\n    """\n    Create Runner[^\n]+\n\n)',
            r"\1    DEPRECATED: Use create_app() instead for Agent Engine deployment.\n    This function is kept for backwards compatibility with older deployment scripts.\n\n",
            content,
        )

        # Add deprecation log
        content = re.sub(
            r'(def create_runner\(\) -> Runner:.*?"""\n)(    logger\.info)',
            r'\1    logger.warning(\n        "⚠️  create_runner() is deprecated. Use create_app() instead.",\n        extra={"spiffe_id": AGENT_SPIFFE_ID}\n    )\n\n\2',
            content,
            flags=re.DOTALL,
        )

    # 7. Fix calls to get_agent() inside create_runner()
    content = content.replace("agent = get_agent()", "agent = create_agent()")

    # 8. Replace module-level root_agent with app
    if (
        "root_agent = get_agent()" in content
        or "root_agent = create_agent()" in content
    ):
        # Replace entire section
        content = re.sub(
            r"# Create the root agent.*?\)\n",
            """# ============================================================================
# AGENT ENGINE ENTRYPOINT (6774 Pattern)
# ============================================================================

# ✅ Module-level App (lazy initialization)
# Agent Engine will access this on first request
app = create_app()

logger.info(
    "✅ App instance created for Agent Engine deployment",
    extra={"spiffe_id": AGENT_SPIFFE_ID}
)

""",
            content,
            flags=re.DOTALL,
        )

    # 9. Update __main__ block
    if "runner = create_runner()" in content and "if __name__ ==" in content:
        # Update __main__ to use App
        content = re.sub(
            r'(if __name__ == "__main__":.*?)try:\n        runner = create_runner\(\)\n        logger\.info\(\n            "🚀 Agent Engine runner ready"',
            r'\1try:\n        # Use new App pattern\n        logger.info(\n            "🚀 Testing App-based deployment"',
            content,
            flags=re.DOTALL,
        )

        content = re.sub(
            r'        logger\.info\(\n            "🚀 Testing App-based deployment"[^\n]+\n        \)\n',
            r"""        logger.info(
            "🚀 Testing App-based deployment",
            extra={"spiffe_id": AGENT_SPIFFE_ID},
        )

        # App is already created at module level
        logger.info(
            "✅ App instance ready for Agent Engine",
            extra={"spiffe_id": AGENT_SPIFFE_ID}
        )
""",
            content,
        )

        # Update local test message
        content = re.sub(
            r"Local test mode - Runner created but not started\.\s+In production, Agent Engine manages the runner lifecycle\.",
            "Local test mode - App created successfully. In production, Agent Engine manages the app lifecycle.",
            content,
        )

        # Update error message
        content = content.replace("Failed to create runner:", "Failed to create app:")

    # Write back
    file_path.write_text(content)
    print(f"✅ Refactored {file_path}")


def main():
    if len(sys.argv) != 2:
        print("Usage: python3 scripts/refactor_to_lazy_app_pattern.py <agent_file.py>")
        sys.exit(1)

    file_path = Path(sys.argv[1])
    if not file_path.exists():
        print(f"❌ File not found: {file_path}")
        sys.exit(1)

    refactor_agent_file(file_path)


if __name__ == "__main__":
    main()
