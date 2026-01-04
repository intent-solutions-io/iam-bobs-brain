"""Write file tool for file operations.

Provides file writing capabilities for Bob's MCP server:
- Write new files
- Append to existing files
- Create directories

Security:
- Restricted to allowed directories
- Denied paths (e.g., /etc, ~/.ssh)
- Size limits enforced

Phase H: Universal Tool Access
"""

import asyncio
import logging
import os
import sys
from pathlib import Path
from typing import Optional

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
MAX_FILE_SIZE = 1024 * 1024  # 1MB max file size
DENIED_PATHS = [
    "/etc",
    "/usr",
    "/bin",
    "/sbin",
    "/var",
    "/root",
    "/.ssh",
    "/.gnupg",
    "/.aws",
    "/.config",
]

# Allowed base directories (relative to repo root or absolute)
ALLOWED_BASES = [
    str(REPO_ROOT),
    "/tmp",
    os.path.expanduser("~/tmp"),
]


# ============================================================================
# OUTPUT MODEL
# ============================================================================


class WriteFileResult(ToolResult):
    """Structured output from write file tool."""

    path: Optional[str] = Field(default=None, description="Absolute file path")
    operation: str = Field(default="", description="Operation performed")
    bytes_written: int = Field(default=0, description="Bytes written")
    created: bool = Field(default=False, description="Whether file was created (vs updated)")


# ============================================================================
# SECURITY HELPERS
# ============================================================================


def _is_path_allowed(path: Path) -> tuple[bool, str]:
    """
    Check if a path is allowed for writing.

    Returns:
        Tuple of (allowed, reason)
    """
    path_str = str(path.resolve())

    # Check denied paths
    for denied in DENIED_PATHS:
        if path_str.startswith(denied) or denied in path_str:
            return False, f"Path contains denied directory: {denied}"

    # Check allowed bases
    for allowed in ALLOWED_BASES:
        if path_str.startswith(allowed):
            return True, "Path is within allowed directory"

    return False, f"Path not in allowed directories: {ALLOWED_BASES}"


# ============================================================================
# TOOL IMPLEMENTATION
# ============================================================================


async def execute(
    path: str,
    content: str,
    mode: str = "write",
    create_dirs: bool = True
) -> WriteFileResult:
    """
    Write content to a file.

    Args:
        path: File path to write to
        content: Content to write
        mode: Write mode ("write" = overwrite, "append" = append)
        create_dirs: Create parent directories if they don't exist

    Returns:
        WriteFileResult with operation details
    """
    if not path:
        return create_error_result(
            WriteFileResult, "write_file", "Path is required"
        )

    if not content:
        return create_error_result(
            WriteFileResult, "write_file", "Content is required"
        )

    # Check content size
    content_bytes = content.encode("utf-8")
    if len(content_bytes) > MAX_FILE_SIZE:
        return create_error_result(
            WriteFileResult, "write_file",
            f"Content exceeds maximum size ({len(content_bytes)} > {MAX_FILE_SIZE} bytes)"
        )

    # Resolve path
    file_path = Path(path)
    if not file_path.is_absolute():
        file_path = REPO_ROOT / file_path
    file_path = file_path.resolve()

    # Security check
    allowed, reason = _is_path_allowed(file_path)
    if not allowed:
        return create_error_result(
            WriteFileResult, "write_file", f"Access denied: {reason}"
        )

    logger.info(f"Writing file: {file_path} (mode={mode})")

    try:
        # Create parent directories if needed
        if create_dirs:
            file_path.parent.mkdir(parents=True, exist_ok=True)

        # Check if file exists
        file_existed = file_path.exists()

        # Write file
        if mode == "append":
            with open(file_path, "a", encoding="utf-8") as f:
                f.write(content)
        else:  # write (overwrite)
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)

        return create_success_result(
            WriteFileResult,
            "write_file",
            path=str(file_path),
            operation=mode,
            bytes_written=len(content_bytes),
            created=not file_existed,
        )

    except PermissionError:
        return create_error_result(
            WriteFileResult, "write_file",
            f"Permission denied: {file_path}"
        )
    except Exception as e:
        logger.error(f"Write file error: {e}")
        return create_error_result(
            WriteFileResult, "write_file", str(e)
        )


async def mkdir(path: str) -> WriteFileResult:
    """
    Create a directory.

    Args:
        path: Directory path to create

    Returns:
        WriteFileResult with operation details
    """
    if not path:
        return create_error_result(
            WriteFileResult, "mkdir", "Path is required"
        )

    # Resolve path
    dir_path = Path(path)
    if not dir_path.is_absolute():
        dir_path = REPO_ROOT / dir_path
    dir_path = dir_path.resolve()

    # Security check
    allowed, reason = _is_path_allowed(dir_path)
    if not allowed:
        return create_error_result(
            WriteFileResult, "mkdir", f"Access denied: {reason}"
        )

    logger.info(f"Creating directory: {dir_path}")

    try:
        dir_existed = dir_path.exists()
        dir_path.mkdir(parents=True, exist_ok=True)

        return create_success_result(
            WriteFileResult,
            "mkdir",
            path=str(dir_path),
            operation="mkdir",
            bytes_written=0,
            created=not dir_existed,
        )

    except PermissionError:
        return create_error_result(
            WriteFileResult, "mkdir",
            f"Permission denied: {dir_path}"
        )
    except Exception as e:
        logger.error(f"Mkdir error: {e}")
        return create_error_result(
            WriteFileResult, "mkdir", str(e)
        )
