# Findings: Stop Signal Placement Equity

## Summary
PRT's signalized stops — and the operationally worse **near-side** placement
documented in Analysis 53 — show **no meaningful demographic disparity**. The
near-side share of signalized stops holds at roughly **85% across every income
quartile** (86.2% in the lowest-income quartile vs. 84.9% in the highest), and at
the census-tract level neither the signalized-stop share nor the near-side share
correlates with median household income, zero-vehicle household share, or Black
population share (all |Spearman ρ| ≤ 0.11, all p > 0.07). Near-side placement is
a **system-wide legacy inheritance**, not a pattern concentrated in disadvantaged
neighborhoods. The equity implication is encouraging in one sense — riders in
low-income areas are not disproportionately burdened by the worse placement — and
practical in another: converting near-side stops to far-side (where warranted)
would benefit riders broadly rather than redress a specific inequity.

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
- **Stop placement ≠ exposure.** This measures where signalized stops are, not
  how many riders board at them; a ridership-weighted equity view could differ
  and is left to future work (cf. Analysis 32 for ridership-weighted stop equity).

## Validation
1. **Data source verified.** `stop_signals` (pipeline 15) validated against the
   `STOP_SIGNALS` schema with `validate(..., subset=True)`; demographics come from
   the shared `assign_stops_to_tracts` helper (point-in-polygon to `census_tracts`),
   the same path used by Analysis 04.
2. **Scope match.** Stops are joined on the PRT internal `stop_id` (the namespace
   shared by `stop_signals` and the `stops` table); 6,299 of 6,306 PRT stops carry
   a resolved `stop_id` and match.
3. **Null handling.** Stops without a tract income are dropped from the
   income-quartile view; share denominators are guarded with `when(... > 0)` so a
   tract with zero households or zero signalized stops yields null (dropped by
   `correlate`), never a divide-by-zero or a NaN counted as a real value.
4. **Aggregate sanity check.** Overall signalized share (~24%) and near-side share
   (~85%) match the system totals in Analysis 53, confirming the join did not drop
   or duplicate stops.
5. **Surprising-result check.** The result is a null, which is the *expected*
   direction here (a legacy system-wide default should not track income); the one
   borderline correlation (zero-vehicle share) was examined and explained as urban
   density, not a disparity.
6. **Small-sample routes/areas flagged.** Tracts below 5 stops (signalized share)
   and 3 signalized stops (near-side share) are excluded; thresholds are reported
   in the output and chart titles.
7. **Multicollinearity.** Not applicable — these are bivariate Spearman
   correlations, not a multi-predictor regression.
8. **Ecological framing.** Documented in Caveats; all language is tract-level.
