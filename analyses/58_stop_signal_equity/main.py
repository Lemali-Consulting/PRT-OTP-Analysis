"""Analysis 58: Test whether traffic-signal stop placement varies with neighborhood demographics."""

from prt_otp_analysis.common import (
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


def build_stop_demographics() -> pl.DataFrame:
    """Join authoritative signal class to each stop's census-tract demographics."""
    signals_df = load_stop_signals()
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
    )
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
    return (
        inc_df.group_by("income_quartile")
        .agg(
            n_stops=pl.len(),
            n_signalized=pl.col("is_signalized").sum(),
            n_nearside=pl.col("is_nearside").sum(),
            n_signal_classified=pl.col("signal_class").is_in(["nearside", "farside"]).sum(),
        )
        .with_columns(
            signalized_share=pl.col("n_signalized") / pl.col("n_stops"),
            nearside_share=pl.when(pl.col("n_signal_classified") > 0)
            .then(pl.col("n_nearside") / pl.col("n_signal_classified"))
            .otherwise(None),
        )
        .sort("income_quartile")
    )


def tract_summary(df: pl.DataFrame) -> pl.DataFrame:
    """Per-tract signalized/near-side shares plus demographic ratios."""
    return (
        df.group_by("geoid")
        .agg(
            n_stops=pl.len(),
            n_signalized=pl.col("is_signalized").sum(),
            n_nearside=pl.col("is_nearside").sum(),
            n_signal_classified=pl.col("signal_class").is_in(["nearside", "farside"]).sum(),
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


@run_analysis(58, "Stop Signal Placement Equity")
def main() -> None:
    """Entry point: join signals to tract demographics and test for disparity."""
    with phase("Joining signal class to census-tract demographics"):
        df = build_stop_demographics()
        n_income = df.drop_nulls("median_household_income").height
        print(f"  {df.height} stops joined to a tract; {n_income} have median income")

    with phase("Income-quartile shares"):
        quartile_df = income_quartile_table(df)
        for row in quartile_df.iter_rows(named=True):
            print(f"  {row['income_quartile']:<22s} "
                  f"n={row['n_stops']:5d}  signalized={row['signalized_share']:.1%}  "
                  f"near-side={row['nearside_share']:.1%}")

    with phase("Tract-level demographic correlations"):
        tract_df = tract_summary(df)
        sig_df = tract_df.filter(pl.col("n_stops") >= MIN_STOPS_PER_TRACT)
        near_df = tract_df.filter(pl.col("n_signal_classified") >= MIN_SIGNALIZED_PER_TRACT)
        corr_rows = []
        print(f"  Signalized-share correlations (tracts with >= {MIN_STOPS_PER_TRACT} "
              f"stops, n = {sig_df.height}):")
        for col, label in DEMOGRAPHICS:
            c = correlate(sig_df, col, "signalized_share")
            print(f"    vs {label:<28s}: rho = {c['spearman_r']:+.3f}, p = {c['spearman_p']:.4f}")
            corr_rows.append({"outcome": "signalized_share", "demographic": col,
                              "spearman_r": c["spearman_r"], "spearman_p": c["spearman_p"],
                              "n": c["n"]})
        print(f"  Near-side-share correlations (tracts with >= {MIN_SIGNALIZED_PER_TRACT} "
              f"signalized stops, n = {near_df.height}):")
        for col, label in DEMOGRAPHICS:
            c = correlate(near_df, col, "nearside_share")
            print(f"    vs {label:<28s}: rho = {c['spearman_r']:+.3f}, p = {c['spearman_p']:.4f}")
            corr_rows.append({"outcome": "nearside_share", "demographic": col,
                              "spearman_r": c["spearman_r"], "spearman_p": c["spearman_p"],
                              "n": c["n"]})

    with phase("Saving outputs"):
        save_csv(
            df.select("stop_id", "signal_class", "has_signal", "geoid",
                      "median_household_income"),
            OUT / "stop_equity.csv",
        )
        save_csv(tract_df.sort("median_household_income"), OUT / "tract_equity_summary.csv")
        save_csv(quartile_df, OUT / "income_quartile_shares.csv")
        save_csv(pl.DataFrame(corr_rows), OUT / "demographic_correlations.csv")

    with phase("Generating charts"):
        make_quartile_chart(quartile_df)
        make_scatter_chart(tract_df)


if __name__ == "__main__":
    main()
