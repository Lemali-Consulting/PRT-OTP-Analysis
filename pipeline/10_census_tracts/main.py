"""Pipeline 10: load census tract polygons + ACS population into prt.db."""

from prt_otp_analysis.census_tracts import main as census_main


def main() -> None:
    """Run census tract ETL."""
    census_main()


if __name__ == "__main__":
    main()
