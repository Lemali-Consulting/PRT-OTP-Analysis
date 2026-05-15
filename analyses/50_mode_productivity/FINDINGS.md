# Findings: Bus vs. Rail — Productivity by Mode

## Key findings

1. **Rail runs fuller than bus.** In 2024 PRT's light rail "T" carried 25.7
   passengers per vehicle revenue hour, against 22.2 for the motor bus network —
   rail was about 16% more productive per hour of service operated. The common
   assumption that buses are the workhorse and rail the showpiece has it
   backwards on this measure: each hour of light rail service moved more riders.

2. **Paratransit drags the agency average far below the bus-and-rail network.**
   PRT's demand-response ACCESS service carried just 1.9 passengers per revenue
   hour in 2024 — roughly one-twelfth the fixed-route rate. It accounted for only
   2.4% of PRT's trips but consumed 22.8% of all revenue hours. This is not
   waste: door-to-door service for riders with disabilities is inherently
   low-productivity and is federally required under the Americans with
   Disabilities Act. But it means the agency-wide productivity figure is a blend
   that no rider of the bus or "T" actually experiences.

3. **The fixed-route network is meaningfully more productive than the agency
   number.** Analysis 48 reported PRT's agency-wide productivity at about 18
   passengers per revenue hour. Strip out paratransit and the incline, and PRT's
   conventional bus-plus-rail network ran at 22.5 in 2024 — 26% higher. The
   service most riders use is healthier than the all-mode blend suggests.

4. **The incline is PRT's most productive service — but tiny and volatile.** The
   Monongahela Incline carried 35.2 passengers per revenue hour in 2024, the
   highest of any mode: a short, frequently-boarded ride up Mount Washington. It
   is also the smallest, at 0.7% of trips, and its productivity swings sharply
   year to year because its revenue hours are small and sensitive to maintenance
   closures (it dropped to 35 in 2020, rebounded to 57 in 2022, then fell again).

5. **The post-2019 decline hit every mode.** From 2019 to 2024, productivity fell
   34% for motor bus (33.7 → 22.2), 42% for light rail (44.6 → 25.7), 21% for
   paratransit (2.4 → 1.9), and 62% for the incline (93.3 → 35.2). Light rail's
   percentage drop was the steeper of the two fixed-route modes — its ridership
   fell faster than the bus while its service hours were cut less.

6. **Before COVID, bus and rail moved in opposite directions.** Motor bus
   productivity *rose* from 28.4 in 2002 to a peak near 38 around 2011, then held
   in the low 30s: PRT cut bus service hours (2.23M → 1.47M VRH) faster than bus
   ridership fell — a genuine right-sizing. Light rail did the reverse, falling
   from about 73 in 2002 to 45 by 2019, as the 2012 North Shore Connector
   extension added service hours without adding proportional ridership. The
   agency-wide story of "service held flat while riders disappeared" is really
   two opposite mode trends averaged together.

## Limitations

- **Agency and mode level only.** NTD reports each mode for the whole agency, so
  this cannot distinguish a busy bus route from a coverage route, or one rail
  line from another. The per-mode figures are network averages.
- **The incline series is small-sample and volatile.** The incline operates a
  few thousand revenue hours a year, so its productivity is sensitive to short
  closures and reporting quirks. Its 2019→2024 change should be read as
  directional, not precise.
- **Paratransit VRH begins in 2007.** The NTD Monthly Module does not report
  revenue hours for demand-response or incline service before 2007, so those two
  productivity series — and the all-mode roll-up — start that year. Motor bus and
  light rail have a complete record from 2002.
- **UPT counts boardings, not riders.** A passenger who transfers is counted on
  each vehicle boarded, so productivity here is boardings per service hour, not
  unique people moved. This inflates bus productivity slightly relative to rail,
  since bus trips involve more transfers.
- **VRH excludes deadhead.** Revenue hours count only time in passenger service,
  not pull-out, layover, or repositioning, so this understates total operating
  effort behind each productive hour — equally across modes.
- **Productivity is not the only goal.** Paratransit's low figure reflects a
  legal service mandate, not inefficiency; a coverage-oriented service is
  expected to score low. The metric describes how full a service runs, not
  whether it is worth running.

## Validation

- **Data source verified.** `upt` and `vrh` columns of `ntd_ridership`, sourced
  from the NTD Monthly Module workbook (UPT and VRH sheets). The `vrh` column was
  added to the table for this analysis; the ETL (`src/prt_otp_analysis/ntd_ridership.py`)
  unpivots the VRH sheet on the same agency/mode/TOS/month grain as UPT. No
  column mapping was written from memory.
- **Temporal scope matches.** All four modes are summed over the same calendar
  years (2002–2024). The all-mode and paratransit/incline series are restricted
  to 2007–2024, the span where every mode has reported VRH; this restriction is
  stated in METHODS.md.
- **Null/missing handling.** Productivity is computed only where reported VRH is
  greater than zero. Pre-2007 demand-response and incline months report VRH = 0;
  these are left null, never treated as real zero-hour service that would yield
  an infinite ratio.
- **Aggregates sanity-checked.** The all-mode 2024 figure (17.8) reconciles with
  Analysis 48's 18.3: Analysis 48 uses the NTD annual TS2.2 workbook (2024 UPT
  37.9M), this analysis uses the NTD Monthly Module (2024 UPT 36.9M). The ~3% gap
  between the two NTD products is normal cross-source variance; both place PRT
  near 18. Motor bus 2024 UPT (32.5M) is consistent with PRT carrying ~88% of its
  trips on the bus.
- **Direction of effects checked.** Productivity fell at every mode after 2019,
  consistent with the documented national post-COVID ridership decline. No
  directional reversal.
- **Surprising result investigated.** Light rail out-productive of motor bus is
  plausible, not a data error: rail serves dense, high-demand corridors at high
  frequency, while the bus network includes many low-density coverage routes.
  The incline ranking highest is also expected — a short ride with rapid
  boardings packs many trips into few service hours. Both were checked against
  the underlying UPT and VRH totals.
- **Ecological framing.** All results are described as mode-level network
  averages for PRT, never as statements about individual routes or riders.
