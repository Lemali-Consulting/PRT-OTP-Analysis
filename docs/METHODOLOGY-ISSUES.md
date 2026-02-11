# Methodology Issues

A review of all 18 analyses for methodological flaws. Data quality issues are out of scope — this focuses on how each analysis is designed, calculated, or interpreted.

> Analyses 01–11 were reviewed in an initial pass. Analyses 12–18 were reviewed in a second red-team pass (2026-02-10). All significant and moderate issues in 12–18 have been resolved in code; see [RED-TEAM-REPORTS/2026-02-10-analyses-12-18.md](../RED-TEAM-REPORTS/2026-02-10-analyses-12-18.md) for the full report.

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

## Cross-Cutting Theme (Analyses 01–11)

The single biggest structural issue is that **OTP data exists at the route-month level, but many analyses project it onto finer-grained entities (stops, neighborhoods, directions) by joining with `route_stops`**. Since the OTP value is the same for all stops on a route in a given month, these joins create an illusion of granularity that does not exist in the underlying measurement. This affects analyses 01, 04, 06, 08, 10, and 11.

---

# Analyses 12–18: Methodology Review

Reviewed 2026-02-10. All significant and moderate issues below have been **resolved** in code unless marked *(inherent — documented only)*.

---

## Significant Issues

### 24. Simpson's paradox from pooling modes in headline correlation (Analysis 12)

The original headline correlation (r = -0.32) pooled BUS, RAIL, and INCLINE. Rail has few stops and long geographic spans with dedicated right-of-way, pulling the pooled correlation toward zero. **Fix:** Bus-only Pearson and Spearman are now the primary metrics (r = -0.38, rho = -0.37); all-mode is reported as secondary.

### 25. System-wide trend not removed before computing cross-route correlations (Analysis 13)

Without detrending, all routes correlate positively (they all dropped during COVID and partially recovered). Clustering was dominated by the COVID response signal, not by genuine differential behavior. **Fix:** System-wide monthly mean OTP is subtracted from each route before computing pairwise correlations. Clusters now reflect route-specific deviations.

### 26. Imputing 0.0 for insufficient-overlap route pairs creates spurious cluster structure (Analysis 13)

Route pairs with too few overlapping months were assigned correlation = 0.0, which is an implicit claim of independence. In a distance matrix, this places them at the median distance, artificially tightening clusters. **Fix:** Insufficient-overlap pairs are now imputed with the median observed correlation rather than 0.0. The number of imputed pairs is reported.

### 27. Regression to the mean untested in COVID recovery analysis (Analysis 14)

Routes with extreme baseline OTP (very high or very low) are statistically likely to move toward the mean in any subsequent period. Without testing for this, the "improved vs. declined" narrative could be a statistical artifact. **Fix:** Added Pearson correlation between baseline OTP and recovery delta. Result: r = -0.25, p = 0.02 — significant RTM effect. FINDINGS.md updated to caveat that extreme movers are partially explained by regression.

### 28. No statistical test for subtype recovery differences (Analysis 14)

The original analysis listed premium vs. local routes qualitatively without testing whether the difference was significant. **Fix:** Added Kruskal-Wallis test across subtypes. Result: H = 5.5, p = 0.24 — not significant. The "premium routes recovered better" claim does not survive statistical testing.

### 29. Inflated sample size in transfer hub correlation (Analysis 16)

The stop-level correlation (n = 6,209) treats each stop as independent, but stops on the same route share the same OTP value. The effective sample size is ~90 (number of routes), not 6,209. This inflates statistical significance by ~70x. **Fix:** Added route-level aggregation (mean stop connectivity per route vs. route OTP) as the primary metric. Result: r = -0.15, p = 0.16 — not significant. The "hub penalty" finding was retracted.

### 30. Ecological fallacy in stop-level OTP for hub and municipal analyses (Analyses 15, 16)

Route-level OTP projected onto stops creates spurious granularity. A route's OTP is not uniform across its stops — performance may vary by segment, time of day, or direction. Municipalities and hubs inherit the route's aggregate number. *(Inherent — documented only.)*

### 31. Static trip weights in municipal equity analysis (Analysis 15)

Same issue as #2 above: the `route_stops` table is a single snapshot, but it's used to weight OTP across a multi-year period. *(Inherent — documented only.)*

### 32. Multicollinearity in multivariate model with no VIF check (Analysis 18)

Stop count, geographic span, and number of municipalities served are correlated with each other. Without checking Variance Inflation Factors, coefficient estimates may be unstable and standard errors inflated. **Fix:** Added VIF computation for all predictors. Results: all VIF < 3 (moderate collinearity). Additionally, a reduced model (without n_munis) is now reported to show coefficient stability.

### 33. n_munis acts as a suppressor variable with misleading coefficient (Analysis 18)

Number of municipalities has a positive coefficient (+0.41 beta), which seems to say "routes crossing more jurisdictions have better OTP." This is a suppressor: n_munis is correlated with stop count and span (negative OTP predictors), and its positive sign reflects its role in controlling for those variables, not a genuine positive effect. **Fix:** Reduced model (without n_munis) reported alongside full model. FINDINGS.md labels n_munis as a suppressor. Full model R² = 0.47, reduced R² = 0.40.

---

## Moderate Issues

### 34. Ward's method assumes Euclidean distance; correlation distance is not Euclidean (Analysis 13)

Ward's linkage minimizes within-cluster variance, which requires Euclidean distance. The distance matrix (1 - r) is a correlation distance, which does not satisfy the Euclidean assumption. **Fix:** Switched to average linkage, which is valid for arbitrary distance matrices.

### 35. Hardcoded k=6 clusters without empirical justification (Analysis 13)

The original code hardcoded 6 clusters. **Fix:** Added silhouette score optimization over k = 3–10. The optimal k happened to be 6 (silhouette = 0.178), but this is now empirically justified rather than arbitrary.

### 36. No minimum-month filter on average OTP (Analysis 12)

Routes with very few months of data could have unreliable average OTP. **Fix:** Added `HAVING COUNT(*) >= 12` to the OTP query, consistent with Analysis 03's minimum data requirement.

### 37. METHODS.md promises Spearman but code only computes Pearson (Analysis 12)

The methods document described both Pearson and Spearman correlations, but the code only computed Pearson. **Fix:** Added Spearman rank correlation (rho = -0.37, p < 0.001 bus-only).

### 38. Default equal-variance t-test for unequal group sizes (Analysis 15)

`scipy.stats.ttest_ind` defaults to `equal_var=True` (Student's t-test). The cross-jurisdictional vs. single-municipality groups have different sizes and potentially different variances. **Fix:** Changed to `equal_var=False` (Welch's t-test). Result: p = 0.86 (unchanged direction).

### 39. Pooled-mode correlation in weekend/weekday analysis (Analysis 17)

The weekend-ratio vs. OTP correlation pooled all modes. **Fix:** Added bus-only correlation. Result: r = -0.06, p = 0.56 — still null, confirming the finding is robust.

### 40. Floating current-period window in COVID recovery (Analysis 14)

The "current" period was defined as the trailing 12 months of available data, but the specific months were not printed, making the analysis harder to reproduce. **Fix:** Current period start and end months are now printed in the analysis output.

### 41. is_rail estimated from ~3 observations (Analysis 18)

The rail mode dummy variable is based on only ~3 rail routes. The coefficient (+0.34 beta, p < 0.001) is significant but estimated from very few data points. *(Documented — no fix possible with existing data.)*

### 42. Monthly OTP conflates weekday and weekend performance (Analysis 17)

The OTP data is monthly aggregates that include both weekday and weekend trips. Correlating a weekend service *schedule* ratio with *monthly* OTP that already includes weekend performance creates a circular element. *(Inherent limitation of the data — documented in FINDINGS.md caveats.)*

---

## Minor Issues

### 43. Max pairwise distance is a noisy proxy for route length (Analysis 12)

Geographic span (Haversine distance between the two farthest stops) is an approximation. A route with a U-shaped path has smaller span than route length. GTFS route shapefiles would give exact length. *(No fix without additional data.)*

### 44. Modes pooled in clustering without stratification (Analysis 13)

All modes (BUS, RAIL) are clustered together. With only ~3 rail routes, mode-specific clustering is not feasible, but rail routes may cluster together simply because of mode rather than genuine co-movement. *(Documented — too few rail routes to stratify.)*

### 45. Numerical instability from matrix inversion in OLS (Analysis 18)

The original code used `np.linalg.inv(X'X)` which can be numerically unstable for near-singular matrices. **Fix:** Switched to `np.linalg.lstsq` for coefficient estimation and `np.linalg.pinv` for the variance-covariance matrix.

---

## Impact Assessment (Analyses 12–18)

### Findings that changed materially after fixes

**Analysis 13 (Correlation Clustering)** — Detrending and linkage fixes changed the cluster composition entirely. The old clusters were artifacts of differential COVID response; the new clusters reflect genuine route-specific co-movement (though silhouette scores remain low at 0.178).

**Analysis 14 (COVID Recovery)** — The headline narrative changed from "premium routes recovered, local routes declined" to "regression to the mean explains a significant portion of the divergence (r = -0.25, p = 0.02), and there is no statistically significant difference between subtypes (p = 0.24)." The policy-relevant finding narrowed to specific eastern-corridor local bus routes.

**Analysis 16 (Transfer Hub Performance)** — The finding was effectively retracted. The stop-level "hub penalty" (r = -0.17, p < 0.001) does not survive correction for non-independent observations. At the route level, the correlation is not significant (r = -0.15, p = 0.16).

### Findings that changed in magnitude but not direction

**Analysis 12 (Geographic Span)** — Bus-only correlation (r = -0.38) is stronger than the original pooled result (r = -0.32). The direction and interpretation are the same, but the Simpson's paradox fix actually strengthened the finding. Partial correlations confirmed stop count has roughly twice the effect of span.

**Analysis 18 (Multivariate Model)** — VIF check confirmed manageable collinearity (all < 3). The reduced model (R² = 0.40) shows the full model's R² = 0.47 is partially inflated by the n_munis suppressor. The bus-only model (R² = 0.38) confirms the findings generalize within the dominant mode. No coefficient changed sign.

### Findings that did not change

**Analysis 15 (Municipal Equity)** — Welch's t-test produced p = 0.86 vs. the original Student's p ≈ 0.85. No material change.

**Analysis 17 (Weekend/Weekday Profile)** — Bus-only correlation (r = -0.06, p = 0.56) confirms the all-mode null result (r = -0.03, p = 0.79). The finding remains: weekend service ratio does not predict OTP.

---

## Cross-Cutting Theme (Analyses 12–18)

The most pervasive issue across analyses 12–18 is **failure to account for non-independence and pooled-mode confounding**. Five of the seven analyses (12, 13, 16, 17, 18) required mode stratification or unit-of-analysis corrections. The lesson: whenever the headline metric is a correlation, always report the bus-only version as primary (given that ~97% of routes are bus) and flag the effective sample size.
