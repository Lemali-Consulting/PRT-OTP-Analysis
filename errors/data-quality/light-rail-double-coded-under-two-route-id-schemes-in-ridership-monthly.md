---
title: Light rail double-coded under two route_id schemes in ridership_monthly
date: 2026-05-15T17:14:38Z
---

## What happened

The `ridership_monthly` table records PRT's light rail network under two
overlapping `route_id` schemes:

- `BLLB` ("BLUE LINE - LIBRARY") and `BLSV` ("BLUE LINE - SOUTH HILLS VILLAGE"),
  both `mode = 'Light Rail'`, present only 2017-01 to 2020-02.
- `BLUE`, `RED`, and `SLVR`, all `mode = 'Rail'`, present the full 2017-01 to
  2024-10 period.

Both schemes carry data for the 2017-2020 overlap window, so any analysis that
sums or ranks all route_ids double-counts light rail ridership in those years
and inflates the system total. The two `mode` labels (`Light Rail` vs `Rail`)
for what is one physical network compound the confusion.

Two additional fragmentary records exist in the same table: `MNT`/`MNT1`
(`mode = 'Rail'`, no `route_name`, 1 and 7 months) and `NA` (no route_id/name/
mode, 1 month).

## How it was discovered

While building the Route Ridership Ranking analysis, the first run ranked
`BLSV` 1st and `BLLB` 3rd as separate light-rail routes. PRT operates a single
light rail system (three T lines), so two "Blue Line" entries near the top of a
route ranking was implausible. Checking each rail route_id's month coverage
showed `BLLB`/`BLSV` ending in 2020-02 while `BLUE`/`RED`/`SLVR` spanned the
full period -- confirming the same service was coded twice. The all-period
weekday averages settled it: old scheme `BLSV` (9,039) + `BLLB` (6,275) = 15,314
vs new scheme `BLUE` (4,929) + `RED` (6,269) + `SLVR` (4,038) = 15,236 -- near
identical totals, i.e. the same ridership recoded.

## What was done

The Route Ridership Ranking analysis and analysis 24 (Daytype Ridership Trends)
both exclude the five codes (`BLLB`, `BLSV`, `MNT`, `MNT1`, `NA`) via an
`EXCLUDED_ROUTES` constant, documented in their METHODS.md and FINDINGS.md. The
superseded pre-2020 Blue Line codes are dropped because `BLUE`/`RED`/`SLVR`
already cover the full period including the overlap.

The four other ridership analyses were then audited:

- **Analysis 24 (Daytype Ridership Trends) -- was affected, now fixed.** It
  queries `ridership_monthly` directly and sums all routes per month, so the
  pre-2020 system total was inflated ~6.5%. This inflated the Jan 2019 baseline
  and understated post-COVID recovery: weekday recovery rose from 64.5% to 69.0%,
  Saturday from 90.7% to 92.8%, Sunday from 83.9% to 86.0% after the fix. The
  same `EXCLUDED_ROUTES` filter was added to its `load_ridership()`.
- **Analyses 19, 25 -- not affected.** Both inner-join `ridership_monthly` to
  `otp_monthly` on `route_id`. `otp_monthly` contains only `BLUE`/`RED`/`SLVR`
  for rail (no `BLLB`/`BLSV`), so the superseded codes are dropped by the join.
- **Analysis 34 -- not affected.** It uses stop-level ridership from
  `wprdc_stop_data.csv` and never reads `ridership_monthly`.

A longer-term fix would reconcile the schemes during `build_db.py` ingestion so
no analysis has to carry an exclusion list.

## Relevant commits

Recorded alongside the Route Ridership Ranking analysis; see `git log` for
`analyses/47_route_ridership_ranking/` and the analysis 24 double-count fix.
