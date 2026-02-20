# Methods: Shelter Equity

## Question
Are bus shelters equitably distributed relative to ridership? Which high-usage stops lack shelters, and does shelter coverage vary by mode or ownership?

## Approach
- Aggregate pre-pandemic weekday ridership to the physical-stop level (summing across routes) to get total daily usage per stop.
- Classify each stop as sheltered or unsheltered using the `shelter` column; further break down by shelter owner.
- Compare median and mean usage between sheltered vs unsheltered stops (Mann-Whitney U test).
- Compute the share of total system ridership served by sheltered stops.
- Identify the top high-usage unsheltered stops (ranked by daily ons+offs) as priority candidates for shelter installation.
- Examine shelter coverage by mode (bus, busway, light rail) and stop type.
- Generate charts: ridership distribution by shelter status, shelter owner breakdown, and a priority list of unsheltered high-usage stops.

## Data
- `data/bus-stop-usage/wprdc_stop_data.csv` -- stop-level boardings/alightings, shelter status, stop type, mode

## Output
- `output/shelter_equity_summary.csv` -- per-stop summary with usage and shelter status
- `output/unsheltered_priority.csv` -- top unsheltered stops ranked by usage
- `output/ridership_by_shelter.png` -- box/violin plot comparing usage distributions
- `output/shelter_coverage_by_mode.png` -- bar chart of shelter coverage rates by mode
