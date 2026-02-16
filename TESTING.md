# Testing Guide

Quick reference for running tests in Bob's Brain.

## Test Pyramid

```
           /  E2E  \         tests/e2e/       (critical workflows, slow)
          / Smoke   \        tests/smoke/      (post-deploy health)
         / Contract  \       tests/ -m contract (schema validation)
        / Integration \      tests/integration/ (GCP, Agent Engine)
       /    Unit       \     tests/unit/        (fast, no deps)
```

## Quick Commands

```bash
# Full CI gate (lint + test) - run before every commit
make ci

# Unit tests only (fast, ~1s)
pytest tests/unit/ -v

# Single test file
pytest tests/unit/test_enterprise_controls.py -v

# Single test function
pytest tests/unit/test_enterprise_controls.py::test_function_name -vvs

# Pattern match
pytest -k "test_mandate" -v

# By marker
pytest -m unit -v
pytest -m integration -v
pytest -m e2e -v
pytest -m smoke -v
pytest -m contract -v

# Coverage report
pytest tests/ --cov=agents --cov=service --cov-report=term-missing

# Drift detection (R8 compliance)
bash scripts/ci/check_nodrift.sh
```

## Environment Toggles

Copy `.env.test` or set in shell:

| Variable | Values | Default (CI) | Purpose |
|---|---|---|---|
| `BOB_TEST_MODE` | `0` / `1` | `1` | Enable test mode (stub services) |
| `BOB_STUB_EXTERNAL` | `0` / `1` | `1` | Force stub all external HTTP |
| `BOB_LLM_MODE` | `stub` / `replay` / `real` | `stub` | LLM response mode |
| `OTEL_TRACES_EXPORTER` | `none` / `otlp` | `none` | OTel trace export |

## Nox Sessions

```bash
nox --list                  # Show all sessions
nox -s tests-3.12           # Tests on Python 3.12
nox -s tests_unit           # Unit tests only
nox -s tests_integration    # Integration tests
nox -s tests_e2e            # End-to-end tests
nox -s tests_smoke          # Smoke tests
nox -s tests_contract       # Contract/schema tests
nox -s coverage             # Coverage with HTML report
nox -s lint                 # Linting (ruff + black)
nox -s security             # Security checks (bandit + safety)
```

## Test Fixtures

Shared fixtures are in `tests/conftest.py` and `tests/fixtures/`:

```python
# Deterministic IDs
def test_something(deterministic_id):
    id1 = deterministic_id("mandate")  # "mandate-0001"
    id2 = deterministic_id("mandate")  # "mandate-0002"

# Controllable time
def test_expiration(fake_clock):
    clock = fake_clock("2025-06-15T10:00:00+00:00")
    clock.advance(hours=2)
    assert clock.now().hour == 12

# Object factories
def test_mandate(mandate_factory):
    mandate = mandate_factory(risk_tier="R2", max_iterations=5)

def test_task(a2a_task_factory):
    task = a2a_task_factory(specialist="iam_qa")

def test_result(a2a_result_factory):
    result = a2a_result_factory(status="SUCCESS", specialist="iam_qa")

def test_gate(gate_result_factory):
    result = gate_result_factory(allowed=False, reason="Budget exceeded")

# Stub providers (no external deps)
def test_with_llm(stub_llm):
    response = stub_llm.generate("check compliance")
    assert stub_llm.call_count == 1

async def test_engine(stub_agent_engine):
    response = await stub_agent_engine.query("hello bob")
    assert response["status"] == "SUCCESS"
```

## Markers

| Marker | Purpose | Speed | External Deps |
|---|---|---|---|
| `unit` | Core logic, no I/O | Fast (<1s) | None |
| `integration` | GCP/Agent Engine | Medium | GCP credentials |
| `contract` | Schema validation | Fast | None |
| `e2e` | Full workflows | Slow | May need services |
| `smoke` | Deploy health | Fast | Deployed endpoint |
| `slack` | Slack webhooks | Medium | Slack webhook URL |
| `arv` | Agent readiness | Medium | May need GCP |
| `slow` | Long-running | Slow | Varies |

## CI Pipeline Order

1. Drift detection (`check_nodrift.sh`) - blocks on R1/R3/R4 violations
2. Lint (flake8/black)
3. Unit tests
4. Integration tests (if GCP available)
5. Coverage threshold check (>= 60%)
6. ARV gates
