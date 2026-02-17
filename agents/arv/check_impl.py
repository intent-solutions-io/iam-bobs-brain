"""
ARV Check Implementations

This module contains the execution logic for each ARV check.
Each function executes a check and returns an ArvResult.
"""

import os
import subprocess

from agents.arv.spec import ArvCheck, ArvResult, Environment


def is_feature_flag_enabled(flag_name: str) -> bool:
    """Check if a feature flag is enabled."""
    value = os.getenv(flag_name, "false").lower()
    return value in ("true", "1", "yes", "on")


def check_conditional_requirement(check: ArvCheck) -> tuple[bool, str]:
    """
    Check if a conditional requirement is met.

    Returns:
        (is_required, reason) tuple
    """
    if not check.required_when:
        return False, ""

    condition = check.required_when

    # RAG conditions
    if "LIVE_RAG_BOB_ENABLED=true" in condition and is_feature_flag_enabled(
        "LIVE_RAG_BOB_ENABLED"
    ):
        return True, "LIVE_RAG_BOB_ENABLED is enabled"

    if "LIVE_RAG_FOREMAN_ENABLED=true" in condition and is_feature_flag_enabled(
        "LIVE_RAG_FOREMAN_ENABLED"
    ):
        return True, "LIVE_RAG_FOREMAN_ENABLED is enabled"

    # Storage conditions
    if "ORG_STORAGE_WRITE_ENABLED=true" in condition and is_feature_flag_enabled(
        "ORG_STORAGE_WRITE_ENABLED"
    ):
        return True, "ORG_STORAGE_WRITE_ENABLED is enabled"

    # Slack conditions
    if "SLACK_NOTIFICATIONS_ENABLED=true" in condition and is_feature_flag_enabled(
        "SLACK_NOTIFICATIONS_ENABLED"
    ):
        return True, "SLACK_NOTIFICATIONS_ENABLED is enabled"

    # GitHub conditions
    if "GITHUB_ISSUE_CREATION_ENABLED=true" in condition and is_feature_flag_enabled(
        "GITHUB_ISSUE_CREATION_ENABLED"
    ):
        return True, "GITHUB_ISSUE_CREATION_ENABLED is enabled"

    # Not required by condition
    return False, ""


def run_check(check: ArvCheck, env: Environment, verbose: bool = False) -> ArvResult:
    """
    Execute an ARV check and return the result.

    Args:
        check: The check to execute
        env: Target environment
        verbose: Whether to include verbose output

    Returns:
        ArvResult with execution status
    """
    # Check if this is a conditional check
    if check.required_when:
        is_conditionally_required, reason = check_conditional_requirement(check)
        if not is_conditionally_required:
            # Skip this check - condition not met
            return ArvResult(
                check=check,
                passed=True,  # Passing by virtue of being skipped
                skipped=True,
                details=f"SKIPPED: {check.required_when}",
            )

    # Execute the check command
    try:
        # Set environment variables
        check_env = os.environ.copy()
        check_env["DEPLOYMENT_ENV"] = env

        # Run the command
        result = subprocess.run(
            check.command,
            check=False, shell=True,
            capture_output=True,
            text=True,
            timeout=300,  # 5 minute timeout
            env=check_env,
        )

        # Determine if passed
        passed = result.returncode == 0

        # Build details
        details = None
        if not passed:
            # Include stdout and stderr for failures
            details = f"Exit code: {result.returncode}"
            if result.stdout:
                details += f"\nStdout:\n{result.stdout[:500]}"  # Limit output
            if result.stderr:
                details += f"\nStderr:\n{result.stderr[:500]}"
        elif verbose and result.stdout:
            # Include output for verbose mode
            details = result.stdout[:500]

        return ArvResult(
            check=check,
            passed=passed,
            skipped=False,
            details=details,
            exit_code=result.returncode,
        )

    except subprocess.TimeoutExpired:
        return ArvResult(
            check=check,
            passed=False,
            skipped=False,
            details="Check timed out after 5 minutes",
            exit_code=124,  # Standard timeout exit code
        )

    except Exception as e:
        return ArvResult(
            check=check,
            passed=False,
            skipped=False,
            details=f"Error executing check: {e!s}",
            exit_code=1,
        )


def run_all_checks(
    checks: list[ArvCheck],
    env: Environment,
    verbose: bool = False,
) -> list[ArvResult]:
    """
    Run multiple checks and collect results.

    Args:
        checks: List of checks to execute
        env: Target environment
        verbose: Whether to include verbose output

    Returns:
        List of ArvResult objects
    """
    results = []
    for check in checks:
        result = run_check(check, env, verbose)
        results.append(result)
    return results
