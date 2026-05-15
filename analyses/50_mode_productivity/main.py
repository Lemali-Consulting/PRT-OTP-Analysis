"""Analysis 50: splits PRT's agency-wide service productivity (passengers per
vehicle revenue hour) into its four modes — motor bus, light rail, paratransit,
and the incline — to see which service the low agency average is hiding."""

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
# VRH for paratransit and the incline is first reported in 2007; before that the
# all-mode roll-up would understate revenue hours and overstate productivity.
ALL_MODE_START = 2007

# NTD mode codes -> readable names. PRT runs exactly these four.
MODE_NAMES = {
    "MB": "Motor Bus",
    "LR": "Light Rail",
    "DR": "Paratransit",
    "IP": "Incline",
}
MODE_ORDER = ["MB", "LR", "DR", "IP"]
MODE_COLORS = {
    "MB": "#3b82f6",  # blue   — bus
    "LR": "#22c55e",  # green  — rail
    "DR": "#f59e0b",  # amber  — paratransit
    "IP": "#a855f7",  # purple — incline
}
FIXED_ROUTE_MODES = ["MB", "LR"]
ROLLUP_NAMES = {
    "FIXED_ROUTE": "Fixed route (bus + rail)",
    "ALL_MODE": "All modes (agency-wide)",
}


def load_mode_year() -> pl.DataFrame:
    """Load PRT monthly UPT/VRH by mode and aggregate to calendar years.

    Productivity (UPT / VRH) is computed only where VRH > 0; mode-years with no
    reported revenue hours are left null rather than counted as zero service.
    """
    raw_df = query_to_polars(
        "SELECT mode, month, upt, vrh FROM ntd_ridership WHERE ntd_id = ?",
        (PRT_NTD_ID,),
    )
    validate(raw_df, NTD_RIDERSHIP, subset=True)

    year_df = (
        raw_df.with_columns(year=pl.col("month").str.slice(0, 4).cast(pl.Int64))
        .filter(pl.col("year").is_between(START_YEAR, COMPARE_YEAR))
        .group_by("mode", "year")
        .agg(upt=pl.col("upt").sum(), vrh=pl.col("vrh").sum())
        .sort("mode", "year")
    )
    return year_df.with_columns(
        productivity=pl.when(pl.col("vrh") > 0)
        .then(pl.col("upt") / pl.col("vrh"))
        .otherwise(None)
    )


def rollup(mode_df: pl.DataFrame, modes: list[str], label: str) -> pl.DataFrame:
    """Sum UPT and VRH across a set of modes into one labelled productivity series."""
    sub = mode_df.filter(pl.col("mode").is_in(modes))
    agg = (
        sub.group_by("year")
        .agg(upt=pl.col("upt").sum(), vrh=pl.col("vrh").sum())
        .sort("year")
    )
    return agg.with_columns(
        mode=pl.lit(label),
        productivity=pl.when(pl.col("vrh") > 0)
        .then(pl.col("upt") / pl.col("vrh"))
        .otherwise(None),
    ).select("mode", "year", "upt", "vrh", "productivity")


def _val(df: pl.DataFrame, mode: str, year: int, col: str) -> float | None:
    """Return one cell from a long mode/year frame, or None if absent."""
    rows = df.filter((pl.col("mode") == mode) & (pl.col("year") == year))
    return rows.row(0, named=True)[col] if len(rows) else None


def build_summary(mode_df: pl.DataFrame, rollup_df: pl.DataFrame) -> pl.DataFrame:
    """One row per mode (and roll-up): productivity at key years and 2024 shares."""
    compare_df = mode_df.filter(pl.col("year") == COMPARE_YEAR)
    total_upt = compare_df["upt"].sum()
    total_vrh = compare_df["vrh"].sum()

    rows = []
    for mode in MODE_ORDER + ["FIXED_ROUTE", "ALL_MODE"]:
        src = rollup_df if mode in ROLLUP_NAMES else mode_df
        p07 = _val(src, mode, ALL_MODE_START, "productivity")
        p19 = _val(src, mode, BASELINE_YEAR, "productivity")
        p24 = _val(src, mode, COMPARE_YEAR, "productivity")
        upt24 = _val(src, mode, COMPARE_YEAR, "upt")
        vrh24 = _val(src, mode, COMPARE_YEAR, "vrh")
        rows.append({
            "mode": ROLLUP_NAMES.get(mode, MODE_NAMES.get(mode, mode)),
            "prod_2007": p07,
            "prod_2019": p19,
            "prod_2024": p24,
            "pct_change_2019_2024": (p24 - p19) / p19 * 100 if p19 and p24 else None,
            "upt_share_2024": upt24 / total_upt * 100 if upt24 else None,
            "vrh_share_2024": vrh24 / total_vrh * 100 if vrh24 else None,
        })
    return pl.DataFrame(rows)


def chart_trends(plt, mode_df: pl.DataFrame) -> None:
    """Productivity by mode, 2002-2024 — one line per mode."""
    fig, ax = plt.subplots(figsize=(12, 6))
    for mode in MODE_ORDER:
        sub = mode_df.filter(
            (pl.col("mode") == mode) & pl.col("productivity").is_not_null()
        ).sort("year")
        ax.plot(sub["year"].to_list(), sub["productivity"].to_list(),
                label=MODE_NAMES[mode], color=MODE_COLORS[mode],
                linewidth=2.5, marker="o", markersize=3)

    ax.axvline(2020, color=COLOR_GRAY, linestyle="--", linewidth=1)
    ax.text(2020.3, ax.get_ylim()[1] * 0.95, "COVID-19", fontsize=9, color="#555555")
    ax.set_ylabel("Passengers per Vehicle Revenue Hour")
    ax.set_xlabel("Year")
    ax.set_ylim(bottom=0)
    ax.set_title("PRT Service Productivity by Mode, 2002–2024")
    ax.legend()
    save_chart(fig, OUT / "mode_productivity_trends.png")


def chart_2024(plt, mode_df: pl.DataFrame, rollup_df: pl.DataFrame) -> None:
    """Bar ranking of 2024 productivity by mode, with roll-up reference lines."""
    fig, ax = plt.subplots(figsize=(10, 6))
    snap = mode_df.filter(pl.col("year") == COMPARE_YEAR).sort("productivity")
    labels = [MODE_NAMES[m] for m in snap["mode"].to_list()]
    vals = snap["productivity"].to_list()
    colors = [MODE_COLORS[m] for m in snap["mode"].to_list()]

    ax.barh(labels, vals, color=colors, edgecolor="white")
    for i, v in enumerate(vals):
        ax.text(v + 0.4, i, f"{v:.1f}", va="center", fontsize=10, fontweight="bold")

    fixed = _val(rollup_df, "FIXED_ROUTE", COMPARE_YEAR, "productivity")
    allm = _val(rollup_df, "ALL_MODE", COMPARE_YEAR, "productivity")
    ax.axvline(fixed, color="#1f2937", linestyle="--", linewidth=1.4)
    ax.text(fixed + 0.4, -0.55, f"Fixed route (bus + rail): {fixed:.1f}",
            fontsize=8.5, color="#1f2937")
    ax.axvline(allm, color=COLOR_GRAY, linestyle=":", linewidth=1.4)
    ax.text(allm + 0.4, -0.85, f"All modes: {allm:.1f}", fontsize=8.5, color="#555555")

    ax.set_xlabel("Passengers per Vehicle Revenue Hour")
    ax.set_title("PRT Service Productivity by Mode, 2024")
    ax.set_ylim(-1.1, len(labels) - 0.4)
    save_chart(fig, OUT / "mode_productivity_2024.png")


def chart_service_vs_ridership(plt, summary_df: pl.DataFrame) -> None:
    """Each mode's 2024 share of trips vs its share of revenue hours."""
    fig, ax = plt.subplots(figsize=(10, 6))
    modes = [MODE_NAMES[m] for m in MODE_ORDER]
    sub = summary_df.filter(pl.col("mode").is_in(modes))
    upt_share = sub["upt_share_2024"].to_list()
    vrh_share = sub["vrh_share_2024"].to_list()

    y = list(range(len(modes)))
    h = 0.38
    ax.barh([i + h / 2 for i in y], upt_share, height=h,
            color="#2563eb", label="Share of trips (UPT)")
    ax.barh([i - h / 2 for i in y], vrh_share, height=h,
            color="#f59e0b", label="Share of service hours (VRH)")
    for i in y:
        ax.text(upt_share[i] + 0.8, i + h / 2, f"{upt_share[i]:.1f}%",
                va="center", fontsize=8.5)
        ax.text(vrh_share[i] + 0.8, i - h / 2, f"{vrh_share[i]:.1f}%",
                va="center", fontsize=8.5)

    ax.set_yticks(y)
    ax.set_yticklabels(modes)
    ax.set_xlabel("Share of PRT total, 2024 (%)")
    ax.set_title("Who Carries the Riders vs. Who Uses the Service Hours, 2024")
    ax.legend()
    save_chart(fig, OUT / "service_vs_ridership_2024.png")


def chart_decline(plt, mode_df: pl.DataFrame) -> None:
    """Productivity by mode in 2019 vs 2024."""
    fig, ax = plt.subplots(figsize=(10, 6))
    p19 = [_val(mode_df, m, BASELINE_YEAR, "productivity") for m in MODE_ORDER]
    p24 = [_val(mode_df, m, COMPARE_YEAR, "productivity") for m in MODE_ORDER]

    x = list(range(len(MODE_ORDER)))
    w = 0.38
    ax.bar([i - w / 2 for i in x], p19, width=w, color=COLOR_GRAY, label="2019")
    ax.bar([i + w / 2 for i in x], p24, width=w,
           color=[MODE_COLORS[m] for m in MODE_ORDER], label="2024")
    for i in x:
        pct = (p24[i] - p19[i]) / p19[i] * 100
        ax.text(i, max(p19[i], p24[i]) + 1.5, f"{pct:+.0f}%", ha="center",
                fontsize=9, fontweight="bold", color="#b91c1c")

    ax.set_xticks(x)
    ax.set_xticklabels([MODE_NAMES[m] for m in MODE_ORDER])
    ax.set_ylabel("Passengers per Vehicle Revenue Hour")
    ax.set_title("Productivity Fell at Every Mode — 2019 vs. 2024")
    ax.legend()
    save_chart(fig, OUT / "productivity_decline_2019_2024.png")


@run_analysis(50, "Bus vs. Rail — Productivity by Mode")
def main():
    plt = setup_plotting()

    with phase("Loading per-mode UPT and VRH"):
        mode_df = load_mode_year()
        rollup_df = pl.concat([
            rollup(mode_df, FIXED_ROUTE_MODES, "FIXED_ROUTE"),
            rollup(mode_df, MODE_ORDER, "ALL_MODE"),
        ])
        print(f"   {len(mode_df)} mode-years across {mode_df['mode'].n_unique()} modes")
        print(f"   record: {mode_df['year'].min()}–{mode_df['year'].max()}")

    with phase("2024 productivity by mode"):
        for mode in MODE_ORDER:
            p = _val(mode_df, mode, COMPARE_YEAR, "productivity")
            print(f"   {MODE_NAMES[mode]:<12s} {p:6.1f} pax/VRH")
        fixed = _val(rollup_df, "FIXED_ROUTE", COMPARE_YEAR, "productivity")
        allm = _val(rollup_df, "ALL_MODE", COMPARE_YEAR, "productivity")
        print(f"   {'Fixed route':<12s} {fixed:6.1f} pax/VRH  (bus + rail only)")
        print(f"   {'All modes':<12s} {allm:6.1f} pax/VRH  (cf. Analysis 48: 18.3)")

    with phase("Building per-mode summary"):
        summary_df = build_summary(mode_df, rollup_df)
        print(f"   {'Mode':<26s} {'2007':>7s} {'2019':>7s} {'2024':>7s} {'19→24':>8s}")
        for r in summary_df.iter_rows(named=True):
            def fmt(v: float | None) -> str:
                return f"{v:7.1f}" if v is not None else f"{'—':>7s}"
            pct = (f"{r['pct_change_2019_2024']:+6.0f}%"
                   if r["pct_change_2019_2024"] is not None else f"{'—':>8s}")
            print(f"   {r['mode']:<26s} {fmt(r['prod_2007'])} {fmt(r['prod_2019'])} "
                  f"{fmt(r['prod_2024'])} {pct}")

    with phase("Saving data"):
        save_csv(
            mode_df.with_columns(mode_name=pl.col("mode").replace(MODE_NAMES))
            .select("year", "mode", "mode_name", "upt", "vrh", "productivity"),
            OUT / "mode_productivity_by_year.csv",
        )
        save_csv(summary_df, OUT / "mode_summary.csv")

    with phase("Generating charts"):
        chart_trends(plt, mode_df)
        chart_2024(plt, mode_df, rollup_df)
        chart_service_vs_ridership(plt, summary_df)
        chart_decline(plt, mode_df)


if __name__ == "__main__":
    main()
