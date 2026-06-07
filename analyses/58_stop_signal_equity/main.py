"""Analysis 58: Test whether traffic-signal stop placement varies with neighborhood demographics."""

from prt_otp_analysis.common import (
    DATA_DIR,
    analysis_dir,
    correlate,
    phase,
    query_to_polars,
    run_analysis,
    save_chart,
    save_csv,
    setup_plotting,
)
from prt_otp_analysis.common.schemas import STOP_SIGNALS, validate
from prt_otp_analysis.stop_tracts import assign_stops_to_tracts

import numpy as np
import polars as pl
from scipy import stats

OUT = analysis_dir(__file__)

MIN_STOPS_PER_TRACT = 5        # for signalized-share correlation
MIN_SIGNALIZED_PER_TRACT = 3   # for near-side-share correlation

QUARTILE_LABELS = ["Q1 (lowest income)", "Q2", "Q3", "Q4 (highest income)"]

# Demographic measures tested against signal placement.
DEMOGRAPHICS = [
    ("median_household_income", "median household income"),
    ("zero_vehicle_share", "zero-vehicle household share"),
    ("black_share", "Black population share"),
]


def load_stop_signals() -> pl.DataFrame:
    """Per-stop authoritative signal class, keyed by PRT internal stop_id."""
    df = query_to_polars(
        """SELECT stop_id, signal_class, has_signal
           FROM stop_signals WHERE stop_id IS NOT NULL"""
    )
    validate(df, STOP_SIGNALS, subset=True)
    return df


def load_stop_ridership() -> pl.DataFrame:
    """Per-stop pre-pandemic weekday usage (boardings + alightings).

    Keyed by the PRT internal `stop_id` (E-code), the same namespace as
    `stop_signals` and the `stops` table, so it joins directly. Usage is
    averaged across measurement days within a route, then summed across the
    routes serving each physical stop — the same construction Analysis 32/34
    use for stop-level ridership.
    """
    csv_path = DATA_DIR / "bus-stop-usage" / "wprdc_stop_data.csv"
    df = pl.read_csv(csv_path, null_values=["NA", ""]).filter(
        (pl.col("time_period") == "Pre-pandemic")
        & (pl.col("serviceday") == "Weekday")
    )
    per_stop_route = (
        df.group_by(["stop_id", "route_name"])
        .agg(pl.col("avg_ons").mean(), pl.col("avg_offs").mean())
    )
    return (
        per_stop_route.group_by("stop_id")
        .agg(pl.col("avg_ons").sum(), pl.col("avg_offs").sum())
        .with_columns(usage=pl.col("avg_ons") + pl.col("avg_offs"))
        .select("stop_id", "usage")
    )


def build_stop_demographics() -> pl.DataFrame:
    """Join authoritative signal class to each stop's census-tract demographics."""
    signals_df = load_stop_signals()
    ridership_df = load_stop_ridership()
    tract_df = assign_stops_to_tracts(
        ["median_household_income", "households_total",
         "households_zero_vehicle", "pop_black_nh"],
    )
    df = signals_df.join(
        tract_df.select(
            "stop_id", "geoid", "population", "median_household_income",
            "households_total", "households_zero_vehicle", "pop_black_nh",
        ),
        on="stop_id",
        how="inner",
    ).join(ridership_df, on="stop_id", how="left")
    return df.with_columns(
        is_nearside=(pl.col("signal_class") == "nearside").cast(pl.Int64),
        is_signalized=pl.col("has_signal"),
    )


def income_quartile_table(df: pl.DataFrame) -> pl.DataFrame:
    """Signalized-stop and near-side shares by tract-income quartile of each stop."""
    inc_df = df.drop_nulls("median_household_income")
    inc = inc_df["median_household_income"].to_numpy()
    cuts = np.quantile(inc, [0.25, 0.5, 0.75])

    def to_quartile(value: float) -> str:
        idx = int(np.searchsorted(cuts, value, side="right"))
        return QUARTILE_LABELS[min(idx, 3)]

    inc_df = inc_df.with_columns(
        pl.col("median_household_income")
        .map_elements(to_quartile, return_dtype=pl.Utf8)
        .alias("income_quartile"),
    )
    # Ridership weights (usage at signalized / near-side stops vs all stops).
    classified = pl.col("signal_class").is_in(["nearside", "farside"])
    use = pl.col("usage")
    return (
        inc_df.group_by("income_quartile")
        .agg(
            n_stops=pl.len(),
            n_signalized=pl.col("is_signalized").sum(),
            n_nearside=pl.col("is_nearside").sum(),
            n_signal_classified=classified.sum(),
            # Ridership-weighted numerators/denominators (usage-null stops drop out).
            use_total=use.sum(),
            use_signalized=use.filter(pl.col("is_signalized") == 1).sum(),
            use_classified=use.filter(classified).sum(),
            use_nearside=use.filter(pl.col("is_nearside") == 1).sum(),
        )
        .with_columns(
            signalized_share=pl.col("n_signalized") / pl.col("n_stops"),
            nearside_share=pl.when(pl.col("n_signal_classified") > 0)
            .then(pl.col("n_nearside") / pl.col("n_signal_classified"))
            .otherwise(None),
            rw_signalized_share=pl.when(pl.col("use_total") > 0)
            .then(pl.col("use_signalized") / pl.col("use_total"))
            .otherwise(None),
            rw_nearside_share=pl.when(pl.col("use_classified") > 0)
            .then(pl.col("use_nearside") / pl.col("use_classified"))
            .otherwise(None),
        )
        .sort("income_quartile")
    )


def tract_summary(df: pl.DataFrame) -> pl.DataFrame:
    """Per-tract signalized/near-side shares plus demographic ratios."""
    classified = pl.col("signal_class").is_in(["nearside", "farside"])
    use = pl.col("usage")
    return (
        df.group_by("geoid")
        .agg(
            n_stops=pl.len(),
            n_signalized=pl.col("is_signalized").sum(),
            n_nearside=pl.col("is_nearside").sum(),
            n_signal_classified=classified.sum(),
            use_total=use.sum(),
            use_signalized=use.filter(pl.col("is_signalized") == 1).sum(),
            use_classified=use.filter(classified).sum(),
            use_nearside=use.filter(pl.col("is_nearside") == 1).sum(),
            median_household_income=pl.col("median_household_income").first(),
            population=pl.col("population").first(),
            households_total=pl.col("households_total").first(),
            households_zero_vehicle=pl.col("households_zero_vehicle").first(),
            pop_black_nh=pl.col("pop_black_nh").first(),
        )
        .with_columns(
            signalized_share=pl.col("n_signalized") / pl.col("n_stops"),
            nearside_share=pl.when(pl.col("n_signal_classified") > 0)
            .then(pl.col("n_nearside") / pl.col("n_signal_classified"))
            .otherwise(None),
            rw_signalized_share=pl.when(pl.col("use_total") > 0)
            .then(pl.col("use_signalized") / pl.col("use_total"))
            .otherwise(None),
            rw_nearside_share=pl.when(pl.col("use_classified") > 0)
            .then(pl.col("use_nearside") / pl.col("use_classified"))
            .otherwise(None),
            zero_vehicle_share=pl.when(pl.col("households_total") > 0)
            .then(pl.col("households_zero_vehicle") / pl.col("households_total"))
            .otherwise(None),
            black_share=pl.when(pl.col("population") > 0)
            .then(pl.col("pop_black_nh") / pl.col("population"))
            .otherwise(None),
        )
    )


def make_quartile_chart(quartile_df: pl.DataFrame) -> None:
    """Grouped bar chart: signalized-stop share and near-side share by income quartile."""
    plt = setup_plotting()
    fig, ax = plt.subplots(figsize=(9, 6))

    order = quartile_df.sort("income_quartile")
    labels = order["income_quartile"].to_list()
    sig = (order["signalized_share"] * 100).to_list()
    near = (order["nearside_share"] * 100).to_list()

    x = np.arange(len(labels))
    width = 0.38
    b1 = ax.bar(x - width / 2, sig, width, label="Signalized-stop share",
                color="#2563eb", alpha=0.85)
    b2 = ax.bar(x + width / 2, near, width, label="Near-side share (of signalized)",
                color="#e11d48", alpha=0.85)
    ax.bar_label(b1, fmt="%.1f%%", padding=3, fontsize=9)
    ax.bar_label(b2, fmt="%.1f%%", padding=3, fontsize=9)

    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=9)
    ax.set_ylabel("Percent")
    ax.set_ylim(0, max(near + sig) * 1.18)
    ax.set_title("Signal Stop Placement by Neighborhood Income Quartile\n"
                 "(flat bars = no income disparity)", fontweight="bold")
    ax.legend(fontsize=9)
    save_chart(fig, OUT / "signal_share_by_income_quartile.png")


def make_scatter_chart(tract_df: pl.DataFrame) -> None:
    """Scatter: tract median income vs signalized-stop share."""
    plt = setup_plotting()
    fig, ax = plt.subplots(figsize=(8, 6))

    d = tract_df.filter(
        (pl.col("n_stops") >= MIN_STOPS_PER_TRACT)
        & pl.col("median_household_income").is_not_null()
    )
    income = d["median_household_income"].to_numpy() / 1000.0
    share = d["signalized_share"].to_numpy() * 100

    ax.scatter(income, share, alpha=0.5, s=30, color="#2563eb",
               edgecolors="white", linewidth=0.5)
    slope, intercept, r, p, _ = stats.linregress(income, share)
    x_line = np.array([income.min(), income.max()])
    ax.plot(x_line, slope * x_line + intercept, color="#e11d48", linewidth=1.5,
            linestyle="--", alpha=0.7, label=f"r={r:.3f}, p={p:.4f}")

    ax.set_xlabel("Tract median household income ($1,000s)")
    ax.set_ylabel("Signalized-stop share (%)")
    ax.set_title(f"Tract Income vs Signalized-Stop Share "
                 f"(>= {MIN_STOPS_PER_TRACT} stops, n = {d.height})", fontweight="bold")
    ax.legend(fontsize=9)
    save_chart(fig, OUT / "tract_income_vs_signal_share.png")


def make_weighted_comparison_chart(quartile_df: pl.DataFrame) -> None:
    """Stop-counted vs ridership-weighted near-side share by income quartile."""
    plt = setup_plotting()
    fig, ax = plt.subplots(figsize=(9, 6))

    order = quartile_df.sort("income_quartile")
    labels = order["income_quartile"].to_list()
    unweighted = (order["nearside_share"] * 100).to_list()
    weighted = (order["rw_nearside_share"] * 100).to_list()

    x = np.arange(len(labels))
    width = 0.38
    b1 = ax.bar(x - width / 2, unweighted, width, label="Per stop (unweighted)",
                color="#64748b", alpha=0.85)
    b2 = ax.bar(x + width / 2, weighted, width, label="Per rider (ridership-weighted)",
                color="#e11d48", alpha=0.85)
    ax.bar_label(b1, fmt="%.1f%%", padding=3, fontsize=9)
    ax.bar_label(b2, fmt="%.1f%%", padding=3, fontsize=9)

    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=9)
    ax.set_ylabel("Near-side share of signalized stops (%)")
    ax.set_ylim(0, max(unweighted + weighted) * 1.18)
    ax.set_title("Near-Side Exposure by Income Quartile: Per Stop vs Per Rider\n"
                 "(flat across quartiles under both weightings)", fontweight="bold")
    ax.legend(fontsize=9)
    save_chart(fig, OUT / "nearside_share_rider_weighted.png")


@run_analysis(58, "Stop Signal Placement Equity")
def main() -> None:
    """Entry point: join signals to tract demographics and test for disparity."""
    with phase("Joining signal class to census-tract demographics"):
        df = build_stop_demographics()
        n_income = df.drop_nulls("median_household_income").height
        print(f"  {df.height} stops joined to a tract; {n_income} have median income")

    with phase("Income-quartile shares (per stop and per rider)"):
        quartile_df = income_quartile_table(df)
        for row in quartile_df.iter_rows(named=True):
            print(f"  {row['income_quartile']:<22s} n={row['n_stops']:5d}  "
                  f"near-side per-stop={row['nearside_share']:.1%}  "
                  f"per-rider={row['rw_nearside_share']:.1%}")

    with phase("Tract-level demographic correlations (per stop and per rider)"):
        tract_df = tract_summary(df)
        sig_df = tract_df.filter(pl.col("n_stops") >= MIN_STOPS_PER_TRACT)
        near_df = tract_df.filter(pl.col("n_signal_classified") >= MIN_SIGNALIZED_PER_TRACT)
        corr_rows = []
        # (outcome label, tract subset, unweighted col, ridership-weighted col)
        outcomes = [
            ("signalized_share", sig_df, "signalized_share", "rw_signalized_share"),
            ("nearside_share", near_df, "nearside_share", "rw_nearside_share"),
        ]
        for name, subset_df, uw_col, rw_col in outcomes:
            print(f"  {name} (n = {subset_df.height} tracts):")
            for col, label in DEMOGRAPHICS:
                cu = correlate(subset_df, col, uw_col)
                cw = correlate(subset_df, col, rw_col)
                print(f"    vs {label:<28s}: per-stop rho={cu['spearman_r']:+.3f} "
                      f"(p={cu['spearman_p']:.3f})  per-rider rho={cw['spearman_r']:+.3f} "
                      f"(p={cw['spearman_p']:.3f})")
                corr_rows.append({"outcome": name, "demographic": col, "weighting": "per_stop",
                                  "spearman_r": cu["spearman_r"], "spearman_p": cu["spearman_p"],
                                  "n": cu["n"]})
                corr_rows.append({"outcome": name, "demographic": col, "weighting": "per_rider",
                                  "spearman_r": cw["spearman_r"], "spearman_p": cw["spearman_p"],
                                  "n": cw["n"]})

    with phase("Saving outputs"):
        save_csv(
            df.select("stop_id", "signal_class", "has_signal", "usage", "geoid",
                      "median_household_income"),
            OUT / "stop_equity.csv",
        )
        save_csv(tract_df.sort("median_household_income"), OUT / "tract_equity_summary.csv")
        save_csv(quartile_df, OUT / "income_quartile_shares.csv")
        save_csv(pl.DataFrame(corr_rows), OUT / "demographic_correlations.csv")

    with phase("Generating charts"):
        make_quartile_chart(quartile_df)
        make_scatter_chart(tract_df)
        make_weighted_comparison_chart(quartile_df)


if __name__ == "__main__":
    main()
