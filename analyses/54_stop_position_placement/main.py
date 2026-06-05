"""Test whether near-side/far-side placement varies by stop position along the route."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import polars as pl
from scipy.stats import pearsonr
from scipy.special import expit

from prt_otp_analysis.common import get_db

ANALYSIS_DIR = Path(__file__).parent
OUTPUT_DIR = ANALYSIS_DIR / "output"
GTFS_DIR = Path(__file__).parent.parent.parent / "data" / "GTFS"
CLASSIFICATIONS_CSV = (
    Path(__file__).parent.parent / "53_stop_signal_placement" / "output" / "stop_classifications.csv"
)

MIN_SIGNALIZED = 5  # minimum signalized stops per route for OTP comparison


def load_stop_positions() -> pl.DataFrame:
    """Return classified stops with their normalized position [0,1] along their canonical route.

    Normalized position = (stop_sequence - 1) / (max_stop_sequence - 1) per trip,
    using the canonical trip (most-served shape for that stop).
    """
    class_df = pl.read_csv(
        CLASSIFICATIONS_CSV,
        schema_overrides={"stop_id": pl.Utf8, "shape_id": pl.Utf8},
    ).filter(pl.col("classification").is_in(["near_side", "far_side"]))

    trips_df = pl.read_csv(
        GTFS_DIR / "trips.txt",
        schema_overrides={
            "trip_id": pl.Utf8,
            "shape_id": pl.Utf8,
            "route_id": pl.Utf8,
            "service_id": pl.Utf8,
        },
    ).select(["trip_id", "shape_id", "route_id"])

    stop_times_df = pl.read_csv(
        GTFS_DIR / "stop_times.txt",
        schema_overrides={"trip_id": pl.Utf8, "stop_id": pl.Utf8},
    ).select(["trip_id", "stop_id", "stop_sequence"])

    # For each shape_id, pick the canonical trip (most stops = most representative)
    trip_lengths_df = (
        stop_times_df
        .join(trips_df.select(["trip_id", "shape_id"]), on="trip_id")
        .group_by(["shape_id", "trip_id"])
        .agg(pl.len().alias("n_stops"))
        .sort("n_stops", descending=True)
        .unique(subset=["shape_id"], keep="first")
        .select(["shape_id", "trip_id"])
    )

    # Get stop_times for canonical trips only, with max_sequence
    canonical_trips = trip_lengths_df["trip_id"].to_list()
    canonical_stop_times_df = (
        stop_times_df
        .filter(pl.col("trip_id").is_in(canonical_trips))
        .join(
            stop_times_df
            .filter(pl.col("trip_id").is_in(canonical_trips))
            .group_by("trip_id")
            .agg(pl.col("stop_sequence").max().alias("max_seq")),
            on="trip_id",
        )
        .with_columns(
            ((pl.col("stop_sequence") - 1) / (pl.col("max_seq") - 1)).alias("position")
        )
        .select(["trip_id", "stop_id", "stop_sequence", "max_seq", "position"])
    )

    # Join canonical trip back via shape_id
    canonical_stop_times_df = canonical_stop_times_df.join(
        trip_lengths_df, on="trip_id"
    )

    # Join classification (which carries shape_id) to get positions
    result_df = (
        class_df
        .join(
            canonical_stop_times_df.select(["shape_id", "stop_id", "stop_sequence", "max_seq", "position"]),
            on=["shape_id", "stop_id"],
            how="inner",
        )
        .join(
            trips_df.unique(subset=["shape_id"]).select(["shape_id", "route_id"]),
            on="shape_id",
            how="left",
        )
    )
    return result_df


def main() -> None:
    OUTPUT_DIR.mkdir(exist_ok=True)

    print("Loading stop positions…")
    stops_df = load_stop_positions()
    print(f"  {len(stops_df)} classified stops with position data")
    print(f"  near_side: {(stops_df['classification'] == 'near_side').sum()}, "
          f"far_side: {(stops_df['classification'] == 'far_side').sum()}")

    positions = stops_df["position"].to_numpy()
    is_nearside = (stops_df["classification"] == "near_side").to_numpy().astype(int)

    # ── Output 1: near-side fraction by position quintile ─────────────────────
    quintile_labels = ["0–20%", "20–40%", "40–60%", "60–80%", "80–100%"]
    edges = [0.0, 0.2, 0.4, 0.6, 0.8, 1.0001]
    ns_fracs, n_stops = [], []
    for lo, hi in zip(edges[:-1], edges[1:]):
        mask = (positions >= lo) & (positions < hi)
        total = mask.sum()
        ns = is_nearside[mask].sum()
        ns_fracs.append(ns / total if total > 0 else np.nan)
        n_stops.append(total)

    fig, ax = plt.subplots(figsize=(8, 5))
    bars = ax.bar(quintile_labels, [f * 100 for f in ns_fracs], color="#e74c3c", edgecolor="white")
    ax.bar_label(bars, fmt="%.1f%%", padding=4, fontsize=10)
    for i, n in enumerate(n_stops):
        ax.text(i, 2, f"n={n}", ha="center", va="bottom", fontsize=8, color="white")
    ax.set_ylim(0, 100)
    ax.axhline(83, color="#555", linewidth=1, linestyle="--", label="System avg (83%)")
    ax.set_xlabel("Stop position along route")
    ax.set_ylabel("Near-side fraction (%)")
    ax.set_title("Near-Side Fraction by Route Position Quintile", fontsize=13, fontweight="bold")
    ax.legend()
    plt.tight_layout()
    fig.savefig(OUTPUT_DIR / "position_quintile_nearside.png", dpi=150)
    plt.close(fig)
    print("Wrote position_quintile_nearside.png")
    for lbl, frac, n in zip(quintile_labels, ns_fracs, n_stops):
        print(f"  {lbl}: {frac*100:.1f}%  (n={n})")

    # ── Logistic regression: position → near_side? ────────────────────────────
    # Manual MLE via scipy.optimize since sklearn is not available
    from scipy.optimize import minimize

    def neg_log_likelihood(params: np.ndarray) -> float:
        b0, b1 = params
        logit = b0 + b1 * positions
        prob = expit(logit)
        eps = 1e-12
        return -np.sum(is_nearside * np.log(prob + eps) + (1 - is_nearside) * np.log(1 - prob + eps))

    res = minimize(neg_log_likelihood, [0.0, 0.0], method="L-BFGS-B")
    b0, b1 = res.x
    coef = b1
    print(f"\nLogistic regression coef (position → near_side): {coef:.3f}")
    print("  (positive = more near-side toward end; negative = more far-side toward end)")

    # ── Output 2: KDE of position by classification ───────────────────────────
    from scipy.stats import gaussian_kde

    ns_pos = positions[is_nearside == 1]
    fs_pos = positions[is_nearside == 0]
    x_grid = np.linspace(0, 1, 300)

    fig, ax = plt.subplots(figsize=(8, 5))
    if len(ns_pos) > 5:
        kde_ns = gaussian_kde(ns_pos, bw_method=0.15)
        ax.fill_between(x_grid, kde_ns(x_grid), alpha=0.35, color="#e74c3c", label=f"Near-side (n={len(ns_pos)})")
        ax.plot(x_grid, kde_ns(x_grid), color="#e74c3c", linewidth=1.5)
    if len(fs_pos) > 5:
        kde_fs = gaussian_kde(fs_pos, bw_method=0.15)
        ax.fill_between(x_grid, kde_fs(x_grid), alpha=0.35, color="#2980b9", label=f"Far-side (n={len(fs_pos)})")
        ax.plot(x_grid, kde_fs(x_grid), color="#2980b9", linewidth=1.5)
    ax.set_xlabel("Normalized stop position (0 = route start, 1 = route end)")
    ax.set_ylabel("Density")
    ax.set_title("Distribution of Stop Position by Classification", fontsize=13, fontweight="bold")
    ax.legend()
    plt.tight_layout()
    fig.savefig(OUTPUT_DIR / "position_kde.png", dpi=150)
    plt.close(fig)
    print("Wrote position_kde.png")

    # ── Output 3: split-half route summaries ─────────────────────────────────
    route_df = (
        stops_df
        .with_columns(
            (pl.col("position") >= 0.5).alias("second_half")
        )
        .group_by(["route_id", "second_half"])
        .agg([
            (pl.col("classification") == "near_side").sum().alias("ns"),
            pl.len().alias("total"),
        ])
        .with_columns(
            (pl.col("ns") / pl.col("total")).alias("ns_frac")
        )
    )

    first_half_df = (
        route_df.filter(~pl.col("second_half"))
        .select(["route_id", pl.col("ns_frac").alias("ns_first_half"), pl.col("total").alias("n_first")])
    )
    second_half_df = (
        route_df.filter(pl.col("second_half"))
        .select(["route_id", pl.col("ns_frac").alias("ns_second_half"), pl.col("total").alias("n_second")])
    )
    overall_df = (
        stops_df
        .group_by("route_id")
        .agg([
            (pl.col("classification") == "near_side").sum().alias("ns_total"),
            pl.len().alias("total"),
        ])
        .with_columns((pl.col("ns_total") / pl.col("total")).alias("ns_overall"))
        .filter(pl.col("total") >= MIN_SIGNALIZED)
        .select(["route_id", "ns_overall", "total"])
    )

    db = get_db()
    otp_df = pl.from_records(
        db.execute(
            "SELECT route_id, AVG(otp) AS mean_otp FROM otp_monthly GROUP BY route_id"
        ).fetchall(),
        schema=["route_id", "mean_otp"],
        orient="row",
    )

    summary_df = (
        overall_df
        .join(first_half_df, on="route_id", how="left")
        .join(second_half_df, on="route_id", how="left")
        .join(otp_df, on="route_id", how="left")
        .drop_nulls(subset=["ns_overall", "mean_otp"])
    )
    summary_df.write_csv(OUTPUT_DIR / "route_position_summary.csv")
    print(f"\nWrote {len(summary_df)} rows → route_position_summary.csv")

    # Correlations
    for col, label in [
        ("ns_overall", "Overall near-side fraction"),
        ("ns_first_half", "First-half near-side fraction"),
        ("ns_second_half", "Second-half near-side fraction"),
    ]:
        sub = summary_df.drop_nulls(subset=[col, "mean_otp"])
        if len(sub) < 10:
            print(f"  {label}: too few routes")
            continue
        r, p = pearsonr(sub[col].to_numpy(), sub["mean_otp"].to_numpy())
        print(f"  {label}: r={r:.3f}  p={p:.4f}  n={len(sub)}")

    # ── Output 4: side-by-side scatter: first-half vs second-half vs OTP ──────
    sub = summary_df.drop_nulls(subset=["ns_first_half", "ns_second_half", "mean_otp"])
    if len(sub) >= 10:
        fig, axes = plt.subplots(1, 2, figsize=(12, 5), sharey=True)
        for ax, col, title, color in [
            (axes[0], "ns_first_half", "First-half near-side fraction", "#e67e22"),
            (axes[1], "ns_second_half", "Second-half near-side fraction", "#e74c3c"),
        ]:
            x = sub[col].to_numpy()
            y = sub["mean_otp"].to_numpy()
            r, p = pearsonr(x, y)
            ax.scatter(x * 100, y * 100, alpha=0.6, s=50, color=color,
                       edgecolors="white", linewidths=0.5)
            m, b = np.polyfit(x, y, 1)
            xline = np.linspace(x.min(), x.max(), 100)
            ax.plot(xline * 100, (m * xline + b) * 100, color="#333",
                    linewidth=1.5, linestyle="--")
            ax.set_title(f"{title}\nr = {r:.2f}  (p = {p:.3f})", fontsize=11, fontweight="bold")
            ax.set_xlabel("Near-side fraction (%)")
        axes[0].set_ylabel("Mean OTP (%)")
        fig.suptitle("Near-Side Fraction vs. Route OTP: First Half vs. Second Half of Route",
                     fontsize=12, fontweight="bold", y=1.01)
        plt.tight_layout()
        fig.savefig(OUTPUT_DIR / "splithalf_otp_comparison.png", dpi=150, bbox_inches="tight")
        plt.close(fig)
        print("Wrote splithalf_otp_comparison.png")

    print("\nDone.")


if __name__ == "__main__":
    main()
