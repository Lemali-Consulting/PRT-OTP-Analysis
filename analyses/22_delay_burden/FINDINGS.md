# Findings: Passenger-Weighted Delay Burden

## Summary
Over the Jan 2019 -- Oct 2024 overlap period, PRT accumulated **55.5 million late weekday rider-trips** out of 179.2 million total (31% late rate). The top 10 routes by delay burden account for **26.6% of all late rider-trips**, and ridership weighting substantially reshuffles which routes appear most problematic compared to a pure OTP ranking.

## Key Numbers
- **55.5 million** cumulative late weekday rider-trips (Jan 2019 -- Oct 2024)
- **179.2 million** total weekday rider-trips; **31.0%** system late rate
- **Top 10 routes** account for 26.6% of all late rider-trips
- Rank correlation between OTP rank and burden rank: Spearman r = 0.40 (p < 0.001) -- moderate, meaning ridership significantly reshuffles priorities
- 93 routes with paired OTP + ridership data

## Top 10 Routes by Delay Burden

| Burden Rank | Route | OTP Rank | Avg OTP | Cumulative Late Rider-Trips |
|-------------|-------|----------|---------|----------------------------|
| 1 | 61C - McKeesport-Homestead | 3 | 59.0% | 2,765,662 |
| 2 | 51 - Carrick | 55 | 68.6% | 2,360,226 |
| 3 | 71C - Point Breeze | 8 | 60.9% | 2,241,803 |
| 4 | 61A - North Braddock | 7 | 60.6% | 2,135,034 |
| 5 | 71B - Highland Park | 10 | 61.9% | 2,086,371 |

Route 51 (Carrick) is the standout example: it ranks only 55th by OTP (68.6%, near the system average) but **2nd by delay burden** because it carries massive ridership. Conversely, Route 77 (Penn Hills) has the worst OTP (54.9%) but ranks only 18th by burden because fewer people ride it.

## Observations
- **Ridership dramatically reshuffles priorities.** The Spearman rank correlation between OTP rank and burden rank is only 0.40 -- OTP rank alone is a poor proxy for human impact.
- The **biggest upward shifts** (more burden than OTP suggests) are high-ridership transit routes: P1 East Busway (+77 ranks), RED light rail (+72), BLUE light rail (+65). These routes have decent OTP (80%+) but carry so many riders that even their small late fractions generate substantial burden.
- The **biggest downward shifts** (less burden than OTP suggests) are low-ridership flyers: 65 Squirrel Hill (-70), P69 Trafford Flyer (-66), P13 Mount Royal Flyer (-51). These have poor OTP but few riders, so the total human impact is small.
- The **delay burden trend** shows a sharp drop during COVID (1.5M to 0.3M monthly late rider-trips), then a partial recovery to ~0.8-1.0M by 2024 -- still well below pre-COVID levels primarily because ridership hasn't recovered.
- Pre-COVID, the system averaged ~1.3M late rider-trips per month. Post-COVID (2023-2024), it averages ~0.8M -- a 40% reduction driven almost entirely by ridership collapse, not OTP improvement.

## Discussion
This analysis reframes the OTP problem from "which routes are most unreliable" to "where does unreliability affect the most people." The two questions give different answers. A policy intervention on Route 51 (the #2 burden route) would affect more riders than fixing Route 77 (the #1 worst OTP route), even though 51's OTP is 14 pp better. Similarly, even small OTP improvements on high-ridership rail/busway routes would reduce more late rider-trips than large OTP improvements on low-ridership flyers.

The system's total delay burden has paradoxically *decreased* post-COVID -- not because service improved, but because fewer people are riding. If ridership recovers without OTP improvements, the burden will return to or exceed pre-COVID levels.

## Caveats
- "Late rider-trips" is a derived metric: `avg_riders * day_count * (1 - OTP)`. It does not measure actual delay duration -- a trip that is 1 minute late counts the same as one that is 30 minutes late.
- Ridership data is weekday only; weekend burden is not captured.
- OTP is a route-level monthly average; stop-level or trip-level variation is not reflected.
- The metric assumes all riders on a route experience the same OTP, which is an approximation -- riders at different stops on the same route may have different experiences.
