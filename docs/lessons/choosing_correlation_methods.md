# Choosing a Correlation Method

When testing whether two variables are associated (e.g., stop count vs. OTP), the two main options in this project are Pearson and Spearman.

## Pearson Correlation

Pick Pearson when:

- You expect a roughly **straight-line** relationship (doubling X roughly doubles the effect on Y).
- Your data is fairly symmetric, not heavily skewed.
- You care about the **strength of the linear fit** specifically.

## Spearman Rank Correlation

Pick Spearman when:

- The relationship might be **curved but consistent** (Y always goes up as X goes up, but not at a constant rate).
- Your data is **skewed or has outliers** — ranking flattens out extremes, so one route with 10x the ridership won't dominate the result.
- You're working with **ordinal data** (things with a natural order but no meaningful numeric scale).

## What "ranking" means

Spearman replaces each raw value with its position when sorted (lowest = rank 1, next = rank 2, etc.), then runs a standard Pearson correlation on those ranks. This is why it detects monotonic relationships even when the actual curve isn't a straight line — it only cares whether the ordering is consistent, not the magnitudes.

## Default approach in this project

Most analyses report both Pearson and Spearman side by side. This is the pragmatic default:

- **If they agree**: the relationship is real and roughly linear.
- **If Spearman is strong but Pearson is weak**: the relationship is real but nonlinear.
- **If Pearson is strong but Spearman is weak**: a few outlier data points may be driving the Pearson result.

If forced to choose only one and unsure about the shape of the relationship, **Spearman is the safer default** — it makes fewer assumptions. You only lose something by choosing Spearman when the relationship is truly linear and you need to quantify the exact linear slope, which is more of a regression question anyway.

## See also

- [Glossary: Pearson Correlation](../GLOSSARY.md#pearson-correlation-r)
- [Glossary: Spearman Rank Correlation](../GLOSSARY.md#spearman-rank-correlation-ρ)
