"""
Unit tests for notifications configuration module.

Tests the notification config helpers and feature flag behavior.
"""

import os
from unittest.mock import patch

from agents.config.notifications import (
    SlackDestination,
    are_slack_notifications_enabled,
    get_notification_summary,
    get_swe_slack_destination,
    should_send_slack_notifications,
)


class TestSlackDestination:
    """Tests for SlackDestination dataclass."""

    def test_webhook_url_valid(self):
        """Test destination with webhook URL is valid."""
        dest = SlackDestination(webhook_url="https://hooks.slack.com/services/ABC123")
        assert dest.is_valid()

    def test_channel_id_valid(self):
        """Test destination with channel ID is valid."""
        dest = SlackDestination(channel_id="C12345678")
        assert dest.is_valid()

    def test_empty_destination_invalid(self):
        """Test empty destination is invalid."""
        dest = SlackDestination()
        assert not dest.is_valid()

    def test_repr_masks_webhook(self):
        """Test __repr__ masks long webhook URLs."""
        dest = SlackDestination(
            webhook_url="https://hooks.slack.com/services/VERYLONGTOKEN123456789"
        )
        repr_str = repr(dest)
        assert "..." in repr_str
        assert "VERYLONGTOKEN" not in repr_str  # Should be truncated

    def test_repr_shows_channel(self):
        """Test __repr__ shows channel ID."""
        dest = SlackDestination(channel_id="C12345678")
        repr_str = repr(dest)
        assert "C12345678" in repr_str


class TestSlackNotificationsEnabled:
    """Tests for are_slack_notifications_enabled()."""

    def test_default_disabled(self):
        """Test notifications are disabled by default."""
        with patch.dict(os.environ, {}, clear=True):
            assert not are_slack_notifications_enabled()

    def test_enabled_with_true(self):
        """Test notifications enabled with 'true'."""
        with patch.dict(os.environ, {"SLACK_NOTIFICATIONS_ENABLED": "true"}):
            assert are_slack_notifications_enabled()

    def test_enabled_with_1(self):
        """Test notifications enabled with '1'."""
        with patch.dict(os.environ, {"SLACK_NOTIFICATIONS_ENABLED": "1"}):
            assert are_slack_notifications_enabled()

    def test_enabled_with_yes(self):
        """Test notifications enabled with 'yes'."""
        with patch.dict(os.environ, {"SLACK_NOTIFICATIONS_ENABLED": "yes"}):
            assert are_slack_notifications_enabled()

    def test_disabled_with_false(self):
        """Test notifications disabled with 'false'."""
        with patch.dict(os.environ, {"SLACK_NOTIFICATIONS_ENABLED": "false"}):
            assert not are_slack_notifications_enabled()

    def test_disabled_with_invalid_value(self):
        """Test notifications disabled with invalid value."""
        with patch.dict(os.environ, {"SLACK_NOTIFICATIONS_ENABLED": "maybe"}):
            assert not are_slack_notifications_enabled()


class TestGetSweSlackDestination:
    """Tests for get_swe_slack_destination()."""

    def test_returns_none_when_not_configured(self):
        """Test returns None when no destination configured."""
        with patch.dict(os.environ, {}, clear=True):
            dest = get_swe_slack_destination()
            assert dest is None

    def test_returns_webhook_destination(self):
        """Test returns webhook destination when configured."""
        webhook = "https://hooks.slack.com/services/TEST"
        with patch.dict(os.environ, {"SLACK_SWE_CHANNEL_WEBHOOK_URL": webhook}):
            dest = get_swe_slack_destination()
            assert dest is not None
            assert dest.webhook_url == webhook
            assert dest.channel_id is None

    def test_returns_channel_destination(self):
        """Test returns channel destination when configured."""
        channel = "C12345678"
        with patch.dict(os.environ, {"SLACK_SWE_CHANNEL_ID": channel}):
            dest = get_swe_slack_destination()
            assert dest is not None
            assert dest.channel_id == channel
            assert dest.webhook_url is None

    def test_prefers_webhook_over_channel(self):
        """Test webhook is preferred when both are configured."""
        webhook = "https://hooks.slack.com/services/TEST"
        channel = "C12345678"
        with patch.dict(
            os.environ,
            {"SLACK_SWE_CHANNEL_WEBHOOK_URL": webhook, "SLACK_SWE_CHANNEL_ID": channel},
        ):
            dest = get_swe_slack_destination()
            assert dest is not None
            assert dest.webhook_url == webhook
            assert dest.channel_id is None


class TestShouldSendSlackNotifications:
    """Tests for should_send_slack_notifications()."""

    def test_false_when_disabled(self):
        """Test returns False when notifications disabled."""
        with patch.dict(os.environ, {}, clear=True):
            assert not should_send_slack_notifications()

    def test_false_when_enabled_but_no_destination(self):
        """Test returns False when enabled but destination not configured."""
        with patch.dict(os.environ, {"SLACK_NOTIFICATIONS_ENABLED": "true"}):
            assert not should_send_slack_notifications()

    def test_true_when_enabled_and_webhook_configured(self):
        """Test returns True when enabled and webhook configured."""
        with patch.dict(
            os.environ,
            {
                "SLACK_NOTIFICATIONS_ENABLED": "true",
                "SLACK_SWE_CHANNEL_WEBHOOK_URL": "https://hooks.slack.com/services/TEST",
            },
        ):
            assert should_send_slack_notifications()

    def test_true_when_enabled_and_channel_configured(self):
        """Test returns True when enabled and channel configured."""
        with patch.dict(
            os.environ,
            {
                "SLACK_NOTIFICATIONS_ENABLED": "true",
                "SLACK_SWE_CHANNEL_ID": "C12345678",
            },
        ):
            assert should_send_slack_notifications()


class TestGetNotificationSummary:
    """Tests for get_notification_summary()."""

    def test_summary_shows_disabled_state(self):
        """Test summary shows when notifications are disabled."""
        with patch.dict(os.environ, {}, clear=True):
            summary = get_notification_summary()
            assert "Slack Enabled: False" in summary
            assert "Not configured" in summary
            assert "Ready to Send: False" in summary

    def test_summary_shows_enabled_state(self):
        """Test summary shows when notifications are enabled and configured."""
        with patch.dict(
            os.environ,
            {
                "SLACK_NOTIFICATIONS_ENABLED": "true",
                "SLACK_SWE_CHANNEL_WEBHOOK_URL": "https://hooks.slack.com/services/TEST",
            },
        ):
            summary = get_notification_summary()
            assert "Slack Enabled: True" in summary
            assert "SlackDestination" in summary
            assert "Ready to Send: True" in summary
