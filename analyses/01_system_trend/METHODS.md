# Methods: System-Wide OTP Trend

## Question
Is PRT on-time performance improving, declining, or stable over the 2019--2025 period?

## Approach
- Compute a monthly system-wide OTP by averaging across all routes, weighted by `trips_7d` from `route_stops` (so high-frequency routes count more).
- Also compute an unweighted mean for comparison.
- Stratify by mode: compute a separate bus-only weighted and unweighted trend to isolate bus performance from structurally higher-performing rail routes.
- Plot all four series (all-mode weighted/unweighted, bus-only weighted/unweighted) as time series to identify trends, seasonal patterns, and the COVID-era shift.
- Compute year-over-year change to quantify the direction.

## Data
- `otp_monthly` -- monthly OTP per route
- `route_stops` -- trip counts for weighting
- `routes` -- mode classification (used to compute bus-only trends)

## Output
- `output/system_trend.csv` -- monthly weighted and unweighted OTP (all modes)
- `output/system_trend_bus_only.csv` -- monthly weighted and unweighted OTP (bus only)
- `output/system_trend.png` -- time series chart with all-mode and bus-only overlays
