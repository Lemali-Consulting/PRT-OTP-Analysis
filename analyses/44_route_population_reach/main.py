"""Analysis 44: rank PRT routes by resident population within walking distance of their stops.

Buffers each stop, dissolves per route, areal-interpolates against ACS tract population.
"""

from pathlib import Path

import geopandas as gpd
import matplotlib.pyplot as plt
import polars as pl
from shapely import wkt
from shapely.geometry import Point

from prt_otp_analysis.common import (
    MODE_COLORS,
    output_dir,
    phase,
    query_to_polars,
    run_analysis,
    save_chart,
    save_csv,
    setup_plotting,
)
from prt_otp_analysis.common.schemas import (
    CENSUS_TRACTS,
    ROUTES,
    ROUTE_STOPS,
    STOPS,
    validate,
)

HERE = Path(__file__).resolve().parent
OUT = output_dir(HERE)

BUFFER_M_BUS = 400
BUFFER_M_RAIL = 800

CRS_GEO = "EPSG:4326"
CRS_M = "EPSG:32617"


def load_stops_with_routes() -> pl.DataFrame:
    """Join stops + route_stops + routes; one row per (route, stop)."""
    stops_df = query_to_polars(
        "SELECT stop_id, lat, lon FROM stops WHERE lat IS NOT NULL AND lon IS NOT NULL"
    )
    validate(stops_df, STOPS, subset=True)
    rs_df = query_to_polars("SELECT route_id, stop_id FROM route_stops")
    validate(rs_df, ROUTE_STOPS, subset=True)
    routes_df = query_to_polars("SELECT route_id, mode FROM routes")
    validate(routes_df, ROUTES, subset=True)
    return rs_df.join(stops_df, on="stop_id").join(routes_df, on="route_id")


def load_tracts() -> gpd.GeoDataFrame:
    """Load census tracts as a GeoDataFrame in meter projection."""
    df = query_to_polars(
        "SELECT geoid, population, land_area_m2, geometry_wkt FROM census_tracts"
    )
    validate(df, CENSUS_TRACTS, subset=True)
    pdf = df.to_pandas()
    pdf["geometry"] = pdf["geometry_wkt"].apply(wkt.loads)
    gdf = gpd.GeoDataFrame(pdf.drop(columns=["geometry_wkt"]), geometry="geometry", crs=CRS_GEO)
    return gdf.to_crs(CRS_M)


def build_route_walksheds(stops_routes_df: pl.DataFrame) -> gpd.GeoDataFrame:
    """Buffer stops by mode-specific radius and dissolve to one polygon per route."""
    pdf = stops_routes_df.to_pandas()
    pdf["geometry"] = [Point(lon, lat) for lon, lat in zip(pdf["lon"], pdf["lat"])]
    gdf = gpd.GeoDataFrame(pdf, geometry="geometry", crs=CRS_GEO).to_crs(CRS_M)
    gdf["buffer_m"] = gdf["mode"].map(
        lambda m: BUFFER_M_RAIL if m in ("RAIL", "INCLINE") else BUFFER_M_BUS
    )
    gdf["geometry"] = gdf.geometry.buffer(gdf["buffer_m"])
    walksheds = gdf.dissolve(by="route_id", aggfunc={"mode": "first"}).reset_index()
    walksheds["walkshed_area_km2"] = walksheds.geometry.area / 1_000_000
    return walksheds


def population_per_route(
    walksheds: gpd.GeoDataFrame,
    tracts: gpd.GeoDataFrame,
) -> pl.DataFrame:
    """Areal interpolation: for each (route, tract) overlap, apportion tract population by area share."""
    tracts = tracts.copy()
    tracts["tract_area_m2"] = tracts.geometry.area
    overlay = gpd.overlay(
        walksheds[["route_id", "geometry"]],
        tracts[["geoid", "population", "tract_area_m2", "geometry"]],
        how="intersection",
        keep_geom_type=True,
    )
    overlay["overlap_area_m2"] = overlay.geometry.area
    overlay["pop_share"] = (
        overlay["overlap_area_m2"] / overlay["tract_area_m2"]
    ) * overlay["population"].fillna(0)
    agg = overlay.groupby("route_id", as_index=False)["pop_share"].sum()
    agg = agg.rename(columns={"pop_share": "population_served"})
    return pl.from_pandas(agg)


def assemble(
    stops_routes_df: pl.DataFrame,
    walksheds: gpd.GeoDataFrame,
    pop_df: pl.DataFrame,
) -> pl.DataFrame:
    """Combine per-route stop count, walkshed area, and population into the final table."""
    stop_counts = (
        stops_routes_df.group_by("route_id")
        .agg(stop_count=pl.col("stop_id").n_unique(), mode=pl.col("mode").first())
    )
    ws_df = pl.from_pandas(walksheds[["route_id", "walkshed_area_km2"]])
    out = (
        stop_counts.join(ws_df, on="route_id")
        .join(pop_df, on="route_id", how="left")
        .with_columns(
            population_served=pl.col("population_served").fill_null(0).round(0).cast(pl.Int64),
        )
        .with_columns(
            population_per_stop=(pl.col("population_served") / pl.col("stop_count")).round(0).cast(pl.Int64),
        )
        .sort("population_served", descending=True)
        .select(
            "route_id", "mode", "stop_count",
            "walkshed_area_km2", "population_served", "population_per_stop",
        )
    )
    return out


def chart_top_routes(df: pl.DataFrame, n: int = 25) -> None:
    """Horizontal bar chart of top-N routes by population served, colored by mode."""
    top = df.head(n).reverse()
    fig, ax = plt.subplots(figsize=(9, 8))
    colors = [MODE_COLORS.get(m, MODE_COLORS["UNKNOWN"]) for m in top["mode"].to_list()]
    ax.barh(top["route_id"].to_list(), top["population_served"].to_list(), color=colors)
    ax.set_xlabel("Residents within walking distance")
    ax.set_title(f"Top {n} PRT routes by population served")
    ax.xaxis.set_major_formatter(lambda x, _: f"{int(x):,}")
    handles = [
        plt.Rectangle((0, 0), 1, 1, color=MODE_COLORS[m])
        for m in ("BUS", "RAIL", "INCLINE")
    ]
    ax.legend(handles, ["Bus", "Rail (LRT)", "Incline"], loc="lower right")
    save_chart(fig, OUT / "route_population_reach_top25.png")


def chart_walkshed_map(walksheds: gpd.GeoDataFrame, tracts: gpd.GeoDataFrame) -> None:
    """Sanity-check map: union of walksheds over tract population density."""
    tracts = tracts.copy()
    tracts["pop_density"] = tracts["population"].fillna(0) / (tracts["land_area_m2"] / 1_000_000)
    union = walksheds.geometry.union_all()
    fig, ax = plt.subplots(figsize=(10, 10))
    tracts.plot(
        column="pop_density",
        cmap="Greys",
        ax=ax,
        edgecolor="white",
        linewidth=0.2,
        legend=True,
        legend_kwds={"label": "Population density (per km²)", "shrink": 0.5},
    )
    gpd.GeoSeries([union], crs=tracts.crs).plot(
        ax=ax, facecolor=MODE_COLORS["BUS"], alpha=0.35, edgecolor="none"
    )
    ax.set_title("PRT system walkshed (all routes) over tract population density")
    ax.set_axis_off()
    save_chart(fig, OUT / "walkshed_map.png")


@run_analysis(44, "Route Population Reach")
def main() -> None:
    setup_plotting()

    with phase("Loading stops, routes, and tracts"):
        stops_routes_df = load_stops_with_routes()
        print(f"  {stops_routes_df['route_id'].n_unique()} routes, "
              f"{stops_routes_df['stop_id'].n_unique()} unique stops")
        tracts = load_tracts()
        print(f"  {len(tracts)} census tracts")

    with phase("Building per-route walksheds"):
        walksheds = build_route_walksheds(stops_routes_df)
        print(f"  {len(walksheds)} route walksheds; "
              f"total area {walksheds['walkshed_area_km2'].sum():.1f} km²")

    with phase("Areal interpolation against tract population"):
        pop_df = population_per_route(walksheds, tracts)
        print(f"  computed for {len(pop_df)} routes")

    with phase("Assembling output"):
        out = assemble(stops_routes_df, walksheds, pop_df)
        save_csv(out, OUT / "route_population_reach.csv")
        print("\n  Top 10 routes by population served:")
        for row in out.head(10).iter_rows(named=True):
            print(f"    {row['route_id']:>5s}  {row['mode']:<7s}  "
                  f"{row['population_served']:>8,}  ({row['stop_count']} stops)")

    with phase("Charting"):
        chart_top_routes(out)
        chart_walkshed_map(walksheds, tracts)


if __name__ == "__main__":
    main()
