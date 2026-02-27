# Understanding the F-Test and Model Comparison

The nested F-test, adjusted R², and Granger causality all share a common pattern: build a simple model, build a more complex one, and ask whether the improvement is real or just noise. The F-test is the formal mechanism for answering that question.

## The core problem

Adding *any* variable to a model will soak up at least a little error by pure chance, even a column of random numbers. Raw model fit (R²) can only go up with more variables. So you need a way to ask: "Did the error shrink more than you'd expect from chance alone?"

## How the F-test works

The F-test compares the leftover error (residuals) of two nested models — one simple, one complex:

```
        (error removed by new variables) / (number of new variables added)
F  =  ────────────────────────────────────────────────────────────────────
                  (remaining error) / (remaining degrees of freedom)
```

- **Numerator**: how much error the new variables removed, divided by how many were added (their cost in degrees of freedom).
- **Denominator**: leftover error divided by remaining degrees of freedom.

Both sides are on the same "error per degree of freedom" scale, making the ratio a fair comparison. A large F means the new variables removed disproportionately more error than what's left in the residuals. You then look up the F value in a known distribution to get a p-value — the probability of seeing an F that large if the new variables were actually useless.

### Concrete example from the project

Analysis 23: a base model predicts OTP from stop count and span. A full model adds four garage assignment dummies. The F-test asks: did adding those four dummies reduce prediction error more than four random columns would have? If p < 0.05, yes — garage assignment genuinely matters beyond what route structure already explains.

## Degrees of freedom

Degrees of freedom (df) is the number of independent pieces of information left after the model has "used up" some to estimate its parameters.

With 50 routes and a model with 3 predictors plus an intercept, the model consumes 4 pieces of information to pin down its coefficients. That leaves df = 46 — the number of independent data points available to estimate the error.

**Simpler analogy**: if you know the mean of 5 numbers is 10 (total = 50), you can freely choose 4 of them, but the 5th is locked in. Estimating the mean "cost" one degree of freedom.

### Why degrees of freedom appear in the denominator

This is more than a heuristic — it's a mathematical correction for the fact that more parameters mechanically reduce error.

If you had 50 data points and 49 predictors, the model could perfectly memorize every point. Raw error would be zero, but the model would be worthless for prediction. Dividing by degrees of freedom (50 − 49 − 1 = 0) would blow up, correctly signaling "this model has no real evidence behind it."

With 3 predictors, you divide by 46, giving a fair per-data-point estimate of remaining error. The denominator asks: "How much error is left *per independent piece of information the model didn't consume*?"

## How adjusted R² relates

Adjusted R² encodes the same intuition as the F-test but as a continuous score rather than a yes/no test.

**R²** is the fraction of total variation the model explains. It can only go up when you add variables — even useless ones — because more variables always soak up noise.

**Adjusted R²** applies a penalty proportional to the number of predictors relative to sample size. It can go *down* if a new variable doesn't justify its presence:

- R² goes from 0.42 to 0.43 after adding a variable — looks like an improvement
- Adjusted R² goes from 0.40 to 0.39 — not worth the added complexity

### F-test vs. adjusted R²

| | F-test | Adjusted R² |
|---|---|---|
| Output | p-value (yes/no at a threshold) | Score (continuous) |
| Best for | Formal hypothesis testing: "Does this block of variables matter?" | Model selection: "Which of these candidate models fits best?" |
| Used in project | Analyses 23, 26, 27, 28 | Analyses 18, 23, 26, 27, 28 |

They're complementary. The F-test gives a definitive answer about a specific comparison. Adjusted R² gives a ranking across many possible models.

## Where this pattern appears in the project

- **Nested F-test** (Analyses 23, 26–28): Does adding garage dummies, log ridership, or log AADT improve the base model?
- **Granger causality** (Analysis 20): Does adding past OTP to a ridership-only autoregressive model improve predictions? (This is an F-test applied to time series.)
- **Adjusted R²** (Analyses 18, 23, 26–28): Reported alongside R² to penalize unnecessary complexity.

## See also

- [Granger Causality](understanding_granger_causality.md) — the time series application of this pattern
- [Glossary: Nested Model F-Test](../GLOSSARY.md#nested-model-f-test)
- [Glossary: R-squared and Adjusted R-squared](../GLOSSARY.md#r-squared-and-adjusted-r-squared)
