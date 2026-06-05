"""Pipeline step 13: build the route_road_city table from the City of Pittsburgh
street centerline. Thin wrapper around prt_otp_analysis.road_overlay_city.main."""

from prt_otp_analysis.road_overlay_city import main as city_main

if __name__ == "__main__":
    city_main()
