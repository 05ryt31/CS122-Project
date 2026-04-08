"""
API client for fetching climate data from NASA POWER.

This module handles all HTTP communication with the NASA POWER API.
It returns raw JSON responses and raises clear errors on failure.

Current data source
-------------------
NASA POWER (Prediction Of Worldwide Energy Resources) provides monthly
climate parameters (temperature, precipitation, humidity, pressure) for
any location on Earth.  No API key is required.

To swap the data source later, create a new fetch function (or class)
that returns a similar dictionary structure, and update main.py to call
it instead.
"""

from typing import Optional

import requests

from src.config import (
    BASE_URL,
    COMMUNITY,
    DEFAULT_END_YEAR,
    DEFAULT_LATITUDE,
    DEFAULT_LONGITUDE,
    DEFAULT_PARAMETERS,
    DEFAULT_START_YEAR,
    REQUEST_TIMEOUT,
)


def fetch_climate_data(
    latitude: float = DEFAULT_LATITUDE,
    longitude: float = DEFAULT_LONGITUDE,
    start_year: int = DEFAULT_START_YEAR,
    end_year: int = DEFAULT_END_YEAR,
    parameters: Optional[list[str]] = None,
) -> dict:
    """
    Fetch monthly climate data from NASA POWER API.

    Parameters
    ----------
    latitude : float
        Latitude of the location (default: Los Angeles).
    longitude : float
        Longitude of the location (default: Los Angeles).
    start_year : int
        First year of data to retrieve.
    end_year : int
        Last year of data to retrieve.
    parameters : list[str] or None
        Climate variables to request.  Defaults to config.DEFAULT_PARAMETERS.

    Returns
    -------
    dict
        The full JSON response from the API.

    Raises
    ------
    requests.HTTPError
        If the API returns a non-2xx status code.
    requests.ConnectionError
        If the server cannot be reached.
    requests.Timeout
        If the request exceeds the timeout limit.
    """
    if parameters is None:
        parameters = DEFAULT_PARAMETERS

    query_params = {
        "parameters": ",".join(parameters),
        "community": COMMUNITY,
        "longitude": longitude,
        "latitude": latitude,
        "start": start_year,
        "end": end_year,
        "format": "JSON",
    }

    response = requests.get(BASE_URL, params=query_params, timeout=REQUEST_TIMEOUT)
    response.raise_for_status()

    return response.json()
