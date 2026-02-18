"""
Pytest configuration for unit tests.

Provides fixtures for optional dependency detection and test skipping.
"""

import pytest

# Check if google-adk is available
# Use broad except: ADK import chain can fail with ImportError,
# ModuleNotFoundError, or other errors depending on Python version
try:
    import google.adk  # noqa: F401

    HAS_ADK = True
except Exception:
    HAS_ADK = False

# Check if google-cloud-apihub is available (for API Registry)
try:
    from google.cloud import apihub_v1  # noqa: F401

    HAS_APIHUB = True
except Exception:
    HAS_APIHUB = False


# Markers for skipping tests based on optional dependencies
requires_adk = pytest.mark.skipif(not HAS_ADK, reason="Requires google-adk package")

requires_apihub = pytest.mark.skipif(
    not HAS_APIHUB, reason="Requires google-cloud-apihub package"
)


def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line(
        "markers", "requires_adk: mark test as requiring google-adk package"
    )
    config.addinivalue_line(
        "markers", "requires_apihub: mark test as requiring google-cloud-apihub package"
    )
