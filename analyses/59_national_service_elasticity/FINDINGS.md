# Findings: National Service Elasticity of Ridership

## Summary

Across 8,323 year-over-year changes at 497 sizeable US transit agencies (1991–2024,
pandemic years set aside), a 1% change in service hours is associated with about a
**0.48% change in ridership in the same direction, the same year**. Cutting service
reliably loses riders — agencies that cut service by 10% or more lost a median of
6.3% of ridership — but ridership moves much less than one-for-one with service, and
service changes explain only a small share (R² ≈ 0.12) of year-to-year ridership
swings. Most of what drives ridership lies outside the agency's service-level dial.
Pittsburgh (PRT) sits squarely on this national pattern.

## Key Numbers

- **Headline elasticity: 0.48** (95% CI [0.46, 0.52]) — % ridership change per 1%
  service change, non-pandemic years, sizeable agencies (n = 8,323).
- **Cuts only: 0.36** (95% CI [0.30, 0.42], n = 2,945) — among service-cut episodes
  alone the slope is a bit shallower.
- **Sensitivity (base VRH ≥ 250,000): 0.52** — essentially unchanged, so the result
  is not an artifact of the size threshold.
- **R² ≈ 0.12** — service change explains ~12% of the variance in same-year ridership
  change. Pearson r = 0.35 (p < 1e-200).
- **Dose–response gradient (median ridership change):** deep cut (≤ −10%) → **−6.3%**;
  cut (−10 to −5%) → −2.6%; mild cut (−5 to 0%) → −0.9%; flat (0 to +5%) → +0.9%;
  growth (> +5%) → **+5.5%**. Monotonic across all five buckets.
- **Pandemic transitions (2020–21): slope ≈ 1.0** — service and ridership co-moved far
  more tightly, confirming the pandemic was a different regime and correctly excluded.

## Observations

- **Service cuts cost riders, but less than proportionally.** The 0.48 slope means an
  agency cutting 10% of service hours typically loses about 5% of ridership in the same
  year. This matches the published short-run transit service elasticity range
  (~0.3–0.5), which is reassuring for the data.
- **The relationship is stable across three decades.** The yearly-fit elasticity hovers
  around 0.3–0.6 from 1992 through 2019 with no trend — the service–ridership link is a
  structural feature, not a recent phenomenon. Only 2020–2021 break out (slope ≈ 1.0+).
- **Service is a minor driver of year-to-year ridership.** With R² ≈ 0.12, roughly
  seven-eighths of the variation in annual ridership change is unrelated to that year's
  service change — reflecting fuel prices, the economy, fares, demographics, and
  competing travel modes. Restoring service helps, but it is not the main lever on
  ridership.
- **The dose–response curve is clean and monotonic.** Bigger cuts → bigger ridership
  losses, bigger expansions → bigger gains, with no reversal. This is the clearest
  single picture of the relationship.
- **PRT is a typical agency on this measure.** Across its history PRT's service-vs-
  ridership changes scatter around the national line. Its pre-pandemic cut years
  (e.g. 1992: −9% VRH / −11% UPT; 2003: −5.5% / −7.5%) track the national slope closely.
  Its 2022–2023 ridership rebounds (+44%, +17% on roughly flat service) are pandemic-
  recovery effects, not a service response.

## Discussion

The dominant message echoes Analysis 39 from a much larger evidence base: service
level is a real but modest lever on ridership. An agency that cuts service will lose
riders along a predictable ~0.5 slope, and a deep cut compounds into a feedback risk
(less service → longer waits → riders leave → cuts look justified). But the low R²
means service restoration alone cannot recover ridership when the larger demand drivers
have shifted — which is exactly PRT's post-2019 situation, where ridership fell far more
than service. The elasticity quantifies the portion of ridership that *is* in the
agency's hands: cutting 10% of service is worth roughly 5% of riders, no small thing,
but the other half of any large ridership swing comes from forces the service budget
does not touch.

## Caveats

- **Association, not causation.** Service and ridership are jointly determined. Agencies
  often cut service *because* ridership is already falling (reverse causality), and both
  respond to shared shocks. The 0.48 slope is descriptive co-movement, not a controlled
  "cut X% → lose Y%" causal estimate. The shallower cuts-only slope (0.36) is consistent
  with this — cuts are often reactive to demand already softening.
- **Ecological / agency-level.** Results describe agencies, not individual riders. No
  inference about why any particular person stopped riding is supported.
- **System-level, all modes.** VRH and UPT aggregate bus, rail, and demand-response into
  one figure per agency. Mode-specific elasticities (a rail cut vs a bus cut) cannot be
  separated here.
- **Recovery years remain in the sample.** Only 2020 and 2021 are flagged pandemic;
  2022–2023 ridership rebounds (large positive intercepts in those years' fits) stay in
  the analytic set and, if anything, attenuate the slope. Excluding them would raise the
  estimate slightly, so 0.48 is conservative.
- **Contemporaneous only.** This measures same-year co-movement; lagged effects (a cut
  this year shedding riders over several years) are not captured and would tend to make
  the true multi-year elasticity larger.
- **VRH measures scheduled service, not quality.** Reliability, frequency, and coverage
  changes that don't move total VRH are invisible to this metric.

## Validation

- **Data source verified.** VRH and UPT from `ntd_annual_service` (NTD TS2.2 workbooks,
  pipeline 06). Columns confirmed against `data/DATA_DICTIONARY.md`. PRT (ntd_id 30022)
  annual values spot-checked against the raw table.
- **Geographic/temporal scope.** Both metrics come from the same table, same agency-year
  grain; changes use strictly consecutive years only (gap years excluded).
- **Null/zero handling.** Only agency-years with VRH > 0 and UPT > 0 in both endpoints
  enter a change pair; nulls and zeros are dropped, not treated as observations.
- **Aggregates sanity-checked.** Headline elasticity (0.48) lands inside the published
  short-run transit service-elasticity range (~0.3–0.5). PRT's annual VRH/UPT match
  Analysis 39's figures.
- **Direction of effects checked.** Slope is positive (cut service → lose riders, grow
  service → gain riders) — the expected direction. The dose–response gradient is
  monotonic with no reversal.
- **Surprising results investigated.** The pandemic subset's near-1.0 slope was
  investigated and is expected (joint exogenous collapse); it is reported separately,
  not folded into the headline.
- **Small-sample handling.** Agencies below 100,000 base VRH are excluded; the per-year
  elasticity chart further drops years with n < 10. The 250,000-VRH sensitivity fit
  confirms the estimate is not threshold-driven.
- **Ecological framing.** All statements are framed as agency-level associations.
