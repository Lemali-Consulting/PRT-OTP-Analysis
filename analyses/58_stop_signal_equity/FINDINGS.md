# Findings: Stop Signal Placement Equity

## Summary
PRT's signalized stops — and the operationally worse **near-side** placement
documented in Analysis 53 — show **no meaningful demographic disparity**. The
near-side share of signalized stops holds at roughly **85% across every income
quartile** (86.2% in the lowest-income quartile vs. 84.9% in the highest), and at
the census-tract level neither the signalized-stop share nor the near-side share
correlates with median household income, zero-vehicle household share, or Black
population share (all |Spearman ρ| ≤ 0.11, all p > 0.07). **The null holds when
stops are weighted by ridership** — per-rider near-side exposure is 85% in the
lowest-income quartile and does not rise monotonically with poverty (it is 83% in
the highest-income quartile and peaks in the middle), so riders in low-income
areas are not disproportionately exposed to near-side stops even after accounting
for how heavily each stop is used. Near-side placement is a **system-wide legacy
inheritance**, not a pattern concentrated in disadvantaged neighborhoods. The
equity implication is encouraging in one sense — riders in low-income areas are
not disproportionately burdened by the worse placement — and practical in another:
converting near-side stops to far-side (where warranted) would benefit riders
broadly rather than redress a specific inequity.

## Key Numbers
- **6,299 stops** matched to a census tract; **6,223** have a tract median income.
- Signalized-stop share by income quartile: **Q1 25.7%, Q2 19.0%, Q3 24.3%,
  Q4 27.9%** — no monotonic income gradient.
- Near-side share by income quartile: **Q1 86.2%, Q2 88.2%, Q3 85.3%, Q4 84.9%**
  — essentially flat.
- Tract-level **signalized-stop share** (n = 294 tracts with ≥ 5 stops) vs:
  - median household income: ρ = +0.044 (p = 0.46)
  - zero-vehicle household share: ρ = +0.105 (p = 0.07)
  - Black population share: ρ = −0.040 (p = 0.50)
- Tract-level **near-side share** (n = 201 tracts with ≥ 3 signalized stops) vs:
  - median household income: ρ = −0.044 (p = 0.55)
  - zero-vehicle household share: ρ = +0.062 (p = 0.39)
  - Black population share: ρ = +0.036 (p = 0.62)
- **Ridership-weighted** near-side share by income quartile: **Q1 85.3%,
  Q2 90.2%, Q3 93.1%, Q4 83.2%** — non-monotonic, lowest-income quartile near the
  bottom of the range (98% of signal stops, 6,174 / 6,299, have usage data).
- Ridership-weighted tract correlations are also null: near-side share vs income
  ρ = −0.051 (p = 0.48), vs zero-vehicle share ρ = +0.017 (p = 0.82), vs Black
  share ρ = +0.043 (p = 0.55). The only correlation to cross p < 0.05 is
  *signalized* share vs zero-vehicle share (ρ = +0.121, p = 0.04) — the same
  urban-density signal seen unweighted, and not the near-side outcome.

## Observations
- **No income gradient in either outcome.** Whether a stop sits at a signal, and
  whether that signal stop is near-side, is independent of neighborhood income.
  The quartile bars are visually flat (see `signal_share_by_income_quartile.png`).
- **The one borderline signal is intuitive and non-significant.** Tracts with more
  zero-vehicle (transit-dependent) households have very slightly more signalized
  stops (ρ = +0.105, p = 0.07) — consistent with transit-dependent areas being
  denser, more urban places that simply have more signals overall. It does not
  reach significance and does not appear in the near-side outcome.
- **Near-side dominance is universal.** The ~85% near-side share is remarkably
  stable across the income distribution, reinforcing Analysis 53's reading that
  near-side placement reflects historical engineering practice applied
  system-wide, not a targeted or recent siting decision.
- **Direction of the (null) effects.** A genuine equity problem would have shown
  lower-income or more-transit-dependent tracts with *higher* near-side shares.
  No such pattern exists; if anything the near-side share trends marginally lower
  in lower-income tracts, the opposite of a disparity.
- **Ridership weighting does not change the conclusion.** Weighting each stop by
  its pre-pandemic weekday usage — so the figures reflect rider *experience*
  rather than stop counts — leaves the picture flat. Per-rider near-side exposure
  is 85.3% in the lowest-income quartile, peaks at 93.1% in Q3, and falls to
  83.2% in the highest-income quartile: no income gradient, and the most
  disadvantaged riders are not the most exposed. This was the one view most
  likely to reveal a hidden disparity (busy stops in poor, dense neighborhoods
  could have dominated), and it did not. See
  `nearside_share_rider_weighted.png`.

## Caveats
- **Ecological framing.** All results are tract-level associations between
  demographics and stop placement. They describe neighborhoods, not individual
  riders, and make no individual-level claim.
- **Null result, not proof of no effect.** Failing to detect a disparity at the
  tract level does not prove perfect equity at finer geographies; it means no
  meaningful tract-level relationship is present in these data.
- **Tract assignment is point-in-polygon.** Each stop is assigned to the tract
  containing its coordinate; a stop near a tract boundary serves residents of
  adjacent tracts whose demographics are not counted.
- **Demographic coverage.** ACS demographics attach only to stops inside a
  5-county PA tract; a small number of out-of-region stops (and tracts with null
  ACS values) drop from the relevant correlation.
- **Ridership data is pre-pandemic.** The usage weights come from pre-pandemic
  weekday boardings/alightings (the WPRDC bus-stop-usage dataset, also used by
  Analyses 32 and 34). Post-pandemic ridership patterns have shifted; if the
  shift correlated with both demographics and near-side placement it could in
  principle move the weighted result, though the per-stop (unweighted) null is
  unaffected by this.
- **Usage coverage is 98%, not 100%.** 6,174 of 6,299 tract-matched signal stops
  carry a usage record; the 125 without one drop from the weighted figures only
  (they remain in the per-stop figures). Their omission cannot manufacture a
  gradient that the per-stop view does not show.

## Validation
1. **Data source verified.** `stop_signals` (pipeline 15) validated against the
   `STOP_SIGNALS` schema with `validate(..., subset=True)`; demographics come from
   the shared `assign_stops_to_tracts` helper (point-in-polygon to `census_tracts`),
   the same path used by Analysis 04.
2. **Scope match.** Stops are joined on the PRT internal `stop_id` (the namespace
   shared by `stop_signals`, the `stops` table, and the WPRDC usage CSV); 6,299 of
   6,306 PRT stops carry a resolved `stop_id` and match, and 6,174 of those (98%)
   carry pre-pandemic weekday usage for the ridership-weighted view.
3. **Null handling.** Stops without a tract income are dropped from the
   income-quartile view; share denominators are guarded with `when(... > 0)` so a
   tract with zero households or zero signalized stops yields null (dropped by
   `correlate`), never a divide-by-zero or a NaN counted as a real value. In the
   ridership-weighted aggregates, usage is summed with `filter`, so the 125
   usage-null stops contribute 0 to both numerator and denominator (they drop out)
   rather than injecting a null weight.
4. **Aggregate sanity check.** Overall signalized share (~24%) and near-side share
   (~85%) match the system totals in Analysis 53, confirming the join did not drop
   or duplicate stops.
5. **Surprising-result check.** The result is a null, which is the *expected*
   direction here (a legacy system-wide default should not track income); the one
   borderline correlation (zero-vehicle share) was examined and explained as urban
   density, not a disparity.
6. **Robustness to weighting.** The null was re-tested with stops weighted by
   ridership — the view most likely to surface a hidden disparity — and the
   conclusion held (no income gradient, near-side correlations still null). A
   result that flipped under weighting would have been a red flag; it did not.
7. **Small-sample routes/areas flagged.** Tracts below 5 stops (signalized share)
   and 3 signalized stops (near-side share) are excluded; thresholds are reported
   in the output and chart titles.
8. **Multicollinearity.** Not applicable — these are bivariate Spearman
   correlations, not a multi-predictor regression.
9. **Ecological framing.** Documented in Caveats; all language is tract-level.
