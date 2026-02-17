"""
Notification configuration module for Slack and other notification channels.

This module provides configuration for sending notifications about SWE/portfolio
completion via Slack and other channels. All features are OPT-IN by default.

ENVIRONMENT-AWARE BEHAVIOR (Phase LIVE3-STAGE-PROD-SAFETY):
- dev: Enabled if SLACK_NOTIFICATIONS_ENABLED=true + webhook set
- staging: Disabled by default; requires SLACK_ENABLE_STAGING=true
- prod: Disabled by default; requires SLACK_ENABLE_PROD=true

Environment Variables:
- SLACK_NOTIFICATIONS_ENABLED: Enable Slack notifications (default: false)
- SLACK_SWE_CHANNEL_WEBHOOK_URL: Webhook URL for SWE notifications
- SLACK_SWE_CHANNEL_ID: Channel ID for SWE notifications (alternative to webhook)
- SLACK_ENABLE_STAGING: Allow Slack in staging (default: false)
- SLACK_ENABLE_PROD: Allow Slack in prod (default: false)
- SLACK_ENV_LABEL: Optional environment label for message prefixes (e.g., "[DEV]")

Usage:
    from agents.config.notifications import (
        should_send_slack_notifications,
        get_swe_slack_destination,
        get_slack_env_prefix
    )

    if should_send_slack_notifications():
        dest = get_swe_slack_destination()
        prefix = get_slack_env_prefix()
        # Send notification with prefix to dest
"""

import logging
import os
from dataclasses import dataclass
from enum import Enum
from typing import Literal, Optional

logger = logging.getLogger(__name__)


class SlackMode(Enum):
    """Slack notification mode based on environment and flags."""
    DISABLED = "disabled"  # Feature off or blocked by environment
    ENABLED = "enabled"    # Ready to send notifications


def _get_current_environment() -> Literal["dev", "staging", "prod"]:
    """Get current environment (imported from features module to avoid circular imports)."""
    from agents.config.features import get_current_environment
    return get_current_environment()


def get_slack_mode() -> SlackMode:
    """
    Determine if Slack notifications should be sent based on environment and flags.

    Behavior matrix:
    - dev: ENABLED if SLACK_NOTIFICATIONS_ENABLED=true + webhook set
    - staging: DISABLED unless SLACK_ENABLE_STAGING=true
    - prod: DISABLED unless SLACK_ENABLE_PROD=true

    Returns:
        SlackMode.ENABLED or SlackMode.DISABLED

    Examples:
        >>> # Dev environment
        >>> os.environ["DEPLOYMENT_ENV"] = "dev"
        >>> os.environ["SLACK_NOTIFICATIONS_ENABLED"] = "true"
        >>> os.environ["SLACK_SWE_CHANNEL_WEBHOOK_URL"] = "https://..."
        >>> get_slack_mode()
        SlackMode.ENABLED

        >>> # Staging environment (requires explicit override)
        >>> os.environ["DEPLOYMENT_ENV"] = "staging"
        >>> os.environ["SLACK_NOTIFICATIONS_ENABLED"] = "true"
        >>> os.environ["SLACK_ENABLE_STAGING"] = "false"
        >>> get_slack_mode()
        SlackMode.DISABLED
    """
    # Check global enable flag first
    if not are_slack_notifications_enabled():
        logger.debug("Slack mode: DISABLED (feature flag off)")
        return SlackMode.DISABLED

    # Get current environment
    env = _get_current_environment()

    # Dev: enabled if webhook is configured
    if env == "dev":
        dest = get_swe_slack_destination()
        if dest and dest.is_valid():
            logger.info("Slack mode: ENABLED (dev environment)")
            return SlackMode.ENABLED
        else:
            logger.warning("Slack mode: DISABLED (dev but no webhook configured)")
            return SlackMode.DISABLED

    # Staging: requires explicit SLACK_ENABLE_STAGING=true
    elif env == "staging":
        enable_staging = os.getenv("SLACK_ENABLE_STAGING", "false").lower() == "true"
        if not enable_staging:
            logger.info("Slack mode: DISABLED (staging requires SLACK_ENABLE_STAGING=true)")
            return SlackMode.DISABLED

        dest = get_swe_slack_destination()
        if dest and dest.is_valid():
            logger.warning("⚠️  Slack mode: ENABLED (staging - explicit override)")
            return SlackMode.ENABLED
        else:
            logger.warning("Slack mode: DISABLED (staging enabled but no webhook)")
            return SlackMode.DISABLED

    # Prod: requires explicit SLACK_ENABLE_PROD=true
    elif env == "prod":
        enable_prod = os.getenv("SLACK_ENABLE_PROD", "false").lower() == "true"
        if not enable_prod:
            logger.info("Slack mode: DISABLED (prod requires SLACK_ENABLE_PROD=true)")
            return SlackMode.DISABLED

        dest = get_swe_slack_destination()
        if dest and dest.is_valid():
            logger.warning("⚠️  Slack mode: ENABLED (PRODUCTION - explicit override)")
            return SlackMode.ENABLED
        else:
            logger.warning("Slack mode: DISABLED (prod enabled but no webhook)")
            return SlackMode.DISABLED

    # Unknown environment: disable for safety
    logger.warning(f"Slack mode: DISABLED (unknown environment: {env})")
    return SlackMode.DISABLED


def get_slack_env_prefix() -> str:
    """
    Get environment prefix for Slack messages.

    Uses SLACK_ENV_LABEL if set, otherwise generates from environment.

    Returns:
        Prefix string (e.g., "[DEV]", "[STAGING]", "[PROD]")

    Examples:
        >>> os.environ["DEPLOYMENT_ENV"] = "dev"
        >>> get_slack_env_prefix()
        "[DEV]"

        >>> os.environ["SLACK_ENV_LABEL"] = "QA"
        >>> get_slack_env_prefix()
        "[QA]"
    """
    # Check for explicit label
    custom_label = os.getenv("SLACK_ENV_LABEL", "").strip()
    if custom_label:
        return f"[{custom_label.upper()}]"

    # Generate from environment
    env = _get_current_environment()
    return f"[{env.upper()}]"


@dataclass
class SlackDestination:
    """
    Represents a Slack notification destination.

    Either webhook_url OR channel_id should be set, not both.
    """
    webhook_url: Optional[str] = None
    channel_id: Optional[str] = None

    def is_valid(self) -> bool:
        """Check if destination has at least one valid target."""
        return bool(self.webhook_url or self.channel_id)

    def __repr__(self) -> str:
        if self.webhook_url:
            # Mask webhook URL for security
            masked = self.webhook_url[:30] + "..." if len(self.webhook_url) > 30 else self.webhook_url
            return f"SlackDestination(webhook={masked})"
        elif self.channel_id:
            return f"SlackDestination(channel={self.channel_id})"
        return "SlackDestination(unconfigured)"


def are_slack_notifications_enabled() -> bool:
    """
    Check if Slack notifications are enabled.

    Returns:
        bool: True if SLACK_NOTIFICATIONS_ENABLED is set to 'true', False otherwise.

    Default: False (opt-in)
    """
    enabled_str = os.getenv("SLACK_NOTIFICATIONS_ENABLED", "false").lower()
    is_enabled = enabled_str in ("true", "1", "yes")

    if is_enabled:
        logger.info("Slack notifications are ENABLED")
    else:
        logger.debug("Slack notifications are DISABLED (set SLACK_NOTIFICATIONS_ENABLED=true to enable)")

    return is_enabled


def get_swe_slack_destination() -> Optional[SlackDestination]:
    """
    Get the Slack destination for SWE/portfolio notifications.

    Checks environment variables in priority order:
    1. SLACK_SWE_CHANNEL_WEBHOOK_URL (preferred - direct webhook)
    2. SLACK_SWE_CHANNEL_ID (alternative - requires bot token)

    Returns:
        SlackDestination or None if not configured.
    """
    webhook_url = os.getenv("SLACK_SWE_CHANNEL_WEBHOOK_URL")
    channel_id = os.getenv("SLACK_SWE_CHANNEL_ID")

    if webhook_url:
        logger.info(f"Slack SWE destination: webhook (masked: {webhook_url[:30]}...)")
        return SlackDestination(webhook_url=webhook_url)
    elif channel_id:
        logger.info(f"Slack SWE destination: channel_id={channel_id}")
        return SlackDestination(channel_id=channel_id)
    else:
        logger.warning(
            "No Slack SWE destination configured. Set SLACK_SWE_CHANNEL_WEBHOOK_URL "
            "or SLACK_SWE_CHANNEL_ID to receive notifications."
        )
        return None


def should_send_slack_notifications() -> bool:
    """
    Combined check: are notifications enabled AND is destination configured?

    This is the main guard function to use before attempting to send Slack messages.

    ENVIRONMENT-AWARE (Phase LIVE3-STAGE-PROD-SAFETY):
    Uses get_slack_mode() to respect environment-specific safety guards.

    Returns:
        bool: True if both enabled and configured, False otherwise.

    Examples:
        >>> # Dev: enabled if flags + webhook set
        >>> should_send_slack_notifications()
        True

        >>> # Staging: disabled unless SLACK_ENABLE_STAGING=true
        >>> os.environ["DEPLOYMENT_ENV"] = "staging"
        >>> should_send_slack_notifications()
        False
    """
    # Use environment-aware mode check
    mode = get_slack_mode()
    return mode == SlackMode.ENABLED


def get_notification_summary() -> str:
    """
    Get a human-readable summary of notification configuration.

    Useful for logging, diagnostics, and readiness checks.

    Returns:
        str: Multi-line summary of notification status.
    """
    lines = []
    lines.append("Notification Configuration:")
    lines.append(f"  Environment: {_get_current_environment()}")
    lines.append(f"  Slack Enabled: {are_slack_notifications_enabled()}")

    destination = get_swe_slack_destination()
    if destination:
        lines.append(f"  Slack Destination: {destination}")
    else:
        lines.append("  Slack Destination: Not configured")

    mode = get_slack_mode()
    lines.append(f"  Slack Mode: {mode.value}")
    lines.append(f"  Environment Prefix: {get_slack_env_prefix()}")
    lines.append(f"  Ready to Send: {should_send_slack_notifications()}")

    return "\n".join(lines)


# Convenience function for logging config at startup
def log_notification_config() -> None:
    """Log the current notification configuration."""
    logger.info(get_notification_summary())


if __name__ == "__main__":
    # Quick test/diagnostic when run directly
    import sys
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    print(get_notification_summary())
    print()

    if should_send_slack_notifications():
        print("✅ Ready to send Slack notifications")
        sys.exit(0)
    else:
        print("❌ Slack notifications not ready (disabled or misconfigured)")
        print()
        print("To enable:")
        print("  export SLACK_NOTIFICATIONS_ENABLED=true")
        print("  export SLACK_SWE_CHANNEL_WEBHOOK_URL=https://hooks.slack.com/services/...")
        sys.exit(1)
