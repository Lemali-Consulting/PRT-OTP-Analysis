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
6. **Ridership-weighted view.** A per-stop count treats a busy downtown stop and
   a rarely used suburban stop equally, but riders do not experience them
   equally. We therefore recompute both the quartile shares and the tract-level
   shares **weighted by pre-pandemic weekday usage** (boardings + alightings per
   stop, from the WPRDC bus-stop-usage CSV). The weighted near-side share answers
   "what fraction of *signalized-stop boardings* happen at a near-side stop?" If
   low-income riders disproportionately *use* near-side stops, the per-rider view
   would show a gradient the per-stop view misses. Spearman correlations are
   re-run on the ridership-weighted tract shares.

## Data
- `stop_signals` table in `prt.db` (PRT authoritative per-stop signal class;
  built by `pipeline/15_stop_signals/`). Join key: PRT internal `stop_id`.
- `stops` table in `prt.db` (lat/lon for tract assignment, via the shared
  `assign_stops_to_tracts` helper).
- `census_tracts` table in `prt.db` (ACS demographics: median household income,
  households_total, households_zero_vehicle, population, pop_black_nh).
- `data/bus-stop-usage/wprdc_stop_data.csv` — pre-pandemic weekday boardings and
  alightings per stop, keyed by the same PRT internal `stop_id`; used for the
  ridership-weighted view. Covers 98% (6,174 / 6,299) of tract-matched signal
  stops; the rest have no usage record and drop out of the weighted figures only.
- **Scope caveat:** ACS demographics are only joined for stops inside a 5-county
  PA tract; a handful of out-of-region stops get null demographics and drop out.

## Output
- `output/stop_equity.csv` — per-stop: stop_id, signal_class, has_signal, usage,
  geoid, median household income.
- `output/tract_equity_summary.csv` — per-tract signalized/near-side shares
  (per-stop and ridership-weighted) with demographics.
- `output/income_quartile_shares.csv` — quartile shares, per-stop and
  ridership-weighted.
- `output/demographic_correlations.csv` — Spearman correlations of each share
  against the three demographics, for both per-stop and per-rider weightings.
- `output/signal_share_by_income_quartile.png` — bar chart of signalized-stop
  share and near-side share by income quartile.
- `output/tract_income_vs_signal_share.png` — scatter of tract median income vs.
  signalized-stop share with fitted trend.
- `output/nearside_share_rider_weighted.png` — near-side share by income quartile,
  per stop vs. per rider (ridership-weighted).
