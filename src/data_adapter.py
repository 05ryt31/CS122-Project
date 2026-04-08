"""
Thin adapter layer between the Tkinter GUI and the backend data pipeline.

This module wraps the existing fetch + normalize functions so the GUI
only needs a single call to get a filtered pandas DataFrame.
"""

import pandas as pd

from src.data_normalizer import normalize_sea_level
from src.sea_level_client import fetch_sea_level_data, get_available_stations


def load_sea_level_data(
    station_name: str,
    start_year: int | None = None,
    end_year: int | None = None,
) -> pd.DataFrame:
    """Fetch, normalize, and optionally filter sea level data.

    Parameters
    ----------
    station_name : str
        A key from the STATIONS dictionary (e.g. "San Francisco, CA").
    start_year : int or None
        Keep only rows with year >= start_year.  None means no lower bound.
    end_year : int or None
        Keep only rows with year <= end_year.  None means no upper bound.

    Returns
    -------
    pd.DataFrame
        Columns: date, year, month, sea_level_m, highest_m, lowest_m,
        station_id, station_name.

    Raises
    ------
    ValueError
        If the station name is not recognized or the API returns an error.
    requests.ConnectionError
        If the NOAA server cannot be reached.
    requests.Timeout
        If the request exceeds the timeout.
    """
    stations = get_available_stations()

    if station_name not in stations:
        raise ValueError(f"Unknown station: {station_name}")

    station_id = stations[station_name]["id"]

    raw_data = fetch_sea_level_data(station_id=station_id)
    df = normalize_sea_level(raw_data)

    if start_year is not None:
        df = df[df["year"] >= start_year]
    if end_year is not None:
        df = df[df["year"] <= end_year]

    return df.reset_index(drop=True)
