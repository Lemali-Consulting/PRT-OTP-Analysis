"""Pipeline 09: load NTD fleet age distribution into prt.db."""

from prt_otp_analysis.ntd_fleet_age import main as ntd_fleet_age_main


def main() -> None:
    """Run NTD fleet age ETL."""
    ntd_fleet_age_main()


if __name__ == "__main__":
    main()
