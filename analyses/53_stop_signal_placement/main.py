"""Classify PRT bus stops as near-side or far-side relative to nearby traffic signals."""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import polars as pl
from scipy.spatial import cKDTree
from scipy.stats import pearsonr, spearmanr
from shapely.geometry import LineString, Point

from prt_otp_analysis.common import get_db

ANALYSIS_DIR = Path(__file__).parent
OUTPUT_DIR = ANALYSIS_DIR / "output"
GTFS_DIR = Path(__file__).parent.parent.parent / "data" / "GTFS"
OSM_SIGNALS_PATH = (
    Path(__file__).parent.parent.parent / "data" / "osm-signals" / "traffic_signals_raw.json"
)

# Tuning constants
SIGNAL_RADIUS_M = 50.0       # max stop-to-signal distance to count as "at an intersection"
AMBIGUOUS_THRESHOLD_M = 5.0  # stops and signals this close along-shape are ambiguous
DEGREES_PER_METER = 1 / 111_320  # approximate; used for KD-tree radius conversion


def load_signals() -> np.ndarray:
    """Return (N, 2) array of signal [lat, lon]."""
    with open(OSM_SIGNALS_PATH) as f:
        raw = json.load(f)
    return np.array([[e["lat"], e["lon"]] for e in raw])


def load_stops() -> pl.DataFrame:
    """Load GTFS stops, excluding the 4 explicit station nodes."""
    return (
        pl.read_csv(
            GTFS_DIR / "stops.txt",
            schema_overrides={"stop_id": pl.Utf8},
        )
        .filter(pl.col("location_type").is_null())
        .select(["stop_id", "stop_name", "stop_lat", "stop_lon"])
    )


def load_canonical_shapes() -> pl.DataFrame:
    """For each stop, return the shape_id used by the most trips.

    Returns a DataFrame with columns: stop_id, shape_id, route_id.
    """
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
    ).select(["trip_id", "stop_id"])

    return (
        stop_times_df
        .join(trips_df, on="trip_id")
        .group_by(["stop_id", "shape_id", "route_id"])
        .agg(pl.len().alias("trip_count"))
        .sort("trip_count", descending=True)
        .unique(subset=["stop_id"], keep="first")
        .select(["stop_id", "shape_id", "route_id"])
    )


def build_shape_lines(shape_ids: set[str]) -> dict[str, LineString]:
    """Load GTFS shapes and return a dict of shape_id → Shapely LineString."""
    shapes_df = (
        pl.read_csv(
            GTFS_DIR / "shapes.txt",
            schema_overrides={"shape_id": pl.Utf8},
        )
        .filter(pl.col("shape_id").is_in(shape_ids))
        .sort(["shape_id", "shape_pt_sequence"])
    )

    lines: dict[str, LineString] = {}
    for (shape_id,), group in shapes_df.group_by("shape_id"):
        coords = list(zip(group["shape_pt_lon"].to_list(), group["shape_pt_lat"].to_list()))
        if len(coords) >= 2:
            lines[shape_id] = LineString(coords)
    return lines


def classify_stop(
    stop_lat: float,
    stop_lon: float,
    signal_lat: float,
    signal_lon: float,
    shape_line: LineString,
) -> str:
    """Return 'near_side', 'far_side', or 'ambiguous'."""
    stop_pt = Point(stop_lon, stop_lat)
    signal_pt = Point(signal_lon, signal_lat)

    stop_pos = shape_line.project(stop_pt)
    signal_pos = shape_line.project(signal_pt)

    delta_deg = signal_pos - stop_pos
    delta_m = delta_deg / DEGREES_PER_METER
    if abs(delta_m) <= AMBIGUOUS_THRESHOLD_M:
        return "ambiguous"
    return "near_side" if delta_deg > 0 else "far_side"


def main() -> None:
    OUTPUT_DIR.mkdir(exist_ok=True)

    print("Loading stops and signals…")
    stops_df = load_stops()
    signals = load_signals()  # shape (N, 2): [lat, lon]

    # Build KD-tree on signals (lat/lon degrees)
    tree = cKDTree(signals)
    stop_coords = stops_df.select(["stop_lat", "stop_lon"]).to_numpy()
    radius_deg = SIGNAL_RADIUS_M * DEGREES_PER_METER
    nearest_dists, nearest_idxs = tree.query(stop_coords, k=1, distance_upper_bound=radius_deg)

    has_signal = nearest_dists < radius_deg
    safe_idxs = nearest_idxs.clip(0, len(signals) - 1)
    signal_lat_col = np.where(has_signal, signals[safe_idxs, 0], np.nan)
    signal_lon_col = np.where(has_signal, signals[safe_idxs, 1], np.nan)
    dist_m_col = np.where(has_signal, nearest_dists / DEGREES_PER_METER, np.nan)

    stops_df = stops_df.with_columns([
        pl.Series("has_signal", has_signal),
        pl.Series("signal_lat", signal_lat_col),
        pl.Series("signal_lon", signal_lon_col),
        pl.Series("signal_dist_m", dist_m_col),
    ])
    print(f"  {has_signal.sum()} of {len(stops_df)} stops have a signal within {SIGNAL_RADIUS_M} m")

    print("Loading canonical shapes…")
    canonical_df = load_canonical_shapes()
    stops_df = stops_df.join(canonical_df, on="stop_id", how="left")

    classifiable_df = stops_df.filter(
        pl.col("has_signal") & pl.col("shape_id").is_not_null()
    )
    print(f"  {len(classifiable_df)} stops are classifiable (signal + shape)")

    print("Building shape geometries…")
    needed_ids = set(classifiable_df["shape_id"].to_list())
    shape_lines = build_shape_lines(needed_ids)
    print(f"  Loaded {len(shape_lines)} shape polylines")

    print("Classifying stops…")
    classifications: list[str] = []
    for row in classifiable_df.iter_rows(named=True):
        sid = row["shape_id"]
        if sid not in shape_lines:
            classifications.append("no_shape")
            continue
        classifications.append(
            classify_stop(
                row["stop_lat"], row["stop_lon"],
                row["signal_lat"], row["signal_lon"],
                shape_lines[sid],
            )
        )

    classifiable_df = classifiable_df.with_columns(
        pl.Series("classification", classifications)
    )

    stops_with_class_df = stops_df.join(
        classifiable_df.select(["stop_id", "classification", "route_id"]),
        on="stop_id",
        how="left",
    ).with_columns(
        pl.when(~pl.col("has_signal"))
        .then(pl.lit("mid_block"))
        .otherwise(pl.col("classification"))
        .alias("classification")
    )

    # ── Output 1: stop-level CSV ──────────────────────────────────────────────
    stop_out_df = stops_with_class_df.select([
        "stop_id", "stop_name", "stop_lat", "stop_lon",
        "classification", "signal_dist_m", "shape_id",
    ])
    stop_out_df.write_csv(OUTPUT_DIR / "stop_classifications.csv")
    print(f"\nWrote {len(stop_out_df)} rows → stop_classifications.csv")

    class_counts = (
        stops_with_class_df
        .group_by("classification")
        .agg(pl.len().alias("count"))
        .sort("count", descending=True)
    )
    print("\nSystem-wide classification:")
    print(class_counts)

    # ── Output 2: route summary ───────────────────────────────────────────────
    signalized_df = stops_with_class_df.filter(
        pl.col("classification").is_in(["near_side", "far_side"])
    )
    route_summary_df = (
        signalized_df
        .group_by("route_id")
        .agg([
            (pl.col("classification") == "near_side").sum().alias("near_side_count"),
            (pl.col("classification") == "far_side").sum().alias("far_side_count"),
        ])
        .with_columns(
            (pl.col("near_side_count") + pl.col("far_side_count")).alias("total_signalized"),
        )
        .with_columns(
            (pl.col("near_side_count") / pl.col("total_signalized")).alias("near_side_fraction"),
        )
        .filter(pl.col("total_signalized") >= 3)
    )

    mid_block_by_route_df = (
        stops_with_class_df
        .filter(pl.col("classification") == "mid_block")
        .group_by("route_id")
        .agg(pl.len().alias("mid_block_count"))
    )
    route_summary_df = route_summary_df.join(mid_block_by_route_df, on="route_id", how="left")

    db = get_db()
    otp_df = pl.from_records(
        db.execute(
            "SELECT route_id, AVG(otp) AS mean_otp FROM otp_monthly GROUP BY route_id"
        ).fetchall(),
        schema=["route_id", "mean_otp"],
        orient="row",
    )
    route_summary_df = route_summary_df.join(otp_df, on="route_id", how="left")
    route_summary_df.write_csv(OUTPUT_DIR / "route_summary.csv")
    print(f"Wrote {len(route_summary_df)} rows → route_summary.csv")

    # ── Output 3: system summary bar chart ────────────────────────────────────
    labels_order = ["near_side", "far_side", "ambiguous", "mid_block", "no_shape"]
    label_display = {
        "near_side": "Near-side",
        "far_side": "Far-side",
        "ambiguous": "Ambiguous",
        "mid_block": "Mid-block",
        "no_shape": "No shape",
    }
    counts_map: dict[str, int] = dict(
        zip(class_counts["classification"].to_list(), class_counts["count"].to_list())
    )
    present = [k for k in labels_order if counts_map.get(k, 0) > 0]
    vals = [counts_map[k] for k in present]
    lbls = [label_display[k] for k in present]
    colors = ["#e74c3c", "#2980b9", "#95a5a6", "#bdc3c7", "#7f8c8d"][: len(present)]

    fig, ax = plt.subplots(figsize=(8, 5))
    bars = ax.bar(lbls, vals, color=colors, edgecolor="white")
    ax.bar_label(bars, fmt="%d", padding=4, fontsize=11)
    total = sum(vals)
    ax.set_ylim(0, max(vals) * 1.18)
    for bar, lbl in zip(bars, lbls):
        if lbl in ("Near-side", "Far-side"):
            pct = bar.get_height() / total * 100
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height() + max(vals) * 0.07,
                f"({pct:.1f}% of all stops)",
                ha="center", va="bottom", fontsize=9, color="#555",
            )
    ax.set_title("PRT Bus Stop Placement at Signalized Intersections", fontsize=14, fontweight="bold")
    ax.set_ylabel("Number of stops")
    plt.tight_layout()
    fig.savefig(OUTPUT_DIR / "system_summary.png", dpi=150)
    plt.close(fig)
    print("Wrote system_summary.png")

    # ── Output 4: near-side fraction vs OTP scatter ───────────────────────────
    corr_df = route_summary_df.drop_nulls(subset=["near_side_fraction", "mean_otp"])
    if len(corr_df) >= 10:
        x = corr_df["near_side_fraction"].to_numpy()
        y = corr_df["mean_otp"].to_numpy()
        r, p_pearson = pearsonr(x, y)
        rho, p_spearman = spearmanr(x, y)

        fig, ax = plt.subplots(figsize=(8, 6))
        ax.scatter(x * 100, y * 100, alpha=0.6, s=50, color="#2980b9", edgecolors="white", linewidths=0.5)
        m, b = np.polyfit(x, y, 1)
        xline = np.linspace(x.min(), x.max(), 100)
        ax.plot(xline * 100, (m * xline + b) * 100, color="#e74c3c", linewidth=1.5, linestyle="--")
        ax.set_xlabel("Near-side fraction (%)", fontsize=12)
        ax.set_ylabel("Mean OTP (%)", fontsize=12)
        ax.set_title(
            f"Route Near-Side Fraction vs. OTP  (r = {r:.2f}, ρ = {rho:.2f})",
            fontsize=13, fontweight="bold",
        )
        plt.tight_layout()
        fig.savefig(OUTPUT_DIR / "nearside_vs_otp.png", dpi=150)
        plt.close(fig)
        print(
            f"Wrote nearside_vs_otp.png  "
            f"(r={r:.3f} p={p_pearson:.4f}, ρ={rho:.3f} p={p_spearman:.4f}, n={len(corr_df)})"
        )
    else:
        print("Too few routes with OTP data; skipping scatter plot.")

    # ── Output 5: top routes by near-side fraction ────────────────────────────
    top_df = (
        route_summary_df
        .filter(pl.col("total_signalized") >= 5)
        .sort("near_side_fraction", descending=True)
        .head(20)
    )
    if len(top_df) > 0:
        fig, ax = plt.subplots(figsize=(9, 7))
        ax.barh(
            top_df["route_id"].to_list()[::-1],
            (top_df["near_side_fraction"] * 100).to_list()[::-1],
            color="#e74c3c", edgecolor="white",
        )
        ax.axvline(50, color="#555", linewidth=1, linestyle="--", label="50%")
        ax.set_xlabel("Near-side fraction (%)")
        ax.set_title(
            "Top 20 Routes by Near-Side Stop Fraction\n(≥ 5 signalized stops)",
            fontweight="bold",
        )
        ax.legend()
        plt.tight_layout()
        fig.savefig(OUTPUT_DIR / "top_nearside_routes.png", dpi=150)
        plt.close(fig)
        print("Wrote top_nearside_routes.png")

    print("\nDone.")


if __name__ == "__main__":
    main()
