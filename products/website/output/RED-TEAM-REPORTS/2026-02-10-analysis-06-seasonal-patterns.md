# Red Team Report: Analysis 06 -- Seasonal Patterns

**Date:** 2026-02-10
**Analysis:** 06_seasonal_patterns
**Trigger:** Counterintuitive finding that winter months outperform summer/fall

## Methodological Issues Identified

### 1. Route Composition Bias (Moderate Severity)

**Problem:** The system-wide seasonal profile included all routes present in each month, but route composition varied by month-of-year. Four routes appeared only in winter months (Dec--Feb) and never in summer:

| Route | Name | Avg OTP | Months Present |
|-------|------|---------|----------------|
| 37 | Castle Shannon | 81.4% | Jan, Feb, Mar |
| 42 | Potomac | 83.1% | Jan, Feb, Mar |
| 53 | Homestead Park | 71.6% | Jan, Feb |
| RLSH | Red Line Shuttle | 97.5% | Jan, Feb, Mar |

No routes appeared only in summer but not winter. These high-OTP winter-only routes inflated winter averages. January had 98 routes reporting while June--August had only 94.

**Fix:** Restricted the system-wide profile to a **balanced panel** of 93 routes present in all 12 months-of-year. This ensures route composition is constant across months.

### 2. Unbalanced Year Coverage (Moderate Severity)

**Problem:** Data spans 2019-01 through 2025-11. December was missing 2025 -- the worst-performing year in the dataset (system average 66.8%). Every other month included 7 years of data; December had only 6. This shielded December from the 2025 decline, inflating its seasonal average.

**Fix:** Restricted analysis to **complete calendar years only** (2019-01 through 2024-12), ensuring every month-of-year has exactly 6 years of data.

### 3. Static Trip Weighting (Low-Moderate Severity)

**Problem:** `route_stops.trips_7d` is a single snapshot of weekly trip counts applied uniformly to all 6+ years of historical data. Route frequencies changed substantially over this period (COVID reductions, service restructuring). Five routes in the OTP data had zero trip weight and fell back to unweighted averaging.

**Fix:** No code change (no historical trip data available). Added documentation noting this limitation. Verified the seasonal pattern holds in both weighted and unweighted averages, confirming the finding is robust to weighting choice.

### 4. Rolling Mean Boundary Effects (Low Severity)

**Problem:** The 12-month rolling mean with `min_samples=6` and `shift(-6)` produces null/noisy trend estimates at series boundaries. The last ~6 months are dropped (null trend), systematically excluding recent low-OTP months.

**Fix:** The complete-years restriction (ending at 2024-12) partially mitigates this by ensuring the boundaries are at year edges rather than mid-year.

## Impact on Findings

| Metric | Before | After | Change |
|--------|--------|-------|--------|
| Best month | January (70.3%) | January (70.8%) | +0.5 pp |
| Worst month | September (64.0%) | September (64.4%) | +0.4 pp |
| Seasonal swing | ~6 pp | 6.8 pp | +0.8 pp |
| Routes in system profile | 98 (variable) | 93 (balanced) | Composition fixed |
| Top seasonal route | O5 (15.4%) | 15 - Charles (15.8%) | Ranking shifted |
| #2 seasonal route | P2 (14.8%) | O5 (15.2%) | |
| #3 seasonal route | 58 (13.9%) | P2 (14.8%) | |

## Verdict

The core finding -- **winter months outperform summer/fall** -- is **confirmed as genuine**. The pattern persists after correcting for route composition bias and unbalanced year coverage. The magnitude of the seasonal swing is similar (~6.8 pp vs ~6 pp). The route-level ranking shifted (route 15 Charles moved to #1), but the overall pattern is consistent.

The original analysis was directionally correct but had methodological weaknesses that could have been exploited to question the finding. The corrections strengthen the credibility of the seasonal pattern.
