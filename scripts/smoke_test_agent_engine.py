#!/usr/bin/env python3
"""
Smoke Test for Vertex AI Agent Engine Deployments

Tests deployed agents with lightweight queries to verify they're responding correctly.

Part of Phase 21 - Real Agent Engine deployment implementation.

Usage:
    # Config-only mode (validation without API calls)
    python scripts/smoke_test_agent_engine.py --config-only

    # Live smoke tests
    python scripts/smoke_test_agent_engine.py \\
        --project bobs-brain \\
        --region us-central1 \\
        --env dev

Exit Codes:
    0 - Success (all tests passed)
    1 - Test failures
    2 - Configuration error
    3 - Missing dependencies

Related Docs:
    - 000-docs/152-AA-REPT-phase-21-agent-engine-dev-first-live-deploy-and-smoke-tests.md
"""

import argparse
import os
import sys
from pathlib import Path
from typing import Dict

# Add repo root to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def validate_config(args: argparse.Namespace) -> Dict:
    """
    Validate smoke test configuration.

    Args:
        args: Command-line arguments

    Returns:
        Configuration dictionary

    Raises:
        SystemExit: If configuration is invalid (exit code 2)
    """
    # Config-only mode doesn't need project/region
    if args.config_only:
        return {
            "mode": "config-only",
            "agents_to_test": ["bob", "foreman"],
        }

    # Live mode requires project and region
    if not args.project:
        args.project = os.getenv("PROJECT_ID")
        if not args.project:
            print("❌ Error: --project required for live tests")
            print("   Or set PROJECT_ID environment variable")
            sys.exit(2)

    if not args.region:
        args.region = os.getenv("LOCATION", "us-central1")

    if not args.env:
        args.env = "dev"

    config = {
        "mode": "live",
        "project": args.project,
        "region": args.region,
        "environment": args.env,
        "agents_to_test": ["bob", "foreman"],
    }

    return config


def run_config_only_tests(config: Dict) -> bool:
    """
    Run config-only smoke tests (no API calls).

    Args:
        config: Test configuration

    Returns:
        True if all tests pass
    """
    print("=" * 80)
    print("SMOKE TEST - CONFIG-ONLY MODE")
    print("=" * 80)
    print("Validating test configuration without making API calls...")
    print()

    # Check that test prompts are defined
    test_prompts = {
        "bob": "What is your name and role?",
        "foreman": "What is your role in the SWE department?",
    }

    print("✅ Test prompts configured:")
    for agent, prompt in test_prompts.items():
        print(f"   {agent}: '{prompt[:50]}...'")

    # Check that we can import required modules
    print("\n✅ Checking Python imports...")
    try:
        import sys

        sys.path.insert(0, str(Path(__file__).parent.parent))
        from agents.config.agent_engine import get_agent_engine_config  # noqa: F401

        print("   agents.config.agent_engine: OK")
    except ImportError as e:
        print(f"   ❌ Import error: {e}")
        return False

    print("\n✅ Config-only smoke test validation passed")
    print("   To run live tests, remove --config-only flag")
    return True


def run_live_smoke_tests(config: Dict) -> bool:
    """
    Run live smoke tests against deployed Agent Engine.

    Args:
        config: Test configuration

    Returns:
        True if all tests pass

    Raises:
        SystemExit: If dependencies are missing (exit code 3)
    """
    # Check dependencies
    try:
        import vertexai
        from vertexai import agent_engines
    except ImportError as e:
        print(f"❌ Error: Missing required libraries: {e}")
        print("   Install with: pip install google-cloud-aiplatform[adk,agent_engines]")
        sys.exit(3)

    print("=" * 80)
    print("SMOKE TEST - LIVE MODE")
    print("=" * 80)
    print(f"Project: {config['project']}")
    print(f"Region: {config['region']}")
    print(f"Environment: {config['environment']}")
    print("=" * 80)
    print()

    # Initialize Vertex AI
    vertexai.init(
        project=config["project"],
        location=config["region"],
    )

    # Get agent configurations
    from agents.config.agent_engine import get_agent_engine_config

    test_results = []

    # Test each agent
    for agent_role in config["agents_to_test"]:
        print(f"\n🧪 Testing {agent_role}...")

        try:
            # Get agent config
            agent_config = get_agent_engine_config(
                env=config["environment"], agent_role=agent_role
            )

            if not agent_config:
                print(f"   ⚠️  {agent_role} not deployed to {config['environment']}")
                continue

            # Check if this is a placeholder
            if "PLACEHOLDER" in agent_config.reasoning_engine_id:
                print(f"   ⚠️  {agent_role} has placeholder config, skipping")
                continue

            resource_name = agent_config.reasoning_engine_id
            print(f"   Resource: {resource_name}")

            # Get the remote app
            try:
                remote_app = agent_engines.get(resource_name)
                print("   ✅ Agent Engine connection established")
            except Exception as e:
                print(f"   ❌ Failed to connect: {e}")
                test_results.append(False)
                continue

            # Send a lightweight smoke test query
            test_prompt = "[SMOKE TEST] What is your name? (Reply briefly)"
            print(f"   📤 Sending: '{test_prompt[:50]}...'")

            try:
                # Create a test session
                import asyncio

                async def test_query():
                    session = await remote_app.async_create_session(
                        user_id="smoke_test_user"
                    )
                    session_id = session["id"]

                    # Send query
                    response_parts = []
                    async for event in remote_app.async_stream_query(
                        user_id="smoke_test_user",
                        session_id=session_id,
                        message=test_prompt,
                    ):
                        if hasattr(event, "text"):
                            response_parts.append(event.text)
                        elif isinstance(event, dict) and "text" in event:
                            response_parts.append(event["text"])

                    return "".join(response_parts)

                response = asyncio.run(test_query())

                # Check response
                if response and len(response) > 0:
                    print(f"   📥 Response: '{response[:100]}...'")
                    print(f"   ✅ {agent_role} responded successfully")
                    test_results.append(True)
                else:
                    print(f"   ❌ {agent_role} returned empty response")
                    test_results.append(False)

            except Exception as e:
                print(f"   ❌ Query failed: {e}")
                test_results.append(False)

        except Exception as e:
            print(f"   ❌ Test error: {e}")
            test_results.append(False)

    # Summary
    print("\n" + "=" * 80)
    print("SMOKE TEST SUMMARY")
    print("=" * 80)

    total_tests = len(test_results)
    passed_tests = sum(test_results)
    failed_tests = total_tests - passed_tests

    print(f"Total tests: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {failed_tests}")

    if failed_tests == 0 and total_tests > 0:
        print("\n✅ All smoke tests passed!")
        return True
    else:
        print(f"\n❌ {failed_tests} smoke tests failed")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Smoke test deployed Agent Engine agents",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Config-only mode (validation without API calls)
    python scripts/smoke_test_agent_engine.py --config-only

    # Live smoke tests
    python scripts/smoke_test_agent_engine.py \\
        --project bobs-brain \\
        --region us-central1 \\
        --env dev
        """,
    )

    parser.add_argument(
        "--config-only",
        action="store_true",
        help="Validate configuration only, do not call APIs",
    )

    parser.add_argument("--project", help="GCP project ID (or use PROJECT_ID env var)")

    parser.add_argument("--region", help="GCP region (or use LOCATION env var)")

    parser.add_argument(
        "--env",
        choices=["dev", "staging", "prod"],
        default="dev",
        help="Environment to test",
    )

    args = parser.parse_args()

    # Validate configuration
    config = validate_config(args)

    # Run appropriate test mode
    if config["mode"] == "config-only":
        success = run_config_only_tests(config)
    else:
        success = run_live_smoke_tests(config)

    # Exit with appropriate code
    if success:
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
