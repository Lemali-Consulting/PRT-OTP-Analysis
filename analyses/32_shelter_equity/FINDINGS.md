# Findings: Shelter Equity

## Summary
Only 7.3% of PRT bus stops have shelters, yet those sheltered stops serve 31% of total system ridership. Sheltered stops have 5x the median daily usage of unsheltered stops (34 vs 7 riders/day). The most striking gap is among regular bus stops, where just 7% have shelters despite serving the vast majority of riders. Several of the system's busiest stops -- including downtown intersections with 2,000+ daily boardings -- lack any shelter.

## Key Numbers
- **6,719** unique physical stops in the pre-pandemic weekday data
- **491** (7.3%) have shelters; **6,228** do not
- Sheltered stops: **median 34.3/day**, mean 162.6/day
- Unsheltered stops: **median 6.5/day**, mean 28.9/day
- Sheltered stops serve **30.7%** of total system ridership despite being only 7% of stops
- Mann-Whitney U test: p = 9.2e-84 (sheltered stops have significantly higher usage)
- **Bus** mode: only **7%** sheltered; **Busway**: 73%; **Light Rail**: 100%

## Observations
- **Shelter placement correlates with usage but leaves major gaps.** The top 20 unsheltered stops each see 1,200-2,800 daily riders. The busiest unsheltered stop (7th St at Penn Ave, 2,841/day) handles more riders than all but a handful of sheltered stops.
- **Downtown Pittsburgh has the biggest equity gap.** Almost all top unsheltered stops are in the downtown/Oakland corridor (5th Ave, Liberty Ave, Wood St, Stanwix St). These are high-exposure locations where riders wait in weather.
- **PAAC and City of Pittsburgh own most shelters** (197 and 174 respectively), with City shelters at higher-usage stops on average (204 vs 165/day).
- **Lamar (advertising) shelters skew low-usage**: 100 shelters averaging only 26 riders/day, suggesting ad-driven placement rather than ridership-driven.
- **Heffner shelters** also serve low-usage stops (avg 3/day), further suggesting non-ridership factors drive some shelter placement.
- **"Envision Downtown" and "Other" shelters** serve the absolute highest-volume locations (2,913 and 1,090/day respectively), but account for only 5 stops total.

## Discussion
The shelter coverage gap represents a tangible rider experience problem. The 20 busiest unsheltered stops collectively serve ~35,000 riders per day who wait without weather protection. Given Pittsburgh's climate (Analysis 28 showed snow days and freeze days significantly affect OTP), shelter absence at high-volume stops compounds the negative experience of unreliable service.

The divergence between shelter owners reveals different placement strategies. PAAC and City of Pittsburgh place shelters at moderately high-usage stops (165-204/day), following a ridership-informed approach. Lamar's advertising-driven placements (26/day average) prioritize visibility for ad revenue over rider need, and Heffner's placements (3/day) appear driven by factors entirely unrelated to ridership. This suggests the advertising-shelter model, while providing free infrastructure, does not align with transit equity goals.

The Pareto finding from Analysis 34 (2% of stops serve 50% of riders) frames the opportunity: sheltering just the top 150 unsheltered stops would reach a large share of unprotected riders. At typical shelter costs of $15-30K per installation, covering the top 20 unsheltered stops would cost $300-600K while protecting ~35,000 daily riders -- a strong return on investment.

The downtown equity gap is particularly striking because these stops are the most visible face of the transit system. Visitors and new riders encountering a 2,800-rider/day stop with no shelter receive a signal about the system's investment priorities. Addressing the downtown/Oakland gaps would improve both rider experience and public perception.

## Caveats
- The shelter field in the WPRDC data may not be fully up to date; some shelters may have been added or removed since the data was compiled.
- "No Shelter" is the default -- stops with missing shelter data are treated as unsheltered, which may slightly overcount the unsheltered total.
- Usage data is pre-pandemic (FY2019); current ridership patterns at specific stops may have shifted.
- Light rail shows 100% coverage but only 1 stop appears in the data, so the mode comparison is limited for rail.
