# analyses

Each numbered subdirectory is a self-contained, independently-runnable analysis. See `CONTRIBUTING.md` in the project root for conventions on adding new analyses.

| # | Name | Question |
|---|------|----------|
| 01 | `01_system_trend` | Is PRT getting more or less on-time over the 2019-2025 window? |
| 02 | `02_mode_comparison` | Does light rail outperform bus? Do limited/express beat local? |
| 03 | `03_route_ranking` | Which routes are best/worst, improving/declining, most volatile? |
| 04 | `04_neighborhood_equity` | Are certain neighborhoods systematically underserved by OTP? |
| 05 | `05_anomaly_investigation` | What explains sharp OTP drops -- data issues or real events? |
| 06 | `06_seasonal_patterns` | Do routes show consistent seasonal OTP patterns? |
| 07 | `07_stop_count_vs_otp` | Do routes with more stops have worse OTP? |
| 08 | `08_hotspot_map` | Where do poor-performing routes cluster geographically? |
| 09 | `09_incline_investigation` | Why does the Monongahela Incline have no OTP data? |
| 10 | `10_frequency_vs_otp` | Does trip frequency correlate with OTP? |
| 11 | `11_directional_asymmetry` | Does IB/OB trip imbalance correlate with worse OTP? |

Run any analysis standalone:
```
uv run python analyses/NN_name/main.py
```
