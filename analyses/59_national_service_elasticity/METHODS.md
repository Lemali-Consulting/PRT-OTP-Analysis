# Methods: National Service Elasticity of Ridership

## Question

Nationally, across all US transit agencies and the full NTD history (1991–2024),
when an agency cuts (or expands) service, how much does its ridership move in the
same year? Put differently: what is the agency-level **service elasticity of
ridership** — the percent change in unlinked passenger trips (UPT) associated
with a 1% change in vehicle revenue hours (VRH) — and how stable is it over time?

This generalizes Analysis 39, which compared a single 2019→2024 snapshot. Here we
use *every* consecutive-year change across three decades and many cut episodes,
not just the COVID window.

## Approach

1. **Build a year-over-year change panel.** For each agency, take every pair of
   consecutive reporting years where VRH and UPT are both present and positive in
   both years. For each pair compute `vrh_pct = ΔVRH/VRH_prev × 100` and
   `upt_pct = ΔUPT/UPT_prev × 100`. One row per agency-year-transition.
2. **Restrict to sizeable agencies.** Keep transitions where the base-year VRH ≥
   100,000 hours (~the largest ~340 agencies in 2019). Tiny rural systems produce
   wild percent swings on small denominators that would dominate the regression.
   The threshold is reported and a sensitivity check at 250,000 is run.
3. **Flag and separate the pandemic.** Transitions ending in 2020 or 2021 are
   marked `pandemic`. The pandemic collapsed service and ridership jointly for
   exogenous public-health reasons, not as a service→ridership response, so these
   transitions are **excluded from the headline elasticity** and reported
   separately.
4. **Trim reporting discontinuities.** Drop transitions with |vrh_pct| > 50% or
   |upt_pct| > 75% as likely mergers, definition changes, or first-year reporting
   artifacts rather than genuine service decisions. The count dropped is reported.
5. **Estimate elasticity (OLS).** Regress `upt_pct ~ vrh_pct` on the non-pandemic,
   trimmed panel. The slope is the elasticity; report slope, 95% CI, R², n, and
   the Pearson correlation. Refit on the **cuts-only** subset (vrh_pct < 0), since
   the question is specifically about service reductions.
6. **Elasticity over time.** Fit the same slope separately within each year
   (1991–2024) to check whether the service–ridership relationship is stable,
   strengthening, or weakening; pandemic years are flagged on the chart.
7. **Dose–response bins.** Bucket transitions by service-change size (deep cut
   ≤ −10%, cut −10 to −5%, mild cut −5 to 0%, roughly flat 0 to +5%, growth > +5%)
   and show the distribution (median, IQR) of ridership change in each bucket.
8. **PRT overlay.** Plot PRT's own consecutive-year changes against the national
   regression line, highlighting its service-cut years.

**Framing.** This is an **agency-level association**, not an individual rider
behavior model and not a causal demand elasticity. Service and ridership are
jointly determined — agencies frequently cut service *because* ridership is
already falling (reverse causality), and both respond to shared shocks (fuel
prices, recessions, local economies). The slope describes how service and
ridership co-move across agencies and years; it is not a controlled estimate of
"cut service by 1% → lose X% of riders."

## Data

| Name | Description | Source |
|------|-------------|--------|
| `ntd_annual_service` | Annual system-level VRH, UPT per agency (1991–2024) | `prt.db` table (pipeline 06, NTD TS2.2 workbooks) |

Columns used: `ntd_id`, `agency_name`, `year`, `vrh`, `upt`. System-level
(all modes aggregated). Inclusion: VRH & UPT present and > 0 in both years of a
transition; base-year VRH ≥ 100,000.

## Output

- `output/service_vs_ridership_scatter.png` — Δ%VRH vs Δ%UPT for all non-pandemic
  sizeable transitions, with the fitted elasticity line, y=x reference, and the
  service-cut region shaded.
- `output/dose_response_bins.png` — distribution of ridership change within each
  service-change bucket (median, IQR, n per bin).
- `output/elasticity_over_time.png` — per-year fitted elasticity slope (1991–2024)
  with 95% CI band; pandemic years flagged.
- `output/prt_cut_episodes.png` — PRT's consecutive-year service vs ridership
  changes over its history, cut years highlighted, against the national line.
- `output/agency_year_changes.csv` — the per-transition change panel used.
- `output/elasticity_by_year.csv` — per-year slope, CI, n, R².
- `output/summary.csv` — headline elasticity estimates (all, cuts-only,
  sensitivity, pandemic-subset).
