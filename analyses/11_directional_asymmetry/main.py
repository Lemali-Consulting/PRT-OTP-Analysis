"""Analysis of inbound vs outbound trip asymmetry and its correlation with OTP."""

import math

import polars as pl

from prt_otp_analysis.common import analysis_dir, correlate_by_mode, mode_scatter, phase, query_to_polars, run_analysis, save_chart, save_csv, setup_plotting

OUT = analysis_dir(__file__)


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
    results = correlate_by_mode(result, "asymmetry_index", "avg_otp")

    return result.sort("asymmetry_index", descending=True), results


def make_chart(df: pl.DataFrame) -> None:
    """Generate scatter plot of directional asymmetry vs OTP."""
    plt = setup_plotting()
    fig, ax = plt.subplots(figsize=(10, 7))
    mode_scatter(ax, df, "asymmetry_index", "avg_otp")
    ax.set_xlabel("Directional Asymmetry Index |IB - OB| / (IB + OB)")
    ax.set_ylabel("Average OTP")
    ax.set_title("Directional Trip Asymmetry vs On-Time Performance")
    ax.legend(fontsize=9)
    ax.set_ylim(0, 1)
    ax.set_xlim(-0.05, 1.05)
    save_chart(fig, OUT / "directional_asymmetry.png")


@run_analysis(11, "Directional Asymmetry")
def main() -> None:
    """Entry point: load data, analyze asymmetry, chart, and save."""
    with phase("Loading data"):
        directional, avg_otp = load_data()
        print(f"  {len(directional)} directional records, {len(avg_otp)} routes with OTP")

    with phase("Analyzing"):
        result, results = analyze(directional, avg_otp)
        if len(result) == 0:
            print("  No data to analyze.")
            return

        print(f"  {results['all_n']} routes analyzed (routes with both IB and OB data)")
        print(f"  All routes:  Pearson r = {results['all_pearson_r']:.4f} (p = {results['all_pearson_p']:.4f})")
        if not math.isnan(results["bus_pearson_r"]):
            print(f"  Bus only:    Pearson r = {results['bus_pearson_r']:.4f} (p = {results['bus_pearson_p']:.4f})")
            print(f"               Spearman r = {results['bus_spearman_r']:.4f} (p = {results['bus_spearman_p']:.4f})")
            print(f"               n = {results['bus_n']} bus routes")

        top5 = result.head(5)
        print("\n  Most asymmetric routes:")
        for row in top5.iter_rows(named=True):
            print(f"    {row['route_id']:>5} - {row['route_name']}: "
                  f"IB={row['ib_trips_wd']}, OB={row['ob_trips_wd']}, "
                  f"asymmetry={row['asymmetry_index']:.3f}, OTP={row['avg_otp']:.1%}")

        save_csv(result, OUT / "directional_asymmetry.csv")

    with phase("Generating chart"):
        make_chart(result)


if __name__ == "__main__":
    main()
