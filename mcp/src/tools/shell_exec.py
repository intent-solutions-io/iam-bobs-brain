"""Shell execution tool for running commands.

Provides command execution capabilities for Bob's MCP server:
- Run shell commands
- Capture stdout/stderr
- Timeout handling

Security:
- Command allowlist enforcement
- Timeout limits
- Working directory restrictions

Phase H: Universal Tool Access
"""

import asyncio
import logging
import os
import shlex
import sys
from pathlib import Path
from typing import List, Optional

# Add agents/ to Python path for imports
REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from agents.shared_contracts.tool_outputs import (
    ToolResult,
    create_success_result,
    create_error_result,
)
from pydantic import Field

logger = logging.getLogger(__name__)

# Security configuration
DEFAULT_TIMEOUT = 60  # seconds
MAX_TIMEOUT = 300  # 5 minutes max
MAX_OUTPUT_SIZE = 100 * 1024  # 100KB max output

# Allowed commands (base command only, not full path)
ALLOWED_COMMANDS = {
    # Development tools
    "python", "python3", "pip", "pip3",
    "node", "npm", "npx", "yarn",
    "go", "cargo", "rustc",
    # Testing
    "pytest", "jest", "mocha",
    # Git
    "git",
    # Build tools
    "make", "cmake",
    # File operations
    "ls", "cat", "head", "tail", "wc", "find", "grep", "rg",
    "mkdir", "touch", "cp", "mv",
    # Utilities
    "echo", "date", "pwd", "env", "which",
    # Terraform
    "terraform",
    # GCP
    "gcloud", "gsutil", "bq",
    # Docker
    "docker", "docker-compose",
}

# Denied commands (never allow)
DENIED_COMMANDS = {
    "rm", "rmdir",  # Destructive
    "sudo", "su",  # Privilege escalation
    "chmod", "chown",  # Permission changes
    "kill", "killall", "pkill",  # Process termination
    "shutdown", "reboot", "halt",  # System control
    "curl", "wget",  # Network downloads (use web_search instead)
    "ssh", "scp", "sftp",  # Remote access
}


# ============================================================================
# OUTPUT MODEL
# ============================================================================


class ShellExecResult(ToolResult):
    """Structured output from shell execution tool."""

    command: str = Field(default="", description="Command that was executed")
    exit_code: int = Field(default=-1, description="Exit code")
    stdout: str = Field(default="", description="Standard output")
    stderr: str = Field(default="", description="Standard error")
    timed_out: bool = Field(default=False, description="Whether command timed out")
    truncated: bool = Field(default=False, description="Whether output was truncated")


# ============================================================================
# SECURITY HELPERS
# ============================================================================


def _is_command_allowed(command: str) -> tuple[bool, str]:
    """
    Check if a command is allowed.

    Args:
        command: Full command string

    Returns:
        Tuple of (allowed, reason)
    """
    # Parse command to get base command
    try:
        parts = shlex.split(command)
    except ValueError as e:
        return False, f"Invalid command syntax: {e}"

    if not parts:
        return False, "Empty command"

    base_cmd = os.path.basename(parts[0])

    # Check denied list first
    if base_cmd in DENIED_COMMANDS:
        return False, f"Command '{base_cmd}' is not allowed (security restriction)"

    # Check allowed list
    if base_cmd not in ALLOWED_COMMANDS:
        return False, f"Command '{base_cmd}' not in allowed list. Allowed: {sorted(ALLOWED_COMMANDS)}"

    return True, "Command is allowed"


def _truncate_output(output: str) -> tuple[str, bool]:
    """Truncate output if too large."""
    if len(output) > MAX_OUTPUT_SIZE:
        return output[:MAX_OUTPUT_SIZE] + "\n... (output truncated)", True
    return output, False


# ============================================================================
# TOOL IMPLEMENTATION
# ============================================================================


async def execute(
    command: str,
    cwd: Optional[str] = None,
    timeout: int = DEFAULT_TIMEOUT,
    env: Optional[dict] = None
) -> ShellExecResult:
    """
    Execute a shell command.

    Args:
        command: Command to execute
        cwd: Working directory (default: repo root)
        timeout: Timeout in seconds (default: 60, max: 300)
        env: Additional environment variables

    Returns:
        ShellExecResult with command output
    """
    if not command:
        return create_error_result(
            ShellExecResult, "shell_exec", "Command is required"
        )

    # Security check
    allowed, reason = _is_command_allowed(command)
    if not allowed:
        return create_error_result(
            ShellExecResult, "shell_exec", reason
        )

    # Validate timeout
    timeout = min(max(1, timeout), MAX_TIMEOUT)

    # Set working directory
    if cwd:
        work_dir = Path(cwd)
        if not work_dir.is_absolute():
            work_dir = REPO_ROOT / work_dir
    else:
        work_dir = REPO_ROOT

    if not work_dir.exists():
        return create_error_result(
            ShellExecResult, "shell_exec",
            f"Working directory does not exist: {work_dir}"
        )

    logger.info(f"Executing: {command} (cwd={work_dir}, timeout={timeout}s)")

    # Build environment
    cmd_env = os.environ.copy()
    if env:
        cmd_env.update(env)

    try:
        # Run command
        proc = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=str(work_dir),
            env=cmd_env,
        )

        try:
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(),
                timeout=timeout
            )
            timed_out = False
        except asyncio.TimeoutError:
            proc.kill()
            await proc.wait()
            stdout, stderr = b"", b"Command timed out"
            timed_out = True

        # Decode and truncate output
        stdout_str, stdout_trunc = _truncate_output(stdout.decode("utf-8", errors="replace"))
        stderr_str, stderr_trunc = _truncate_output(stderr.decode("utf-8", errors="replace"))

        return create_success_result(
            ShellExecResult,
            "shell_exec",
            command=command,
            exit_code=proc.returncode or 0,
            stdout=stdout_str,
            stderr=stderr_str,
            timed_out=timed_out,
            truncated=stdout_trunc or stderr_trunc,
        )

    except Exception as e:
        logger.error(f"Shell exec error: {e}")
        return create_error_result(
            ShellExecResult, "shell_exec", str(e)
        )
