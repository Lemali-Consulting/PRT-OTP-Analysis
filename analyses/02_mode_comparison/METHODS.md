# Methods: Mode Comparison

## Question
Does light rail (dedicated right-of-way) consistently outperform bus? Do limited/express routes beat their local counterparts?

## Approach
- Group routes by mode (BUS, RAIL, INCLINE) and compute average OTP per mode per month.
- Classify bus routes by type (local, limited, express/flyer, busway) using route ID patterns (L suffix, X suffix, P/G/O prefix).
- Compare paired routes sharing the same corridor (e.g. 51 vs 51L) as natural experiments.
- Test whether the mode gap changes over time.

## Data
- `otp_monthly` -- monthly OTP per route
- `routes` -- mode classification

## Output
- `output/mode_comparison.csv` -- monthly OTP by mode/type
- `output/mode_comparison.png` -- comparison chart
