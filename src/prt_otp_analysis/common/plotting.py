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
