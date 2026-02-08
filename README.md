# PRT On-Time Performance Analysis

Analysis of Pittsburgh Regional Transit (PRT) on-time performance across routes, stops, and time.

## Setup

Requires Python 3.14+ and [uv](https://docs.astral.sh/uv/).

```bash
uv sync
```

## Data

Raw CSVs live in `data/` and are normalized into a SQLite database at `data/prt.db`.

To rebuild the database from source CSVs:

```bash
uv run python src/prt_otp_analysis/build_db.py
```

### Database tables

| Table            | Rows    | Description                            |
|------------------|---------|----------------------------------------|
| `routes`         | 105     | Route dimension (id, name, mode)       |
| `stops`          | 6,466   | Physical stop locations                |
| `route_stops`    | 11,078  | Which stops serve which routes         |
| `stop_reference` | 7,554   | Historical stop reference (all feeds)  |
| `otp_monthly`    | 7,651   | Monthly on-time percentage by route    |

OTP data spans January 2019 through December 2025 across 99 routes. Values are between 0.0 (0%) and 1.0 (100%).

See [`data/DATA_DICTIONARY.md`](data/DATA_DICTIONARY.md) for full schema documentation, source file mapping, and known data quality notes.

## Analyses

Each analysis is self-contained in a numbered directory under `analyses/`. Run any analysis independently:

```bash
uv run python analyses/01_system_trend/main.py
```

| # | Analysis | Question |
|---|----------|----------|
| 01 | System Trend | Is PRT getting more or less on-time over time? |
| 02 | Mode Comparison | Does rail outperform bus? Local vs express? |
| 03 | Route Ranking | Which routes are best/worst and trending up/down? |
| 04 | Neighborhood Equity | Are certain areas systematically underserved? |
| 05 | Anomaly Investigation | What explains sharp OTP drops? |

Each directory contains a `METHODS.md` describing the approach. See [`CONTRIBUTING.md`](CONTRIBUTING.md) for conventions on adding new analyses.

## Project structure

```
PRT-OTP-Analysis/
├── pyproject.toml
├── CONTRIBUTING.md                     # Analysis conventions
├── ANALYSIS-PROPOSAL.md                # Full list of proposed analyses
├── data/
│   ├── prt.db                          # SQLite database (generated)
│   ├── DATA_DICTIONARY.md              # Schema + data quality docs
│   ├── routes_by_month.csv             # Monthly OTP by route (wide format)
│   ├── Transit_stops_*.csv             # Current stops by route
│   ├── PRT_Current_Routes_*.csv        # Current route metadata
│   └── PRT_Stop_Reference_*.csv        # Historical stop lookup
├── src/prt_otp_analysis/
│   ├── build_db.py                     # ETL: CSVs → SQLite
│   └── common.py                       # Shared DB access + utilities
└── analyses/
    ├── 01_system_trend/                # System-wide OTP trend
    ├── 02_mode_comparison/             # BUS vs RAIL, local vs express
    ├── 03_route_ranking/               # Best/worst performers
    ├── 04_neighborhood_equity/         # Geographic equity
    └── 05_anomaly_investigation/       # Sharp drop forensics
```
