"""Matplotlib configuration and shared plotting utilities."""


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
