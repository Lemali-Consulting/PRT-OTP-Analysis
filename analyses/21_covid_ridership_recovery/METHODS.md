# Methods: COVID Ridership vs OTP Recovery

## Question
Did routes that recovered ridership fastest also recover OTP? Or does ridership recovery degrade OTP (e.g., through crowding and longer dwell times)?

## Approach
- Define pre-COVID baseline as Jan 2019 -- Feb 2020 for both ridership and OTP.
- Define recovery period as Jan 2023 -- Oct 2024 (post-stabilization).
- For each route, compute ridership recovery ratio (recovery avg / baseline avg) and OTP recovery delta (recovery avg - baseline avg).
- Scatter plot ridership recovery vs OTP recovery, colored by mode/subtype.
- Test correlation (Pearson and Spearman) between ridership recovery and OTP recovery.
- Test for regression to the mean: compute correlation between baseline OTP and OTP delta. A significant negative correlation indicates RTM, which would bias the recovery correlation.
- Stratify by route subtype (local, express, premium, rail) and test for group differences.

## Data

| Name | Description | Source |
|------|-------------|--------|
| `otp_monthly` | route_id, month, OTP | `prt.db` table |
| `ridership_monthly` | route_id, month, day_type='WEEKDAY', avg_riders | `prt.db` table |
| `routes` | route_id, mode for subtype classification | `prt.db` table |

**Notes:** Join on route_id and month; restrict to overlap period. Exclude routes missing from either dataset or with fewer than 6 months in either period.

## Output
- `output/recovery_scatter.png` -- ridership recovery ratio vs OTP delta
- `output/recovery_by_subtype.png` -- box plots by route subtype
- `output/recovery_data.csv` -- per-route recovery metrics
