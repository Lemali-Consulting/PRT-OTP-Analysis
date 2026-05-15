# Methods: Route Ridership Ranking

## Question
Which PRT routes carry the most riders? This analysis produces a single
leaderboard of every route ranked by average weekday daily ridership over the
full available history (January 2017 - October 2024).

## Approach
- Load every route-month-daytype record from `ridership_monthly`.
- Restrict the ranking metric to `WEEKDAY` records (weekday service is the
  largest and most comparable day type across routes).
- For each route, average `avg_riders` across all weekday months it operated.
  This yields the route's typical weekday daily ridership over the period.
- Rank routes descending by that average. Assign an integer rank, the route's
  share of total system weekday ridership, and a running cumulative share so the
  long tail of low-ridership routes is visible.
- Count the number of weekday months observed per route (`n_months`) and flag
  routes with fewer than 12 months of data, since their average rests on a
  short, possibly non-representative window.
- Carry Saturday and Sunday averages as extra columns for context (not used for
  ranking).
- Summarise totals and route counts by mode (Bus, Rail, Light Rail, Incline).

## Data

| Name | Description | Source |
|------|-------------|--------|
| `ridership_monthly` | Average daily riders per route, month, and day type | `prt.db` table |

Filters: `avg_riders IS NOT NULL`. The ranking metric uses `day_type = 'WEEKDAY'`
only.

Five route codes are excluded. The light-rail network appears under two
overlapping code schemes: `BLLB` and `BLSV` are the pre-2020 Blue Line codes,
and the same service runs the full 2017-2024 period under `BLUE`, `RED`, and
`SLVR` -- keeping both would double-count rail in 2017-2020. `NA`, `MNT`, and
`MNT1` are fragmentary rows with no route name. All other routes are kept;
short-history routes are flagged (`short_history`) rather than dropped.

## Output
- `output/route_ridership_ranking.csv` -- every route ranked, with weekday /
  Saturday / Sunday averages, month count, system share, and cumulative share.
- `output/top25_ridership.png` -- horizontal bar chart of the 25 busiest routes,
  coloured by mode.
- `output/ridership_by_mode.png` -- total weekday ridership and route count by mode.
