# Methods: Ridership Concentration (Pareto)

## Question
How concentrated is ridership across stops? What fraction of stops serves 80% of riders, and does ridership concentration on a route correlate with that route's OTP?

## Approach
- Aggregate pre-pandemic weekday stop-level ridership (datekeys 201909, 202001) to physical-stop level and per-route level.
- **System-wide Pareto**: sort all stops by usage, compute cumulative share, and find the fraction of stops that serve 50%, 80%, and 90% of total ridership.
- **Per-route Gini coefficient**: for each route, compute the Gini coefficient of stop-level usage as a concentration metric (0 = perfectly even, 1 = all ridership at one stop).
- Join per-route Gini with route-level average OTP from the database and test for correlation (Pearson, Spearman).
- Generate a system-wide Pareto curve and a scatter plot of Gini vs OTP by route.

## Data
- `data/bus-stop-usage/wprdc_stop_data.csv` -- stop-level boardings/alightings
- `otp_monthly` -- monthly OTP per route
- `routes` -- route name and mode

## Output
- `output/pareto_system.csv` -- cumulative ridership share by stop rank
- `output/route_gini.csv` -- per-route Gini coefficient and OTP
- `output/pareto_curve.png` -- system-wide Pareto curve
- `output/gini_vs_otp.png` -- scatter plot of route Gini vs average OTP
