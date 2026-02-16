"""
FakeClock - Controllable clock for deterministic time-dependent tests.

Usage:
    clock = FakeClock.from_iso("2025-06-15T10:00:00+00:00")
    assert clock.now().hour == 10

    clock.advance(hours=2, minutes=30)
    assert clock.now().hour == 12
    assert clock.now().minute == 30

    # Use as context manager to patch datetime.now()
    with clock.patch("agents.shared_contracts.pipeline_contracts"):
        mandate = Mandate(expires_at=clock.now())
        clock.advance(hours=1)
        assert mandate.is_expired()
"""

from datetime import datetime, timedelta, timezone
from unittest.mock import patch


class FakeClock:
    """A controllable clock that can be advanced manually."""

    def __init__(self, start: datetime):
        if start.tzinfo is None:
            start = start.replace(tzinfo=timezone.utc)
        self._current = start

    @classmethod
    def from_iso(cls, iso_string: str) -> "FakeClock":
        """Create a FakeClock from an ISO 8601 string."""
        dt = datetime.fromisoformat(iso_string.replace("Z", "+00:00"))
        return cls(dt)

    def now(self) -> datetime:
        """Get the current fake time."""
        return self._current

    def advance(self, **kwargs) -> datetime:
        """Advance the clock by the given timedelta kwargs.

        Args:
            **kwargs: Arguments passed to timedelta (hours, minutes, seconds, days, etc.)

        Returns:
            The new current time.
        """
        self._current += timedelta(**kwargs)
        return self._current

    def set(self, dt: datetime) -> None:
        """Set the clock to a specific time."""
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        self._current = dt

    def patch(self, module_path: str):
        """Return a context manager that patches datetime.now() in the given module.

        Args:
            module_path: Dotted module path (e.g., "agents.shared_contracts.pipeline_contracts")

        Returns:
            A unittest.mock.patch context manager.
        """
        clock = self

        class _FakeDatetime(datetime):
            @classmethod
            def now(cls, tz=None):
                return clock.now()

        return patch(f"{module_path}.datetime", _FakeDatetime)
