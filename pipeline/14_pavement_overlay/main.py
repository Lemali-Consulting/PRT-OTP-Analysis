"""Pipeline step 14: build the route_road_pavement table from SPC's NHS
pavement-condition layer. Thin wrapper around prt_otp_analysis.road_overlay_pavement.main."""

from prt_otp_analysis.road_overlay_pavement import main as pavement_main

if __name__ == "__main__":
    pavement_main()
