"""
Thin adapter layer between the Tkinter GUI and the NASA POWER pipeline.

Mirrors src/data_adapter.py for sea level: wraps fetch + normalize so the
GUI only needs a single call to get a filtered pandas DataFrame.
"""

import pandas as pd

from src.api_client import fetch_climate_data
from src.sea_level_client import get_available_stations
from src.storage import build_dataframe, save_csv, slugify_station_name


def load_climate_data(
    station_name: str,
    start_year: int | None = None,
    end_year: int | None = None,
) -> pd.DataFrame:
    """Fetch, normalize, and optionally filter NASA POWER climate data.

    Climate data is location-based (lat/lon).  We reuse the STATIONS
    dictionary so the GUI can offer the same location dropdown across
    both datasets.

    Parameters
    ----------
    station_name : str
        A key from the STATIONS dictionary (e.g. "San Francisco, CA").
    start_year : int or None
        Lower year bound (inclusive).  None means use API default.
    end_year : int or None
        Upper year bound (inclusive).  None means use API default.

    Returns
    -------
    pd.DataFrame
        Columns: date, year, month, T2M, PRECTOTCORR, RH2M, PS,
        station_id, station_name.
    """
    stations = get_available_stations()

    if station_name not in stations:
        raise ValueError(f"Unknown station: {station_name}")

    station = stations[station_name]
    latitude = station["lat"]
    longitude = station["lon"]

    fetch_kwargs: dict = {"latitude": latitude, "longitude": longitude}
    if start_year is not None:
        fetch_kwargs["start_year"] = start_year
    if end_year is not None:
        fetch_kwargs["end_year"] = end_year

    raw_data = fetch_climate_data(**fetch_kwargs)
    df = build_dataframe(raw_data)

    # NASA POWER includes annual-mean rows encoded as month=13; drop them.
    df = df[df["month"].between(1, 12)].reset_index(drop=True)

    # NASA POWER occasionally returns -999 as a fill value for missing data.
    fill_cols = [c for c in df.columns if c not in ("year", "month")]
    for col in fill_cols:
        df[col] = df[col].where(df[col] != -999)

    df = df.assign(
        date=pd.to_datetime(
            df["year"].astype(str) + "-" + df["month"].astype(str).str.zfill(2) + "-01"
        ),
        station_id=station["id"],
        station_name=station_name,
    )

    if start_year is not None:
        df = df[df["year"] >= start_year]
    if end_year is not None:
        df = df[df["year"] <= end_year]

    column_order = [
        "date", "year", "month",
        "T2M", "PRECTOTCORR", "RH2M", "PS",
        "station_id", "station_name",
    ]
    available = [c for c in column_order if c in df.columns]
    df = df[available].reset_index(drop=True)

    slug = slugify_station_name(station_name)
    save_csv(df, filename=f"climate_{slug}_{station['id']}.csv")

    return df
