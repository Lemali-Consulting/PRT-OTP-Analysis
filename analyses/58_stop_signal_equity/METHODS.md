# Methods: Stop Signal Placement Equity

## Question
Do stops at traffic signals — and specifically the operationally worse
**near-side** placement — cluster in lower-income, more transit-dependent, or
higher-minority neighborhoods? In other words, is the legacy near-side default
(Analysis 53) distributed unequally across the population it serves?

## Approach
1. Load PRT's authoritative per-stop signal classification from the
   `stop_signals` table (`signal_class`, `has_signal`).
2. Assign every stop to its containing ACS census tract via point-in-polygon
   (`assign_stops_to_tracts`), attaching the tract's median household income,
   total/zero-vehicle households, population, and Black (non-Hispanic) population.
3. **Income-quartile view.** Bin stops by their tract's median household income
   into quartiles. For each quartile compute (a) the signalized-stop share
   (fraction of stops at a signal) and (b) the near-side share (fraction of
   signalized stops that are near-side). A disparity would show as a monotonic
   gradient across quartiles.
4. **Tract-level correlations.** For each tract with enough stops, compute the
   signalized-stop share and near-side share, then correlate (Spearman) against
   three demographic measures: median household income, zero-vehicle household
   share, and Black population share. Spearman is used because the demographic
   distributions are skewed and the relationship need not be linear.
5. **Minimum-sample thresholds.** Tracts need ≥ 5 stops for the signalized-share
   correlation and ≥ 3 signalized stops for the near-side-share correlation;
   thresholds are reported. Quartile shares use all stops with a tract income.

## Data
- `stop_signals` table in `prt.db` (PRT authoritative per-stop signal class;
  built by `pipeline/15_stop_signals/`). Join key: PRT internal `stop_id`.
- `stops` table in `prt.db` (lat/lon for tract assignment, via the shared
  `assign_stops_to_tracts` helper).
- `census_tracts` table in `prt.db` (ACS demographics: median household income,
  households_total, households_zero_vehicle, population, pop_black_nh).
- **Scope caveat:** ACS demographics are only joined for stops inside a 5-county
  PA tract; a handful of out-of-region stops get null demographics and drop out.

## Output
- `output/stop_equity.csv` — per-stop: stop_id, signal_class, has_signal, geoid,
  median household income.
- `output/tract_equity_summary.csv` — per-tract signalized/near-side shares with
  demographics.
- `output/signal_share_by_income_quartile.png` — bar chart of signalized-stop
  share and near-side share by income quartile.
- `output/tract_income_vs_signal_share.png` — scatter of tract median income vs.
  signalized-stop share with fitted trend.
