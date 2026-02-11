# Methods: COVID Recovery Trajectories

## Question
PRT system OTP declined from ~69% pre-COVID to ~62% currently (Analysis 01). But did all routes decline equally, or did some recover while others cratered? What route characteristics predict recovery?

## Approach
- Define **pre-COVID baseline** as average OTP during 2019-01 through 2020-02 (14 months before COVID disruption).
- Define **current period** as the trailing 12 months of data.
- For each route with data in both periods, compute:
  - **Recovery delta** = current OTP - baseline OTP (positive = improved, negative = declined).
  - **Recovery ratio** = current OTP / baseline OTP.
- Exclude routes with fewer than 6 months in either period.
- Characterize recovery by mode, bus subtype, stop count, and geographic span.
- Identify the most-recovered and most-declined routes.
- Test whether mode, stop count, or bus subtype predicts recovery.

## Data
- `otp_monthly` -- monthly OTP per route
- `routes` -- mode classification
- `route_stops` -- stop count per route

## Output
- `output/covid_recovery.csv` -- per-route baseline, current, delta, and characteristics
- `output/recovery_distribution.png` -- histogram of recovery deltas
- `output/recovery_by_mode.png` -- box plot of recovery delta by mode/subtype
