"""Pipeline 15: load PRT's authoritative bus-stop signal classification into prt.db."""

from prt_otp_analysis.stop_signals import main as stop_signals_main


def main() -> None:
    """Run the stop-signal ingestion ETL."""
    stop_signals_main()


if __name__ == "__main__":
    main()
