# Methods: System-Wide OTP Trend

## Question
Is PRT on-time performance improving, declining, or stable over the 2019--2025 period?

## Approach
- Compute a monthly system-wide OTP by averaging across all routes, weighted by daily trip counts so high-frequency routes count more.
- **Time-varying weights (Jan 2019 -- Mar 2021):** Use `daily_trips` from `scheduled_trips_monthly` (WEEKDAY day type), sourced from WPRDC monthly schedule data. This provides month-specific service levels per route.
- **Static fallback (Apr 2021 -- Nov 2025):** Use `MAX(trips_7d) / 7` from `route_stops` as an approximate daily trip count per route. MAX avoids the SUM-across-stops conflation with route length (Methodology Issue #1).
- Also compute an unweighted mean for comparison.
- Stratify by mode: compute a separate bus-only weighted and unweighted trend to isolate bus performance from structurally higher-performing rail routes.
- Plot all four series (all-mode weighted/unweighted, bus-only weighted/unweighted) as time series to identify trends, seasonal patterns, and the COVID-era shift. The time-varying weight region is shaded on the chart.
- Compute year-over-year change to quantify the direction.

## Data
- `otp_monthly` -- monthly OTP per route
- `scheduled_trips_monthly` -- WPRDC time-varying daily trip counts per route per month (WEEKDAY), Nov 2016 -- Mar 2021
- `route_stops` -- static trip counts for fallback weighting (Apr 2021 onward)
- `routes` -- mode classification (used to compute bus-only trends)

## Output
- `output/system_trend.csv` -- monthly weighted and unweighted OTP (all modes), with pct_time_varying column
- `output/system_trend_bus_only.csv` -- monthly weighted and unweighted OTP (bus only)
- `output/system_trend.png` -- time series chart with all-mode and bus-only overlays; shaded region marks time-varying weight period
