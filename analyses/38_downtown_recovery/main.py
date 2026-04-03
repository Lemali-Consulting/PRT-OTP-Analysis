"""Test whether downtown-dependent routes explain Pittsburgh's poor ridership recovery."""

import math

import numpy as np
import polars as pl
from scipy import stats

from prt_otp_analysis.common import DATA_DIR, PRE_COVID_BASELINE_YEAR, analysis_dir, classify_bus_route, correlate, get_db, phase, query_to_polars, run_analysis, save_chart, save_csv, setup_plotting, weighted_mean

OUT = analysis_dir(__file__)

# Downtown Pittsburgh centroid (matches analysis 33)
DT_LAT, DT_LON = 40.4406, -79.9959
DT_RADIUS_KM = 2.0

BASELINE_YEAR = PRE_COVID_BASELINE_YEAR

# Commuter-type subtypes (flyer, express, busway) vs local vs limited
COMMUTER_SUBTYPES = {"express", "flyer", "busway"}


def add_service_type(df: pl.DataFrame) -> pl.DataFrame:
    """Add subtype and service_type columns based on route_id naming conventions."""
    return df.with_columns(
        pl.col("route_id")
        .map_elements(classify_bus_route, return_dtype=pl.Utf8)
        .alias("subtype"),
    ).with_columns(
        pl.when(pl.col("subtype").is_in(COMMUTER_SUBTYPES))
        .then(pl.lit("Commuter/Express"))
        .when(pl.col("subtype") == "limited")
        .then(pl.lit("Limited"))
        .otherwise(pl.lit("Local"))
        .alias("service_type"),
    )


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
            weighted_index=weighted_mean("indexed", "avg_riders"),
            n_routes=pl.col("route_id").n_unique(),
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

    save_chart(fig, OUT / "recovery_trajectories.png", dpi=150)


def plot_trajectories_by_service_type(df: pl.DataFrame) -> None:
    """Plot recovery trajectories faceted by service type."""
    plt = setup_plotting()

    service_types = ["Local", "Limited", "Commuter/Express"]
    fig, axes = plt.subplots(1, 3, figsize=(18, 6), sharey=True)

    colors = {"High": "#dc2626", "Medium": "#f59e0b", "Low": "#2563eb"}

    for ax, stype in zip(axes, service_types):
        sub_df = df.filter(pl.col("service_type") == stype)
        n_routes = sub_df["route_id"].n_unique()

        monthly = (
            sub_df.group_by(["month", "dt_tercile"])
            .agg(
                weighted_index=weighted_mean("indexed", "avg_riders"),
                n_routes=pl.col("route_id").n_unique(),
            )
            .sort("month")
        )

        for tercile in ["High", "Medium", "Low"]:
            tsub = monthly.filter(pl.col("dt_tercile") == tercile).sort("month")
            if len(tsub) == 0:
                continue
            n = tsub["n_routes"].max()
            ax.plot(
                tsub["month"].to_list(),
                tsub["weighted_index"].to_list(),
                label=f"{tercile} (n={n})",
                color=colors[tercile],
                linewidth=2,
            )

        ax.axhline(100, color="gray", linewidth=0.8, linestyle="--", alpha=0.5)
        ax.axvspan("2020-03", "2020-06", alpha=0.08, color="gray")
        ticks = [m for m in monthly["month"].unique().sort().to_list() if m.endswith("-01")]
        ax.set_xticks(ticks)
        ax.set_xticklabels([m[:4] for m in ticks], rotation=0, fontsize=8)
        ax.set_title(f"{stype} routes (n={n_routes})")
        ax.legend(loc="lower right", fontsize=8)
        ax.set_ylim(0, 130)

    axes[0].set_ylabel("Indexed weekday ridership (2019 = 100)")
    fig.suptitle("Recovery by Downtown Dependence — Faceted by Service Type", fontsize=14)
    fig.tight_layout()
    save_chart(fig, OUT / "recovery_by_service_type.png", dpi=150)


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
        corr = correlate(route_df, "dt_share", "recovery_2024")
        slope, intercept = np.polyfit(x[mask], y[mask], 1)
        x_line = np.linspace(x[mask].min(), x[mask].max(), 100)
        ax.plot(x_line, slope * x_line + intercept, color="#dc2626", linewidth=1.5,
                linestyle="--", label=f"Spearman ρ = {corr['spearman_r']:.2f} (p = {corr['spearman_p']:.3f})")

    ax.axhline(100, color="gray", linewidth=0.8, linestyle="--", alpha=0.5)
    ax.set_xlabel("Downtown boardings share (% of route total)")
    ax.set_ylabel("2024 ridership as % of 2019")
    ax.set_title("Downtown Dependence vs. Ridership Recovery")
    ax.legend()

    save_chart(fig, OUT / "scatter_dt_share_vs_recovery.png", dpi=150)


def plot_scatter_by_service_type(route_df: pl.DataFrame) -> None:
    """Scatter plot of downtown share vs recovery, colored by service type."""
    plt = setup_plotting()

    fig, ax = plt.subplots(figsize=(9, 6))

    type_colors = {"Local": "#2563eb", "Limited": "#f59e0b", "Commuter/Express": "#dc2626"}

    for stype, color in type_colors.items():
        sub = route_df.filter(pl.col("service_type") == stype)
        if len(sub) == 0:
            continue
        x = sub["dt_share"].to_numpy() * 100
        y = sub["recovery_2024"].to_numpy()
        sizes = np.clip(sub["baseline_2019"].to_numpy() / 100, 10, 200)
        ax.scatter(
            x, y, s=sizes, alpha=0.6, color=color, edgecolors="white",
            linewidth=0.5, label=f"{stype} (n={len(sub)})",
        )

    ax.axhline(100, color="gray", linewidth=0.8, linestyle="--", alpha=0.5)
    ax.set_xlabel("Downtown boardings share (% of route total)")
    ax.set_ylabel("2024 ridership as % of 2019")
    ax.set_title("Downtown Dependence vs. Recovery — By Service Type")
    ax.legend()

    save_chart(fig, OUT / "scatter_by_service_type.png", dpi=150)


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


def run_service_type_analysis(route_df: pl.DataFrame) -> pl.DataFrame:
    """Test downtown dependence effect within each service type and overall with covariate."""
    results = []

    # Within-group Spearman correlations
    for stype in ["Local", "Limited", "Commuter/Express"]:
        sub = route_df.filter(pl.col("service_type") == stype).drop_nulls(
            subset=["dt_share", "recovery_2024"]
        )
        if len(sub) >= 5:
            r, p = stats.spearmanr(sub["dt_share"].to_numpy(), sub["recovery_2024"].to_numpy())
            results.append({
                "test": "Spearman (within group)",
                "group": stype,
                "n": len(sub),
                "statistic": round(r, 3),
                "p_value": round(p, 4),
                "significant": p < 0.05,
            })

    # Kruskal-Wallis across service types (is recovery different by type?)
    groups_by_type = {}
    for stype in ["Local", "Limited", "Commuter/Express"]:
        vals = route_df.filter(pl.col("service_type") == stype)["recovery_2024"].drop_nulls().to_list()
        if len(vals) >= 3:
            groups_by_type[stype] = vals

    if len(groups_by_type) >= 2:
        h_stat, kw_p = stats.kruskal(*groups_by_type.values())
        results.append({
            "test": "Kruskal-Wallis (service type)",
            "group": " vs ".join(groups_by_type.keys()),
            "n": sum(len(v) for v in groups_by_type.values()),
            "statistic": round(h_stat, 3),
            "p_value": round(kw_p, 4),
            "significant": kw_p < 0.05,
        })

    # Partial correlation: rank-based approach
    # Encode service_type as ordinal for partial correlation
    type_rank = {"Local": 0, "Limited": 1, "Commuter/Express": 2}
    valid_df = route_df.drop_nulls(subset=["dt_share", "recovery_2024"]).with_columns(
        pl.col("service_type").replace_strict(type_rank).cast(pl.Float64).alias("type_rank")
    )
    if len(valid_df) >= 10:
        # Partial Spearman: residualize both dt_share and recovery on service type rank
        dt_vals = valid_df["dt_share"].to_numpy()
        rec_vals = valid_df["recovery_2024"].to_numpy()
        type_vals = valid_df["type_rank"].to_numpy()

        # Rank-based residuals
        dt_resid = dt_vals - np.array([np.mean(dt_vals[type_vals == t]) for t in type_vals])
        rec_resid = rec_vals - np.array([np.mean(rec_vals[type_vals == t]) for t in type_vals])

        r_partial, p_partial = stats.spearmanr(dt_resid, rec_resid)
        results.append({
            "test": "Partial Spearman (controlling service type)",
            "group": "All",
            "n": len(valid_df),
            "statistic": round(r_partial, 3),
            "p_value": round(p_partial, 4),
            "significant": p_partial < 0.05,
        })

    return pl.DataFrame(results)


@run_analysis(38, "Downtown Recovery Gap")
def main() -> None:
    """Entry point."""

    # Step 1: Downtown-dependence scores + service type classification
    with phase("Computing downtown-dependence scores from stop-level data"):
        route_scores = compute_downtown_scores()
        route_scores = assign_terciles(route_scores)
        route_scores = add_service_type(route_scores)
        print(f"  {len(route_scores)} routes scored")
        for t in ["High", "Medium", "Low"]:
            sub = route_scores.filter(pl.col("dt_tercile") == t)
            print(f"  {t:6s}: n={len(sub)}, median dt_share={sub['dt_share'].median():.1%}")
        print("\n  Service type breakdown:")
        for stype in ["Local", "Limited", "Commuter/Express"]:
            sub = route_scores.filter(pl.col("service_type") == stype)
            if len(sub) > 0:
                print(f"  {stype:20s}: n={len(sub)}, median dt_share={sub['dt_share'].median():.1%}")

    # Step 2: Load ridership and compute recovery
    with phase("Loading monthly ridership"):
        ridership = load_ridership()
        df = compute_recovery(ridership, route_scores)
        # Merge tercile labels and service type
        df = df.join(
            route_scores.select("route_id", "dt_tercile", "service_type"),
            on="route_id",
            how="left",
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
        corr = correlate(route_df, "dt_share", "recovery_2024")
        print(f"\n  Spearman (dt_share vs recovery): ρ={corr['spearman_r']:.3f}, p={corr['spearman_p']:.4f}")

    # Step 4b: Service type analysis
    with phase("Analyzing recovery by service type"):
        print("\nRecovery by service type (2024 avg as % of 2019):")
        for stype in ["Local", "Limited", "Commuter/Express"]:
            sub = route_df.filter(pl.col("service_type") == stype)
            if len(sub) > 0:
                med = sub["recovery_2024"].median()
                mean = sub["recovery_2024"].mean()
                dt_med = sub["dt_share"].median()
                print(
                    f"  {stype:20s}: median recovery={med:.1f}%, "
                    f"mean={mean:.1f}%, median dt_share={dt_med:.1%}, n={len(sub)}"
                )

        service_type_results = run_service_type_analysis(route_df)
        print("\nService type statistical tests:")
        for row in service_type_results.iter_rows(named=True):
            sig = "*" if row["significant"] else ""
            print(
                f"  {row['test']:45s} {row['group']:20s} "
                f"n={row['n']:3d}, stat={row['statistic']:.3f}, "
                f"p={row['p_value']:.4f} {sig}"
            )

    # Step 5: Charts
    with phase("Generating charts"):
        plot_trajectories(df)
        plot_scatter(route_df)
        plot_trajectories_by_service_type(df)
        plot_scatter_by_service_type(route_df)

    # Step 6: Save CSV
    with phase("Saving CSVs"):
        sorted_route_df = route_df.sort("dt_share", descending=True)
        save_csv(sorted_route_df, OUT / "route_downtown_scores.csv")
        save_csv(test_results, OUT / "statistical_tests.csv")
        save_csv(service_type_results, OUT / "service_type_tests.csv")


if __name__ == "__main__":
    main()
