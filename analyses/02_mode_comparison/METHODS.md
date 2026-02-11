# Methods: Mode Comparison

## Question
Does light rail (dedicated right-of-way) consistently outperform bus? Do limited/express routes beat their local counterparts?

## Approach
- Exclude UNKNOWN-mode routes (37, 42, P2, RLSH, SWL) from the analysis to avoid ambiguous classifications.
- Group routes by mode (BUS, RAIL) and compute average OTP per mode per month, both unweighted and trip-weighted (using `trips_7d` from `route_stops`).
- Perform a Mann-Whitney U test on the monthly mode-level OTP distributions to formally test whether the RAIL--BUS difference is statistically significant.
- Classify bus routes by type using route ID patterns:
  - **Busway:** P1, P2, P3, G2 (dedicated right-of-way)
  - **Flyer:** Other P/G-prefix routes (e.g., P17, P78, G3, G31) and O-prefix routes (park-and-ride express services)
  - **Limited:** L-suffix routes (e.g., 51L, 53L)
  - **Express:** X-suffix routes
  - **Local:** All other bus routes
- Compare paired routes sharing the same corridor (e.g. 51 vs 51L) as natural experiments. Perform a paired t-test on monthly OTP differences and report the mean difference with a 95% confidence interval.
- Test whether the mode gap changes over time.

## Data
- `otp_monthly` -- monthly OTP per route
- `routes` -- mode classification (filter out UNKNOWN)
- `route_stops` -- trip counts for trip-weighted mode averages

## Output
- `output/mode_comparison.csv` -- monthly OTP by mode/type (unweighted)
- `output/mode_comparison_weighted.csv` -- monthly OTP by mode (trip-weighted)
- `output/mode_comparison.png` -- comparison chart
