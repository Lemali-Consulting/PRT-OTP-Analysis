"""Analysis 46: test whether denser Allegheny County census tracts sit closer
to PRT transit stops than sparsely populated ones."""

from pathlib import Path

import geopandas as gpd
import polars as pl
from scipy import stats

from prt_otp_analysis.common import (
    output_dir,
    phase,
    query_to_polars,
    run_analysis,
    save_chart,
    save_csv,
    setup_plotting,
)
from prt_otp_analysis.walksheds import CRS_GEO, CRS_M, load_tracts

HERE = Path(__file__).resolve().parent
OUT = output_dir(HERE)

ALLEGHENY_FIPS = "003"
HALF_MILE_M = 805.0  # ~1/2 mile, the standard transit walk-shed threshold


def load_stops() -> gpd.GeoDataFrame:
    """Load PRT stops with valid coordinates, projected to meters."""
    stop_df = query_to_polars(
        "SELECT stop_id, lat, lon FROM stops WHERE lat IS NOT NULL AND lon IS NOT NULL"
    )
    gdf = gpd.GeoDataFrame(
        stop_df.to_pandas(),
        geometry=gpd.points_from_xy(stop_df["lon"], stop_df["lat"]),
        crs=CRS_GEO,
    )
    return gdf.to_crs(CRS_M)


def tract_proximity(tracts_gdf: gpd.GeoDataFrame, stops_gdf: gpd.GeoDataFrame) -> pl.DataFrame:
    """Distance from each tract centroid to its nearest stop, with density."""
    centroids = tracts_gdf[["geoid", "population", "land_area_m2"]].copy()
    centroids = gpd.GeoDataFrame(
        centroids, geometry=tracts_gdf.geometry.centroid, crs=CRS_M
    )
    nearest = gpd.sjoin_nearest(
        centroids, stops_gdf[["geometry"]], distance_col="dist_to_stop_m"
    )
    # sjoin_nearest can emit ties; keep the closest row per tract.
    nearest = nearest.sort_values("dist_to_stop_m").drop_duplicates("geoid")

    tract_df = pl.from_pandas(
        nearest[["geoid", "population", "land_area_m2", "dist_to_stop_m"]]
    )
    tract_df = tract_df.with_columns(
        pop_density=pl.col("population") / (pl.col("land_area_m2") / 1_000_000),
        within_half_mile=pl.col("dist_to_stop_m") <= HALF_MILE_M,
    )
    # Density quartile (1 = sparsest, 4 = densest); only for populated tracts.
    populated = tract_df.filter(pl.col("population") > 0)
    populated = populated.with_columns(
        density_quartile=(
            (pl.col("pop_density").rank(method="ordinal") - 1)
            / populated.height * 4
        ).floor().clip(0, 3).cast(pl.Int64) + 1
    )
    return tract_df.join(
        populated.select("geoid", "density_quartile"), on="geoid", how="left"
    )


def analyze(tract_df: pl.DataFrame) -> dict:
    """Spearman correlation, quartile gradient, and coverage summary."""
    populated = tract_df.filter(pl.col("population") > 0)
    rho, p = stats.spearmanr(
        populated["pop_density"], populated["dist_to_stop_m"]
    )
    quartile_df = (
        populated.group_by("density_quartile")
        .agg(
            n_tracts=pl.len(),
            median_dist_m=pl.col("dist_to_stop_m").median(),
            median_density=pl.col("pop_density").median(),
        )
        .sort("density_quartile")
    )
    served = tract_df.filter(pl.col("within_half_mile"))
    total_pop = tract_df["population"].sum()
    return {
        "n_tracts": tract_df.height,
        "n_populated": populated.height,
        "spearman_rho": rho,
        "spearman_p": p,
        "quartile_df": quartile_df,
        "tracts_within_half_mile": tract_df["within_half_mile"].sum(),
        "pop_within_half_mile": served["population"].sum(),
        "total_pop": total_pop,
        "pop_coverage_pct": 100 * served["population"].sum() / total_pop,
        "median_dist_m": tract_df["dist_to_stop_m"].median(),
    }


def make_charts(tract_df: pl.DataFrame, results: dict) -> None:
    """Density-vs-distance scatter and the quartile gradient bar chart."""
    plt = setup_plotting()
    populated = tract_df.filter(pl.col("population") > 0)

    fig, ax = plt.subplots(figsize=(10, 7))
    ax.scatter(
        populated["pop_density"].to_list(),
        populated["dist_to_stop_m"].to_list(),
        color="#3b82f6", s=28, alpha=0.6, edgecolors="white", linewidths=0.5,
    )
    ax.set_xscale("log")
    ax.set_xlabel("Tract population density (people / km², log scale)")
    ax.set_ylabel("Distance to nearest stop (meters)")
    ax.set_title("Population Density vs Distance to Nearest PRT Stop\n(Allegheny County census tracts)")
    ax.annotate(
        f"Spearman rho = {results['spearman_rho']:.3f} (p = {results['spearman_p']:.3g})",
        xy=(0.04, 0.93), xycoords="axes fraction", fontsize=10,
    )
    save_chart(fig, OUT / "density_vs_distance.png")

    quartile_df = results["quartile_df"]
    fig, ax = plt.subplots(figsize=(9, 6))
    labels = ["Q1\n(sparsest)", "Q2", "Q3", "Q4\n(densest)"]
    ax.bar(labels, quartile_df["median_dist_m"].to_list(), color="#3b82f6")
    ax.set_ylabel("Median distance to nearest stop (meters)")
    ax.set_title("Transit Proximity by Population-Density Quartile")
    for i, d in enumerate(quartile_df["median_dist_m"].to_list()):
        ax.text(i, d, f"{d:,.0f} m", ha="center", va="bottom", fontsize=9)
    save_chart(fig, OUT / "distance_by_density_quartile.png")


@run_analysis(46, "Population Transit Proximity")
def main() -> None:
    """Entry point: load data, compute proximity, analyze, chart, and save."""
    with phase("Loading Allegheny County tracts and PRT stops"):
        tracts_gdf = load_tracts(extra_cols=["county_fips"])
        tracts_gdf = tracts_gdf[tracts_gdf["county_fips"] == ALLEGHENY_FIPS].copy()
        stops_gdf = load_stops()
        print(f"  {len(tracts_gdf)} tracts, {len(stops_gdf)} stops")

    with phase("Computing tract-to-stop proximity"):
        tract_df = tract_proximity(tracts_gdf, stops_gdf)

    with phase("Analyzing"):
        results = analyze(tract_df)
        print(f"  Density vs distance: Spearman rho = {results['spearman_rho']:.4f} "
              f"(p = {results['spearman_p']:.3g}), n = {results['n_populated']} populated tracts")
        print(f"  Median tract distance to nearest stop: {results['median_dist_m']:,.0f} m")
        for row in results["quartile_df"].iter_rows(named=True):
            print(f"    Q{row['density_quartile']}: median {row['median_dist_m']:,.0f} m "
                  f"to nearest stop ({row['n_tracts']} tracts)")
        print(f"  Coverage: {results['tracts_within_half_mile']} of {results['n_tracts']} "
              f"tracts and {results['pop_coverage_pct']:.1f}% of county population "
              f"within {HALF_MILE_M:.0f} m of a stop")
        save_csv(tract_df, OUT / "tract_transit_proximity.csv")

    with phase("Generating charts"):
        make_charts(tract_df, results)


if __name__ == "__main__":
    main()
