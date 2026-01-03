"""
Nox configuration for Bob's Brain multi-version testing.

This file defines test sessions for running pytest across multiple Python versions,
linting, type checking, and MCP-specific tests. Follows Google Analytics MCP patterns.

Sessions:
- tests: Run pytest on Python 3.10, 3.11, 3.12, 3.13
- lint: Run ruff and black checks
- typecheck: Run mypy on agents/ and mcp/
- tests_mcp: Run MCP-specific tests
- tests_unit: Run unit tests only
- tests_integration: Run integration tests only
- tests_slack: Run Slack integration tests
- coverage: Generate test coverage report
- security: Run security checks (bandit, safety)

Usage:
    nox                    # Run default sessions (tests)
    nox -s tests           # Run tests on all Python versions
    nox -s tests-3.12      # Run tests on Python 3.12 only
    nox -s lint            # Run linting checks
    nox -s typecheck       # Run mypy type checking
    nox -s coverage        # Generate coverage report
    nox --list             # List all available sessions
"""

import nox

# Nox configuration
nox.options.sessions = ["tests"]
nox.options.reuse_existing_virtualenvs = True
nox.options.error_on_external_run = False

# Python versions to test (aligned with ADK requirements)
PYTHON_VERSIONS = ["3.10", "3.11", "3.12", "3.13"]
DEFAULT_PYTHON = "3.12"  # Bob's Brain currently uses Python 3.12


@nox.session(python=PYTHON_VERSIONS)
def tests(session):
    """
    Run pytest on all supported Python versions.

    Tests include:
    - Unit tests (tests/unit/)
    - Integration tests (tests/integration/)
    - Slack tests (tests/slack_*)
    - SWE pipeline tests

    Usage:
        nox -s tests           # All Python versions
        nox -s tests-3.12      # Python 3.12 only
    """
    session.log(f"Running tests on Python {session.python}")

    # Install dependencies
    session.install("-r", "requirements.txt")
    session.install("pytest>=7.4.0", "pytest-asyncio>=0.21.0", "pytest-cov>=4.1.0")

    # Run pytest with color output and verbose mode
    session.run(
        "pytest",
        "tests/",
        "-v",
        "--color=yes",
        "--tb=short",
        "--strict-markers",
        *session.posargs,  # Allow passing additional args
    )


@nox.session(python=DEFAULT_PYTHON)
def tests_unit(session):
    """
    Run unit tests only (tests/unit/).

    Fast-running tests for core functionality without external dependencies.

    Usage:
        nox -s tests_unit
    """
    session.log("Running unit tests")

    session.install("-r", "requirements.txt")
    session.install("pytest>=7.4.0", "pytest-asyncio>=0.21.0", "pytest-cov>=4.1.0")

    # Ignore test files with known import issues (stale tests)
    ignore_patterns = [
        "--ignore=tests/unit/test_slack_formatter.py",
        "--ignore=tests/unit/test_slack_sender.py",
        "--ignore=tests/unit/test_storage_writer.py",
        "--ignore=tests/unit/test_notifications_config.py",
        "--ignore=tests/unit/test_storage_config.py",
    ]

    session.run(
        "pytest",
        "tests/unit/",
        *ignore_patterns,
        "-v",
        "--color=yes",
        "--tb=short",
        *session.posargs,
    )


@nox.session(python=DEFAULT_PYTHON)
def tests_integration(session):
    """
    Run integration tests only (tests/integration/).

    Tests that interact with external services (Agent Engine, GCS, etc.).

    Usage:
        nox -s tests_integration
    """
    session.log("Running integration tests")

    session.install("-r", "requirements.txt")
    session.install("pytest>=7.4.0", "pytest-asyncio>=0.21.0", "pytest-cov>=4.1.0")

    session.run(
        "pytest",
        "tests/integration/",
        "-v",
        "--color=yes",
        "--tb=short",
        *session.posargs,
    )


@nox.session(python=DEFAULT_PYTHON)
def tests_slack(session):
    """
    Run Slack integration tests (tests/slack_*/).

    Tests for Slack webhook, gateway, and E2E flows.

    Usage:
        nox -s tests_slack
    """
    session.log("Running Slack integration tests")

    session.install("-r", "requirements.txt")
    session.install("pytest>=7.4.0", "pytest-asyncio>=0.21.0", "pytest-cov>=4.1.0")

    session.run(
        "pytest",
        "tests/slack_gateway/",
        "tests/slack_e2e/",
        "-v",
        "--color=yes",
        "--tb=short",
        *session.posargs,
    )


@nox.session(python=DEFAULT_PYTHON)
def tests_mcp(session):
    """
    Run MCP-specific tests (if/when MCP integration is added).

    Currently a placeholder for future MCP server testing.

    Usage:
        nox -s tests_mcp
    """
    session.log("Running MCP-specific tests")

    session.install("-r", "requirements.txt")
    session.install("pytest>=7.4.0", "pytest-asyncio>=0.21.0")

    # Check if mcp/ directory exists
    import os
    if os.path.exists("mcp/"):
        session.run(
            "pytest",
            "mcp/",
            "-v",
            "--color=yes",
            "--tb=short",
            *session.posargs,
        )
    else:
        session.log("No MCP tests found (mcp/ directory does not exist)")


@nox.session(python=DEFAULT_PYTHON)
def lint(session):
    """
    Run linting checks with ruff and black.

    Checks:
    - ruff: Fast Python linter (replaces flake8, isort, etc.)
    - black: Code formatting check

    Usage:
        nox -s lint
    """
    session.log("Running linting checks")

    session.install("ruff>=0.1.0", "black>=23.10.0")

    # Run ruff linter
    session.log("Running ruff linter...")
    session.run(
        "ruff",
        "check",
        "agents/",
        "service/",
        "scripts/",
        "tests/",
        "--select=E,F,W,C90,I,N,UP,YTT,S,BLE,B,A,COM,C4,DTZ,T10,EM,EXE,ISC,ICN,G,INP,PIE,T20,PYI,PT,Q,RSE,RET,SLF,SIM,TID,TCH,ARG,PTH,ERA,PD,PGH,PL,TRY,NPY,RUF",
        "--ignore=E501,S101,S603,S607",  # Ignore line length, assert usage, subprocess
        *session.posargs,
    )

    # Run black formatting check
    session.log("Running black formatting check...")
    session.run(
        "black",
        "--check",
        "--diff",
        "agents/",
        "service/",
        "scripts/",
        "tests/",
        *session.posargs,
    )


@nox.session(python=DEFAULT_PYTHON)
def format_code(session):
    """
    Auto-format code with black and ruff.

    Applies formatting changes in-place.

    Usage:
        nox -s format_code
    """
    session.log("Auto-formatting code")

    session.install("ruff>=0.1.0", "black>=23.10.0")

    # Run ruff auto-fixes
    session.log("Running ruff auto-fixes...")
    session.run(
        "ruff",
        "check",
        "agents/",
        "service/",
        "scripts/",
        "tests/",
        "--fix",
        *session.posargs,
    )

    # Run black formatting
    session.log("Running black formatting...")
    session.run(
        "black",
        "agents/",
        "service/",
        "scripts/",
        "tests/",
        *session.posargs,
    )


@nox.session(python=DEFAULT_PYTHON)
def typecheck(session):
    """
    Run mypy type checking on agents/ and service/.

    Checks static types for improved code quality and IDE support.

    Usage:
        nox -s typecheck
    """
    session.log("Running mypy type checking")

    session.install("-r", "requirements.txt")
    session.install("mypy>=1.6.0")

    # Run mypy on agents/ directory
    session.log("Type checking agents/...")
    session.run(
        "mypy",
        "agents/",
        "--ignore-missing-imports",
        "--no-strict-optional",
        "--warn-redundant-casts",
        "--warn-unused-ignores",
        "--no-implicit-reexport",
        *session.posargs,
    )

    # Run mypy on service/ directory
    session.log("Type checking service/...")
    session.run(
        "mypy",
        "service/",
        "--ignore-missing-imports",
        "--no-strict-optional",
        "--warn-redundant-casts",
        "--warn-unused-ignores",
        "--no-implicit-reexport",
        *session.posargs,
    )


@nox.session(python=DEFAULT_PYTHON)
def coverage(session):
    """
    Generate test coverage report with pytest-cov.

    Generates both terminal and HTML coverage reports.

    Usage:
        nox -s coverage
    """
    session.log("Generating test coverage report")

    session.install("-r", "requirements.txt")
    session.install("pytest>=7.4.0", "pytest-asyncio>=0.21.0", "pytest-cov>=4.1.0")

    session.run(
        "pytest",
        "tests/",
        "--cov=agents",
        "--cov=service",
        "--cov-report=term-missing",
        "--cov-report=html",
        "--cov-report=xml",
        "--cov-config=.coveragerc",
        "-v",
        *session.posargs,
    )

    session.log("Coverage report generated in htmlcov/index.html")


@nox.session(python=DEFAULT_PYTHON)
def security(session):
    """
    Run security checks with bandit and safety.

    Checks:
    - bandit: Security vulnerability scanner
    - safety: Dependency vulnerability scanner

    Usage:
        nox -s security
    """
    session.log("Running security checks")

    session.install("bandit>=1.7.5", "safety>=2.3.0")

    # Run bandit security scanner
    session.log("Running bandit security scanner...")
    session.run(
        "bandit",
        "-r",
        "agents/",
        "service/",
        "scripts/",
        "-ll",  # Only report medium/high severity
        "-i",  # Show confidence level
        *session.posargs,
    )

    # Run safety vulnerability scanner
    session.log("Running safety dependency scanner...")
    session.run(
        "safety",
        "check",
        "--json",
        *session.posargs,
    )


@nox.session(python=DEFAULT_PYTHON)
def docs(session):
    """
    Validate documentation structure and AgentCard JSON files.

    Checks:
    - AgentCard JSON validation (A2A protocol compliance)
    - Document filing system (NNN-CC-ABCD naming)

    Usage:
        nox -s docs
    """
    session.log("Validating documentation and AgentCards")

    session.install("-r", "requirements.txt")
    session.install("jsonschema>=4.0.0")

    # Run AgentCard validation
    session.log("Validating AgentCard JSON files...")
    session.run("python", "scripts/check_a2a_contracts.py", "--all", *session.posargs)


@nox.session(python=DEFAULT_PYTHON)
def arv(session):
    """
    Run Agent Readiness Verification (ARV) checks.

    Comprehensive checks for:
    - Hard Mode rules (R1-R8)
    - RAG readiness
    - Agent Engine configuration
    - Deployment readiness

    Usage:
        nox -s arv
    """
    session.log("Running Agent Readiness Verification (ARV)")

    session.install("-r", "requirements.txt")

    # Run ARV department checks
    session.log("Running ARV department checks...")
    session.run(
        "python",
        "scripts/run_arv_department.py",
        "--env", "dev",
        *session.posargs,
    )


@nox.session(python=DEFAULT_PYTHON)
def ci(session):
    """
    Run full CI suite (lint + typecheck + tests + security).

    This is the comprehensive check that runs in CI/CD pipelines.

    Usage:
        nox -s ci
    """
    session.log("Running full CI suite")

    # Run all CI checks sequentially
    session.notify("lint")
    session.notify("typecheck")
    session.notify("tests")
    session.notify("security")
    session.notify("docs")


@nox.session(python=DEFAULT_PYTHON)
def clean(session):
    """
    Clean up generated files and caches.

    Removes:
    - __pycache__ directories
    - .pytest_cache
    - .mypy_cache
    - coverage reports
    - .nox virtualenvs

    Usage:
        nox -s clean
    """
    session.log("Cleaning up generated files and caches")

    import shutil
    import pathlib

    patterns = [
        "**/__pycache__",
        "**/*.pyc",
        "**/*.pyo",
        ".pytest_cache",
        ".mypy_cache",
        "htmlcov",
        ".coverage",
        "coverage.xml",
        ".nox",
    ]

    for pattern in patterns:
        for path in pathlib.Path(".").glob(pattern):
            if path.is_file():
                session.log(f"Removing file: {path}")
                path.unlink()
            elif path.is_dir():
                session.log(f"Removing directory: {path}")
                shutil.rmtree(path)

    session.log("Cleanup complete")


@nox.session(python=PYTHON_VERSIONS)
def quick(session):
    """
    Quick smoke test on all Python versions (unit tests only).

    Fast feedback loop for rapid development.

    Usage:
        nox -s quick
        nox -s quick-3.12  # Python 3.12 only
    """
    session.log(f"Running quick smoke test on Python {session.python}")

    session.install("-r", "requirements.txt")
    session.install("pytest>=7.4.0", "pytest-asyncio>=0.21.0")

    # Ignore test files with known import issues (stale tests)
    ignore_patterns = [
        "--ignore=tests/unit/test_slack_formatter.py",
        "--ignore=tests/unit/test_slack_sender.py",
        "--ignore=tests/unit/test_storage_writer.py",
        "--ignore=tests/unit/test_notifications_config.py",
        "--ignore=tests/unit/test_storage_config.py",
    ]

    session.run(
        "pytest",
        "tests/unit/",
        *ignore_patterns,
        "-v",
        "--color=yes",
        "-x",  # Stop on first failure
        *session.posargs,
    )
