"""Pipeline 02: load WPRDC scheduled trip tables into prt.db."""

from prt_otp_analysis.scheduled_trips import main as scheduled_trips_main


def main() -> None:
    """Run scheduled-trips ETL."""
    scheduled_trips_main()


if __name__ == "__main__":
    main()
