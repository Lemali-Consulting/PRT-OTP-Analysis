# Findings: NTD Annual Service ETL

Loaded NTD TS2.2 annual service data into `ntd_annual_service` table from two source files: the 2023 edition (1991–2023) and the 2024 edition (2015–2024), with the newer file taking precedence for overlapping years.

- **93,188 rows** written (2,794 unique agencies × up to 34 years each)
- **2,794 unique agencies** with identifier data
- **Year range**: 1991–2024

## PRT verification (NTD ID 30022)

| Year | VRH | VRM | UPT | VOMS |
|------|-----|-----|-----|------|
| 2019 | 2,382,972 | 31,955,492 | 64,007,925 | 942 |
| 2023 | 2,025,498 | 26,447,131 | 37,908,532 | 780 |
| 2024 | 2,070,196 | 26,908,180 | 37,876,514 | 766 |
