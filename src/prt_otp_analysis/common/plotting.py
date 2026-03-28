"""Matplotlib configuration, shared color palettes, and plotting utilities."""

# -- Semantic colors (Tailwind-inspired) -------------------------------------
COLOR_PRIMARY = "#2563eb"  # blue – main data series, primary emphasis
COLOR_NEGATIVE = "#ef4444"  # red – negative values, anomalies, poor OTP
COLOR_GOOD = "#22c55e"  # green – positive values, meets threshold
COLOR_WARNING = "#f59e0b"  # amber – caution, near-threshold
COLOR_GRAY = "#9ca3af"  # gray – muted, secondary, unknown

# -- Categorical palettes ----------------------------------------------------
MODE_COLORS: dict[str, str] = {
    "BUS": "#3b82f6",
    "RAIL": "#22c55e",
    "INCLINE": "#f59e0b",
    "UNKNOWN": "#9ca3af",
}

BUS_TYPE_COLORS: dict[str, str] = {
    "local": "#3b82f6",
    "limited": "#8b5cf6",
    "express": "#ef4444",
    "busway": "#f59e0b",
    "flyer": "#06b6d4",
}


def mode_scatter(
    ax,
    df: "pl.DataFrame",
    x_col: str,
    y_col: str,
    *,
    trend: bool = True,
    min_n: int = 3,
) -> dict[str, float] | None:
    """Plot mode-colored scatter points with an optional bus-only trendline.

    Draws one scatter series per mode in *MODE_COLORS* and, when *trend* is
    True, overlays a linear regression line for BUS routes.  Returns the
    regression stats ``{"r", "p", "slope", "intercept"}`` or ``None`` if the
    trendline was skipped.
    """
    import polars as pl
    from scipy import stats

    for mode, color in MODE_COLORS.items():
        subset = df.filter(pl.col("mode") == mode)
        if len(subset) == 0:
            continue
        ax.scatter(
            subset[x_col].to_list(),
            subset[y_col].to_list(),
            color=color,
            label=mode,
            s=40,
            alpha=0.7,
            edgecolors="white",
            linewidths=0.5,
        )

    if not trend:
        return None

    bus_df = df.filter(pl.col("mode") == "BUS").drop_nulls(subset=[x_col, y_col])
    if len(bus_df) < min_n:
        return None

    x_vals = bus_df[x_col].to_list()
    y_vals = bus_df[y_col].to_list()
    reg = stats.linregress(x_vals, y_vals)
    x_line = [min(x_vals), max(x_vals)]
    y_line = [reg.slope * xi + reg.intercept for xi in x_line]
    ax.plot(
        x_line,
        y_line,
        color="#1e40af",
        linewidth=1.5,
        linestyle="--",
        label=f"BUS trend (r={reg.rvalue:.3f}, p={reg.pvalue:.3f})",
    )
    return {
        "r": float(reg.rvalue),
        "p": float(reg.pvalue),
        "slope": float(reg.slope),
        "intercept": float(reg.intercept),
    }


def setup_plotting():
    """Configure matplotlib defaults for consistent chart styling and return plt."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    plt.rcParams.update({
        "figure.figsize": (12, 6),
        "figure.dpi": 150,
        "axes.grid": True,
        "grid.alpha": 0.3,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "font.size": 10,
    })
    return plt
