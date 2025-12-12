"""
Configuration module for REST API client.

Contains API settings and runtime constants.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# =============================================================================
# Binance API Configuration (Public endpoints - no auth required)
# =============================================================================

BINANCE_BASE_URL = "https://api.binance.com"

# =============================================================================
# Logging Configuration
# =============================================================================

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE = Path("logs/rest_api.log")

# =============================================================================
# Output Configuration
# =============================================================================

SNAPSHOT_DIR = Path("snapshots")

# =============================================================================
# Request Settings
# =============================================================================

REQUEST_TIMEOUT = 10  # seconds
