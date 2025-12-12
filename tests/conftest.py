"""
Pytest configuration and shared fixtures.
"""

import pytest


@pytest.fixture
def sample_symbol():
    """Provide a sample trading symbol."""
    return "ETHUSDT"
