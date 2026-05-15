# Findings: Route Ridership Ranking

## Summary
Ranked all 103 PRT routes by average weekday daily ridership over 2017-2024.
The busiest route is the **P1 East Busway-All Stops** (6,635 weekday riders),
followed by the **Red Line** light rail (6,269) and the **51 Carrick** bus
(6,063). Ridership is heavily concentrated: the top 18 routes carry half of all
weekday ridership, and the top 47 carry 80%. The remaining ~55 routes share the
last fifth.

## Key Numbers
- **103 routes** ranked; system total **147,413** average weekday daily riders.
- **Top 5:** P1 (6,635), RED (6,269), 51 (6,063), BLUE (4,929), 61C (4,816).
- **Concentration:** top 18 routes = 50% of weekday ridership; top 47 = 80%.
- **By mode:** Bus carries 131,289 riders across 99 routes (89%); Rail 15,236
  across 3 routes (10%); the Monongahela Incline 888 across 1 route (0.6%).
- **3 routes** flagged `short_history` (< 12 weekday months of data).

## Observations
- The single busiest route is a bus rapid transit corridor (P1 East Busway),
  not a rail line -- consistent with PRT's busway-centric network design.
- Three light rail lines (Red, Blue, Silver) all rank in the top 8, each
  carrying 4,000-6,300 weekday riders despite being only 3 of 103 routes.
- The 61x and 71x route families (Oakland/East End corridors) dominate the
  upper-middle of the ranking -- seven of the top 13 routes are 61- or 71-coded.
- The long tail is real: roughly half of all routes individually account for
  less than 1% of system weekday ridership each.

## Caveats
- **Two light-rail code schemes.** The pre-2020 Blue Line codes `BLLB`/`BLSV`
  were excluded because the same service is recorded for the full period under
  `BLUE`/`RED`/`SLVR`. Keeping both would have double-counted rail ridership in
  2017-2020. See METHODS.md.
- **Average spans a disrupted period.** The 2017-2024 window includes the COVID
  ridership collapse and partial recovery, so a route's average sits below its
  typical pre-pandemic level and above its 2020 trough. This is a historical
  average, not a current snapshot.
- **Routes operate for different spans.** A route present for only part of the
  period is averaged over the months it ran. Three short-history routes are
  flagged; their ranks rest on a thin window.
- **Ecological scope.** This ranks routes, not riders or neighborhoods. A
  high-ridership route is not necessarily efficient -- pair with a productivity
  analysis (passengers per revenue hour) for that.
- **Weekday-only ranking.** Saturday and Sunday averages are in the CSV but do
  not affect rank; a weekend-heavy route may rank lower here than its total
  ridership would suggest.

## Validation

### Data inputs
1. **Data source verified.** Columns (`route_id`, `month`, `day_type`,
   `avg_riders`, `route_name`, `mode`) confirmed against the `ridership_monthly`
   table definition in `build_db.py`. No column mapping written from memory.
2. **Temporal scope.** Single table, single window (2017-01 to 2024-10). The
   ranking metric is filtered to `day_type = 'WEEKDAY'` consistently.
3. **Null handling.** `avg_riders IS NULL` rows dropped in the query. Routes
   with no weekday record are dropped from the ranking (`weekday_avg_riders`
   not null filter). Saturday/Sunday columns may be null where a route runs no
   weekend service -- left as null, not zero-filled.

### Results plausibility
4. **Aggregates sanity-checked.** System total of 147k average weekday riders is
   plausible for a multi-year average that includes the COVID trough (PRT's
   pre-pandemic weekday ridership was ~200k+; the 2020-2022 collapse pulls the
   2017-2024 mean well below that).
5. **Surprising results investigated.** An initial run had `BLSV`/`BLLB`
   ranking 1st and 3rd as separate light-rail routes. Investigation found these
   are superseded pre-2020 Blue Line codes overlapping `BLUE`/`RED`/`SLVR`,
   which double-counted rail. They were excluded; the corrected ranking has P1
   first. An error report was filed.
6. **Direction of effects checked.** The ranking matches known PRT high-ridership
   corridors -- East Busway (P1), the T lines, Carrick (51), and the Oakland
   61/71 families all rank at the top, as expected.

### Statistical diagnostics
7. **Multicollinearity.** Not applicable -- no regression in this analysis.
8. **Small-sample routes flagged.** Routes with fewer than 12 weekday months are
   flagged `short_history` in the output (3 routes); none were silently dropped.
9. **Ecological framing.** Results describe route-level ridership volumes, not
   individual rider behavior. Noted in Caveats.
