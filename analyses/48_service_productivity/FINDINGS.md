# Findings: Service Productivity (Passengers per Revenue Hour)

## Key findings

1. **PRT's service productivity has roughly halved since 1991** — from 39.2 passengers per vehicle revenue hour in 1991 to 18.3 in 2024, a 53% decline. Each hour of bus and rail service now carries fewer than half as many riders as it did three decades ago.

2. **The decline is demand-driven, not a right-sizing of service.** Over the full 1991–2024 record, PRT's service hours barely moved (VRH −5%) while ridership collapsed (UPT −55%). PRT kept very nearly the same amount of service on the street as riders disappeared — the productivity drop is emptier vehicles, not a deliberate match of supply to demand.

3. **PRT's post-pandemic productivity drop was the steepest of all 8 peer cities.** Between 2019 and 2024, PRT productivity fell 32% (26.9 → 18.3), worse than every peer — Portland (−25%), Baltimore (−27%), Buffalo (−24%), St. Louis (−22%), Minneapolis (−21%), Cleveland (−20%), Denver (−20%).

4. **The decline is long-run, not just a COVID shock.** PRT productivity had already fallen 31% from 1991 (39.2) to 2019 (26.9) before the pandemic. COVID then roughly doubled the cumulative loss in five years.

5. **PRT's 2024 productivity (18.3) is mid-pack, leaning low.** It trails Minneapolis (25.1), Portland (22.8), Buffalo (18.7), and Denver (18.6), and sits above Baltimore (16.1), Cleveland (15.2), and St. Louis (14.7). Productivity fell at every peer — this is a national pattern, not a Pittsburgh-specific failure — but Pittsburgh's *rate* of recent decline stands out.

## Limitations

- **Agency-wide only.** NTD reports productivity for the whole agency; it cannot be broken down by route, mode, or neighborhood. A coverage-oriented route serving a low-density area will have low productivity by design, so this metric is not a verdict on any individual service.
- **UPT counts boardings, not riders.** Unlinked passenger trips count each boarding separately, so a rider who transfers is counted more than once. Productivity here measures boardings per service hour, not unique people moved.
- **VRH excludes deadhead.** Vehicle revenue hours count only time in revenue service, not pull-out, layover, or repositioning, so this understates total operating effort behind each productive hour.
- **Productivity is not the only goal.** Lower productivity can reflect a deliberate equity choice to serve lower-density areas. The metric describes how full the service runs, not whether the service is worth running.

## Validation

- **Data source verified.** `upt` and `vrh` columns of `ntd_annual_service` (NTD annual data, TS2.2). No column mapping written from memory.
- **Null/missing handling.** All 8 peer agencies have complete, non-null UPT and VRH for every year 1991–2024 (34 city-years each) — verified before analysis. No rows dropped.
- **Aggregates sanity-checked.** PRT 2024 UPT (37.9M) and VRH (2.07M) match the figures used in Analysis 40. The implied 2024 productivity (18.3) is consistent with Analysis 40's reported −41% UPT / −13% VRH change over 2019–2024, which arithmetically yields a ≈−32% productivity change.
- **Direction of effects checked.** Productivity fell at all 8 agencies post-COVID, consistent with the well-documented national decline in transit ridership relative to service. No directional reversal.
- **Surprising result investigated.** PRT having the steepest 2019–2024 productivity drop is notable but not anomalous: Analyses 36 and 40 already show PRT among the steepest ridership losers nationally while cutting less service than several peers. Steepest ridership loss combined with a below-median service cut necessarily produces the steepest productivity drop. This is a real pattern, not a data error.
