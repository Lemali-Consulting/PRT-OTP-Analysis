"""Analysis 30: Within-route panel -- does changing trip frequency predict OTP changes?"""

from pathlib import Path

import numpy as np
import polars as pl
from scipy import stats

from prt_otp_analysis.common import correlate, output_dir, print_done, print_header, query_to_polars, save_chart, save_csv, setup_plotting

HERE = Path(__file__).resolve().parent
OUT = output_dir(HERE)


def load_panel() -> pl.DataFrame:
    """Load the route-month panel: OTP joined with scheduled trips for the overlap period."""
    return query_to_polars("""
        SELECT o.route_id, o.month, o.otp,
               st.daily_trips,
               r.mode
        FROM otp_monthly o
        INNER JOIN scheduled_trips_monthly st
            ON o.route_id = st.route_id
            AND o.month = st.month
            AND st.day_type = 'WEEKDAY'
        LEFT JOIN routes r ON o.route_id = r.route_id
        ORDER BY o.route_id, o.month
    """)


def compute_deltas(df: pl.DataFrame) -> pl.DataFrame:
    """Compute month-over-month changes within each route."""
    df = df.sort(["route_id", "month"])

    df = df.with_columns(
        prev_otp=pl.col("otp").shift(1).over("route_id"),
        prev_trips=pl.col("daily_trips").shift(1).over("route_id"),
        prev_month=pl.col("month").shift(1).over("route_id"),
    )

    # Only keep rows where previous month exists (within same route)
    df = df.filter(pl.col("prev_otp").is_not_null())

    df = df.with_columns(
        delta_otp=pl.col("otp") - pl.col("prev_otp"),
        delta_trips=pl.col("daily_trips") - pl.col("prev_trips"),
    )

    return df


def detrend(df: pl.DataFrame) -> pl.DataFrame:
    """Remove system-wide monthly trend from delta_otp."""
    monthly_mean = (
        df.group_by("month")
        .agg(system_delta_otp=pl.col("delta_otp").mean())
    )
    df = df.join(monthly_mean, on="month")
    df = df.with_columns(
        detrended_delta_otp=pl.col("delta_otp") - pl.col("system_delta_otp"),
    )
    return df


def run_regression(x: list[float], y: list[float]) -> dict:
    """OLS regression of y on x, returning slope, intercept, r, p, se."""
    result = stats.linregress(x, y)
    return {
        "slope": result.slope,
        "intercept": result.intercept,
        "r": result.rvalue,
        "p": result.pvalue,
        "se": result.stderr,
        "n": len(x),
    }


def make_chart(df: pl.DataFrame, reg: dict) -> None:
    """Scatter: delta_trips vs detrended delta_otp with regression line."""
    plt = setup_plotting()
    fig, ax = plt.subplots(figsize=(10, 7))

    x = df["delta_trips"].to_numpy()
    y = df["detrended_delta_otp"].to_numpy()

    # Color by pre/post COVID
    pre_covid = df.filter(pl.col("month") < "2020-03")
    post_covid = df.filter(pl.col("month") >= "2020-03")

    ax.scatter(
        pre_covid["delta_trips"].to_list(),
        pre_covid["detrended_delta_otp"].to_list(),
        alpha=0.25, s=15, color="#2563eb", label=f"Pre-COVID (n={len(pre_covid)})",
    )
    ax.scatter(
        post_covid["delta_trips"].to_list(),
        post_covid["detrended_delta_otp"].to_list(),
        alpha=0.25, s=15, color="#e11d48", label=f"Post-COVID (n={len(post_covid)})",
    )

    # Regression line
    x_line = np.linspace(x.min(), x.max(), 100)
    y_line = reg["slope"] * x_line + reg["intercept"]
    ax.plot(x_line, y_line, color="black", linewidth=1.5,
            label=f"OLS: slope={reg['slope']:.5f}, p={reg['p']:.3f}")

    ax.axhline(0, color="gray", linewidth=0.5)
    ax.axvline(0, color="gray", linewidth=0.5)
    ax.set_xlabel("Month-over-Month Change in Daily Trips")
    ax.set_ylabel("Detrended Month-over-Month Change in OTP")
    ax.set_title("Service Level vs OTP: Within-Route Longitudinal Panel")
    ax.legend(fontsize=9)

    save_chart(fig, OUT / "service_level_scatter.png")


def main() -> None:
    """Entry point: build panel, compute deltas, regress, and chart."""
    print_header(30, "Service Level vs OTP Longitudinal")

    print("\nLoading panel data...")
    panel = load_panel()
    print(f"  {len(panel):,} route-month observations")
    print(f"  {panel['route_id'].n_unique()} routes, months: {panel['month'].min()} to {panel['month'].max()}")

    print("\nComputing month-over-month deltas...")
    df = compute_deltas(panel)
    print(f"  {len(df):,} delta observations (after dropping first month per route)")

    print("\nDetrending (removing system-wide monthly mean delta)...")
    df = detrend(df)

    # Save panel
    panel_df = df.select(
        "route_id", "month", "mode", "otp", "daily_trips",
        "delta_otp", "delta_trips", "detrended_delta_otp",
    )
    save_csv(panel_df, OUT / "service_level_panel.csv")

    # --- All routes ---
    print("\n--- All routes ---")
    x_all = df["delta_trips"].to_list()
    y_all = df["detrended_delta_otp"].to_list()

    reg_all = run_regression(x_all, y_all)
    print(f"  OLS: slope={reg_all['slope']:.5f} (SE={reg_all['se']:.5f}), r={reg_all['r']:.3f}, p={reg_all['p']:.4f}, n={reg_all['n']}")

    corr_all = correlate(df, "delta_trips", "detrended_delta_otp")
    r_s, p_s = corr_all["spearman_r"], corr_all["spearman_p"]
    print(f"  Spearman: rho={r_s:.3f}, p={p_s:.4f}")

    # --- Bus only ---
    bus = df.filter(pl.col("mode") == "BUS")
    print(f"\n--- Bus only (n={len(bus)}) ---")
    x_bus = bus["delta_trips"].to_list()
    y_bus = bus["detrended_delta_otp"].to_list()

    reg_bus = run_regression(x_bus, y_bus)
    print(f"  OLS: slope={reg_bus['slope']:.5f} (SE={reg_bus['se']:.5f}), r={reg_bus['r']:.3f}, p={reg_bus['p']:.4f}, n={reg_bus['n']}")

    corr_bus = correlate(bus, "delta_trips", "detrended_delta_otp")
    r_sb, p_sb = corr_bus["spearman_r"], corr_bus["spearman_p"]
    print(f"  Spearman: rho={r_sb:.3f}, p={p_sb:.4f}")

    # --- Pre vs post COVID ---
    pre = df.filter(pl.col("month") < "2020-03")
    post = df.filter(pl.col("month") >= "2020-03")
    print(f"\n--- Pre-COVID (n={len(pre)}) ---")
    if len(pre) > 10:
        reg_pre = run_regression(pre["delta_trips"].to_list(), pre["detrended_delta_otp"].to_list())
        print(f"  OLS: slope={reg_pre['slope']:.5f}, r={reg_pre['r']:.3f}, p={reg_pre['p']:.4f}")

    print(f"\n--- Post-COVID (n={len(post)}) ---")
    if len(post) > 10:
        reg_post = run_regression(post["delta_trips"].to_list(), post["detrended_delta_otp"].to_list())
        print(f"  OLS: slope={reg_post['slope']:.5f}, r={reg_post['r']:.3f}, p={reg_post['p']:.4f}")

    # Summary CSV
    summary = pl.DataFrame([
        {"group": "all", "n": reg_all["n"], "slope": reg_all["slope"], "se": reg_all["se"],
         "pearson_r": reg_all["r"], "pearson_p": reg_all["p"], "spearman_rho": r_s, "spearman_p": p_s},
        {"group": "bus_only", "n": reg_bus["n"], "slope": reg_bus["slope"], "se": reg_bus["se"],
         "pearson_r": reg_bus["r"], "pearson_p": reg_bus["p"], "spearman_rho": r_sb, "spearman_p": p_sb},
    ])
    save_csv(summary, OUT / "service_level_summary.csv")

    print("\nGenerating chart...")
    make_chart(df, reg_all)

    print_done()


if __name__ == "__main__":
    main()
