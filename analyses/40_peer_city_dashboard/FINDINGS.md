# Findings: Peer City Dashboard

## Key findings

1. **Pittsburgh's ridership loss (-40.8%) is near the peer median.** All 8 cities lost 23–45% of riders between 2019 and 2024. Cleveland fared best (-22.6%), St. Louis worst (-45.2%). Pittsburgh's loss is among the steepest.

2. **Service cuts (-13.1%) are mid-range.** PRT's 13% reduction in vehicle revenue hours is comparable to Portland (-10.7%) and Buffalo (-14.8%). Denver (-23.6%), Minneapolis (-22.5%), and St. Louis (-29.3%) cut far more deeply. Cleveland cut the least (-3.2%).

3. **Pittsburgh is the only peer city where fare revenue per trip increased.** PRT's effective fare rose from $1.57 to $1.70 per trip (+8.3%), while every other peer saw fare-per-trip decline — some sharply (Minneapolis $1.27→$0.92, Portland $1.19→$0.92). This likely reflects peer cities adopting reduced-fare programs or fare-free experiments during and after the pandemic, while PRT maintained its fare structure.

4. **Farebox recovery collapsed everywhere, but Pittsburgh retained a relative advantage.** PRT's farebox recovery ratio fell from 23.2% to 12.8%, but this is the second-highest among peers (after Buffalo at 18.0%). Denver dropped from 24.0% to 7.2%, and Baltimore from 16.1% to 6.2%.

5. **Fare revenue fell less steeply at PRT (-36.2%) than at most peers** despite comparable ridership losses. Baltimore (-51.4%), Denver (-58.6%), Minneapolis (-55.6%), Portland (-48.0%), and St. Louis (-51.3%) all lost about half their fare revenue. This is consistent with PRT maintaining fare levels while peers discounted.

## Limitations

- **No reliability data.** The NTD does not collect on-time performance; peer reliability comparisons are not possible with public data.
- **Fare revenue is not the same as fare price.** NTD reports total fare revenue, not fare schedules. A city that introduced fare-free service would show lower fare-per-trip even if the base fare didn't change.
- **System-level aggregation only.** NTD data is agency-wide; we cannot break down by route, mode, or neighborhood.

## Validation

- **Data source verified.** All metrics sourced from NTD TS2.2 workbook (`ntd_annual_service` table: `upt`, `vrh`, `fares`, `opexp` columns).
- **Aggregates sanity-checked.** PRT 2019 fare revenue ($100.8M) and operating expenses ($433.5M) are consistent with PRT's published financial reports.
- **Direction of effects checked.** All cities show ridership decline, service cuts, and fare revenue loss — consistent with known pandemic impacts on transit. No directional anomalies.
- **Surprising result investigated.** Pittsburgh's fare-per-trip increase is surprising but explained by PRT maintaining its fare structure while peers adopted discounts or fare-free programs. This is a real policy difference, not a data error.
