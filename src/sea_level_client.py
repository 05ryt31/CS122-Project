"""
Sea level data client using the NOAA CO-OPS Tides & Currents API.

This module fetches monthly mean sea level measurements from NOAA's
network of coastal tide gauge stations.  The data comes from verified
observations and includes several tidal statistics per month.

Data source
-----------
NOAA Center for Operational Oceanographic Products and Services (CO-OPS).
https://api.tidesandcurrents.noaa.gov/api/prod/

This is **station-level** sea level data, not satellite-derived global
mean sea level.  To swap for a global dataset (e.g., NASA PODAAC
satellite altimetry), replace or extend the fetch function and update
the normalizer accordingly.

No API key is required.
"""

from typing import Optional

import requests

from src.config import (
    DEFAULT_STATION_ID,
    REQUEST_TIMEOUT,
    SEA_LEVEL_BASE_URL,
    SEA_LEVEL_END_DATE,
    SEA_LEVEL_START_DATE,
    STATIONS,
)


def get_available_stations() -> dict[str, dict]:
    """Return the dictionary of available tide gauge stations.

    The Tkinter frontend can call this to populate a station selector.
    Each key is a human-readable station name; the value contains
    ``id``, ``lat``, and ``lon``.

    Returns
    -------
    dict[str, dict]
        e.g. ``{"The Battery, NY": {"id": "8518750", "lat": 40.70, "lon": -74.01}, ...}``
    """
    return STATIONS


def fetch_sea_level_data(
    station_id: str = DEFAULT_STATION_ID,
    begin_date: str = SEA_LEVEL_START_DATE,
    end_date: str = SEA_LEVEL_END_DATE,
    datum: str = "STND",
    units: str = "metric",
) -> dict:
    """Fetch monthly mean sea level from NOAA CO-OPS.

    Parameters
    ----------
    station_id : str
        NOAA station identifier (default: The Battery, NY).
    begin_date : str
        Start date in YYYYMMDD format.
    end_date : str
        End date in YYYYMMDD format.
    datum : str
        Vertical datum for measurements (default: STND = station datum).
    units : str
        "metric" (meters) or "english" (feet).

    Returns
    -------
    dict
        The full JSON response including ``metadata`` and ``data`` keys.

    Raises
    ------
    requests.HTTPError
        If the API returns a non-2xx status code.
    requests.ConnectionError
        If the server cannot be reached.
    requests.Timeout
        If the request exceeds the timeout limit.
    ValueError
        If the API returns an error message instead of data.
    """
    query_params = {
        "station": station_id,
        "begin_date": begin_date,
        "end_date": end_date,
        "product": "monthly_mean",
        "datum": datum,
        "units": units,
        "time_zone": "gmt",
        "format": "json",
        "application": "CS122_NASAClimateDashboard",
    }

    response = requests.get(
        SEA_LEVEL_BASE_URL, params=query_params, timeout=REQUEST_TIMEOUT
    )
    response.raise_for_status()

    payload = response.json()

    # The NOAA API returns {"error": {"message": "..."}} on bad requests
    # instead of using HTTP status codes.
    if "error" in payload:
        raise ValueError(
            f"NOAA API error: {payload['error'].get('message', payload['error'])}"
        )

    return payload
