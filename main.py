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
from src.sea_level_client import fetch_sea_level_data
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


def collect_sea_level_data() -> None:
    """Fetch and store NOAA CO-OPS sea level data."""
    print("=" * 50)
    print("[2/2] NOAA CO-OPS – Sea Level Data")
    print("=" * 50)
    print("Fetching sea level data from NOAA CO-OPS API...")

    try:
        raw_data = fetch_sea_level_data()
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
    station = df["station_name"].iloc[0]
    print(f"Station: {station}")
    print("\nFirst 5 rows:")
    print(df.head().to_string(index=False))


def main() -> None:
    """Run the full data collection pipeline for all sources."""
    collect_climate_data()
    print()
    collect_sea_level_data()
    print()
    print("Done. All data saved to data/raw/ and data/processed/.")


if __name__ == "__main__":
    main()
