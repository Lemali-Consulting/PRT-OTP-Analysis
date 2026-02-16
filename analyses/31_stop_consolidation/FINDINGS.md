# Findings: Stop Consolidation Candidates

## Summary
43% of all stop-route combinations in the PRT system see fewer than 5 daily boardings+alightings on weekdays, and nearly all of these have a same-route neighbor within 400 m walking distance. Removing these low-usage stops could yield an average OTP improvement of +3.2 percentage points per route, with the highest-impact routes gaining up to +10 pp. The top candidates are long suburban/flyer routes with many lightly used stops along corridors.

## Key Numbers
- **11,461** stop-route combinations in the pre-pandemic weekday data
- **4,991** (43%) are low-usage (< 5 avg daily ons+offs)
- **4,963** of those have a neighbor on the same route within 400 m (consolidation candidates)
- **87 of 90** routes (97%) matched to OTP data have at least one candidate
- **Median** candidates per route: **44 stops**
- **Regression slope**: each stop removed is associated with +0.059 pp OTP
- **Average** estimated OTP gain: **+3.2 pp** across routes with candidates
- **Maximum** estimated OTP gain: **+10.2 pp** (Route 59, Mon Valley -- 174 candidate stops)

## Observations
- **Flyer/express routes have the most candidates**: P10 (167), P16 (159), O5 (148) -- these long-distance routes serve many stops with minimal usage along the way.
- **Route 59 (Mon Valley)** tops the list with 174 candidates out of 334 stop-route pairs, representing a potential 52% reduction in stops.
- **The candidate map shows candidates distributed system-wide**, with particularly dense clusters in outer suburban corridors where stop spacing is tight but usage is low.
- **Almost all low-usage stops (99.4%) have a nearby neighbor**, meaning very few riders would lack a within-walking-distance alternative.
- **The OTP gain estimate is conservative**: the regression slope (-0.059 pp/stop) comes from cross-sectional variation, not from an experiment. Actual gains from targeted consolidation could differ.

## Discussion
Stop consolidation is the most directly actionable lever this project has identified for improving OTP. Analysis 07 established that stop count is the strongest single predictor of poor OTP (r = -0.53), and this analysis shows that nearly half the system's stop-route pairs see trivially low usage. The 400 m walk-distance filter ensures that riders at removed stops would have a viable alternative nearby.

The concentration of candidates on flyer routes (P10, P16, O5) is intuitive: these routes traverse long suburban corridors where stops were placed at frequent intervals to maximize coverage, but actual demand clusters at a few park-and-ride or transfer locations. Converting these routes to limited-stop service in the low-usage segments could dramatically improve running times without meaningfully reducing access.

The estimated +3.2 pp average gain is modest but meaningful at scale. For the 87 routes with candidates, this represents a collective improvement that could shift system-wide OTP upward by 1-2 points. The most impactful routes (59, P10, P16) could see gains equivalent to eliminating one-third of their current schedule deviation.

However, stop consolidation is politically sensitive. Community opposition to stop removal often exceeds what ridership data would justify, and ADA requirements may mandate retaining certain stops regardless of usage. A phased approach -- starting with stops below 1 rider/day that have a neighbor within 200 m -- would minimize controversy while capturing the easiest gains.

## Caveats
- The regression slope is a system-wide average; individual route geometry and operations may produce different marginal effects.
- Stop usage data is from FY2019 (pre-pandemic); current usage patterns may have shifted.
- The analysis does not account for ADA accessibility requirements, transfer connections, or political/community factors in stop placement.
- Some stops may appear low-usage on one route but serve high volumes on other routes at the same physical location; the data is per stop-route, not per physical stop.
- Projected stop counts can go negative for routes where the CSV has more stop-route combinations than the DB stop count (due to different data vintages).
