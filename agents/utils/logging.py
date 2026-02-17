"""
Structured Logging Helper for Bob's Brain

Provides standardized logging with correlation IDs, agent context,
and structured fields for observability.

Part of Phase RC2 observability improvements.
"""

import json
import logging
import sys
from datetime import datetime
from typing import Dict


class StructuredLogger:
    """
    Structured logger with correlation ID support.

    Provides JSON-ish structured logging with consistent field names
    for correlation IDs, agent names, and pipeline steps.
    """

    def __init__(self, name: str, level: int = logging.INFO, enable_json: bool = False):
        """
        Initialize structured logger.

        Args:
            name: Logger name (usually module name)
            level: Logging level (default: INFO)
            enable_json: Whether to output pure JSON (default: False - human-readable)
        """
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)
        self.enable_json = enable_json

        # Add console handler if not already added
        if not self.logger.handlers:
            handler = logging.StreamHandler(sys.stdout)
            handler.setLevel(level)

            if enable_json:
                # Pure JSON format
                formatter = logging.Formatter("%(message)s")
            else:
                # Human-readable with timestamp
                formatter = logging.Formatter(
                    "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                    datefmt="%Y-%m-%d %H:%M:%S",
                )

            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

    def _format_message(self, event: str, level: str, **fields) -> str:
        """
        Format log message with structured fields.

        Args:
            event: Event description
            level: Log level (INFO, ERROR, etc.)
            **fields: Additional structured fields

        Returns:
            Formatted log message (JSON or human-readable)
        """
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": level,
            "event": event,
            **fields,
        }

        if self.enable_json:
            # Pure JSON
            return json.dumps(log_entry)
        else:
            # Human-readable format
            msg_parts = [f"[{event}]"]

            # Add key fields first
            priority_keys = ["pipeline_run_id", "agent", "step", "repo_id"]
            for key in priority_keys:
                if key in fields:
                    msg_parts.append(f"{key}={fields[key]}")

            # Add remaining fields
            for key, value in fields.items():
                if key not in priority_keys:
                    msg_parts.append(f"{key}={value}")

            return " ".join(msg_parts)

    def log_info(self, event: str, **fields):
        """
        Log info-level event.

        Args:
            event: Event description
            **fields: Structured fields (pipeline_run_id, agent, step, etc.)

        Example:
            logger.log_info(
                "pipeline_started",
                pipeline_run_id="abc-123",
                agent="foreman",
                repo_id="bobs-brain"
            )
        """
        message = self._format_message(event, "INFO", **fields)
        self.logger.info(message)

    def log_error(self, event: str, **fields):
        """
        Log error-level event.

        Args:
            event: Event description
            **fields: Structured fields (error, pipeline_run_id, etc.)

        Example:
            logger.log_error(
                "pipeline_failed",
                pipeline_run_id="abc-123",
                agent="iam-adk",
                error="Failed to parse agent.py"
            )
        """
        message = self._format_message(event, "ERROR", **fields)
        self.logger.error(message)

    def log_warning(self, event: str, **fields):
        """
        Log warning-level event.

        Args:
            event: Event description
            **fields: Structured fields

        Example:
            logger.log_warning(
                "rate_limit_approaching",
                pipeline_run_id="abc-123",
                remaining=100,
                limit=5000
            )
        """
        message = self._format_message(event, "WARNING", **fields)
        self.logger.warning(message)

    def log_debug(self, event: str, **fields):
        """
        Log debug-level event.

        Args:
            event: Event description
            **fields: Structured fields
        """
        message = self._format_message(event, "DEBUG", **fields)
        self.logger.debug(message)


# Global logger instances (can be imported and used directly)
_loggers: Dict[str, StructuredLogger] = {}


def get_logger(
    name: str, level: int = logging.INFO, enable_json: bool = False
) -> StructuredLogger:
    """
    Get or create a structured logger.

    Args:
        name: Logger name (usually __name__)
        level: Logging level
        enable_json: Whether to output pure JSON

    Returns:
        StructuredLogger instance

    Example:
        from agents.utils.logging import get_logger

        logger = get_logger(__name__)
        logger.log_info(
            "task_completed",
            pipeline_run_id=run_id,
            agent="bob",
            duration_ms=1250
        )
    """
    if name not in _loggers:
        _loggers[name] = StructuredLogger(name, level, enable_json)
    return _loggers[name]


# Convenience functions for common logging patterns
def log_pipeline_start(pipeline_run_id: str, repo_id: str, task: str, env: str = "dev"):
    """
    Log pipeline start event.

    Args:
        pipeline_run_id: Unique ID for this pipeline run
        repo_id: Repository being processed
        task: Task description
        env: Environment (dev/staging/prod)
    """
    logger = get_logger("pipeline")
    logger.log_info(
        "pipeline_started",
        pipeline_run_id=pipeline_run_id,
        agent="foreman",
        repo_id=repo_id,
        task=task,
        env=env,
    )


def log_pipeline_complete(
    pipeline_run_id: str,
    repo_id: str,
    duration_seconds: float,
    issues_found: int,
    issues_fixed: int,
):
    """
    Log pipeline completion event.

    Args:
        pipeline_run_id: Unique ID for this pipeline run
        repo_id: Repository processed
        duration_seconds: Total duration
        issues_found: Number of issues found
        issues_fixed: Number of issues fixed
    """
    logger = get_logger("pipeline")
    logger.log_info(
        "pipeline_completed",
        pipeline_run_id=pipeline_run_id,
        agent="foreman",
        repo_id=repo_id,
        duration_seconds=duration_seconds,
        issues_found=issues_found,
        issues_fixed=issues_fixed,
    )


def log_agent_step(
    pipeline_run_id: str, agent: str, step: str, status: str, **extra_fields
):
    """
    Log agent step event.

    Args:
        pipeline_run_id: Unique ID for this pipeline run
        agent: Agent name (iam-adk, iam-issue, etc.)
        step: Step name (analysis, issue_creation, etc.)
        status: Status (started, completed, failed)
        **extra_fields: Additional fields
    """
    logger = get_logger(f"agent.{agent}")
    logger.log_info(
        f"step_{status}",
        pipeline_run_id=pipeline_run_id,
        agent=agent,
        step=step,
        **extra_fields,
    )


def log_github_operation(
    pipeline_run_id: str, operation: str, repo: str, status: str, **extra_fields
):
    """
    Log GitHub operation event.

    Args:
        pipeline_run_id: Unique ID for this pipeline run
        operation: Operation type (fetch_repo, create_issue, etc.)
        repo: Repository (owner/repo)
        status: Status (started, success, failed)
        **extra_fields: Additional fields (issue_number, etc.)
    """
    logger = get_logger("github")
    logger.log_info(
        f"github_{operation}_{status}",
        pipeline_run_id=pipeline_run_id,
        operation=operation,
        repo=repo,
        **extra_fields,
    )


# Example usage and testing
if __name__ == "__main__":
    print("📊 Structured Logging Demo")
    print("=" * 60)

    # Create logger
    logger = get_logger("demo", enable_json=False)

    # Log various events
    run_id = "test-run-123"

    logger.log_info(
        "demo_started", pipeline_run_id=run_id, agent="test", step="initialization"
    )

    logger.log_info(
        "processing_file",
        pipeline_run_id=run_id,
        agent="iam-adk",
        step="analysis",
        file_path="agents/bob/agent.py",
        lines=250,
    )

    logger.log_warning(
        "pattern_violation",
        pipeline_run_id=run_id,
        agent="iam-adk",
        violation="missing_memory_bank",
        severity="medium",
    )

    logger.log_error(
        "api_call_failed",
        pipeline_run_id=run_id,
        agent="github",
        operation="create_issue",
        error="Rate limit exceeded",
        retry_after=60,
    )

    logger.log_info(
        "demo_completed", pipeline_run_id=run_id, agent="test", duration_ms=1500
    )

    print("\n" + "=" * 60)
    print("Logging examples completed")
