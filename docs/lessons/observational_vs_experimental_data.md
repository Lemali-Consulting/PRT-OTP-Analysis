# Observational vs. Experimental Data

This is the overarching context for why the project uses the statistical toolkit it does. Every method in the glossary is, at some level, a workaround for not being able to run controlled experiments.

## The fundamental difference

In an **experiment**, you control the variables. You could theoretically create two identical 20 km routes — one with 15 stops, one with 40 — and measure the OTP difference. The stop count effect would be clean because you held span constant by design.

In **observational data**, you take the world as it is. PRT's routes evolved over decades based on where people live, where jobs are, political boundaries, road networks, and terrain. A long route through suburban sprawl naturally has more stops because there are more dispersed destinations to serve. You can't untangle span from stop count by designing a clean experiment — you observe the system as it exists and use statistical tools to approximate what an experiment would have told you.

## Why this matters for a transit system

Transit agencies can't A/B test their networks. You can't randomly assign half your riders to a high-frequency route and half to a low-frequency one. You can't hold geography constant while varying stop spacing. The data you have reflects the accumulated decisions of decades of planning, politics, and ridership patterns — all tangled together.

## What the statistical tools are actually doing

Each method in this project is an attempt to approximate experimental control using observational data:

- **Partial correlation** approximates "hold stop count constant and look at span" by regressing out the shared variation.
- **Multiple regression** approximates "hold everything constant simultaneously" by estimating each predictor's effect while accounting for the others.
- **VIF** tells you when variables are too entangled for even those tools to separate cleanly.
- **Detrending** approximates "remove the system-wide time trend so we can compare routes fairly."
- **Pre/post analysis** approximates a before-and-after experiment around service changes, though without a true control group.
- **Non-parametric tests** hedge against distributional assumptions you can't verify because you didn't design the data-generating process.
- **Granger causality** approximates a causal test using time ordering, though it only captures predictive precedence.

## The fundamental limitation

These are powerful tools, but they all share one limitation: **there could always be an unmeasured variable you didn't control for**. No amount of statistical sophistication fully closes the door on confounders in observational data. This is why the analyses flag caveats like:

- **Ecological fallacy** (Analyses 15, 16): aggregate patterns may not hold at the individual level.
- **Selection effects** (Analysis 29): routes that received service changes were chosen for a reason, not randomly assigned.
- **Simpson's paradox** (Analyses 04, 07, 10, 11, 12, 15, 17): aggregate trends can reverse within subgroups.
- **Regression to the mean** (Analyses 03, 14): extreme values naturally move toward the average over time.

These caveats aren't disclaimers tacked on for caution — they're direct consequences of working with observational data. The statistical methods reduce ambiguity; they don't eliminate it.

## See also

- [VIF and Multicollinearity](understanding_vif_and_multicollinearity.md) — detecting when predictors are too entangled
- [Partial Correlation](understanding_partial_correlation.md) — approximating experimental control for one variable
- [Glossary: Caveats section](../GLOSSARY.md#11-important-concepts-and-caveats) — the specific warnings flagged across analyses
