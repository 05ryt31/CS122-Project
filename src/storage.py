"""
Storage utilities for saving climate data to disk.

This module provides functions to:
- Save raw API responses as JSON files.
- Convert climate data into a flat table and save as CSV.

All paths default to the project's data/ directory (see config.py).
"""

import json
from pathlib import Path

import pandas as pd

from src.config import RAW_DATA_DIR, PROCESSED_DATA_DIR


def save_raw_json(data: dict, filename: str = "climate_raw.json") -> Path:
    """
    Save a raw API response dictionary to a JSON file.

    Parameters
    ----------
    data : dict
        The raw JSON response from the API.
    filename : str
        Name of the output file (saved inside data/raw/).

    Returns
    -------
    Path: The absolute path to the saved file.
    """
    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
    filepath = RAW_DATA_DIR / filename

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    return filepath


def build_dataframe(data: dict) -> pd.DataFrame:
    """
    Convert a NASA POWER JSON response into a flat DataFrame.

    The POWER API nests monthly values under
    ``data["properties"]["parameter"][PARAM_NAME]`` where each key is a
    year-month string like ``"200001"`` and each value is the measurement.

    This function unpacks that structure into a tidy table with columns:
    ``year``, ``month``, and one column per climate parameter.

    Parameters
    ----------
    data : dict
        The full JSON response from NASA POWER.

    Returns
    -------
    pd.DataFrame
        A DataFrame with one row per year-month observation.
    """
    params_dict = data["properties"]["parameter"]

    records: list[dict] = []
    # Use the first parameter's keys to iterate over all year-month entries
    first_param = next(iter(params_dict))
    for year_month, _ in params_dict[first_param].items():
        row = {
            "year": int(year_month[:4]),
            "month": int(year_month[4:]),
        }
        for param_name, monthly_values in params_dict.items():
            row[param_name] = monthly_values.get(year_month)
        records.append(row)

    df = pd.DataFrame(records)
    df = df.sort_values(["year", "month"]).reset_index(drop=True)
    return df


def save_csv(df: pd.DataFrame, filename: str = "climate_data.csv") -> Path:
    """
    Save a DataFrame to a CSV file in the processed data directory.

    Parameters
    ----------
    df : pd.DataFrame
        The data to save.
    filename : str
        Name of the output CSV file (saved inside data/processed/).

    Returns
    -------
    Path
        The absolute path to the saved file.
    """
    PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)
    filepath = PROCESSED_DATA_DIR / filename

    df.to_csv(filepath, index=False)
    return filepath
