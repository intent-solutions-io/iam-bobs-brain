"""
Notification system for Bob's Brain SWE/portfolio pipeline.

Provides Slack notifications for pipeline completion events.

Usage:
    from agents.notifications import send_portfolio_notification

    success = send_portfolio_notification(portfolio_result, env="dev")
"""

from agents.notifications.slack_formatter import (
    format_portfolio_completion,
    format_portfolio_completion_simple,
)
from agents.notifications.slack_sender import (
    send_portfolio_notification,
    test_slack_connection,
)

__all__ = [
    "format_portfolio_completion",
    "format_portfolio_completion_simple",
    "send_portfolio_notification",
    "test_slack_connection",
]
