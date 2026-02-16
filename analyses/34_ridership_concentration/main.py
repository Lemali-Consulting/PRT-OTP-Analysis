"""Quantify ridership concentration across stops and test whether it correlates with OTP."""

from pathlib import Path

import numpy as np
import polars as pl
from scipy import stats

from prt_otp_analysis.common import output_dir, query_to_polars, setup_plotting

HERE = Path(__file__).resolve().parent
OUT = output_dir(HERE)
DATA_DIR = HERE.parents[1] / "data"


def gini(values: list[float]) -> float:
    """Compute the Gini coefficient for a list of non-negative values."""
    arr = np.array(values, dtype=float)
    arr = arr[~np.isnan(arr)]
    if len(arr) < 2 or arr.sum() == 0:
        return float("nan")
    arr = np.sort(arr)
    n = len(arr)
    index = np.arange(1, n + 1)
    return (2 * np.sum(index * arr) - (n + 1) * np.sum(arr)) / (n * np.sum(arr))


def load_stop_usage() -> pl.DataFrame:
    """Load pre-pandemic weekday stop-route usage from the WPRDC CSV."""
    csv_path = DATA_DIR / "bus-stop-usage" / "wprdc_stop_data.csv"
    df = pl.read_csv(csv_path, null_values=["NA", ""])
    df = df.filter(
        (pl.col("time_period") == "Pre-pandemic")
        & (pl.col("serviceday") == "Weekday")
    )
    # Average across datekeys per stop-route, then compute total usage
    usage = (
        df.group_by(["stop_id", "route_name"])
        .agg(
            pl.col("avg_ons").mean().alias("avg_ons"),
            pl.col("avg_offs").mean().alias("avg_offs"),
            pl.col("stop_name").first().alias("stop_name"),
            pl.col("latitude").first().alias("lat"),
            pl.col("longitude").first().alias("lon"),
        )
        .with_columns(
            (pl.col("avg_ons") + pl.col("avg_offs")).alias("avg_daily_usage")
        )
    )
    return usage


def system_pareto(usage: pl.DataFrame) -> pl.DataFrame:
    """Compute system-wide Pareto curve at the physical-stop level."""
    # Aggregate to physical stop
    per_stop = (
        usage.group_by("stop_id")
        .agg(
            pl.col("avg_daily_usage").sum(),
            pl.col("stop_name").first(),
        )
        .sort("avg_daily_usage", descending=True)
    )

    total = per_stop["avg_daily_usage"].sum()
    cum = per_stop["avg_daily_usage"].cum_sum()
    n = len(per_stop)

    pareto = per_stop.with_columns(
        (pl.Series("rank", range(1, n + 1)) / n * 100).alias("pct_stops"),
        (cum / total * 100).alias("cum_pct_ridership"),
    )
    return pareto


def route_gini(usage: pl.DataFrame) -> pl.DataFrame:
    """Compute Gini coefficient per route from stop-level usage."""
    routes = usage["route_name"].unique().to_list()
    rows = []
    for rt in routes:
        sub = usage.filter(pl.col("route_name") == rt)
        vals = sub["avg_daily_usage"].drop_nulls().to_list()
        if len(vals) < 3:
            continue
        g = gini(vals)
        rows.append({
            "route_name": rt,
            "gini": g,
            "n_stops": len(vals),
            "total_usage": sum(vals),
            "max_stop_usage": max(vals),
        })
    return pl.DataFrame(rows)


def load_route_otp() -> pl.DataFrame:
    """Load average OTP per route from the database."""
    return query_to_polars("""
        SELECT o.route_id, r.route_name, r.mode,
               AVG(o.otp) AS avg_otp
        FROM otp_monthly o
        JOIN routes r ON o.route_id = r.route_id
        GROUP BY o.route_id
        HAVING COUNT(*) >= 12
    """)


def make_charts(pareto: pl.DataFrame, gini_otp: pl.DataFrame) -> None:
    """Generate Pareto curve and Gini vs OTP scatter plot."""
    plt = setup_plotting()

    # --- System-wide Pareto curve ---
    fig, ax = plt.subplots(figsize=(10, 7))
    pct_stops = pareto["pct_stops"].to_list()
    cum_rider = pareto["cum_pct_ridership"].to_list()

    ax.plot(pct_stops, cum_rider, color="#3b82f6", linewidth=2)
    ax.plot([0, 100], [0, 100], color="#94a3b8", linewidth=1, linestyle="--", label="Perfect equality")

    # Find key thresholds
    for target in [50, 80, 90]:
        for i, cr in enumerate(cum_rider):
            if cr >= target:
                ax.axhline(target, color="#d1d5db", linewidth=0.5)
                ax.axvline(pct_stops[i], color="#d1d5db", linewidth=0.5)
                ax.plot(pct_stops[i], target, "o", color="#ef4444", markersize=8)
                ax.annotate(f"{pct_stops[i]:.0f}% of stops -> {target}% of riders",
                            xy=(pct_stops[i], target),
                            xytext=(pct_stops[i] + 5, target - 5),
                            fontsize=9, color="#ef4444")
                break

    ax.set_xlabel("% of Stops (ranked by usage)")
    ax.set_ylabel("Cumulative % of Ridership")
    ax.set_title("System-Wide Ridership Pareto Curve")
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.legend(loc="lower right")
    fig.tight_layout()
    fig.savefig(OUT / "pareto_curve.png", bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved {OUT / 'pareto_curve.png'}")

    # --- Gini vs OTP scatter ---
    fig, ax = plt.subplots(figsize=(10, 7))
    mode_colors = {"BUS": "#3b82f6", "RAIL": "#22c55e", "INCLINE": "#f59e0b", "UNKNOWN": "#9ca3af"}

    for mode, color in mode_colors.items():
        sub = gini_otp.filter(pl.col("mode") == mode)
        if len(sub) == 0:
            continue
        ax.scatter(
            sub["gini"].to_list(), sub["avg_otp"].to_list(),
            color=color, label=mode, s=50, alpha=0.7, edgecolors="white", linewidths=0.5,
        )

    # Bus-only regression
    bus = gini_otp.filter(pl.col("mode") == "BUS").drop_nulls(subset=["gini", "avg_otp"])
    if len(bus) >= 3:
        x = bus["gini"].to_list()
        y = bus["avg_otp"].to_list()
        lr = stats.linregress(x, y)
        r, p = stats.pearsonr(x, y)
        x_line = [min(x), max(x)]
        y_line = [lr.slope * xi + lr.intercept for xi in x_line]
        ax.plot(x_line, y_line, color="#1e40af", linewidth=1.5, linestyle="--",
                label=f"BUS trend (r={r:.3f}, p={p:.3f})")

    ax.set_xlabel("Gini Coefficient (ridership concentration)")
    ax.set_ylabel("Average OTP")
    ax.set_title("Route-Level Ridership Concentration vs On-Time Performance")
    ax.legend(fontsize=9)
    ax.set_ylim(0, 1)
    fig.tight_layout()
    fig.savefig(OUT / "gini_vs_otp.png", bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved {OUT / 'gini_vs_otp.png'}")


def main() -> None:
    """Entry point: load data, compute Pareto and Gini, correlate with OTP."""
    print("=" * 60)
    print("Analysis 34: Ridership Concentration (Pareto)")
    print("=" * 60)

    print("\nLoading stop-level usage (pre-pandemic weekday)...")
    usage = load_stop_usage()
    print(f"  {len(usage):,} stop-route combinations")

    print("\nComputing system-wide Pareto curve...")
    pareto = system_pareto(usage)
    cum = pareto["cum_pct_ridership"].to_list()
    pct = pareto["pct_stops"].to_list()
    for target in [50, 80, 90]:
        for i, cr in enumerate(cum):
            if cr >= target:
                print(f"  {target}% of ridership served by top {pct[i]:.1f}% of stops")
                break

    sys_gini = gini(
        usage.group_by("stop_id").agg(pl.col("avg_daily_usage").sum())["avg_daily_usage"].to_list()
    )
    print(f"  System-wide Gini: {sys_gini:.3f}")

    print("\nComputing per-route Gini coefficients...")
    route_g = route_gini(usage)
    print(f"  {len(route_g)} routes with >= 3 stops")
    print(f"  Gini range: {route_g['gini'].min():.3f} - {route_g['gini'].max():.3f}")
    print(f"  Median Gini: {route_g['gini'].median():.3f}")

    print("\nLoading route OTP...")
    route_otp = load_route_otp()

    # Join Gini with OTP (CSV route_name = DB route_id)
    gini_otp = route_g.join(route_otp, left_on="route_name", right_on="route_id", how="inner")
    print(f"  {len(gini_otp)} routes matched")

    bus = gini_otp.filter(pl.col("mode") == "BUS").drop_nulls(subset=["gini", "avg_otp"])
    if len(bus) >= 3:
        r, p = stats.pearsonr(bus["gini"].to_list(), bus["avg_otp"].to_list())
        rho, p_rho = stats.spearmanr(bus["gini"].to_list(), bus["avg_otp"].to_list())
        print(f"  Bus-only Pearson r = {r:.3f} (p = {p:.3f})")
        print(f"  Bus-only Spearman rho = {rho:.3f} (p = {p_rho:.3f})")

    print("\nSaving CSVs...")
    pareto.write_csv(OUT / "pareto_system.csv")
    print(f"  Saved {OUT / 'pareto_system.csv'}")
    gini_otp.write_csv(OUT / "route_gini.csv")
    print(f"  Saved {OUT / 'route_gini.csv'}")

    print("\nGenerating charts...")
    make_charts(pareto, gini_otp)

    print("\nDone.")


if __name__ == "__main__":
    main()
