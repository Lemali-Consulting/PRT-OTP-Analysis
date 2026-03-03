"""Pipeline 04: load route-level traffic exposure metrics into prt.db."""

from prt_otp_analysis.traffic_overlay import main as traffic_main


def main() -> None:
    """Run traffic overlay ETL."""
    traffic_main()


if __name__ == "__main__":
    main()
