# Methods: Weather ETL

## Question
How do we produce a monthly weather feature table aligned to OTP months?

## Approach
1. Fetch or read cached NOAA daily observations for Pittsburgh airport station.
2. Aggregate daily metrics to monthly precipitation, snowfall, temperature, wind, and event-day counts.
3. Rebuild `weather_monthly` in `prt.db`.
4. Verify temporal overlap with `otp_monthly`.

## Data
- NOAA daily summaries API (`PRCP`, `SNOW`, `SNWD`, `TMAX`, `TMIN`, `AWND`)
- Cached CSV under `data/noaa-weather/`

## Output
- `weather_monthly` table in `data/prt.db`
