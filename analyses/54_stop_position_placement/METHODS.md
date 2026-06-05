# Methods: Stop Position and Near-Side Placement

## Question
Does near-side vs. far-side stop placement vary by position along the route?
And does the near-side fraction in the *second half* of a route — where delay
has had more time to accumulate — predict route OTP better than the overall
near-side fraction?

## Approach

### Step 1 — Assign normalized position to each classified stop
Join the stop classifications from Analysis 53 to `stop_times` via the stop's
canonical `shape_id` → `trip_id` mapping. For each stop on its canonical trip,
compute:

  `position = (stop_sequence − 1) / (max_stop_sequence − 1)`

This gives a value in [0, 1] where 0 = first stop, 1 = last stop. Only
near_side and far_side stops are included; mid-block and ambiguous are excluded.

### Step 2 — Test for position gradient in near-side fraction
Bin stops into 5 equal-width position quintiles (0–20%, 20–40%, …, 80–100%)
and compute the near-side fraction within each quintile. Plot as a bar chart.
Run a logistic regression of classification (near_side = 1, far_side = 0) on
normalized position to test whether position is a significant predictor.

### Step 3 — Split-half OTP predictor comparison
For each route, compute:
- `ns_first_half`: near-side fraction among stops with position < 0.5
- `ns_second_half`: near-side fraction among stops with position ≥ 0.5

Join to route mean OTP. Compare the Pearson r of each fraction with OTP
against the overall near-side fraction from Analysis 53. The hypothesis is that
`ns_second_half` is a stronger predictor because delay accumulates along the
route — a near-side stop near the terminus costs more in end-point OTP.

### Step 4 — KDE of stop position by classification
Overlay kernel density estimates of normalized stop position for near-side and
far-side stops to show whether the two classes cluster differently along routes.

## Data

| Source | How used |
|--------|----------|
| `analyses/53_stop_signal_placement/output/stop_classifications.csv` | Classification + canonical shape_id |
| `data/GTFS/stop_times.txt` | stop_id → stop_sequence per trip |
| `data/GTFS/trips.txt` | trip_id → shape_id, route_id |
| `otp_monthly` table in `prt.db` | Route mean OTP |

## Output
- `output/position_quintile_nearside.png` — near-side fraction by route-position quintile
- `output/position_kde.png` — KDE of stop position by classification
- `output/splithalf_otp_comparison.png` — first-half vs. second-half near-side fraction vs. OTP
- `output/route_position_summary.csv` — per-route ns_first_half, ns_second_half, ns_overall, mean_otp
