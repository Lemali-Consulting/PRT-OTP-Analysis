"""Geographic scatter plot of stop-level on-time performance."""

from pathlib import Path

import folium
import polars as pl
from branca.colormap import LinearColormap

from prt_otp_analysis.common import output_dir, query_to_polars, setup_plotting

HERE = Path(__file__).resolve().parent
OUT = output_dir(HERE)
GTFS = Path(__file__).resolve().parent.parent.parent / "data" / "GTFS"


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


def load_route_shapes() -> dict[str, list[tuple[float, float]]]:
    """Load GTFS shapes and return one polyline per route (the longest variant)."""
    trips = pl.read_csv(
        GTFS / "trips.txt",
        columns=["route_id", "shape_id"],
        schema_overrides={"service_id": pl.Utf8},
    )
    shapes = pl.read_csv(GTFS / "shapes.txt")

    # Count points per shape to pick the most complete variant per route
    shape_lengths = shapes.group_by("shape_id").len()
    route_shapes = (
        trips.select("route_id", "shape_id")
        .unique()
        .join(shape_lengths, on="shape_id")
        .sort(["route_id", "len"], descending=[False, True])
        .group_by("route_id")
        .first()
    )
    best_shape_ids = set(route_shapes["shape_id"].to_list())

    # Build polylines from the selected shapes
    selected = shapes.filter(pl.col("shape_id").is_in(best_shape_ids))
    polylines: dict[str, list[tuple[float, float]]] = {}
    shape_to_route = dict(zip(
        route_shapes["shape_id"].to_list(),
        route_shapes["route_id"].to_list(),
    ))
    for shape_id, group in selected.sort("shape_pt_sequence").group_by("shape_id"):
        route_id = shape_to_route[shape_id[0]]
        polylines[str(route_id)] = list(zip(
            group["shape_pt_lat"].to_list(),
            group["shape_pt_lon"].to_list(),
        ))
    return polylines


def load_route_otp() -> dict[str, float]:
    """Load average OTP per route from the database."""
    df = query_to_polars("""
        SELECT route_id, AVG(otp) AS avg_otp
        FROM otp_monthly
        GROUP BY route_id
    """)
    return dict(zip(df["route_id"].to_list(), df["avg_otp"].to_list()))


def make_interactive_map(
    df: pl.DataFrame,
    route_shapes: dict[str, list[tuple[float, float]]],
    route_otp: dict[str, float],
) -> None:
    """Generate an interactive folium map with OTP-colored stop markers and route lines."""
    center_lat = df["lat"].mean()
    center_lon = df["lon"].mean()

    m = folium.Map(location=[center_lat, center_lon], zoom_start=11,
                   tiles="CartoDB positron")

    colormap = LinearColormap(
        colors=["#d73027", "#fee08b", "#1a9850"],  # red -> yellow -> green
        vmin=0.5, vmax=0.9,
        caption="Weighted Average OTP",
    )

    # Route lines layer (added first so stops render on top)
    routes_layer = folium.FeatureGroup(name="Route Lines", show=False)
    for route_id, coords in sorted(route_shapes.items()):
        otp = route_otp.get(route_id)
        if otp is None:
            continue
        folium.PolyLine(
            locations=coords,
            color=colormap(otp),
            weight=3,
            opacity=0.7,
            popup=folium.Popup(
                f"<b>Route {route_id}</b><br>OTP: {otp:.1%}",
                max_width=200,
            ),
        ).add_to(routes_layer)
    routes_layer.add_to(m)

    # Stops layer
    stops_layer = folium.FeatureGroup(name="Stops")
    valid = df.filter(pl.col("weighted_otp").is_not_nan() & pl.col("weighted_otp").is_not_null())
    for row in valid.iter_rows(named=True):
        otp = row["weighted_otp"]
        hood = row["hood"] if row["hood"] and row["hood"] != "0" else "N/A"
        popup_text = (
            f"<b>Stop {row['stop_id']}</b><br>"
            f"Neighborhood: {hood}<br>"
            f"Municipality: {row['muni'] or 'N/A'}<br>"
            f"OTP: {otp:.1%}<br>"
            f"Routes: {row['route_count']}<br>"
            f"Weekly trips: {row['total_trips_7d']:,}"
        )
        folium.CircleMarker(
            location=[row["lat"], row["lon"]],
            radius=2,
            color=colormap(otp),
            weight=0,
            fill=True,
            fill_color=colormap(otp),
            fill_opacity=0.7,
            popup=folium.Popup(popup_text, max_width=250),
        ).add_to(stops_layer)
    stops_layer.add_to(m)

    colormap.add_to(m)
    folium.LayerControl().add_to(m)

    # Scale marker radius with zoom: 2px at zoom 11, 3px (~50% bigger) at zoom 15.
    zoom_js = folium.Element("""
    <script>
    document.addEventListener("DOMContentLoaded", function() {
        var map = Object.values(window).find(v => v instanceof L.Map);
        function scaleMarkers() {
            var zoom = map.getZoom();
            var radius = 2 * Math.pow(1.1, zoom - 11);
            map.eachLayer(function(layer) {
                if (layer instanceof L.CircleMarker && !(layer instanceof L.Circle)) {
                    layer.setRadius(radius);
                }
            });
        }
        map.on("zoomend", scaleMarkers);
    });
    </script>
    """)
    m.get_root().html.add_child(zoom_js)

    m.save(str(OUT / "hotspot_map.html"))
    print(f"  Interactive map saved to {OUT / 'hotspot_map.html'}")


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

    print("\nLoading GTFS route shapes...")
    route_shapes = load_route_shapes()
    route_otp = load_route_otp()
    print(f"  {len(route_shapes)} route shapes loaded")

    print("\nGenerating interactive map...")
    make_interactive_map(stop_otp, route_shapes, route_otp)

    print("\nDone.")


if __name__ == "__main__":
    main()
