"""Analysis 42: cross-reference Allegheny Go adoption with municipal OTP."""

import re

import polars as pl
from scipy import stats

from prt_otp_analysis.common import (
    DATA_DIR,
    OTP_GOOD_THRESHOLD,
    OTP_WARNING_THRESHOLD,
    analysis_dir,
    phase,
    query_to_polars,
    run_analysis,
    save_chart,
    save_csv,
    setup_plotting,
    weighted_mean,
)

OUT = analysis_dir(__file__)
AG_DIR = DATA_DIR / "allegheny-go"
MIN_STOPS = 10

TIER_MIDPOINTS: dict[str, int] = {
    "1 - 5": 3,
    "6 - 25": 15,
    "26 - 50": 38,
    "51 - 100": 75,
    "101 - 500": 200,
}

# Regex to extract the base municipality name from the DB format
# "Baldwin borough (Allegheny, PA)" → "baldwin"
_DB_MUNI_RE = re.compile(
    r"^(.+?)\s+(?:borough|city|township|municipality)\s+\(",
    re.IGNORECASE,
)


def normalize_muni(name: str) -> str:
    """Normalize a municipality name to a lowercase key for joining."""
    # DB format: "Baldwin borough (Allegheny, PA)"
    m = _DB_MUNI_RE.match(name)
    if m:
        return m.group(1).strip().lower()
    # Tract format: "Baldwin Borough", "City of Pittsburgh", "Ross Township"
    key = name.strip()
    if key.lower().startswith("city of "):
        key = key[8:]
    for suffix in [" Borough", " Township", " Municipality", " borough", " township"]:
        if key.endswith(suffix):
            key = key[: -len(suffix)]
    return key.lower()


def load_tract_reach() -> pl.DataFrame:
    """Load tract reach data with midpoint households."""
    tract_df = pl.read_csv(AG_DIR / "tract_reach.csv")
    tract_df = tract_df.filter(
        (pl.col("municipality") != "Unpopulated Areas")
        & (pl.col("municipality") != "%null%")
        & pl.col("municipality").is_not_null()
    )
    tract_df = tract_df.with_columns(
        midpoint=pl.col("reached_households").replace_strict(
            TIER_MIDPOINTS, return_dtype=pl.Int64
        ),
        muni_key=pl.col("municipality").map_elements(
            normalize_muni, return_dtype=pl.Utf8
        ),
    )
    return tract_df


def aggregate_adoption(tract_df: pl.DataFrame) -> pl.DataFrame:
    """Aggregate tract-level adoption to municipality level."""
    return (
        tract_df.group_by("muni_key")
        .agg(
            municipality=pl.col("municipality").first(),
            total_households=pl.col("midpoint").sum(),
            n_tracts=pl.len(),
            mean_lat=pl.col("lat").mean(),
            mean_lon=pl.col("lon").mean(),
        )
        .sort("total_households", descending=True)
    )


def load_muni_otp() -> pl.DataFrame:
    """Compute trip-weighted OTP per municipality (same pattern as Analysis 15)."""
    stop_otp_df = query_to_polars("""
        SELECT rs.stop_id, rs.route_id, rs.trips_wd,
               s.muni, s.county,
               AVG(o.otp) AS route_avg_otp
        FROM route_stops rs
        JOIN stops s ON rs.stop_id = s.stop_id
        JOIN otp_monthly o ON rs.route_id = o.route_id
        WHERE s.muni IS NOT NULL AND s.muni != '0'
        GROUP BY rs.stop_id, rs.route_id, rs.trips_wd, s.muni, s.county
    """)

    muni_otp_df = (
        stop_otp_df.group_by("muni", "county")
        .agg(
            avg_otp=weighted_mean("route_avg_otp", "trips_wd"),
            n_stops=pl.col("stop_id").n_unique(),
            n_routes=pl.col("route_id").n_unique(),
        )
        .filter(pl.col("n_stops") >= MIN_STOPS)
        .with_columns(
            muni_key=pl.col("muni").map_elements(
                normalize_muni, return_dtype=pl.Utf8
            ),
        )
    )
    return muni_otp_df


def join_adoption_otp(
    adoption_df: pl.DataFrame, muni_otp_df: pl.DataFrame
) -> pl.DataFrame:
    """Join adoption and OTP on normalized municipality name."""
    joined_df = adoption_df.join(muni_otp_df, on="muni_key", how="inner")

    n_adoption = len(adoption_df)
    n_otp = len(muni_otp_df)
    n_joined = len(joined_df)
    print(f"  Adoption municipalities: {n_adoption}")
    print(f"  OTP municipalities (≥{MIN_STOPS} stops): {n_otp}")
    print(f"  Matched: {n_joined}")
    print(f"  Unmatched adoption: {n_adoption - n_joined}")

    return joined_df.sort("total_households", descending=True)


def analyze(joined_df: pl.DataFrame) -> dict[str, float]:
    """Compute correlation between adoption and OTP."""
    results: dict[str, float] = {}
    households = joined_df["total_households"].to_list()
    otp = joined_df["avg_otp"].to_list()

    rho, p = stats.spearmanr(households, otp)
    results["spearman_rho"] = rho
    results["spearman_p"] = p
    results["n_munis"] = len(joined_df)

    # Robustness: without Pittsburgh
    no_pgh_df = joined_df.filter(pl.col("muni_key") != "pittsburgh")
    if len(no_pgh_df) > 3:
        rho2, p2 = stats.spearmanr(
            no_pgh_df["total_households"].to_list(),
            no_pgh_df["avg_otp"].to_list(),
        )
        results["spearman_rho_no_pgh"] = rho2
        results["spearman_p_no_pgh"] = p2
        results["n_munis_no_pgh"] = len(no_pgh_df)

    return results


def make_scatter(joined_df: pl.DataFrame, results: dict[str, float]) -> None:
    """Scatter plot of adoption vs OTP by municipality."""
    plt = setup_plotting()
    fig, ax = plt.subplots(figsize=(10, 7))

    otp = joined_df["avg_otp"].to_list()
    households = joined_df["total_households"].to_list()
    n_tracts = joined_df["n_tracts"].to_list()

    sizes = [max(20, t * 8) for t in n_tracts]
    colors = [
        "#22c55e" if v >= OTP_GOOD_THRESHOLD
        else "#f59e0b" if v >= OTP_WARNING_THRESHOLD
        else "#ef4444"
        for v in otp
    ]

    ax.scatter(otp, households, s=sizes, c=colors, alpha=0.7, edgecolors="white")

    # Label top municipalities by adoption
    top_df = joined_df.sort("total_households", descending=True).head(8)
    for row in top_df.iter_rows(named=True):
        ax.annotate(
            row["municipality"],
            (row["avg_otp"], row["total_households"]),
            fontsize=7, alpha=0.8,
            xytext=(5, 3), textcoords="offset points",
        )

    # Reference lines
    median_otp = joined_df["avg_otp"].median()
    median_adopt = joined_df["total_households"].median()
    ax.axvline(median_otp, color="#9ca3af", linestyle=":", alpha=0.5)
    ax.axhline(median_adopt, color="#9ca3af", linestyle=":", alpha=0.5)

    rho = results["spearman_rho"]
    p = results["spearman_p"]
    ax.set_title("Allegheny Go Adoption vs On-Time Performance by Municipality")
    ax.set_xlabel("Trip-Weighted Average OTP")
    ax.set_ylabel("Est. Reached Households (midpoint sum)")
    ax.text(
        0.02, 0.98,
        f"Spearman ρ = {rho:.3f} (p = {p:.3f}, n = {results['n_munis']})",
        transform=ax.transAxes, fontsize=9, va="top",
    )

    save_chart(fig, OUT / "adoption_vs_otp.png")


def make_demographics_chart() -> None:
    """Bar charts summarizing program demographics."""
    plt = setup_plotting()
    demo_df = pl.read_csv(AG_DIR / "demographics_summary.csv")

    categories = ["age", "race", "gender", "children_in_household"]
    titles = ["Age Distribution", "Race Distribution", "Gender", "Children in Household"]

    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    axes = axes.flatten()

    for ax, cat, title in zip(axes, categories, titles):
        subset_df = demo_df.filter(pl.col("category") == cat)
        groups = subset_df["group"].to_list()
        counts = subset_df["count"].to_list()

        # Wrap long labels
        groups = [g[:25] + "..." if len(g) > 28 else g for g in groups]

        bars = ax.barh(range(len(groups)), counts, color="#3b82f6", edgecolor="white")
        ax.set_yticks(range(len(groups)))
        ax.set_yticklabels(groups, fontsize=8)
        ax.set_title(title, fontsize=11)
        ax.invert_yaxis()
        for i, c in enumerate(counts):
            ax.text(c + max(counts) * 0.01, i, f"{c:,}", va="center", fontsize=8)

    fig.suptitle("Allegheny Go Program Demographics", fontsize=14, y=1.01)
    fig.tight_layout()
    save_chart(fig, OUT / "demographics_summary.png")


@run_analysis(42, "Allegheny Go Equity")
def main() -> None:
    """Entry point: cross-reference Allegheny Go adoption with municipal OTP."""
    with phase("Loading tract reach data"):
        tract_df = load_tract_reach()
        print(f"  {len(tract_df)} tracts after filtering")
        adoption_df = aggregate_adoption(tract_df)
        print(f"  {len(adoption_df)} municipalities with adoption data")

    with phase("Loading municipal OTP"):
        muni_otp_df = load_muni_otp()
        print(f"  {len(muni_otp_df)} municipalities with ≥{MIN_STOPS} stops")

    with phase("Joining and analyzing"):
        joined_df = join_adoption_otp(adoption_df, muni_otp_df)
        results = analyze(joined_df)

        rho = results["spearman_rho"]
        p = results["spearman_p"]
        print(f"  Spearman ρ = {rho:.3f} (p = {p:.3f})")
        if "spearman_rho_no_pgh" in results:
            print(
                f"  Without Pittsburgh: ρ = {results['spearman_rho_no_pgh']:.3f} "
                f"(p = {results['spearman_p_no_pgh']:.3f})"
            )

        save_csv(joined_df.select(
            "municipality", "muni", "avg_otp", "n_stops", "n_routes",
            "total_households", "n_tracts",
        ), OUT / "muni_adoption_otp.csv")

    with phase("Generating charts"):
        make_scatter(joined_df, results)
        make_demographics_chart()


if __name__ == "__main__":
    main()
