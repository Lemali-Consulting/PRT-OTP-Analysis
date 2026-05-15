"""Analysis 49: test whether transit service and boardings track Allegheny
County census-tract population density, the way stop proximity does (Analysis
46) -- and whether boardings diverge from residential density."""

from pathlib import Path

import geopandas as gpd
import numpy as np
import polars as pl
from scipy import stats

from prt_otp_analysis.common import (
    COLOR_GRAY,
    COLOR_PRIMARY,
    DATA_DIR,
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
BOARDINGS_DATEKEY = 201909  # September 2019 -- canonical pre-pandemic month
BOARDINGS_SERVICEDAY = "Weekday"
QUARTILE_LABELS = ["Q1\n(sparsest)", "Q2", "Q3", "Q4\n(densest)"]


def load_service_stops() -> pl.DataFrame:
    """Weekly scheduled bus trips per stop, with coordinates and a label.

    Restricted to bus (and busway) service: the WPRDC boardings dataset is
    bus-only, so light-rail and incline service are excluded to keep the
    service and boardings metrics on the same footing.
    """
    rs_df = query_to_polars(
        "SELECT rs.stop_id, rs.trips_7d FROM route_stops rs "
        "JOIN routes r ON rs.route_id = r.route_id WHERE r.mode = 'BUS'"
    )
    service_df = rs_df.group_by("stop_id").agg(weekly_trips=pl.col("trips_7d").sum())
    stops_df = query_to_polars(
        "SELECT stop_id, lat, lon, hood, muni FROM stops "
        "WHERE lat IS NOT NULL AND lon IS NOT NULL"
    )
    return stops_df.join(service_df, on="stop_id", how="left").with_columns(
        weekly_trips=pl.col("weekly_trips").fill_null(0)
    )


def load_boardings_stops() -> pl.DataFrame:
    """Average weekday boardings per physical stop (pre-pandemic), with coordinates."""
    csv_path = DATA_DIR / "bus-stop-usage" / "wprdc_stop_data.csv"
    df = pl.read_csv(csv_path, null_values=["NA", ""], infer_schema_length=20000)
    slc = df.filter(
        (pl.col("datekey") == BOARDINGS_DATEKEY)
        & (pl.col("serviceday") == BOARDINGS_SERVICEDAY)
    )
    return slc.group_by("stop_id").agg(
        boardings=pl.col("avg_ons").fill_null(0).sum(),
        lat=pl.col("latitude").first(),
        lon=pl.col("longitude").first(),
    )


def sum_to_tracts(
    points_df: pl.DataFrame, tracts_gdf: gpd.GeoDataFrame, value_col: str
) -> tuple[pl.DataFrame, int]:
    """Point-in-polygon assign stops to tracts; return per-tract sums and the
    count of stops that fell outside every tract."""
    pdf = points_df.to_pandas()
    gdf = gpd.GeoDataFrame(
        pdf, geometry=gpd.points_from_xy(pdf["lon"], pdf["lat"]), crs=CRS_GEO
    ).to_crs(CRS_M)
    joined = gpd.sjoin(
        gdf, tracts_gdf[["geoid", "geometry"]], how="left", predicate="within"
    )
    n_unmatched = int(joined["geoid"].isna().sum())
    matched_df = pl.from_pandas(joined.dropna(subset=["geoid"])[["geoid", value_col]])
    summed = matched_df.group_by("geoid").agg(pl.col(value_col).sum())
    return summed, n_unmatched


def tract_neighborhood_labels(
    service_df: pl.DataFrame, tracts_gdf: gpd.GeoDataFrame
) -> pl.DataFrame:
    """Most common neighborhood/municipality among each tract's stops, for labels."""
    pdf = service_df.to_pandas()
    gdf = gpd.GeoDataFrame(
        pdf, geometry=gpd.points_from_xy(pdf["lon"], pdf["lat"]), crs=CRS_GEO
    ).to_crs(CRS_M)
    joined = gpd.sjoin(
        gdf, tracts_gdf[["geoid", "geometry"]], how="inner", predicate="within"
    )
    labelled = pl.from_pandas(
        joined[["geoid", "hood", "muni"]]
    ).with_columns(
        area=pl.coalesce(pl.col("hood"), pl.col("muni"))
    )
    return (
        labelled.drop_nulls("area")
        .group_by("geoid", "area")
        .len()
        .sort("len", descending=True)
        .group_by("geoid")
        .agg(area_label=pl.col("area").first())
    )


def rail_served_geoids(tracts_gdf: gpd.GeoDataFrame) -> set[str]:
    """GEOIDs of tracts that contain at least one light-rail stop.

    Light-rail-corridor tracts board mostly on the 'T', which the bus-stop-usage
    dataset does not cover; flagging them keeps the boardings results honest.
    """
    rail_df = query_to_polars(
        "SELECT DISTINCT s.stop_id, s.lat, s.lon FROM stops s "
        "JOIN route_stops rs ON s.stop_id = rs.stop_id "
        "JOIN routes r ON rs.route_id = r.route_id "
        "WHERE r.mode = 'RAIL' AND s.lat IS NOT NULL"
    )
    pdf = rail_df.to_pandas()
    gdf = gpd.GeoDataFrame(
        pdf, geometry=gpd.points_from_xy(pdf["lon"], pdf["lat"]), crs=CRS_GEO
    ).to_crs(CRS_M)
    joined = gpd.sjoin(
        gdf, tracts_gdf[["geoid", "geometry"]], how="inner", predicate="within"
    )
    return set(joined["geoid"])


def build_tract_table(
    tracts_gdf: gpd.GeoDataFrame,
    service_by_tract: pl.DataFrame,
    boardings_by_tract: pl.DataFrame,
    labels_df: pl.DataFrame,
    rail_geoids: set[str],
) -> pl.DataFrame:
    """One row per Allegheny tract: density, service, boardings, and quartile."""
    tract_df = pl.from_pandas(
        tracts_gdf[["geoid", "population", "land_area_m2"]]
    ).with_columns(rail_served=pl.col("geoid").is_in(list(rail_geoids)))
    tract_df = (
        tract_df.join(service_by_tract, on="geoid", how="left")
        .join(boardings_by_tract, on="geoid", how="left")
        .join(labels_df, on="geoid", how="left")
        .with_columns(
            weekly_trips=pl.col("weekly_trips").fill_null(0),
            boardings=pl.col("boardings").fill_null(0.0),
            pop_density=pl.col("population") / (pl.col("land_area_m2") / 1_000_000),
        )
        .with_columns(
            boardings_per_1000=pl.when(pl.col("population") > 0)
            .then(1000 * pl.col("boardings") / pl.col("population"))
            .otherwise(None),
        )
    )
    # Density quartile (1 = sparsest, 4 = densest); only for populated tracts.
    populated = tract_df.filter(pl.col("population") > 0)
    populated = populated.with_columns(
        density_quartile=(
            (pl.col("pop_density").rank(method="ordinal") - 1)
            / populated.height
            * 4
        )
        .floor()
        .clip(0, 3)
        .cast(pl.Int64)
        + 1
    )
    return tract_df.join(
        populated.select("geoid", "density_quartile"), on="geoid", how="left"
    )


def fit_residuals(tract_df: pl.DataFrame) -> pl.DataFrame:
    """Log-log regression of boardings on density; attach predicted + residual.

    Residuals isolate tracts that board far above or below what their
    residential density predicts -- the destination-driven divergence.
    """
    populated = tract_df.filter(pl.col("population") > 0)
    x = np.log10(populated["pop_density"].to_numpy())
    y = np.log10(populated["boardings"].to_numpy() + 1)
    slope, intercept, r, p, _ = stats.linregress(x, y)
    expected = 10 ** (slope * x + intercept) - 1
    resid = y - (slope * x + intercept)
    fitted = populated.select("geoid").with_columns(
        expected_boardings=pl.Series(expected),
        boardings_resid=pl.Series(resid),
    )
    out = tract_df.join(fitted, on="geoid", how="left")
    return out, {"slope": slope, "intercept": intercept, "r": r, "p": p}


def analyze(tract_df: pl.DataFrame) -> dict:
    """Spearman correlations and density-quartile gradients."""
    populated = tract_df.filter(pl.col("population") > 0)
    rho_serv, p_serv = stats.spearmanr(
        populated["pop_density"], populated["weekly_trips"]
    )
    rho_board, p_board = stats.spearmanr(
        populated["pop_density"], populated["boardings"]
    )
    rho_board_pop, p_board_pop = stats.spearmanr(
        populated["population"], populated["boardings"]
    )
    rho_serv_pop, _ = stats.spearmanr(
        populated["population"], populated["weekly_trips"]
    )
    quartile_df = (
        populated.group_by("density_quartile")
        .agg(
            n_tracts=pl.len(),
            median_density=pl.col("pop_density").median(),
            median_weekly_trips=pl.col("weekly_trips").median(),
            median_boardings=pl.col("boardings").median(),
            median_boardings_per_1000=pl.col("boardings_per_1000").median(),
        )
        .sort("density_quartile")
    )
    return {
        "n_populated": populated.height,
        "rho_serv": rho_serv,
        "p_serv": p_serv,
        "rho_board": rho_board,
        "p_board": p_board,
        "rho_board_pop": rho_board_pop,
        "p_board_pop": p_board_pop,
        "rho_serv_pop": rho_serv_pop,
        "quartile_df": quartile_df,
    }


def chart_scatter(tract_df: pl.DataFrame, y_col: str, ylabel: str,
                  title: str, rho: float, p: float, path: Path,
                  log_y: bool = False) -> None:
    """Density-vs-metric scatter, annotated with the Spearman correlation."""
    plt = setup_plotting()
    populated = tract_df.filter(pl.col("population") > 0)
    fig, ax = plt.subplots(figsize=(10, 7))
    ax.scatter(
        populated["pop_density"].to_list(),
        populated[y_col].to_list(),
        color=COLOR_PRIMARY, s=28, alpha=0.6, edgecolors="white", linewidths=0.5,
    )
    ax.set_xscale("log")
    if log_y:
        ax.set_yscale("symlog")
    ax.set_xlabel("Tract population density (people / km², log scale)")
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    ax.annotate(
        f"Spearman rho = {rho:.3f} (p = {p:.3g})",
        xy=(0.04, 0.93), xycoords="axes fraction", fontsize=10,
    )
    save_chart(fig, path)


def chart_quartile_bar(quartile_df: pl.DataFrame, col: str, ylabel: str,
                       title: str, path: Path, fmt: str = ",.0f") -> None:
    """Bar chart of a metric's median across density quartiles."""
    plt = setup_plotting()
    fig, ax = plt.subplots(figsize=(9, 6))
    vals = quartile_df[col].to_list()
    ax.bar(QUARTILE_LABELS, vals, color=COLOR_PRIMARY)
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    for i, v in enumerate(vals):
        ax.text(i, v, f"{v:{fmt}}", ha="center", va="bottom", fontsize=9)
    save_chart(fig, path)


def chart_residuals(tract_df: pl.DataFrame, outliers: pl.DataFrame,
                    fit: dict, path: Path) -> None:
    """Log-log boardings-vs-density scatter with fit line and labeled outliers."""
    plt = setup_plotting()
    populated = tract_df.filter(pl.col("population") > 0)
    dens = populated["pop_density"].to_numpy()
    board = populated["boardings"].to_numpy()
    fig, ax = plt.subplots(figsize=(10, 7))
    ax.scatter(dens, board + 1, color=COLOR_GRAY, s=24, alpha=0.5,
               edgecolors="white", linewidths=0.5)
    xs = np.array([dens.min(), dens.max()])
    ys = 10 ** (fit["slope"] * np.log10(xs) + fit["intercept"])
    ax.plot(xs, ys, color=COLOR_PRIMARY, linewidth=2,
            label="Boardings predicted by population density")
    # Label the over-boarding (positive-residual) outliers; the under-boarding
    # tracts all pile up at zero boardings, so labelling them just overprints.
    for row in outliers.filter(pl.col("boardings_resid") > 0).iter_rows(named=True):
        ax.annotate(
            str(row["area_label"] or row["geoid"]),
            xy=(row["pop_density"], row["boardings"] + 1),
            xytext=(4, 3), textcoords="offset points",
            fontsize=7.5, alpha=0.9,
        )
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("Tract population density (people / km², log scale)")
    ax.set_ylabel("Average weekday boardings + 1 (log scale)")
    ax.set_title("Boardings vs Density: Tracts That Over- and Under-Board\n"
                 "(Allegheny County census tracts)")
    ax.legend(loc="lower right", fontsize=9)
    save_chart(fig, path)


@run_analysis(49, "Transit Service & Boardings vs Population Density")
def main() -> None:
    """Load data, assign stops to tracts, correlate, chart, and save."""
    with phase("Loading Allegheny County tracts and stop data"):
        tracts_gdf = load_tracts(extra_cols=["county_fips"])
        tracts_gdf = tracts_gdf[tracts_gdf["county_fips"] == ALLEGHENY_FIPS].copy()
        service_stops_df = load_service_stops()
        boardings_stops_df = load_boardings_stops()
        print(f"  {len(tracts_gdf)} tracts, {service_stops_df.height} service stops, "
              f"{boardings_stops_df.height} boardings stops")
        print(f"  total pre-pandemic weekday boardings: "
              f"{boardings_stops_df['boardings'].sum():,.0f}")

    with phase("Assigning stops to tracts"):
        service_by_tract, n_unmatched_serv = sum_to_tracts(
            service_stops_df.select("stop_id", "lat", "lon", "weekly_trips"),
            tracts_gdf, "weekly_trips",
        )
        boardings_by_tract, n_unmatched_board = sum_to_tracts(
            boardings_stops_df, tracts_gdf, "boardings",
        )
        labels_df = tract_neighborhood_labels(service_stops_df, tracts_gdf)
        rail_geoids = rail_served_geoids(tracts_gdf)
        print(f"  stops outside all Allegheny tracts: "
              f"{n_unmatched_serv} service, {n_unmatched_board} boardings")

    with phase("Building tract table"):
        tract_df = build_tract_table(
            tracts_gdf, service_by_tract, boardings_by_tract, labels_df,
            rail_geoids,
        )
        tract_df, fit = fit_residuals(tract_df)
        assigned_board = tract_df["boardings"].sum()
        print(f"  {tract_df.height} tracts ({len(rail_geoids)} light-rail-served); "
              f"{assigned_board:,.0f} boardings assigned to tracts")

    with phase("Analyzing"):
        results = analyze(tract_df)
        print(f"  Q1 service: density vs weekly trips "
              f"Spearman rho = {results['rho_serv']:.3f} "
              f"(p = {results['p_serv']:.3g}), n = {results['n_populated']}")
        print(f"  Q2 boardings: density vs boardings "
              f"Spearman rho = {results['rho_board']:.3f} "
              f"(p = {results['p_board']:.3g})")
        print(f"     boardings vs population Spearman rho = "
              f"{results['rho_board_pop']:.3f}")
        for row in results["quartile_df"].iter_rows(named=True):
            print(f"    Q{row['density_quartile']}: "
                  f"{row['median_weekly_trips']:,.0f} weekly trips, "
                  f"{row['median_boardings']:,.0f} boardings, "
                  f"{row['median_boardings_per_1000']:,.0f} boardings/1k residents "
                  f"({row['n_tracts']} tracts)")

    with phase("Saving data and charts"):
        save_csv(
            tract_df.select(
                "geoid", "area_label", "population", "land_area_m2", "pop_density",
                "weekly_trips", "boardings", "boardings_per_1000",
                "density_quartile", "rail_served", "expected_boardings",
                "boardings_resid",
            ).sort("pop_density", descending=True),
            OUT / "tract_service_boardings.csv",
        )
        save_csv(results["quartile_df"], OUT / "quartile_summary.csv")

        ranked = tract_df.filter(pl.col("boardings_resid").is_not_null()).sort(
            "boardings_resid", descending=True
        )
        outliers = pl.concat([ranked.head(10), ranked.tail(10)])
        save_csv(
            outliers.select(
                "geoid", "area_label", "population", "pop_density",
                "boardings", "rail_served", "expected_boardings", "boardings_resid",
            ),
            OUT / "boardings_outlier_tracts.csv",
        )

        qdf = results["quartile_df"]
        chart_scatter(tract_df, "weekly_trips", "Weekly scheduled trips serving tract",
                      "Population Density vs Transit Service\n"
                      "(Allegheny County census tracts)",
                      results["rho_serv"], results["p_serv"],
                      OUT / "density_vs_service.png")
        chart_quartile_bar(qdf, "median_weekly_trips",
                           "Median weekly scheduled trips",
                           "Transit Service by Population-Density Quartile",
                           OUT / "service_by_density_quartile.png")
        chart_scatter(tract_df, "boardings", "Average weekday boardings",
                      "Population Density vs Boardings\n"
                      "(Allegheny County census tracts)",
                      results["rho_board"], results["p_board"],
                      OUT / "density_vs_boardings.png", log_y=True)
        chart_quartile_bar(qdf, "median_boardings",
                           "Median average weekday boardings",
                           "Boardings by Population-Density Quartile",
                           OUT / "boardings_by_density_quartile.png")
        chart_quartile_bar(qdf, "median_boardings_per_1000",
                           "Median boardings per 1,000 residents",
                           "Boardings per Resident by Population-Density Quartile",
                           OUT / "boardings_per_capita_by_quartile.png")
        chart_residuals(tract_df, outliers, fit,
                        OUT / "boardings_vs_density_residuals.png")


if __name__ == "__main__":
    main()
