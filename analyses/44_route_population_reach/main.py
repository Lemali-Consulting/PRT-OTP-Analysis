"""Analysis 44: rank PRT routes by resident population within walking distance of their stops.

Buffers each stop, dissolves per route, areal-interpolates against ACS tract population.
"""

from pathlib import Path

import geopandas as gpd
import matplotlib.pyplot as plt
import polars as pl

from prt_otp_analysis.common import (
    MODE_COLORS,
    output_dir,
    phase,
    run_analysis,
    save_chart,
    save_csv,
    setup_plotting,
)
from prt_otp_analysis.walksheds import (
    build_route_walksheds,
    load_stops_with_routes,
    load_tracts,
    population_per_route,
)

HERE = Path(__file__).resolve().parent
OUT = output_dir(HERE)


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
