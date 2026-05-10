"""
ttkbootstrap-themed dashboard for the NASA Climate Data project.

Two-pane layout:
  - Left: notebook (Sea Level / Climate tabs) with controls + summary.
  - Right: embedded matplotlib plot.

Usage
-----
    python -m src.gui
"""

import tkinter as tk

import ttkbootstrap as ttk
from ttkbootstrap.style import ThemeDefinition

import pandas as pd
import matplotlib
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from src.climate_adapter import load_climate_data
from src.data_adapter import load_sea_level_data
from src.data_analysis import apply_mode, add_trendline, get_summary_stats, get_trend_per_year
from src.sea_level_client import get_available_stations


# ---------------------------------------------------------------------------
# Palette + theme
# ---------------------------------------------------------------------------

NASA_BLUE = "#0B3D91"
NASA_RED = "#FC3D21"
SURFACE = "#F4F6F8"
TEXT = "#1A1A1A"
MUTED = "#6B7280"
GRID = "#E5E7EB"
WHITE = "#FFFFFF"

NASA_THEME = ThemeDefinition(
    name="nasa",
    themetype="light",
    colors={
        "primary": NASA_BLUE,
        "secondary": MUTED,
        "success": "#198754",
        "info": "#3B82F6",
        "warning": "#F59E0B",
        "danger": NASA_RED,
        "light": SURFACE,
        "dark": TEXT,
        "bg": WHITE,
        "fg": TEXT,
        "selectbg": NASA_BLUE,
        "selectfg": WHITE,
        "border": GRID,
        "inputfg": TEXT,
        "inputbg": WHITE,
        "active": SURFACE,
    },
)

matplotlib.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Helvetica", "Arial", "DejaVu Sans"],
    "axes.edgecolor": MUTED,
    "axes.labelcolor": TEXT,
    "axes.titleweight": "bold",
    "axes.titlesize": 12,
    "xtick.color": MUTED,
    "ytick.color": MUTED,
    "grid.color": GRID,
    "grid.linewidth": 0.6,
    "axes.grid": True,
    "axes.spines.top": False,
    "axes.spines.right": False,
})

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

SEA_LEVEL_UNITS = {"sea_level_m": "m", "highest_m": "m", "lowest_m": "m"}

CLIMATE_UNITS = {"T2M": "°C", "PRECTOTCORR": "mm/day", "RH2M": "%", "PS": "kPa"}


# ---------------------------------------------------------------------------
# Plot panel (embedded)
# ---------------------------------------------------------------------------

class PlotPanel(ttk.Frame):
    """Matplotlib figure embedded in the right pane."""

    def __init__(self, parent) -> None:
        super().__init__(parent, padding=12)

        self.figure = Figure(figsize=(7, 4.4), dpi=100, facecolor=WHITE)
        self.ax = self.figure.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.figure, master=self)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

        self._draw_placeholder()

    def _draw_placeholder(self) -> None:
        self.ax.clear()
        self.ax.text(
            0.5, 0.5,
            "Load data to see chart",
            ha="center", va="center",
            fontsize=14, color=MUTED,
            transform=self.ax.transAxes,
        )
        self.ax.set_xticks([])
        self.ax.set_yticks([])
        for spine in self.ax.spines.values():
            spine.set_visible(False)
        self.ax.grid(False)
        self.figure.tight_layout()
        self.canvas.draw()

    def update_plot(
        self,
        df: pd.DataFrame,
        metric: str,
        metric_label: str,
        station_name: str,
        trend_label: str | None = None,
    ) -> None:
        self.ax.clear()
        self.ax.grid(True)
        self.ax.spines["left"].set_visible(True)
        self.ax.spines["bottom"].set_visible(True)

        plot_df = df.dropna(subset=[metric])
        if plot_df.empty:
            self.ax.text(
                0.5, 0.5,
                "No data available for this selection.",
                ha="center", va="center", fontsize=12, color=MUTED,
                transform=self.ax.transAxes,
            )
        else:
            self.ax.plot(
                plot_df["date"], plot_df[metric],
                linewidth=1.6, color=NASA_BLUE, label=metric_label,
            )

            if "trendline" in plot_df.columns and plot_df["trendline"].notna().any():
                self.ax.plot(
                    plot_df["date"], plot_df["trendline"],
                    linewidth=1.6, linestyle="--", color=NASA_RED,
                    label=trend_label or "Trendline",
                )
                self.ax.legend(frameon=False, loc="best")

            tick_step = max(1, len(plot_df) // 10)
            self.ax.set_xticks(plot_df["date"].values[::tick_step])
            self.ax.tick_params(axis="x", rotation=45, labelsize=8)

        self.ax.set_xlabel("Date")
        self.ax.set_ylabel(metric_label)
        self.ax.set_title(f"{station_name}  —  {metric_label}", color=TEXT, pad=12)
        self.figure.tight_layout()
        self.canvas.draw()


# ---------------------------------------------------------------------------
# Dataset tab base class
# ---------------------------------------------------------------------------

class DatasetTab(ttk.Frame):
    """Shared widgets and behavior for one dataset tab."""

    metrics: dict[str, str] = {}
    units: dict[str, str] = {}

    def __init__(self, parent, controller) -> None:
        super().__init__(parent, padding=14)
        self.controller = controller
        self.stations = get_available_stations()
        self.current_df: pd.DataFrame | None = None
        self._build_ui()

    def loader(self, station_name, start_year, end_year):
        raise NotImplementedError

    # -- UI ------------------------------------------------------------------

    def _build_ui(self) -> None:
        label_font = ("Helvetica", 10, "bold")

        controls = ttk.Labelframe(
            self, text="  Settings  ", padding=14, bootstyle="primary",
        )
        controls.pack(fill="x", pady=(0, 14))
        controls.columnconfigure(1, weight=1)

        ttk.Label(controls, text="Station", font=label_font).grid(
            row=0, column=0, sticky="w", pady=8, padx=(0, 12),
        )
        self.station_var = tk.StringVar()
        self.station_combo = ttk.Combobox(
            controls,
            textvariable=self.station_var,
            values=list(self.stations.keys()),
            state="readonly",
            bootstyle="primary",
        )
        self.station_combo.grid(row=0, column=1, sticky="ew", pady=8)
        self.station_combo.current(0)

        ttk.Label(controls, text="Metric", font=label_font).grid(
            row=1, column=0, sticky="w", pady=8, padx=(0, 12),
        )
        self.metric_var = tk.StringVar()
        self._metric_keys = list(self.metrics.keys())
        self._metric_display = [f"{key}  —  {label}" for key, label in self.metrics.items()]
        self.metric_combo = ttk.Combobox(
            controls,
            textvariable=self.metric_var,
            values=self._metric_display,
            state="readonly",
            bootstyle="primary",
        )
        self.metric_combo.grid(row=1, column=1, sticky="ew", pady=8)
        self.metric_combo.current(0)

        ttk.Label(controls, text="Start Year", font=label_font).grid(
            row=2, column=0, sticky="w", pady=8, padx=(0, 12),
        )
        self.start_year_var = tk.StringVar(value="2000")
        ttk.Entry(
            controls, textvariable=self.start_year_var, bootstyle="primary",
        ).grid(row=2, column=1, sticky="ew", pady=8)

        ttk.Label(controls, text="End Year", font=label_font).grid(
            row=3, column=0, sticky="w", pady=8, padx=(0, 12),
        )
        self.end_year_var = tk.StringVar(value="2024")
        ttk.Entry(
            controls, textvariable=self.end_year_var, bootstyle="primary",
        ).grid(row=3, column=1, sticky="ew", pady=8)

        ttk.Label(controls, text="Aggregation", font=label_font).grid(
            row=4, column=0, sticky="w", pady=8, padx=(0, 12),
        )
        self.mode_var = tk.StringVar(value="monthly")
        ttk.Combobox(
            controls,
            textvariable=self.mode_var,
            values=["monthly", "yearly", "decade"],
            state="readonly",
            bootstyle="primary",
        ).grid(row=4, column=1, sticky="ew", pady=8)

        self.trend_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            controls,
            text="Show trendline",
            variable=self.trend_var,
            bootstyle="primary-round-toggle",
        ).grid(row=5, column=0, columnspan=2, sticky="w", pady=(12, 4))

        self.load_btn = ttk.Button(
            self,
            text="Load Data",
            command=self._on_load_data,
            bootstyle="primary",
            padding=(10, 12),
        )
        self.load_btn.pack(fill="x", pady=(0, 8))

        self.refresh_btn = ttk.Button(
            self,
            text="Update Plot",
            command=self._on_show_plot,
            bootstyle="info-outline",
            padding=(10, 10),
        )
        self.refresh_btn.pack(fill="x")

        summary_frame = ttk.Labelframe(
            self, text="  Data Summary  ", padding=10, bootstyle="secondary",
        )
        summary_frame.pack(fill="both", expand=True, pady=(14, 0))

        self.summary_text = tk.Text(
            summary_frame,
            height=10,
            wrap="word",
            font=("Menlo", 10),
            relief="flat",
            background=SURFACE,
            foreground=TEXT,
            state="disabled",
            padx=10,
            pady=8,
        )
        self.summary_text.pack(fill="both", expand=True)
        self._set_summary("Load data to see summary statistics.")

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
            self.controller.set_status(f"{label} must be a number.", level="danger")
            raise
        if year < 1900 or year > 2100:
            self.controller.set_status(
                f"{label} must be between 1900 and 2100.", level="danger",
            )
            raise ValueError(f"{label} out of range")
        return year

    def _get_metric_unit(self, metric: str) -> str:
        return self.units.get(metric, "")

    def _convert_trend_for_mode(self, trend_per_year: float) -> float:
        mode = self.mode_var.get()
        if mode == "monthly":
            return trend_per_year / 12
        if mode == "decade":
            return trend_per_year * 10
        return trend_per_year

    def _get_trend_unit_label(self, metric: str) -> str:
        unit = self._get_metric_unit(metric)
        mode = self.mode_var.get()
        if mode == "monthly":
            return f"{unit}/month" if unit else "per month"
        if mode == "decade":
            return f"{unit}/decade" if unit else "per decade"
        return f"{unit}/year" if unit else "per year"

    def _build_trend_label(self, metric: str) -> str | None:
        if not self.trend_var.get() or self.current_df is None:
            return None
        trend_per_year = get_trend_per_year(self.current_df, metric)
        if trend_per_year is None:
            return None
        trend_value = self._convert_trend_for_mode(trend_per_year)
        trend_unit = self._get_trend_unit_label(metric)
        return f"Trend: {trend_value:+.4f} {trend_unit}"

    # -- Event handlers ------------------------------------------------------

    def _on_load_data(self) -> None:
        station_name = self.station_var.get()
        if not station_name:
            self.controller.set_status("Please select a station.", level="warning")
            return

        try:
            start_year = self._parse_year(self.start_year_var.get(), "Start Year")
            end_year = self._parse_year(self.end_year_var.get(), "End Year")
        except ValueError:
            return

        if start_year and end_year and start_year > end_year:
            self.controller.set_status(
                "Start Year must be <= End Year.", level="danger",
            )
            return

        metric = self._selected_metric_key()
        mode = self.mode_var.get()
        show_trendline = self.trend_var.get()

        self.controller.set_status(f"Loading data for {station_name}…", level="info")
        self.load_btn.configure(text="Loading…", state="disabled")
        self.update_idletasks()

        try:
            df = self.loader(station_name, start_year, end_year)
            df = apply_mode(df, metric, mode)
            if show_trendline:
                df = add_trendline(df, metric)
        except Exception as exc:
            self.controller.set_status(f"Error: {exc}", level="danger")
            self.current_df = None
            self._set_summary("Failed to load data. Check your connection.")
            return
        finally:
            self.load_btn.configure(text="Load Data", state="normal")

        self.current_df = df

        if df.empty:
            self.controller.set_status(
                "No data found for the selected year range.", level="warning",
            )
            self._set_summary("No rows returned. Try a different year range.")
            return

        self.controller.set_status(
            f"Loaded {len(df)} rows for {station_name}.", level="success",
        )
        self._display_summary(df, station_name)
        self._render_plot()

    def _on_show_plot(self) -> None:
        if self.current_df is None or self.current_df.empty:
            self.controller.set_status(
                "Load data first before updating the plot.", level="warning",
            )
            return
        self._render_plot()
        self.controller.set_status("Plot updated.", level="info")

    def _render_plot(self) -> None:
        metric = self._selected_metric_key()
        metric_label = self.metrics.get(metric, metric)
        station_name = self.station_var.get()
        trend_label = self._build_trend_label(metric)

        self.controller.plot_panel.update_plot(
            self.current_df, metric, metric_label, station_name, trend_label,
        )

    # -- Display -------------------------------------------------------------

    def _display_summary(self, df: pd.DataFrame, station_name: str) -> None:
        metric = self._selected_metric_key()
        metric_label = self.metrics.get(metric, metric)
        stats = get_summary_stats(df, metric)

        raw_unit = self._get_metric_unit(metric)
        unit = f" {raw_unit}" if raw_unit else ""

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

        trend_per_year = get_trend_per_year(df, metric)
        if trend_per_year is not None:
            trend_value = self._convert_trend_for_mode(trend_per_year)
            trend_unit = self._get_trend_unit_label(metric)
            lines.append(f"Trend:        {trend_value:+.4f} {trend_unit}")

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
    units = SEA_LEVEL_UNITS

    def loader(self, station_name, start_year, end_year):
        return load_sea_level_data(
            station_name=station_name, start_year=start_year, end_year=end_year,
        )


class ClimateTab(DatasetTab):
    metrics = CLIMATE_METRICS
    units = CLIMATE_UNITS

    def loader(self, station_name, start_year, end_year):
        return load_climate_data(
            station_name=station_name, start_year=start_year, end_year=end_year,
        )


# ---------------------------------------------------------------------------
# Main controller
# ---------------------------------------------------------------------------

class ClimateDashboardGUI:
    """Top-level controller: header, paned body, status bar."""

    def __init__(self, root: ttk.Window) -> None:
        self.root = root
        self.root.title("NASA Climate Data Dashboard")
        self.root.geometry("1100x720")
        self.root.minsize(960, 620)

        self._build_header()
        self._build_body()
        self._build_status_bar()

    def _build_header(self) -> None:
        header = tk.Frame(self.root, bg=NASA_BLUE, height=60)
        header.pack(fill="x", side="top")
        header.pack_propagate(False)

        title = tk.Label(
            header,
            text="NASA Climate Data Dashboard",
            font=("Helvetica", 17, "bold"),
            bg=NASA_BLUE,
            fg="white",
        )
        title.pack(side="left", padx=24, pady=14)

        subtitle = tk.Label(
            header,
            text="Sea level & climate trends",
            font=("Helvetica", 11),
            bg=NASA_BLUE,
            fg="#C7D5EE",
        )
        subtitle.pack(side="left", padx=(0, 24), pady=18)

    def _build_body(self) -> None:
        body = ttk.Frame(self.root, padding=(14, 14, 14, 8))
        body.pack(fill="both", expand=True)

        paned = ttk.Panedwindow(body, orient="horizontal")
        paned.pack(fill="both", expand=True)

        left = ttk.Frame(paned, padding=(0, 0, 8, 0))
        notebook = ttk.Notebook(left, bootstyle="primary")
        notebook.pack(fill="both", expand=True)

        self.sea_level_tab = SeaLevelTab(notebook, self)
        self.climate_tab = ClimateTab(notebook, self)
        notebook.add(self.sea_level_tab, text="  Sea Level  ")
        notebook.add(self.climate_tab, text="  Climate  ")

        paned.add(left, weight=2)

        right = ttk.Frame(paned, padding=(8, 0, 0, 0))
        self.plot_panel = PlotPanel(right)
        self.plot_panel.pack(fill="both", expand=True)

        paned.add(right, weight=3)

    def _build_status_bar(self) -> None:
        bar = ttk.Frame(self.root, padding=(14, 6))
        bar.pack(fill="x", side="bottom")

        self.status_var = tk.StringVar(
            value="Ready. Select a station and click Load Data.",
        )
        self.status_label = ttk.Label(
            bar,
            textvariable=self.status_var,
            bootstyle="secondary",
            font=("Helvetica", 10),
        )
        self.status_label.pack(side="left")

    def set_status(self, text: str, level: str = "info") -> None:
        bootstyle_map = {
            "info": "secondary",
            "success": "success",
            "warning": "warning",
            "danger": "danger",
        }
        self.status_var.set(text)
        self.status_label.configure(bootstyle=bootstyle_map.get(level, "secondary"))


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    """Launch the dashboard GUI."""
    root = ttk.Window(themename="cosmo")
    root.style.register_theme(NASA_THEME)
    root.style.theme_use("nasa")
    ClimateDashboardGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
