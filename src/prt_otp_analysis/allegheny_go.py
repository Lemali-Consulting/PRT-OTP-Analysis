"""Extract Allegheny Go fare-program ridership data from the county Tableau dashboard."""

import http.cookiejar
import json
import re
import sqlite3
import urllib.parse
import urllib.request
from pathlib import Path

import polars as pl

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
DB_PATH = DATA_DIR / "prt.db"
CACHE_DIR = DATA_DIR / "allegheny-go"
CACHE_FILE = CACHE_DIR / "ridership_weekly.csv"

BASE_URL = "https://tableau.alleghenycounty.us"
EMBED_PATH = "/t/PublicSite/views/AlleghenyGoDashboard/Ridership"
VIZQL_PREFIX = "/vizql/t/PublicSite/w/AlleghenyGoDashboard/v/Ridership"

EMBED_URL = f"{BASE_URL}{EMBED_PATH}?%3Aembed=yes&%3Atoolbar=no&%3AshowAppBanner=false"

USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"

# Worksheet that contains the weekly time series
TIME_SERIES_SHEET = "Ridership Total Rides over Time (2)"


def _build_opener() -> urllib.request.OpenerDirector:
    """Build an HTTP opener with cookie support for session persistence."""
    cj = http.cookiejar.CookieJar()
    return urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))


def _form_data() -> bytes:
    """Encode the standard form payload for Tableau VizQL endpoints."""
    return urllib.parse.urlencode({
        "worksheetPortSize": json.dumps({"w": 800, "h": 600}),
        "dashboardPortSize": json.dumps({"w": 800, "h": 600}),
        "sheet_id": "Ridership",
    }).encode("utf-8")


def _start_session(opener: urllib.request.OpenerDirector) -> str:
    """Create a Tableau VizQL session and return its ID.

    The flow is: GET the embed page (for cookies), then POST to startSession/viewing
    which returns JSON containing the session ID.
    """
    # GET embed page to initialize cookies
    req1 = urllib.request.Request(EMBED_URL, headers={"User-Agent": USER_AGENT})
    opener.open(req1, timeout=30).read()

    # POST to startSession/viewing to create the VizQL session
    url = (
        f"{BASE_URL}{VIZQL_PREFIX}/startSession/viewing"
        "?%3Aembed=yes&%3Atoolbar=no&%3AshowAppBanner=false&%3Aredirect=auth"
    )
    req2 = urllib.request.Request(
        url,
        data=_form_data(),
        method="POST",
        headers={
            "User-Agent": USER_AGENT,
            "Content-Type": "application/x-www-form-urlencoded",
        },
    )
    raw = opener.open(req2, timeout=60).read().decode("utf-8")

    match = re.search(r'sessionid.*?([A-F0-9]{20,}[^"]*)', raw, re.IGNORECASE)
    if not match:
        raise RuntimeError(
            "Could not extract session ID from startSession response. "
            "The dashboard may have changed."
        )
    return match.group(1)


def _bootstrap(opener: urllib.request.OpenerDirector, session_id: str) -> str:
    """POST to bootstrapSession and return the raw multipart response body."""
    url = f"{BASE_URL}{VIZQL_PREFIX}/bootstrapSession/sessions/{session_id}"
    req = urllib.request.Request(
        url,
        data=_form_data(),
        method="POST",
        headers={
            "User-Agent": USER_AGENT,
            "Content-Type": "application/x-www-form-urlencoded",
        },
    )
    return opener.open(req, timeout=120).read().decode("utf-8")


def _parse_multipart(raw: str) -> list[dict]:
    """Parse Tableau's length-prefixed multipart response.

    Format: <len>;<json><len>;<json>...
    Returns all parsed JSON parts.
    """
    parts: list[dict] = []
    pos = 0
    while pos < len(raw):
        sep = raw.index(";", pos)
        length = int(raw[pos:sep])
        start = sep + 1
        end = start + length
        parts.append(json.loads(raw[start:end]))
        pos = end

    if len(parts) < 2:
        raise ValueError(f"Expected ≥2 parts in VizQL response, got {len(parts)}")
    return parts


def _decode_alias(idx: int, data: list) -> object:
    """Decode a Tableau alias index into an actual value.

    Positive indices are direct lookups. Negative indices use the convention:
    -3 → data[0], -4 → data[1], etc. (-1 and -2 are reserved for null/empty.)
    """
    if idx >= 0:
        return data[idx] if idx < len(data) else None
    real_idx = -(idx + 3)
    if 0 <= real_idx < len(data):
        return data[real_idx]
    return None


def parse_bootstrap_response(raw: str) -> pl.DataFrame:
    """Parse a Tableau bootstrapSession response into a weekly ridership DataFrame.

    Extracts data from the secondaryInfo.presModelMap which contains both the
    data dictionary (raw values) and worksheet viz data (index mappings).

    Returns a DataFrame with columns: week_start (str), rides (int), riders (int).
    """
    parts = _parse_multipart(raw)
    secondary = parts[1].get("secondaryInfo", {})
    pres_map = secondary.get("presModelMap", {})

    # --- Data dictionary: raw value arrays by type ---
    dd = (
        pres_map["dataDictionary"]["presModelHolder"]
        ["genDataDictionaryPresModel"]["dataSegments"]["0"]["dataColumns"]
    )
    data_by_type: dict[str, list] = {}
    for col in dd:
        data_by_type[col["dataType"]] = col["dataValues"]

    datetimes = data_by_type.get("datetime", [])
    integers = data_by_type.get("integer", [])

    if not datetimes:
        raise ValueError("No datetime column found in data dictionary")
    if not integers:
        raise ValueError("No integer column found in data dictionary")

    # --- Worksheet: index mappings for the time series ---
    viz_data = (
        pres_map["vizData"]["presModelHolder"]
        ["genPresModelMapPresModel"]["presModelMap"]
    )
    if TIME_SERIES_SHEET not in viz_data:
        available = list(viz_data.keys())
        raise ValueError(
            f"Worksheet '{TIME_SERIES_SHEET}' not found. Available: {available}"
        )

    pane_list = (
        viz_data[TIME_SERIES_SHEET]["presModelHolder"]
        ["genVizDataPresModel"]["paneColumnsData"]["paneColumnsList"]
    )

    if len(pane_list) < 2:
        raise ValueError(
            f"Expected ≥2 panes (rides + riders), got {len(pane_list)}"
        )

    # Pane 0: rides — column 1 has date indices, column 2 has ride alias indices
    pane0_cols = pane_list[0]["vizPaneColumns"]
    date_indices = pane0_cols[1]["valueIndices"]
    ride_alias_indices = pane0_cols[2]["aliasIndices"]

    # Pane 1: riders — column 2 has rider alias indices
    pane1_cols = pane_list[1]["vizPaneColumns"]
    rider_alias_indices = pane1_cols[2]["aliasIndices"]

    n = len(date_indices)
    if len(ride_alias_indices) != n or len(rider_alias_indices) != n:
        raise ValueError(
            f"Mismatched array lengths: dates={n}, "
            f"rides={len(ride_alias_indices)}, riders={len(rider_alias_indices)}"
        )

    # Decode indices into actual values
    dates = [datetimes[i][:10] for i in date_indices]  # trim time portion
    rides = [_decode_alias(idx, integers) for idx in ride_alias_indices]
    riders = [_decode_alias(idx, integers) for idx in rider_alias_indices]

    return pl.DataFrame({
        "week_start": dates,
        "rides": rides,
        "riders": riders,
    })


def extract_ridership() -> pl.DataFrame:
    """Fetch weekly ridership data from the Allegheny Go Tableau dashboard.

    Three-step HTTP flow using stdlib only (no browser required):
    1. GET embed page → initialize cookies
    2. POST startSession/viewing → obtain VizQL session ID
    3. POST bootstrapSession → retrieve data dictionary + worksheet indices
    """
    opener = _build_opener()
    session_id = _start_session(opener)
    raw = _bootstrap(opener, session_id)
    return parse_bootstrap_response(raw)


def write_to_db(ridership_df: pl.DataFrame) -> None:
    """Write allegheny_go_weekly table (drop/recreate)."""
    conn = sqlite3.connect(DB_PATH)

    conn.execute("DROP TABLE IF EXISTS allegheny_go_weekly")
    conn.execute("""
        CREATE TABLE allegheny_go_weekly (
            week_start TEXT PRIMARY KEY,
            rides      INTEGER NOT NULL,
            riders     INTEGER NOT NULL
        )
    """)
    conn.executemany(
        "INSERT INTO allegheny_go_weekly (week_start, rides, riders) VALUES (?, ?, ?)",
        ridership_df.rows(),
    )
    conn.commit()

    count = conn.execute("SELECT COUNT(*) FROM allegheny_go_weekly").fetchone()[0]
    conn.close()
    print(f"  Wrote {count} rows to allegheny_go_weekly")


def main() -> None:
    """Entry point: extract Allegheny Go ridership and write to DB."""
    print("=" * 60)
    print("Allegheny Go Dashboard ETL")
    print("=" * 60)

    # Step 1: Try cache first
    if CACHE_FILE.exists():
        print(f"\n1. Loading cached {CACHE_FILE.name}")
        ridership_df = pl.read_csv(CACHE_FILE)
    else:
        print("\n1. Fetching data from Tableau dashboard...")
        ridership_df = extract_ridership()

        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        ridership_df.write_csv(CACHE_FILE)
        print(f"  Cached to {CACHE_FILE}")

    print(f"  Rows: {len(ridership_df)}")
    print(f"  Date range: {ridership_df['week_start'][0]} to {ridership_df['week_start'][-1]}")

    # Step 2: Write to DB
    print("\n2. Writing to database...")
    write_to_db(ridership_df)

    # Step 3: Verify
    print("\n3. Verification...")
    total_rides = ridership_df["rides"].sum()
    avg_riders = ridership_df["riders"].mean()
    print(f"  Total rides: {total_rides:,}")
    print(f"  Avg weekly riders: {avg_riders:,.0f}")

    print("\nDone.")


if __name__ == "__main__":
    main()
