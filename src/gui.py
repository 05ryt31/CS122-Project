"""
Tkinter frontend for the NASA Climate Data Dashboard.

Provides a two-window interface:
  1. **Main window** – station/metric selection, year range, data summary.
  2. **Plot window** – matplotlib line chart embedded in a Toplevel window.

Usage
-----
    python -m src.gui

Classes
-------
SeaLevelDashboardGUI
    The main application controller.  Creates the root window, loads data
    via ``src.data_adapter``, and manages the plot window lifecycle.
PlotWindow
    A Toplevel window that embeds a matplotlib figure for visualization.
"""

import tkinter as tk
from tkinter import ttk

import pandas as pd
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from src.data_adapter import load_sea_level_data
from src.sea_level_client import get_available_stations
from src.data_analysis import apply_mode, add_trendline, get_summary_stats

# Sea level metrics available for plotting / summary
METRICS = {
    "sea_level_m": "Mean Sea Level (m)",
    "highest_m": "Highest Water Level (m)",
    "lowest_m": "Lowest Water Level (m)",
}


# ---------------------------------------------------------------------------
# Plot window (second window)
# ---------------------------------------------------------------------------

class PlotWindow:
    """A Toplevel window that displays a matplotlib chart.

    Parameters
    ----------
    parent : tk.Tk
        The root Tk window (used as the transient parent).
    """

    def __init__(self, parent: tk.Tk) -> None:
        self.top = tk.Toplevel(parent)
        self.top.title("Sea Level Plot")
        self.top.geometry("800x550")
        self.top.minsize(600, 400)

        # Header label showing station + metric
        self.header_var = tk.StringVar(value="No data loaded")
        header_label = ttk.Label(
            self.top,
            textvariable=self.header_var,
            font=("Helvetica", 13, "bold"),
            anchor="center",
        )
        header_label.pack(pady=(10, 0), fill="x")

        # Matplotlib figure and canvas
        self.figure = Figure(figsize=(7, 4), dpi=100)
        self.ax = self.figure.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.figure, master=self.top)
        self.canvas.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=10)

    # -- public helpers ------------------------------------------------------

    def update_plot(
        self,
        df: pd.DataFrame,
        metric: str,
        station_name: str,
    ) -> None:
        """Redraw the chart with new data.

        Parameters
        ----------
        df : pd.DataFrame
            Processed sea level data (must contain ``date`` and *metric*).
        metric : str
            Column name to plot on the y-axis.
        station_name : str
            Station display name shown in the header and axis label.
        """
        self.ax.clear()

        metric_label = METRICS.get(metric, metric)
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
              
            # Show only a subset of x-tick labels to avoid overlap
            tick_step = max(1, len(plot_df) // 10)
            self.ax.set_xticks(plot_df["date"].values[::tick_step])
            self.ax.tick_params(axis="x", rotation=45, labelsize=8)

        self.ax.set_xlabel("Date")
        self.ax.set_ylabel(metric_label)
        self.ax.set_title(f"{metric_label} over Time")
        self.figure.tight_layout()
        self.canvas.draw()

    def bring_to_front(self) -> None:
        """Raise the plot window above other windows."""
        self.top.lift()
        self.top.focus_force()

    def is_alive(self) -> bool:
        """Return True if the Toplevel window still exists."""
        try:
            return self.top.winfo_exists()
        except tk.TclError:
            return False


# ---------------------------------------------------------------------------
# Main dashboard window
# ---------------------------------------------------------------------------

class SeaLevelDashboardGUI:
    """Main application window for the NASA Climate Data Dashboard.

    Responsibilities:
    - Station and metric selection via dropdown menus.
    - Optional year range filtering.
    - Load data from the backend and display a summary.
    - Open / update a secondary plot window.
    """

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("NASA Climate Data Dashboard")
        self.root.geometry("520x620")
        self.root.minsize(480, 580)

        # Internal state
        self.stations = get_available_stations()
        self.current_df: pd.DataFrame | None = None
        self.plot_window: PlotWindow | None = None

        self._build_ui()

    # -- UI construction -----------------------------------------------------

    def _build_ui(self) -> None:
        """Assemble all widgets in the main window."""
        pad = {"padx": 14, "pady": 4}

        # Title
        title = ttk.Label(
            self.root,
            text="NASA Climate Data Dashboard",
            font=("Helvetica", 16, "bold"),
        )
        title.pack(pady=(14, 6))

        subtitle = ttk.Label(
            self.root,
            text="Sea Level Analysis Tool",
            font=("Helvetica", 11),
        )
        subtitle.pack(pady=(0, 10))

        # --- Controls frame -------------------------------------------------
        controls = ttk.LabelFrame(self.root, text="Settings", padding=10)
        controls.pack(fill="x", **pad)

        # Station selector
        ttk.Label(controls, text="Station:").grid(
            row=0, column=0, sticky="w", pady=4,
        )
        self.station_var = tk.StringVar()
        station_names = list(self.stations.keys())
        self.station_combo = ttk.Combobox(
            controls,
            textvariable=self.station_var,
            values=station_names,
            state="readonly",
            width=28,
        )
        self.station_combo.grid(row=0, column=1, columnspan=2, sticky="w", pady=4)
        self.station_combo.current(0)

        # Metric selector – show "column — Description" for clarity
        ttk.Label(controls, text="Metric:").grid(
            row=1, column=0, sticky="w", pady=4,
        )
        self.metric_var = tk.StringVar()
        self._metric_display = [
            f"{key}  —  {label}" for key, label in METRICS.items()
        ]
        self._metric_keys = list(METRICS.keys())
        self.metric_combo = ttk.Combobox(
            controls,
            textvariable=self.metric_var,
            values=self._metric_display,
            state="readonly",
            width=34,
        )
        self.metric_combo.grid(row=1, column=1, columnspan=2, sticky="w", pady=4)
        self.metric_combo.current(0)

        # Year range
        ttk.Label(controls, text="Start Year:").grid(
            row=2, column=0, sticky="w", pady=4,
        )
        self.start_year_var = tk.StringVar(value="2000")
        self.start_year_entry = ttk.Entry(
            controls, textvariable=self.start_year_var, width=8,
        )
        self.start_year_entry.grid(row=2, column=1, sticky="w", pady=4)

        ttk.Label(controls, text="End Year:").grid(
            row=3, column=0, sticky="w", pady=4,
        )
        self.end_year_var = tk.StringVar(value="2024")
        self.end_year_entry = ttk.Entry(
            controls, textvariable=self.end_year_var, width=8,
        )
        self.end_year_entry.grid(row=3, column=1, sticky="w", pady=4)

        # Data mode and trendline

        ttk.Label(controls, text="Data:").grid(
            row=4, column=0, sticky="w", pady=4,
        )

        self.mode_var = tk.StringVar(value="monthly")
        self.trend_var = tk.BooleanVar(value=False)

        self.mode_combo = ttk.Combobox(
            controls,
            textvariable=self.mode_var,
            values=["monthly", "yearly", "decade"],
            state="readonly",
            width=16,
        )
        
        self.mode_combo.grid(row=4, column=1, sticky="w", pady=4)

        self.trend_check  =ttk.Checkbutton(
            controls,
            text='show trendline',
            variable=self.trend_var
        )
        self.trend_check.grid(row=4, column=3,  sticky="w", pady=4)

        # --- Buttons ---------------------------------------------------------
        btn_frame = ttk.Frame(self.root)
        btn_frame.pack(fill="x", **pad)

        self.load_btn = ttk.Button(
            btn_frame, text="Load Data", command=self._on_load_data,
        )
        self.load_btn.pack(side="left", padx=(0, 8))

        self.plot_btn = ttk.Button(
            btn_frame, text="Show Plot", command=self._on_show_plot,
        )
        self.plot_btn.pack(side="left")

        # --- Status label ----------------------------------------------------
        self.status_var = tk.StringVar(value="Select a station and click Load Data.")
        status_label = ttk.Label(
            self.root,
            textvariable=self.status_var,
            foreground="gray",
        )
        status_label.pack(fill="x", **pad)

        # --- Summary text area -----------------------------------------------
        summary_frame = ttk.LabelFrame(self.root, text="Data Summary", padding=6)
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

    # -- Input validation ----------------------------------------------------

    def _selected_metric_key(self) -> str:
        """Return the column name from the descriptive combo selection."""
        idx = self.metric_combo.current()
        return self._metric_keys[idx]

    def _parse_year(self, raw: str, label: str) -> int | None:
        """Parse a year string, returning None if blank or showing an error."""
        stripped = raw.strip()
        if not stripped:
            return None
        try:
            year = int(stripped)
        except ValueError:
            self._set_status(f"Error: {label} must be a number.", error=True)
            raise
        if year < 1900 or year > 2100:
            self._set_status(
                f"Error: {label} must be between 1900 and 2100.", error=True,
            )
            raise ValueError(f"{label} out of range")
        return year

    # -- Event handlers ------------------------------------------------------

    def _on_load_data(self) -> None:
        """Handle the Load Data button click."""
        station_name = self.station_var.get()
        if not station_name:
            self._set_status("Error: Please select a station.", error=True)
            return

        try:
            start_year = self._parse_year(self.start_year_var.get(), "Start Year")
            end_year = self._parse_year(self.end_year_var.get(), "End Year")
        except ValueError:
            return

        if start_year and end_year and start_year > end_year:
            self._set_status(
                "Error: Start Year must be <= End Year.", error=True,
            )
            return

        metric = self._selected_metric_key()
        mode = self.mode_var.get()
        show_trendline = self.trend_var.get()
        
        self._set_status(f"Loading data for {station_name}...")
        self.root.update_idletasks()

        try:
            df = load_sea_level_data(
                station_name=station_name,
                start_year=start_year,
                end_year=end_year,
            )

            df = apply_mode(df, metric, mode)

            if show_trendline:
                df = add_trendline(df, metric)
              
        except Exception as exc:
            self._set_status(f"Error: {exc}", error=True)
            self.current_df = None
            self._set_summary("Failed to load data. Check your connection.")
            return

        self.current_df = df

        if df.empty:
            self._set_status(
                "No data found for the selected year range.", error=True,
            )
            self._set_summary("No rows returned. Try a different year range.")
            return

        self._set_status(f"Loaded {len(df)} rows for {station_name}.")
        self._display_summary(df, station_name)

    def _on_show_plot(self) -> None:
        """Handle the Show Plot button click."""
        if self.current_df is None or self.current_df.empty:
            self._set_status("Load data first before showing a plot.", error=True)
            return

        metric = self._selected_metric_key()
        station_name = self.station_var.get()

        # Create the plot window if it doesn't exist or was closed
        if self.plot_window is None or not self.plot_window.is_alive():
            self.plot_window = PlotWindow(self.root)

        self.plot_window.update_plot(self.current_df, metric, station_name)
        self.plot_window.bring_to_front()
        self._set_status("Plot updated.")

    # -- Display helpers -----------------------------------------------------

    def _display_summary(self, df: pd.DataFrame, station_name: str) -> None:
        """Build and show a textual summary of the loaded data."""
        metric = self._selected_metric_key()
        metric_label = METRICS.get(metric, metric)
        stats = get_summary_stats(df, metric)

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
                f"Average:      {stats['average']:.4f} m",
                f"Min:          {stats['min']:.4f} m",
                f"Max:          {stats['max']:.4f} m",
                f"Std Dev:      {stats['std_dev']:.4f} m",
            ])

        self._set_summary("\n".join(lines))

    def _set_summary(self, text: str) -> None:
        """Replace the contents of the summary text widget."""
        self.summary_text.configure(state="normal")
        self.summary_text.delete("1.0", "end")
        self.summary_text.insert("1.0", text)
        self.summary_text.configure(state="disabled")

    def _set_status(self, message: str, *, error: bool = False) -> None:
        """Update the status label text and color."""
        self.status_var.set(message)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    """Launch the dashboard GUI."""
    root = tk.Tk()
    SeaLevelDashboardGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
