# Statistical Methods Glossary

A plain-English reference for every statistical method, test, and concept used across the 35 analyses in this project. Organized from simplest to most advanced.

---

## 1. Descriptive Statistics

These are the building blocks — ways to summarize a set of numbers with a single value.

### Mean (Average)

Add up all the values and divide by how many there are. Used in every analysis as the default summary. The catch: means are sensitive to outliers. One route with 20% OTP could drag down a system average even if most routes are at 80%+.

*Used in: all 35 analyses*

### Median

Sort all values and pick the middle one. Unlike the mean, the median ignores extreme outliers. When analyses report both mean and median, a big gap between them signals a skewed distribution (a few very high or very low values pulling the mean).

*Used in: 01, 02, 03, 04, 06, 07, 10–12, 14–35*

### Standard Deviation (SD)

Measures how spread out values are around the mean. A small SD means most values cluster tightly; a large SD means they're scattered. If the mean OTP is 70% with SD of 5%, most routes fall between 65–75%. With SD of 15%, the range is much wider.

*Used in: 03, 05, 06, 14, 18, 19, 22, 23, 29*

### Quantiles and Percentiles

Dividing data into equal-sized chunks. The 25th percentile (Q1) means 25% of values are below this point. The 75th (Q3) means 75% are below. The median is the 50th percentile. Quintiles split data into 5 groups (top 20%, next 20%, etc.).

*Used in: 04, 20, 25, 27, 29*

### Interquartile Range (IQR)

The gap between Q3 and Q1: `IQR = Q75 − Q25`. This captures the "middle 50%" of your data and is a robust measure of spread that ignores outliers. Used in box plots as the height of the box.

*Used in: 20, 25*

### Variance

Standard deviation squared. Rarely reported directly (SD is more intuitive) but used internally in calculations like VIF (see below).

*Used in: 18*

---

## 2. Weighted Statistics

### Trip-Weighted Mean

Instead of treating every route equally, this weights each route's OTP by how many trips it runs. A route running 200 trips/day counts 10× more than one running 20. This better reflects the *system's* performance since more passengers experience high-frequency routes.

Formula: `Σ(OTP × trips) / Σ(trips)`

*Used in: 01, 02, 04, 06, 08, 15, 16, 19, 22, 23*

### Ridership-Weighted Mean

Same idea, but weights by actual riders instead of scheduled trips. A route with 5,000 daily riders matters more than one with 500, even if they run similar trip counts. Analysis 19 found a statistically significant gap between trip-weighted and ridership-weighted OTP (paired t-test, p < 0.001).

*Used in: 01, 19, 22, 23*

---

## 3. Correlation Methods

Correlation measures whether two variables move together. All correlation values range from −1 to +1:
- **+1** = perfect positive relationship (as X goes up, Y goes up)
- **0** = no relationship
- **−1** = perfect negative relationship (as X goes up, Y goes down)

### Pearson Correlation (r)

Measures **linear** association — do the two variables move together in a straight line? This is the "standard" correlation most people think of. Sensitive to outliers and assumes the relationship is roughly linear.

Example from the project: stop count vs. OTP has Pearson r = −0.52, meaning routes with more stops tend to have lower OTP.

*Used in: 07, 10–17, 20, 21, 24–28, 30, 34*

### Spearman Rank Correlation (ρ)

Instead of using raw values, Spearman ranks both variables from lowest to highest and then computes correlation on the ranks. This detects **monotonic** relationships (consistently increasing or decreasing) even if the shape isn't a straight line. More robust to outliers than Pearson.

Often reported alongside Pearson as a sanity check — if Spearman and Pearson agree, the relationship is likely real and roughly linear. If Spearman is strong but Pearson is weak, the relationship exists but is curved.

*Used in: 07, 10–12, 14, 16, 17, 20–22, 24, 25, 27–30, 34*

### Partial Correlation

Measures the correlation between X and Y **after removing the influence of Z**. Example: does route geographic span still predict OTP after accounting for the number of stops? (Answer: yes, partial r = −0.30.)

*Used in: 12*

### Lagged Cross-Correlation

Checks whether changes in X at time *t* predict changes in Y at time *t + k* (k months later). Used to test whether OTP changes lead or follow ridership changes.

*Used in: 20*

### Correlation Matrix

A table showing the Pearson correlation between every pair of variables (or routes). Used as input to clustering — routes with similar OTP trajectories over time have high correlations and get grouped together.

*Used in: 13*

---

## 4. Regression

Regression fits a mathematical line (or surface) through data points to model how one variable predicts another.

### Simple OLS Linear Regression

OLS = "Ordinary Least Squares." Finds the straight line `y = slope × x + intercept` that minimizes the sum of squared distances between the line and the actual data points. Returns:
- **Slope**: how much Y changes per unit change in X
- **R-value / R²**: how much of the variation in Y is explained by X (0% to 100%)
- **p-value**: probability of seeing this result if there were truly no relationship (< 0.05 is conventionally "significant")

*Used in: 02, 03, 07, 10–12, 14, 21–31, 34*

### Multiple OLS Regression

Same idea, but with multiple predictors: `y = b₁x₁ + b₂x₂ + ... + intercept`. Lets you ask: "Which factors predict OTP, and how much does each one matter after controlling for the others?"

*Used in: 18, 23, 26, 27, 28*

### Standardized Coefficients (Beta Weights)

When predictors are on different scales (e.g., stop count ranges 10–80 while span ranges 2–40 km), raw coefficients aren't comparable. Standardizing converts everything to "units of standard deviation" so you can say "a 1-SD increase in stop count changes OTP by 0.3 SD" and compare directly across predictors.

*Used in: 18, 26, 27, 28*

### R-squared and Adjusted R-squared

**R²** = the fraction of variation in the outcome explained by the model (0 to 1). An R² of 0.40 means the model explains 40% of the variation.

**Adjusted R²** penalizes for adding more predictors. A raw R² can only go up when you add variables (even useless ones); adjusted R² can go *down* if the new variable doesn't help enough to justify the added complexity.

*Used in: 18, 23, 26, 27, 28*

### Nested Model F-Test

Compares a "base" model (fewer predictors) to a "full" model (more predictors). Asks: "Does adding these extra predictors significantly improve the model, or is the improvement just noise?" A significant F-test (p < 0.05) means the extra predictors earn their keep.

*Used in: 23, 26, 27, 28*

### Variance Inflation Factor (VIF)

Detects **multicollinearity** — when predictor variables are too correlated with each other. VIF > 5 or 10 is a warning sign. If two predictors are highly correlated (e.g., stop count and route length), the model can't tell their effects apart, and the coefficients become unreliable.

*Used in: 18, 26, 27, 28*

### Degrees of Freedom (df)

The number of independent pieces of information left after the model has "used up" some to estimate its parameters. Every parameter the model estimates — including the intercept — costs one degree of freedom. A model with 3 predictors actually estimates 4 parameters (3 slopes + 1 intercept), so with 50 data points: df = 50 − 4 = 46.

The intercept counts because even a model with zero predictors still estimates one thing: the overall average. That already consumes one piece of information from your data.

This is also why the standard deviation formula divides by `n − 1` rather than `n` — computing the mean first consumed one degree of freedom, so only `n − 1` independent pieces of information remain to estimate the spread.

Degrees of freedom appear in the denominator of the F-test and t-test formulas as a correction — they prevent models with many parameters from appearing artificially good by accounting for the information consumed by each parameter.

*Used in: all regression and hypothesis test analyses*

---

## 5. Hypothesis Tests

A hypothesis test asks: "Could this result have happened by chance?"

### P-Value

The probability of seeing a result as extreme as yours **if there were truly no effect** (the "null hypothesis"). The process: (1) assume no effect, (2) use a theoretical distribution (t, F, chi-squared, etc.) to determine what random chance would produce, (3) measure how far your result falls into the tail of that distribution. The p-value is the area in the tail beyond your result — the fraction of random outcomes that would be as extreme or more extreme.

Convention: p < 0.05 = "statistically significant" (less than 5% chance that noise alone explains the result). This threshold is a social convention, not a law of nature.

Common misinterpretations:
- P-value is **not** the probability that the null hypothesis is true. It's the probability of the *data* given the null — a subtle but important distinction.
- P < 0.05 does not mean the effect is large or practically important. With enough data, tiny effects produce tiny p-values. Always check the effect size alongside the p-value.
- P > 0.05 does not mean "no effect." It means you lack enough evidence to rule out chance — possibly due to a small sample (low statistical power).

*Used in: all hypothesis test and regression analyses*

### Parametric Tests (assume roughly normal distributions)

**Paired t-Test** — Compares two measurements on the *same* subjects. Example: is trip-weighted OTP different from ridership-weighted OTP for the same set of routes? Each route serves as its own control. *(Used in: 02, 19)*

**Independent Samples t-Test (Welch's)** — Compares means of two *different* groups. Example: do cross-jurisdictional routes have different OTP than single-municipality routes? Welch's version doesn't assume equal variances. *(Used in: 15)*

**One-Sample t-Test** — Tests whether a group's mean differs from a specific value (usually zero). Example: is the average OTP change after service restructuring significantly different from zero? *(Used in: 29)*

### ANOVA (Analysis of Variance)

Compares means across **three or more groups** in a single test. Instead of running separate t-tests for every pair (which inflates false positive risk), ANOVA asks: "Is the variation in OTP *between* groups larger than the variation *within* groups?" The ratio of between-group to within-group variation is an F-statistic — same concept as the nested model F-test. A large F means the groups genuinely differ, not just from random noise.

This project doesn't use ANOVA directly because it assumes normally distributed data within each group. Instead, it uses **Kruskal-Wallis** (below), which answers the same question without that assumption. *(Not used directly; see Kruskal-Wallis)*

### Non-Parametric Tests (no distribution assumptions)

These don't assume your data follows a bell curve. Safer for skewed data or small samples, but slightly less powerful when normality holds.

**Mann-Whitney U Test** — Non-parametric alternative to the independent t-test. Compares two groups by ranking all values together and checking whether one group's ranks are systematically higher. Example: do sheltered stops have higher ridership than unsheltered ones? *(Used in: 02, 32)*

**Kruskal-Wallis Test** — Non-parametric alternative to one-way ANOVA (see above). Compares three or more groups using ranks instead of raw values, so it doesn't assume normality. Asks the same question as ANOVA — "do these groups differ?" — but is safer for the skewed, messy distributions typical of transit data. Example: does OTP differ across garage assignments (Ross, Collier, East Liberty, West Mifflin)? *(Used in: 14, 21, 23, 29)*

**Wilcoxon Signed-Rank Test** — Non-parametric alternative to the paired t-test. Ranks the *differences* between paired measurements and tests whether they're symmetric around zero. *(Used in: 19)*

### Multiple Comparison Correction

**Bonferroni Correction** — When you run many tests at once (e.g., 93 routes × Granger test), some will be "significant" by pure chance. Bonferroni multiplies each p-value by the number of tests to compensate. Conservative but simple: `adjusted_p = p × n_tests`. *(Used in: 20)*

---

## 6. Time Series Methods

### Rolling Mean (Moving Average)

Averages the last *N* months to smooth out noise. A 12-month rolling mean removes seasonal patterns and reveals the underlying trend. "Centered" means the window spans 6 months before and after each point (better for decomposition but can't be used for forecasting).

*Used in: 01, 03, 04, 05, 06*

### Rolling Z-Score (Anomaly Detection)

`z = (value − rolling_mean) / rolling_SD`

Measures how many standard deviations the current value is from its recent average. |z| > 2 flags an anomaly (expected to catch ~4.5% of normal data as false positives). This is the project's primary anomaly detection method.

*Used in: 05*

### Seasonal Decomposition

Breaks a time series into three additive components:
1. **Trend** — long-run direction (from rolling mean)
2. **Seasonal** — repeating monthly pattern (average deviation by calendar month)
3. **Residual** — what's left (random noise or unusual events)

Amplitude = max seasonal value − min seasonal value, capturing how strong the seasonal swing is.

*Used in: 06*

### Detrending

Removes the system-wide trend so you can compare routes fairly. If system OTP rose 5% in 2023, detrending subtracts that 5% from every route, isolating route-specific behavior. Done by subtracting the system-wide monthly mean from each route's monthly value.

*Used in: 13, 20, 30*

### Granger Causality

Tests whether past values of X help predict future values of Y beyond what Y's own past predicts. **Important caveat**: Granger "causality" is really about predictive precedence, not true causation. In this project, it tested whether OTP changes predict ridership changes (result: no, after Bonferroni correction).

*Used in: 20*

---

## 7. Clustering

### Hierarchical Clustering (Average Linkage)

Groups items by iteratively merging the two closest clusters. "Average linkage" defines the distance between two clusters as the average distance between all pairs of members. Produces a tree (dendrogram) showing the nesting structure.

*Used in: 13*

### Dendrogram

A tree diagram showing how clusters merge. The height where two branches join indicates how different those clusters are. "Cutting" the tree at a chosen height produces a specific number of groups.

*Used in: 13*

### Silhouette Score

Measures how well each item fits its assigned cluster. Ranges from −1 to +1:
- **+1** = well-matched to its cluster, poorly matched to others
- **0** = on the boundary between clusters
- **−1** = probably in the wrong cluster

The average silhouette score across all items helps pick the best number of clusters.

*Used in: 13*

---

## 8. Inequality and Concentration Metrics

### Gini Coefficient

Measures inequality on a 0-to-1 scale. **0** = perfectly equal (every route carries the same ridership), **1** = perfectly unequal (one route carries everything). In this project, used to quantify how concentrated ridership is across routes and stops.

*Used in: 25, 34*

### Lorenz Curve

A visual companion to the Gini coefficient. Plots cumulative share of ridership (Y-axis) against cumulative share of routes sorted from smallest to largest (X-axis). The further the curve bows from the 45° line, the more unequal the distribution.

*Used in: 25, 34*

### Pareto (80/20) Analysis

Asks: "What fraction of routes carry 80% of riders?" If 20% of routes carry 80% of riders, that's a classic Pareto distribution. Used to identify the critical few routes that serve the most passengers.

*Used in: 34*

---

## 9. Geographic Methods

### Haversine Formula

Calculates the straight-line distance between two latitude/longitude points on Earth's surface, accounting for the planet's curvature. Returns distance in kilometers (or meters). Used throughout the project to measure route geographic span and classify stops into distance zones from downtown.

*Used in: 12, 18, 23, 26, 27, 31, 33*

### Geographic Span

The maximum haversine distance between any two stops on a route. A proxy for how "spread out" a route is. Longer spans tend to predict lower OTP because there's more opportunity for delay accumulation.

*Used in: 12, 18, 23, 26, 27, 31*

---

## 10. Data Transformations

### Log Transformation

Applying `log(x)` compresses right-skewed data (a few very large values) into a more symmetric shape. Used on ridership and traffic (AADT) data before regression. If a log-transformed predictor works better, it suggests the relationship is proportional rather than additive (e.g., doubling ridership matters more than adding 1,000 riders).

*Used in: 26, 27*

### Indexing to a Baseline

Sets a reference period to 100 and expresses all other periods as a percentage of that baseline. If Jan 2019 = 100 and June 2023 = 85, ridership dropped 15% from baseline. Useful for comparing trends across entities with very different absolute values.

*Used in: 21, 24, 33*

---

## 11. Important Concepts and Caveats

These aren't methods you run — they're conceptual pitfalls that the analyses flag as warnings.

### Simpson's Paradox

A trend that appears in aggregated data can reverse when you split by subgroups. Example: system-wide, more stops might correlate with *lower* OTP. But within bus-only routes, the relationship could flip. Always check subgroups before trusting aggregate results.

*Flagged in: 04, 07, 10, 11, 12, 15, 17*

### Regression to the Mean

Extreme values tend to move toward the average over time, even without any intervention. A route with unusually bad OTP one year will probably improve the next year simply because extreme luck doesn't persist. This makes it tricky to tell whether improvements are real or just natural bounce-back.

*Flagged in: 03, 14*

### Ecological Fallacy

Inferring individual-level conclusions from group-level data. Just because a *municipality* has low average OTP doesn't mean every *stop* there performs poorly. The analyses work at the route level, so stop-level or passenger-level conclusions require caution.

*Flagged in: 15, 16*

### Selection Effect / Survivorship Bias

Routes that received service changes may have been chosen *because* they were performing badly. Comparing their before/after OTP is biased because they weren't randomly selected — their "before" is artificially low.

*Flagged in: 29*

### Statistical Power

The ability to detect a real effect. With only 4 rail routes, even a large difference in OTP might not reach statistical significance simply because there aren't enough data points. Small samples → low power → null results that don't necessarily mean "no effect."

*Flagged in: 02, 05, 20*

### Multicollinearity

When predictor variables are correlated with each other (e.g., stop count and route length), regression can't reliably separate their individual effects. The total model fit (R²) may be fine, but individual coefficients become unstable. VIF is the formal diagnostic.

*Flagged in: 12, 18, 26, 27*

---

## Quick Reference: Which Analyses Use What

| Method | Analyses |
|---|---|
| Pearson correlation | 07, 10–17, 20, 21, 24–28, 30, 34 |
| Spearman correlation | 07, 10–12, 14, 16, 17, 20–22, 24, 25, 27–30, 34 |
| Simple OLS regression | 02, 03, 07, 10–12, 14, 21–31, 34 |
| Multiple OLS regression | 18, 23, 26, 27, 28 |
| Mann-Whitney U | 02, 32 |
| Kruskal-Wallis | 14, 21, 23, 29 |
| Paired t-test | 02, 19 |
| Wilcoxon signed-rank | 19 |
| Rolling z-score | 05 |
| Seasonal decomposition | 06 |
| Granger causality | 20 |
| Hierarchical clustering | 13 |
| Gini / Lorenz | 25, 34 |
| Haversine distance | 12, 18, 23, 26, 27, 31, 33 |
| VIF | 18, 26, 27, 28 |
| Nested F-test | 23, 26, 27, 28 |
| Bonferroni correction | 20 |
