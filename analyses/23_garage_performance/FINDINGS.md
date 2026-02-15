# Findings: Garage-Level Performance

## Summary
PRT garages differ **significantly** in route-level OTP, and the difference **survives controlling for route structure**. An OLS model with stop count and geographic span as controls shows that garage dummies add significant explanatory power (F = 4.55, p = 0.005). Collier garage routes run +5.4 pp above East Liberty routes after controlling for stop count and span (p < 0.001).

## Key Numbers

| Garage | Routes | Mean OTP | Ridership-Wtd OTP | Avg Daily Riders |
|--------|--------|----------|-------------------|-----------------|
| South Hills Village | 3 | 85.4% | 85.3% | 11,588 |
| Collier | 18 | 73.6% | 73.9% | 14,226 |
| Ross | 22 | 70.7% | 69.5% | 20,141 |
| West Mifflin | 19 | 67.9% | 65.8% | 32,388 |
| East Liberty | 31 | 67.1% | 67.5% | 42,259 |

- **Kruskal-Wallis (all routes)**: H = 24.4, p = 0.0001 (5 garages)
- **Kruskal-Wallis (bus only)**: H = 20.0, p = 0.0002 (4 garages)
- 93 routes with 12+ months of paired data

### Controlled OLS Model (bus only, n = 89, reference = East Liberty)

| Model | R² | Adj R² |
|-------|----|--------|
| Base (stop_count + span) | 0.313 | 0.297 |
| Full (+ garage dummies) | 0.410 | 0.374 |

**F-test for garage dummies: F = 4.55, p = 0.005** -- garages are significant after controls.

| Feature | Coefficient | p-value |
|---------|-------------|---------|
| stop_count | -0.00039 | 0.001 |
| span_km | -0.0022 | 0.014 |
| garage_Collier | +0.054 | <0.001 |
| garage_Ross | +0.029 | 0.040 |
| garage_West_Mifflin | +0.014 | 0.358 |

## Observations
- **Collier** routes outperform East Liberty by +5.4 pp even after controlling for stop count and span (p < 0.001). This is a substantial and statistically robust effect.
- **Ross** routes outperform East Liberty by +2.9 pp after controls (p = 0.04), a marginally significant effect.
- **West Mifflin** does not differ significantly from East Liberty after controls (+1.4 pp, p = 0.36). The raw difference between these two garages (0.8 pp) was largely explained by route structure.
- Adding garage dummies increases R² from 0.313 to 0.410 (+9.7 pp), a meaningful improvement beyond what route structure alone explains.
- The monthly trend chart shows all garages move together with system-wide trends (COVID spike, 2022 trough), but the relative ordering is stable: Collier consistently above Ross, which is consistently above East Liberty and West Mifflin.

## Discussion
The controlled analysis overturns the initial interpretation that garage differences were purely a composition effect. **Collier's advantage is real and operationally meaningful**: after accounting for the fact that it operates shorter routes with fewer stops, Collier routes still outperform East Liberty routes by 5.4 pp. This could reflect differences in traffic conditions in the western suburbs, garage-level operational practices (scheduling, dispatch, maintenance), or corridor-specific factors not captured by stop count and span alone.

West Mifflin's poor raw performance, by contrast, *is* largely explained by route structure: it operates the long eastern-corridor routes, and after controlling for that, it is statistically indistinguishable from East Liberty.

The R² increase from 0.31 to 0.41 suggests that garage assignment captures roughly 10% of OTP variance beyond what stop count and span explain -- a nontrivial amount that warrants further investigation with operational data (staffing, vehicle age, traffic conditions by corridor).

## Caveats
- The `current_garage` field is a snapshot; historical garage assignments are not available. If routes were reassigned between garages, the analysis would not capture that (though the data shows no garage changes for any route).
- The controlled model uses only stop count and span as structural controls. Adding further controls (e.g., traffic density, road type, schedule slack) could reduce or eliminate the garage effect.
- The F-test assumes normally distributed residuals; the Kruskal-Wallis test (non-parametric) is more robust but does not support covariates.
- South Hills Village (n=3 rail routes) and Incline (excluded, no OTP data) are too small for meaningful comparison and are excluded from the controlled model.
