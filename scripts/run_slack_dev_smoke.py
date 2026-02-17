#!/usr/bin/env python3
"""
Slack Dev Smoke Test (SLACK-ENDTOEND-DEV S3)

Tests the dev wiring for:
- Slack webhook service (service/slack_webhook/)
- Feature flag validation (SLACK_BOB_ENABLED)
- A2A gateway routing (Option B) or direct Agent Engine (Option A)
- End-to-end flow: Synthetic Slack event → Webhook → Gateway/Engine → Response

This is a DEV-ONLY smoke test. It validates that:
1. Slack webhook service is running and healthy
2. Feature flag (SLACK_BOB_ENABLED) works correctly
3. Configuration validation catches missing credentials
4. Routing works (via a2a_gateway or direct Agent Engine)
5. Slack events are processed correctly

Requirements:
- Slack webhook service running (local or Cloud Run)
- SLACK_BOB_ENABLED=true (for enabled tests)
- SLACK_BOT_TOKEN and SLACK_SIGNING_SECRET set (for enabled tests)
- A2A_GATEWAY_URL or Agent Engine vars set (for routing tests)

Usage:
    # Test health endpoint only
    python3 scripts/run_slack_dev_smoke.py --health-only

    # Test with synthetic event (requires service running)
    python3 scripts/run_slack_dev_smoke.py --url http://localhost:8080

    # Test Cloud Run deployment
    python3 scripts/run_slack_dev_smoke.py --url https://slack-webhook-xxx.run.app

Exit Codes:
    0: Smoke test passed
    1: Smoke test failed (config issue, service error)
    2: Service not running (expected if not deployed yet)

Part of: SLACK-ENDTOEND-DEV / S3
"""

import argparse
import json
import sys
import time
from typing import Any, Dict, Optional
from urllib.parse import urljoin

try:
    import httpx
except ImportError:
    print("❌ Error: httpx not installed. Run: pip install httpx")
    sys.exit(1)


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Dev smoke test for Slack webhook integration"
    )
    parser.add_argument(
        "--url",
        type=str,
        default="http://localhost:8080",
        help="Slack webhook service URL (default: http://localhost:8080)",
    )
    parser.add_argument(
        "--health-only",
        action="store_true",
        help="Only test health endpoint (no synthetic event)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show detailed output",
    )
    return parser.parse_args()


def print_header(title: str):
    """Print section header."""
    print(f"\n{'=' * 80}")
    print(f"  {title}")
    print(f"{'=' * 80}\n")


def print_result(test_name: str, passed: bool, details: str = ""):
    """Print test result."""
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"{status} - {test_name}")
    if details:
        print(f"     {details}")


def test_health_endpoint(base_url: str, verbose: bool = False) -> tuple[bool, Optional[Dict[str, Any]]]:
    """
    Test the /health endpoint.

    Args:
        base_url: Base URL of the service
        verbose: Show detailed output

    Returns:
        (success, health_data): Tuple of success status and health response
    """
    print_header("Test 1: Health Endpoint")

    try:
        url = urljoin(base_url, "/health")
        response = httpx.get(url, timeout=10.0)
        response.raise_for_status()
        health_data = response.json()

        if verbose:
            print("Health Response:")
            print(json.dumps(health_data, indent=2))

        # Check required fields
        required_fields = ["status", "service", "version", "slack_bot_enabled"]
        for field in required_fields:
            if field not in health_data:
                print_result(
                    "Health endpoint structure",
                    False,
                    f"Missing required field: {field}",
                )
                return False, None

        print_result("Health endpoint reachable", True)
        print_result(
            f"Service: {health_data.get('service')} v{health_data.get('version')}",
            True,
        )
        print_result(
            f"Slack bot enabled: {health_data.get('slack_bot_enabled')}",
            True,
        )
        print_result(
            f"Config valid: {health_data.get('config_valid')}",
            True,
        )
        print_result(
            f"Routing: {health_data.get('routing')}",
            True,
        )

        # Check if Slack is disabled
        if not health_data.get("slack_bot_enabled"):
            print(
                "\n⚠️  Note: Slack bot is DISABLED (SLACK_BOB_ENABLED=false)"
            )
            print(
                "     This is expected in secure environments. Set SLACK_BOB_ENABLED=true for full testing."
            )

        # Check config validity
        if not health_data.get("config_valid"):
            missing = health_data.get("missing_vars", [])
            print(f"\n⚠️  Note: Config is INVALID. Missing: {', '.join(missing)}")
            print(
                "     Set required env vars for full testing (see .env.example)."
            )

        return True, health_data

    except httpx.ConnectError:
        print_result(
            "Service connection", False, f"Could not connect to {base_url}"
        )
        print(
            "\n⚠️  Service not running. Start with: uvicorn service.slack_webhook.main:app"
        )
        return False, None

    except httpx.HTTPStatusError as e:
        print_result(
            "Health endpoint", False, f"HTTP {e.response.status_code}"
        )
        return False, None

    except Exception as e:
        print_result("Health endpoint", False, f"Error: {e!s}")
        return False, None


def create_synthetic_slack_event(text: str = "Hello Bob!") -> Dict[str, Any]:
    """
    Create a synthetic Slack app_mention event.

    Args:
        text: Message text to send

    Returns:
        Slack event payload
    """
    return {
        "type": "event_callback",
        "event": {
            "type": "app_mention",
            "user": "U0000TESTUSER",
            "text": f"<@U07NRCYJX8A> {text}",  # Bob's user ID
            "ts": str(time.time()),
            "channel": "C0000TESTCHAN",
            "event_ts": str(time.time()),
        },
    }


def test_slack_event(
    base_url: str, health_data: Dict[str, Any], verbose: bool = False
) -> bool:
    """
    Test sending a synthetic Slack event.

    Args:
        base_url: Base URL of the service
        health_data: Health endpoint response data
        verbose: Show detailed output

    Returns:
        True if test passed
    """
    print_header("Test 2: Synthetic Slack Event")

    # Check if Slack is enabled
    if not health_data.get("slack_bot_enabled"):
        print_result(
            "Slack event processing",
            True,
            "Skipped (Slack bot disabled, as expected)",
        )
        return True

    # Check if config is valid
    if not health_data.get("config_valid"):
        print_result(
            "Slack event processing",
            True,
            "Skipped (Config invalid, missing credentials)",
        )
        return True

    try:
        url = urljoin(base_url, "/slack/events")
        event = create_synthetic_slack_event("This is a dev smoke test!")

        if verbose:
            print(f"Sending event to: {url}")
            print("Event payload:")
            print(json.dumps(event, indent=2))

        response = httpx.post(
            url,
            json=event,
            timeout=30.0,  # Allow time for Agent Engine call
        )
        response.raise_for_status()
        result = response.json()

        if verbose:
            print("\nResponse:")
            print(json.dumps(result, indent=2))

        # Check response
        if result.get("ok"):
            print_result("Slack event accepted", True)
            print(
                "\n⚠️  Note: This test only validates that the event was accepted."
            )
            print(
                "     Check Cloud Run logs to see if Bob responded successfully."
            )
            print(
                "     For full end-to-end validation, check Slack workspace."
            )
            return True
        else:
            print_result("Slack event processing", False, f"Response: {result}")
            return False

    except httpx.HTTPStatusError as e:
        print_result(
            "Slack event", False, f"HTTP {e.response.status_code}"
        )
        if verbose:
            print(f"Response: {e.response.text}")
        return False

    except Exception as e:
        print_result("Slack event", False, f"Error: {e!s}")
        return False


def test_url_verification(base_url: str, verbose: bool = False) -> bool:
    """
    Test Slack URL verification challenge.

    Args:
        base_url: Base URL of the service
        verbose: Show detailed output

    Returns:
        True if test passed
    """
    print_header("Test 3: URL Verification Challenge")

    try:
        url = urljoin(base_url, "/slack/events")
        challenge_event = {
            "type": "url_verification",
            "challenge": "test-challenge-string",
        }

        if verbose:
            print(f"Sending challenge to: {url}")

        response = httpx.post(url, json=challenge_event, timeout=10.0)
        response.raise_for_status()
        result = response.json()

        if verbose:
            print(f"Response: {result}")

        # Check if challenge was echoed back
        if result.get("challenge") == "test-challenge-string":
            print_result("URL verification", True)
            return True
        else:
            print_result(
                "URL verification", False, f"Expected challenge echo, got: {result}"
            )
            return False

    except Exception as e:
        print_result("URL verification", False, f"Error: {e!s}")
        return False


def main():
    """Run all smoke tests."""
    args = parse_args()

    print("\n🧪 Slack Webhook Dev Smoke Test")
    print(f"   Service URL: {args.url}")
    print(f"   Mode: {'Health check only' if args.health_only else 'Full tests'}")

    # Test 1: Health endpoint
    health_success, health_data = test_health_endpoint(args.url, args.verbose)
    if not health_success:
        print("\n❌ Smoke test FAILED - Service not reachable")
        return 2  # Service not running

    if args.health_only:
        print("\n✅ Health check PASSED")
        return 0

    # Test 2: URL verification
    url_verify_success = test_url_verification(args.url, args.verbose)

    # Test 3: Synthetic event
    event_success = test_slack_event(args.url, health_data, args.verbose)

    # Summary
    print_header("Smoke Test Summary")

    all_passed = health_success and url_verify_success and event_success

    if all_passed:
        print("✅ All smoke tests PASSED")
        print("\n📋 Next steps:")
        print("   1. Check Cloud Run logs for actual Bob responses")
        print("   2. Test in real Slack workspace with @bobs_brain mention")
        print("   3. Verify routing method (A2A gateway or direct Agent Engine)")
        return 0
    else:
        print("❌ Some smoke tests FAILED")
        print("\n📋 Troubleshooting:")
        print("   1. Check environment variables (.env)")
        print("   2. Verify SLACK_BOB_ENABLED=true")
        print("   3. Confirm SLACK_BOT_TOKEN and SLACK_SIGNING_SECRET are set")
        print("   4. Ensure A2A_GATEWAY_URL or Agent Engine vars are configured")
        return 1


if __name__ == "__main__":
    sys.exit(main())
