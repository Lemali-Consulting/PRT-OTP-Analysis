# Understanding Lagged Cross-Correlation

Lagged cross-correlation tests whether changes in one time series predict changes in another time series some number of periods later.

## The problem it solves

A regular correlation tells you whether two variables move together *at the same time*. But sometimes the effect is delayed — a drop in OTP this month might not show up in ridership until next month or the month after. Lagged cross-correlation checks for these delayed relationships.

## How it works mechanically

Say you have monthly OTP and ridership for a route:

```
Month:      Jan  Feb  Mar  Apr  May  Jun  Jul  Aug
OTP:         72   68   74   71   69   75   73   70
Ridership:  450  440  460  455  435  465  458  448
```

**Lag 0**: Correlate the two series as-is. January OTP pairs with January ridership, February with February, etc. This is just a standard Pearson correlation.

**Lag 1**: Shift OTP forward by one month. Now January's OTP pairs with February's ridership, February's OTP with March's ridership. This asks: "Does this month's OTP predict *next* month's ridership?"

**Lag 2**: Shift by two months. January's OTP pairs with March's ridership. "Does OTP predict ridership two months out?"

Repeat for as many lags as you want to test. The lag that produces the strongest correlation tells you the typical delay between a change in one variable and the response in the other.

## How it's used in this project

Analysis 20 tests lags 0 through 6 months, asking: if OTP drops this month, does ridership follow 1, 2, 3... up to 6 months later? The result was underwhelming — no lag showed a strong, consistent relationship across routes.

## Limitations

**You lose data at each lag.** When you shift by *k* months, the first *k* OTP values have no ridership to pair with. With 48 months of data and lag 6, you're correlating only 42 pairs. Short time series run out of data fast, which limits how many lags you can meaningfully test.

**Direction matters.** Shifting OTP forward tests "does OTP predict future ridership?" Shifting ridership forward would test the reverse. Analysis 20 tests both directions.

**Correlation is not causation, even with a lag.** A lagged relationship could be driven by a third variable (e.g., seasonal patterns affect both OTP and ridership with different timing). This is why Analysis 20 follows up with Granger causality, which is a more rigorous version of the same question — and which also came back null after correction for multiple testing.

## See also

- [Glossary: Lagged Cross-Correlation](../GLOSSARY.md#lagged-cross-correlation)
- [Glossary: Granger Causality](../GLOSSARY.md#granger-causality)
- [Glossary: Pearson Correlation](../GLOSSARY.md#pearson-correlation-r)
