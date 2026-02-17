"""
Slack message formatter for SWE/portfolio notifications.

Converts PortfolioResult into Slack Block Kit format for rich, readable messages.

Usage:
    from agents.notifications.slack_formatter import format_portfolio_completion

    message_blocks = format_portfolio_completion(portfolio_result, env="dev")
"""

from typing import Any, Dict, List

from agents.shared_contracts import PortfolioResult


def format_portfolio_completion(
    result: PortfolioResult, env: str = "dev"
) -> List[Dict[str, Any]]:
    """
    Format a PortfolioResult into Slack Block Kit blocks.

    Args:
        result: The portfolio result to format
        env: Environment name (dev/staging/prod)

    Returns:
        List of Slack Block Kit blocks ready to send via webhook/API.
    """
    blocks = []

    # Header section
    blocks.append(_make_header_block(result, env))
    blocks.append({"type": "divider"})

    # Summary section
    blocks.append(_make_summary_block(result))

    # Issue breakdown (if issues found)
    if result.total_issues_found > 0:
        blocks.append({"type": "divider"})
        blocks.append(_make_issue_breakdown_block(result))

    # Top repos section (if multiple repos)
    if len(result.repos) > 1:
        blocks.append({"type": "divider"})
        blocks.append(_make_top_repos_block(result))

    # Footer section
    blocks.append({"type": "divider"})
    blocks.append(_make_footer_block(result))

    return blocks


def _make_header_block(result: PortfolioResult, env: str) -> Dict[str, Any]:
    """Create the header block with emoji and title."""
    # Pick emoji based on results
    if result.total_repos_errored > 0:
        emoji = ":warning:"
    elif result.total_issues_found > 0:
        emoji = ":mag:"
    else:
        emoji = ":white_check_mark:"

    env_badge = _get_env_badge(env)

    return {
        "type": "section",
        "text": {
            "type": "mrkdwn",
            "text": (
                f"{emoji} *Portfolio SWE Audit Complete* {env_badge}\n"
                f"Run ID: `{result.portfolio_run_id[:8]}...`"
            ),
        },
    }


def _make_summary_block(result: PortfolioResult) -> Dict[str, Any]:
    """Create the summary metrics block."""
    fix_rate = (
        (result.total_issues_fixed / result.total_issues_found * 100)
        if result.total_issues_found > 0
        else 0.0
    )

    duration_str = _format_duration(result.portfolio_duration_seconds)

    summary_text = f"*Repos:* {result.total_repos_analyzed} analyzed"

    if result.total_repos_skipped > 0:
        summary_text += f", {result.total_repos_skipped} skipped"
    if result.total_repos_errored > 0:
        summary_text += f", {result.total_repos_errored} errored"

    summary_text += (
        f"\n*Issues:* {result.total_issues_found} found, "
        f"{result.total_issues_fixed} fixed ({fix_rate:.1f}%)"
        f"\n*Duration:* {duration_str}"
    )

    return {"type": "section", "text": {"type": "mrkdwn", "text": summary_text}}


def _make_issue_breakdown_block(result: PortfolioResult) -> Dict[str, Any]:
    """Create the issue breakdown block."""
    fields = []

    # By severity
    if result.issues_by_severity:
        severity_text = "\n".join(
            [
                f"{_severity_emoji(sev)} {sev.title()}: {count}"
                for sev, count in sorted(
                    result.issues_by_severity.items(),
                    key=lambda x: _severity_order(x[0]),
                    reverse=True,
                )
            ]
        )
        fields.append({"type": "mrkdwn", "text": f"*By Severity*\n{severity_text}"})

    # By type
    if result.issues_by_type:
        type_text = "\n".join(
            [
                f"• {issue_type.replace('_', ' ').title()}: {count}"
                for issue_type, count in sorted(
                    result.issues_by_type.items(), key=lambda x: x[1], reverse=True
                )[
                    :5
                ]  # Top 5 types
            ]
        )
        fields.append({"type": "mrkdwn", "text": f"*By Type*\n{type_text}"})

    return {"type": "section", "fields": fields}


def _make_top_repos_block(result: PortfolioResult) -> Dict[str, Any]:
    """Create the top repos block showing repos with most issues."""
    if not result.repos_by_issue_count:
        return {
            "type": "section",
            "text": {"type": "mrkdwn", "text": "*Top Repos*\nNo repos to display"},
        }

    # Show top 5 repos by issue count
    top_repos_text = "*Top Repos by Issues*\n"
    for i, (repo_id, issue_count) in enumerate(result.repos_by_issue_count[:5], 1):
        emoji = ":fire:" if i == 1 else f"{i}."
        top_repos_text += f"{emoji} `{repo_id}`: {issue_count} issues\n"

    return {"type": "section", "text": {"type": "mrkdwn", "text": top_repos_text}}


def _make_footer_block(result: PortfolioResult) -> Dict[str, Any]:
    """Create the footer block with timestamp and link."""
    timestamp_str = result.timestamp.strftime("%Y-%m-%d %H:%M:%S UTC")

    footer_text = (
        f"Completed at {timestamp_str} | "
        f"<https://github.com/jeremylongshore/bobs-brain|View Project>"
    )

    return {"type": "context", "elements": [{"type": "mrkdwn", "text": footer_text}]}


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================


def _get_env_badge(env: str) -> str:
    """Get a badge for the environment."""
    badges = {
        "dev": ":construction: DEV",
        "staging": ":test_tube: STAGING",
        "prod": ":rocket: PROD",
    }
    return badges.get(env, f"({env.upper()})")


def _severity_emoji(severity: str) -> str:
    """Get emoji for severity level."""
    emojis = {
        "critical": ":rotating_light:",
        "high": ":red_circle:",
        "medium": ":orange_circle:",
        "low": ":yellow_circle:",
        "info": ":information_source:",
    }
    return emojis.get(severity.lower(), ":grey_question:")


def _severity_order(severity: str) -> int:
    """Get numeric order for severity (for sorting)."""
    order = {"critical": 5, "high": 4, "medium": 3, "low": 2, "info": 1}
    return order.get(severity.lower(), 0)


def _format_duration(seconds: float) -> str:
    """Format duration in human-readable format."""
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f}m"
    else:
        hours = seconds / 3600
        return f"{hours:.1f}h"


# ============================================================================
# ALTERNATIVE FORMAT: SIMPLE TEXT
# ============================================================================


def format_portfolio_completion_simple(
    result: PortfolioResult, env: str = "dev"
) -> str:
    """
    Format a PortfolioResult as simple text (fallback for non-block webhooks).

    Args:
        result: The portfolio result to format
        env: Environment name (dev/staging/prod)

    Returns:
        Plain text string ready to send via simple webhook.
    """
    fix_rate = (
        (result.total_issues_fixed / result.total_issues_found * 100)
        if result.total_issues_found > 0
        else 0.0
    )

    duration_str = _format_duration(result.portfolio_duration_seconds)

    lines = [
        f"Portfolio SWE Audit Complete ({env.upper()})",
        f"Run ID: {result.portfolio_run_id[:8]}...",
        "",
        f"Repos: {result.total_repos_analyzed} analyzed",
    ]

    if result.total_repos_skipped > 0:
        lines.append(f"  - {result.total_repos_skipped} skipped")
    if result.total_repos_errored > 0:
        lines.append(f"  - {result.total_repos_errored} errored")

    lines.extend(
        [
            "",
            f"Issues: {result.total_issues_found} found, {result.total_issues_fixed} fixed ({fix_rate:.1f}%)",
            f"Duration: {duration_str}",
        ]
    )

    if result.repos_by_issue_count:
        lines.append("")
        lines.append("Top Repos:")
        for repo_id, issue_count in result.repos_by_issue_count[:3]:
            lines.append(f"  • {repo_id}: {issue_count} issues")

    return "\n".join(lines)


if __name__ == "__main__":
    # Quick test/demo
    import json
    from datetime import datetime

    # Create a sample PortfolioResult for testing
    sample_result = PortfolioResult(
        portfolio_run_id="test-12345678-abcd-efgh",
        repos=[],
        total_repos_analyzed=5,
        total_repos_skipped=1,
        total_repos_errored=0,
        total_issues_found=42,
        total_issues_fixed=30,
        issues_by_severity={
            "critical": 2,
            "high": 10,
            "medium": 20,
            "low": 8,
            "info": 2,
        },
        issues_by_type={
            "adk_violation": 15,
            "pattern_drift": 12,
            "security": 8,
            "tech_debt": 7,
        },
        repos_by_issue_count=[
            ("bobs-brain", 20),
            ("diagnosticpro", 12),
            ("pipelinepilot", 10),
        ],
        portfolio_duration_seconds=456.78,
        timestamp=datetime.now(),
    )

    # Test Block Kit format
    print("=== BLOCK KIT FORMAT ===")
    blocks = format_portfolio_completion(sample_result, env="dev")
    print(json.dumps(blocks, indent=2))

    print("\n=== SIMPLE TEXT FORMAT ===")
    simple_text = format_portfolio_completion_simple(sample_result, env="dev")
    print(simple_text)
