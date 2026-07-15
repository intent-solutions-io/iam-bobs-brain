"""Security and execution tests for ARV checks."""

from pathlib import Path

from agents.arv.check_impl import run_check
from agents.arv.spec import ArvCheck


def _check(command: str) -> ArvCheck:
    return ArvCheck(
        id="test-command",
        description="Test command execution",
        category="tests",
        required=True,
        command=command,
    )


def test_run_check_executes_argument_vector() -> None:
    result = run_check(_check("python3 -c 'print(\"ready\")'"), "dev", verbose=True)

    assert result.passed is True
    assert result.exit_code == 0
    assert result.details == "ready\n"


def test_run_check_does_not_interpret_shell_operators(tmp_path: Path) -> None:
    marker = tmp_path / "shell-was-used"
    command = f"python3 -c 'print(\"safe\")' ; touch {marker}"

    result = run_check(_check(command), "dev")

    assert result.passed is True
    assert not marker.exists()


def test_run_check_rejects_empty_command() -> None:
    result = run_check(_check(""), "dev")

    assert result.passed is False
    assert result.exit_code == 1
    assert (
        result.details == "Error executing check: ARV check command must not be empty"
    )
