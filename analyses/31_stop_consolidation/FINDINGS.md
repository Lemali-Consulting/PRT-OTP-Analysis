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

### What the data shows
Analysis 07 established that stop count is the strongest single predictor of poor OTP (r = -0.53), and this analysis shows that nearly half the system's stop-route pairs see trivially low usage. The correlation between stop count and OTP is real and robust across multiple specifications.

The concentration of candidates on flyer routes (P10, P16, O5) is intuitive: these routes traverse long suburban corridors where stops were placed at frequent intervals to maximize coverage, but actual demand clusters at a few park-and-ride or transfer locations.

### Why the OTP gain estimate is likely overstated
The +3.2 pp average gain estimate assumes each stop removed saves equivalent time, but PRT bus drivers already skip stops where no one is waiting and no one has signaled to alight. A low-usage stop with <5 daily boardings is empty on the vast majority of individual bus trips, meaning the bus already passes it without stopping most of the time. Removing the sign does not change this operational reality.

The cross-sectional regression slope (-0.059 pp/stop) captures the fact that routes with many stops are structurally different -- they are longer, serve denser urban corridors with more traffic signals, and have higher cumulative probability of someone being at the next stop. These are route design characteristics, not marginal effects of individual stops. The causal effect of removing a single low-usage stop is likely well below the regression estimate.

Analysis 34 (Ridership Concentration) reinforces this interpretation: per-stop ridership concentration has no correlation with OTP (r = -0.016, p = 0.88), suggesting dwell time from passenger volumes is not the dominant mechanism. The stop count/OTP relationship is better understood as a proxy for route design philosophy (local vs limited-stop vs express) rather than a per-stop causal lever.

### Accessibility and equity concerns
The 400 m walk-distance filter assumes riders can walk to the next stop, but this may not hold for riders with disabilities, elderly riders, or those with mobility limitations -- particularly given Pittsburgh's hilly terrain. ADA compliance is not just a legal requirement but a core service obligation. Any consolidation program would require stop-by-stop accessibility review. Some low-usage stops may also serve riders making short trips where incremental stop spacing is the primary value of the bus service.

### Reframing the finding
The stop count/OTP relationship is best read as evidence that **route design with fewer, better-spaced stops outperforms local-stop design** -- which is already reflected in the busway/express vs local gap (Analysis 02). The policy implication points more toward limited-stop or express overlays on high-ridership corridors than toward individual stop removal. Converting low-usage suburban segments to limited-stop service (as the flyer route candidates suggest) is more defensible than piecemeal stop removal, because it redesigns the service pattern rather than degrading existing local coverage.

Stop consolidation remains politically sensitive. Community opposition to stop removal often exceeds what ridership data would justify. A phased approach -- starting with stops below 1 rider/day that have a neighbor within 200 m, with accessibility review -- would minimize controversy while testing whether actual OTP gains materialize.

## Caveats
- **The OTP gain estimate is likely overstated** because buses already skip empty stops operationally; removing the sign at a stop that is already being passed most trips has minimal time savings.
- The regression slope is a cross-sectional system-wide average reflecting route design differences, not a causal per-stop marginal effect. Individual stop removal may have near-zero impact.
- **Accessibility**: the 400 m walk-distance filter may be inadequate for riders with disabilities or limited mobility, especially on Pittsburgh's hilly terrain. ADA review is required before any consolidation.
- **Short trips**: some low-usage stops serve riders making short trips where incremental stop spacing is the primary value of the service.
- Stop usage data is from FY2019 (pre-pandemic); current usage patterns may have shifted.
- Some stops may appear low-usage on one route but serve high volumes on other routes at the same physical location; the data is per stop-route, not per physical stop.
- Projected stop counts can go negative for routes where the CSV has more stop-route combinations than the DB stop count (due to different data vintages).
