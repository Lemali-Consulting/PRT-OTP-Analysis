# Understanding Paired T-Tests

A paired t-test compares two measurements taken on the **same** subjects. The key mechanic: it reduces everything to a single column of differences, then tests whether those differences are systematically different from zero.

## How it works

Say you want to know whether ridership-weighted OTP is different from trip-weighted OTP (Analysis 19). Both are computed for the same set of routes:

| Route | Trip-Weighted OTP | Ridership-Weighted OTP | Difference |
|-------|-------------------|------------------------|------------|
| 61A   | 72%               | 68%                    | −4%        |
| 71B   | 81%               | 79%                    | −2%        |
| P1    | 90%               | 88%                    | −2%        |
| 28X   | 75%               | 70%                    | −5%        |

**Step 1**: Compute the difference for each route. Now you have a single column of numbers.

**Step 2**: Ask "Is the average of these differences significantly different from zero?" This is just a one-sample t-test on the difference column — mean difference divided by its standard error gives a t-statistic, which you look up on the t-distribution to get a p-value.

In Analysis 19: t = −18.1, p < 0.001. The differences are overwhelmingly negative.

## Why pairing matters

If you ignored the pairing and compared the two columns as independent groups, you'd be swamped by variation *between* routes. Route 61A has 72% OTP while P1 has 90% — a huge gap that has nothing to do with the weighting method. By computing differences within each route, you cancel out all route-to-route variation and isolate just the weighting effect.

This is the same logic as a before/after study. To test whether a medication lowers blood pressure, you don't compare treated patients against untreated patients (too much person-to-person variation). You measure the *same* patients before and after, compute each person's change, and test whether the average change is zero.

## When to use a paired t-test

- You have two measurements on the **same** subjects (same routes, same stops, same time periods).
- You want to test whether there's a systematic difference between the two measurements.
- The differences are roughly normally distributed (or you have a large enough sample for the central limit theorem to apply).

If the normality assumption is doubtful, use the **Wilcoxon signed-rank test** instead — the non-parametric equivalent. Analysis 19 runs both as a robustness check (Wilcoxon W = 1, p < 0.001, confirming the result).

## See also

- [P-Values](understanding_p_values.md) — how the p-value is computed from the t-statistic
- [Observational vs. Experimental Data](observational_vs_experimental_data.md) — pairing approximates experimental control
- [Glossary: Paired t-Test](../GLOSSARY.md#parametric-tests-assume-roughly-normal-distributions)
- [Glossary: Wilcoxon Signed-Rank Test](../GLOSSARY.md#non-parametric-tests-no-distribution-assumptions)
