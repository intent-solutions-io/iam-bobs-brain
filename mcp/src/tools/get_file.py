"""Get file contents tool."""

import logging
import sys
from pathlib import Path

# Add agents/ to Python path for imports
REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from agents.shared_contracts.tool_outputs import (
    FileResult,
    create_success_result,
    create_error_result,
)

logger = logging.getLogger(__name__)

MAX_FILE_SIZE = 1024 * 1024  # 1MB

ALLOWED_EXTENSIONS = {
    ".py", ".md", ".txt", ".json", ".yaml", ".yml",
    ".toml", ".cfg", ".ini", ".sh", ".bash",
    ".tf", ".hcl", ".html", ".css", ".js"
}

DENIED_PATHS = {
    ".env", ".secrets", "credentials", "private_key",
    "id_rsa", "id_ed25519", ".pem", ".key"
}


async def execute(path: str) -> FileResult:
    """
    Get contents of a file.

    Args:
        path: File path to read

    Returns:
        FileResult with file contents, size, and metadata

    Security:
        - Only allowed file extensions (text/code files)
        - Denies sensitive files (.env, credentials, keys)
        - Max file size: 1MB
        - UTF-8 encoding required
    """
    if not path:
        return create_error_result(FileResult, "get_file", "Path is required")

    if _is_denied_path(path):
        logger.warning(f"Denied path requested: {path}")
        return create_error_result(
            FileResult, "get_file", "Access denied - sensitive file"
        )

    file_path = Path(path)

    if not file_path.exists():
        return create_error_result(
            FileResult, "get_file", f"File not found: {path}"
        )

    if not file_path.is_file():
        return create_error_result(FileResult, "get_file", f"Not a file: {path}")

    if file_path.suffix.lower() not in ALLOWED_EXTENSIONS:
        return create_error_result(
            FileResult, "get_file", f"File type not allowed: {file_path.suffix}"
        )

    file_size = file_path.stat().st_size
    if file_size > MAX_FILE_SIZE:
        return create_error_result(
            FileResult, "get_file", f"File too large: {file_size} bytes"
        )

    try:
        content = file_path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return create_error_result(
            FileResult, "get_file", "File is not valid UTF-8 text"
        )
    except Exception as e:
        return create_error_result(
            FileResult, "get_file", f"Failed to read file: {e}"
        )

    lines = content.count("\n") + 1

    return create_success_result(
        FileResult,
        "get_file",
        path=str(file_path),
        content=content,
        size=file_size,
        lines=lines,
        encoding="utf-8",
    )


def _is_denied_path(path: str) -> bool:
    """Check if path contains sensitive patterns."""
    path_lower = path.lower()
    for denied in DENIED_PATHS:
        if denied in path_lower:
            return True
    return False
