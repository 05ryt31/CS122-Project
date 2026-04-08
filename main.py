"""
NASA Climate Data Dashboard – Data Collection Entry Point

This script runs the full data collection pipeline for all sources:

1. NASA POWER – monthly climate data (temperature, precipitation, etc.)
2. NOAA CO-OPS – monthly mean sea level from tide gauge stations

For each source the pipeline:
  a. Fetches data from the API.
  b. Saves the raw JSON response to data/raw/.
  c. Converts data to a tabular CSV and saves to data/processed/.
  d. Prints a short summary.

Usage
-----
    python main.py

No API keys are required.  An internet connection is needed.
"""

import requests

from src.api_client import fetch_climate_data
from src.data_normalizer import normalize_sea_level
from src.sea_level_client import fetch_sea_level_data, get_available_stations
from src.storage import build_dataframe, save_csv, save_raw_json


def collect_climate_data() -> None:
    """Fetch and store NASA POWER climate data."""
    print("=" * 50)
    print("[1/2] NASA POWER – Climate Data")
    print("=" * 50)
    print("Fetching climate data from NASA POWER API...")

    try:
        raw_data = fetch_climate_data()
    except requests.ConnectionError:
        print("Error: Could not connect to the NASA POWER API.")
        print("Check your internet connection and try again.")
        return
    except requests.Timeout:
        print("Error: The request timed out. Try again later.")
        return
    except requests.HTTPError as e:
        print(f"Error: API returned status {e.response.status_code}.")
        return

    json_path = save_raw_json(raw_data, filename="climate_raw.json")
    print(f"Raw JSON saved to: {json_path}")

    df = build_dataframe(raw_data)
    csv_path = save_csv(df, filename="climate_data.csv")
    print(f"CSV saved to:      {csv_path}")

    print(f"\nRows:    {len(df)}")
    print(f"Columns: {list(df.columns)}")
    print(f"Years:   {df['year'].min()} – {df['year'].max()}")
    print("\nFirst 5 rows:")
    print(df.head().to_string(index=False))


def collect_sea_level_data(station_name: str | None = None) -> None:
    """Fetch and store NOAA CO-OPS sea level data for a given station.

    Parameters
    ----------
    station_name : str or None
        A key from ``STATIONS`` in config.py (e.g. "San Francisco, CA").
        When None, the default station is used.
    """
    stations = get_available_stations()

    # Look up station ID from the name; fall back to default
    if station_name and station_name in stations:
        station_id = stations[station_name]["id"]
    else:
        station_name = None
        station_id = None  # fetch_sea_level_data will use its default

    print("=" * 50)
    print("[2/2] NOAA CO-OPS – Sea Level Data")
    print("=" * 50)
    display = station_name or "default"
    print(f"Fetching sea level data for station: {display}")

    try:
        kwargs: dict = {}
        if station_id:
            kwargs["station_id"] = station_id
        raw_data = fetch_sea_level_data(**kwargs)
    except requests.ConnectionError:
        print("Error: Could not connect to the NOAA CO-OPS API.")
        print("Check your internet connection and try again.")
        return
    except requests.Timeout:
        print("Error: The request timed out. Try again later.")
        return
    except requests.HTTPError as e:
        print(f"Error: API returned status {e.response.status_code}.")
        return
    except ValueError as e:
        print(f"Error: {e}")
        return

    json_path = save_raw_json(raw_data, filename="sea_level_raw.json")
    print(f"Raw JSON saved to: {json_path}")

    df = normalize_sea_level(raw_data)
    csv_path = save_csv(df, filename="sea_level_data.csv")
    print(f"CSV saved to:      {csv_path}")

    print(f"\nRows:    {len(df)}")
    print(f"Columns: {list(df.columns)}")
    print(f"Date range: {df['date'].iloc[0]} – {df['date'].iloc[-1]}")
    print(f"Station: {df['station_name'].iloc[0]}")
    print("\nFirst 5 rows:")
    print(df.head().to_string(index=False))


def main() -> None:
    """Run the full data collection pipeline for all sources."""
    collect_climate_data()
    print()

    # Pass a station name to fetch data for that location.
    # The Tkinter frontend will call collect_sea_level_data() with the
    # user's selection from get_available_stations().
    collect_sea_level_data(station_name="San Francisco, CA")
    print()
    print("Done. All data saved to data/raw/ and data/processed/.")


if __name__ == "__main__":
    main()
