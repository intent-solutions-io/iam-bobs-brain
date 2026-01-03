"""
Unit tests for Slack sender module.

Tests the actual sending logic with mocked HTTP requests.
"""

import pytest
import os
from unittest.mock import patch, MagicMock, Mock
from datetime import datetime

from agents.shared_contracts import PortfolioResult
from agents.config.notifications import SlackDestination
from agents.notifications.slack_sender import (
    send_portfolio_notification,
    _send_via_webhook,
    _send_via_api,
    test_slack_connection
)


@pytest.fixture
def sample_portfolio_result():
    """Create a sample PortfolioResult for testing."""
    return PortfolioResult(
        portfolio_run_id="test-12345678-abcd",
        repos=[],
        total_repos_analyzed=5,
        total_issues_found=42,
        total_issues_fixed=30,
        portfolio_duration_seconds=456.78,
        timestamp=datetime.now()
    )


class TestSendPortfolioNotification:
    """Tests for send_portfolio_notification()."""

    def test_returns_false_when_disabled(self, sample_portfolio_result):
        """Test returns False when notifications disabled."""
        with patch.dict(os.environ, {}, clear=True):
            result = send_portfolio_notification(sample_portfolio_result, env="dev")
            assert result is False

    def test_returns_false_when_no_destination(self, sample_portfolio_result):
        """Test returns False when enabled but no destination."""
        with patch.dict(os.environ, {"SLACK_NOTIFICATIONS_ENABLED": "true"}):
            result = send_portfolio_notification(sample_portfolio_result, env="dev")
            assert result is False

    @patch("agents.notifications.slack_sender._send_via_webhook")
    def test_calls_webhook_sender_when_webhook_configured(
        self, mock_webhook, sample_portfolio_result
    ):
        """Test calls webhook sender when webhook URL configured."""
        mock_webhook.return_value = True

        with patch.dict(os.environ, {
            "SLACK_NOTIFICATIONS_ENABLED": "true",
            "SLACK_SWE_CHANNEL_WEBHOOK_URL": "https://hooks.slack.com/services/TEST"
        }):
            result = send_portfolio_notification(sample_portfolio_result, env="dev")
            assert result is True
            mock_webhook.assert_called_once()

    @patch("agents.notifications.slack_sender._send_via_api")
    def test_calls_api_sender_when_channel_configured(
        self, mock_api, sample_portfolio_result
    ):
        """Test calls API sender when channel ID configured."""
        mock_api.return_value = True

        with patch.dict(os.environ, {
            "SLACK_NOTIFICATIONS_ENABLED": "true",
            "SLACK_SWE_CHANNEL_ID": "C12345678"
        }):
            result = send_portfolio_notification(sample_portfolio_result, env="dev")
            assert result is True
            mock_api.assert_called_once()

    @patch("agents.notifications.slack_sender._send_via_webhook")
    def test_returns_false_on_send_failure(
        self, mock_webhook, sample_portfolio_result
    ):
        """Test returns False when send fails."""
        mock_webhook.return_value = False

        with patch.dict(os.environ, {
            "SLACK_NOTIFICATIONS_ENABLED": "true",
            "SLACK_SWE_CHANNEL_WEBHOOK_URL": "https://hooks.slack.com/services/TEST"
        }):
            result = send_portfolio_notification(sample_portfolio_result, env="dev")
            assert result is False

    @patch("agents.notifications.slack_sender._send_via_webhook")
    def test_handles_exception_gracefully(
        self, mock_webhook, sample_portfolio_result
    ):
        """Test handles exceptions without crashing."""
        mock_webhook.side_effect = Exception("Network error")

        with patch.dict(os.environ, {
            "SLACK_NOTIFICATIONS_ENABLED": "true",
            "SLACK_SWE_CHANNEL_WEBHOOK_URL": "https://hooks.slack.com/services/TEST"
        }):
            result = send_portfolio_notification(sample_portfolio_result, env="dev")
            assert result is False  # Should not crash


class TestSendViaWebhook:
    """Tests for _send_via_webhook()."""

    @patch("agents.notifications.slack_sender.requests.post")
    def test_returns_true_on_success(self, mock_post):
        """Test returns True when webhook POST succeeds."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = "ok"
        mock_post.return_value = mock_response

        webhook_url = "https://hooks.slack.com/services/TEST"
        blocks = [{"type": "section", "text": {"type": "mrkdwn", "text": "Test"}}]

        result = _send_via_webhook(webhook_url, blocks)
        assert result is True
        mock_post.assert_called_once()

    @patch("agents.notifications.slack_sender.requests.post")
    def test_returns_false_on_non_200_status(self, mock_post):
        """Test returns False when webhook returns non-200 status."""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_post.return_value = mock_response

        webhook_url = "https://hooks.slack.com/services/TEST"
        blocks = [{"type": "section", "text": {"type": "mrkdwn", "text": "Test"}}]

        result = _send_via_webhook(webhook_url, blocks)
        assert result is False

    @patch("agents.notifications.slack_sender.requests.post")
    def test_returns_false_on_non_ok_response(self, mock_post):
        """Test returns False when webhook returns 200 but not 'ok'."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = "invalid_payload"
        mock_post.return_value = mock_response

        webhook_url = "https://hooks.slack.com/services/TEST"
        blocks = [{"type": "section", "text": {"type": "mrkdwn", "text": "Test"}}]

        result = _send_via_webhook(webhook_url, blocks)
        assert result is False

    @patch("agents.notifications.slack_sender.requests.post")
    def test_handles_timeout(self, mock_post):
        """Test handles timeout gracefully."""
        import requests
        mock_post.side_effect = requests.exceptions.Timeout()

        webhook_url = "https://hooks.slack.com/services/TEST"
        blocks = [{"type": "section", "text": {"type": "mrkdwn", "text": "Test"}}]

        result = _send_via_webhook(webhook_url, blocks, timeout=5)
        assert result is False

    @patch("agents.notifications.slack_sender.requests.post")
    def test_handles_request_exception(self, mock_post):
        """Test handles request exceptions gracefully."""
        import requests
        mock_post.side_effect = requests.exceptions.RequestException("Network error")

        webhook_url = "https://hooks.slack.com/services/TEST"
        blocks = [{"type": "section", "text": {"type": "mrkdwn", "text": "Test"}}]

        result = _send_via_webhook(webhook_url, blocks)
        assert result is False

    @patch("agents.notifications.slack_sender.requests.post")
    def test_sends_correct_payload(self, mock_post):
        """Test sends correct JSON payload to webhook."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = "ok"
        mock_post.return_value = mock_response

        webhook_url = "https://hooks.slack.com/services/TEST"
        blocks = [{"type": "section", "text": {"type": "mrkdwn", "text": "Test"}}]

        _send_via_webhook(webhook_url, blocks)

        # Check that post was called with correct arguments
        call_kwargs = mock_post.call_args.kwargs
        assert "json" in call_kwargs
        assert call_kwargs["json"]["blocks"] == blocks


class TestSendViaApi:
    """Tests for _send_via_api()."""

    def test_returns_false_when_no_bot_token(self):
        """Test returns False when SLACK_BOT_TOKEN not set."""
        with patch.dict(os.environ, {}, clear=True):
            channel_id = "C12345678"
            blocks = [{"type": "section", "text": {"type": "mrkdwn", "text": "Test"}}]

            result = _send_via_api(channel_id, blocks)
            assert result is False

    @patch("agents.notifications.slack_sender.requests.post")
    def test_returns_true_on_success(self, mock_post):
        """Test returns True when API POST succeeds."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"ok": True, "ts": "1234567890.123456"}
        mock_post.return_value = mock_response

        with patch.dict(os.environ, {"SLACK_BOT_TOKEN": "xoxb-test-token"}):
            channel_id = "C12345678"
            blocks = [{"type": "section", "text": {"type": "mrkdwn", "text": "Test"}}]

            result = _send_via_api(channel_id, blocks)
            assert result is True
            mock_post.assert_called_once()

    @patch("agents.notifications.slack_sender.requests.post")
    def test_returns_false_on_api_error(self, mock_post):
        """Test returns False when API returns error."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"ok": False, "error": "channel_not_found"}
        mock_post.return_value = mock_response

        with patch.dict(os.environ, {"SLACK_BOT_TOKEN": "xoxb-test-token"}):
            channel_id = "C12345678"
            blocks = [{"type": "section", "text": {"type": "mrkdwn", "text": "Test"}}]

            result = _send_via_api(channel_id, blocks)
            assert result is False

    @patch("agents.notifications.slack_sender.requests.post")
    def test_uses_bearer_token(self, mock_post):
        """Test uses Bearer token authentication."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"ok": True}
        mock_post.return_value = mock_response

        with patch.dict(os.environ, {"SLACK_BOT_TOKEN": "xoxb-test-token"}):
            channel_id = "C12345678"
            blocks = [{"type": "section", "text": {"type": "mrkdwn", "text": "Test"}}]

            _send_via_api(channel_id, blocks)

            # Check that post was called with correct headers
            call_kwargs = mock_post.call_args.kwargs
            assert "headers" in call_kwargs
            assert "Bearer xoxb-test-token" in call_kwargs["headers"]["Authorization"]


class TestSlackConnection:
    """Tests for test_slack_connection()."""

    def test_returns_false_when_no_destination(self):
        """Test returns False when no destination configured."""
        with patch.dict(os.environ, {}, clear=True):
            result = test_slack_connection()
            assert result is False

    @patch("agents.notifications.slack_sender._send_via_webhook")
    def test_calls_webhook_for_webhook_destination(self, mock_webhook):
        """Test calls webhook sender for webhook destination."""
        mock_webhook.return_value = True

        dest = SlackDestination(webhook_url="https://hooks.slack.com/services/TEST")
        result = test_slack_connection(destination=dest)
        assert result is True
        mock_webhook.assert_called_once()

    @patch("agents.notifications.slack_sender._send_via_api")
    def test_calls_api_for_channel_destination(self, mock_api):
        """Test calls API sender for channel destination."""
        mock_api.return_value = True

        with patch.dict(os.environ, {"SLACK_BOT_TOKEN": "xoxb-test-token"}):
            dest = SlackDestination(channel_id="C12345678")
            result = test_slack_connection(destination=dest)
            assert result is True
            mock_api.assert_called_once()

    @patch("agents.notifications.slack_sender._send_via_webhook")
    def test_handles_test_failure(self, mock_webhook):
        """Test handles connection test failure."""
        mock_webhook.return_value = False

        dest = SlackDestination(webhook_url="https://hooks.slack.com/services/TEST")
        result = test_slack_connection(destination=dest)
        assert result is False
