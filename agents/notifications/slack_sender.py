"""
Slack message sender for SWE/portfolio notifications.

Handles the actual HTTP POST to Slack webhooks or Slack API.

Usage:
    from agents.notifications.slack_sender import send_portfolio_notification

    success = send_portfolio_notification(portfolio_result, env="dev")
"""

import logging
import os
from typing import Any, Dict, List, Optional

import requests

from agents.config.notifications import (
    SlackDestination,
    get_swe_slack_destination,
    should_send_slack_notifications,
)
from agents.notifications.slack_formatter import format_portfolio_completion
from agents.shared_contracts import PortfolioResult

logger = logging.getLogger(__name__)


def send_portfolio_notification(
    result: PortfolioResult, env: str = "dev", *, timeout: int = 10
) -> bool:
    """
    Send a portfolio completion notification to Slack.

    This is the main entry point for sending Slack notifications from the
    portfolio orchestrator.

    Args:
        result: The portfolio result to send
        env: Environment name (dev/staging/prod)
        timeout: HTTP request timeout in seconds

    Returns:
        bool: True if sent successfully, False otherwise.

    Note:
        Failures are logged but do NOT raise exceptions - this function is
        designed to never crash the caller's pipeline.
    """
    # Guard: Check if notifications are enabled and configured
    if not should_send_slack_notifications():
        logger.info("Slack notifications disabled or not configured - skipping")
        return False

    destination = get_swe_slack_destination()
    if not destination:
        logger.warning("No Slack destination configured - skipping notification")
        return False

    try:
        # Format the message
        blocks = format_portfolio_completion(result, env=env)

        # Send via appropriate method
        if destination.webhook_url:
            success = _send_via_webhook(
                destination.webhook_url, blocks, timeout=timeout
            )
        elif destination.channel_id:
            success = _send_via_api(destination.channel_id, blocks, timeout=timeout)
        else:
            logger.error("Slack destination has neither webhook_url nor channel_id")
            return False

        if success:
            logger.info(f"Successfully sent portfolio notification to Slack ({env})")
        else:
            logger.warning(f"Failed to send portfolio notification to Slack ({env})")

        return success

    except Exception as e:
        # Catch-all: log but never crash the caller
        logger.error(f"Unexpected error sending Slack notification: {e}", exc_info=True)
        return False


def _send_via_webhook(
    webhook_url: str, blocks: List[Dict[str, Any]], *, timeout: int = 10
) -> bool:
    """
    Send message via Slack webhook URL.

    Args:
        webhook_url: The Slack webhook URL
        blocks: Block Kit blocks to send
        timeout: HTTP request timeout

    Returns:
        bool: True if successful, False otherwise.
    """
    payload = {"blocks": blocks}

    try:
        response = requests.post(
            webhook_url,
            json=payload,
            timeout=timeout,
            headers={"Content-Type": "application/json"},
        )

        if response.status_code == 200 and response.text == "ok":
            logger.debug("Webhook POST succeeded")
            return True
        else:
            logger.warning(
                f"Webhook POST failed: status={response.status_code}, "
                f"body={response.text[:200]}"
            )
            return False

    except requests.exceptions.Timeout:
        logger.warning(f"Webhook POST timed out after {timeout}s")
        return False
    except requests.exceptions.RequestException as e:
        logger.warning(f"Webhook POST request failed: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error in webhook POST: {e}", exc_info=True)
        return False


def _send_via_api(
    channel_id: str, blocks: List[Dict[str, Any]], *, timeout: int = 10
) -> bool:
    """
    Send message via Slack API (requires bot token).

    Args:
        channel_id: The Slack channel ID
        blocks: Block Kit blocks to send
        timeout: HTTP request timeout

    Returns:
        bool: True if successful, False otherwise.
    """
    # Get bot token from environment
    bot_token = os.getenv("SLACK_BOT_TOKEN")
    if not bot_token:
        logger.error("SLACK_BOT_TOKEN not set - cannot send via API")
        return False

    url = "https://slack.com/api/chat.postMessage"
    headers = {
        "Authorization": f"Bearer {bot_token}",
        "Content-Type": "application/json",
    }
    payload = {"channel": channel_id, "blocks": blocks}

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=timeout)

        if response.status_code == 200:
            data = response.json()
            if data.get("ok"):
                logger.debug(f"API POST succeeded: ts={data.get('ts')}")
                return True
            else:
                logger.warning(f"API POST failed: {data.get('error')}")
                return False
        else:
            logger.warning(f"API POST failed: status={response.status_code}")
            return False

    except requests.exceptions.Timeout:
        logger.warning(f"API POST timed out after {timeout}s")
        return False
    except requests.exceptions.RequestException as e:
        logger.warning(f"API POST request failed: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error in API POST: {e}", exc_info=True)
        return False


# ============================================================================
# TESTING & DIAGNOSTICS
# ============================================================================


def test_slack_connection(
    destination: Optional[SlackDestination] = None, *, timeout: int = 10
) -> bool:
    """
    Test Slack connection with a simple message.

    Sends a test message to verify connectivity and configuration.

    Args:
        destination: SlackDestination to test (if None, uses config)
        timeout: HTTP request timeout

    Returns:
        bool: True if test message sent successfully.
    """
    if destination is None:
        destination = get_swe_slack_destination()

    if not destination or not destination.is_valid():
        logger.error("No valid Slack destination configured")
        return False

    # Create a simple test message
    test_blocks = [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": ":white_check_mark: *Slack Connection Test*\n"
                "This is a test message from Bob's Brain notification system.",
            },
        },
        {
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": "If you see this, Slack notifications are working!",
                }
            ],
        },
    ]

    try:
        if destination.webhook_url:
            success = _send_via_webhook(
                destination.webhook_url, test_blocks, timeout=timeout
            )
        elif destination.channel_id:
            success = _send_via_api(
                destination.channel_id, test_blocks, timeout=timeout
            )
        else:
            logger.error("Destination has neither webhook_url nor channel_id")
            return False

        if success:
            logger.info("✅ Slack connection test PASSED")
        else:
            logger.error("❌ Slack connection test FAILED")

        return success

    except Exception as e:
        logger.error(f"Slack connection test error: {e}", exc_info=True)
        return False


if __name__ == "__main__":
    # Quick test/demo
    import sys

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    print("Slack Sender Test")
    print("=" * 60)
    print()

    # Check if notifications are enabled
    if not should_send_slack_notifications():
        print("❌ Slack notifications are not enabled or configured")
        print()
        print("To enable:")
        print("  export SLACK_NOTIFICATIONS_ENABLED=true")
        print(
            "  export SLACK_SWE_CHANNEL_WEBHOOK_URL=https://hooks.slack.com/services/..."
        )
        sys.exit(1)

    # Test connection
    print("Testing Slack connection...")
    success = test_slack_connection()

    if success:
        print()
        print("✅ Slack notifications are working!")
        print()
        print("You can now send portfolio notifications using:")
        print("  send_portfolio_notification(portfolio_result, env='dev')")
        sys.exit(0)
    else:
        print()
        print("❌ Slack connection test failed")
        print("Check logs above for details")
        sys.exit(1)
