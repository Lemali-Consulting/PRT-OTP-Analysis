# Methodology Issues

A review of all 11 analyses for methodological flaws. Data quality issues are out of scope — this focuses on how each analysis is designed, calculated, or interpreted.

---

## Significant Issues

These could produce misleading or incorrect conclusions.

### 1. `SUM(trips_wd)` across stops measures stop-visits, not trip frequency (Analyses 01, 04, 06, 10, 11)

Multiple analyses sum `trips_wd` or `trips_7d` from `route_stops` across all stops, which yields `actual_trips × number_of_stops`, not trip count. This confounds every metric with route length. In **Analysis 11** it is especially damaging: routes with different inbound/outbound stop counts show phantom asymmetry even when actual trip counts are identical.

### 2. Static `trips_7d` weights applied across a multi-year period (Analyses 01, 04, 06)

The `route_stops` table is a single point-in-time snapshot, but it is used to weight OTP data spanning 2019–2025. Service levels changed dramatically over this period (COVID alone guarantees it). Analysis 01's "weighted system trend" retroactively applies current service patterns to historical months.

### 3. Single linear slope fitted through a COVID structural break (Analysis 03)

A single OLS line through 2019–2025 means every route's "trend" is dominated by the COVID drop, not by any recent trajectory. Routes that recovered fully still show a negative slope. The "improving vs. declining" rankings are largely a measure of COVID impact, not current direction.

### 4. Anomaly detection includes the current observation in its own baseline (Analysis 05)

The rolling mean and standard deviation include the month being tested. The more extreme an anomaly, the more it inflates the baseline stats and suppresses its own z-score. This is self-dampening — the detector is weakest precisely when it should be strongest.

### 5. Simpson's paradox from pooling modes (Analyses 02, 07, 10)

Correlations and averages are computed across BUS, RAIL, and INCLINE together. Rail has dedicated right-of-way and fundamentally different characteristics. The overall correlation between stop count and OTP (Analysis 07) or frequency and OTP (Analysis 10) could be entirely driven by between-mode differences, saying nothing about the within-mode relationship.

### 6. Route-level OTP spread to stops as if it were stop-level data (Analyses 04, 08)

The neighborhood equity and hotspot analyses join route-level OTP to individual stops, treating the same route-month observation as independent data for every stop it serves. This is an ecological fallacy — a route's OTP is not uniform across its stops. Analysis 04's equity quintiles and Analysis 08's "hotspot" map are both built on this inflated foundation.

---

## Moderate Issues

### 7. METHODS.md describes decomposition that code doesn't implement (Analysis 06)

The methods specify detrending before computing seasonal profiles (trend = 12-month rolling mean, seasonal = month-of-year mean of residuals). The code just computes raw month-of-year averages without removing trend, so any multi-year OTP trend contaminates the seasonal profile.

### 8. Look-ahead bias in quintile assignment (Analysis 04)

Neighborhoods are assigned to quintiles based on their overall mean OTP, then that fixed label is applied to monthly time series. This uses future data to classify past observations — a neighborhood that improved dramatically is stuck in a low quintile for its early months too.

### 9. Mean OTP ranking gives equal weight to 2019 and 2024 (Analysis 03)

The "best/worst" rankings average across all months equally. A route that was terrible during COVID but excellent now is penalized. For operational decisions, a trailing-12-month window would be more actionable.

### 10. No uncertainty shown for small-n groups (Analysis 02)

Mode-level averages for INCLINE (1–2 routes) and RAIL (~3 routes) are plotted alongside BUS (70+ routes) with no confidence intervals. Apparent "volatility" in RAIL/INCLINE is noise from small sample sizes.

### 11. Route length is an uncontrolled confounder (Analysis 07)

The hypothesis is that more stops cause worse OTP, but routes with more stops are also longer routes with more traffic, more signals, etc. The correlation may reflect route length, not stops per se.

### 12. Excluding combined "IB,OB" stops biases asymmetry upward (Analysis 11)

Stops labeled `IB,OB` are likely shared stops used in both directions. Excluding them means the remaining stops overrepresent the asymmetric portions of the route.

### 13. One-direction routes get asymmetry = 1.0 (Analysis 11)

Routes with trips in only one direction after filtering (e.g., routes 11, 60) receive the maximum asymmetry index, acting as outliers that dominate the Pearson correlation. These may be loop routes where IB/OB labeling is not applicable, not genuinely asymmetric operations.

### 14. No control for mode in correlation analyses (Analysis 10)

The scatter plot colors points by mode, but the Pearson r is computed across all modes combined. A stratified correlation (within BUS only) would be more defensible.

---

## Minor Issues

### 15. Paired-route comparison has uncontrolled confounds (Analysis 02)

Local and limited/express variants of the same corridor (e.g., 51 vs 51L) have different stop patterns, ridership profiles, and time-of-day schedules. Simply differencing their OTP values does not constitute a controlled comparison.

### 16. `var()` uses sample variance in slope denominator (Analysis 03)

Polars `.var()` defaults to ddof=1 (sample variance), while the OLS slope formula expects population variance (ddof=0). For routes near the 12-month minimum, this introduces a small error. The numerator uses `.mean()` (population covariance), making the formula internally inconsistent.

### 17. Slope units are not interpretable (Analysis 03)

The slope is in "OTP per time-index" where time-index is a sequential integer. This is not convertible to a natural unit like percentage points per year without additional context.

### 18. Z-scores on bounded [0,1] data violate normality (Analysis 05)

OTP values are proportions bounded between 0 and 1. Routes with high mean OTP (e.g., 0.95) cannot have symmetric distributions. The 2-sigma threshold implies a false-positive rate that only holds under normality.

### 19. Bidirectional anomaly flagging conflates improvements with degradations (Analysis 05)

The z-score uses absolute value, so sharp improvements and sharp drops are flagged equally. A route that improved after a schedule change is counted the same as one that collapsed.

### 20. Title says "Hotspot Map" but no spatial clustering is performed (Analysis 08)

Geographic analysis typically uses spatial statistical tests (e.g., Getis-Ord Gi*, kernel density). The analysis is a colored scatter plot, not a hotspot analysis.

### 21. Pearson r reported without significance tests (Analyses 07, 10, 11)

No p-values, confidence intervals, or outlier assessments accompany the correlation coefficients. With small sample sizes and likely non-normal distributions, statistical significance is not guaranteed.

### 22. Unweighted system average inconsistent with weighted stop OTP (Analysis 08)

The system average is computed as a simple mean of stop-level OTPs, while individual stop scores are trip-weighted. The benchmark is inconsistent with the methodology.

### 23. No minimum data span for seasonal amplitude ranking (Analysis 06)

A route with only 1 year of data has each calendar month represented by a single observation. Its "seasonal amplitude" is noise, but it is ranked alongside routes with 5+ years of data.

---

## Impact Assessment

How likely are these issues to materially change the conclusions each analysis draws?

### Probably wouldn't change the conclusions

**Analysis 01 (System Trend)** — The weighted vs. unweighted lines are both plotted, and the overall shape of the trend (COVID dip, recovery trajectory) is visible either way. The static weights affect the magnitude of the weighted line but probably not its direction. The conclusion is descriptive — "here's what happened" — and the chart tells a broadly correct story regardless.

**Analysis 05 (Anomaly Detection)** — The self-dampening window means some anomalies are missed (higher false-negative rate), but the ones that are flagged are still genuinely anomalous. The top-5 most-flagged routes are probably still anomalous, just maybe in a different order. The COVID attribution is hardcoded and obviously correct for those months.

**Analysis 08 (Hotspot Map)** — The map is descriptive. It effectively shows "which stops are served by bad routes," which is less useful than "which stops cause delays" but still geographically informative. The visual pattern of where poor-performing routes cluster is probably real.

**Analysis 09 (Incline Investigation)** — It's a data audit. The finding that the incline has no OTP data is a factual observation. The "data pipeline artifact" label is speculative but harmless.

### Would change numbers but probably not the direction

**Analysis 02 (Mode Comparison)** — Rail almost certainly outperforms bus regardless of weighting. The unweighted averaging overstates uncertainty in RAIL/INCLINE, but the directional claim (rail > bus) is robust. The paired-route analysis (51 vs 51L) is more vulnerable — the difference could shrink or grow with better controls — but the sign is probably stable.

**Analysis 04 (Neighborhood Equity)** — There genuinely are neighborhoods with worse OTP. The specific rankings would shift (and the quintile gap magnitude would change), but the existence of geographic disparity is almost certainly real. The look-ahead bias in quintile assignment affects the time series shape but not the overall finding that a gap exists.

**Analysis 06 (Seasonal Patterns)** — Winter is probably worse than summer regardless of methodology. The missing detrending could shift which month is "best" or "worst" by a month or two, and the route-level amplitude rankings are unreliable for short-history routes, but the broad seasonal pattern is likely robust.

### Could genuinely change the conclusions

**Analysis 03 (Route Ranking)** — The most vulnerable analysis. The "improving vs. declining" rankings are almost certainly dominated by COVID recovery rates, not current trajectories. A route that cratered in 2020 and recovered by 2022 shows a negative slope because the single line is pulled down by the dip. A post-COVID-only analysis could produce a substantially different ranking of which routes are improving or declining. The "best/worst average OTP" ranking is also diluted by including years that may not reflect current operations.

**Analyses 10 and 11 (Frequency vs OTP, Directional Asymmetry)** — Both produce a single Pearson r as their headline finding, and both use metrics confounded with route length. In Analysis 10, the "frequency" metric is really stop-visits, so the correlation could be capturing "longer routes have worse OTP" rather than anything about frequency. Fix the metric, and r could shrink to near-zero or change sign. In Analysis 11, routes with different IB/OB stop counts show phantom asymmetry — the correlation between "asymmetry" and OTP may be entirely artifactual.

**Analysis 07 (Stop Count vs OTP)** — The pooled Pearson r across all modes is a textbook Simpson's paradox setup. Rail has few stops and high OTP; bus has many stops and lower OTP. That between-mode difference could drive the entire correlation. Within bus routes alone, the relationship might be flat. Fixing the methodology could plausibly eliminate the finding.

### Summary

Of the 11 analyses, four (03, 07, 10, 11) have methodology issues that could genuinely change their conclusions. The common thread is that these are the analyses making specific quantitative claims (correlation coefficients, slope rankings) where the methodology issues directly contaminate the number being reported. The more descriptive analyses (01, 08) and those making broad directional claims (02, 06) are likely telling roughly the right story even if the details shift.

---

## Recommendations

### Fixable with existing data

**Analysis 03: Restrict slope to post-COVID period.** Filter to 2022-01 onward before fitting the linear slope. Report both an all-time average and a trailing-12-month average for rankings. Fix the ddof inconsistency in the variance calculation. Express slope in interpretable units (OTP change per year).

**Analysis 05: Lag the rolling window by one month.** Shift the rolling mean/std calculation by 1 period so the current observation is excluded from its own baseline.

**Analyses 07, 10, 11: Stratify correlations by mode.** Compute and report correlations for bus routes only. Rail and incline have too few observations to correlate meaningfully. Add Spearman rank correlation and p-values via scipy.

**Analysis 10: Use MAX(trips_wd) as frequency metric.** Instead of SUM (which confounds with route length), MAX captures the core-segment frequency — the number of trips at the route's most-served stop.

**Analysis 11: Use MAX(trips_wd) per direction, exclude one-direction routes.** MAX avoids phantom asymmetry from unequal stop counts. Routes with only one direction (likely loops) should be excluded from the correlation. Include IB,OB stops in both directions rather than dropping them.

**Analysis 06: Implement detrending and add min-years filter.** Compute a 12-month centered rolling mean as the trend, subtract it, then average residuals by month-of-year. Require 3+ years of data for route-level amplitude rankings.

**Analysis 04: Use rolling quintile assignment.** Assign quintiles based on trailing-12-month OTP at each time step instead of using overall mean (which introduces look-ahead bias).

**Analysis 02: Add route-count annotations.** Label each mode's chart legend with the number of routes (n) to make the sample-size imbalance explicit.

### Requires additional data

**Historical GTFS schedules** — Would fix the static-weights problem (issues 1, 2) across analyses 01, 04, and 06 by providing month-by-month trip counts. PRT likely publishes GTFS feeds; historical archives may be available from transitfeeds.com or the Mobility Database.

**Stop-level OTP (AVL arrival times)** — Would fix the ecological fallacy (issue 6) in analyses 04 and 08 by providing genuine stop-level performance data. Requires PRT's internal automatic vehicle location data.

**Route length in miles** — Would let Analysis 07 control for route length as a confounder. Calculable approximately from stop lat/lon coordinates, or precisely from GTFS route shapefiles.

**Ridership data** — Would improve weighting by reflecting actual passenger impact rather than scheduled service. PRT publishes ridership reports, though stop-level data would be ideal.

**External event calendar** — Would improve Analysis 05 by enabling systematic anomaly attribution beyond the four hardcoded COVID months. PRT service alerts (via GTFS-RT archives) would be the most natural source.

---

## Cross-Cutting Theme

The single biggest structural issue is that **OTP data exists at the route-month level, but many analyses project it onto finer-grained entities (stops, neighborhoods, directions) by joining with `route_stops`**. Since the OTP value is the same for all stops on a route in a given month, these joins create an illusion of granularity that does not exist in the underlying measurement. This affects analyses 01, 04, 06, 08, 10, and 11.
