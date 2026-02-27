# Understanding VIF and Multicollinearity

Multicollinearity means predictor variables are correlated with each other. VIF (Variance Inflation Factor) is the diagnostic that detects it.

## The problem

When two predictors move in lockstep, a regression model can't figure out which one actually drives the outcome. It splits credit between them arbitrarily, producing coefficients that are unstable and hard to interpret.

## Non-transportation example

Imagine predicting revenue at a beach stand using both ice cream sales and cone sales as predictors. They carry almost the same information — when one goes up, so does the other. The model might say "ice cream has a huge positive effect and cones have a negative effect," or flip it entirely, depending on tiny random fluctuations. The total prediction (R²) is fine, but the individual coefficients are meaningless.

## How VIF works

For each predictor, VIF asks: "How well can I predict *this* predictor using all the other predictors?"

1. Regress predictor X on all other predictors.
2. Get the R² from that regression.
3. VIF = 1 / (1 − R²).

If the other predictors explain 90% of X's variation (R² = 0.90), then VIF = 10. This means X's coefficient standard error is √10 ≈ 3.2 times larger than it would be if X were completely independent of the other predictors.

## Interpretation thresholds

- **VIF = 1**: No collinearity. This predictor is independent of the others.
- **VIF 1–5**: Moderate, generally acceptable.
- **VIF 5–10**: Concerning. Coefficients are getting unreliable.
- **VIF > 10**: Serious problem. Individual coefficients shouldn't be trusted.

## What to do about high VIF

- **Drop one of the correlated predictors** — if stop count and span carry similar information, pick the one more relevant to your question.
- **Use partial correlation** — isolate each predictor's unique contribution (see [partial correlation lesson](understanding_partial_correlation.md)).
- **Accept it for prediction** — if you only care about the model's total predictive accuracy (R²) and not individual coefficients, multicollinearity doesn't matter.

## How it's used in this project

- **Analysis 12**: Found stop count and geographic span correlated at r = 0.41. Not extreme, but enough to warrant caution when interpreting individual coefficients. Used partial correlation as a workaround.
- **Analyses 18, 26, 27, 28**: Compute VIF formally before interpreting beta weights. If VIF is low, individual coefficients can be trusted. If high, the model still works for prediction but you can't claim "this specific variable matters more than that one."

## See also

- [Partial Correlation](understanding_partial_correlation.md) — an alternative approach when two predictors are correlated
- [F-Test and Model Comparison](understanding_f_test_and_model_comparison.md) — testing whether adding correlated predictors improves the model
- [Glossary: VIF](../GLOSSARY.md#variance-inflation-factor-vif)
- [Glossary: Multicollinearity](../GLOSSARY.md#multicollinearity)
