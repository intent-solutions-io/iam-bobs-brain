"""Get file contents tool."""

import logging
from pathlib import Path

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


async def execute(path: str) -> dict:
    """Get contents of a file."""
    if not path:
        return {"error": "Path is required"}

    if _is_denied_path(path):
        logger.warning(f"Denied path requested: {path}")
        return {"error": "Access denied - sensitive file"}

    file_path = Path(path)

    if not file_path.exists():
        return {"error": f"File not found: {path}"}

    if not file_path.is_file():
        return {"error": f"Not a file: {path}"}

    if file_path.suffix.lower() not in ALLOWED_EXTENSIONS:
        return {"error": f"File type not allowed: {file_path.suffix}"}

    file_size = file_path.stat().st_size
    if file_size > MAX_FILE_SIZE:
        return {"error": f"File too large: {file_size} bytes"}

    try:
        content = file_path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return {"error": "File is not valid UTF-8 text"}
    except Exception as e:
        return {"error": f"Failed to read file: {e}"}

    return {
        "path": str(file_path),
        "size": file_size,
        "lines": content.count("\n") + 1,
        "content": content
    }


def _is_denied_path(path: str) -> bool:
    """Check if path contains sensitive patterns."""
    path_lower = path.lower()
    for denied in DENIED_PATHS:
        if denied in path_lower:
            return True
    return False
