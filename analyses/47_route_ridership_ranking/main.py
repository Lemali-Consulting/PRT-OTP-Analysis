"""Analysis 47: Rank every PRT route by average weekday daily ridership over 2017-2024."""

import polars as pl

from prt_otp_analysis.common import analysis_dir, phase, query_to_polars, run_analysis, save_chart, save_csv, setup_plotting

OUT = analysis_dir(__file__)

# Minimum weekday months for a route's average to be considered representative.
MIN_MONTHS = 12

# Route codes excluded from the ranking. The light-rail network is recorded
# under two overlapping code schemes: BLLB/BLSV are the superseded pre-2020
# Blue Line codes whose service is already captured by BLUE/RED/SLVR across the
# full 2017-2024 period, so keeping both double-counts rail. NA/MNT/MNT1 are
# fragmentary rows with no route name.
EXCLUDED_ROUTES = {
    "BLLB": "superseded light-rail code (Blue Line - Library)",
    "BLSV": "superseded light-rail code (Blue Line - South Hills Village)",
    "MNT": "fragmentary record, no route name (1 month)",
    "MNT1": "fragmentary record, no route name (7 months)",
    "NA": "junk record, no route id/name/mode",
}

# Colours per mode for charts (DB mode labels are mixed-case).
MODE_COLOR = {
    "Bus": "#2563eb",
    "Rail": "#e11d48",
    "Light Rail": "#16a34a",
    "Incline": "#f59e0b",
    "Unknown": "#94a3b8",
}


def load_ridership() -> pl.DataFrame:
    """Load non-null route-month-daytype ridership records, dropping excluded codes."""
    placeholders = ", ".join(f"'{r}'" for r in EXCLUDED_ROUTES)
    return query_to_polars(f"""
        SELECT route_id, month, day_type, avg_riders, route_name, mode
        FROM ridership_monthly
        WHERE avg_riders IS NOT NULL
          AND route_id NOT IN ({placeholders})
    """)


def rank_routes(df: pl.DataFrame) -> pl.DataFrame:
    """Rank routes by mean weekday daily ridership, with system and cumulative share."""
    ranked = (
        df.group_by("route_id")
        .agg(
            route_name=pl.col("route_name").drop_nulls().first(),
            mode=pl.col("mode").drop_nulls().first(),
            weekday_avg_riders=pl.col("avg_riders").filter(pl.col("day_type") == "WEEKDAY").mean(),
            n_months=pl.col("avg_riders").filter(pl.col("day_type") == "WEEKDAY").count(),
            sat_avg_riders=pl.col("avg_riders").filter(pl.col("day_type") == "SAT.").mean(),
            sun_avg_riders=pl.col("avg_riders").filter(pl.col("day_type") == "SUN.").mean(),
        )
        .filter(pl.col("weekday_avg_riders").is_not_null())
        .with_columns(pl.col("mode").fill_null("Unknown"))
        .sort("weekday_avg_riders", descending=True)
    )

    total = ranked["weekday_avg_riders"].sum()
    ranked = (
        ranked.with_columns(
            rank=pl.Series("rank", range(1, len(ranked) + 1)),
            system_share=pl.col("weekday_avg_riders") / total,
            short_history=pl.col("n_months") < MIN_MONTHS,
        )
        .with_columns(cum_share=pl.col("system_share").cum_sum())
        .select(
            "rank", "route_id", "route_name", "mode",
            "weekday_avg_riders", "sat_avg_riders", "sun_avg_riders",
            "n_months", "short_history", "system_share", "cum_share",
        )
    )
    return ranked


def mode_summary(ranked: pl.DataFrame) -> pl.DataFrame:
    """Total weekday ridership and route count per mode."""
    return (
        ranked.group_by("mode")
        .agg(
            n_routes=pl.len(),
            total_weekday_riders=pl.col("weekday_avg_riders").sum(),
        )
        .sort("total_weekday_riders", descending=True)
    )


def make_top25_chart(ranked: pl.DataFrame) -> None:
    """Horizontal bar chart of the 25 busiest routes, coloured by mode."""
    plt = setup_plotting()
    top = ranked.head(25).reverse()  # reverse so rank 1 sits at the top

    labels = top["route_id"].to_list()
    values = top["weekday_avg_riders"].to_list()
    colors = [MODE_COLOR.get(m, MODE_COLOR["Unknown"]) for m in top["mode"].to_list()]

    fig, ax = plt.subplots(figsize=(10, 9))
    bars = ax.barh(labels, values, color=colors)
    ax.bar_label(bars, labels=[f"{v:,.0f}" for v in values], padding=3, fontsize=8)

    ax.set_xlabel("Average Weekday Daily Riders (2017-2024)")
    ax.set_ylabel("Route")
    ax.set_title("25 Busiest PRT Routes by Average Weekday Ridership")
    ax.margins(x=0.12)

    seen = list(dict.fromkeys(top["mode"].to_list()))
    handles = [plt.Rectangle((0, 0), 1, 1, color=MODE_COLOR.get(m, MODE_COLOR["Unknown"])) for m in seen]
    ax.legend(handles, seen, title="Mode", loc="lower right", fontsize=9)

    save_chart(fig, OUT / "top25_ridership.png")


def make_mode_chart(modes: pl.DataFrame) -> None:
    """Bar chart of total weekday ridership by mode, annotated with route counts."""
    plt = setup_plotting()
    labels = modes["mode"].to_list()
    values = modes["total_weekday_riders"].to_list()
    counts = modes["n_routes"].to_list()
    colors = [MODE_COLOR.get(m, MODE_COLOR["Unknown"]) for m in labels]

    fig, ax = plt.subplots(figsize=(8, 6))
    bars = ax.bar(labels, values, color=colors)
    ax.bar_label(
        bars,
        labels=[f"{v:,.0f}\n({c} routes)" for v, c in zip(values, counts)],
        padding=3,
        fontsize=9,
    )

    ax.set_ylabel("Total Average Weekday Daily Riders")
    ax.set_xlabel("Mode")
    ax.set_title("Weekday Ridership by Mode (Sum of Route Averages, 2017-2024)")
    ax.margins(y=0.15)

    save_chart(fig, OUT / "ridership_by_mode.png")


@run_analysis(47, "Route Ridership Ranking")
def main() -> None:
    """Entry point: rank routes by weekday ridership, summarise by mode, save outputs."""

    with phase("Loading ridership data"):
        ride_df = load_ridership()
        print(f"  {len(ride_df):,} rows, {ride_df['route_id'].n_unique()} routes")
        print(f"  Month range: {ride_df['month'].min()} to {ride_df['month'].max()}")
        print(f"  Excluded {len(EXCLUDED_ROUTES)} route codes:")
        for code, reason in EXCLUDED_ROUTES.items():
            print(f"    {code:<5s} - {reason}")

    with phase("Ranking routes by weekday ridership"):
        ranked = rank_routes(ride_df)
        total = ranked["weekday_avg_riders"].sum()
        print(f"  {len(ranked)} routes ranked")
        print(f"  System total: {total:,.0f} avg weekday daily riders")
        short = ranked.filter(pl.col("short_history"))
        print(f"  {len(short)} routes flagged with < {MIN_MONTHS} weekday months")

        print("\n  Top 10 routes:")
        for row in ranked.head(10).iter_rows(named=True):
            print(f"    {row['rank']:>3}. {row['route_id']:<8s} "
                  f"{row['weekday_avg_riders']:>8,.0f}/wkday  "
                  f"({row['system_share']:.1%}, cum {row['cum_share']:.1%})  {row['mode']}")

        # Where does cumulative share cross key thresholds?
        for target in (0.50, 0.80):
            crossed = ranked.filter(pl.col("cum_share") >= target)
            if len(crossed) > 0:
                n_routes = crossed["rank"].min()
                print(f"  Top {n_routes} routes carry {target:.0%} of weekday ridership")

    with phase("Summarising by mode"):
        modes = mode_summary(ranked)
        for row in modes.iter_rows(named=True):
            print(f"    {row['mode']:<12s}: {row['total_weekday_riders']:>10,.0f} riders "
                  f"across {row['n_routes']} routes")

    with phase("Saving CSV"):
        save_csv(ranked, OUT / "route_ridership_ranking.csv")
        save_csv(modes, OUT / "ridership_by_mode.csv")

    with phase("Generating charts"):
        make_top25_chart(ranked)
        make_mode_chart(modes)


if __name__ == "__main__":
    main()
