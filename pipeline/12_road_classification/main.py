"""Pipeline 12: load route-level road-classification metrics into prt.db."""

from prt_otp_analysis.road_overlay import main as road_main


def main() -> None:
    """Run road-classification overlay ETL."""
    road_main()


if __name__ == "__main__":
    main()
