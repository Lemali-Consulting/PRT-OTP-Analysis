"""Console output helpers and file-saving wrappers for analysis scripts."""

from pathlib import Path

import polars as pl


def print_header(number: int | str, title: str) -> None:
    """Print a standard analysis header with separator lines."""
    print("=" * 60)
    print(f"Analysis {number}: {title}")
    print("=" * 60)


def print_done() -> None:
    """Print the standard analysis completion message."""
    print("\nDone.")


def save_csv(df: pl.DataFrame, path: str | Path, *, quiet: bool = False) -> Path:
    """Write a Polars DataFrame to CSV with standardized logging."""
    path = Path(path)
    df.write_csv(path)
    if not quiet:
        print(f"  Saved to {path}")
    return path


def save_chart(fig, path: Path, **savefig_kwargs) -> None:
    """Save a matplotlib figure, close it, and print confirmation.

    Calls tight_layout(), savefig(bbox_inches='tight'), and plt.close(fig).
    Extra keyword arguments are forwarded to savefig.
    """
    import matplotlib.pyplot as plt

    fig.tight_layout()
    fig.savefig(path, bbox_inches="tight", **savefig_kwargs)
    plt.close(fig)
    print(f"  Chart saved to {path}")
