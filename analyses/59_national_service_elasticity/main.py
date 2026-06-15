"""Analysis 59: estimate the agency-level service elasticity of ridership across the full NTD panel (1991-2024)."""

import numpy as np
import polars as pl
import statsmodels.api as sm

from prt_otp_analysis.common import (
    COLOR_GRAY,
    COLOR_NEGATIVE,
    COLOR_PRIMARY,
    analysis_dir,
    correlate,
    get_db,
    phase,
    run_analysis,
    save_chart,
    save_csv,
    setup_plotting,
    validate,
)
from prt_otp_analysis.common.schemas import NTD_ANNUAL_SERVICE

OUT = analysis_dir(__file__)

PRT_NTD_ID = 30022
MIN_BASE_VRH = 100_000        # exclude tiny agencies whose % swings dominate
SENSITIVITY_VRH = 250_000     # robustness threshold
VRH_TRIM_PCT = 50.0           # drop |vrh_pct| above this (reporting discontinuities)
UPT_TRIM_PCT = 75.0           # drop |upt_pct| above this
PANDEMIC_END_YEARS = (2020, 2021)


def load_changes(conn) -> pl.DataFrame:
    """Build the consecutive-year change panel: one row per agency-year transition.

    Returns columns: ntd_id, agency_name, year (end year), vrh_prev, vrh,
    upt_prev, upt, vrh_pct, upt_pct, base_vrh, pandemic.
    """
    rows = conn.execute("""
        SELECT ntd_id, agency_name, year, vrh, upt
        FROM ntd_annual_service
        WHERE vrh > 0 AND upt > 0
        ORDER BY ntd_id, year
    """).fetchall()
    df = pl.DataFrame([dict(r) for r in rows])
    validate(df, NTD_ANNUAL_SERVICE, subset=True)

    # Lag within agency; only keep strictly consecutive years (year - prev == 1).
    df = df.sort("ntd_id", "year").with_columns(
        vrh_prev=pl.col("vrh").shift(1).over("ntd_id"),
        upt_prev=pl.col("upt").shift(1).over("ntd_id"),
        year_prev=pl.col("year").shift(1).over("ntd_id"),
    )
    df = df.filter(
        pl.col("year_prev").is_not_null() & (pl.col("year") - pl.col("year_prev") == 1)
    )

    df = df.with_columns(
        base_vrh=pl.col("vrh_prev"),
        vrh_pct=(pl.col("vrh") - pl.col("vrh_prev")) / pl.col("vrh_prev") * 100,
        upt_pct=(pl.col("upt") - pl.col("upt_prev")) / pl.col("upt_prev") * 100,
        pandemic=pl.col("year").is_in(PANDEMIC_END_YEARS),
    )
    return df


def fit_elasticity(change_df: pl.DataFrame) -> dict[str, float]:
    """OLS of upt_pct ~ vrh_pct. Returns slope (elasticity), intercept, CI, R², n."""
    x = change_df["vrh_pct"].to_numpy()
    y = change_df["upt_pct"].to_numpy()
    n = len(x)
    if n < 3:
        nan = float("nan")
        return {"slope": nan, "intercept": nan, "ci_lo": nan, "ci_hi": nan, "r2": nan, "n": n}
    model = sm.OLS(y, sm.add_constant(x)).fit()
    ci = model.conf_int(alpha=0.05)
    return {
        "slope": float(model.params[1]),
        "intercept": float(model.params[0]),
        "ci_lo": float(ci[1][0]),
        "ci_hi": float(ci[1][1]),
        "r2": float(model.rsquared),
        "n": n,
    }


@run_analysis(59, "National Service Elasticity of Ridership")
def main():
    plt = setup_plotting()
    conn = get_db()

    with phase("Building year-over-year change panel"):
        raw_df = load_changes(conn)
        conn.close()
        print(f"   {len(raw_df):,} consecutive-year transitions (VRH & UPT > 0, all agencies)")

        sized_df = raw_df.filter(pl.col("base_vrh") >= MIN_BASE_VRH)
        print(f"   {len(sized_df):,} transitions from agencies with base VRH >= {MIN_BASE_VRH:,}")

        # Trim reporting discontinuities.
        trimmed_df = sized_df.filter(
            (pl.col("vrh_pct").abs() <= VRH_TRIM_PCT) & (pl.col("upt_pct").abs() <= UPT_TRIM_PCT)
        )
        dropped = len(sized_df) - len(trimmed_df)
        print(f"   Dropped {dropped} transitions exceeding trim bounds "
              f"(|VRH|>{VRH_TRIM_PCT:.0f}% or |UPT|>{UPT_TRIM_PCT:.0f}%)")

        analytic_df = trimmed_df.filter(~pl.col("pandemic"))
        pandemic_df = trimmed_df.filter(pl.col("pandemic"))
        cuts_df = analytic_df.filter(pl.col("vrh_pct") < 0)
        print(f"   Analytic (non-pandemic) sample: {len(analytic_df):,} transitions "
              f"({analytic_df['ntd_id'].n_unique()} agencies, "
              f"{analytic_df['year'].min()}-{analytic_df['year'].max()})")
        print(f"   Of those, {len(cuts_df):,} are service cuts (VRH change < 0)")

    # ---- Headline elasticity fits ----
    with phase("Estimating elasticity"):
        all_fit = fit_elasticity(analytic_df)
        cuts_fit = fit_elasticity(cuts_df)
        sens_fit = fit_elasticity(
            trimmed_df.filter((pl.col("base_vrh") >= SENSITIVITY_VRH) & ~pl.col("pandemic"))
        )
        pandemic_fit = fit_elasticity(pandemic_df)
        corr = correlate(analytic_df, "vrh_pct", "upt_pct")

        print(f"\n   All non-pandemic transitions  : elasticity = {all_fit['slope']:.3f} "
              f"[{all_fit['ci_lo']:.3f}, {all_fit['ci_hi']:.3f}]  "
              f"R²={all_fit['r2']:.3f}  n={all_fit['n']:,}")
        print(f"   Service cuts only             : elasticity = {cuts_fit['slope']:.3f} "
              f"[{cuts_fit['ci_lo']:.3f}, {cuts_fit['ci_hi']:.3f}]  "
              f"R²={cuts_fit['r2']:.3f}  n={cuts_fit['n']:,}")
        print(f"   Sensitivity (base VRH>={SENSITIVITY_VRH:,}) : elasticity = {sens_fit['slope']:.3f} "
              f"[{sens_fit['ci_lo']:.3f}, {sens_fit['ci_hi']:.3f}]  n={sens_fit['n']:,}")
        print(f"   Pandemic transitions (2020-21): elasticity = {pandemic_fit['slope']:.3f} "
              f"[{pandemic_fit['ci_lo']:.3f}, {pandemic_fit['ci_hi']:.3f}]  n={pandemic_fit['n']:,}")
        print(f"   Pearson r (non-pandemic): {corr['pearson_r']:.3f} (p={corr['pearson_p']:.1e})")

        summary_df = pl.DataFrame([
            {"sample": "all_non_pandemic", **all_fit},
            {"sample": "cuts_only", **cuts_fit},
            {"sample": f"sensitivity_vrh_{SENSITIVITY_VRH}", **sens_fit},
            {"sample": "pandemic_2020_2021", **pandemic_fit},
        ])

    # ---- Per-year elasticity ----
    with phase("Fitting per-year elasticity"):
        year_rows = []
        for yr in sorted(trimmed_df["year"].unique().to_list()):
            yr_df = trimmed_df.filter(pl.col("year") == yr)
            fit = fit_elasticity(yr_df)
            year_rows.append({"year": yr, "pandemic": yr in PANDEMIC_END_YEARS, **fit})
        year_df = pl.DataFrame(year_rows)

    # ---- Save CSVs ----
    print()
    save_csv(
        analytic_df.select(
            "ntd_id", "agency_name", "year", "vrh_prev", "vrh", "upt_prev", "upt",
            "vrh_pct", "upt_pct", "base_vrh",
        ).sort("year", "ntd_id"),
        OUT / "agency_year_changes.csv",
    )
    save_csv(year_df, OUT / "elasticity_by_year.csv")
    save_csv(summary_df, OUT / "summary.csv")

    # ---- Chart 1: scatter with elasticity line ----
    with phase("Generating service-vs-ridership scatter"):
        x = analytic_df["vrh_pct"].to_numpy()
        y = analytic_df["upt_pct"].to_numpy()

        fig, ax = plt.subplots(figsize=(11, 9))
        ax.axvspan(-VRH_TRIM_PCT, 0, color=COLOR_NEGATIVE, alpha=0.05, zorder=0)
        ax.text(-VRH_TRIM_PCT + 1, UPT_TRIM_PCT - 4, "service cut →", color=COLOR_NEGATIVE,
                fontsize=9, alpha=0.8, va="top")

        ax.scatter(x, y, s=14, alpha=0.30, color=COLOR_PRIMARY, edgecolors="none", zorder=2)

        line_x = np.array([-VRH_TRIM_PCT, VRH_TRIM_PCT])
        ax.plot(line_x, all_fit["intercept"] + all_fit["slope"] * line_x,
                color=COLOR_NEGATIVE, linewidth=2.5, zorder=4,
                label=f"Elasticity = {all_fit['slope']:.2f}  (R²={all_fit['r2']:.2f}, n={all_fit['n']:,})")
        ax.plot(line_x, line_x, color=COLOR_GRAY, linestyle="--", linewidth=1, zorder=3,
                label="1:1 (ridership tracks service exactly)")

        ax.axhline(0, color="#CCCCCC", linewidth=0.8, zorder=1)
        ax.axvline(0, color="#CCCCCC", linewidth=0.8, zorder=1)
        ax.set_xlim(-VRH_TRIM_PCT, VRH_TRIM_PCT)
        ax.set_ylim(-UPT_TRIM_PCT, UPT_TRIM_PCT)
        ax.set_xlabel("Service change, year over year — Vehicle Revenue Hours (%)")
        ax.set_ylabel("Ridership change, year over year — Unlinked Passenger Trips (%)")
        ax.set_title("When agencies change service, how does ridership move?\n"
                     f"US transit agencies, base VRH ≥ {MIN_BASE_VRH:,}, 1991–2024, pandemic years excluded")
        ax.legend(loc="lower right", fontsize=9)
        save_chart(fig, OUT / "service_vs_ridership_scatter.png")

    # ---- Chart 2: dose-response bins ----
    with phase("Generating dose-response bins"):
        bins = [
            ("Deep cut\n(≤ −10%)", pl.col("vrh_pct") <= -10),
            ("Cut\n(−10 to −5%)", (pl.col("vrh_pct") > -10) & (pl.col("vrh_pct") <= -5)),
            ("Mild cut\n(−5 to 0%)", (pl.col("vrh_pct") > -5) & (pl.col("vrh_pct") < 0)),
            ("Flat / small grow\n(0 to +5%)", (pl.col("vrh_pct") >= 0) & (pl.col("vrh_pct") <= 5)),
            ("Growth\n(> +5%)", pl.col("vrh_pct") > 5),
        ]
        labels, medians, q1s, q3s, ns = [], [], [], [], []
        for label, cond in bins:
            sub = analytic_df.filter(cond)["upt_pct"]
            if len(sub) == 0:
                continue
            labels.append(label)
            medians.append(sub.median())
            q1s.append(sub.quantile(0.25))
            q3s.append(sub.quantile(0.75))
            ns.append(len(sub))

        fig, ax = plt.subplots(figsize=(11, 7))
        xpos = range(len(labels))
        lower = [m - q for m, q in zip(medians, q1s)]
        upper = [q - m for q, m in zip(q3s, medians)]
        colors = [COLOR_NEGATIVE if m < 0 else COLOR_PRIMARY for m in medians]
        ax.bar(xpos, medians, color=colors, alpha=0.85,
               yerr=[lower, upper], capsize=6, error_kw={"alpha": 0.5, "lw": 1.2})
        ax.axhline(0, color="#999999", linewidth=0.9)
        for i, (m, n) in enumerate(zip(medians, ns)):
            ax.text(i, m + (1 if m >= 0 else -1), f"{m:+.1f}%\n(n={n})",
                    ha="center", va="bottom" if m >= 0 else "top", fontsize=8)
        ax.set_xticks(list(xpos))
        ax.set_xticklabels(labels, fontsize=9)
        ax.set_ylabel("Ridership change — median (bars), IQR (whiskers) (%)")
        ax.set_title("Ridership change by size of service change\n"
                     "US transit agencies, 1991–2024, pandemic years excluded")
        save_chart(fig, OUT / "dose_response_bins.png")

    # ---- Chart 3: elasticity over time ----
    with phase("Generating elasticity-over-time chart"):
        plot_df = year_df.filter(pl.col("n") >= 10).sort("year")
        yrs = plot_df["year"].to_list()
        slopes = plot_df["slope"].to_list()
        lo = plot_df["ci_lo"].to_list()
        hi = plot_df["ci_hi"].to_list()
        is_pan = plot_df["pandemic"].to_list()

        fig, ax = plt.subplots(figsize=(13, 6.5))
        ax.fill_between(yrs, lo, hi, color=COLOR_PRIMARY, alpha=0.15, zorder=1)
        ax.plot(yrs, slopes, color=COLOR_PRIMARY, linewidth=1.8, marker="o", markersize=4, zorder=2)
        for yr, s, pan in zip(yrs, slopes, is_pan):
            if pan:
                ax.scatter([yr], [s], color=COLOR_NEGATIVE, s=70, zorder=3, edgecolors="white")
        ax.axhline(all_fit["slope"], color=COLOR_GRAY, linestyle="--", linewidth=1.2,
                   label=f"Pooled non-pandemic elasticity = {all_fit['slope']:.2f}")
        ax.axhline(0, color="#CCCCCC", linewidth=0.8)
        ax.scatter([], [], color=COLOR_NEGATIVE, s=70, edgecolors="white",
                   label="Pandemic year (2020, 2021)")
        ax.set_xlabel("Year")
        ax.set_ylabel("Fitted elasticity (Δ%UPT per 1% Δ%VRH)")
        ax.set_title("Service elasticity of ridership over time\n"
                     "Slope of yearly Δridership-vs-Δservice fit, sizeable US agencies")
        ax.legend(loc="upper left", fontsize=9)
        save_chart(fig, OUT / "elasticity_over_time.png")

    # ---- Chart 4: PRT overlay ----
    with phase("Generating PRT cut-episodes chart"):
        prt_df = trimmed_df.filter(pl.col("ntd_id") == PRT_NTD_ID).sort("year")
        fig, ax = plt.subplots(figsize=(11, 9))

        bg = analytic_df
        ax.scatter(bg["vrh_pct"].to_numpy(), bg["upt_pct"].to_numpy(),
                   s=10, alpha=0.12, color=COLOR_GRAY, edgecolors="none", zorder=1)
        line_x = np.array([-30, 30])
        ax.plot(line_x, all_fit["intercept"] + all_fit["slope"] * line_x,
                color="#888888", linewidth=1.8, linestyle="--", zorder=2,
                label=f"National elasticity = {all_fit['slope']:.2f}")

        for row in prt_df.iter_rows(named=True):
            is_cut = row["vrh_pct"] < 0
            is_pan = row["pandemic"]
            color = COLOR_NEGATIVE if is_pan else (COLOR_PRIMARY if is_cut else "#6ACC65")
            ax.scatter(row["vrh_pct"], row["upt_pct"], s=90, color=color,
                       edgecolors="black", linewidths=0.8, zorder=4)
            ax.annotate(str(row["year"]), (row["vrh_pct"], row["upt_pct"]),
                        textcoords="offset points", xytext=(6, 5), fontsize=8)

        ax.scatter([], [], s=90, color=COLOR_PRIMARY, edgecolors="black", label="PRT service-cut year")
        ax.scatter([], [], s=90, color="#6ACC65", edgecolors="black", label="PRT service-growth year")
        ax.scatter([], [], s=90, color=COLOR_NEGATIVE, edgecolors="black", label="PRT pandemic year")
        ax.axhline(0, color="#CCCCCC", linewidth=0.8)
        ax.axvline(0, color="#CCCCCC", linewidth=0.8)
        ax.set_xlim(-30, 30)
        ax.set_ylim(-60, 30)
        ax.set_xlabel("PRT service change, year over year — VRH (%)")
        ax.set_ylabel("PRT ridership change, year over year — UPT (%)")
        ax.set_title("Pittsburgh (PRT) service vs ridership changes against the national pattern")
        ax.legend(loc="lower right", fontsize=9)
        save_chart(fig, OUT / "prt_cut_episodes.png")

    # ---- Console: PRT episode detail ----
    print("\n   PRT consecutive-year changes:")
    for row in prt_df.iter_rows(named=True):
        tag = " [pandemic]" if row["pandemic"] else (" [cut]" if row["vrh_pct"] < 0 else "")
        print(f"     {row['year']}: VRH {row['vrh_pct']:>+6.1f}%   UPT {row['upt_pct']:>+6.1f}%{tag}")


if __name__ == "__main__":
    main()
