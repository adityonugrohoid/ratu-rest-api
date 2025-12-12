"""
Tests for the config module.
"""

from rest_api import config


def test_binance_base_url():
    """Test that Binance base URL is defined."""
    assert hasattr(config, "BINANCE_BASE_URL")
    assert "binance.com" in config.BINANCE_BASE_URL


def test_request_timeout_positive():
    """Test that request timeout is positive."""
    assert config.REQUEST_TIMEOUT > 0


def test_snapshot_dir():
    """Test that snapshot directory is defined."""
    assert hasattr(config, "SNAPSHOT_DIR")
