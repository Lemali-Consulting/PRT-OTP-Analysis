# WPRDC Scheduled Trip Counts -- Data Provenance

## Datasets

### 1. Monthly Schedule Aggregation (`schedule_monthly_agg.csv`)
- **WPRDC Dataset:** `d1eb0fcd-ba60-4407-9969-ceef464d0c00`
- **Resource:** `1ca23fa8-53ca-43be-a7f7-82d4c7ff10f5`
- **URL:** https://data.wprdc.org/dataset/d1eb0fcd-ba60-4407-9969-ceef464d0c00/resource/1ca23fa8-53ca-43be-a7f7-82d4c7ff10f5/download/schedule_monthly_agg.csv
- **Coverage:** Nov 2016 -- Mar 2021
- **Key columns:** `dateKey` (YYYYMM), `RouteCode`, `DayType` (WEEKDAY/SAT./SUN.), `Trips` (daily count), `TripDist` (daily miles), `PickID`, `Garage`, `Mode`

### 2. Schedule Period Lookup (`paac_pick_lookup.csv`)
- **WPRDC Dataset:** `b401859c-412b-4cb6-ad88-a4183b83183d`
- **Resource:** `3f789a37-d02b-4f2e-9212-3b824fb06678`
- **URL:** https://data.wprdc.org/dataset/b401859c-412b-4cb6-ad88-a4183b83183d/resource/3f789a37-d02b-4f2e-9212-3b824fb06678/download/paac_pick_lookup.csv
- **Key columns:** `PickID`, `PickStart` (date), `PickEnd` (date)

## Access
- No authentication required (public WPRDC data)
- Downloaded by `src/prt_otp_analysis/scheduled_trips.py`
- Access date: 2026-02-15
