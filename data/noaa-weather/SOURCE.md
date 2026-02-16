# NOAA Weather Data Source

## API Endpoint

NCEI Climate Data Online (CDO) Access Data Service v1:

```
https://www.ncei.noaa.gov/access/services/data/v1
  ?dataset=daily-summaries
  &stations=USW00094823
  &startDate=2019-01-01
  &endDate=2025-12-31
  &dataTypes=PRCP,SNOW,SNWD,TMAX,TMIN,AWND
  &format=csv
  &units=metric
```

No API token required.

## Station

- **Station ID:** USW00094823
- **Name:** Pittsburgh International Airport (KPIT)
- **Location:** 40.4846N, 80.2144W, elevation 367m
- **Network:** GHCND (Global Historical Climatology Network - Daily)
- **Note:** ~20km from downtown Pittsburgh; standard station for regional climate analysis

## Fields

| Field | Description | Units |
|-------|-------------|-------|
| PRCP  | Daily precipitation | mm (tenths of mm in raw, metric flag converts) |
| SNOW  | Daily snowfall | mm |
| SNWD  | Snow depth on ground | mm |
| TMAX  | Daily maximum temperature | degrees Celsius (tenths) |
| TMIN  | Daily minimum temperature | degrees Celsius (tenths) |
| AWND  | Average daily wind speed | m/s (tenths) |

## Access Date

February 2026
