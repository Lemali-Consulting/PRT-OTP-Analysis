"""Pipeline 05: load NTD monthly ridership tables into prt.db."""

from prt_otp_analysis.ntd_ridership import main as ntd_main


def main() -> None:
    """Run NTD ridership ETL."""
    ntd_main()


if __name__ == "__main__":
    main()
