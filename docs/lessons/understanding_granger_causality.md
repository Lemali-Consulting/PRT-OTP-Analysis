# Understanding Granger Causality

Granger causality tests whether knowing the past values of one time series helps predict another time series **better than that series' own past already does**.

## How it differs from lagged cross-correlation

Lagged cross-correlation asks: "Is OTP correlated with ridership *k* months later?" Granger causality asks a sharper question: "Does past OTP improve my prediction of ridership beyond what ridership's own history already tells me?"

The distinction matters because time series have momentum. If ridership has been declining for three months, it will probably be low next month too. A simple lagged correlation between OTP and ridership might just pick up that shared momentum rather than a genuine OTP-to-ridership signal. Granger causality accounts for this by giving ridership's own past first crack at the prediction.

## How it works mechanically

**Step 1 — Build the baseline model.** Predict this month's ridership using only ridership's own past values (e.g., ridership from 1, 2, and 3 months ago). This is an autoregressive model — the series predicting itself.

**Step 2 — Build the full model.** Predict this month's ridership using its own past values *plus* past OTP values (OTP from 1, 2, and 3 months ago).

**Step 3 — Compare with an F-test.** Did adding OTP significantly reduce the prediction error? If yes, OTP "Granger-causes" ridership — its past contains information about ridership's future that ridership's own past doesn't already capture.

This is essentially a nested model F-test (see [Glossary](../GLOSSARY.md#nested-model-f-test)) applied to time series.

## The name is misleading

Granger "causality" is really about **predictive precedence**, not causation in the everyday sense. If a third variable (say, weather or service changes) drives both OTP and ridership with different timing, OTP could Granger-cause ridership without actually causing it. The test cannot distinguish "X causes Y" from "X and Y are both caused by Z, but X reacts first."

## How Analysis 20 uses it

It runs the Granger test on each of the 93 routes individually (maxlag=3), producing 93 p-values. Since running 93 simultaneous tests means some will be "significant" by pure chance, it applies Bonferroni correction (multiplies each p-value by 93). After correction: zero routes show significant Granger causality in either direction.

This null result is actually informative — it suggests OTP and ridership are driven by largely separate mechanisms rather than one causing the other.

## Assumptions and limitations

- **Requires enough data.** Each route needs a long enough monthly series for the autoregressive models to be meaningful. Short series (under ~30 months) have low statistical power.
- **Assumes stationarity.** The test assumes the statistical properties of the series don't change over time. This is why Analysis 20 detrends the data first — removing the system-wide monthly mean before testing.
- **Only tests linear predictive relationships.** A nonlinear causal relationship (e.g., OTP only affects ridership below a threshold) would be missed.
- **Multiple testing burden.** Running the test on 93 routes requires correction (Bonferroni in this project), which makes it harder to find significant results. This is a necessary trade-off to avoid false positives.

## See also

- [Lagged Cross-Correlation](understanding_lagged_cross_correlation.md) — the simpler precursor to Granger causality
- [Glossary: Granger Causality](../GLOSSARY.md#granger-causality)
- [Glossary: Bonferroni Correction](../GLOSSARY.md#bonferroni-correction)
- [Glossary: Nested Model F-Test](../GLOSSARY.md#nested-model-f-test)
