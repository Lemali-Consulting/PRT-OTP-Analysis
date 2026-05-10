"""Point-in-polygon assignment of PRT stops to ACS census tracts.

Provides one helper that returns a Polars DataFrame keyed by `stop_id` with the
containing tract's GEOID and selected ACS demographics, replacing the fuzzy
`stops.hood` field used by older analyses.
"""

import geopandas as gpd
import polars as pl
from shapely.geometry import Point

from prt_otp_analysis.common import query_to_polars
from prt_otp_analysis.common.schemas import STOPS, validate
from prt_otp_analysis.walksheds import CRS_GEO, CRS_M, load_tracts

DEFAULT_TRACT_COLS = [
    "median_household_income",
    "households_total",
    "households_zero_vehicle",
    "pop_white_nh",
    "pop_black_nh",
    "pop_asian_nh",
    "pop_hispanic",
]


def assign_stops_to_tracts(
    extra_tract_cols: list[str] | None = None,
) -> pl.DataFrame:
    """Return one row per stop with its containing tract's GEOID and ACS columns.

    Stops outside any 5-county PA tract (e.g., a handful of stops just over the
    West Virginia line) get NULL for tract columns.
    """
    cols = DEFAULT_TRACT_COLS if extra_tract_cols is None else extra_tract_cols

    stops_df = query_to_polars(
        "SELECT stop_id, lat, lon FROM stops WHERE lat IS NOT NULL AND lon IS NOT NULL"
    )
    validate(stops_df, STOPS, subset=True)

    tracts = load_tracts(extra_cols=cols)

    pdf = stops_df.to_pandas()
    pdf["geometry"] = [Point(lon, lat) for lon, lat in zip(pdf["lon"], pdf["lat"])]
    stops_gdf = gpd.GeoDataFrame(pdf, geometry="geometry", crs=CRS_GEO).to_crs(CRS_M)

    keep = ["geoid", "population", "land_area_m2", *cols, "geometry"]
    joined = gpd.sjoin(
        stops_gdf,
        tracts[keep],
        how="left",
        predicate="within",
    ).drop(columns=["geometry", "index_right"])

    out = pl.from_pandas(joined).drop("lat", "lon")
    return out
