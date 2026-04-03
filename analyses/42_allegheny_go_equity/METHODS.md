# Methods: Allegheny Go Equity

## Question

Do municipalities with poor on-time performance have higher or lower Allegheny Go
fare-program adoption? If low-income residents disproportionately live in areas
with unreliable bus service, the program's benefits may be undercut by poor
service quality.

## Approach

1. Load tract-level Allegheny Go adoption data (`tract_reach.csv`), which reports
   reached households per census tract in five tiers (1-5, 6-25, 26-50, 51-100,
   101-500). Convert tiers to numeric midpoints for aggregation.
2. Aggregate adoption to municipality level (sum of midpoint households, count of tracts).
3. Compute municipality-level trip-weighted OTP from `route_stops`, `stops`, and
   `otp_monthly`, following the same pre-aggregation pattern as Analysis 15.
4. Join adoption and OTP on normalized municipality name.
5. Compute Spearman rank correlation between municipal adoption and OTP.
   Run with and without Pittsburgh as a robustness check.
6. Summarize program demographics as context.

## Data

| Name | Description | Source |
|------|-------------|--------|
| `tract_reach.csv` | Census-tract-level Allegheny Go enrollment reach | `data/allegheny-go/` |
| `demographics_summary.csv` | Program demographics by age/race/gender/children | `data/allegheny-go/` |
| `stops` | Municipality for each stop | `prt.db` table |
| `route_stops` | Links routes to stops with trip counts | `prt.db` table |
| `otp_monthly` | Monthly OTP per route | `prt.db` table |

## Output

- `muni_adoption_otp.csv` — per-municipality OTP and Allegheny Go adoption
- `adoption_vs_otp.png` — scatter of adoption vs OTP by municipality
- `demographics_summary.png` — bar charts of program demographics
