"""
NASA Climate Data Dashboard – Data Collection Entry Point

This script demonstrates the full data collection pipeline:
1. Fetch monthly climate data from NASA POWER API.
2. Save the raw JSON response to data/raw/.
3. Convert the data to a tabular CSV and save to data/processed/.
4. Print a short summary of what was collected.

Usage
-----
    python main.py

No API key is required.  An internet connection is needed for the fetch.
"""

import requests

from src.api_client import fetch_climate_data
from src.storage import build_dataframe, save_csv, save_raw_json


def main() -> None:
    """Run the data collection pipeline."""
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

    # Save raw response
    json_path = save_raw_json(raw_data)
    print(f"Raw JSON saved to: {json_path}")

    # Build table and save CSV
    df = build_dataframe(raw_data)
    csv_path = save_csv(df)
    print(f"CSV saved to:      {csv_path}")

    # Summary
    print()
    print("--- Collection Summary ---")
    print(f"Rows:    {len(df)}")
    print(f"Columns: {list(df.columns)}")
    print(f"Years:   {df['year'].min()} – {df['year'].max()}")
    print()
    print("First 5 rows:")
    print(df.head().to_string(index=False))


if __name__ == "__main__":
    main()
