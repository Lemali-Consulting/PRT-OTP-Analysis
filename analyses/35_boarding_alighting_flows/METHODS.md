# Methods: Boarding/Alighting Flow Analysis

## Question
Which stops are major trip generators (net boardings) vs trip attractors (net alightings), and how does the boarding/alighting balance vary by direction and geography?

## Approach
- Aggregate pre-pandemic weekday ridership to the physical-stop level, keeping boardings and alightings separate.
- Compute net flow per stop: `net = avg_ons - avg_offs`. Positive = net generator (more people board than alight); negative = net attractor.
- Classify stops by net flow magnitude and sign; identify the top generators and attractors.
- Examine the inbound/outbound direction dimension: inbound stops should skew toward alightings (attractor) and outbound toward boardings (generator) if the network is radial.
- Map net flow geographically to reveal land-use patterns (residential origins vs employment/commercial destinations).
- Compute the boarding-to-alighting ratio per stop and examine its distribution.

## Data
- `data/bus-stop-usage/wprdc_stop_data.csv` -- stop-level boardings/alightings by route, direction, and period

## Output
- `output/stop_net_flow.csv` -- per-stop boardings, alightings, net flow, and classification
- `output/net_flow_map.png` -- geographic scatter plot colored by net flow (blue = generator, red = attractor)
- `output/top_generators_attractors.png` -- horizontal bar chart of top 15 generators and attractors
