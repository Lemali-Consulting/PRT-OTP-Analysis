# Methods: Allegheny Go Program Growth

## Question

How has the Allegheny Go fare program grown since its May 2024 launch, and does
its ridership growth track with or diverge from system-level on-time performance?

## Approach

1. Load weekly ridership from the `allegheny_go_weekly` database table and convert
   to monthly totals by assigning each week to its calendar month.
2. Compute monthly system-average OTP from `otp_monthly`.
3. Load weekly enrollments from CSV, convert to monthly.
4. Overlay monthly rides on system OTP using a dual-axis chart for the overlap
   period (May 2024 through November 2025).
5. Track rides-per-rider as a utilization metric over time.
6. Build an enrollment-by-type stacked area chart.

## Data

| Name | Description | Source |
|------|-------------|--------|
| `allegheny_go_weekly` | Weekly rides and unique riders | `prt.db` table |
| `enrollments_weekly.csv` | Weekly enrollments by type | `data/allegheny-go/` |
| `otp_monthly` | Monthly OTP per route | `prt.db` table |

## Output

- `growth_vs_otp.csv` — monthly Allegheny Go metrics alongside system OTP
- `ridership_otp_overlay.png` — dual-axis chart of program ridership and system OTP
- `enrollment_by_type.png` — stacked area of enrollment types over time
- `utilization_trend.png` — rides-per-rider utilization over time
