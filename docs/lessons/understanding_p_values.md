# Understanding P-Values

A p-value answers: "If there were truly no effect, how likely is it that random chance alone would produce a result this extreme?"

## The four-step process

Every hypothesis test follows the same pattern, regardless of which specific test it is.

### Step 1 — Assume nothing is happening

This is the "null hypothesis." For a correlation: "these two variables are unrelated." For a regression slope: "the true slope is zero." For a group comparison: "the groups have the same mean."

### Step 2 — Determine what random chance would produce

Under the null hypothesis, statisticians have worked out **theoretical distributions** — known curves describing how the test statistic (t, F, U, etc.) would be distributed if you ran the experiment thousands of times with no real effect, just random noise.

These distributions aren't arbitrary. They're derived mathematically from assumptions about the data (usually normality and independence):

- **t-distribution**: Used for regression slopes and t-tests. Shaped like a bell curve but with fatter tails, especially with small samples. As sample size grows, it converges to a normal distribution. Degrees of freedom control how fat the tails are — fewer data points means more uncertainty, so the tails stay fatter.
- **F-distribution**: Used for the F-test. Always positive (it's a ratio of variances). Shaped like a right-skewed hump. Two degrees-of-freedom values control its shape (one for the numerator, one for the denominator).
- **Normal (z) distribution**: Used when samples are large enough. The classic bell curve.
- **Chi-squared, U, and other distributions**: Each test has its own reference distribution, but the logic is always the same.

### Step 3 — See where your actual result lands

If your t-statistic is 0.5, it's right in the fat middle of the t-distribution — a completely unremarkable result under the null hypothesis. If your t-statistic is 4.2, it's way out in the tail — very unlikely if nothing were really going on.

### Step 4 — The p-value is the area in the tail

The p-value is the fraction of the theoretical distribution that is as extreme or more extreme than what you observed. A t-statistic of 4.2 with 46 degrees of freedom has only about 0.01% of the distribution beyond it, so p ≈ 0.0001.

## Why p < 0.05 means "significant"

By convention, p < 0.05 means "there's less than a 5% chance that random noise alone would produce a result this extreme." The 5% threshold is a social convention, not a law of nature — some fields use stricter thresholds (particle physics uses p < 0.0000003).

## What it looks like in this project's code

Most analyses call library functions that handle the math internally:

```python
r, p = scipy.stats.pearsonr(x, y)       # correlation
t, p = scipy.stats.ttest_ind(a, b)       # two-group comparison
U, p = scipy.stats.mannwhitneyu(a, b)    # non-parametric comparison
```

The custom OLS functions in Analyses 18, 23, 26–28 show the manual version explicitly:

```python
t_stat = coefficient / standard_error
p_value = 2 * (1 - stats.t.cdf(abs(t_stat), df=n - k - 1))
```

That second line is literally "find the area in both tails of the t-distribution beyond my t-statistic." The `2 *` makes it two-tailed — checking for extreme values in either direction (unusually high or unusually low).

## Common misinterpretations

- **P-value is NOT the probability that the null hypothesis is true.** It's the probability of the *data* given the null, not the probability of the null given the data. Subtle but important distinction.
- **P < 0.05 does not mean the effect is large or practically important.** With enough data, tiny meaningless effects can produce small p-values. Always check the effect size (correlation, slope, difference) alongside the p-value.
- **P > 0.05 does not mean "no effect."** It means you don't have enough evidence to rule out chance — possibly because your sample is too small (low statistical power).

## See also

- [F-Test and Model Comparison](understanding_f_test_and_model_comparison.md) — how p-values are used in model comparison
- [Glossary: Degrees of Freedom](../GLOSSARY.md#degrees-of-freedom-df) — controls the shape of the reference distribution
- [Glossary: Bonferroni Correction](../GLOSSARY.md#bonferroni-correction) — adjusting p-values for multiple tests
