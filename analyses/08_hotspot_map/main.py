"""Geographic scatter plot of stop-level on-time performance."""

from pathlib import Path

import polars as pl

from prt_otp_analysis.common import output_dir, query_to_polars, setup_plotting

HERE = Path(__file__).resolve().parent
OUT = output_dir(HERE)


def load_data() -> pl.DataFrame:
    """Load per-stop weighted OTP with coordinates."""
    return query_to_polars("""
        SELECT rs.stop_id, rs.route_id, rs.trips_7d,
               s.lat, s.lon, s.hood, s.muni,
               route_avg.avg_otp
        FROM route_stops rs
        JOIN stops s ON rs.stop_id = s.stop_id
        JOIN (
            SELECT route_id, AVG(otp) AS avg_otp
            FROM otp_monthly
            GROUP BY route_id
        ) route_avg ON rs.route_id = route_avg.route_id
    """)


def analyze(df: pl.DataFrame) -> pl.DataFrame:
    """Compute per-stop trip-weighted OTP."""
    stop_otp = (
        df.group_by(["stop_id", "lat", "lon", "hood", "muni"])
        .agg(
            weighted_otp=(pl.col("avg_otp") * pl.col("trips_7d")).sum() / pl.col("trips_7d").sum(),
            route_count=pl.col("route_id").n_unique(),
            total_trips_7d=pl.col("trips_7d").sum(),
        )
        .filter(pl.col("weighted_otp").is_not_null())
        .sort("weighted_otp")
    )
    return stop_otp


def make_chart(df: pl.DataFrame) -> None:
    """Generate geographic scatter plot colored by OTP."""
    plt = setup_plotting()
    from matplotlib.colors import Normalize

    fig, ax = plt.subplots(figsize=(12, 10))

    lon = df["lon"].to_list()
    lat = df["lat"].to_list()
    otp = df["weighted_otp"].to_list()

    norm = Normalize(vmin=0.5, vmax=0.9)
    sc = ax.scatter(
        lon, lat, c=otp, cmap="RdYlGn", norm=norm,
        s=4, alpha=0.6, edgecolors="none",
    )

    fig.colorbar(sc, ax=ax, label="Weighted Average OTP", shrink=0.8)

    system_avg = sum(otp) / len(otp)
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    ax.set_title(f"PRT Stop-Level On-Time Performance (system avg: {system_avg:.1%})")
    ax.set_aspect("equal")

    fig.tight_layout()
    fig.savefig(OUT / "hotspot_map.png", bbox_inches="tight")
    plt.close(fig)
    print(f"  Chart saved to {OUT / 'hotspot_map.png'}")


def main() -> None:
    """Entry point: load data, compute stop OTP, map, and save."""
    print("=" * 60)
    print("Analysis 08: Hot-Spot Map")
    print("=" * 60)

    print("\nLoading data...")
    raw = load_data()
    print(f"  {len(raw):,} route-stop records loaded")

    print("\nAnalyzing...")
    stop_otp = analyze(raw)
    print(f"  {len(stop_otp):,} stops with OTP computed")

    best = stop_otp.sort("weighted_otp", descending=True).head(3)
    worst = stop_otp.sort("weighted_otp").head(3)
    print("\n  Best-performing stops:")
    for row in best.iter_rows(named=True):
        hood = row["hood"] or "N/A"
        print(f"    {row['stop_id']} ({hood}): {row['weighted_otp']:.1%}")
    print("  Worst-performing stops:")
    for row in worst.iter_rows(named=True):
        hood = row["hood"] or "N/A"
        print(f"    {row['stop_id']} ({hood}): {row['weighted_otp']:.1%}")

    print("\nSaving CSV...")
    stop_otp.write_csv(OUT / "hotspot_map.csv")
    print(f"  Saved to {OUT / 'hotspot_map.csv'}")

    print("\nGenerating chart...")
    make_chart(stop_otp)

    print("\nDone.")


if __name__ == "__main__":
    main()
