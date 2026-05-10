"""Fetch ACS 5-year tract population + TIGER polygons for PRT-area counties and load into prt.db."""

import io
import json
import sqlite3
import zipfile
from pathlib import Path
from urllib.request import Request, urlopen

import geopandas as gpd
import polars as pl

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
DB_PATH = DATA_DIR / "prt.db"
CENSUS_DIR = DATA_DIR / "census-tracts"

STATE_FIPS = "42"  # Pennsylvania
COUNTY_FIPS = {
    "003": "Allegheny",
    "007": "Beaver",
    "019": "Butler",
    "125": "Washington",
    "129": "Westmoreland",
}
TIGER_YEAR = 2022
ACS_YEAR = 2022  # ACS 5-year ending year (covers 2018-2022)
TIGER_URL = (
    f"https://www2.census.gov/geo/tiger/TIGER{TIGER_YEAR}/TRACT/"
    f"tl_{TIGER_YEAR}_{STATE_FIPS}_tract.zip"
)
ACS_URL = (
    f"https://api.census.gov/data/{ACS_YEAR}/acs/acs5"
    f"?get=B01003_001E,NAME"
    f"&for=tract:*"
    f"&in=state:{STATE_FIPS}"
    f"&in=county:{','.join(COUNTY_FIPS)}"
)


def _download(url: str, dest: Path) -> None:
    """Download URL to dest if not already cached."""
    if dest.exists():
        print(f"  cached: {dest.name}")
        return
    print(f"  downloading {url}")
    req = Request(url, headers={"User-Agent": "prt-otp-analysis/0.1"})
    with urlopen(req) as resp, open(dest, "wb") as f:
        f.write(resp.read())


def fetch_tiger() -> gpd.GeoDataFrame:
    """Download (cached) PA tract shapefile and return tracts in our 5 counties."""
    CENSUS_DIR.mkdir(parents=True, exist_ok=True)
    zip_path = CENSUS_DIR / f"tl_{TIGER_YEAR}_{STATE_FIPS}_tract.zip"
    _download(TIGER_URL, zip_path)
    extract_dir = CENSUS_DIR / f"tl_{TIGER_YEAR}_{STATE_FIPS}_tract"
    if not extract_dir.exists():
        with zipfile.ZipFile(zip_path) as zf:
            zf.extractall(extract_dir)
    shp = next(extract_dir.glob("*.shp"))
    gdf = gpd.read_file(shp)
    gdf = gdf[gdf["COUNTYFP"].isin(COUNTY_FIPS)].copy()
    return gdf


def fetch_acs() -> pl.DataFrame:
    """Fetch ACS B01003 (total population) for our 5 counties via Census API."""
    cache = CENSUS_DIR / f"acs5_{ACS_YEAR}_b01003.json"
    if cache.exists():
        print(f"  cached: {cache.name}")
        rows = json.loads(cache.read_text())
    else:
        print(f"  downloading {ACS_URL}")
        req = Request(ACS_URL, headers={"User-Agent": "prt-otp-analysis/0.1"})
        with urlopen(req) as resp:
            rows = json.loads(resp.read())
        cache.write_text(json.dumps(rows))
    header, *body = rows
    df = pl.DataFrame(body, schema=header, orient="row")
    df = df.with_columns(
        geoid=pl.col("state") + pl.col("county") + pl.col("tract"),
        population=pl.col("B01003_001E").cast(pl.Int64, strict=False),
    )
    return df.select("geoid", "population")


def build_dataframe() -> pl.DataFrame:
    """Join TIGER polygons with ACS population, return DataFrame matching CENSUS_TRACTS schema."""
    print("\n1. Fetching TIGER tract polygons...")
    gdf = fetch_tiger()
    print(f"  {len(gdf)} tracts in {len(COUNTY_FIPS)} counties")

    print("\n2. Fetching ACS B01003 population...")
    pop_df = fetch_acs()
    print(f"  {len(pop_df)} ACS rows")

    # ALAND is land area in m^2; INTPTLAT/INTPTLON are internal point (string degrees with leading sign).
    records = []
    for _, row in gdf.iterrows():
        records.append({
            "geoid": row["GEOID"],
            "state_fips": row["STATEFP"],
            "county_fips": row["COUNTYFP"],
            "tract_code": row["TRACTCE"],
            "land_area_m2": float(row["ALAND"]),
            "intpt_lat": float(row["INTPTLAT"]),
            "intpt_lon": float(row["INTPTLON"]),
            "geometry_wkt": row["geometry"].wkt,
        })
    geom_df = pl.DataFrame(records)
    df = geom_df.join(pop_df, on="geoid", how="left")
    df = df.filter(pl.col("land_area_m2") > 0)
    return df.select(
        "geoid", "state_fips", "county_fips", "tract_code",
        "population", "land_area_m2", "intpt_lat", "intpt_lon", "geometry_wkt",
    )


def write_to_db(df: pl.DataFrame) -> None:
    """Write census_tracts table to prt.db."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute("DROP TABLE IF EXISTS census_tracts")
    conn.execute("""
        CREATE TABLE census_tracts (
            geoid         TEXT PRIMARY KEY,
            state_fips    TEXT NOT NULL,
            county_fips   TEXT NOT NULL,
            tract_code    TEXT NOT NULL,
            population    INTEGER,
            land_area_m2  REAL NOT NULL,
            intpt_lat     REAL NOT NULL,
            intpt_lon     REAL NOT NULL,
            geometry_wkt  TEXT NOT NULL
        )
    """)
    conn.executemany(
        "INSERT INTO census_tracts (geoid, state_fips, county_fips, tract_code, "
        "population, land_area_m2, intpt_lat, intpt_lon, geometry_wkt) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        df.rows(),
    )
    conn.commit()
    count = conn.execute("SELECT COUNT(*) FROM census_tracts").fetchone()[0]
    total_pop = conn.execute("SELECT SUM(population) FROM census_tracts").fetchone()[0]
    conn.close()
    print(f"  Wrote {count} tracts, total population {total_pop:,}")


def main() -> None:
    """Entry point: fetch census data and write to prt.db."""
    print("=" * 60)
    print("Census Tracts ETL (TIGER + ACS B01003)")
    print("=" * 60)
    df = build_dataframe()
    print("\n3. Writing to database...")
    write_to_db(df)
    print("\nDone.")


if __name__ == "__main__":
    main()
