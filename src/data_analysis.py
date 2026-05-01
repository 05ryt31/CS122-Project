import numpy as np
import pandas as pd


_DEFAULT_PASSTHROUGH = ("station_id", "station_name")


def apply_mode(df, metric, mode, passthrough_cols=_DEFAULT_PASSTHROUGH):
    '''convert data to month, year, or decade format based on user input '''
    if mode == "monthly":
        return df.copy()

    agg_spec = {metric: "mean"}
    for col in passthrough_cols:
        if col in df.columns:
            agg_spec[col] = "first"

    if mode == "yearly":
        df = df.groupby("year", as_index=False).agg(agg_spec)
        df["date"] = pd.to_datetime(df["year"].astype(str) + "-01-01")
        return df.sort_values("date").reset_index(drop=True)

    if mode == "decade":
        df = df.copy()
        df["decade"] = (df["year"] // 10) * 10
        df = df.groupby("decade", as_index=False).agg(agg_spec)
        df["year"] = df["decade"]
        df["date"] = pd.to_datetime(df["decade"].astype(str) + "-01-01")
        return df.sort_values("date").reset_index(drop=True)

    return df.copy()


def add_trendline(df, metric):
    '''creates a clean dataset to compute a trendline '''
    df = df.copy()
    df["trendline"] = np.nan

    clean_df = df.dropna(subset=[metric]).copy()
    if len(clean_df) < 2:
        return df
        
    clean_df["date"] = pd.to_datetime(clean_df["date"])
    clean_df["years"] = (
        (clean_df["date"] - clean_df["date"].iloc[0]).dt.days / 365.25
    )
    
    x = clean_df["years"]
    y = clean_df[metric]
    
    coeffs = np.polyfit(x, y, 1)
    best_fit = np.poly1d(coeffs)

    clean_df["trendline"] = best_fit(x)

    df.loc[clean_df.index, "trendline"] = clean_df["trendline"]
    return df

def get_trend_per_year(df, metric):
    clean_df = df.dropna(subset=[metric]).copy()
    if len(clean_df) < 2:
        return None

    
    clean_df["date"] = pd.to_datetime(clean_df["date"])

    clean_df["years"] = (
        (clean_df["date"] - clean_df["date"].iloc[0]).dt.days / 365.25
    )

    x = clean_df["years"]
    y = clean_df[metric]

    coeffs = np.polyfit(x, y, 1)
    slope = coeffs[0]  
    return slope    #in unit/yr    
    
def get_summary_stats(df, metric):
    ''' Using user input dates and metric to calculate basic stats.

        Returns: rows loaded, average, date start and end, average, min, max, standard deviation.
    '''
    values = df[metric].dropna()

    stats = {
        "rows_loaded": len(df),
        "valid_points": len(values),
        "missing_points": len(df) - len(values),
        "date_start": None,
        "date_end": None,
        "average": None,
        "min": None,
        "max": None,
        "std_dev": None,
    }

    if not df.empty:
        stats["date_start"] = df["date"].iloc[0]
        stats["date_end"] = df["date"].iloc[-1]

    if not values.empty:
        stats["average"] = values.mean()
        stats["min"] = values.min()
        stats["max"] = values.max()
        stats["std_dev"] = values.std()

    return stats
