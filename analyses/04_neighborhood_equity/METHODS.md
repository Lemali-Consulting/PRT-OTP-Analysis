# Methods: Tract Equity

## Question
How does on-time performance vary across the geographic and demographic landscape PRT serves -- by census tract, by tract income level, and by race composition?

## Approach
- Replace the fuzzy `stops.hood` field (NULL for ~58% of stops, only 89 hand-curated areas) with **point-in-polygon assignment** of every PRT stop to its containing 2020 census tract (TIGER 2022 polygons in `census_tracts`). All 6,466 stops map to a tract; 343 tracts have at least one stop.
- Pre-aggregate OTP to one row per route (`AVG(otp) GROUP BY route_id, HAVING COUNT(*) >= 12`) so each route contributes one weight regardless of how many months it has data for.
- Join route-level mean OTP to `route_stops` (filtered to non-null `trips_7d`) and to the stop→tract assignment.
- For each tract, compute:
  - **Weighted OTP**: route-level mean OTP weighted by `trips_7d` -- "what OTP does the average *trip* in this tract experience?"
  - **Unweighted OTP**: simple average across the unique routes touching the tract -- "what is the average reliability of *routes* serving this area?"
  - `otp_gap = weighted - unweighted` (where high-frequency routes over- or under-perform their route average).
- Filter to tracts served by **at least 2 routes** (`MIN_ROUTES = 2`); single-route tracts are too noisy to rank.
- **Bus-only stratification**: re-run weighted OTP using only BUS-mode routes to detect Simpson's paradox (rail inflating an area's apparent equity).
- **Income gradient**: bin tracts into 5 quintiles by `median_household_income` (B19013), then compute trip-weighted mean OTP per quintile.
- **Quintile time series**: per-tract-month weighted OTP, then trailing 12-month rolling assignment to OTP quintiles (avoids look-ahead) to track whether the equity gap is widening or narrowing.

## Data

| Name | Description | Source |
|------|-------------|--------|
| `otp_monthly` | Monthly OTP per route (routes with < 12 months excluded) | `prt.db` table |
| `route_stops` | Routes ↔ stops with `trips_7d` for trip weighting | `prt.db` table |
| `stops` | `lat`/`lon` (for point-in-polygon) and `muni`/`county` (for tract labels) | `prt.db` table |
| `routes` | `mode` for bus-only stratification | `prt.db` table |
| `census_tracts` | TIGER 2022 tract polygons + ACS 5-year (2018-2022) demographics: `population` (B01003), `median_household_income` (B19013), `households_zero_vehicle` (derived from B25044), race composition (B03002) | `prt.db` table (Pipeline 10) |

## Output
- `output/tract_otp.csv` -- per-tract weighted/unweighted OTP, otp_gap, route/stop counts, bus-only OTP, plus tract demographics (population, median income, %zero-vehicle households, %non-white population, primary muni/county)
- `output/tract_otp_bus_only.csv` -- bus-only weighted OTP per tract
- `output/otp_by_income_quintile.csv` -- mean OTP and trip-weighted OTP for each tract income quintile
- `output/tract_equity.png` -- top/bottom tracts bar chart and quintile time series
- `output/weighted_vs_unweighted_otp.png` -- scatter and gap chart for the frequency-weighting effect
- `output/otp_by_income.png` -- tract OTP scattered against median income, plus per-quintile means
