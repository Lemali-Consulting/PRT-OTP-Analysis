# Methods: Near-Side vs. Far-Side Stop Placement

## Question
Are PRT bus stops placed before (near-side) or after (far-side) traffic signals
at signalized intersections? What fraction of stops at signals are near-side vs.
far-side, and does placement correlate with route-level OTP?

## Approach

### Step 1 — Match stops to nearby signals
For every GTFS stop, find all OSM traffic signals within a 50 m radius.  A
stop with no signal within 50 m is classified as "mid-block" and excluded from
the near/far analysis.  The 50 m threshold captures stops set back slightly from
the crosswalk box while avoiding picking up the *next* intersection (typical
Pittsburgh block face is 80–120 m).

### Step 2 — Assign each stop to a canonical route shape
A stop may serve many trips.  Pick the single GTFS shape that visits the stop
the most times (`stop_times` → `trips` → `shapes`).  Use that shape to infer
the direction of travel through the stop.

### Step 3 — Determine near-side vs. far-side via shape projection
Project both the stop coordinate and the nearby signal coordinate onto the
canonical shape polyline using the Shapely `project` method (returns distance
along the line).  

- **Near-side**: stop's along-shape position < signal's along-shape position
  (stop comes first in the direction of travel → bus stops, boards, then waits
  for the light).
- **Far-side**: stop's along-shape position > signal's along-shape position
  (bus clears the intersection, then stops to board).
- **Ambiguous**: stop and signal project to within 5 m of each other along the
  shape (essentially co-located; excluded from near/far counts).

### Step 4 — Aggregate and summarize
- System-wide fraction: near-side / far-side / mid-block counts.
- By route: fraction of signalized stops that are near-side; join to route OTP
  from `otp_monthly` to test for correlation.
- By neighborhood / planning district (optional, if a spatial join to a
  neighborhood GeoJSON is available).

### Step 5 — OTP correlation
Compute Pearson r and Spearman ρ between each route's near-side fraction and
its mean OTP.  Transit-operations theory predicts near-side stops are worse for
OTP (bus must stop twice — once for passengers, once for the light), so a
negative correlation between near-side fraction and OTP is the expected sign.

### Step 6 — Validate against PRT's authoritative classification
PRT supplied an authoritative per-stop signal classification (the `stop_signals`
table, built by `pipeline/15_stop_signals/`). The GTFS heuristic above is
compared against it stop-by-stop on the shared `stop_code` key:

- **Signal detection** — a 2×2 confusion matrix of heuristic "signalized"
  (near/far) vs. PRT "has signal", reporting precision, recall, and accuracy.
- **Near vs. far** — among stops both sources call signalized, the agreement
  rate and a 2×2 near/far confusion matrix.

The route-level OTP correlation (Step 5) is then **re-run on the authoritative
near/far labels** (joining `stop_signals` → `route_stops` → `otp_monthly`), so
the headline OTP result no longer depends on the OSM proxy.

## Data

| Source | How used |
|--------|----------|
| `data/GTFS/stops.txt` | Stop lat/lon and stop_code (join key to authoritative labels) |
| `data/GTFS/shapes.txt` | Route shape polylines for direction-of-travel projection |
| `data/GTFS/stop_times.txt` | Links stops → trips for canonical shape assignment |
| `data/GTFS/trips.txt` | Links trips → shape_id |
| `data/osm-signals/traffic_signals_raw.json` | Signal lat/lon (2,820 OSM nodes) — heuristic only |
| `stop_signals` table in `prt.db` | PRT authoritative per-stop signal class (validation + authoritative re-run) |
| `route_stops` table in `prt.db` | Stop → route mapping for authoritative route-level aggregation |
| `otp_monthly` table in `prt.db` | Route mean OTP for correlation step |

Stops are filtered to bus stops only (exclude light-rail stations whose
right-of-way geometry differs fundamentally from street stops).

## Output
- `output/stop_classifications.csv` — one row per stop; columns: stop_id,
  stop_name, lat, lon, classification (near_side/far_side/mid_block/ambiguous),
  nearest_signal_distance_m, shape_id
- `output/route_summary.csv` — one row per route; near_side_count,
  far_side_count, mid_block_count, near_side_fraction, mean_otp
- `output/system_summary.png` — bar chart: system-wide stop classification
  breakdown
- `output/nearside_vs_otp.png` — scatter plot: route near-side fraction vs.
  mean OTP (with regression line)
- `output/top_nearside_routes.png` — ranked bar chart of routes by near-side
  fraction
- `output/heuristic_vs_authoritative.csv` — per-stop comparison of the GTFS
  heuristic label vs. PRT's authoritative class (join on stop_code)
- `output/validation_confusion.png` — confusion matrices: signal detection
  (left) and near vs. far (right), heuristic vs. PRT
- `output/authoritative_route_summary.csv` — per-route near/far counts and mean
  OTP using PRT authoritative labels
- `output/authoritative_nearside_vs_otp.png` — scatter: route near-side fraction
  (authoritative) vs. mean OTP
