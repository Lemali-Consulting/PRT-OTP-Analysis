"""Per-route walkshed construction and areal-interpolated population served.

Shared helpers used by analyses that need to relate routes to the residents within
walking distance of their stops (mode-specific buffer, dissolved per route, areal
interpolation against ACS tract polygons).
"""

import geopandas as gpd
import polars as pl
from shapely import wkt
from shapely.geometry import Point

from prt_otp_analysis.common import query_to_polars
from prt_otp_analysis.common.schemas import (
    CENSUS_TRACTS,
    ROUTES,
    ROUTE_STOPS,
    STOPS,
    validate,
)

BUFFER_M_BUS = 400
BUFFER_M_RAIL = 800

CRS_GEO = "EPSG:4326"
CRS_M = "EPSG:32617"  # UTM zone 17N — covers SW Pennsylvania


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


def load_tracts(extra_cols: list[str] | None = None) -> gpd.GeoDataFrame:
    """Load census tracts as a GeoDataFrame in meter projection.

    Always includes geoid, population, land_area_m2, geometry. Extra columns
    (e.g., median_household_income) can be requested via *extra_cols*.
    """
    cols = ["geoid", "population", "land_area_m2", "geometry_wkt"]
    if extra_cols:
        cols = ["geoid", "population", *extra_cols, "land_area_m2", "geometry_wkt"]
    df = query_to_polars(f"SELECT {', '.join(cols)} FROM census_tracts")
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


def route_population_served() -> pl.DataFrame:
    """One-shot helper: returns DataFrame with route_id, mode, population_served (Int64).

    Identical to the per-route population column emitted by Analysis 44.
    """
    stops_routes_df = load_stops_with_routes()
    tracts = load_tracts()
    walksheds = build_route_walksheds(stops_routes_df)
    pop_df = population_per_route(walksheds, tracts)
    mode_df = (
        stops_routes_df.group_by("route_id")
        .agg(mode=pl.col("mode").first())
    )
    return (
        mode_df.join(pop_df, on="route_id", how="left")
        .with_columns(
            population_served=pl.col("population_served").fill_null(0).round(0).cast(pl.Int64),
        )
        .select("route_id", "mode", "population_served")
    )
