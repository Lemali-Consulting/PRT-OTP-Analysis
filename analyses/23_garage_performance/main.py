"""Analysis 23: Compare OTP and ridership across PRT garages to surface operational differences."""

import math
from pathlib import Path

import numpy as np
import polars as pl
from scipy import stats

from prt_otp_analysis.common import output_dir, query_to_polars, setup_plotting

HERE = Path(__file__).resolve().parent
OUT = output_dir(HERE)

MIN_MONTHS = 12


def load_data() -> pl.DataFrame:
    """Load OTP joined with garage assignment and ridership."""
    df = query_to_polars("""
        SELECT o.route_id, o.month, o.otp,
               r.avg_riders, r.current_garage,
               rt.mode
        FROM otp_monthly o
        JOIN ridership_monthly r
            ON o.route_id = r.route_id AND o.month = r.month
            AND r.day_type = 'WEEKDAY'
        JOIN routes rt ON o.route_id = rt.route_id
        WHERE r.current_garage IS NOT NULL
    """)

    # Filter to routes with enough data
    route_counts = df.group_by("route_id").agg(pl.col("month").count().alias("n"))
    keep = route_counts.filter(pl.col("n") >= MIN_MONTHS)["route_id"].to_list()
    df = df.filter(pl.col("route_id").is_in(keep))

    return df


def route_level_summary(df: pl.DataFrame) -> pl.DataFrame:
    """Compute route-level average OTP and ridership with garage assignment."""
    return (
        df.group_by("route_id", "current_garage", "mode")
        .agg(
            avg_otp=pl.col("otp").mean(),
            avg_riders=pl.col("avg_riders").mean(),
            n_months=pl.col("month").count(),
        )
        .sort("current_garage", "avg_otp")
    )


def garage_summary(route_df: pl.DataFrame) -> pl.DataFrame:
    """Compute garage-level summary statistics."""
    return (
        route_df.group_by("current_garage")
        .agg(
            n_routes=pl.col("route_id").count(),
            mean_otp=pl.col("avg_otp").mean(),
            median_otp=pl.col("avg_otp").median(),
            std_otp=pl.col("avg_otp").std(),
            min_otp=pl.col("avg_otp").min(),
            max_otp=pl.col("avg_otp").max(),
            total_riders=pl.col("avg_riders").sum(),
            weighted_otp=(
                (pl.col("avg_otp") * pl.col("avg_riders")).sum() / pl.col("avg_riders").sum()
            ),
        )
        .sort("mean_otp", descending=True)
    )


def monthly_by_garage(df: pl.DataFrame) -> pl.DataFrame:
    """Compute monthly ridership-weighted OTP per garage."""
    return (
        df.group_by("current_garage", "month")
        .agg(
            weighted_otp=(
                (pl.col("otp") * pl.col("avg_riders")).sum() / pl.col("avg_riders").sum()
            ),
            unweighted_otp=pl.col("otp").mean(),
            total_riders=pl.col("avg_riders").sum(),
            n_routes=pl.col("route_id").n_unique(),
        )
        .sort("current_garage", "month")
    )


def statistical_tests(route_df: pl.DataFrame) -> dict:
    """Run Kruskal-Wallis and pairwise Mann-Whitney tests across garages."""
    results = {}

    # All routes
    garages = sorted(route_df["current_garage"].unique().to_list())
    groups = []
    garage_names = []
    for g in garages:
        vals = route_df.filter(pl.col("current_garage") == g)["avg_otp"].to_list()
        if len(vals) >= 3:
            groups.append(vals)
            garage_names.append(g)

    if len(groups) >= 2:
        h, p = stats.kruskal(*groups)
        results["kruskal_h_all"] = h
        results["kruskal_p_all"] = p
        results["garages_tested_all"] = garage_names

    # Bus-only
    bus_df = route_df.filter(pl.col("mode") == "BUS")
    bus_groups = []
    bus_names = []
    for g in garages:
        vals = bus_df.filter(pl.col("current_garage") == g)["avg_otp"].to_list()
        if len(vals) >= 3:
            bus_groups.append(vals)
            bus_names.append(g)

    if len(bus_groups) >= 2:
        h, p = stats.kruskal(*bus_groups)
        results["kruskal_h_bus"] = h
        results["kruskal_p_bus"] = p
        results["garages_tested_bus"] = bus_names

    return results


def make_trend_chart(monthly: pl.DataFrame) -> None:
    """Plot monthly ridership-weighted OTP by garage."""
    plt = setup_plotting()
    fig, ax = plt.subplots(figsize=(14, 6))

    garage_colors = {
        "Ross": "#2563eb",
        "Collier": "#16a34a",
        "East Liberty": "#e11d48",
        "West Mifflin": "#f59e0b",
        "South Hills Village": "#8b5cf6",
        "Incline": "#9ca3af",
    }

    # Build x-axis from all months
    all_months = sorted(monthly["month"].unique().to_list())
    month_to_x = {m: i for i, m in enumerate(all_months)}
    tick_positions = [i for i, m in enumerate(all_months) if m.endswith("-01")]
    tick_labels = [all_months[i][:4] for i in tick_positions]

    for garage in sorted(monthly["current_garage"].unique().to_list()):
        gdf = monthly.filter(pl.col("current_garage") == garage).sort("month")
        months = gdf["month"].to_list()
        x = [month_to_x[m] for m in months]
        y = gdf["weighted_otp"].to_list()
        color = garage_colors.get(garage, "#9ca3af")
        ax.plot(x, y, color=color, linewidth=1.5, label=garage, alpha=0.8)

    if "2020-03" in all_months:
        covid_idx = month_to_x["2020-03"]
        ax.axvline(covid_idx, color="#ef4444", linestyle=":", alpha=0.5)

    ax.set_ylabel("Ridership-Weighted OTP")
    ax.set_xlabel("Month")
    ax.set_title("Monthly OTP by Garage (Ridership-Weighted)")
    ax.set_xticks(tick_positions)
    ax.set_xticklabels(tick_labels)
    ax.legend(loc="lower left", fontsize=8)
    ax.set_ylim(0.45, 0.90)

    fig.tight_layout()
    fig.savefig(OUT / "garage_otp_trend.png", bbox_inches="tight")
    plt.close(fig)
    print(f"  Chart saved to {OUT / 'garage_otp_trend.png'}")


def make_boxplot(route_df: pl.DataFrame) -> None:
    """Box plot of route-level OTP by garage, all routes and bus-only."""
    plt = setup_plotting()
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

    garage_colors = ["#2563eb", "#16a34a", "#e11d48", "#f59e0b", "#8b5cf6", "#9ca3af"]

    for ax, title, filt in [
        (ax1, "All Routes", route_df),
        (ax2, "Bus Only", route_df.filter(pl.col("mode") == "BUS")),
    ]:
        garages = sorted(filt["current_garage"].unique().to_list())
        data = []
        labels = []
        for g in garages:
            vals = filt.filter(pl.col("current_garage") == g)["avg_otp"].to_list()
            if len(vals) >= 2:
                data.append(vals)
                labels.append(f"{g}\n(n={len(vals)})")

        bp = ax.boxplot(data, tick_labels=labels, patch_artist=True)
        for patch, color in zip(bp["boxes"], garage_colors):
            patch.set_facecolor(color)
            patch.set_alpha(0.6)
        ax.set_ylabel("Route-Level Average OTP")
        ax.set_title(title)
        ax.tick_params(axis="x", labelsize=8)

    fig.suptitle("OTP Distribution by Garage", fontsize=13, y=1.02)
    fig.tight_layout()
    fig.savefig(OUT / "garage_boxplot.png", bbox_inches="tight")
    plt.close(fig)
    print(f"  Chart saved to {OUT / 'garage_boxplot.png'}")


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Return the great-circle distance in km between two lat/lon points."""
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2
         + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2))
         * math.sin(dlon / 2) ** 2)
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def compute_span(lats: list[float], lons: list[float]) -> float:
    """Return the max pairwise haversine distance (km) among a set of points."""
    max_dist = 0.0
    n = len(lats)
    for i in range(n):
        for j in range(i + 1, n):
            d = haversine_km(lats[i], lons[i], lats[j], lons[j])
            if d > max_dist:
                max_dist = d
    return max_dist


def fit_ols(y: np.ndarray, X_raw: np.ndarray, feature_names: list[str]) -> dict:
    """Fit OLS regression and return results dict."""
    n, k = X_raw.shape
    X = np.column_stack([np.ones(n), X_raw])
    beta, _, _, _ = np.linalg.lstsq(X, y, rcond=None)
    y_hat = X @ beta
    residuals = y - y_hat
    ss_res = np.sum(residuals ** 2)
    ss_tot = np.sum((y - np.mean(y)) ** 2)
    r_squared = 1 - ss_res / ss_tot
    adj_r_squared = 1 - (1 - r_squared) * (n - 1) / (n - k - 1)
    mse = ss_res / (n - k - 1)
    XtX_inv = np.linalg.pinv(X.T @ X)
    se = np.sqrt(np.diag(XtX_inv) * mse)
    t_vals = beta / se
    p_vals = [2 * (1 - stats.t.cdf(abs(t), df=n - k - 1)) for t in t_vals]
    return {
        "r_squared": r_squared,
        "adj_r_squared": adj_r_squared,
        "n": n, "k": k,
        "features": ["intercept"] + feature_names,
        "coefficients": beta.tolist(),
        "std_errors": se.tolist(),
        "p_values": p_vals,
    }


def load_structural_features() -> pl.DataFrame:
    """Load route-level structural features (stop count, span) for the controlled model."""
    stop_counts = query_to_polars("""
        SELECT route_id, COUNT(DISTINCT stop_id) AS stop_count
        FROM route_stops GROUP BY route_id
    """)
    stops_by_route = query_to_polars("""
        SELECT rs.route_id, s.lat, s.lon
        FROM route_stops rs
        JOIN stops s ON rs.stop_id = s.stop_id
        WHERE s.lat IS NOT NULL AND s.lon IS NOT NULL
    """)
    spans = []
    for route_id in stops_by_route["route_id"].unique().sort().to_list():
        subset = stops_by_route.filter(pl.col("route_id") == route_id)
        span_km = compute_span(subset["lat"].to_list(), subset["lon"].to_list())
        spans.append({"route_id": route_id, "span_km": span_km})
    span_df = pl.DataFrame(spans)

    return stop_counts.join(span_df, on="route_id", how="inner")


def controlled_garage_test(route_df: pl.DataFrame) -> dict:
    """Fit OLS models with and without garage dummies, controlling for stop count, span, and mode."""
    struct = load_structural_features()
    df = route_df.join(struct, on="route_id", how="inner")
    df = df.with_columns(
        pl.when(pl.col("mode") == "RAIL").then(1.0).otherwise(0.0).alias("is_rail"),
    )

    # Bus-only analysis (drop rail and South Hills Village)
    bus_df = df.filter(pl.col("mode") == "BUS").drop_nulls(subset=["stop_count", "span_km"])

    # Reference garage = East Liberty (largest, excluded from dummies)
    bus_garages = sorted(set(bus_df["current_garage"].to_list()) - {"East Liberty"})
    for g in bus_garages:
        col_name = f"garage_{g.replace(' ', '_')}"
        bus_df = bus_df.with_columns(
            pl.when(pl.col("current_garage") == g).then(1.0).otherwise(0.0).alias(col_name),
        )

    y = bus_df["avg_otp"].to_numpy()

    # Model 1: structural only (stop_count, span_km)
    base_features = ["stop_count", "span_km"]
    X_base = np.column_stack([bus_df[f].to_numpy().astype(float) for f in base_features])
    base_results = fit_ols(y, X_base, base_features)

    # Model 2: structural + garage dummies
    garage_cols = [f"garage_{g.replace(' ', '_')}" for g in bus_garages]
    full_features = base_features + garage_cols
    X_full = np.column_stack([bus_df[f].to_numpy().astype(float) for f in full_features])
    full_results = fit_ols(y, X_full, full_features)

    # F-test for garage dummies (nested model comparison)
    n = len(y)
    k_base = len(base_features)
    k_full = len(full_features)
    k_diff = k_full - k_base
    ss_res_base = np.sum((y - np.mean(y)) ** 2) * (1 - base_results["r_squared"])
    ss_res_full = np.sum((y - np.mean(y)) ** 2) * (1 - full_results["r_squared"])
    f_stat = ((ss_res_base - ss_res_full) / k_diff) / (ss_res_full / (n - k_full - 1))
    f_p = 1 - stats.f.cdf(f_stat, k_diff, n - k_full - 1)

    return {
        "base_results": base_results,
        "full_results": full_results,
        "f_stat": f_stat,
        "f_p": f_p,
        "k_diff": k_diff,
        "n_bus": n,
        "bus_garages": bus_garages,
        "garage_cols": garage_cols,
    }


def main() -> None:
    """Entry point: load, summarize, test, chart, and save."""
    print("=" * 60)
    print("Analysis 23: Garage-Level Performance")
    print("=" * 60)

    print("\nLoading data...")
    df = load_data()
    n_routes = df["route_id"].n_unique()
    print(f"  {len(df):,} route-month observations ({n_routes} routes)")

    print("\nComputing route-level summaries...")
    route_df = route_level_summary(df)
    gsummary = garage_summary(route_df)

    print("\n  Garage summary:")
    print(f"  {'Garage':<22} {'Routes':>6} {'Mean OTP':>9} {'Wt OTP':>9} {'Riders':>10}")
    for row in gsummary.iter_rows(named=True):
        print(f"  {row['current_garage']:<22} {row['n_routes']:>6} "
              f"{row['mean_otp']:>9.1%} {row['weighted_otp']:>9.1%} "
              f"{row['total_riders']:>10,.0f}")

    print("\nStatistical tests...")
    test_results = statistical_tests(route_df)

    if "kruskal_h_all" in test_results:
        print(f"  Kruskal-Wallis (all routes): H = {test_results['kruskal_h_all']:.3f}, "
              f"p = {test_results['kruskal_p_all']:.4f}")
        print(f"    Garages tested: {test_results['garages_tested_all']}")

    if "kruskal_h_bus" in test_results:
        print(f"  Kruskal-Wallis (bus only):   H = {test_results['kruskal_h_bus']:.3f}, "
              f"p = {test_results['kruskal_p_bus']:.4f}")
        print(f"    Garages tested: {test_results['garages_tested_bus']}")

    print("\nControlled analysis (OLS with structural controls)...")
    ctrl = controlled_garage_test(route_df)
    base = ctrl["base_results"]
    full = ctrl["full_results"]
    print(f"\n  Bus-only models (n = {ctrl['n_bus']}, reference garage = East Liberty):")
    print(f"  Base model (stop_count + span): R² = {base['r_squared']:.4f}, "
          f"Adj R² = {base['adj_r_squared']:.4f}")
    print(f"  Full model (+ garage dummies):  R² = {full['r_squared']:.4f}, "
          f"Adj R² = {full['adj_r_squared']:.4f}")
    print(f"  R² change: +{full['r_squared'] - base['r_squared']:.4f}")
    print(f"\n  F-test for garage dummies: F = {ctrl['f_stat']:.3f}, "
          f"p = {ctrl['f_p']:.4f} (df = {ctrl['k_diff']}, {ctrl['n_bus'] - full['k'] - 1})")
    if ctrl['f_p'] < 0.05:
        print("  => Garage dummies ARE significant after controlling for route structure.")
    else:
        print("  => Garage dummies are NOT significant after controlling for route structure.")

    # Print garage coefficients
    print(f"\n  {'Feature':<25s} {'Coeff':>10s} {'Std Err':>10s} {'p-value':>10s}")
    print(f"  {'-'*55}")
    for i, feat in enumerate(full["features"]):
        coeff = full["coefficients"][i]
        se = full["std_errors"][i]
        p = full["p_values"][i]
        sig = "***" if p < 0.001 else "**" if p < 0.01 else "*" if p < 0.05 else ""
        print(f"  {feat:<25s} {coeff:>10.6f} {se:>10.6f} {p:>10.4f} {sig}")

    print("\nComputing monthly trends...")
    monthly = monthly_by_garage(df)

    print("\nSaving CSVs...")
    gsummary.write_csv(OUT / "garage_summary.csv")
    print(f"  {OUT / 'garage_summary.csv'}")
    route_df.write_csv(OUT / "garage_route_detail.csv")
    print(f"  {OUT / 'garage_route_detail.csv'}")
    monthly.write_csv(OUT / "garage_monthly.csv")
    print(f"  {OUT / 'garage_monthly.csv'}")

    print("\nGenerating charts...")
    make_trend_chart(monthly)
    make_boxplot(route_df)

    print("\nDone.")


if __name__ == "__main__":
    main()
