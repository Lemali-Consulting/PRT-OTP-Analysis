# Findings: Mode Comparison

## Summary

Light rail **significantly outperforms bus**, and dedicated right-of-way is the strongest differentiator. Among bus routes, limited-stop variants beat their local counterparts.

## Key Numbers

| Mode / Type | Avg OTP | Route Count |
|-------------|---------|-------------|
| RAIL | 84% | 3 |
| Busway (P/G prefix) | 71--76% | ~6 |
| Limited (L suffix) | ~72% | varies |
| Express (X suffix) | ~70% | varies |
| Local bus | 63--69% | ~80 |

- Paired route comparison (2 pairs found): limited variants average **+3.5 percentage points** over their local counterparts.
- The RAIL--BUS gap has been roughly stable over time -- both modes declined in parallel, suggesting system-wide factors rather than mode-specific ones.

## Observations

- Busway routes (P1, P3, G2, G3) perform nearly as well as rail, consistent with the dedicated-right-of-way hypothesis.
- Only 2 local/limited pairs were found in the data (routes with matching base IDs). More pairs would strengthen the comparison.
- The INCLINE mode has no OTP data and was excluded.

## Caveats

- Bus route classification uses route ID naming conventions (L/X suffix, P/G/O prefix). Some routes may be misclassified if their ID doesn't follow the standard pattern.
- Rail has only 3 routes (RED, BLUE, SLVR), so its average is sensitive to any single route's performance.
