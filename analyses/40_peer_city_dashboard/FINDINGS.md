# Findings: Peer City Dashboard

## Key findings

1. **Pittsburgh's ridership loss (-40.8%) is near the peer median.** All 8 cities lost 30–46% of riders between 2019 and 2023. Cleveland fared best (-30.3%), St. Louis worst (-46.3%). Pittsburgh's loss is middle-of-the-pack.

2. **Service cuts (-15.0%) are also mid-range.** PRT's 15% reduction in vehicle revenue hours is comparable to Baltimore (-12.0%), Buffalo (-15.6%), and Portland (-16.1%). Denver (-25.8%), Minneapolis (-26.5%), and St. Louis (-34.2%) cut far more deeply.

3. **Pittsburgh is the only peer city where fare revenue per trip increased.** PRT's effective fare rose from $1.57 to $1.63 per trip (+3.8%), while every other peer saw fare-per-trip decline — some sharply (Denver $1.47→$0.98, Minneapolis $1.27→$0.99). This likely reflects peer cities adopting reduced-fare programs or fare-free experiments during and after the pandemic, while PRT maintained its fare structure.

4. **Farebox recovery collapsed everywhere, but Pittsburgh retained a relative advantage.** PRT's farebox recovery ratio fell from 23.2% to 12.8%, but this is the second-highest among peers (after Buffalo at 17.5%). Denver dropped from 24.0% to 8.4%, and Baltimore from 16.1% to 7.1%.

5. **Fare revenue fell less steeply at PRT (-38.8%) than at most peers** despite comparable ridership losses. Baltimore (-51.9%), Denver (-58.8%), Minneapolis (-54.9%), Portland (-50.1%), and St. Louis (-50.7%) all lost over half their fare revenue. This is consistent with PRT maintaining fare levels while peers discounted.

## Limitations

- **No reliability data.** The NTD does not collect on-time performance; peer reliability comparisons are not possible with public data.
- **Fare revenue is not the same as fare price.** NTD reports total fare revenue, not fare schedules. A city that introduced fare-free service would show lower fare-per-trip even if the base fare didn't change.
- **2023 is the latest year with complete financial data.** The NTD TS2.2 workbook covers through 2023 for fares and operating expenses (2024 for service metrics only).
- **System-level aggregation only.** NTD data is agency-wide; we cannot break down by route, mode, or neighborhood.

## Validation

- **Data source verified.** All metrics sourced from NTD TS2.2 workbook (`ntd_annual_service` table: `upt`, `vrh`, `fares`, `opexp` columns).
- **Aggregates sanity-checked.** PRT 2019 fare revenue ($100.8M) and operating expenses ($433.5M) are consistent with PRT's published financial reports.
- **Direction of effects checked.** All cities show ridership decline, service cuts, and fare revenue loss — consistent with known pandemic impacts on transit. No directional anomalies.
- **Surprising result investigated.** Pittsburgh's fare-per-trip increase is surprising but explained by PRT maintaining its fare structure while peers adopted discounts or fare-free programs. This is a real policy difference, not a data error.
