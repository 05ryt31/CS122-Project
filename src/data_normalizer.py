"""
Data normalizer for converting raw API responses into clean DataFrames.

Each normalize function takes a raw response dictionary from an API client
and returns a pandas DataFrame with standardized columns.  This makes it
easy for downstream analysis and visualization code to work with data from
different sources in a uniform way.
"""

from typing import Optional

import pandas as pd


def _safe_float(value: str) -> Optional[float]:
    """Convert a string to float, returning None for empty or invalid values."""
    if not value or value.strip() == "":
        return None
    return float(value)


def normalize_sea_level(raw_data: dict) -> pd.DataFrame:
    """Convert a NOAA CO-OPS monthly-mean response into a tidy DataFrame.

    The raw response nests rows under ``raw_data["data"]``, each containing
    ``year``, ``month``, ``MSL`` (mean sea level), and other tidal stats.
    This function extracts the key fields and builds a clean table.

    Parameters
    ----------
    raw_data : dict
        The full JSON response from ``fetch_sea_level_data()``.

    Returns
    -------
    pd.DataFrame
        Columns: ``date``, ``year``, ``month``, ``sea_level_m``,
        ``highest_m``, ``lowest_m``, ``station_id``, ``station_name``.
    """
    metadata = raw_data.get("metadata", {})
    station_id = metadata.get("id", "unknown")
    station_name = metadata.get("name", "unknown")

    records: list[dict] = []
    for entry in raw_data["data"]:
        year = int(entry["year"])
        month = int(entry["month"])
        records.append({
            "date": pd.Timestamp(year=year, month=month, day=1),
            "year": year,
            "month": month,
            "sea_level_m": _safe_float(entry["MSL"]),
            "highest_m": _safe_float(entry["highest"]),
            "lowest_m": _safe_float(entry["lowest"]),
            "station_id": station_id,
            "station_name": station_name,
        })

    df = pd.DataFrame(records).sort_values('date').reset_index(drop=True)

    return df
