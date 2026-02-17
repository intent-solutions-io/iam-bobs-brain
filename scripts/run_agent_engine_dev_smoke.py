#!/usr/bin/env python3
"""
Agent Engine Dev Smoke Test (AE3)

Tests the dev wiring for:
- Agent Engine config module (agents/config/agent_engine.py)
- A2A gateway (service/a2a_gateway/) with agent_engine_client
- End-to-end flow: Synthetic request → Gateway → Agent Engine → Response

This is a DEV-ONLY smoke test. It validates that:
1. Agent Engine IDs are properly configured for dev
2. A2A gateway can route to Agent Engine
3. Authentication works (ADC)
4. Basic request/response flow succeeds

Requirements:
- DEPLOYMENT_ENV=dev
- AGENT_ENGINE_BOB_ID_DEV set (or another agent configured)
- GCP Application Default Credentials (gcloud auth application-default login)
- Agent Engine deployed and accessible

Usage:
    python3 scripts/run_agent_engine_dev_smoke.py
    python3 scripts/run_agent_engine_dev_smoke.py --agent bob
    python3 scripts/run_agent_engine_dev_smoke.py --agent foreman --prompt "Hello foreman"

Exit Codes:
    0: Smoke test passed
    1: Smoke test failed (config issue, auth issue, or Agent Engine error)
    2: Agent Engine not configured (non-blocking - expected if not set up yet)

Part of: AE-DEV-WIREUP / AE3
"""

import argparse
import asyncio
import json
import sys
from pathlib import Path
from typing import Optional

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from agents.config.agent_engine import (
    build_agent_config,
    get_current_environment,
)
from service.a2a_gateway.agent_engine_client import call_agent_engine


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Dev smoke test for Agent Engine wiring"
    )
    parser.add_argument(
        "--agent",
        type=str,
        default="bob",
        help="Agent role to test (default: bob)",
    )
    parser.add_argument(
        "--prompt",
        type=str,
        default="Hello! This is a dev smoke test. Please respond briefly.",
        help="Test prompt to send to agent",
    )
    parser.add_argument(
        "--env",
        type=str,
        default=None,
        help="Override environment (default: current environment)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show detailed output",
    )
    return parser.parse_args()


async def run_smoke_test(
    agent_role: str,
    prompt: str,
    env: Optional[str] = None,
    verbose: bool = False,
) -> int:
    """
    Run Agent Engine smoke test.

    Args:
        agent_role: Agent to test (bob, foreman, etc.)
        prompt: Test prompt
        env: Environment override
        verbose: Show detailed output

    Returns:
        Exit code (0=success, 1=failure, 2=not configured)
    """
    print("=" * 80)
    print("AGENT ENGINE DEV SMOKE TEST (AE3)")
    print("=" * 80)
    print()

    # Determine environment
    current_env = env or get_current_environment()
    print(f"Environment: {current_env}")
    print(f"Agent Role: {agent_role}")
    print()

    # Check if dev
    if current_env != "dev":
        print("⚠️  This smoke test is designed for DEV only")
        print(f"   Current environment: {current_env}")
        print("   Set DEPLOYMENT_ENV=dev to run this test")
        print()
        return 1

    # Check if agent is configured
    print("Checking Agent Engine configuration...")
    agent_config = build_agent_config(agent_role, current_env)

    if not agent_config:
        print(f"ℹ️  Agent '{agent_role}' is NOT configured for {current_env}")
        print()
        print(f"   This is expected if you haven't deployed {agent_role} to Agent Engine yet.")
        print("   To configure:")
        print(f"     export AGENT_ENGINE_{agent_role.replace('-', '_').upper()}_ID_DEV=your-engine-id")
        print()
        print("✅ Smoke test completed (agent not configured - non-blocking)")
        return 2  # Non-blocking exit code

    print("✅ Agent configured:")
    if verbose:
        print(f"   Engine ID: {agent_config.reasoning_engine_id}")
        print(f"   Project: {agent_config.project_id}")
        print(f"   Location: {agent_config.location}")
        print(f"   SPIFFE ID: {agent_config.spiffe_id}")
    else:
        print(f"   Engine ID: {agent_config.reasoning_engine_id}")
    print()

    # Test prompt
    print(f"Test Prompt: {prompt[:60]}{'...' if len(prompt) > 60 else ''}")
    print()

    # Call Agent Engine
    print("Calling Agent Engine via agent_engine_client...")
    try:
        result = await call_agent_engine(
            agent_role=agent_role,
            prompt=prompt,
            correlation_id="smoke-test-dev",
            env=current_env,
        )

        if result.error:
            print("❌ Agent Engine call failed:")
            print(f"   Error: {result.error}")
            if verbose and result.metadata:
                print(f"   Metadata: {json.dumps(result.metadata, indent=2)}")
            print()
            return 1

        print("✅ Agent Engine response received:")
        print()
        print("Response:")
        print("-" * 80)
        print(result.response[:500])  # First 500 chars
        if len(result.response) > 500:
            print(f"\n... (truncated, total length: {len(result.response)} chars)")
        print("-" * 80)
        print()

        if verbose and result.metadata:
            print("Metadata:")
            print(json.dumps(result.metadata, indent=2))
            print()

        if result.session_id:
            print(f"Session ID: {result.session_id}")
            print()

        print("=" * 80)
        print("✅ SMOKE TEST PASSED")
        print("=" * 80)
        print()
        print("Summary:")
        print(f"  - Agent: {agent_role}")
        print(f"  - Environment: {current_env}")
        print(f"  - Engine ID: {agent_config.reasoning_engine_id}")
        print(f"  - Response Length: {len(result.response)} chars")
        print(f"  - Session ID: {result.session_id or 'N/A'}")
        print()
        print("The dev wiring is working correctly!")
        print("You can now:")
        print("  1. Test other agents (--agent foreman, --agent iam-adk)")
        print("  2. Deploy to staging when ready")
        print()

        return 0

    except Exception as e:
        print("❌ Smoke test failed with exception:")
        print(f"   {type(e).__name__}: {e}")
        if verbose:
            import traceback
            print()
            print("Traceback:")
            traceback.print_exc()
        print()
        return 1


def main():
    """Main entry point."""
    args = parse_args()

    exit_code = asyncio.run(
        run_smoke_test(
            agent_role=args.agent,
            prompt=args.prompt,
            env=args.env,
            verbose=args.verbose,
        )
    )

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
