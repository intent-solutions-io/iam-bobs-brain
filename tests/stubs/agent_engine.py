"""
Stub Agent Engine client for testing without GCP credentials.

Replaces httpx calls to Vertex AI Agent Engine REST API with
deterministic in-memory responses.

Usage:
    from tests.stubs.agent_engine import StubAgentEngineClient

    client = StubAgentEngineClient()
    response = await client.query("Hello Bob")
    assert response["status"] == "SUCCESS"

    # Register custom responses
    client.register_response("compliance check", {
        "status": "SUCCESS",
        "result": {"compliance_status": "COMPLIANT"}
    })
"""

from typing import Any, Dict, List, Optional


class StubAgentEngineClient:
    """In-memory stub for Agent Engine REST API calls.

    Simulates the Agent Engine query endpoint without network I/O.

    Attributes:
        call_log: All calls made for test assertions.
        sessions: Simulated session state.
    """

    DEFAULT_RESPONSE = {
        "status": "SUCCESS",
        "result": {
            "message": "Stub Agent Engine response",
            "agent": "bob",
        },
    }

    def __init__(self):
        self._responses: Dict[str, Dict[str, Any]] = {}
        self._default = dict(self.DEFAULT_RESPONSE)
        self.call_log: List[Dict[str, Any]] = []
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self._call_count = 0

    def register_response(self, query_contains: str, response: Dict[str, Any]):
        """Register a canned response for queries containing the given string."""
        self._responses[query_contains] = response

    async def query(
        self,
        message: str,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Simulate Agent Engine query endpoint.

        Args:
            message: User message to send.
            session_id: Optional session ID for context.
            user_id: Optional user ID.

        Returns:
            Canned response dict matching Agent Engine REST API shape.
        """
        self._call_count += 1
        self.call_log.append({
            "call_number": self._call_count,
            "message": message,
            "session_id": session_id,
            "user_id": user_id,
        })

        # Track session
        if session_id:
            if session_id not in self.sessions:
                self.sessions[session_id] = {"messages": []}
            self.sessions[session_id]["messages"].append(message)

        # Match against registered responses
        for key, response in self._responses.items():
            if key in message.lower():
                return response

        return dict(self._default)

    async def create_session(self, user_id: str = "test-user") -> str:
        """Simulate session creation."""
        session_id = f"stub-session-{len(self.sessions) + 1}"
        self.sessions[session_id] = {"user_id": user_id, "messages": []}
        return session_id

    async def delete_session(self, session_id: str) -> bool:
        """Simulate session deletion."""
        if session_id in self.sessions:
            del self.sessions[session_id]
            return True
        return False

    @property
    def call_count(self) -> int:
        return self._call_count

    def reset(self):
        """Reset all state."""
        self.call_log.clear()
        self.sessions.clear()
        self._call_count = 0
        self._responses.clear()
