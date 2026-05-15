"""Pipeline 11: load route-level traffic signal exposure metrics into prt.db."""

from prt_otp_analysis.signal_overlay import main as signal_main


def main() -> None:
    """Run signal overlay ETL."""
    signal_main()


if __name__ == "__main__":
    main()
