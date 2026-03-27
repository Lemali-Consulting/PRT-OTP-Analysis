"""Pipeline 06: load NTD annual service tables (VRH, VRM) into prt.db."""

from prt_otp_analysis.ntd_service import main as ntd_service_main


def main() -> None:
    """Run NTD annual service ETL."""
    ntd_service_main()


if __name__ == "__main__":
    main()
