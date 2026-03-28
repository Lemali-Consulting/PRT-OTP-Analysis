"""Console output helpers and file-saving wrappers for analysis scripts."""

import functools
from pathlib import Path
from typing import Callable

import polars as pl


def analysis_dir(caller_file: str) -> Path:
    """Return the output/ directory for the analysis that owns *caller_file*.

    Replaces the two-line ``HERE = Path(__file__).resolve().parent`` /
    ``OUT = output_dir(HERE)`` boilerplate.  Usage::

        OUT = analysis_dir(__file__)
    """
    here = Path(caller_file).resolve().parent
    out = here / "output"
    out.mkdir(parents=True, exist_ok=True)
    return out


def run_analysis(number: int | str, title: str) -> Callable:
    """Decorator that prints a header/done banner around an analysis entry point.

    Usage::

        @run_analysis(7, "Stop Count vs OTP")
        def main() -> None:
            ...
    """
    def decorator(fn: Callable) -> Callable:
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            print_header(number, title)
            result = fn(*args, **kwargs)
            print_done()
            return result
        return wrapper
    return decorator


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
