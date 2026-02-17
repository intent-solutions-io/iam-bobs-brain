"""
Stub LLM provider for deterministic tests.

Reads BOB_LLM_MODE to decide behavior:
- "stub"   : Returns canned responses immediately (default in CI)
- "replay"  : Replays recorded responses from fixtures (future)
- "real"    : Passes through to live API (requires credentials)

Usage:
    from tests.stubs.llm import StubLLM

    llm = StubLLM()
    response = llm.generate("What is ADK?")
    assert response == "This is a stub LLM response."

    # Custom canned responses
    llm = StubLLM(responses={"compliance": "COMPLIANT"})
    response = llm.generate("compliance")
    assert response == "COMPLIANT"
"""

import os
from typing import Any, Dict, List, Optional

BOB_LLM_MODE = os.getenv("BOB_LLM_MODE", "stub")


class StubLLM:
    """Stub LLM that returns canned responses for testing.

    Attributes:
        mode: Current LLM mode (stub, replay, real).
        call_log: List of all calls made (for assertion in tests).
    """

    DEFAULT_RESPONSE = "This is a stub LLM response."

    def __init__(
        self,
        responses: Optional[Dict[str, str]] = None,
        default_response: Optional[str] = None,
        mode: Optional[str] = None,
    ):
        self.mode = mode or BOB_LLM_MODE
        self._responses = responses or {}
        self._default = default_response or self.DEFAULT_RESPONSE
        self.call_log: List[Dict[str, Any]] = []
        self._call_count = 0

    def generate(self, prompt: str, **kwargs) -> str:
        """Generate a stub response.

        If the prompt matches a key in self._responses, return that value.
        Otherwise return the default response.
        """
        self._call_count += 1
        self.call_log.append(
            {
                "call_number": self._call_count,
                "prompt": prompt,
                "kwargs": kwargs,
            }
        )

        # Check for exact match first
        if prompt in self._responses:
            return self._responses[prompt]

        # Check for substring match
        for key, response in self._responses.items():
            if key in prompt:
                return response

        return self._default

    async def agenerate(self, prompt: str, **kwargs) -> str:
        """Async version of generate (same behavior, no actual I/O)."""
        return self.generate(prompt, **kwargs)

    @property
    def call_count(self) -> int:
        """Number of calls made to this stub."""
        return self._call_count

    def reset(self):
        """Reset call log and counter."""
        self.call_log.clear()
        self._call_count = 0
