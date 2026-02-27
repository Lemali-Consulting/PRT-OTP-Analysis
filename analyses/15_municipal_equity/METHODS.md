# Methods: Municipal/County Equity

## Question
Analysis 04 examined neighborhood equity but lost 58% of stops due to missing `hood` data. The `muni` (municipality) and `county` fields have broader coverage. Do suburban municipalities get better or worse service reliability than the City of Pittsburgh? Do routes that cross municipal boundaries perform differently?

## Approach
- For each stop, assign OTP from the routes serving it (trip-weighted average from `route_stops` and `otp_monthly`).
- Aggregate stop-level OTP by municipality and county, weighted by trips.
- Rank municipalities by average OTP.
- Identify **cross-jurisdictional routes** (routes with stops in 2+ municipalities) and compare their OTP to single-municipality routes.
- Compare Pittsburgh city vs suburban municipalities.
- Bar chart of top/bottom municipalities, and Pittsburgh vs suburban comparison.

## Data

| Name | Description | Source |
|------|-------------|--------|
| `stops` | Municipality (`muni`) and county for each stop | `prt.db` table |
| `route_stops` | Links routes to stops with trip counts | `prt.db` table |
| `otp_monthly` | Monthly OTP per route | `prt.db` table |
| `routes` | Mode classification | `prt.db` table |

## Output
- `output/municipal_otp.csv` -- per-municipality average OTP and stop count
- `output/top_bottom_municipalities.png` -- bar chart of best/worst municipalities
- `output/pittsburgh_vs_suburban.png` -- comparison chart
