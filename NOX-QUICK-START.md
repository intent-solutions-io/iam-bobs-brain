# Nox Quick Start

**Bob's Brain Multi-Version Testing**

## TL;DR

```bash
# Install
pip install nox

# List sessions
nox --list

# Quick test (Python 3.12)
nox -s quick-3.12

# Full unit tests
nox -s tests_unit

# All Python versions
nox -s tests

# Code quality
nox -s lint

# Full CI suite
nox -s ci
```

---

## Most Used Sessions

### Development

```bash
# Quick smoke test (10 seconds)
nox -s quick-3.12

# Unit tests (15 seconds)
nox -s tests_unit

# Format code
nox -s format_code

# Lint check
nox -s lint
```

### Pre-Commit

```bash
# Full CI suite (60 seconds)
nox -s ci

# Or individually
nox -s lint
nox -s typecheck
nox -s tests_unit
nox -s security
```

### Debugging

```bash
# Specific test file
nox -s tests_unit -- tests/unit/test_imports.py -v

# Single test function
nox -s tests_unit -- -k test_agentcard_validation -vv

# With debugger
nox -s tests_unit -- --pdb
```

---

## Available Sessions

| Session | Purpose | Duration |
|---------|---------|----------|
| `tests` | All Python versions (3.10-3.13) | ~60s |
| `tests_unit` | Unit tests only | ~15s |
| `tests_integration` | Integration tests | ~30s |
| `tests_slack` | Slack integration tests | ~20s |
| `lint` | Ruff + Black linting | ~5s |
| `typecheck` | Mypy type checking | ~10s |
| `coverage` | Coverage report | ~20s |
| `security` | Bandit + Safety checks | ~10s |
| `arv` | ARV (Agent Readiness Verification) | ~15s |
| `ci` | Full CI suite | ~60s |
| `quick-3.12` | Quick smoke test | ~10s |
| `clean` | Cleanup caches | ~2s |

---

## Passing Arguments to pytest

Use `--` to separate nox args from pytest args:

```bash
# Run specific test
nox -s tests_unit -- tests/unit/test_imports.py

# Use pytest filter
nox -s tests_unit -- -k test_a2a

# Verbose output
nox -s tests_unit -- -vv

# Stop on first failure
nox -s tests_unit -- -x
```

---

## Common Workflows

### Quick Development Loop

```bash
# 1. Make changes to code

# 2. Quick smoke test
nox -s quick-3.12

# 3. If passes, run full unit tests
nox -s tests_unit

# 4. Format code
nox -s format_code

# 5. Commit
git commit -am "feat: add new feature"
```

### Pre-Commit Workflow

```bash
# 1. Format code
nox -s format_code

# 2. Run all checks
nox -s ci

# 3. If all pass, commit
git add .
git commit -m "feat: add comprehensive tests"
```

### Debugging Test Failures

```bash
# 1. Run with verbose output
nox -s tests_unit -- -vv

# 2. Run specific failing test
nox -s tests_unit -- tests/unit/test_a2a_card.py -vv

# 3. Run with full traceback
nox -s tests_unit -- --tb=long

# 4. Use pytest debugger
nox -s tests_unit -- --pdb
```

---

## Configuration Files

- **`noxfile.py`** - Nox session definitions
- **`pytest.ini`** - Pytest configuration
- **`.coveragerc`** - Coverage settings
- **`requirements-nox.txt`** - Nox dependencies

---

## Troubleshooting

### "nox: command not found"

```bash
pip install nox
```

### "Session failed with exit code 1"

```bash
# Run with verbose output
nox -s tests_unit -- -vv
```

### "Python X.XX not found"

```bash
# Install missing Python version (Ubuntu)
sudo apt-get install python3.11 python3.11-venv
```

---

## Integration with Makefile

You can also use the Makefile for common operations:

```bash
make test              # Existing pytest
make lint              # Existing lint
make coverage          # Existing coverage

# Or use nox directly for multi-version testing
nox -s tests           # Test on all Python versions
```

---

## Documentation

For detailed documentation, see:

**`000-docs/241-TQ-GUID-nox-multi-version-testing-guide.md`**

Includes:
- Complete session reference
- CI/CD integration patterns
- Best practices
- Troubleshooting guide
- Configuration details

---

## Summary

**Nox provides:**
- Multi-version testing (Python 3.10-3.13)
- Isolated environments (no dependency conflicts)
- Fast feedback (virtualenv reuse)
- CI-ready automation

**Get started:**
```bash
nox --list
nox -s quick-3.12
```

**For help:**
```bash
nox --help
nox -s <session-name> --help
```
