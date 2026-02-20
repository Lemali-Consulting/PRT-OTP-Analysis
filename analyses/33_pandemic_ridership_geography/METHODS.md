# Methods: Pandemic Ridership Geography

## Question
Where did ridership fall the most during the pandemic, and does the geographic pattern differ by mode or stop type?

## Approach
- Compute average weekday usage per physical stop in two periods: pre-pandemic (mean of datekeys 201909, 202001) and pandemic (mean of 202009, 202104).
- Calculate the absolute change and percentage change in usage per stop.
- Classify stops into geographic zones using distance from downtown Pittsburgh centroid (40.4406, -79.9959): downtown core (< 2 km), inner ring (2-8 km), outer ring (> 8 km).
- Compare ridership loss by zone and mode.
- Generate a geographic scatter map of stops colored by percentage change.
- Produce summary bar chart by zone and a histogram of change distributions.

## Data
- `data/bus-stop-usage/wprdc_stop_data.csv` -- stop-level boardings/alightings across 4 time periods

## Output
- `output/pandemic_change_by_stop.csv` -- per-stop pre/post usage and change metrics
- `output/ridership_change_map.png` -- geographic scatter plot colored by % change
- `output/change_by_zone.png` -- bar chart of median % change by zone and histogram of changes
