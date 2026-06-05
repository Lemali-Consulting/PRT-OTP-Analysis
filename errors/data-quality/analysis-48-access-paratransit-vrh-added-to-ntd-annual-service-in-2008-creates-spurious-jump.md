---
title: Analysis 48: ACCESS paratransit VRH added to ntd_annual_service in 2008 creates spurious jump
date: 2026-06-05T15:28:14Z
---

## What happened

`ntd_annual_service` changed its VRH aggregate in 2008 to include ACCESS (demand-response / DR mode) paratransit vehicle revenue hours. Before 2008 that table reported fixed-route-only VRH; starting in 2008 it included ~700K ACCESS hours per year.

This produced an artificial 18% jump in PRT's VRH from 2007 (2,190,548) to 2008 (2,587,521) — the exact opposite of what actually happened. Fixed-route service (MB + LR) was CUT from ~2.08M to ~1.88M hours following Port Authority's June 2007 service cuts.

Because UPT was always reported as all-mode (ACCESS boardings were included throughout), the mixed series also inflated pre-2008 productivity (ACCESS VRH absent from denominator) and deflated post-2008 productivity (ACCESS VRH now in denominator). The original findings stated "service hours barely moved (VRH −5%)" — the corrected fixed-route figure is VRH −26%.

## How it was discovered

A user noticed that Analysis 48's decomposition chart showed VRH rising in 2007-08, which contradicted published news reports of Port Authority service cuts in June 2007 (Pittsburgh Post-Gazette, 2007-06-16).

Cross-referencing `ntd_ridership` mode-level data confirmed the cause: DR mode VRH first appears in 2007 in the monthly table (~726K hrs/year), and the 2008 `ntd_annual_service` aggregate matches MB+LR+DR combined — confirming ACCESS was added to the aggregate that year.

## What was done

Updated `analyses/48_service_productivity/main.py` to build a corrected PRT series:
- For years 1991–2007: `ntd_annual_service` VRH used as-is (already fixed-route only).
- For years 2008–2024: DR VRH and UPT are subtracted from `ntd_annual_service` totals using annual sums from `ntd_ridership`.

Peer comparison charts continue to use `ntd_annual_service` directly (agency-wide, consistent across all 8 agencies for the comparison years).

Updated `FINDINGS.md` and `METHODS.md` with corrected numbers and documentation of the correction.

## Relevant commits

<!-- filled in after commit -->
