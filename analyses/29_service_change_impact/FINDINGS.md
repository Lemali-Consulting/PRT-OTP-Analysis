# Findings: Service Change Impact on OTP

## Summary

Schedule changes (pick period transitions) are associated with a small but statistically significant **positive** OTP shift on average, though the effect is weak and does not differ significantly by event type (increase, cut, or neutral).

## Key Numbers

- **738 schedule change events** detected across 101 routes (Nov 2016 -- Mar 2021)
- **Mean OTP delta: +0.6 pp** (t=2.95, p=0.003) -- schedule changes are followed by slightly higher OTP on average
- **By event type:**
  - Service increases (+118 trips/day avg): +1.3 pp OTP delta (n=110)
  - Service cuts (-64 trips/day avg): +0.1 pp OTP delta (n=215)
  - Neutral (same trips, new schedule): +0.8 pp OTP delta (n=413)
- **Kruskal-Wallis across types:** H=4.03, p=0.13 -- no significant difference between event types
- **Trip delta vs OTP delta:** Pearson r=0.072 (p=0.050), Spearman rho=0.074 (p=0.045) -- marginally significant positive association

## Observations

- The dominant event type is "neutral" (413 of 738) -- same trip count, different schedule period. This suggests most pick transitions are schedule restructurings rather than service level changes.
- Service increases show the largest OTP improvement (+1.3 pp), while service cuts show nearly no change (+0.1 pp). However, the Kruskal-Wallis test does not detect a significant difference, so this pattern may be noise.
- COVID period events (n=184) show a smaller mean delta (+0.2 pp) than non-COVID events (+0.8 pp), possibly because the COVID period involves confounding system-wide disruptions.
- The correlation between trip count change and OTP change is marginally significant (p~0.05) but very weak (r=0.07), explaining less than 1% of variance.

## Discussion

The statistically significant but tiny positive mean delta (+0.6 pp) is best interpreted as evidence that schedule changes are **not harmful** to OTP, rather than evidence that they improve it. The effect size is operationally negligible -- less than 1 percentage point -- and the lack of differentiation across event types (Kruskal-Wallis p=0.13) means we cannot conclude that service increases help or that service cuts hurt.

The most striking finding is the dominance of "neutral" events (413 of 738). Most pick period transitions leave trip counts unchanged, meaning PRT's schedule restructurings are primarily about rearranging timing, not adding or removing service. These neutral events still show a +0.8 pp OTP delta, which is consistent with the hypothesis that PRT uses schedule changes as opportunities to adjust running times or pad recovery time -- operational improvements that would improve OTP without changing trip frequency.

The marginal Spearman correlation (rho=0.074, p=0.045) aligns with the direction suggested by Analysis 30's pre-COVID subperiod (adding trips slightly degrades OTP), but in the opposite direction here -- adding trips is associated with better OTP. This apparent contradiction dissolves when considering that Analysis 29 measures 3-month average shifts around discrete events, while Analysis 30 measures month-over-month continuous variation. The schedule change event likely captures a package of operational adjustments (new running times, rerouted deadheads, adjusted layover) that happen to coincide with trip count changes, not a pure frequency effect.

For policy, the null Kruskal-Wallis result is the most actionable finding: it suggests PRT can adjust service levels (up or down) without expecting systematic OTP consequences. OTP is determined by factors other than how many trips are scheduled.

## Caveats

- The 3-month averaging window means overlapping events can contaminate each other. Routes with frequent schedule changes (every 2-3 months) have correlated before/after windows.
- The positive mean OTP delta could reflect a selection effect: PRT may time schedule changes to coincide with seasonal improvements or known operational gains.
- Causality cannot be established -- schedule changes and OTP improvements may share common causes (e.g., new management priorities).
