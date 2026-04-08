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

# ---------------------------------------------------------------------------
# NOAA CO-OPS Tides & Currents API configuration
#
# Provides monthly mean sea level measured by coastal tide gauge stations.
# This is station-level data (not satellite-derived global mean sea level).
# For global trends, data from multiple stations can be combined, or this
# source can be replaced with a satellite altimetry dataset later.
#
# Documentation: https://api.tidesandcurrents.noaa.gov/api/prod/
# No API key is required.
# ---------------------------------------------------------------------------
SEA_LEVEL_BASE_URL = (
    "https://api.tidesandcurrents.noaa.gov/api/prod/datagetter"
)

# Available tide gauge stations.  The Tkinter frontend will use this
# dictionary to populate a station selector.  Each key is a display-
# friendly label; the value holds the NOAA station ID and coordinates.
STATIONS = {
    "The Battery, NY": {"id": "8518750", "lat": 40.7006, "lon": -74.0142},
    "San Francisco, CA": {"id": "9414290", "lat": 37.8063, "lon": -122.4659},
    "Los Angeles, CA": {"id": "9410660", "lat": 33.7200, "lon": -118.2720},
    "Seattle, WA": {"id": "9447130", "lat": 47.6026, "lon": -122.3393},
    "Honolulu, HI": {"id": "1612340", "lat": 21.3067, "lon": -157.8670},
    "Key West, FL": {"id": "8724580", "lat": 24.5508, "lon": -81.8081},
    "Boston, MA": {"id": "8443970", "lat": 42.3539, "lon": -71.0503},
    "Miami Beach, FL": {"id": "8723170", "lat": 25.7682, "lon": -80.1320},
}

# Default station used when no station is selected
DEFAULT_STATION_ID = "8518750"
DEFAULT_STATION_NAME = "The Battery, NY"

# Date range for sea level data
SEA_LEVEL_START_DATE = "20000101"
SEA_LEVEL_END_DATE = "20241231"
