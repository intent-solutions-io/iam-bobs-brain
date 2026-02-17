#!/usr/bin/env python3
"""
Test suite for Bob v1 Basic
"""

import sys
from pathlib import Path

import pytest

# Add version directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "versions" / "v1-basic"))


def test_bob_import():
    """Test that Bob can be imported"""
    try:
        from bob_clean import BobBrain

        assert BobBrain is not None
    except ImportError:
        pytest.skip("Bob v1 not available")


def test_bob_initialization():
    """Test Bob initialization"""
    try:
        from bob_clean import BobBrain

        bob = BobBrain()
        assert bob is not None
        assert hasattr(bob, "chat")
        assert hasattr(bob, "home_dir")
    except ImportError:
        pytest.skip("Bob v1 not available")


def test_bob_commands():
    """Test Bob's command system"""
    try:
        from bob_clean import BobBrain

        bob = BobBrain()

        # Test status command
        response = bob.chat("status")
        assert response is not None
        assert len(response) > 0

        # Test memory command
        response = bob.chat("memory")
        assert response is not None

    except ImportError:
        pytest.skip("Bob v1 not available")


def test_bob_conversation():
    """Test basic conversation"""
    try:
        from bob_clean import BobBrain

        bob = BobBrain()

        response = bob.chat("Hello Bob!")
        assert response is not None
        assert len(response) > 0
        assert not response.startswith("Error")

    except ImportError:
        pytest.skip("Bob v1 not available")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
