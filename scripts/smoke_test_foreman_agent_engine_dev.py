#!/usr/bin/env python3
"""
Smoke Test for Foreman's Agent Engine Dev Instance

Tests that the inline-deployed Foreman agent on Vertex AI Agent Engine is responding
correctly to basic health check queries.

This script should be run AFTER a successful dev deployment of Foreman via inline source.

## Usage

Set environment variables:

    export GCP_PROJECT_ID=your-project-id
    export GCP_LOCATION=us-central1
    export FOREMAN_AGENT_ENGINE_NAME_DEV=projects/YOUR_PROJECT/locations/us-central1/reasoningEngines/YOUR_AGENT_ID

Run the smoke test:

    python scripts/smoke_test_foreman_agent_engine_dev.py

Or via Makefile:

    make smoke-foreman-agent-engine-dev

## Expected Result

Success case:
    [SMOKE] Connected to: projects/.../reasoningEngines/...
    [SMOKE] Response snippet: {"status":"ok","agent":"foreman"}
    [SMOKE] RESULT: PASS

Failure case:
    [SMOKE] ERROR: Failed to connect to agent
    [SMOKE] RESULT: FAIL
    Exit code: 1

## References

- Standard: 000-docs/6767-INLINE-DR-STND-inline-source-deployment-for-vertex-agent-engine.md
- Phase 42: 000-docs/211-AA-PLAN-phase-42-agent-engine-dev-ci-deploy.md

"""

import os
import sys
from typing import Optional

# Lazy import to avoid issues in environments without SDK installed
try:
    from google.cloud import aiplatform
except ImportError as e:
    print(f"[SMOKE] ERROR: Missing required Google Cloud SDK dependencies: {e}", file=sys.stderr)
    print("[SMOKE] Install with: pip install google-cloud-aiplatform", file=sys.stderr)
    sys.exit(1)


def get_env_var(name: str, required: bool = True) -> Optional[str]:
    """Get environment variable with clear error messaging."""
    value = os.getenv(name)
    if required and not value:
        print(f"[SMOKE] ERROR: Missing required environment variable: {name}", file=sys.stderr)
        print(f"[SMOKE] Set it with: export {name}=your-value", file=sys.stderr)
        return None
    return value


def smoke_test_foreman_agent_engine_dev() -> int:
    """
    Run smoke test against Foreman's dev Agent Engine instance.

    Returns:
        0 if test passes, 1 if test fails
    """
    print("[SMOKE] Starting Foreman Agent Engine dev smoke test...")
    print()

    # Get configuration from environment
    project_id = get_env_var("GCP_PROJECT_ID")
    location = get_env_var("GCP_LOCATION", required=False) or "us-central1"
    agent_name = get_env_var("FOREMAN_AGENT_ENGINE_NAME_DEV")

    # Check required variables
    if not project_id or not agent_name:
        print("[SMOKE] RESULT: FAIL (missing configuration)", file=sys.stderr)
        return 1

    print("[SMOKE] Configuration:")
    print(f"[SMOKE]   Project: {project_id}")
    print(f"[SMOKE]   Location: {location}")
    print(f"[SMOKE]   Agent: {agent_name}")
    print()

    try:
        # Initialize Vertex AI
        aiplatform.init(project=project_id, location=location)

        # Connect to the agent
        print("[SMOKE] Connecting to Agent Engine instance...")
        print(f"[SMOKE]   Resource name: {agent_name}")
        print()

        # Create reasoning engine client
        from google.cloud.aiplatform_v1beta1 import ReasoningEngineExecutionServiceClient
        from google.cloud.aiplatform_v1beta1.types import QueryReasoningEngineRequest

        client = ReasoningEngineExecutionServiceClient(
            client_options={"api_endpoint": f"{location}-aiplatform.googleapis.com"}
        )

        # Create a simple health check query for foreman
        # Foreman expects structured tasks, so we send a minimal orchestration request
        test_prompt = 'Health check: respond with a short JSON object {"status":"ok","agent":"foreman"}.'

        print("[SMOKE] Sending test query...")
        print(f"[SMOKE]   Prompt: {test_prompt}")
        print()

        # Send the query
        request = QueryReasoningEngineRequest(
            name=agent_name,
            input={"query": test_prompt},
        )

        response = client.query_reasoning_engine(request=request)

        # Extract response content
        response_text = str(response.output) if hasattr(response, 'output') else str(response)

        print("[SMOKE] Response received:")
        print(f"[SMOKE]   {response_text[:200]}...")  # Show first 200 chars
        print()

        # Check if response contains expected health check markers
        success_markers = ["status", "ok"]
        all_present = all(marker.lower() in response_text.lower() for marker in success_markers)

        if all_present:
            print("[SMOKE] ✅ Health check markers found in response")
            print("[SMOKE] RESULT: PASS")
            return 0
        else:
            print("[SMOKE] ⚠️  Expected markers not found in response", file=sys.stderr)
            print(f"[SMOKE]   Expected: {success_markers}", file=sys.stderr)
            print("[SMOKE] RESULT: FAIL (unexpected response)", file=sys.stderr)
            return 1

    except Exception as e:
        print(f"[SMOKE] ERROR: {type(e).__name__}: {e}", file=sys.stderr)
        print()
        print("[SMOKE] Troubleshooting:")
        print("[SMOKE]   1. Verify FOREMAN_AGENT_ENGINE_NAME_DEV is correct")
        print("[SMOKE]   2. Check that dev deployment succeeded")
        print("[SMOKE]   3. Ensure you have access to the Agent Engine instance")
        print("[SMOKE]   4. Verify your GCP credentials are valid")
        print()
        print("[SMOKE] RESULT: FAIL (exception)", file=sys.stderr)
        return 1


def main():
    """Main entry point."""
    exit_code = smoke_test_foreman_agent_engine_dev()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
