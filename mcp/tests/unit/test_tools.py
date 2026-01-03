"""Unit tests for MCP tools.

Updated to work with Pydantic structured outputs (Phase A).
"""

import pytest
from pathlib import Path
import tempfile
import os

# Add parent to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


class TestSearchCodebase:
    """Tests for search_codebase tool."""

    @pytest.mark.asyncio
    async def test_empty_query_returns_error(self):
        """Empty query should return error result."""
        from src.tools import search_codebase
        result = await search_codebase.execute(query="")
        # Now returns Pydantic model
        assert result.success is False
        assert result.error is not None
        assert "required" in result.error.lower() or "query" in result.error.lower()

    @pytest.mark.asyncio
    async def test_search_finds_pattern(self):
        """Should find matching patterns."""
        from src.tools import search_codebase

        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.py"
            test_file.write_text("def hello_world():\n    pass\n")

            result = await search_codebase.execute(
                query="hello_world", path=tmpdir, file_pattern="*.py"
            )
            # Now returns Pydantic model
            assert result.success is True
            assert result.match_count >= 1


class TestGetFile:
    """Tests for get_file tool."""

    @pytest.mark.asyncio
    async def test_empty_path_returns_error(self):
        """Empty path should return error result."""
        from src.tools import get_file
        result = await get_file.execute(path="")
        # Now returns Pydantic model
        assert result.success is False
        assert result.error is not None

    @pytest.mark.asyncio
    async def test_denies_sensitive_files(self):
        """Should deny access to sensitive files."""
        from src.tools import get_file
        result = await get_file.execute(path="/path/to/.env")
        # Now returns Pydantic model
        assert result.success is False
        assert result.error is not None
        assert "denied" in result.error.lower()


class TestCheckPatterns:
    """Tests for check_patterns tool."""

    @pytest.mark.asyncio
    async def test_detects_forbidden_imports(self):
        """Should detect forbidden imports like langchain."""
        from src.tools import check_patterns

        with tempfile.TemporaryDirectory() as tmpdir:
            bad_file = Path(tmpdir) / "bad.py"
            bad_file.write_text("from langchain import stuff\n")

            result = await check_patterns.execute(path=tmpdir, rules=["R1"])
            # Now returns Pydantic model - status field (not compliance_status)
            assert result.status == "VIOLATIONS_FOUND"
            assert len(result.violations) > 0

    @pytest.mark.asyncio
    async def test_passes_clean_code(self):
        """Should pass clean code."""
        from src.tools import check_patterns

        with tempfile.TemporaryDirectory() as tmpdir:
            good_file = Path(tmpdir) / "good.py"
            good_file.write_text("from google.adk import Agent\n")

            result = await check_patterns.execute(path=tmpdir, rules=["R1"])
            # Now returns Pydantic model - status field (not compliance_status)
            assert result.status == "COMPLIANT"
