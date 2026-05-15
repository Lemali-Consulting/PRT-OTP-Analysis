# Findings: Service Productivity (Passengers per Revenue Hour)

## Key findings

1. **PRT's service productivity has roughly halved since 1991** — from 39.2 passengers per vehicle revenue hour in 1991 to 18.3 in 2024, a 53% decline. Each hour of bus and rail service now carries fewer than half as many riders as it did three decades ago.

2. **The decline is demand-driven, not a right-sizing of service.** Over the full 1991–2024 record, PRT's service hours barely moved (VRH −5%) while ridership collapsed (UPT −55%). PRT kept very nearly the same amount of service on the street as riders disappeared — the productivity drop is emptier vehicles, not a deliberate match of supply to demand.

3. **PRT's post-pandemic productivity drop was the steepest of all 8 peer cities.** Between 2019 and 2024, PRT productivity fell 32% (26.9 → 18.3), worse than every peer — Portland (−25%), Baltimore (−27%), Buffalo (−24%), St. Louis (−22%), Minneapolis (−21%), Cleveland (−20%), Denver (−20%).

4. **The decline is long-run, not just a COVID shock.** PRT productivity had already fallen 31% from 1991 (39.2) to 2019 (26.9) before the pandemic. COVID then roughly doubled the cumulative loss in five years.

5. **PRT's 2024 productivity (18.3) is mid-pack, leaning low.** It trails Minneapolis (25.1), Portland (22.8), Buffalo (18.7), and Denver (18.6), and sits above Baltimore (16.1), Cleveland (15.2), and St. Louis (14.7). Productivity fell at every peer — this is a national pattern, not a Pittsburgh-specific failure — but Pittsburgh's *rate* of recent decline stands out.

6. **Population decline explains only about a tenth of the drop.** PRT serves Allegheny County, which lost roughly 8% of its residents between the 1990 census (1,336,449) and 2024 (1,231,809). But PRT ridership fell 55% over the same span, so ridership *per resident* roughly halved — from 64 to 31 trips per resident per year. A log decomposition of the ridership decline attributes ~10% to fewer residents and ~90% to each remaining resident riding less. Because service hours barely moved, the same split applies to the productivity decline: depopulation is a minor factor, and the collapse is overwhelmingly a demand problem.

## Limitations

- **Agency-wide blend.** The figures here come from the NTD annual workbook, which aggregates all modes into one number — mixing motor bus, light rail, the ACCESS paratransit service, and the incline. Analysis 50 splits the metric by mode and shows the blend matters: PRT's fixed-route bus-and-rail network runs about 26% above the all-mode 2024 figure, because low-productivity paratransit (a federally mandated door-to-door service) drags the agency average down. Productivity still cannot be broken down by route or neighborhood — a coverage-oriented route serving a low-density area will have low productivity by design, so this metric is not a verdict on any individual service.
- **UPT counts boardings, not riders.** Unlinked passenger trips count each boarding separately, so a rider who transfers is counted more than once. Productivity here measures boardings per service hour, not unique people moved.
- **VRH excludes deadhead.** Vehicle revenue hours count only time in revenue service, not pull-out, layover, or repositioning, so this understates total operating effort behind each productive hour.
- **Productivity is not the only goal.** Lower productivity can reflect a deliberate equity choice to serve lower-density areas. The metric describes how full the service runs, not whether the service is worth running.
- **Population normalization is coarse.** County population is paired with the NTD record only at census/estimate years (1990/2000/2010/2020 decennial counts plus the 2024 estimate), with no annual interpolation; the 1990 count stands in for 1991 with a ~9-month offset. Allegheny County is also broader than PRT's true ridership catchment, so the per-capita figures are county-wide averages, not the usage of the population actually within reach of service. The ~10% population share is approximate but robust — even the City of Pittsburgh's steeper ~18% loss would still leave per-capita decline as the dominant factor.

## Validation

- **Data source verified.** `upt` and `vrh` columns of `ntd_annual_service` (NTD annual data, TS2.2). No column mapping written from memory. Allegheny County population is from the U.S. Census Bureau: decennial counts for 1990–2020 and the Vintage 2024 Population Estimates Program figure (2020 census base less the reported 2020–2024 decline).
- **Population discontinuity avoided.** Decennial census counts and intercensal estimates use different methods; mixing a pre-2020 estimate with the 2020 census produces a spurious population jump. The decomposition uses only decennial counts plus one post-2020 estimate, so no method break falls inside the series.
- **Null/missing handling.** All 8 peer agencies have complete, non-null UPT and VRH for every year 1991–2024 (34 city-years each) — verified before analysis. No rows dropped.
- **Aggregates sanity-checked.** PRT 2024 UPT (37.9M) and VRH (2.07M) match the figures used in Analysis 40. The implied 2024 productivity (18.3) is consistent with Analysis 40's reported −41% UPT / −13% VRH change over 2019–2024, which arithmetically yields a ≈−32% productivity change.
- **Direction of effects checked.** Productivity fell at all 8 agencies post-COVID, consistent with the well-documented national decline in transit ridership relative to service. No directional reversal.
- **Surprising result investigated.** PRT having the steepest 2019–2024 productivity drop is notable but not anomalous: Analyses 36 and 40 already show PRT among the steepest ridership losers nationally while cutting less service than several peers. Steepest ridership loss combined with a below-median service cut necessarily produces the steepest productivity drop. This is a real pattern, not a data error.
