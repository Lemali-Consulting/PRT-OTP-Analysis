# Findings: NTD Annual Service ETL

Loaded NTD TS2.2 annual service data into `ntd_annual_service` table.

- **90,057 rows** written (3,062 agencies × up to 33 years each)
- **2,729 unique agencies** with identifier data
- **43,391 non-null VRH values**, 43,589 VRM, 43,475 UPT, 35,316 VOMS
- **Year range**: 1991–2023

## PRT verification (NTD ID 30022)

| Year | VRH | VRM | UPT | VOMS |
|------|-----|-----|-----|------|
| 2019 | 2,382,972 | 31,955,492 | 64,007,925 | 942 |
| 2023 | 2,025,498 | 26,447,131 | 37,908,532 | 780 |
