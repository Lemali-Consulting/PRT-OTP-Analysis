"""Test whether downtown-dependent routes explain Pittsburgh's poor ridership recovery."""

import math
from pathlib import Path

import numpy as np
import polars as pl
from scipy import stats

from prt_otp_analysis.common import PRE_COVID_BASELINE_YEAR, get_db, output_dir, query_to_polars, setup_plotting

HERE = Path(__file__).resolve().parent
OUT = output_dir(HERE)
DATA_DIR = HERE.parents[1] / "data"

# Downtown Pittsburgh centroid (matches analysis 33)
DT_LAT, DT_LON = 40.4406, -79.9959
DT_RADIUS_KM = 2.0

BASELINE_YEAR = PRE_COVID_BASELINE_YEAR


def haversine_km(lat: float, lon: float) -> float:
    """Return distance in km from downtown centroid."""
    R = 6371
    rlat1, rlat2 = math.radians(DT_LAT), math.radians(lat)
    dlat = math.radians(lat - DT_LAT)
    dlon = math.radians(lon - DT_LON)
    a = math.sin(dlat / 2) ** 2 + math.cos(rlat1) * math.cos(rlat2) * math.sin(dlon / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def compute_downtown_scores() -> pl.DataFrame:
    """Compute downtown-dependence score for each route using stop-level data."""
    csv_path = DATA_DIR / "bus-stop-usage" / "wprdc_stop_data.csv"
    df = pl.read_csv(csv_path, null_values=["NA", ""])

    # Pre-pandemic weekday boardings by stop and route
    pre = df.filter(
        (pl.col("time_period") == "Pre-pandemic")
        & (pl.col("serviceday") == "Weekday")
    )
    stop_route = (
        pre.group_by(["stop_id", "route_name", "latitude", "longitude"])
        .agg(pl.col("avg_ons").mean().alias("avg_boardings"))
        .drop_nulls(subset=["latitude", "longitude", "avg_boardings"])
    )

    # Classify stops as downtown or not
    dists = [
        haversine_km(lat, lon)
        for lat, lon in zip(
            stop_route["latitude"].to_list(), stop_route["longitude"].to_list()
        )
    ]
    stop_route = stop_route.with_columns(
        pl.Series("dist_km", dists),
    ).with_columns(
        (pl.col("dist_km") < DT_RADIUS_KM).alias("is_downtown"),
    )

    # Downtown boardings share per route
    stop_route = stop_route.with_columns(
        (pl.col("avg_boardings") * pl.col("is_downtown").cast(pl.Float64)).alias(
            "dt_boardings"
        )
    )
    route_scores = (
        stop_route.group_by("route_name")
        .agg(
            pl.col("avg_boardings").sum().alias("total_boardings"),
            pl.col("dt_boardings").sum().alias("dt_boardings"),
            pl.col("stop_id").n_unique().alias("n_stops"),
        )
        .with_columns(
            (pl.col("dt_boardings") / pl.col("total_boardings")).alias("dt_share")
        )
        .rename({"route_name": "route_id"})
        .sort("dt_share", descending=True)
    )
    return route_scores


def load_ridership() -> pl.DataFrame:
    """Load monthly weekday ridership from database."""
    return query_to_polars(
        "SELECT route_id, month, avg_riders, route_name "
        "FROM ridership_monthly WHERE day_type = 'WEEKDAY'"
    )


def compute_recovery(
    ridership: pl.DataFrame, route_scores: pl.DataFrame
) -> pl.DataFrame:
    """Compute 2019-indexed ridership and merge with downtown scores."""
    # Compute 2019 baseline per route
    baseline = (
        ridership.filter(pl.col("month").str.starts_with(BASELINE_YEAR))
        .group_by("route_id")
        .agg(pl.col("avg_riders").mean().alias("baseline_2019"))
    )

    # Join baseline and compute index
    df = ridership.join(baseline, on="route_id", how="inner")
    df = df.filter(pl.col("baseline_2019") > 0).with_columns(
        (pl.col("avg_riders") / pl.col("baseline_2019") * 100).alias("indexed")
    )

    # Merge downtown scores
    df = df.join(
        route_scores.select("route_id", "dt_share", "total_boardings"),
        on="route_id",
        how="inner",
    )
    return df


def assign_terciles(route_scores: pl.DataFrame) -> pl.DataFrame:
    """Assign downtown-dependence terciles."""
    thirds = route_scores["dt_share"].quantile(1 / 3), route_scores["dt_share"].quantile(2 / 3)
    return route_scores.with_columns(
        pl.when(pl.col("dt_share") <= thirds[0])
        .then(pl.lit("Low"))
        .when(pl.col("dt_share") <= thirds[1])
        .then(pl.lit("Medium"))
        .otherwise(pl.lit("High"))
        .alias("dt_tercile")
    )


def plot_trajectories(df: pl.DataFrame) -> None:
    """Plot recovery trajectories by downtown-dependence tercile."""
    plt = setup_plotting()

    # Aggregate: ridership-weighted mean index per tercile per month
    monthly = (
        df.group_by(["month", "dt_tercile"])
        .agg(
            (pl.col("indexed") * pl.col("avg_riders")).sum().alias("weighted_sum"),
            pl.col("avg_riders").sum().alias("total_riders"),
            pl.col("route_id").n_unique().alias("n_routes"),
        )
        .with_columns(
            (pl.col("weighted_sum") / pl.col("total_riders")).alias("weighted_index")
        )
        .sort("month")
    )

    fig, ax = plt.subplots(figsize=(12, 6))

    colors = {"High": "#dc2626", "Medium": "#f59e0b", "Low": "#2563eb"}
    for tercile in ["High", "Medium", "Low"]:
        sub = monthly.filter(pl.col("dt_tercile") == tercile).sort("month")
        n = sub["n_routes"].max()
        ax.plot(
            sub["month"].to_list(),
            sub["weighted_index"].to_list(),
            label=f"{tercile} downtown dependence (n={n})",
            color=colors[tercile],
            linewidth=2,
        )

    ax.axhline(100, color="gray", linewidth=0.8, linestyle="--", alpha=0.5)
    ax.axvspan("2020-03", "2020-06", alpha=0.08, color="gray", label="Initial lockdown")

    # Thin x-axis labels
    ticks = [m for m in monthly["month"].unique().sort().to_list() if m.endswith("-01")]
    ax.set_xticks(ticks)
    ax.set_xticklabels([m[:4] for m in ticks], rotation=0)

    ax.set_ylabel("Indexed weekday ridership (2019 = 100)")
    ax.set_xlabel("")
    ax.set_title("Ridership Recovery by Downtown Dependence")
    ax.legend(loc="lower right")
    ax.set_ylim(0, 130)

    fig.tight_layout()
    fig.savefig(OUT / "recovery_trajectories.png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved {OUT / 'recovery_trajectories.png'}")


def plot_scatter(route_df: pl.DataFrame) -> None:
    """Scatter plot of downtown share vs 2024 recovery."""
    plt = setup_plotting()

    fig, ax = plt.subplots(figsize=(8, 6))

    x = route_df["dt_share"].to_numpy() * 100
    y = route_df["recovery_2024"].to_numpy()
    sizes = np.clip(route_df["baseline_2019"].to_numpy() / 100, 10, 200)

    ax.scatter(x, y, s=sizes, alpha=0.5, color="#3b82f6", edgecolors="white", linewidth=0.5)

    # Regression line
    mask = np.isfinite(x) & np.isfinite(y)
    if mask.sum() > 5:
        rho, p_val = stats.spearmanr(x[mask], y[mask])
        slope, intercept = np.polyfit(x[mask], y[mask], 1)
        x_line = np.linspace(x[mask].min(), x[mask].max(), 100)
        ax.plot(x_line, slope * x_line + intercept, color="#dc2626", linewidth=1.5,
                linestyle="--", label=f"Spearman ρ = {rho:.2f} (p = {p_val:.3f})")

    ax.axhline(100, color="gray", linewidth=0.8, linestyle="--", alpha=0.5)
    ax.set_xlabel("Downtown boardings share (% of route total)")
    ax.set_ylabel("2024 ridership as % of 2019")
    ax.set_title("Downtown Dependence vs. Ridership Recovery")
    ax.legend()

    fig.tight_layout()
    fig.savefig(OUT / "scatter_dt_share_vs_recovery.png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved {OUT / 'scatter_dt_share_vs_recovery.png'}")


def run_tests(route_df: pl.DataFrame) -> pl.DataFrame:
    """Kruskal-Wallis and pairwise Mann-Whitney tests on recovery by tercile."""
    results = []

    groups = {}
    for t in ["High", "Medium", "Low"]:
        vals = route_df.filter(pl.col("dt_tercile") == t)["recovery_2024"].drop_nulls().to_list()
        groups[t] = vals

    if all(len(v) >= 3 for v in groups.values()):
        h_stat, kw_p = stats.kruskal(*groups.values())
        results.append({
            "test": "Kruskal-Wallis",
            "comparison": "High vs Medium vs Low",
            "statistic": round(h_stat, 3),
            "p_value": round(kw_p, 4),
            "significant": kw_p < 0.05,
        })

        pairs = [("High", "Medium"), ("High", "Low"), ("Medium", "Low")]
        for a, b in pairs:
            u_stat, mw_p = stats.mannwhitneyu(groups[a], groups[b], alternative="two-sided")
            adj_p = min(mw_p * 3, 1.0)
            results.append({
                "test": "Mann-Whitney (Bonferroni)",
                "comparison": f"{a} vs {b}",
                "statistic": round(u_stat, 1),
                "p_value": round(adj_p, 4),
                "significant": adj_p < 0.05,
            })

    return pl.DataFrame(results)


def main() -> None:
    """Entry point."""
    print("=" * 60)
    print("Analysis 38: Downtown Recovery Gap")
    print("=" * 60)

    # Step 1: Downtown-dependence scores
    print("\nComputing downtown-dependence scores from stop-level data...")
    route_scores = compute_downtown_scores()
    route_scores = assign_terciles(route_scores)
    print(f"  {len(route_scores)} routes scored")
    for t in ["High", "Medium", "Low"]:
        sub = route_scores.filter(pl.col("dt_tercile") == t)
        print(f"  {t:6s}: n={len(sub)}, median dt_share={sub['dt_share'].median():.1%}")

    # Step 2: Load ridership and compute recovery
    print("\nLoading monthly ridership...")
    ridership = load_ridership()
    df = compute_recovery(ridership, route_scores)
    # Merge tercile labels
    df = df.join(
        route_scores.select("route_id", "dt_tercile"), on="route_id", how="left"
    )
    print(f"  {df['route_id'].n_unique()} routes with both ridership and downtown scores")

    # Step 3: Compute 2024 recovery ratio per route
    recovery_2024 = (
        df.filter(pl.col("month").str.starts_with("2024"))
        .group_by("route_id")
        .agg(pl.col("indexed").mean().alias("recovery_2024"))
    )
    route_df = route_scores.join(recovery_2024, on="route_id", how="inner")
    # Also get baseline for scatter sizing
    baseline = (
        ridership.filter(pl.col("month").str.starts_with(BASELINE_YEAR))
        .group_by("route_id")
        .agg(pl.col("avg_riders").mean().alias("baseline_2019"))
    )
    route_df = route_df.join(baseline, on="route_id", how="inner")

    print("\nRecovery by tercile (2024 avg as % of 2019):")
    for t in ["High", "Medium", "Low"]:
        sub = route_df.filter(pl.col("dt_tercile") == t)
        med = sub["recovery_2024"].median()
        mean = sub["recovery_2024"].mean()
        print(f"  {t:6s}: median={med:.1f}%, mean={mean:.1f}%, n={len(sub)}")

    # Step 4: Statistical tests
    print("\nStatistical tests:")
    test_results = run_tests(route_df)
    for row in test_results.iter_rows(named=True):
        sig = "*" if row["significant"] else ""
        print(f"  {row['test']:30s} {row['comparison']:25s} "
              f"stat={row['statistic']:.3f}, p={row['p_value']:.4f} {sig}")

    # Spearman correlation (continuous)
    x = route_df["dt_share"].to_numpy()
    y = route_df["recovery_2024"].to_numpy()
    mask = np.isfinite(x) & np.isfinite(y)
    rho, p_val = stats.spearmanr(x[mask], y[mask])
    print(f"\n  Spearman (dt_share vs recovery): ρ={rho:.3f}, p={p_val:.4f}")

    # Step 5: Charts
    print("\nGenerating charts...")
    plot_trajectories(df)
    plot_scatter(route_df)

    # Step 6: Save CSV
    route_df.sort("dt_share", descending=True).write_csv(
        OUT / "route_downtown_scores.csv"
    )
    test_results.write_csv(OUT / "statistical_tests.csv")
    print(f"  Saved {OUT / 'route_downtown_scores.csv'}")
    print(f"  Saved {OUT / 'statistical_tests.csv'}")

    print("\nDone.")


if __name__ == "__main__":
    main()
