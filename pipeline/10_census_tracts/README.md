# Pipeline 10: Census Tracts

Fetches 2022 TIGER/Line census tract polygons and ACS 5-year (2018–2022) demographics — total population (`B01003`), median household income (`B19013`), vehicle availability (`B25044`), and race/ethnicity (`B03002`) — for Allegheny, Beaver, Butler, Washington, and Westmoreland counties. Writes the joined result to the `census_tracts` table in `prt.db` for use in geographic equity and walkshed analyses.
