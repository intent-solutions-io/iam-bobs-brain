"""
Stub providers for isolating tests from external dependencies.

Stubs replace real external services (Agent Engine, GCS, Slack, etc.)
with deterministic in-memory implementations for fast, reliable tests.

Modules:
    llm          - Stub LLM responses (canned completions, BOB_LLM_MODE=stub)
    agent_engine - Stub for Vertex AI Agent Engine REST API
    http_replay  - HTTP record/replay helpers using respx
"""
