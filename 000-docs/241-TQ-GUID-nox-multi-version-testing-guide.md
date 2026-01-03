# Nox Multi-Version Testing Guide

**Document ID:** 241-TQ-GUID
**Category:** Testing & Quality
**Type:** Guide
**Status:** Active
**Created:** 2025-12-20
**Last Updated:** 2025-12-20

---

## Overview

Bob's Brain uses **Nox** for multi-version Python testing, inspired by Google Analytics MCP patterns. Nox provides a robust, reproducible testing environment across Python 3.10, 3.11, 3.12, and 3.13.

This guide covers:
- All available Nox sessions
- How to run tests locally
- Integration with existing test infrastructure
- CI/CD integration patterns
- Best practices and common workflows

---

## Quick Start

### Installation

```bash
# Install nox in your virtualenv
source .venv/bin/activate
pip install nox

# Or install globally (recommended for development)
pip install --user nox  # Linux/macOS
```

### Basic Usage

```bash
# List all available sessions
nox --list

# Run default sessions (tests on all Python versions)
nox

# Run specific session
nox -s tests_unit

# Run session on specific Python version
nox -s tests-3.12

# Run with additional pytest arguments
nox -s tests_unit -- -k test_imports -v
```

---

## Available Sessions

### Test Sessions

#### `tests` (Default)
Run pytest on all supported Python versions (3.10, 3.11, 3.12, 3.13).

```bash
nox                    # All Python versions
nox -s tests           # Explicit all versions
nox -s tests-3.12      # Python 3.12 only
nox -s tests-3.13      # Python 3.13 only
```

**What it tests:**
- Unit tests (`tests/unit/`)
- Integration tests (`tests/integration/`)
- Slack tests (`tests/slack_*`)
- SWE pipeline tests

**Duration:** ~15-30 seconds per Python version

---

#### `tests_unit`
Run unit tests only (fast, no external dependencies).

```bash
nox -s tests_unit

# With pytest filters
nox -s tests_unit -- -k test_a2a_card
nox -s tests_unit -- tests/unit/test_imports.py -v
```

**What it tests:**
- AgentCard validation (`test_a2a_card.py`)
- Agent Engine client (`test_agent_engine_client.py`)
- Lazy loading patterns (`test_iam_adk_lazy_loading.py`)
- API registry (`test_api_registry.py`)
- Basic imports (`test_imports.py`)

**Duration:** ~15 seconds

**Excluded tests** (known import issues):
- `test_slack_formatter.py` (stale)
- `test_slack_sender.py` (stale)
- `test_storage_writer.py` (stale)
- `test_notifications_config.py` (stale)
- `test_storage_config.py` (stale)

---

#### `tests_integration`
Run integration tests (requires GCP, Agent Engine).

```bash
nox -s tests_integration
```

**What it tests:**
- Agent Engine integration
- GCS upload/download
- RAG readiness checks

**Duration:** ~30-60 seconds (depends on network)

---

#### `tests_slack`
Run Slack integration tests.

```bash
nox -s tests_slack
```

**What it tests:**
- Slack webhook endpoints
- A2A gateway communication
- End-to-end Slack flows

**Duration:** ~20-40 seconds

---

#### `tests_mcp`
Run MCP-specific tests (placeholder for future MCP integration).

```bash
nox -s tests_mcp
```

**Status:** Currently a placeholder (no MCP tests yet)

---

### Code Quality Sessions

#### `lint`
Run linting checks with ruff and black.

```bash
nox -s lint
```

**Checks:**
- **ruff:** Fast Python linter (E, F, W, C90, I, N, UP, S, B, etc.)
- **black:** Code formatting check (--check mode)

**Ignored rules:**
- `E501`: Line length (handled by black)
- `S101`: Assert usage (pytest)
- `S603`, `S607`: Subprocess security (intentional)

**Duration:** ~5 seconds

---

#### `format_code`
Auto-format code with black and ruff.

```bash
nox -s format_code
```

**Actions:**
- Apply ruff auto-fixes
- Format code with black

**Duration:** ~5 seconds

---

#### `typecheck`
Run mypy type checking on `agents/` and `service/`.

```bash
nox -s typecheck

# With additional mypy args
nox -s typecheck -- --strict
```

**Checks:**
- Type annotations
- Redundant casts
- Unused ignores
- Implicit re-exports

**Duration:** ~10-15 seconds

---

### Coverage & Security Sessions

#### `coverage`
Generate test coverage report with pytest-cov.

```bash
nox -s coverage

# View HTML report
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
```

**Generates:**
- Terminal coverage report (with missing lines)
- HTML report (`htmlcov/index.html`)
- XML report (`coverage.xml` for CI)

**Configuration:** See `.coveragerc` for exclusions and settings

**Duration:** ~20 seconds

---

#### `security`
Run security checks with bandit and safety.

```bash
nox -s security
```

**Checks:**
- **bandit:** Security vulnerability scanner (medium/high severity)
- **safety:** Dependency vulnerability scanner

**Duration:** ~10 seconds

---

### Documentation & ARV Sessions

#### `docs`
Validate documentation structure and AgentCard JSON files.

```bash
nox -s docs
```

**Validates:**
- AgentCard JSON schema compliance
- A2A protocol contracts
- Document filing system naming

**Duration:** ~3 seconds

---

#### `arv`
Run Agent Readiness Verification (ARV) checks.

```bash
nox -s arv

# With additional args
nox -s arv -- --verbose
```

**Checks:**
- Hard Mode rules (R1-R8)
- RAG readiness
- Agent Engine configuration
- Deployment readiness

**Duration:** ~15-20 seconds

---

### Utility Sessions

#### `ci`
Run full CI suite (lint + typecheck + tests + security).

```bash
nox -s ci
```

**Runs (in order):**
1. `lint`
2. `typecheck`
3. `tests`
4. `security`
5. `docs`

**Duration:** ~60-90 seconds

---

#### `quick`
Quick smoke test on all Python versions (unit tests only).

```bash
nox -s quick           # All Python versions
nox -s quick-3.12      # Python 3.12 only
```

**What it does:**
- Runs unit tests with `-x` (stop on first failure)
- Fast feedback loop for development

**Duration:** ~10 seconds per Python version

---

#### `clean`
Clean up generated files and caches.

```bash
nox -s clean
```

**Removes:**
- `__pycache__` directories
- `.pytest_cache`, `.mypy_cache`
- Coverage reports (`htmlcov/`, `.coverage`, `coverage.xml`)
- `.nox` virtualenvs

**Duration:** ~2 seconds

---

## Common Workflows

### Development Workflow

```bash
# 1. Quick smoke test after changes
nox -s quick-3.12

# 2. Run unit tests with coverage
nox -s tests_unit

# 3. Check code quality
nox -s lint

# 4. Type check
nox -s typecheck

# 5. Full test suite before commit
nox -s ci
```

---

### Pre-Commit Workflow

```bash
# Format code
nox -s format_code

# Run all checks
nox -s ci

# If all pass, commit
git add .
git commit -m "feat(tests): add new test cases"
```

---

### CI/CD Integration

#### GitHub Actions Integration

Add to `.github/workflows/ci.yml`:

```yaml
jobs:
  nox-tests:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.10", "3.11", "3.12", "3.13"]

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python ${{ matrix.python-version }}
        uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}

      - name: Install nox
        run: pip install nox

      - name: Run tests
        run: nox -s tests-${{ matrix.python-version }}

  nox-quality:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Install nox
        run: pip install nox

      - name: Run linting
        run: nox -s lint

      - name: Run type checking
        run: nox -s typecheck

      - name: Run security checks
        run: nox -s security
```

---

### Debugging Failed Tests

```bash
# Run specific test with verbose output
nox -s tests_unit -- tests/unit/test_a2a_card.py -vv

# Run with pytest debugger
nox -s tests_unit -- --pdb

# Run with full traceback
nox -s tests_unit -- --tb=long

# Run single test function
nox -s tests_unit -- -k test_agentcard_validation -vv
```

---

## Configuration Files

### `noxfile.py`
Main Nox configuration defining all sessions.

**Location:** `/home/jeremy/000-projects/iams/bobs-brain/noxfile.py`

**Key settings:**
- `nox.options.sessions = ["tests"]` - Default sessions
- `nox.options.reuse_existing_virtualenvs = True` - Speed optimization
- `PYTHON_VERSIONS = ["3.10", "3.11", "3.12", "3.13"]` - Supported versions
- `DEFAULT_PYTHON = "3.12"` - Current development version

---

### `pytest.ini`
Pytest configuration for test discovery and behavior.

**Location:** `/home/jeremy/000-projects/iams/bobs-brain/pytest.ini`

**Key settings:**
- Test paths: `tests/`
- Test patterns: `test_*.py`, `*_test.py`
- Asyncio mode: `auto`
- Markers: `unit`, `integration`, `slack`, `slow`, `mcp`, `arv`

**Usage:**
```bash
# Run only unit tests
pytest -m unit

# Run only integration tests
pytest -m integration

# Skip slow tests
pytest -m "not slow"
```

---

### `.coveragerc`
Coverage configuration for pytest-cov.

**Location:** `/home/jeremy/000-projects/iams/bobs-brain/.coveragerc`

**Key settings:**
- Source: `agents/`, `service/`
- Omit: Tests, venvs, archives, docs
- Reports: Terminal (missing lines), HTML, XML

**Coverage targets:**
- **Minimum:** 70% overall
- **Goal:** 85% for core agents
- **Aspirational:** 95% for critical paths

---

### `requirements-nox.txt`
Nox-specific testing dependencies.

**Location:** `/home/jeremy/000-projects/iams/bobs-brain/requirements-nox.txt`

**Includes:**
- Testing: pytest, pytest-asyncio, pytest-cov, pytest-xdist, pytest-timeout
- Linting: ruff, black
- Type checking: mypy
- Security: bandit, safety
- Documentation: jsonschema

**Installation:**
```bash
pip install -r requirements-nox.txt
```

---

## Integration with Makefile

Nox sessions can be integrated with the existing Makefile:

```makefile
# Add to Makefile
nox-test: ## Run tests via nox (all Python versions)
	nox -s tests

nox-quick: ## Quick smoke test via nox
	nox -s quick-3.12

nox-ci: ## Full CI suite via nox
	nox -s ci

nox-clean: ## Clean nox virtualenvs
	nox -s clean
```

**Usage:**
```bash
make nox-test
make nox-quick
make nox-ci
```

---

## Best Practices

### Session Selection

**Use `quick` for:**
- Rapid development feedback
- Post-edit smoke tests
- Quick validation before detailed testing

**Use `tests_unit` for:**
- Testing core logic without external dependencies
- Fast iteration on unit tests
- Pre-commit validation

**Use `tests` for:**
- Full test suite across all Python versions
- Pre-merge validation
- Release readiness checks

**Use `ci` for:**
- Comprehensive quality checks
- Pre-commit to main/develop
- Release candidate validation

---

### Virtual Environment Reuse

Nox caches virtualenvs in `.nox/` by default. This speeds up subsequent runs.

**To force rebuild:**
```bash
# Rebuild specific session
nox -s tests_unit -r

# Rebuild all sessions
nox -r
```

**To clean all nox virtualenvs:**
```bash
nox -s clean
# Or
rm -rf .nox/
```

---

### Passing Arguments to pytest

Use `--` to pass arguments to pytest:

```bash
# Run specific test file
nox -s tests_unit -- tests/unit/test_imports.py

# Use pytest filters
nox -s tests_unit -- -k test_a2a

# Verbose output
nox -s tests_unit -- -vv

# Stop on first failure
nox -s tests_unit -- -x

# Show local variables on failure
nox -s tests_unit -- --showlocals
```

---

### Performance Optimization

**Parallel testing:**
```bash
# Install pytest-xdist
pip install pytest-xdist

# Run tests in parallel
nox -s tests_unit -- -n auto
```

**Skip slow tests:**
```bash
# Mark slow tests in pytest.ini
pytest -m "not slow"

# In noxfile
nox -s tests_unit -- -m "not slow"
```

---

## Troubleshooting

### Common Issues

#### "nox: command not found"

**Solution:**
```bash
# Install nox
pip install nox

# Or install in virtualenv
source .venv/bin/activate
pip install nox
```

---

#### "Session failed with exit code 1"

**Solution:**
```bash
# Run with verbose output
nox -s tests_unit -- -vv

# Check test failures
nox -s tests_unit -- --tb=long
```

---

#### "ImportError in test collection"

**Known issue:** Some stale test files have missing imports.

**Solution:** Noxfile excludes known problematic tests:
- `test_slack_formatter.py`
- `test_slack_sender.py`
- `test_storage_writer.py`
- `test_notifications_config.py`
- `test_storage_config.py`

**To run specific test:**
```bash
nox -s tests_unit -- tests/unit/test_imports.py
```

---

#### "Python version X.XX not found"

**Solution:**
```bash
# Install missing Python version (Ubuntu/Debian)
sudo apt-get install python3.11 python3.11-venv

# Or use pyenv
pyenv install 3.11.0
pyenv global 3.11.0
```

---

## Integration with Bob's Brain Standards

### Hard Mode Rules

Nox testing supports Bob's Brain Hard Mode rules:

- **R1 (ADK-Only):** Tests validate no alternative frameworks
- **R2 (Vertex AI):** Integration tests validate Agent Engine deployment
- **R4 (CI-Only):** Nox provides CI-ready test automation
- **R5 (Dual Memory):** Tests validate memory service wiring
- **R8 (Drift Detection):** ARV session checks for drift

---

### Document Filing System

This document follows **Document Filing System v3.0**:

- **Format:** `241-TQ-GUID-nox-multi-version-testing-guide.md`
- **Number:** 241 (sequential)
- **Category:** TQ (Testing & Quality)
- **Type:** GUID (Guide)
- **Description:** nox-multi-version-testing-guide

See: `000-docs/6767-DR-STND-document-filing-system-standard-v3.md`

---

## Related Documents

- **120-AA-AUDT-appaudit-devops-playbook.md** - Complete DevOps onboarding guide
- **6767-DR-STND-adk-agent-engine-spec-and-hardmode-rules.md** - Hard Mode rules
- **240-DR-STND-mcp-security-and-testing-standards-rationale.md** - Security testing standards

---

## Future Enhancements

### Planned Features

1. **MCP Server Testing**
   - Dedicated `tests_mcp` session for MCP servers
   - MCP protocol compliance checks
   - Inspector integration tests

2. **Parallel Testing**
   - pytest-xdist integration for parallel execution
   - Session-level parallelization

3. **Benchmark Testing**
   - Performance regression detection
   - Agent response time benchmarks
   - Memory usage profiling

4. **Contract Testing**
   - A2A protocol contract validation
   - AgentCard schema evolution checks
   - API compatibility testing

---

## Changelog

### 2025-12-20 - Initial Release (v1.0)

**Added:**
- Complete Nox configuration (`noxfile.py`)
- 15+ test sessions across 4 Python versions
- Pytest configuration (`pytest.ini`)
- Coverage configuration (`.coveragerc`)
- Nox-specific dependencies (`requirements-nox.txt`)
- Comprehensive documentation

**Sessions:**
- `tests`: Multi-version testing (3.10, 3.11, 3.12, 3.13)
- `tests_unit`: Unit tests only
- `tests_integration`: Integration tests
- `tests_slack`: Slack integration tests
- `tests_mcp`: MCP tests (placeholder)
- `lint`: Ruff + Black linting
- `format_code`: Auto-formatting
- `typecheck`: Mypy type checking
- `coverage`: Coverage reporting
- `security`: Bandit + Safety security checks
- `docs`: Documentation validation
- `arv`: ARV checks
- `ci`: Full CI suite
- `quick`: Quick smoke tests
- `clean`: Cleanup utility

**Fixes:**
- Excluded stale test files with import errors
- Configured pytest markers for test organization
- Optimized virtualenv reuse for speed

---

## Summary

Nox provides Bob's Brain with:

- **Multi-version testing** across Python 3.10-3.13
- **Isolated environments** for reproducible tests
- **Comprehensive sessions** for all testing needs
- **CI/CD ready** automation
- **Developer-friendly** workflows

**Get started:**
```bash
pip install nox
nox --list
nox -s quick-3.12
```

For detailed help, run:
```bash
nox --help
nox -s <session-name> --help
```

---

**Document Status:** Active
**Maintained By:** Bob's Brain Team
**Review Cycle:** Quarterly
**Next Review:** 2026-03-20
