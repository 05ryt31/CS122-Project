"""
Configuration constants for NASA Climate Data Dashboard.

This module stores API endpoints, default parameters, and file paths
used throughout the data collection pipeline.
"""

from pathlib import Path

# ---------------------------------------------------------------------------
# Project paths (relative to project root)
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_DATA_DIR = PROJECT_ROOT / "data" / "processed"

# ---------------------------------------------------------------------------
# NASA POWER API configuration
#
# The POWER (Prediction Of Worldwide Energy Resources) API provides
# climate data such as temperature, precipitation, and humidity.
# Documentation: https://power.larc.nasa.gov/docs/
# No API key is required for NASA POWER.
# ---------------------------------------------------------------------------
BASE_URL = "https://power.larc.nasa.gov/api/temporal/monthly/point"

# Climate parameters to request.
# T2M          – Temperature at 2 meters (°C)
# PRECTOTCORR  – Precipitation corrected (mm/day)
# RH2M         – Relative humidity at 2 meters (%)
# PS           – Surface pressure (kPa)
DEFAULT_PARAMETERS = ["T2M", "PRECTOTCORR", "RH2M", "PS"]

# Default location: Los Angeles, CA
DEFAULT_LATITUDE = 34.05
DEFAULT_LONGITUDE = -118.24

# Date range (years)
DEFAULT_START_YEAR = 2000
DEFAULT_END_YEAR = 2024

# Community type for the POWER API request
# "RE" = Renewable Energy, "SB" = Sustainable Buildings, "AG" = Agroclimatology
COMMUNITY = "RE"

# Request timeout in seconds
REQUEST_TIMEOUT = 30
