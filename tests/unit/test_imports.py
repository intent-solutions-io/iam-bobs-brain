"""
Test ADK Imports - Hard Mode (R1)

Ensures all imports work correctly and prevent regression.
Tests align with Google Cloud user manual patterns.
"""

import pytest


def test_adk_agent_imports():
    """Test LlmAgent import from google.adk.agents (R1)"""
    from google.adk.agents import LlmAgent
    assert LlmAgent is not None


def test_adk_runner_import():
    """Test Runner import from google.adk top-level"""
    from google.adk import Runner
    assert Runner is not None


def test_adk_session_service_import():
    """Test VertexAiSessionService from google.adk.sessions (R5)"""
    from google.adk.sessions import VertexAiSessionService
    assert VertexAiSessionService is not None


def test_adk_memory_service_import():
    """Test VertexAiMemoryBankService from google.adk.memory (R5)"""
    from google.adk.memory import VertexAiMemoryBankService
    assert VertexAiMemoryBankService is not None


def test_a2a_agent_card_import():
    """Test AgentCard from a2a.types (R7)"""
    from a2a.types import AgentCard
    assert AgentCard is not None


def test_all_imports_together():
    """Test all imports can be loaded together"""
    from google.adk.agents import LlmAgent
    from google.adk import Runner
    from google.adk.sessions import VertexAiSessionService
    from google.adk.memory import VertexAiMemoryBankService
    from a2a.types import AgentCard

    assert all([
        LlmAgent is not None,
        Runner is not None,
        VertexAiSessionService is not None,
        VertexAiMemoryBankService is not None,
        AgentCard is not None
    ])


def test_no_alternative_frameworks():
    """Test that alternative frameworks are NOT imported (R1 enforcement)"""
    # These should fail to import
    prohibited_imports = [
        "langchain",
        "crewai",
        "autogen"
    ]

    for module in prohibited_imports:
        with pytest.raises(ImportError):
            __import__(module)
