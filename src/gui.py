"""
Tkinter frontend for the NASA Climate Data Dashboard.

Two-tab interface (Sea Level / Climate) plus a shared plot window.

Usage
-----
    python -m src.gui
"""

import tkinter as tk
from tkinter import ttk

import pandas as pd
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from src.climate_adapter import load_climate_data
from src.data_adapter import load_sea_level_data
from src.data_analysis import add_trendline, apply_mode, get_summary_stats
from src.sea_level_client import get_available_stations

SEA_LEVEL_METRICS = {
    "sea_level_m": "Mean Sea Level (m)",
    "highest_m": "Highest Water Level (m)",
    "lowest_m": "Lowest Water Level (m)",
}

CLIMATE_METRICS = {
    "T2M": "Temperature at 2m (°C)",
    "PRECTOTCORR": "Precipitation (mm/day)",
    "RH2M": "Relative Humidity (%)",
    "PS": "Surface Pressure (kPa)",
}


# ---------------------------------------------------------------------------
# Plot window (shared across tabs)
# ---------------------------------------------------------------------------

class PlotWindow:
    """A Toplevel window that displays a matplotlib chart."""

    def __init__(self, parent: tk.Tk) -> None:
        self.top = tk.Toplevel(parent)
        self.top.title("Data Plot")
        self.top.geometry("800x550")
        self.top.minsize(600, 400)

        self.header_var = tk.StringVar(value="No data loaded")
        header_label = ttk.Label(
            self.top,
            textvariable=self.header_var,
            font=("Helvetica", 13, "bold"),
            anchor="center",
        )
        header_label.pack(pady=(10, 0), fill="x")

        self.figure = Figure(figsize=(7, 4), dpi=100)
        self.ax = self.figure.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.figure, master=self.top)
        self.canvas.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=10)

    def update_plot(
        self,
        df: pd.DataFrame,
        metric: str,
        metric_label: str,
        station_name: str,
    ) -> None:
        """Redraw the chart with new data."""
        self.ax.clear()

        self.header_var.set(f"{station_name}  —  {metric_label}")

        plot_df = df.dropna(subset=[metric])
        if plot_df.empty:
            self.ax.text(
                0.5, 0.5,
                "No data available for this selection.",
                ha="center", va="center", fontsize=12,
                transform=self.ax.transAxes,
            )
        else:
            self.ax.plot(
                plot_df["date"],
                plot_df[metric],
                linewidth=1.2,
                color="#1f77b4",
                label=metric_label,
            )

            if "trendline" in plot_df.columns and plot_df["trendline"].notna().any():
                self.ax.plot(
                    plot_df["date"],
                    plot_df["trendline"],
                    linewidth=1.5,
                    linestyle="--",
                    color="#d62728",
                    label="Trendline",
                )
                self.ax.legend()

            tick_step = max(1, len(plot_df) // 10)
            self.ax.set_xticks(plot_df["date"].values[::tick_step])
            self.ax.tick_params(axis="x", rotation=45, labelsize=8)

        self.ax.set_xlabel("Date")
        self.ax.set_ylabel(metric_label)
        self.ax.set_title(f"{metric_label} over Time")
        self.figure.tight_layout()
        self.canvas.draw()

    def bring_to_front(self) -> None:
        self.top.lift()
        self.top.focus_force()

    def is_alive(self) -> bool:
        try:
            return self.top.winfo_exists()
        except tk.TclError:
            return False


# ---------------------------------------------------------------------------
# Dataset tab base class
# ---------------------------------------------------------------------------

class DatasetTab(ttk.Frame):
    """Shared widgets and behavior for one dataset tab.

    Subclasses provide:
      - ``metrics``: dict mapping column key -> display label.
      - ``loader(station_name, start_year, end_year)``: fetches a DataFrame.
      - ``unit``: string appended to summary stats (e.g. "m" or "").
    """

    metrics: dict[str, str] = {}
    unit: str = ""

    def __init__(self, parent, controller) -> None:
        super().__init__(parent)
        self.controller = controller
        self.stations = get_available_stations()
        self.current_df: pd.DataFrame | None = None
        self._build_ui()

    def loader(self, station_name, start_year, end_year):
        raise NotImplementedError

    # -- UI ------------------------------------------------------------------

    def _build_ui(self) -> None:
        pad = {"padx": 14, "pady": 4}

        controls = ttk.LabelFrame(self, text="Settings", padding=10)
        controls.pack(fill="x", **pad)

        ttk.Label(controls, text="Station:").grid(row=0, column=0, sticky="w", pady=4)
        self.station_var = tk.StringVar()
        self.station_combo = ttk.Combobox(
            controls,
            textvariable=self.station_var,
            values=list(self.stations.keys()),
            state="readonly",
            width=28,
        )
        self.station_combo.grid(row=0, column=1, columnspan=2, sticky="w", pady=4)
        self.station_combo.current(0)

        ttk.Label(controls, text="Metric:").grid(row=1, column=0, sticky="w", pady=4)
        self.metric_var = tk.StringVar()
        self._metric_keys = list(self.metrics.keys())
        self._metric_display = [
            f"{key}  —  {label}" for key, label in self.metrics.items()
        ]
        self.metric_combo = ttk.Combobox(
            controls,
            textvariable=self.metric_var,
            values=self._metric_display,
            state="readonly",
            width=34,
        )
        self.metric_combo.grid(row=1, column=1, columnspan=2, sticky="w", pady=4)
        self.metric_combo.current(0)

        ttk.Label(controls, text="Start Year:").grid(row=2, column=0, sticky="w", pady=4)
        self.start_year_var = tk.StringVar(value="2000")
        ttk.Entry(controls, textvariable=self.start_year_var, width=8).grid(
            row=2, column=1, sticky="w", pady=4,
        )

        ttk.Label(controls, text="End Year:").grid(row=3, column=0, sticky="w", pady=4)
        self.end_year_var = tk.StringVar(value="2024")
        ttk.Entry(controls, textvariable=self.end_year_var, width=8).grid(
            row=3, column=1, sticky="w", pady=4,
        )

        ttk.Label(controls, text="Data:").grid(row=4, column=0, sticky="w", pady=4)
        self.mode_var = tk.StringVar(value="monthly")
        ttk.Combobox(
            controls,
            textvariable=self.mode_var,
            values=["monthly", "yearly", "decade"],
            state="readonly",
            width=16,
        ).grid(row=4, column=1, sticky="w", pady=4)

        self.trend_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            controls,
            text="show trendline",
            variable=self.trend_var,
        ).grid(row=4, column=3, sticky="w", pady=4)

        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill="x", **pad)
        ttk.Button(btn_frame, text="Load Data", command=self._on_load_data).pack(
            side="left", padx=(0, 8),
        )
        ttk.Button(btn_frame, text="Show Plot", command=self._on_show_plot).pack(
            side="left",
        )

        self.status_var = tk.StringVar(value="Select a station and click Load Data.")
        ttk.Label(self, textvariable=self.status_var, foreground="gray").pack(
            fill="x", **pad,
        )

        summary_frame = ttk.LabelFrame(self, text="Data Summary", padding=6)
        summary_frame.pack(fill="both", expand=True, **pad)

        self.summary_text = tk.Text(
            summary_frame,
            height=14,
            wrap="word",
            font=("Courier", 11),
            state="disabled",
        )
        scrollbar = ttk.Scrollbar(
            summary_frame, orient="vertical", command=self.summary_text.yview,
        )
        self.summary_text.configure(yscrollcommand=scrollbar.set)
        self.summary_text.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    # -- Helpers -------------------------------------------------------------

    def _selected_metric_key(self) -> str:
        return self._metric_keys[self.metric_combo.current()]

    def _parse_year(self, raw: str, label: str) -> int | None:
        stripped = raw.strip()
        if not stripped:
            return None
        try:
            year = int(stripped)
        except ValueError:
            self.status_var.set(f"Error: {label} must be a number.")
            raise
        if year < 1900 or year > 2100:
            self.status_var.set(f"Error: {label} must be between 1900 and 2100.")
            raise ValueError(f"{label} out of range")
        return year

    # -- Event handlers ------------------------------------------------------

    def _on_load_data(self) -> None:
        station_name = self.station_var.get()
        if not station_name:
            self.status_var.set("Error: Please select a station.")
            return

        try:
            start_year = self._parse_year(self.start_year_var.get(), "Start Year")
            end_year = self._parse_year(self.end_year_var.get(), "End Year")
        except ValueError:
            return

        if start_year and end_year and start_year > end_year:
            self.status_var.set("Error: Start Year must be <= End Year.")
            return

        metric = self._selected_metric_key()
        mode = self.mode_var.get()
        show_trendline = self.trend_var.get()

        self.status_var.set(f"Loading data for {station_name}...")
        self.update_idletasks()

        try:
            df = self.loader(station_name, start_year, end_year)
            df = apply_mode(df, metric, mode)
            if show_trendline:
                df = add_trendline(df, metric)
        except Exception as exc:
            self.status_var.set(f"Error: {exc}")
            self.current_df = None
            self._set_summary("Failed to load data. Check your connection.")
            return

        self.current_df = df

        if df.empty:
            self.status_var.set("No data found for the selected year range.")
            self._set_summary("No rows returned. Try a different year range.")
            return

        self.status_var.set(f"Loaded {len(df)} rows for {station_name}.")
        self._display_summary(df, station_name)

    def _on_show_plot(self) -> None:
        if self.current_df is None or self.current_df.empty:
            self.status_var.set("Load data first before showing a plot.")
            return

        metric = self._selected_metric_key()
        metric_label = self.metrics.get(metric, metric)
        station_name = self.station_var.get()

        plot_window = self.controller.get_plot_window()
        plot_window.update_plot(self.current_df, metric, metric_label, station_name)
        plot_window.bring_to_front()
        self.status_var.set("Plot updated.")

    # -- Display -------------------------------------------------------------

    def _display_summary(self, df: pd.DataFrame, station_name: str) -> None:
        metric = self._selected_metric_key()
        metric_label = self.metrics.get(metric, metric)
        stats = get_summary_stats(df, metric)
        unit = f" {self.unit}" if self.unit else ""

        lines = [
            f"Station:      {station_name}",
            f"Metric:       {metric_label}",
            f"Mode:         {self.mode_var.get()}",
            f"Date range:   {df['date'].iloc[0]} to {df['date'].iloc[-1]}",
            f"Rows loaded:  {stats['rows_loaded']}",
            "",
        ]

        if stats["average"] is None:
            lines.append("No valid values for this metric.")
        else:
            lines.extend([
                f"Average:      {stats['average']:.4f}{unit}",
                f"Min:          {stats['min']:.4f}{unit}",
                f"Max:          {stats['max']:.4f}{unit}",
                f"Std Dev:      {stats['std_dev']:.4f}{unit}",
            ])

        self._set_summary("\n".join(lines))

    def _set_summary(self, text: str) -> None:
        self.summary_text.configure(state="normal")
        self.summary_text.delete("1.0", "end")
        self.summary_text.insert("1.0", text)
        self.summary_text.configure(state="disabled")


# ---------------------------------------------------------------------------
# Concrete tabs
# ---------------------------------------------------------------------------

class SeaLevelTab(DatasetTab):
    metrics = SEA_LEVEL_METRICS
    unit = "m"

    def loader(self, station_name, start_year, end_year):
        return load_sea_level_data(
            station_name=station_name,
            start_year=start_year,
            end_year=end_year,
        )


class ClimateTab(DatasetTab):
    metrics = CLIMATE_METRICS
    unit = ""

    def loader(self, station_name, start_year, end_year):
        return load_climate_data(
            station_name=station_name,
            start_year=start_year,
            end_year=end_year,
        )


# ---------------------------------------------------------------------------
# Main controller
# ---------------------------------------------------------------------------

class ClimateDashboardGUI:
    """Top-level controller: owns the notebook and shared plot window."""

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("NASA Climate Data Dashboard")
        self.root.geometry("560x680")
        self.root.minsize(500, 600)

        self.plot_window: PlotWindow | None = None

        title = ttk.Label(
            root,
            text="NASA Climate Data Dashboard",
            font=("Helvetica", 16, "bold"),
        )
        title.pack(pady=(14, 6))

        notebook = ttk.Notebook(root)
        notebook.pack(fill="both", expand=True, padx=10, pady=10)

        self.sea_level_tab = SeaLevelTab(notebook, self)
        self.climate_tab = ClimateTab(notebook, self)
        notebook.add(self.sea_level_tab, text="Sea Level")
        notebook.add(self.climate_tab, text="Climate")

    def get_plot_window(self) -> PlotWindow:
        if self.plot_window is None or not self.plot_window.is_alive():
            self.plot_window = PlotWindow(self.root)
        return self.plot_window


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    """Launch the dashboard GUI."""
    root = tk.Tk()
    ClimateDashboardGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
