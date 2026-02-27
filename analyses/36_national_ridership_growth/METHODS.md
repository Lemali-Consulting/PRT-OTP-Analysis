# Methods: National Ridership Growth (2019 vs 2024)

## Question
What is the average 2019-to-2024 ridership change across the 150 largest US transit agencies, and where does Pittsburgh Regional Transit rank?

## Approach
- Sum unlinked passenger trips (UPT) by agency across all modes/TOS for calendar years 2019 and 2024.
- Require at least 10 months of non-null data in both years to avoid partial-year artifacts.
- Rank agencies by 2019 total to define the "top 150" (pre-pandemic baseline, not distorted by COVID).
- Compute percent change ((2024 − 2019) / 2019 × 100) per agency.
- Report median, mean, and IQR of the percent change distribution.
- Count how many agencies have recovered to or exceeded 2019 levels.
- Identify PRT's rank in the distribution.

## Data
- `ntd_ridership` — monthly UPT by agency/mode/TOS, filtered to 2019 and 2024.
- `ntd_agency` — agency names for labeling.

## Output
- `output/ridership_growth_distribution.png` — histogram of percent change with PRT highlighted.
- `output/ridership_growth_ranking.png` — horizontal bar chart of all 150 agencies, PRT in distinct color.
- `output/ridership_growth_data.csv` — per-agency data (ntd_id, agency_name, upt_2019, upt_2024, pct_change, rank).
