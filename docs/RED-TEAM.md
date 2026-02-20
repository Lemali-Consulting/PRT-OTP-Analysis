# Red-Team Protocol

## Scope

Review the specified analysis (or analyses) against the checklist below. **Report only — do not modify any code or files.** Output a structured report of findings for human review.

## Rules

1. **Only flag issues that fall into a checklist category below.** Do not invent novel methodological objections outside these categories.
2. **Every finding must cite the specific file, line(s), and code or query** that exhibits the issue. If you cannot point to concrete evidence, do not report it.
3. **Classify severity honestly:**
   - **Significant** — could change the direction or statistical significance of a finding.
   - **Moderate** — affects magnitude, precision, or reproducibility but not direction.
   - **Low** — cosmetic, documentation-only, or inherent to the data with no available fix.
4. **Do not fix anything.** The report is the deliverable. Fixes happen only after human review and approval.
5. **Do not re-check issues already documented** in existing RED-TEAM-REPORTS/ files for the same analysis.

## Checklist

### A. Unit of Analysis

- [ ] Is the unit of observation in the code (stop, route, route-month, system-month) consistent with what METHODS.md describes?
- [ ] Are correlations or regressions computed at the correct unit? (e.g., route-level OTP should not be correlated at the stop level, which inflates n.)
- [ ] Are observations independent at the stated unit, or is there clustering/nesting that is unaccounted for?

### B. Mode Stratification

- [ ] Are bus and rail pooled together? If so, is there a bus-only stratification to check for Simpson's paradox?
- [ ] If pooled results are the headline, is there justification for pooling?

### C. Statistical Testing

- [ ] Do claims of group differences (e.g., "premium routes recovered better") have a formal test (t-test, Kruskal-Wallis, etc.)?
- [ ] Do correlations report p-values or confidence intervals?
- [ ] Are multiple comparisons accounted for when many tests are run?

### D. Regression to the Mean

- [ ] Do before/after or baseline-vs-change comparisons test for RTM? (e.g., correlation between baseline level and delta.)

### E. Composition and Panel Balance

- [ ] Does the set of entities (routes, stops) change across time periods? If so, is the analysis restricted to a balanced panel or does it document the impact?
- [ ] Are time periods balanced (same number of years/months per group)?
- [ ] Are there minimum-observation filters (e.g., routes with fewer than N months excluded)?

### F. Code-Documentation Consistency

- [ ] Does the code implement what METHODS.md says? (e.g., if METHODS.md says "Spearman correlation," does the code compute Spearman?)
- [ ] Do chart labels, titles, and legends match what the code actually computed?
- [ ] Does FINDINGS.md accurately reflect the current output?

### G. Joins and Filters

- [ ] Do SQL JOINs match the intended relationships? (e.g., INNER vs LEFT, correct join keys.)
- [ ] Are NULL, zero, or sentinel values in filter columns handled? (e.g., `hood = '0'` in the stops table.)
- [ ] Are WHERE/HAVING clauses consistent with the stated inclusion criteria?

### H. Numerical and Implementation Correctness

- [ ] Are there division-by-zero, NaN propagation, or empty-group edge cases?
- [ ] Are rolling windows, lags, or shifts correctly parameterized? (e.g., `min_samples` vs `min_periods` in polars.)
- [ ] For matrix operations, are numerically stable methods used? (e.g., `lstsq` over `inv`.)

## Report Format

Post results in `RED-TEAM-REPORTS/`, named `YYYY-MM-DD-analysis-NN-short-name.md`, using this structure:

```markdown
# Red-Team Report: Analysis NN — Name

**Date:** YYYY-MM-DD
**Reviewer:** [human or model]
**Status:** Report only — no code changes made

## Findings

| # | Category | Severity | File:Line | Issue | Evidence | Suggested Fix |
|---|----------|----------|-----------|-------|----------|---------------|
| 1 | A | Significant | main.py:45 | ... | ... | ... |

## No Issues Found

List checklist categories that were checked and passed cleanly.

## Out of Scope

Note anything suspicious that does not fit a checklist category.
These are suggestions only and should not be acted on without human review.
```

## After Fixes Are Applied

Once a human has reviewed the report and approved fixes:

1. Apply the approved fixes and rerun the analysis.
2. Update the analysis's `FINDINGS.md` and `METHODS.md` if findings or methodology changed.
3. If `FINDINGS.md` changed, update the root-level `FINDINGS.md` as well.
4. Add a `## Review History` entry at the bottom of the analysis's `FINDINGS.md`:
   ```markdown
   ## Review History

   - YYYY-MM-DD: [RED-TEAM-REPORTS/filename.md](../../RED-TEAM-REPORTS/filename.md) — N issues (M significant). Brief summary of changes.
   ```
