# Findings: COVID Ridership vs OTP Recovery

## Summary
**Zero of 93 routes** have recovered to pre-COVID ridership levels (median -43%, all negative). Routes that lost *more* ridership tended to see *better* OTP recovery (r = -0.21, p = 0.047), weakly supporting the hypothesis that ridership recovery degrades OTP through crowding and longer dwell times.

## Key Numbers
- **Ridership recovery**: median -43.4%, mean -44.5%; 0/93 routes at or above pre-COVID
- **OTP recovery**: 35/93 routes improved, 58/93 declined vs pre-COVID
- **Correlation (ridership change vs OTP change)**: Pearson r = -0.21, p = 0.047; Spearman r = -0.29, p = 0.005
- **Kruskal-Wallis (OTP delta by subtype)**: H = 2.89, p = 0.58 (not significant)
- Pre-COVID baseline: Jan 2019 -- Feb 2020; recovery period: Jan 2023 -- Oct 2024
- 93 routes with 6+ months in both periods

## Observations
- The scatter plot falls entirely in the left half (all ridership declines). The two populated quadrants are "both declined" (58 routes) and "riders down, OTP up" (35 routes). There are zero routes in the "both improved" or "riders up, OTP down" quadrants.
- **Flyers lost the most ridership** (median -68%), consistent with the collapse of peak-hour commute demand. Despite this, flyers show the widest spread in OTP recovery (some improved substantially, others declined).
- **Busway routes** had the best OTP recovery (median +3.3 pp), likely because their dedicated right-of-way insulates them from the traffic impacts that affect other routes.
- **Local bus routes** (n=64) show the widest spread on both axes, reflecting the diversity of the category. Some locals improved OTP by 10 pp while others declined by 19 pp.
- The routes that improved OTP the most (P7 +18 pp, P69 +10 pp, 41 +10 pp) all lost substantial ridership (-32% to -61%), consistent with the idea that fewer riders means shorter dwell times and better schedule adherence.

## Discussion
The weak negative correlation between ridership recovery and OTP recovery is consistent with a **crowding mechanism**: routes that regained more riders saw their OTP degrade (or fail to improve), while routes that stayed emptier ran closer to schedule. However, the effect is weak (r = -0.21) and the correlation is borderline significant (p = 0.047), so it should be interpreted cautiously.

The most policy-relevant finding is the **universal ridership collapse**: every single route is still below pre-COVID levels, with a median loss of 43%. This dwarfs any OTP effects. The system is running fewer riders on roughly the same infrastructure, and OTP has *still* declined for most routes -- suggesting that the OTP decline is driven by operational factors (staffing, vehicle maintenance, traffic congestion) rather than demand-side crowding alone.

The absence of subtype differences (Kruskal-Wallis p = 0.58) confirms Analysis 14's finding: no route type has recovered OTP systematically better or worse than others.

## Caveats
- The ridership data ends Oct 2024; more recent ridership trends are not captured.
- "Recovery" is defined as a simple average comparison between two periods, not a trajectory analysis. A route could be on an upward trend that the period average does not fully reflect.
- The correlation between ridership change and OTP change does not establish causation; both could be driven by a third factor (e.g., service cuts, schedule changes).
- Flyer and busway subtypes have small sample sizes (n=17 and n=3), limiting subtype-level conclusions.
- Ridership data is weekday only; weekend recovery patterns may differ.
