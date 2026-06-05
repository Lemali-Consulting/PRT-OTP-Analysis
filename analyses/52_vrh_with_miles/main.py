"""Analysis 52: trends in PRT's vehicle revenue hours and vehicle revenue miles
by mode, and what the VRM/VRH ratio (operating speed) reveals about service change."""

import polars as pl

from prt_otp_analysis.common import (
    COLOR_GRAY,
    analysis_dir,
    phase,
    query_to_polars,
    run_analysis,
    save_chart,
    save_csv,
    setup_plotting,
)
from prt_otp_analysis.common.schemas import NTD_RIDERSHIP, validate

OUT = analysis_dir(__file__)

PRT_NTD_ID = 30022
START_YEAR = 2002
BASELINE_YEAR = 2019
COMPARE_YEAR = 2024

MODE_NAMES = {
    "MB": "Motor Bus",
    "LR": "Light Rail",
    "DR": "Paratransit",
    "IP": "Incline",
}
# IP excluded from speed analysis — short vertical track makes mph uninformative.
SPEED_MODES = ["MB", "LR", "DR"]
MODE_COLORS = {
    "MB": "#3b82f6",
    "LR": "#22c55e",
    "DR": "#f59e0b",
}


def load_mode_year() -> pl.DataFrame:
    """Load PRT monthly VRH/VRM by mode and aggregate to calendar years."""
    raw_df = query_to_polars(
        "SELECT mode, month, vrh, vrm FROM ntd_ridership WHERE ntd_id = ?",
        (PRT_NTD_ID,),
    )
    validate(raw_df, NTD_RIDERSHIP, subset=True)

    return (
        raw_df.with_columns(year=pl.col("month").str.slice(0, 4).cast(pl.Int64))
        .filter(pl.col("year").is_between(START_YEAR, COMPARE_YEAR))
        .group_by("mode", "year")
        .agg(vrh=pl.col("vrh").sum(), vrm=pl.col("vrm").sum())
        .sort("mode", "year")
        .with_columns(
            mph=pl.when(pl.col("vrh") > 0)
            .then(pl.col("vrm") / pl.col("vrh"))
            .otherwise(None)
        )
    )


def _val(df: pl.DataFrame, mode: str, year: int, col: str) -> float | None:
    rows = df.filter((pl.col("mode") == mode) & (pl.col("year") == year))
    return rows.row(0, named=True)[col] if len(rows) else None


def build_summary(mode_df: pl.DataFrame) -> pl.DataFrame:
    rows = []
    for mode in SPEED_MODES:
        mph07 = _val(mode_df, mode, 2007, "mph")
        mph19 = _val(mode_df, mode, BASELINE_YEAR, "mph")
        mph24 = _val(mode_df, mode, COMPARE_YEAR, "mph")
        rows.append({
            "mode": MODE_NAMES[mode],
            "mph_2007": mph07,
            "mph_2019": mph19,
            "mph_2024": mph24,
            "pct_change_2019_2024": (mph24 - mph19) / mph19 * 100
            if mph19 and mph24 else None,
        })
    return pl.DataFrame(rows)


def chart_speed_trends(plt, mode_df: pl.DataFrame) -> None:
    """Operating speed (mph) by mode, 2002–2024."""
    fig, ax = plt.subplots(figsize=(12, 6))
    for mode in SPEED_MODES:
        sub = mode_df.filter(
            (pl.col("mode") == mode) & pl.col("mph").is_not_null()
        ).sort("year")
        ax.plot(
            sub["year"].to_list(),
            sub["mph"].to_list(),
            label=MODE_NAMES[mode],
            color=MODE_COLORS[mode],
            linewidth=2.5,
            marker="o",
            markersize=3,
        )

    ax.axvline(2020, color=COLOR_GRAY, linestyle="--", linewidth=1)
    ax.text(2020.3, ax.get_ylim()[1] * 0.95, "COVID-19", fontsize=9, color="#555555")
    ax.set_ylabel("Miles per Vehicle Revenue Hour (mph)")
    ax.set_xlabel("Year")
    ax.set_ylim(bottom=0)
    ax.set_title(
        "PRT Operating Speed by Mode, 2002–2024\n"
        "(Vehicle Revenue Miles ÷ Vehicle Revenue Hours)"
    )
    ax.legend()
    save_chart(fig, OUT / "speed_trends.png")


def chart_vrh_vrm_index(plt, mode_df: pl.DataFrame) -> None:
    """Indexed VRH and VRM by mode (2019 = 100)."""
    fig, axes = plt.subplots(1, len(SPEED_MODES), figsize=(15, 5), sharey=True)
    fig.suptitle(
        "PRT Service Volume by Mode — VRH and VRM Indexed to 2019", fontsize=13
    )

    for ax, mode in zip(axes, SPEED_MODES):
        sub = mode_df.filter(
            (pl.col("mode") == mode)
            & pl.col("vrh").is_not_null()
            & pl.col("vrm").is_not_null()
        ).sort("year")

        base_vrh = _val(sub, mode, BASELINE_YEAR, "vrh")
        base_vrm = _val(sub, mode, BASELINE_YEAR, "vrm")
        if not base_vrh or not base_vrm:
            continue

        years = sub["year"].to_list()
        vrh_idx = [v / base_vrh * 100 for v in sub["vrh"].to_list()]
        vrm_idx = [v / base_vrm * 100 for v in sub["vrm"].to_list()]

        ax.plot(years, vrh_idx, label="VRH", color="#2563eb", linewidth=2)
        ax.plot(
            years, vrm_idx, label="VRM", color="#dc2626", linewidth=2, linestyle="--"
        )
        ax.axhline(100, color=COLOR_GRAY, linewidth=0.8, linestyle=":")
        ax.axvline(2020, color=COLOR_GRAY, linestyle="--", linewidth=0.8)
        ax.set_title(MODE_NAMES[mode])
        ax.set_xlabel("Year")
        if ax == axes[0]:
            ax.set_ylabel("Index (2019 = 100)")
        ax.legend(fontsize=8)

    save_chart(fig, OUT / "vrh_vrm_index.png")


@run_analysis(52, "VRH and Vehicle Revenue Miles")
def main():
    plt = setup_plotting()

    with phase("Loading VRH and VRM data"):
        mode_df = load_mode_year()
        print(
            f"   {len(mode_df)} mode-years; range "
            f"{mode_df['year'].min()}–{mode_df['year'].max()}"
        )

    with phase("Operating speed by mode"):
        for mode in SPEED_MODES:
            mph19 = _val(mode_df, mode, BASELINE_YEAR, "mph")
            mph24 = _val(mode_df, mode, COMPARE_YEAR, "mph")
            delta = (
                (mph24 - mph19) / mph19 * 100
                if mph19 and mph24
                else float("nan")
            )
            print(
                f"   {MODE_NAMES[mode]:<12s} "
                f"2019: {mph19:5.2f} mph  "
                f"2024: {mph24:5.2f} mph  ({delta:+.1f}%)"
            )

    with phase("Building summary"):
        summary_df = build_summary(mode_df)

    with phase("Saving data"):
        save_csv(
            mode_df.with_columns(mode_name=pl.col("mode").replace(MODE_NAMES)),
            OUT / "speed_by_mode.csv",
        )
        save_csv(summary_df, OUT / "mode_speed_summary.csv")

    with phase("Generating charts"):
        chart_speed_trends(plt, mode_df)
        chart_vrh_vrm_index(plt, mode_df)


if __name__ == "__main__":
    main()
