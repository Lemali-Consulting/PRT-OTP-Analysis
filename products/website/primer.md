## Transit Metrics

### On-Time Performance (OTP)

The central measure in this project. A trip is "on time" if the bus arrives no more than 1 minute early or 5 minutes late relative to its scheduled time. OTP is the percentage of trips meeting this threshold.

$$\text{OTP} = \frac{\text{on-time trips}}{\text{total trips}} \times 100$$

**Range:** 0% to 100%. PRT's system-wide OTP typically falls between 60% and 80%.

**Three flavors of averaging:**

- **Unweighted OTP** — each route-month gets equal weight, regardless of how many trips it runs. Useful for comparing route-level performance on a level playing field.
- **Trip-weighted OTP** — weights each route-month by its number of trips. Routes with more scheduled service count more. This is the "system average" PRT would report.
- **Ridership-weighted OTP** — weights each route-month by its ridership. This answers: "What OTP does the typical *rider* experience?" A route carrying 10,000 riders matters more than one carrying 500.

**Why it matters:** Unweighted and ridership-weighted OTP can diverge substantially. If high-ridership routes perform worse than low-ridership ones, the average rider experiences worse service than the route-level average suggests.

### Average Weekday Ridership (AWR)

The average number of boardings on a typical weekday for a route or the system. Calculated from monthly ridership data divided by the number of weekdays in the month. AWR is the standard transit industry measure for comparing ridership across routes and time periods.

### Late Rider-Trips

The estimated number of riders affected by late buses in a given period:

$$\text{Late rider-trips} = \text{ridership} \times (1 - \text{OTP} / 100)$$

A route with 10,000 monthly riders and 70% OTP produces 3,000 late rider-trips. This metric combines service quality with ridership volume to identify where delays cause the most harm.

### Ridership Concentration

Measures how unevenly ridership is distributed across routes, using the Lorenz curve and a concentration index analogous to the Gini coefficient.

$$\text{Concentration Index} = \frac{\sum_{i=1}^{n}(2i - n - 1) \cdot x_i}{n \sum_{i=1}^{n} x_i}$$

where $x_i$ is ridership for route $i$ sorted in ascending order.

**Range:** 0 (all routes carry equal ridership) to 1 (all ridership on one route). PRT's concentration index is typically around 0.6–0.7, meaning a small number of routes carry the vast majority of riders.

### Service Structure Metrics

Several analyses examine the physical characteristics of routes:

- **Stop count** — total number of stops served by a route.
- **Geographic span** — straight-line distance (km) between a route's two most distant stops.
- **Stop density** — stops per kilometer of geographic span. High density means frequent stops; low density means an express-like pattern.
- **Directional asymmetry** — the difference in stop count or OTP between the inbound and outbound directions of a route. Large asymmetry can indicate one-way traffic patterns or route design issues.
- **Hub connectivity** — the number of major transfer hubs a route serves. Routes touching more hubs tend to have different performance profiles.

---

## Descriptive Statistics

### Summary Statistics

Most analyses begin by reporting basic distributional measures:

- **Mean** — the arithmetic average. Sensitive to outliers.
- **Median** — the middle value when sorted. More robust to extreme values.
- **Standard deviation (SD)** — measures spread around the mean. About 68% of values fall within 1 SD of the mean for normally distributed data.
- **Interquartile range (IQR)** — the range from the 25th to the 75th percentile. Contains the middle 50% of values and is robust to outliers.
- **Percentiles** — the value below which a given percentage of observations fall. The 10th percentile OTP tells you the performance level that only the worst 10% of routes fall below.

### Weighted Averages

When routes differ in size, a simple average can be misleading. Weighted averages account for this:

$$\bar{x}_w = \frac{\sum_{i} w_i \, x_i}{\sum_{i} w_i}$$

where $w_i$ is the weight (trips, riders, or population) for observation $i$.

**Trip-weighted** averages treat each scheduled trip equally — a route running 500 trips/month counts five times as much as one running 100. **Ridership-weighted** averages treat each rider equally — the experience of a route carrying 10,000 riders dominates one carrying 1,000.

### Year-over-Year Change

Many analyses track how a metric changes between years or periods. Reported as either:

- **Absolute change** ($\Delta$): new value minus old value. "OTP rose by 3.2 percentage points."
- **Percentage change**: $\frac{\text{new} - \text{old}}{\text{old}} \times 100$. "Ridership grew 15%."

Percentage-point changes and percentage changes are different. If OTP goes from 70% to 73%, that is a 3 percentage-point increase but a 4.3% increase.

---

## Correlation Methods

Correlation measures how two variables move together. All correlations in this project are computed at the route or system level — they describe relationships between *route-level averages*, not individual trips or riders.

### Pearson Correlation (r)

Measures the strength of a *linear* relationship between two continuous variables.

$$r = \frac{\sum (x_i - \bar{x})(y_i - \bar{y})}{\sqrt{\sum (x_i - \bar{x})^2 \sum (y_i - \bar{y})^2}}$$

**Range:** $-1$ to $+1$.

- $+1$ = perfect positive linear relationship.
- $-1$ = perfect negative linear relationship.
- $0$ = no linear relationship (but a nonlinear one might still exist).

**Sensitivity:** Pearson is sensitive to outliers. A single extreme value can inflate or deflate $r$ substantially.

### Spearman Rank Correlation

Like Pearson, but computed on the *ranks* of the data rather than the raw values. Captures any monotonic relationship (consistently increasing or decreasing), even if the relationship is curved.

**When to prefer it:** When the data are skewed, contain outliers, or the relationship is monotonic but not strictly linear. Many PRT analyses report both Pearson and Spearman as a robustness check.

### Partial Correlation

Measures the correlation between two variables *after removing the effect* of one or more confounders. For example, the partial correlation between stop count and OTP controlling for ridership asks: "Among routes with similar ridership, do those with more stops still have worse OTP?"

$$r_{xy \cdot z} = \frac{r_{xy} - r_{xz} \, r_{yz}}{\sqrt{(1 - r_{xz}^2)(1 - r_{yz}^2)}}$$

If the partial correlation is much smaller than the raw correlation, the apparent relationship was largely driven by the confounder.

---

## Hypothesis Tests

Hypothesis tests assess whether an observed pattern is likely due to chance. The **p-value** is the probability of seeing a result at least as extreme as the observed one if there were truly no effect. A small p-value (conventionally $p < 0.05$) suggests the pattern is unlikely to be due to chance alone.

### Mann-Whitney U Test

A nonparametric test for whether two independent groups differ in their distributions. Used when comparing, say, bus routes serving low-income neighborhoods vs. those serving high-income ones.

**Why nonparametric?** It does not assume the data are normally distributed — only that observations can be ranked. This makes it appropriate for skewed OTP or ridership data.

Effect size is reported as rank-biserial $r$:

$$r = 1 - \frac{2U}{n_1 n_2}$$

where $U$ is the test statistic and $n_1$, $n_2$ are the group sizes. Ranges from $-1$ to $+1$; values near $0$ indicate no difference.

### Paired t-test

Tests whether the mean difference between paired observations is zero. Used when the same routes are measured at two time points (e.g., OTP before vs. after a service change).

$$t = \frac{\bar{d}}{s_d / \sqrt{n}}$$

where $\bar{d}$ is the mean of the paired differences, $s_d$ is their standard deviation, and $n$ is the number of pairs.

### Kruskal-Wallis Test

The nonparametric equivalent of one-way ANOVA. Tests whether three or more groups have the same distribution. Used, for example, to compare OTP across multiple garages or seasonal categories.

If significant, it tells you the groups differ *somewhere*, but not which specific pairs differ — follow-up pairwise tests (e.g., Dunn's test) are needed.

### Wilcoxon Signed-Rank Test

A nonparametric paired test — the nonparametric counterpart to the paired t-test. Tests whether the median difference between paired observations is zero. More robust than the paired t-test when differences are skewed.

### Bonferroni Correction

When running multiple hypothesis tests simultaneously, the chance of at least one false positive grows. The Bonferroni correction divides the significance threshold by the number of tests:

$$\alpha_{\text{adjusted}} = \frac{\alpha}{m}$$

where $m$ is the number of tests. If testing 10 comparisons at $\alpha = 0.05$, each individual test must reach $p < 0.005$ to be considered significant.

**Trade-off:** Bonferroni is conservative — it reduces false positives but increases the chance of missing real effects (false negatives). It is most appropriate when the number of tests is modest (under ~20).

---

## Regression Methods

### OLS Regression

Ordinary least squares regression fits a linear model predicting an outcome from one or more predictors by minimizing the sum of squared residuals.

$$y = \beta_0 + \beta_1 x_1 + \beta_2 x_2 + \cdots + \epsilon$$

Key statistics reported:

- **$R^2$** — the proportion of variance in the outcome explained by the model. Ranges from 0 to 1. An $R^2$ of 0.45 means the predictors explain 45% of the variation.
- **Adjusted $R^2$** — penalizes $R^2$ for the number of predictors. Prevents overfit models from looking artificially good.
- **Standardized coefficients ($\beta$)** — express each predictor's effect in standard deviation units, making it possible to compare the relative importance of predictors measured on different scales. A standardized $\beta$ of 0.3 means a 1 SD increase in the predictor is associated with a 0.3 SD increase in the outcome.

### Nested F-Tests

Used to compare two regression models where one is a subset of the other (e.g., Model 1 has predictors A and B; Model 2 adds C and D). The F-test asks: "Does adding the extra predictors significantly improve the fit?"

$$F = \frac{(R^2_{\text{full}} - R^2_{\text{reduced}}) / k}{(1 - R^2_{\text{full}}) / (n - p - 1)}$$

where $k$ is the number of added predictors, $n$ is the sample size, and $p$ is the total number of predictors in the full model.

A significant F-test means the additional predictors contribute meaningfully beyond what was already in the model.

### Variance Inflation Factor (VIF)

Measures how much a predictor's variance is inflated by correlation with other predictors (multicollinearity).

$$\text{VIF}_j = \frac{1}{1 - R_j^2}$$

where $R_j^2$ is the $R^2$ from regressing predictor $j$ on all other predictors.

**Interpretation:**
- VIF = 1: no multicollinearity.
- VIF = 5: the predictor's standard error is $\sqrt{5} \approx 2.2$ times larger than it would be without multicollinearity.
- VIF > 10: severe multicollinearity — coefficient estimates become unstable.

When VIF is high, predictors are too correlated to disentangle their individual effects. Analyses address this by dropping redundant predictors or combining them.

---

## Time Series Methods

### Seasonal Decomposition

Breaks a time series into three components:

$$Y_t = T_t + S_t + R_t$$

- **Trend ($T_t$)** — the long-run direction (improving or declining OTP).
- **Seasonality ($S_t$)** — repeating patterns within each year (e.g., winter dips in OTP).
- **Residual ($R_t$)** — what is left after removing trend and seasonality. Large residuals point to unusual events (service changes, weather, COVID).

PRT analyses use additive decomposition with a 12-month period, appropriate when seasonal fluctuations are roughly constant in magnitude over time.

### Augmented Dickey-Fuller (ADF) Test

Tests whether a time series is **stationary** — meaning its statistical properties (mean, variance) do not change over time.

- **Null hypothesis:** the series has a unit root (is non-stationary — it wanders without reverting to a mean).
- **Rejection** ($p < 0.05$): the series is stationary.

**Why it matters:** Many time series methods (including Granger causality) require stationary data. If a series is non-stationary, it must be differenced (subtracting each value from the previous one) before analysis.

### Granger Causality

Tests whether past values of series $X$ help predict future values of series $Y$, beyond what $Y$'s own past values predict. If so, $X$ is said to "Granger-cause" $Y$.

**Important caveats:**
- Granger causality is about *predictive precedence*, not true causation. If ridership changes Granger-cause OTP changes, it means ridership shifts tend to precede OTP shifts — not necessarily that one causes the other.
- Both series must be stationary (see ADF test above).
- Results depend on the number of lags tested.

### Lagged Cross-Correlation

Measures the correlation between series $X$ at time $t$ and series $Y$ at time $t + k$, for various lags $k$. This reveals whether changes in one series precede changes in the other, and by how many months.

A peak at lag $k = -2$ means $X$ leads $Y$ by 2 months. A peak at $k = 0$ means the two series move in sync.

---

## Clustering

### Hierarchical Clustering (Ward's Method)

Groups routes (or other units) into clusters based on similarity, building a tree (dendrogram) from the bottom up:

1. Start with each route as its own cluster.
2. At each step, merge the two clusters whose combination increases within-cluster variance the least (Ward's criterion).
3. Continue until all routes are in one cluster.

The dendrogram is then "cut" at a chosen height to produce a specific number of clusters.

**Why Ward's method?** It tends to produce compact, similarly-sized clusters and works well with the Euclidean-like distances used in PRT analyses.

### Silhouette Score

Measures how well each observation fits its assigned cluster versus the nearest neighboring cluster.

$$s(i) = \frac{b(i) - a(i)}{\max(a(i),\, b(i))}$$

where $a(i)$ is the average distance from point $i$ to other points in its cluster, and $b(i)$ is the average distance to points in the nearest other cluster.

**Range:** $-1$ to $+1$.
- Near $+1$: well-clustered — the point is much closer to its own cluster than to others.
- Near $0$: borderline — the point sits between two clusters.
- Negative: misclassified — the point is closer to another cluster.

The average silhouette score across all points summarizes overall clustering quality.

### Correlation-Based Distance

Instead of using geographic or Euclidean distance, some analyses define route similarity based on how similarly their OTP time series behave:

$$d(i, j) = 1 - |r_{ij}|$$

where $r_{ij}$ is the Pearson correlation between routes $i$ and $j$ over time. Routes with highly correlated OTP patterns (rising and falling together) are considered "close," even if they serve different parts of the city.

---

## Key Concepts

### Detrending

Many PRT analyses need to distinguish route-specific behavior from system-wide shocks (weather, COVID, service changes) that affect all routes simultaneously.

**Approach:** Subtract the system-wide monthly average from each route's value:

$$\text{detrended}_{i,t} = x_{i,t} - \bar{x}_t$$

A positive detrended value means the route performed better than the system average that month; a negative value means it performed worse. This removes shared variation and isolates route-specific patterns.

### COVID Recovery Metrics

Several analyses quantify how routes recovered from the pandemic ridership collapse:

- **Recovery delta** — the absolute difference between a route's post-COVID metric and its pre-COVID baseline.
- **Recovery ratio** — post-COVID value divided by pre-COVID value. A ratio of 0.85 means the route has recovered to 85% of its pre-pandemic level.

Pre-COVID baselines are typically defined as the 12 months before March 2020. Post-COVID periods vary by analysis but generally begin in mid-2021 or later.

### Lorenz Curve and Concentration Index

The Lorenz curve visualizes inequality in a distribution. For ridership concentration:

1. Sort routes from lowest to highest ridership.
2. Plot the cumulative share of routes (x-axis) against the cumulative share of total ridership (y-axis).

If ridership were perfectly equal, the curve would be a 45-degree line. The more it bows away from that line, the more concentrated ridership is.

The **concentration index** (analogous to the Gini coefficient) is twice the area between the Lorenz curve and the 45-degree line. It summarizes the curve as a single number from 0 (perfect equality) to 1 (maximum concentration).
