# Research Plan

This document tracks the analysis roadmap, sequencing, and open methodological priorities.

## Immediate Priorities

1. Maintain reproducible data ingestion via `pipeline/`.
2. Keep all analyses independently runnable and documented.
3. Publish provenance-linked outputs through `products/website/`.

## Current Focus

- Harden pipeline and manifest coverage.
- Keep findings synchronized across local analysis docs and root summaries.
- Expand cross-analysis synthesis in `FINDINGS.md` and report products.

## Backlog

### Census-tract follow-ups

The `census_tracts` table (Pipeline 10, added with Analysis 44) joins TIGER 2022 polygons with ACS 5-year (2018–2022) total population for Allegheny + Beaver + Butler + Washington + Westmoreland counties. It enables several follow-up analyses:

1. **Population-weighted system OTP.** Weight each route's OTP by its `population_served` (Analysis 44 output) to compute the OTP experienced by the average resident, then compare to trip-weighted (Analysis 19) and unweighted system OTP. *Joins: `otp_monthly` × Analysis 44 output.*

2. **Transit deserts.** Of the 2.17M people in the 5-county area, what share live outside any walkshed? Map gaps and rank the largest underserved tracts. *Joins: `census_tracts` × `stops` (buffer union).*

3. **Tract-level upgrade for Analyses 04 / 15 / 32.** Replace the fuzzy `stops.hood` field (NULL for ~58% of stops) with point-in-polygon assignment to tracts. Expands neighborhood equity from 89 hand-curated areas to all 669 tracts and removes the no-hood gap. *Joins: `stops` × `census_tracts` (point-in-polygon).*

4. **Per-capita service supply vs peer cities.** Express NTD VRH per resident in the catchment instead of per agency, for fairer cross-city comparison. Requires extending the census ingestion to peer-city counties. *Joins: `ntd_annual_service` × `census_tracts` (extended).*

5. **Latent demand model.** Compute boardings-per-resident-in-walkshed for each tract; high-population/low-boarding tracts are intervention candidates, the inverse identifies overperformers. *Joins: `bus_stop_usage` × `stops` × `census_tracts`.*

6. **Richer ACS variables (foundational extension).** Adding `B19013` (median household income), `B25044` (vehicle ownership), and `B03002` (race/ethnicity) to Pipeline 10 — ~20 lines in `census_tracts.py` — enables genuine demographic-equity analyses (income vs OTP, zero-vehicle-household reach vs ridership) without the fuzzy `hood` field. Highest unlock per unit of effort; powers many follow-ups.
