"""Analysis of inbound vs outbound trip asymmetry and its correlation with OTP."""

from pathlib import Path

import polars as pl
from scipy import stats

from prt_otp_analysis.common import output_dir, query_to_polars, setup_plotting

HERE = Path(__file__).resolve().parent
OUT = output_dir(HERE)


def load_data() -> tuple[pl.DataFrame, pl.DataFrame]:
    """Load directional peak trip frequency and average OTP per route."""
    # Use MAX(trips_wd) per route-direction to get peak frequency, not stop-visits.
    # Include IB,OB stops in both directions to avoid exclusion bias.
    directional = query_to_polars("""
        SELECT route_id, 'IB' AS direction,
               MAX(trips_wd) AS trips_wd, MAX(trips_7d) AS trips_7d
        FROM route_stops
        WHERE direction IN ('IB', 'IB,OB')
          AND trips_wd IS NOT NULL
        GROUP BY route_id
        UNION ALL
        SELECT route_id, 'OB' AS direction,
               MAX(trips_wd) AS trips_wd, MAX(trips_7d) AS trips_7d
        FROM route_stops
        WHERE direction IN ('OB', 'IB,OB')
          AND trips_wd IS NOT NULL
        GROUP BY route_id
    """)
    avg_otp = query_to_polars("""
        SELECT o.route_id, r.route_name, r.mode,
               AVG(o.otp) AS avg_otp, COUNT(*) AS months
        FROM otp_monthly o
        JOIN routes r ON o.route_id = r.route_id
        GROUP BY o.route_id
        HAVING COUNT(*) >= 12
    """)
    return directional, avg_otp


def analyze(directional: pl.DataFrame, avg_otp: pl.DataFrame) -> tuple[pl.DataFrame, dict]:
    """Compute asymmetry index per route and correlate with OTP."""
    # Pivot to get IB and OB columns
    pivoted = directional.pivot(on="direction", index="route_id", values="trips_wd")

    if "IB" not in pivoted.columns or "OB" not in pivoted.columns:
        print("  Warning: Missing IB or OB direction data")
        return pl.DataFrame(), {}

    pivoted = pivoted.rename({"IB": "ib_trips_wd", "OB": "ob_trips_wd"})

    # Drop routes missing a direction entirely (likely loop routes, not genuinely asymmetric)
    pivoted = pivoted.filter(
        pl.col("ib_trips_wd").is_not_null() & pl.col("ob_trips_wd").is_not_null()
    )

    # Compute asymmetry index
    pivoted = pivoted.with_columns(
        total_trips=pl.col("ib_trips_wd") + pl.col("ob_trips_wd"),
    )
    pivoted = pivoted.filter(pl.col("total_trips") > 0)
    pivoted = pivoted.with_columns(
        asymmetry_index=(
            (pl.col("ib_trips_wd") - pl.col("ob_trips_wd")).abs()
            / pl.col("total_trips")
        ),
    )

    # Join with OTP
    result = pivoted.join(avg_otp, on="route_id", how="inner")

    # Compute correlations
    results = {}

    # All routes
    r_all, p_all = stats.pearsonr(
        result["asymmetry_index"].to_list(), result["avg_otp"].to_list()
    )
    results["all_pearson_r"] = r_all
    results["all_pearson_p"] = p_all
    results["all_n"] = len(result)

    # Bus only
    bus = result.filter(pl.col("mode") == "BUS")
    if len(bus) > 2:
        r_bus, p_bus = stats.pearsonr(
            bus["asymmetry_index"].to_list(), bus["avg_otp"].to_list()
        )
        rho_bus, p_rho = stats.spearmanr(
            bus["asymmetry_index"].to_list(), bus["avg_otp"].to_list()
        )
        results["bus_pearson_r"] = r_bus
        results["bus_pearson_p"] = p_bus
        results["bus_spearman_r"] = rho_bus
        results["bus_spearman_p"] = p_rho
        results["bus_n"] = len(bus)

    return result.sort("asymmetry_index", descending=True), results


def make_chart(df: pl.DataFrame, results: dict) -> None:
    """Generate scatter plot of directional asymmetry vs OTP."""
    plt = setup_plotting()
    fig, ax = plt.subplots(figsize=(10, 7))

    mode_colors = {"BUS": "#3b82f6", "RAIL": "#22c55e", "INCLINE": "#f59e0b", "UNKNOWN": "#9ca3af"}

    for mode, color in mode_colors.items():
        subset = df.filter(pl.col("mode") == mode)
        if len(subset) == 0:
            continue
        ax.scatter(
            subset["asymmetry_index"].to_list(),
            subset["avg_otp"].to_list(),
            color=color, label=mode, s=40, alpha=0.7, edgecolors="white", linewidths=0.5,
        )

    # Bus-only regression line
    bus = df.filter(pl.col("mode") == "BUS")
    x_vals = bus["asymmetry_index"].to_list()
    y_vals = bus["avg_otp"].to_list()
    if len(x_vals) > 1:
        reg = stats.linregress(x_vals, y_vals)
        x_line = [min(x_vals), max(x_vals)]
        y_line = [reg.slope * xi + reg.intercept for xi in x_line]
        r_bus = results.get("bus_pearson_r", 0)
        p_bus = results.get("bus_pearson_p", 1)
        ax.plot(x_line, y_line, color="#1e40af", linewidth=1.5, linestyle="--",
                label=f"BUS trend (r={r_bus:.3f}, p={p_bus:.3f})")

    ax.set_xlabel("Directional Asymmetry Index |IB - OB| / (IB + OB)")
    ax.set_ylabel("Average OTP")
    ax.set_title("Directional Trip Asymmetry vs On-Time Performance")
    ax.legend(fontsize=9)
    ax.set_ylim(0, 1)
    ax.set_xlim(-0.05, 1.05)

    fig.tight_layout()
    fig.savefig(OUT / "directional_asymmetry.png", bbox_inches="tight")
    plt.close(fig)
    print(f"  Chart saved to {OUT / 'directional_asymmetry.png'}")


def main() -> None:
    """Entry point: load data, analyze asymmetry, chart, and save."""
    print("=" * 60)
    print("Analysis 11: Directional Asymmetry")
    print("=" * 60)

    print("\nLoading data...")
    directional, avg_otp = load_data()
    print(f"  {len(directional)} directional records, {len(avg_otp)} routes with OTP")

    print("\nAnalyzing...")
    result, results = analyze(directional, avg_otp)
    if len(result) == 0:
        print("  No data to analyze.")
        return

    print(f"  {results['all_n']} routes analyzed (routes with both IB and OB data)")
    print(f"  All routes:  Pearson r = {results['all_pearson_r']:.4f} (p = {results['all_pearson_p']:.4f})")
    if "bus_pearson_r" in results:
        print(f"  Bus only:    Pearson r = {results['bus_pearson_r']:.4f} (p = {results['bus_pearson_p']:.4f})")
        print(f"               Spearman r = {results['bus_spearman_r']:.4f} (p = {results['bus_spearman_p']:.4f})")
        print(f"               n = {results['bus_n']} bus routes")

    top5 = result.head(5)
    print("\n  Most asymmetric routes:")
    for row in top5.iter_rows(named=True):
        print(f"    {row['route_id']:>5} - {row['route_name']}: "
              f"IB={row['ib_trips_wd']}, OB={row['ob_trips_wd']}, "
              f"asymmetry={row['asymmetry_index']:.3f}, OTP={row['avg_otp']:.1%}")

    print("\nSaving CSV...")
    result.write_csv(OUT / "directional_asymmetry.csv")
    print(f"  Saved to {OUT / 'directional_asymmetry.csv'}")

    print("\nGenerating chart...")
    make_chart(result, results)

    print("\nDone.")


if __name__ == "__main__":
    main()
