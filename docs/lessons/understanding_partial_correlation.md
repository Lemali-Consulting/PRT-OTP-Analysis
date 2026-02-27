# Understanding Partial Correlation

Partial correlation measures the relationship between two variables after removing the influence of a third. "Removing the influence" means isolating the portion of each variable that the third variable can't explain.

## The problem it solves

When two predictors are correlated with each other (e.g., route span and stop count), a simple correlation between either one and OTP is ambiguous. You don't know if span *itself* matters or if it's just a proxy for "has lots of stops."

## How it works mechanically

Using the example from Analysis 12 (geographic span vs. OTP, controlling for stop count):

1. **Regress span on stop count.** The residuals are the part of span that stop count can't explain — routes that are longer or shorter than you'd expect given their number of stops.

2. **Regress OTP on stop count.** The residuals are the part of OTP that stop count can't explain — routes performing better or worse than you'd expect given their number of stops.

3. **Correlate the two sets of residuals.** This is the partial correlation.

## Intuition

Think of it as comparing like with like. Instead of comparing a 10-stop route against a 50-stop route, you're comparing two 30-stop routes — one that spans 15 km and one that spans 8 km. Stop count is held roughly equal, so any remaining OTP difference is attributable to span itself.

## Result from this project

In Analysis 12, the raw Pearson correlation between span and OTP was stronger than the partial correlation (r = −0.30) after controlling for stop count. This means:

- Some of span's apparent effect on OTP was really just stop count in disguise.
- But span still has its own independent negative relationship with OTP — longer routes perform worse even among routes with similar stop counts.

## Assumptions and limitations

Partial correlation controls for the variable you specify — and **only** that variable. It assumes that the third variable you're regressing out is the only confounder. In reality, there may be a fourth, fifth, or sixth variable also influencing both span and OTP (e.g., traffic conditions, time-of-day mix, road geometry). The residuals you correlate in step 3 still contain all of those uncontrolled influences, so the partial correlation may still be confounded — just less so than the raw correlation.

This is a fundamental limitation: partial correlation doesn't prove that span *causes* lower OTP. It only says "the relationship survives after accounting for stop count." Another lurking variable could still explain it.

When you suspect multiple confounders, multiple regression (Analyses 18, 23, 26–28) is the more appropriate tool — it controls for several variables simultaneously. Partial correlation is best treated as a quick check for one specific confounder, not as a definitive answer.

## When to use partial correlation

- You have two predictors that are correlated with each other and you want to know which one is actually driving the relationship with the outcome.
- You suspect a confounding variable and want to "hold it constant" without running a full multiple regression.
- It's a lighter-weight alternative to multiple regression when you only need to check one relationship while controlling for one confounder.

## See also

- [Glossary: Partial Correlation](../GLOSSARY.md#partial-correlation)
- [Glossary: Pearson Correlation](../GLOSSARY.md#pearson-correlation-r)
- [Choosing a Correlation Method](choosing_correlation_methods.md)
